#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .branch_plan_one_shot import verify_one_shot_branch_plan
from .core import stable_hash
from .io_utils import load_json, load_jsonl, sha256_file


def _maybe_sha(path: Path):
    return sha256_file(path) if path.exists() else None


def _journal_manifest(journal_dir: Path):
    rows = []
    if journal_dir.exists():
        for path in sorted(journal_dir.glob('*.jsonl')):
            rows.append({'file': path.name, 'sha256': sha256_file(path)})
    return rows


def _load_plan_bundle(plan_dir: Path):
    bundle = {
        'plan': load_json(plan_dir / 'branch_plan.json'),
        'parent_snapshot': load_json(plan_dir / 'parent_snapshot.json'),
        'one_shot_envelope': load_json(plan_dir / 'one_shot_intervention_envelope.json'),
        'branch_rows': load_jsonl(plan_dir / 'branch_execution_manifest.jsonl'),
        'branch_manifests': load_jsonl(plan_dir / 'branch_manifests.jsonl'),
    }
    verify_one_shot_branch_plan(bundle)
    return bundle


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--raw-dir', required=True)
    ap.add_argument('--plan-dir', required=True)
    ap.add_argument('--authorization-record')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    raw = Path(args.raw_dir)
    plan_dir = Path(args.plan_dir)
    bundle = _load_plan_bundle(plan_dir)
    traces_path = raw / 'traces.jsonl'
    if not traces_path.exists():
        raise ValueError('one_shot_traces_required_for_evidence_freeze')
    traces = load_jsonl(traces_path)
    planned_ids = {x['run_id'] for x in bundle['branch_rows']}
    if any(x.get('run_id') not in planned_ids for x in traces):
        raise ValueError('one_shot_trace_not_in_frozen_plan')

    statuses = {}
    conditions = {}
    exposure_counts = {}
    for trace in traces:
        statuses[trace.get('run_status')] = statuses.get(trace.get('run_status'), 0) + 1
        condition = trace.get('condition_id')
        conditions[condition] = conditions.get(condition, 0) + 1
        exposure_counts[trace.get('run_id')] = len([x for x in trace.get('runtime_transform_records') or [] if x.get('experiment_origin') is True])

    journals = _journal_manifest(raw / 'journals')
    record = {
        'schema': 'RB-R5MID-PROSPECTIVE-ONE-SHOT-EVIDENCE-BATCH-v0.1',
        'plan_hash': bundle['plan']['plan_hash'],
        'parent_state_hash': bundle['parent_snapshot']['state_hash'],
        'one_shot_envelope_hash': bundle['one_shot_envelope']['envelope_hash'],
        'planned_branch_count': len(bundle['branch_rows']),
        'preserved_trace_count': len(traces),
        'run_status_counts': statuses,
        'condition_trace_counts': conditions,
        'direct_experiment_origin_exposure_counts': exposure_counts,
        'traces_sha256': sha256_file(traces_path),
        'summary_sha256': _maybe_sha(raw / 'summary.json'),
        'errors_sha256': _maybe_sha(raw / 'errors.json'),
        'journal_manifest': journals,
        'journal_manifest_hash': stable_hash(journals),
        'branch_plan_sha256': sha256_file(plan_dir / 'branch_plan.json'),
        'parent_snapshot_sha256': sha256_file(plan_dir / 'parent_snapshot.json'),
        'one_shot_envelope_sha256': sha256_file(plan_dir / 'one_shot_intervention_envelope.json'),
        'branch_execution_manifest_sha256': sha256_file(plan_dir / 'branch_execution_manifest.jsonl'),
        'branch_manifests_sha256': sha256_file(plan_dir / 'branch_manifests.jsonl'),
        'authorization_record_sha256': sha256_file(args.authorization_record) if args.authorization_record else None,
        'raw_evidence_frozen_before_derived_analysis': True,
        'semantic_status': 'NOT_ADJUDICATED',
        'paid_evaluator_called': False,
        'source_role': bundle['plan'].get('source_evidence_role'),
        'measurement_binding': bundle['plan'].get('source_measurement_binding'),
    }
    record['evidence_batch_hash'] = stable_hash(record)
    Path(args.out).write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print('ONE_SHOT_RAW_EVIDENCE_FROZEN=YES')
    print('EVIDENCE_BATCH_HASH=' + record['evidence_batch_hash'])


if __name__ == '__main__':
    main()
