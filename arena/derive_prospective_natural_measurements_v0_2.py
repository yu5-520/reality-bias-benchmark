#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .io_utils import load_json, load_jsonl, write_jsonl
from .process_reality_dynamics_v0_2 import build_process_reality_measurement
from .system_behavior_adapter import adapt_arena_trace_v03
from .system_behavior_dynamics_v4 import build_system_dynamics_view
from .system_behavior_lineage_v4 import build_system_lineage_view


def derive(*, raw_dir, evidence_batch_path):
    raw = Path(raw_dir)
    evidence = load_json(evidence_batch_path)
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
            'measurement_derivation_version': 'v0.2_SOURCE_REF_BOUND_ROOT',
        }
        if selection.get('selection_status') == 'ANCHOR_SELECTED':
            candidate = selection['selected_candidate']
            snapshot = selection['selected_snapshot']
            state_key = (candidate.get('structural_facts') or {}).get('state_key')
            measurement = build_process_reality_measurement(
                trace=trace,
                adapter_result=adapted,
                dynamics_view=dynamics,
                lineage_view=lineage,
                target_source_event_index=candidate['event_index'],
                target_state_key=state_key,
                target_candidate_id=candidate.get('candidate_id'),
                branch_start_turn=snapshot['turns'],
            )
            measurement.update(base)
            measurements.append(measurement)
            base['mechanism_measurement_status'] = measurement['mechanism_measurement_status']
            base['root_resolution_status'] = measurement['root_resolution']['status']
            base['target_root_behavior_event_id'] = measurement['target_root_behavior_event_id']
        else:
            base['mechanism_measurement_status'] = 'NO_SELECTED_NATURAL_JUMP_MECHANISM_VIEW'
            base['root_resolution_status'] = 'NOT_APPLICABLE'
            base['target_root_behavior_event_id'] = None
        index.append(base)
    return traces, measurements, index, evidence


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--raw-dir', required=True)
    ap.add_argument('--evidence-batch', required=True)
    ap.add_argument('--outdir', required=True)
    args = ap.parse_args()
    out = Path(args.outdir)
    if out.exists():
        raise ValueError('refusing_to_overwrite_prospective_measurements_v02')
    out.mkdir(parents=True)
    traces, measurements, index, evidence = derive(raw_dir=args.raw_dir, evidence_batch_path=args.evidence_batch)
    write_jsonl(out / 'prospective_process_measurements_v0.2.jsonl', measurements)
    write_jsonl(out / 'prospective_measurement_index_v0.2.jsonl', index)
    resolved = sum(1 for x in measurements if (x.get('root_resolution') or {}).get('status') == 'RESOLVED_EXACT_SOURCE_EVENT')
    unresolved = len(measurements) - resolved
    summary = {
        'schema': 'RB-PROSPECTIVE-NATURAL-MEASUREMENT-SUMMARY-v0.2',
        'evidence_batch_hash': evidence['evidence_batch_hash'],
        'trace_count': len(traces),
        'selected_jump_measurement_count': len(measurements),
        'resolved_selected_jump_root_count': resolved,
        'unresolved_selected_jump_root_count': unresolved,
        'root_binding_rule': 'ARENA_SOURCE_REF_PLUS_SELECTED_STATE_KEY',
        'semantic_status': 'NOT_ADJUDICATED',
        'paid_evaluator_called': False,
        'new_subject_provider_call': False,
        'supersedes_derived_measurement_only': 'v0.1_event_index_equality_binding',
        'raw_evidence_changed': False,
    }
    (out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('PROSPECTIVE_STRUCTURAL_MEASUREMENTS_V02=' + str(len(measurements)))
    print('RESOLVED_SELECTED_JUMP_ROOTS=' + str(resolved))
    print('UNRESOLVED_SELECTED_JUMP_ROOTS=' + str(unresolved))
    print('NEW_PROVIDER_CALL=NO')


if __name__ == '__main__':
    main()
