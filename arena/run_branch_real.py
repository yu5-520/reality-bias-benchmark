#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from arena.branch_plan import verify_branch_plan
from arena.core import stable_hash
from arena.cost_budget import BudgetedProvider, pricing_policy
from arena.engine import run_arena_once
from arena.io_utils import load_json, load_jsonl, sha256_file
from arena.journal import Journal
from arena.providers import provider_from_config


AUTH_PHRASE = 'CALL_REAL_R5R6_BRANCH_API'


def _append_jsonl(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')
        f.flush()
        os.fsync(f.fileno())


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def load_plan_bundle(plan_dir):
    plan_dir = Path(plan_dir)
    bundle = {
        'plan': load_json(plan_dir / 'branch_plan.json'),
        'parent_snapshot': load_json(plan_dir / 'parent_snapshot.json'),
        'intervention_start_snapshot': load_json(plan_dir / 'intervention_start_snapshot.json'),
        'branch_rows': load_jsonl(plan_dir / 'branch_execution_manifest.jsonl'),
        'branch_manifests': load_jsonl(plan_dir / 'branch_manifests.jsonl'),
    }
    verify_branch_plan(bundle)
    return bundle


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


def validate_execution_bindings(bundle, *, provider_name, model_config_path, code_sha):
    verify_branch_plan(bundle)
    plan = bundle['plan']
    rows = bundle['branch_rows']
    model_identity = plan.get('model_identity') or {}
    config_identity = plan.get('config_identity') or {}
    code_identity = plan.get('code_identity') or {}

    if provider_name != model_identity.get('provider'):
        raise ValueError('authorization_provider_does_not_match_frozen_branch_plan')
    if model_config_path != model_identity.get('model_config_path'):
        raise ValueError('model_config_path_does_not_match_frozen_branch_plan')
    if code_sha != code_identity.get('branch_execution_commit'):
        raise ValueError('execution_code_sha_does_not_match_frozen_branch_plan')

    model_path = ROOT / model_config_path
    arena_path = ROOT / config_identity['arena_config_path']
    domain_path = ROOT / f"arena/domains/{config_identity['domain_id']}.json"
    if sha256_file(model_path) != model_identity.get('model_config_hash'):
        raise ValueError('model_config_hash_does_not_match_frozen_branch_plan')
    if sha256_file(arena_path) != config_identity.get('arena_config_hash'):
        raise ValueError('arena_config_hash_does_not_match_frozen_branch_plan')
    if sha256_file(domain_path) != config_identity.get('domain_hash'):
        raise ValueError('domain_hash_does_not_match_frozen_branch_plan')

    model_config = load_json(model_path)
    if model_config.get('provider') != provider_name:
        raise ValueError('provider_does_not_match_current_model_config')
    for row in rows:
        if row.get('model_provider') != provider_name:
            raise ValueError('row_provider_mismatch:' + row['run_id'])
        if row.get('model_config_hash') != model_identity.get('model_config_hash'):
            raise ValueError('row_model_hash_mismatch:' + row['run_id'])
        if row.get('arena_config_hash') != config_identity.get('arena_config_hash'):
            raise ValueError('row_arena_hash_mismatch:' + row['run_id'])
        if row.get('domain_hash') != config_identity.get('domain_hash'):
            raise ValueError('row_domain_hash_mismatch:' + row['run_id'])
        if row.get('branch_execution_code_commit_sha') != code_sha:
            raise ValueError('row_code_sha_mismatch:' + row['run_id'])
        if row.get('scientific_status') != 'CANDIDATE_UNTIL_EXPLICIT_REAL_RUN_FREEZE_AND_API_AUTHORIZATION':
            raise ValueError('row_scientific_status_invalid:' + row['run_id'])
        if row.get('automatic_paid_evaluator') is not False:
            raise ValueError('automatic_paid_evaluator_must_be_false:' + row['run_id'])
    return model_config, load_json(arena_path), load_json(domain_path)


def _authorization_record(args, bundle, model_config, code_sha):
    plan = bundle['plan']
    policy = pricing_policy(model_config)
    record = {
        'schema': 'RB-PAID-SUBJECT-AUTHORIZATION-v0.1',
        'experiment_family': 'R5R6-FROZEN-PARENT-BRANCH-v0.1',
        'phase': 'PHASE_B_BRANCH_CONTINUATION_ONLY',
        'authorization_phrase': args.authorization_phrase,
        'provider': args.provider,
        'model_config_path': args.model_config,
        'model_config_version': model_config.get('config_version'),
        'model_alias': model_config.get('model_alias'),
        'branch_plan_hash': plan['plan_hash'],
        'source_trace_hash': (plan.get('common_identity') or {}).get('source_trace_hash'),
        'source_evidence_hash': (plan.get('common_identity') or {}).get('source_evidence_hash'),
        'selection_record_hash': (plan.get('common_identity') or {}).get('selection_record_hash'),
        'parent_state_hash': plan['parent_snapshot_hash'],
        'intervention_start_state_hash': plan['intervention_start_snapshot_hash'],
        'replicates': plan['replicates'],
        'branch_run_count': plan['branch_row_count'],
        'max_subject_calls': args.max_subject_calls,
        'spending_ceiling': args.spending_ceiling,
        'currency': args.currency.upper(),
        'pricing_policy': policy,
        'branch_execution_code_commit_sha': code_sha,
        'automatic_paid_evaluator': False,
        'semantic_review': 'DEFERRED_APPEND_ONLY',
        'phase_a_rerun_authorized': False,
        'financial_guard_note': (
            'Runtime uses a pre-call reservation guard and provider-usage post-call estimate. '
            'The ceiling is an explicit authorization boundary and engineering stop guard, not a provider invoice guarantee.'
        ),
    }
    record['authorization_hash'] = stable_hash(record)
    return record


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--plan-dir', required=True)
    ap.add_argument('--outdir', required=True)
    ap.add_argument('--provider', required=True)
    ap.add_argument('--model-config', required=True)
    ap.add_argument('--spending-ceiling', required=True, type=float)
    ap.add_argument('--currency', required=True)
    ap.add_argument('--max-subject-calls', required=True, type=int)
    ap.add_argument('--authorization-phrase', required=True)
    ap.add_argument('--code-sha')
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

    code_sha = args.code_sha or os.environ.get('GITHUB_SHA') or 'LOCAL_OR_UNRECORDED'
    bundle = load_plan_bundle(args.plan_dir)
    model_config, arena_config, domain = validate_execution_bindings(
        bundle,
        provider_name=args.provider,
        model_config_path=args.model_config,
        code_sha=code_sha,
    )
    _credential_check(model_config)

    outdir = Path(args.outdir)
    if outdir.exists():
        raise ValueError('refusing to overwrite R5/R6 branch output directory; choose a new path')
    outdir.mkdir(parents=True, exist_ok=False)
    auth = _authorization_record(args, bundle, model_config, code_sha)
    _write_json(outdir / 'authorization_record.json', auth)

    upstream = provider_from_config(model_config)
    provider = BudgetedProvider(
        upstream,
        model_config,
        spending_ceiling=args.spending_ceiling,
        currency=args.currency,
        max_calls=args.max_subject_calls,
    )

    rows = bundle['branch_rows']
    parent = bundle['parent_snapshot']
    intervention = bundle['intervention_start_snapshot']
    manifests = {manifest['branch_hash']: manifest for manifest in bundle['branch_manifests']}
    traces_path = outdir / 'traces.jsonl'
    journal_dir = Path(str(traces_path) + '.journals')
    errors_jsonl_path = outdir / 'errors.jsonl'
    errors_array_path = outdir / 'errors.json'
    errors = []
    attempted_run_ids = []
    unattempted_run_ids = []
    recorded_run_ids = []

    for row_index, row in enumerate(rows):
        if provider.budget_stop_reason:
            unattempted_run_ids.extend(x['run_id'] for x in rows[row_index:])
            break

        attempted_run_ids.append(row['run_id'])
        manifest = manifests[row['branch_hash']]
        start_snapshot = parent if row['condition_id'] == 'CONTROL_CONTINUATION' else intervention
        journal_path = journal_dir / f"{row['pair_id']}--{row['condition_id']}.jsonl"
        try:
            with Journal(journal_path) as journal:
                journal({
                    'record_type': 'r5r6_branch_run_started',
                    'manifest_row': row,
                    'branch_manifest': manifest,
                    'branch_plan_hash': bundle['plan']['plan_hash'],
                    'authorization_hash': auth['authorization_hash'],
                    'arena_config': arena_config,
                    'model_config': model_config,
                })
                trace = run_arena_once(
                    domain,
                    arena_config,
                    provider,
                    row['run_id'],
                    row.get('logical_seed'),
                    recorder=journal,
                    initial_state_snapshot=start_snapshot,
                    branch_manifest=manifest,
                )
                journal({
                    'record_type': 'r5r6_branch_run_finished',
                    'run_status': trace['run_status'],
                    'termination_reason': trace['termination_reason'],
                    'budget_summary': provider.summary(),
                })

            trace.update({
                'trial': row['replicate_index'],
                'pair_id': row['pair_id'],
                'replicate_index': row['replicate_index'],
                'condition_id': row['condition_id'],
                'pair_order_pattern': row['pair_order_pattern'],
                'execution_order': row['execution_order'],
                'branch_plan_hash': bundle['plan']['plan_hash'],
                'source_selection_record_hash': row['source_selection_record_hash'],
                'code_commit_sha': code_sha,
                'domain_hash': row['domain_hash'],
                'arena_config_path': row['arena_config_path'],
                'arena_config_version': row.get('arena_config_version'),
                'arena_config_hash': row['arena_config_hash'],
                'model_config_path': row['model_config_path'],
                'model_config_version': row.get('model_config_version'),
                'model_config_hash': row['model_config_hash'],
                'provider': args.provider,
                'authorization_hash': auth['authorization_hash'],
                'budget_summary_after_run': provider.summary(),
                'review_status': 'PENDING_REVIEW',
            })
            _append_jsonl(traces_path, trace)
            recorded_run_ids.append(row['run_id'])
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
    summary = {
        'schema': 'RB-R5R6-BRANCH-RUN-SUMMARY-v0.1',
        'branch_plan_hash': bundle['plan']['plan_hash'],
        'authorization_hash': auth['authorization_hash'],
        'attempted_run_ids': attempted_run_ids,
        'recorded_run_ids': recorded_run_ids,
        'unattempted_run_ids': unattempted_run_ids,
        'runner_error_count': len(errors),
        'budget_summary': provider.summary(),
        'automatic_paid_evaluator_called': False,
        'phase_a_rerun_called': False,
        'review_status': 'PENDING_REVIEW',
    }
    summary['summary_hash'] = stable_hash(summary)
    _write_json(outdir / 'summary.json', summary)

    if provider.budget_stop_reason:
        raise SystemExit('R5/R6 branch collection stopped by budget guard; preserved partial evidence.')
    if errors:
        raise SystemExit('R5/R6 branch collection contains runner errors; preserved all available evidence.')

    print('R5/R6 Phase-B branch collection complete; semantic review remains deferred and no Phase-A rerun occurred.')


if __name__ == '__main__':
    main()
