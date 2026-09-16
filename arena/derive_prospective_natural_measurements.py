#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .io_utils import load_json, load_jsonl, write_jsonl
from .process_reality_dynamics_v0_1 import build_process_reality_measurement
from .system_behavior_adapter import adapt_arena_trace_v03
from .system_behavior_dynamics_v4 import build_system_dynamics_view
from .system_behavior_lineage_v4 import build_system_lineage_view


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--raw-dir', required=True)
    ap.add_argument('--evidence-batch', required=True)
    ap.add_argument('--outdir', required=True)
    args = ap.parse_args()
    raw = Path(args.raw_dir)
    out = Path(args.outdir)
    if out.exists():
        raise ValueError('refusing_to_overwrite_prospective_measurements')
    out.mkdir(parents=True)
    evidence = load_json(args.evidence_batch)
    if evidence.get('raw_evidence_frozen_before_derived_analysis') is not True:
        raise ValueError('prospective_raw_freeze_required_before_derivation')
    traces = load_jsonl(raw / 'traces.jsonl')
    measurements = []
    index = []
    for trace in traces:
        run_id = trace['run_id']
        selection_path = raw / 'selection_packages' / f'{run_id}.json'
        selection = load_json(selection_path) if selection_path.exists() else {'selection_status': 'MISSING_SELECTION_PACKAGE'}
        adapted = adapt_arena_trace_v03(trace)
        dynamics = build_system_dynamics_view(adapted)
        lineage = build_system_lineage_view(adapted, dynamics_view=dynamics)
        base = {
            'trajectory_id': run_id,
            'run_status': trace.get('run_status'),
            'selection_status': selection.get('selection_status'),
            'jump_candidate_count': len(dynamics.get('jump_candidates') or []),
            'structural_lineage_relation_count': len(lineage.get('lineage_relations') or []),
            'semantic_status': 'NOT_ADJUDICATED',
            'evidence_batch_hash': evidence['evidence_batch_hash'],
        }
        if selection.get('selection_status') == 'ANCHOR_SELECTED':
            candidate = selection['selected_candidate']
            snapshot = selection['selected_snapshot']
            measurement = build_process_reality_measurement(
                trace=trace,
                adapter_result=adapted,
                dynamics_view=dynamics,
                lineage_view=lineage,
                target_source_event_index=candidate['event_index'],
                branch_start_turn=snapshot['turns'],
            )
            measurement.update(base)
            measurements.append(measurement)
            base['mechanism_measurement_status'] = 'DERIVED_FROM_SELECTED_NATURAL_JUMP'
        else:
            base['mechanism_measurement_status'] = 'NO_SELECTED_NATURAL_JUMP_MECHANISM_VIEW'
        index.append(base)
    write_jsonl(out / 'prospective_process_measurements.jsonl', measurements)
    write_jsonl(out / 'prospective_measurement_index.jsonl', index)
    summary = {
        'schema': 'RB-PROSPECTIVE-NATURAL-MEASUREMENT-SUMMARY-v0.1',
        'evidence_batch_hash': evidence['evidence_batch_hash'],
        'trace_count': len(traces),
        'selected_jump_measurement_count': len(measurements),
        'semantic_status': 'NOT_ADJUDICATED',
        'paid_evaluator_called': False,
    }
    (out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('PROSPECTIVE_STRUCTURAL_MEASUREMENTS=' + str(len(measurements)))
    print('PAID_EVALUATOR_CALLED=NO')


if __name__ == '__main__':
    main()
