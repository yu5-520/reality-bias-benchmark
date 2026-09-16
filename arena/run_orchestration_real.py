#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from arena.build_orchestration_manifest import verify_pairing
from arena.core import stable_hash
from arena.cost_budget import BudgetedProvider, pricing_policy
from arena.engine import run_arena_once
from arena.io_utils import load_json, load_jsonl, sha256_file
from arena.journal import Journal
from arena.orchestration_compare import build_comparison_record, verify_comparison_record
from arena.providers import provider_from_config
from arena.structured_routing import run_structured_once, validate_structured_policy


AUTH_PHRASE = 'CALL_REAL_R7_API'


def _append_jsonl(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')
        f.flush()
        os.fsync(f.fileno())


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def _credential_check(model_config):
    provider = model_config.get('provider')
    if provider == 'deepseek':
        if not os.environ.get('DEEPSEEK_API_KEY'):
            raise SystemExit('DEEPSEEK_API_KEY is not set')
        return
    if provider == 'alibaba_cloud_bailian_business_space':
        credential_env = model_config.get('credential_env', 'BAI')
        if not os.environ.get(credential_env):
            raise SystemExit(f'{credential_env} is not set')
        if not os.environ.get(model_config.get('base_url_env', 'BAILIAN_BASE_URL')):
            raise SystemExit('Bailian base URL env is not set')
        if not os.environ.get(model_config.get('model_env', 'BAILIAN_MODEL')):
            raise SystemExit('Bailian model env is not set')
        return
    raise SystemExit('unsupported provider: ' + str(provider))


def _validate_manifest_bindings(rows, arena_path, policy_path, model_path, provider_name):
    verify_pairing(rows)
    arena_hash = sha256_file(arena_path)
    policy_hash = sha256_file(policy_path)
    model_hash = sha256_file(model_path)
    model_config = load_json(model_path)
    if model_config.get('provider') != provider_name:
        raise ValueError('authorization_provider_does_not_match_model_config_provider')

    for row in rows:
        domain_path = ROOT / f"arena/domains/{row['domain_id']}.json"
        if row.get('domain_hash') != sha256_file(domain_path):
            raise ValueError('manifest_domain_hash_mismatch:' + row['run_id'])
        if row.get('arena_config_hash') != arena_hash:
            raise ValueError('manifest_arena_hash_mismatch:' + row['run_id'])
        if row.get('structured_policy_hash') != policy_hash:
            raise ValueError('manifest_structured_policy_hash_mismatch:' + row['run_id'])
        if row.get('model_config_hash') != model_hash:
            raise ValueError('manifest_model_hash_mismatch:' + row['run_id'])
        if row.get('model_provider') != provider_name:
            raise ValueError('manifest_provider_mismatch:' + row['run_id'])
        if row.get('scientific_status') != 'CANDIDATE_UNTIL_EXPLICIT_REAL_RUN_FREEZE_AND_API_AUTHORIZATION':
            raise ValueError('manifest_scientific_status_invalid:' + row['run_id'])
    return model_config


def _authorization_record(args, rows, manifest_path, arena_path, policy_path, model_path, model_config):
    pairs = sorted({row['pair_id'] for row in rows})
    policy = pricing_policy(model_config)
    record = {
        'schema': 'RB-PAID-SUBJECT-AUTHORIZATION-v0.1',
        'experiment_family': 'R7-ORCHESTRATION-BOUNDARY-v0.1',
        'authorization_phrase': args.authorization_phrase,
        'provider': args.provider,
        'model_config_path': str(model_path.relative_to(ROOT)),
        'model_config_version': model_config.get('config_version'),
        'model_alias': model_config.get('model_alias'),
        'pair_count': len(pairs),
        'run_count': len(rows),
        'max_subject_calls': args.max_subject_calls,
        'spending_ceiling': args.spending_ceiling,
        'currency': args.currency.upper(),
        'pricing_policy': policy,
        'manifest_path': str(manifest_path),
        'manifest_sha256': sha256_file(manifest_path),
        'arena_config_sha256': sha256_file(arena_path),
        'structured_policy_sha256': sha256_file(policy_path),
        'model_config_sha256': sha256_file(model_path),
        'code_commit_sha': rows[0].get('code_commit_sha'),
        'automatic_paid_evaluator': False,
        'semantic_review': 'DEFERRED_APPEND_ONLY',
        'financial_guard_note': (
            'Runtime uses a pre-call reservation guard and provider-usage post-call estimate. '
            'The ceiling is an explicit authorization boundary and engineering stop guard, not a provider invoice guarantee.'
        ),
    }
    record['authorization_hash'] = stable_hash(record)
    return record


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--outdir', required=True)
    ap.add_argument('--arena-config', default='arena/config/arena_v0.3.json')
    ap.add_argument('--structured-policy', default='arena/config/structured_ecommerce_v0.1.json')
    ap.add_argument('--model-config', required=True)
    ap.add_argument('--provider', required=True)
    ap.add_argument('--spending-ceiling', required=True, type=float)
    ap.add_argument('--currency', required=True)
    ap.add_argument('--max-subject-calls', required=True, type=int)
    ap.add_argument('--authorization-phrase', required=True)
    ap.add_argument('--execute-real-api', action='store_true')
    args = ap.parse_args()

    if not args.execute_real_api:
        raise SystemExit('Refusing provider calls: --execute-real-api is required.')
    if args.authorization_phrase != AUTH_PHRASE:
        raise SystemExit(f'Refusing provider calls: authorization phrase must equal {AUTH_PHRASE}.')
    if args.spending_ceiling <= 0:
        raise SystemExit('Refusing provider calls: positive spending ceiling required.')
    if args.max_subject_calls <= 0:
        raise SystemExit('Refusing provider calls: positive max-subject-calls required.')

    manifest_path = Path(args.manifest)
    outdir = Path(args.outdir)
    arena_path = ROOT / args.arena_config
    policy_path = ROOT / args.structured_policy
    model_path = ROOT / args.model_config
    if outdir.exists():
        raise ValueError('refusing to overwrite R7 output directory; choose a new path')
    outdir.mkdir(parents=True, exist_ok=False)

    rows = load_jsonl(manifest_path)
    model_config = _validate_manifest_bindings(rows, arena_path, policy_path, model_path, args.provider)
    policy = load_json(policy_path)
    arena_config = load_json(arena_path)
    first_domain = load_json(ROOT / f"arena/domains/{rows[0]['domain_id']}.json")
    validate_structured_policy(first_domain, policy)
    _credential_check(model_config)

    auth = _authorization_record(args, rows, manifest_path, arena_path, policy_path, model_path, model_config)
    _write_json(outdir / 'authorization_record.json', auth)

    upstream = provider_from_config(model_config)
    provider = BudgetedProvider(
        upstream,
        model_config,
        spending_ceiling=args.spending_ceiling,
        currency=args.currency,
        max_calls=args.max_subject_calls,
    )

    traces_path = outdir / 'traces.jsonl'
    errors_jsonl_path = outdir / 'errors.jsonl'
    errors_array_path = outdir / 'errors.json'
    journal_dir = Path(str(traces_path) + '.journals')
    comparisons_path = outdir / 'pair_comparisons.jsonl'
    pair_index_path = outdir / 'pair_index.json'
    traces_by_pair = {}
    attempted_run_ids = []
    unattempted_run_ids = []
    errors = []

    for row_index, row in enumerate(rows):
        if provider.budget_stop_reason:
            unattempted_run_ids.extend(x['run_id'] for x in rows[row_index:])
            break

        attempted_run_ids.append(row['run_id'])
        domain_path = ROOT / f"arena/domains/{row['domain_id']}.json"
        domain = load_json(domain_path)
        journal_path = journal_dir / f"{row['pair_id']}--{row['condition_id']}.jsonl"
        try:
            with Journal(journal_path) as journal:
                journal({
                    'record_type': 'r7_run_started',
                    'manifest_row': row,
                    'authorization_hash': auth['authorization_hash'],
                    'arena_config': arena_config,
                    'structured_policy': policy,
                    'model_config': model_config,
                })
                if row['condition_id'] == 'EMERGENT_FREE_ROUTING':
                    trace = run_arena_once(
                        domain,
                        arena_config,
                        provider,
                        row['run_id'],
                        row.get('logical_seed'),
                        recorder=journal,
                    )
                elif row['condition_id'] == 'STRUCTURED_SYSTEM_OWNED_ROUTING':
                    trace = run_structured_once(
                        domain,
                        arena_config,
                        provider,
                        policy,
                        row['run_id'],
                        row.get('logical_seed'),
                        recorder=journal,
                    )
                else:
                    raise ValueError('unsupported_condition_id:' + str(row['condition_id']))
                journal({
                    'record_type': 'r7_run_finished',
                    'run_status': trace['run_status'],
                    'termination_reason': trace['termination_reason'],
                    'budget_summary': provider.summary(),
                })

            trace.update({
                'trial': row['trial'],
                'pair_id': row['pair_id'],
                'condition_id': row['condition_id'],
                'pair_execution_order': row['pair_execution_order'],
                'pair_order_pattern': row['pair_order_pattern'],
                'code_commit_sha': row.get('code_commit_sha'),
                'domain_hash': row['domain_hash'],
                'arena_config_path': args.arena_config,
                'arena_config_version': arena_config['version'],
                'arena_config_hash': row['arena_config_hash'],
                'structured_policy_path': args.structured_policy,
                'structured_policy_version': policy.get('version'),
                'structured_policy_hash': row['structured_policy_hash'],
                'model_config_path': args.model_config,
                'model_config_version': model_config.get('config_version'),
                'model_config_hash': row['model_config_hash'],
                'provider': args.provider,
                'authorization_hash': auth['authorization_hash'],
                'budget_summary_after_run': provider.summary(),
                'review_status': 'PENDING_REVIEW',
            })
            _append_jsonl(traces_path, trace)
            traces_by_pair.setdefault(row['pair_id'], {})[row['condition_id']] = trace
            print(
                f"{row['run_id']} {trace['run_status']} condition={row['condition_id']} "
                f"turns={trace['turns']} estimated_spend={provider.estimated_spend:.8f} {provider.currency}",
                flush=True,
            )
        except Exception as err:
            error = {
                'run_id': row['run_id'],
                'pair_id': row['pair_id'],
                'condition_id': row['condition_id'],
                'error': repr(err),
                'budget_summary': provider.summary(),
            }
            errors.append(error)
            _append_jsonl(errors_jsonl_path, error)
            print(f"ERROR {row['run_id']}: {err}", file=sys.stderr, flush=True)

    _write_json(errors_array_path, errors)

    pair_index = []
    for pair_id in sorted({row['pair_id'] for row in rows}):
        conditions = traces_by_pair.get(pair_id, {})
        free = conditions.get('EMERGENT_FREE_ROUTING')
        structured = conditions.get('STRUCTURED_SYSTEM_OWNED_ROUTING')
        if free is not None and structured is not None:
            comparison = build_comparison_record(
                free,
                structured,
                comparison_id=pair_id,
                fixture_identity={
                    'kind': 'REAL_SUBJECT_PAIRED_ORCHESTRATION',
                    'authorization_hash': auth['authorization_hash'],
                },
                code_identity={'commit': free.get('code_commit_sha')},
                scientific_status='SUBJECT_EVIDENCE_PENDING_SEMANTIC_REVIEW',
            )
            verify_comparison_record(comparison)
            _append_jsonl(comparisons_path, comparison)
            pair_index.append({'pair_id': pair_id, 'pair_status': 'PAIR_RECORDED', 'comparison_hash': comparison['comparison_hash']})
        else:
            pair_index.append({
                'pair_id': pair_id,
                'pair_status': 'PAIR_INCOMPLETE',
                'recorded_conditions': sorted(conditions),
            })

    final_summary = {
        'schema': 'RB-R7-PAIRED-RUN-SUMMARY-v0.1',
        'authorization_hash': auth['authorization_hash'],
        'manifest_sha256': auth['manifest_sha256'],
        'attempted_run_ids': attempted_run_ids,
        'unattempted_run_ids': unattempted_run_ids,
        'pair_index': pair_index,
        'runner_errors': len(errors),
        'budget_summary': provider.summary(),
        'review_status': 'PENDING_REVIEW',
        'automatic_paid_evaluator_called': False,
    }
    final_summary['summary_hash'] = stable_hash(final_summary)
    _write_json(pair_index_path, final_summary)

    if provider.budget_stop_reason:
        raise SystemExit('R7 subject collection stopped by budget guard; preserved partial evidence.')
    if errors or any(item['pair_status'] != 'PAIR_RECORDED' for item in pair_index):
        raise SystemExit('R7 subject collection has errors or incomplete pair(s); preserved all available evidence.')

    print('R7 paired subject collection complete; semantic review remains deferred.')


if __name__ == '__main__':
    main()
