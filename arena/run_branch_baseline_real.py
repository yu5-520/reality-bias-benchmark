#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from arena.anchor_selection import select_anchor, validate_anchor_rule
from arena.build_branch_baseline_manifest import verify_manifest
from arena.core import stable_hash
from arena.cost_budget import BudgetedProvider, pricing_policy
from arena.engine import run_arena_once
from arena.io_utils import load_json, load_jsonl, sha256_file
from arena.journal import Journal
from arena.providers import provider_from_config


AUTH_PHRASE = 'CALL_REAL_R5R6_BASELINE_API'


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
        base_env = model_config.get('base_url_env', 'BAILIAN_BASE_URL')
        model_env = model_config.get('model_env', 'BAILIAN_MODEL')
        if not os.environ.get(base_env):
            raise SystemExit(f'{base_env} is not set')
        if not os.environ.get(model_env):
            raise SystemExit(f'{model_env} is not set')
        return
    raise SystemExit('unsupported provider: ' + str(provider))


def _validate_bindings(rows, arena_path, model_path, rule_path, provider_name):
    verify_manifest(rows)
    arena_hash = sha256_file(arena_path)
    model_hash = sha256_file(model_path)
    rule_hash = sha256_file(rule_path)
    model = load_json(model_path)
    rule = load_json(rule_path)
    validate_anchor_rule(rule)
    if model.get('provider') != provider_name:
        raise ValueError('authorization_provider_does_not_match_model_config_provider')

    for row in rows:
        domain_path = ROOT / f"arena/domains/{row['domain_id']}.json"
        if row.get('domain_hash') != sha256_file(domain_path):
            raise ValueError('manifest_domain_hash_mismatch:' + row['run_id'])
        if row.get('arena_config_hash') != arena_hash:
            raise ValueError('manifest_arena_hash_mismatch:' + row['run_id'])
        if row.get('model_config_hash') != model_hash:
            raise ValueError('manifest_model_hash_mismatch:' + row['run_id'])
        if row.get('anchor_rule_hash') != rule_hash:
            raise ValueError('manifest_anchor_rule_hash_mismatch:' + row['run_id'])
        if row.get('model_provider') != provider_name:
            raise ValueError('manifest_provider_mismatch:' + row['run_id'])
        if row.get('scientific_status') != 'CANDIDATE_UNTIL_EXPLICIT_REAL_RUN_FREEZE_AND_API_AUTHORIZATION':
            raise ValueError('manifest_scientific_status_invalid:' + row['run_id'])
    return model, rule


