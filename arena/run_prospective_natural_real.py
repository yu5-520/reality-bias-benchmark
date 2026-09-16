#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .anchor_selection import select_anchor, validate_anchor_rule
from .build_prospective_natural_manifest import SCIENTIFIC_STATUS, verify_manifest
from .core import stable_hash
from .cost_budget import BudgetedProvider, pricing_policy
from .engine import run_arena_once
from .io_utils import load_json, load_jsonl, sha256_file
from .journal import Journal
from .providers import provider_from_config

ROOT = Path(__file__).resolve().parents[1]
AUTH_PHRASE = 'CALL_REAL_R2R6_PROSPECTIVE_NATURAL_API'


def _append_jsonl(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')
        f.flush()
        os.fsync(f.fileno())


def _write_json(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(row, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def _credential_check(model_config):
    if model_config.get('provider') == 'deepseek':
        if not os.environ.get('DEEPSEEK_API_KEY'):
            raise SystemExit('DEEPSEEK_API_KEY is not set')
        return
    raise SystemExit('unsupported prospective provider: ' + str(model_config.get('provider')))


def _validate(rows, provider_name):
    verify_manifest(rows)
    first = rows[0]
    contract = load_json(ROOT / first['contract_path'])
    rule = load_json(ROOT / first['anchor_rule_path'])
    model = load_json(ROOT / first['model_config_path'])
    validate_anchor_rule(rule)
    if contract.get('status') != 'FROZEN_BEFORE_PROSPECTIVE_SUBJECT_EVIDENCE':
        raise ValueError('prospective_contract_not_frozen')
    if contract.get('paid_subject_execution_authorized') is not False:
        raise ValueError('prospective_contract_must_remain_non_authorizing')
    if model.get('provider') != provider_name:
        raise ValueError('prospective_provider_mismatch')
    for row in rows:
        for path_key, hash_key in (
            ('contract_path', 'contract_hash'),
            ('theory_contract_path', 'theory_contract_hash'),
            ('measurement_plan_path', 'measurement_plan_hash'),
            ('arena_config_path', 'arena_config_hash'),
            ('model_config_path', 'model_config_hash'),
            ('anchor_rule_path', 'anchor_rule_hash'),
        ):
            if sha256_file(ROOT / row[path_key]) != row[hash_key]:
                raise ValueError('prospective_binding_hash_mismatch:' + hash_key)
        if row.get('scientific_status') != SCIENTIFIC_STATUS:
            raise ValueError('prospective_row_status_invalid')
    return contract, rule, model


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--outdir', required=True)
    ap.add_argument('--provider', required=True)
    ap.add_argument('--per-run-max-calls', required=True, type=int)
    ap.add_argument('--per-run-spending-ceiling', required=True, type=float)
    ap.add_argument('--global-spending-ceiling', required=True, type=float)
    ap.add_argument('--currency', default='USD')
    ap.add_argument('--authorization-phrase', required=True)
    ap.add_argument('--execute-real-api', action='store_true')
    args = ap.parse_args()
    if not args.execute_real_api or args.authorization_phrase != AUTH_PHRASE:
        raise SystemExit('Refusing provider calls: new prospective explicit authorization required.')
    if min(args.per_run_max_calls, args.per_run_spending_ceiling, args.global_spending_ceiling) <= 0:
        raise SystemExit('positive prospective limits required')
    rows = load_jsonl(args.manifest)
    contract, rule, model_config = _validate(rows, args.provider)
    if args.global_spending_ceiling < args.per_run_spending_ceiling * len(rows):
        raise SystemExit('global ceiling must cover all symmetric per-run ceilings')
    _credential_check(model_config)
    out = Path(args.outdir)
    if out.exists():
        raise ValueError('refusing_to_overwrite_prospective_output')
    out.mkdir(parents=True)
    auth = {
        'schema': 'RB-PROSPECTIVE-NATURAL-PAID-AUTHORIZATION-RECORD-v0.1',
        'batch_id': contract['batch_id'],
        'authorization_phrase': args.authorization_phrase,
        'provider': args.provider,
        'run_count': len(rows),
        'per_run_max_calls': args.per_run_max_calls,
        'per_run_spending_ceiling': args.per_run_spending_ceiling,
        'global_spending_ceiling': args.global_spending_ceiling,
        'currency': args.currency.upper(),
        'pricing_policy': pricing_policy(model_config),
        'manifest_sha256': sha256_file(args.manifest),
        'automatic_paid_evaluator': False,
        'one_shot_branch_authorized': False,
        'no_outcome_aware_rerun': True,
    }
    auth['authorization_hash'] = stable_hash(auth)
    _write_json(out / 'authorization_record.json', auth)
    upstream = provider_from_config(model_config)
    total_estimated_spend = 0.0
    traces_path = out / 'traces.jsonl'
    selection_index = out / 'selection_index.jsonl'
    errors_path = out / 'errors.jsonl'
    errors = []
    status_counts = {}
    for row in rows:
        provider = BudgetedProvider(upstream, model_config, spending_ceiling=args.per_run_spending_ceiling, currency=args.currency, max_calls=args.per_run_max_calls)
        snapshots = []
        snapshot_path = out / 'snapshots' / f"{row['run_id']}.jsonl"
        journal_path = out / 'journals' / (stable_hash({'run_id': row['run_id']})[:20] + '.jsonl')
        def save_snapshot(snapshot):
            snapshots.append(snapshot)
            _append_jsonl(snapshot_path, snapshot)
        try:
            domain = load_json(ROOT / f"arena/domains/{row['domain_id']}.json")
            arena_config = load_json(ROOT / row['arena_config_path'])
            with Journal(journal_path) as journal:
                trace = run_arena_once(domain, arena_config, provider, row['run_id'], row['logical_seed'], recorder=journal, state_snapshot_callback=save_snapshot)
            trace.update({
                'trial': row['trial'],
                'phase': row['phase'],
                'batch_id': row['batch_id'],
                'code_commit_sha': row['code_commit_sha'],
                'domain_hash': row['domain_hash'],
                'arena_config_path': row['arena_config_path'],
                'arena_config_hash': row['arena_config_hash'],
                'model_config_path': row['model_config_path'],
                'model_config_hash': row['model_config_hash'],
                'anchor_rule_path': row['anchor_rule_path'],
                'anchor_rule_hash': row['anchor_rule_hash'],
                'contract_path': row['contract_path'],
                'contract_hash': row['contract_hash'],
                'theory_contract_hash': row['theory_contract_hash'],
                'measurement_plan_hash': row['measurement_plan_hash'],
                'provider': args.provider,
                'authorization_hash': auth['authorization_hash'],
                'snapshot_count': len(snapshots),
                'snapshot_hashes': [x['state_hash'] for x in snapshots],
                'review_status': 'PENDING_REVIEW',
                'prospective_evidence': True,
            })
            _append_jsonl(traces_path, trace)
            evidence_hash = stable_hash({
                'trace_hash': stable_hash(trace),
                'snapshot_hashes': trace['snapshot_hashes'],
                'manifest_row_hash': stable_hash(row),
                'anchor_rule_hash': row['anchor_rule_hash'],
            })
            if trace['run_status'] == 'RUN_COMPLETE':
                selection = select_anchor(trace, snapshots, rule, evidence_hash=evidence_hash, selection_id=f"{row['run_id']}:PROSPECTIVE:ANCHOR:v0.3")
            else:
                selection = {
                    'selection_status': 'SKIPPED_NONCOMPLETE_BASELINE',
                    'trace_hash': stable_hash(trace),
                    'evidence_hash': evidence_hash,
                    'rule_hash': stable_hash(rule),
                    'eligible_count': 0,
                    'selection_record': None,
                    'selected_candidate': None,
                    'selected_snapshot': None,
                    'run_status': trace['run_status'],
                }
            status_counts[selection['selection_status']] = status_counts.get(selection['selection_status'], 0) + 1
            _write_json(out / 'selection_packages' / f"{row['run_id']}.json", selection)
            _append_jsonl(selection_index, {
                'run_id': row['run_id'],
                'run_status': trace['run_status'],
                'selection_status': selection['selection_status'],
                'eligible_count': selection.get('eligible_count', 0),
                'selection_record_hash': (selection.get('selection_record') or {}).get('record_hash'),
                'selected_candidate_id': (selection.get('selected_candidate') or {}).get('candidate_id'),
                'selected_state_hash': (selection.get('selection_record') or {}).get('selected_state_hash'),
            })
            total_estimated_spend += float(provider.estimated_spend)
        except Exception as err:
            error = {'run_id': row['run_id'], 'error': repr(err), 'snapshot_count_preserved': len(snapshots)}
            errors.append(error)
            _append_jsonl(errors_path, error)
    summary = {
        'schema': 'RB-PROSPECTIVE-NATURAL-RUN-SUMMARY-v0.1',
        'batch_id': contract['batch_id'],
        'planned_run_count': len(rows),
        'runner_error_count': len(errors),
        'selection_status_counts': status_counts,
        'estimated_total_spend': total_estimated_spend,
        'currency': args.currency.upper(),
        'per_run_max_calls': args.per_run_max_calls,
        'per_run_spending_ceiling': args.per_run_spending_ceiling,
        'global_spending_ceiling': args.global_spending_ceiling,
        'automatic_paid_evaluator_called': False,
        'one_shot_branch_called': False,
        'outcome_aware_rerun_count': 0,
    }
    summary['summary_hash'] = stable_hash(summary)
    _write_json(out / 'summary.json', summary)
    _write_json(out / 'errors.json', errors)
    if errors:
        raise SystemExit('prospective natural collection contains runner errors; preserved all available raw evidence')
    print('PROSPECTIVE_NATURAL_COLLECTION_COMPLETE')
    print('PAID_EVALUATOR_CALLED=NO')
    print('ONE_SHOT_BRANCH_CALLED=NO')


if __name__ == '__main__':
    main()
