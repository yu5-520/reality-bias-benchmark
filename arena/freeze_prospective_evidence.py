#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import stable_hash
from .io_utils import load_json, load_jsonl, sha256_file


def maybe_sha(path):
    return sha256_file(path) if Path(path).exists() else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--raw-dir', required=True)
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    raw = Path(args.raw_dir)
    if not raw.exists():
        raise ValueError('prospective_raw_dir_missing')
    rows = load_jsonl(args.manifest)
    traces_path = raw / 'traces.jsonl'
    summary_path = raw / 'summary.json'
    if not traces_path.exists() or not summary_path.exists():
        raise ValueError('prospective_required_raw_evidence_missing')
    traces = load_jsonl(traces_path)
    summary = load_json(summary_path)
    selection_index_path = raw / 'selection_index.jsonl'
    selection_index = load_jsonl(selection_index_path) if selection_index_path.exists() else []
    record = {
        'schema': 'RB-PROSPECTIVE-NATURAL-EVIDENCE-BATCH-v0.1',
        'batch_id': rows[0]['batch_id'],
        'manifest_sha256': sha256_file(args.manifest),
        'traces_sha256': sha256_file(traces_path),
        'selection_index_sha256': maybe_sha(selection_index_path),
        'summary_sha256': sha256_file(summary_path),
        'errors_json_sha256': maybe_sha(raw / 'errors.json'),
        'planned_run_count': len(rows),
        'preserved_trace_count': len(traces),
        'selection_record_count': len(selection_index),
        'run_status_counts': {},
        'selection_status_counts': summary.get('selection_status_counts', {}),
        'code_commit_sha': rows[0]['code_commit_sha'],
        'contract_hash': rows[0]['contract_hash'],
        'theory_contract_hash': rows[0]['theory_contract_hash'],
        'measurement_plan_hash': rows[0]['measurement_plan_hash'],
        'anchor_rule_hash': rows[0]['anchor_rule_hash'],
        'automatic_paid_evaluator_called': False,
        'one_shot_branch_called': False,
        'raw_evidence_frozen_before_derived_analysis': True,
        'semantic_status': 'NOT_ADJUDICATED',
    }
    for trace in traces:
        status = trace.get('run_status')
        record['run_status_counts'][status] = record['run_status_counts'].get(status, 0) + 1
    record['evidence_batch_hash'] = stable_hash(record)
    Path(args.out).write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print('PROSPECTIVE_EVIDENCE_FROZEN=YES')
    print('EVIDENCE_BATCH_HASH=' + record['evidence_batch_hash'])


if __name__ == '__main__':
    main()
