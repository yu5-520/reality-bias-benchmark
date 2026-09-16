#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .branch_plan_one_shot import verify_one_shot_branch_plan
from .io_utils import load_json, load_jsonl, write_jsonl
from .process_reality_dynamics_v0_4 import build_process_reality_measurement, compare_process_reality
from .system_behavior_adapter import adapt_arena_trace_v03
from .system_behavior_dynamics_v4 import build_system_dynamics_view
from .system_behavior_lineage_v4 import build_system_lineage_view


def load_plan_bundle(plan_dir):
    p = Path(plan_dir)
    bundle = {
        'plan': load_json(p / 'branch_plan.json'),
        'parent_snapshot': load_json(p / 'parent_snapshot.json'),
        'one_shot_envelope': load_json(p / 'one_shot_intervention_envelope.json'),
        'branch_rows': load_jsonl(p / 'branch_execution_manifest.jsonl'),
        'branch_manifests': load_jsonl(p / 'branch_manifests.jsonl'),
    }
    verify_one_shot_branch_plan(bundle)
    return bundle


def _exposure_integrity(trace, row):
    records = [x for x in trace.get('runtime_transform_records') or [] if x.get('experiment_origin') is True]
    expected = 1 if row['condition_id'] == 'ONE_SHOT_JUMP_INTERVENTION' else 0
    failures = []
    if len(records) != expected:
        failures.append({
            'run_id': trace.get('run_id'),
            'type': 'DIRECT_EXPOSURE_COUNT_MISMATCH',
            'expected': expected,
            'observed': len(records),
        })
    if records:
        if any(x.get('persistent_state_mutation') is not False for x in records):
            failures.append({'run_id': trace.get('run_id'), 'type': 'PERSISTENT_EXPERIMENT_STATE_MUTATION_OBSERVED'})
        if any(x.get('consumed_after_delivery') is not True for x in records):
            failures.append({'run_id': trace.get('run_id'), 'type': 'EXPERIMENT_OVERLAY_NOT_CONSUMED'})
    summary = trace.get('one_shot_intervention_summary') or {}
    if row['condition_id'] == 'ONE_SHOT_JUMP_INTERVENTION':
        if summary and summary.get('experiment_origin_reinjection_count') not in (0, None):
            failures.append({'run_id': trace.get('run_id'), 'type': 'EXPERIMENT_ORIGIN_REINJECTION_OBSERVED'})
        if summary and summary.get('persistent_state_mutation') not in (False, None):
            failures.append({'run_id': trace.get('run_id'), 'type': 'TRANSFORM_SUMMARY_PERSISTENT_MUTATION'})
    return failures