def _authorization_record(args, rows, manifest_path, arena_path, model_path, rule_path, model_config):
    policy = pricing_policy(model_config)
    record = {
        'schema': 'RB-PAID-SUBJECT-AUTHORIZATION-v0.1',
        'experiment_family': 'R5R6-BRANCH-BASELINE-v0.1',
        'phase': 'BASELINE_SNAPSHOT_COLLECTION_ONLY',
        'authorization_phrase': args.authorization_phrase,
        'provider': args.provider,
        'model_config_path': str(model_path.relative_to(ROOT)),
        'model_config_version': model_config.get('config_version'),
        'model_alias': model_config.get('model_alias'),
        'run_count': len(rows),
        'max_subject_calls': args.max_subject_calls,
        'spending_ceiling': args.spending_ceiling,
        'currency': args.currency.upper(),
        'pricing_policy': policy,
        'manifest_path': str(manifest_path),
        'manifest_sha256': sha256_file(manifest_path),
        'arena_config_sha256': sha256_file(arena_path),
        'model_config_sha256': sha256_file(model_path),
        'anchor_rule_sha256': sha256_file(rule_path),
        'code_commit_sha': rows[0].get('code_commit_sha'),
        'automatic_paid_evaluator': False,
        'branch_continuation_authorized': False,
        'semantic_review': 'DEFERRED_APPEND_ONLY',
        'financial_guard_note': (
            'Runtime uses pre-call reservation plus provider-usage post-call estimate. '
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
    ap.add_argument('--model-config', required=True)
    ap.add_argument('--anchor-rule', default='arena/config/r5r6_anchor_rule_v0.2.json')
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
    model_path = ROOT / args.model_config
    rule_path = ROOT / args.anchor_rule
    if outdir.exists():
        raise ValueError('refusing to overwrite R5/R6 baseline output directory; choose a new path')
    outdir.mkdir(parents=True, exist_ok=False)

    rows = load_jsonl(manifest_path)
    model_config, rule = _validate_bindings(rows, arena_path, model_path, rule_path, args.provider)
    arena_config = load_json(arena_path)
    _credential_check(model_config)
    auth = _authorization_record(args, rows, manifest_path, arena_path, model_path, rule_path, model_config)
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
    journal_dir = Path(str(traces_path) + '.journals')
    selection_index_path = outdir / 'selection_index.jsonl'
    errors_path = outdir / 'errors.jsonl'
    errors_array_path = outdir / 'errors.json'
    attempted_run_ids = []
    unattempted_run_ids = []
    errors = []
    selection_status_counts = {}

    for row_index, row in enumerate(rows):
        if provider.budget_stop_reason:
            unattempted_run_ids.extend(x['run_id'] for x in rows[row_index:])
            break

        attempted_run_ids.append(row['run_id'])
        domain_path = ROOT / f"arena/domains/{row['domain_id']}.json"
        domain = load_json(domain_path)
        snapshots = []
        snapshot_path = outdir / 'snapshots' / f"{row['run_id']}.jsonl"
        journal_path = journal_dir / f"{row['run_id']}.jsonl"

        def save_snapshot(snapshot):
            snapshots.append(snapshot)
            _append_jsonl(snapshot_path, snapshot)

        try:
            with Journal(journal_path) as journal:
                journal({
                    'record_type': 'r5r6_baseline_started',
                    'manifest_row': row,
                    'authorization_hash': auth['authorization_hash'],
                    'arena_config': arena_config,
                    'model_config': model_config,
                    'anchor_rule': rule,
                })
                trace = run_arena_once(
                    domain,
                    arena_config,
                    provider,
                    row['run_id'],
                    row.get('logical_seed'),
                    recorder=journal,
                    state_snapshot_callback=save_snapshot,
                )
                journal({
                    'record_type': 'r5r6_baseline_finished',
                    'run_status': trace['run_status'],
                    'termination_reason': trace['termination_reason'],
                    'snapshot_count': len(snapshots),
                    'budget_summary': provider.summary(),
                })

            trace.update({
                'trial': row['trial'],
                'phase': row['phase'],
                'code_commit_sha': row.get('code_commit_sha'),
                'domain_hash': row['domain_hash'],
                'arena_config_path': args.arena_config,
                'arena_config_hash': row['arena_config_hash'],
                'model_config_path': args.model_config,
                'model_config_hash': row['model_config_hash'],
                'anchor_rule_path': args.anchor_rule,
                'anchor_rule_hash': row['anchor_rule_hash'],
                'provider': args.provider,
                'authorization_hash': auth['authorization_hash'],
                'snapshot_count': len(snapshots),
                'snapshot_hashes': [snapshot['state_hash'] for snapshot in snapshots],
                'budget_summary_after_run': provider.summary(),
                'review_status': 'PENDING_REVIEW',
            })
            _append_jsonl(traces_path, trace)

            baseline_evidence_hash = stable_hash({
                'trace_hash': stable_hash(trace),
                'snapshot_hashes': trace['snapshot_hashes'],
                'manifest_row_hash': stable_hash(row),
                'anchor_rule_hash': row['anchor_rule_hash'],
            })
            if trace['run_status'] == 'RUN_COMPLETE':
                selection = select_anchor(
                    trace,
                    snapshots,
                    rule,
                    evidence_hash=baseline_evidence_hash,
                    selection_id=f"{row['run_id']}:R5R6:ANCHOR-SELECTION-v0.2",
                )
            else:
                selection = {
                    'selection_status': 'SKIPPED_NONCOMPLETE_BASELINE',
                    'trace_hash': stable_hash(trace),
                    'evidence_hash': baseline_evidence_hash,
                    'rule_hash': stable_hash(rule),
                    'eligible_count': 0,
                    'selection_record': None,
                    'selected_candidate': None,
                    'selected_snapshot': None,
                    'run_status': trace['run_status'],
                }

            selection_status_counts[selection['selection_status']] = selection_status_counts.get(selection['selection_status'], 0) + 1
            selection_summary = {
                'run_id': row['run_id'],
                'selection_status': selection['selection_status'],
                'evidence_hash': baseline_evidence_hash,
                'eligible_count': selection.get('eligible_count', 0),
                'selection_record_hash': (selection.get('selection_record') or {}).get('record_hash'),
                'selected_state_hash': (selection.get('selection_record') or {}).get('selected_state_hash'),
                'selected_candidate_id': (selection.get('selected_candidate') or {}).get('candidate_id'),
            }
            _append_jsonl(selection_index_path, selection_summary)
            _write_json(outdir / 'selection_packages' / f"{row['run_id']}.json", selection)

            print(
                f"{row['run_id']} {trace['run_status']} snapshots={len(snapshots)} "
                f"selection={selection['selection_status']} estimated_spend={provider.estimated_spend:.8f} {provider.currency}",
                flush=True,
            )
        except Exception as err:
            error = {
                'run_id': row['run_id'],
                'error': repr(err),
                'snapshot_count_preserved': len(snapshots),
                'budget_summary': provider.summary(),
            }
            errors.append(error)
            _append_jsonl(errors_path, error)
            print(f"ERROR {row['run_id']}: {err}", file=sys.stderr, flush=True)

    _write_json(errors_array_path, errors)
    summary = {
        'schema': 'RB-R5R6-BASELINE-SNAPSHOT-SUMMARY-v0.1',
        'authorization_hash': auth['authorization_hash'],
        'manifest_sha256': auth['manifest_sha256'],
        'attempted_run_ids': attempted_run_ids,
        'unattempted_run_ids': unattempted_run_ids,
        'runner_error_count': len(errors),
        'selection_status_counts': selection_status_counts,
        'budget_summary': provider.summary(),
        'automatic_paid_evaluator_called': False,
        'branch_continuation_called': False,
        'review_status': 'PENDING_REVIEW',
    }
    summary['summary_hash'] = stable_hash(summary)
    _write_json(outdir / 'summary.json', summary)

    if provider.budget_stop_reason:
        raise SystemExit('R5/R6 baseline collection stopped by budget guard; preserved partial evidence.')
    if errors:
        raise SystemExit('R5/R6 baseline collection contains runner errors; preserved all available evidence.')

    print('R5/R6 baseline snapshot collection complete; branch continuation remains separately unauthorized.')


if __name__ == '__main__':
    main()