def derive(plan_dir, traces_path, evidence_batch_path):
    bundle = load_plan_bundle(plan_dir)
    evidence = load_json(evidence_batch_path)
    if evidence.get('raw_evidence_frozen_before_derived_analysis') is not True:
        raise ValueError('one_shot_raw_evidence_must_be_frozen_before_derivation')
    if evidence.get('plan_hash') != bundle['plan']['plan_hash']:
        raise ValueError('one_shot_evidence_plan_hash_mismatch')
    traces = load_jsonl(traces_path)
    rows = {x['run_id']: x for x in bundle['branch_rows']}
    measurements = []
    by_run = {}
    integrity_failures = []
    target = bundle['plan']['common_identity']
    state_key = target.get('state_key')

    for trace in traces:
        row = rows.get(trace.get('run_id'))
        if row is None:
            raise ValueError('trace_not_in_one_shot_plan:' + str(trace.get('run_id')))
        integrity_failures.extend(_exposure_integrity(trace, row))
        adapted = adapt_arena_trace_v03(trace)
        dynamics = build_system_dynamics_view(adapted)
        lineage = build_system_lineage_view(adapted, dynamics_view=dynamics)
        measurement = build_process_reality_measurement(
            trace=trace,
            adapter_result=adapted,
            dynamics_view=dynamics,
            lineage_view=lineage,
            target_source_event_index=target['selected_candidate_event_index'],
            target_state_key=state_key,
            target_candidate_id=target.get('selected_candidate_id'),
            branch_start_turn=bundle['parent_snapshot']['turns'],
        )
        measurement.update({
            'pair_id': row['pair_id'],
            'condition_id': row['condition_id'],
            'replicate_index': row['replicate_index'],
            'execution_order': row['execution_order'],
            'pair_order_pattern': row['pair_order_pattern'],
            'source_raw_evidence_batch_hash': evidence['evidence_batch_hash'],
            'semantic_status': 'NOT_ADJUDICATED',
        })
        measurements.append(measurement)
        by_run[trace['run_id']] = measurement

    comparisons = []
    pair_index = []
    for pair_id in sorted({x['pair_id'] for x in bundle['branch_rows']}):
        pair_rows = [x for x in bundle['branch_rows'] if x['pair_id'] == pair_id]
        control_row = next(x for x in pair_rows if x['condition_id'] == 'CONTROL_CONTINUATION')
        intervention_row = next(x for x in pair_rows if x['condition_id'] == 'ONE_SHOT_JUMP_INTERVENTION')
        control = by_run.get(control_row['run_id'])
        intervention = by_run.get(intervention_row['run_id'])
        pair_failure_ids = {control_row['run_id'], intervention_row['run_id']}
        exposure_ok = not any(x['run_id'] in pair_failure_ids for x in integrity_failures)
        roots_ok = bool(
            control and intervention
            and control.get('mechanism_measurement_status') == 'ROOT_RESOLVED'
            and intervention.get('mechanism_measurement_status') == 'ROOT_RESOLVED'
        )
        statuses_ok = bool(control and intervention and control.get('run_status') == intervention.get('run_status') == 'RUN_COMPLETE')

        pair_record = {
            'pair_id': pair_id,
            'control_run_id': control_row['run_id'],
            'intervention_run_id': intervention_row['run_id'],
            'control_run_status': control.get('run_status') if control else 'MISSING_TRACE',
            'intervention_run_status': intervention.get('run_status') if intervention else 'MISSING_TRACE',
            'root_resolution_ok': roots_ok,
            'exposure_integrity_ok': exposure_ok,
            'comparison_generated': False,
            'semantic_status': 'NOT_ADJUDICATED',
        }

        if roots_ok and statuses_ok and exposure_ok:
            comparison = compare_process_reality(control, intervention, comparison_id=pair_id + ':PROCESS_REALITY:v0.4')
            control_paths = ((control.get('root_descendant_topology') or {}).get('observed_path_families') or {})
            intervention_paths = ((intervention.get('root_descendant_topology') or {}).get('observed_path_families') or {})
            control_overflow = bool(control_paths.get('path_family_overflow'))
            intervention_overflow = bool(intervention_paths.get('path_family_overflow'))
            comparison['pair_id'] = pair_id
            comparison['source_raw_evidence_batch_hash'] = evidence['evidence_batch_hash']
            comparison['path_family_completeness'] = {
                'control_overflow': control_overflow,
                'intervention_overflow': intervention_overflow,
                'status': 'COMPLETE_WITHIN_FROZEN_CAP' if not (control_overflow or intervention_overflow) else 'PARTIAL_CAP_CENSORED',
                'claim_rule': 'Do not claim a complete observed path-family set for a branch with path_family_overflow=true.',
            }
            comparisons.append(comparison)
            pair_record['comparison_generated'] = True
            pair_record['pair_status'] = 'COMPLETE_ROOT_RESOLVED_THREE_LAYER_PAIR'
            pair_record['path_family_completeness_status'] = comparison['path_family_completeness']['status']
        elif control and intervention:
            pair_record['pair_status'] = 'PRESERVED_NONCOMPARABLE_OR_CENSORED_PAIR'
            pair_record['path_family_completeness_status'] = 'NOT_COMPARED'
        else:
            pair_record['pair_status'] = 'INCOMPLETE_TRACE_PAIR'
            pair_record['path_family_completeness_status'] = 'NOT_COMPARED'
        pair_index.append(pair_record)

    return measurements, comparisons, pair_index, integrity_failures, evidence


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--plan-dir', required=True)
    ap.add_argument('--traces', required=True)
    ap.add_argument('--evidence-batch', required=True)
    ap.add_argument('--outdir', required=True)
    args = ap.parse_args()
    out = Path(args.outdir)
    if out.exists():
        raise ValueError('refusing_to_overwrite_process_measurement_v04_dir')
    out.mkdir(parents=True)
    measurements, comparisons, pair_index, integrity_failures, evidence = derive(
        args.plan_dir, args.traces, args.evidence_batch
    )
    write_jsonl(out / 'process_reality_measurements_v0.4.jsonl', measurements)
    write_jsonl(out / 'paired_process_comparisons_v0.4.jsonl', comparisons)
    write_jsonl(out / 'pair_index_v0.4.jsonl', pair_index)
    write_jsonl(out / 'integrity_failures.jsonl', integrity_failures)
    summary = {
        'schema': 'RB-PROCESS-REALITY-DERIVATION-SUMMARY-v0.4',
        'source_raw_evidence_batch_hash': evidence['evidence_batch_hash'],
        'measurement_count': len(measurements),
        'complete_pair_comparison_count': len(comparisons),
        'pair_count': len(pair_index),
        'integrity_failure_count': len(integrity_failures),
        'measurement_layers': ['JUMP_RECURRENCE', 'INHERITED_INERTIA', 'PATH_TOPOLOGY'],
        'topology_scope': 'ROOT_DESCENDANT_PRIMARY_FULL_POST_CONTEXT_SECONDARY',
        'path_family_cap': 4096,
        'semantic_status': 'NOT_ADJUDICATED',
        'paid_evaluator_called': False,
        'terminal_outcome_is_primary': False,
    }
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print('PROCESS_REALITY_MEASUREMENTS_V04=' + str(len(measurements)))
    print('PAIRED_COMPARISONS_V04=' + str(len(comparisons)))
    print('INTEGRITY_FAILURES=' + str(len(integrity_failures)))


if __name__ == '__main__':
    main()
