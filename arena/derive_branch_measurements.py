#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from .core import stable_hash
from .io_utils import load_json, load_jsonl, write_jsonl
from .run_branch_real import load_plan_bundle
from .trajectory_measurement_v3 import (
    compare_branch_measurements,
    measure_branch_trace,
    verify_branch_comparison,
    verify_branch_measurement,
)


VALID_PAIR_STATUSES = {'RUN_COMPLETE'}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def derive_bundle(*, plan_dir, traces_path, evidence_batch_path):
    plan_bundle = load_plan_bundle(plan_dir)
    traces = load_jsonl(traces_path)
    evidence = load_json(evidence_batch_path)
    evidence_hash = evidence.get('evidence_batch_hash')
    _require(evidence_hash and isinstance(evidence_hash, str), 'evidence_batch_hash_required')

    rows_by_run = {row['run_id']: row for row in plan_bundle['branch_rows']}
    _require(len(rows_by_run) == len(plan_bundle['branch_rows']), 'duplicate_branch_plan_run_id')
    _require(len({trace['run_id'] for trace in traces}) == len(traces), 'duplicate_branch_trace_run_id')

    measurements = []
    traces_by_pair = {}
    measurement_by_run = {}
    for trace in traces:
        row = rows_by_run.get(trace.get('run_id'))
        _require(row is not None, 'trace_not_present_in_branch_plan:' + str(trace.get('run_id')))
        branch = trace.get('experimental_branch') or {}
        _require(branch.get('branch_hash') == row.get('branch_hash'), 'trace_branch_hash_mismatch:' + trace['run_id'])
        _require(branch.get('parent_state_hash') == row.get('parent_state_hash'), 'trace_parent_state_hash_mismatch:' + trace['run_id'])
        _require(branch.get('branch_start_state_hash') == row.get('branch_start_state_hash'), 'trace_branch_start_hash_mismatch:' + trace['run_id'])
        _require(trace.get('branch_plan_hash') == plan_bundle['plan']['plan_hash'], 'trace_branch_plan_hash_mismatch:' + trace['run_id'])

        measurement = measure_branch_trace(trace, evidence_batch_hash=evidence_hash)
        verify_branch_measurement(measurement)
        measurement.update({
            'pair_id': row['pair_id'],
            'replicate_index': row['replicate_index'],
            'condition_id': row['condition_id'],
            'pair_order_pattern': row['pair_order_pattern'],
            'execution_order': row['execution_order'],
            'branch_plan_hash': plan_bundle['plan']['plan_hash'],
        })
        # Rebind the hash after adding branch-plan/pair identity.
        material = dict(measurement)
        material.pop('measurement_hash', None)
        measurement['measurement_hash'] = stable_hash(material)
        verify_branch_measurement(measurement)
        measurements.append(measurement)
        measurement_by_run[trace['run_id']] = measurement
        traces_by_pair.setdefault(row['pair_id'], {})[row['condition_id']] = trace

    comparisons = []
    pair_index = []
    expected_pairs = sorted({row['pair_id'] for row in plan_bundle['branch_rows']})
    for pair_id in expected_pairs:
        rows = [row for row in plan_bundle['branch_rows'] if row['pair_id'] == pair_id]
        by_condition_row = {row['condition_id']: row for row in rows}
        pair_traces = traces_by_pair.get(pair_id, {})
        control_trace = pair_traces.get('CONTROL_CONTINUATION')
        intervention_trace = pair_traces.get('STATUS_DOWNGRADE_INTERVENTION')
        if control_trace is None or intervention_trace is None:
            pair_index.append({
                'pair_id': pair_id,
                'pair_status': 'PAIR_INCOMPLETE_MISSING_TRACE',
                'recorded_conditions': sorted(pair_traces),
            })
            continue
        if control_trace.get('run_status') not in VALID_PAIR_STATUSES or intervention_trace.get('run_status') not in VALID_PAIR_STATUSES:
            pair_index.append({
                'pair_id': pair_id,
                'pair_status': 'PAIR_INCOMPLETE_NONCOMPLETE_TRACE',
                'control_run_status': control_trace.get('run_status'),
                'intervention_run_status': intervention_trace.get('run_status'),
            })
            continue

        control_row = by_condition_row['CONTROL_CONTINUATION']
        intervention_row = by_condition_row['STATUS_DOWNGRADE_INTERVENTION']
        control_measurement = measurement_by_run[control_row['run_id']]
        intervention_measurement = measurement_by_run[intervention_row['run_id']]
        comparison = compare_branch_measurements(
            control_measurement,
            intervention_measurement,
            comparison_id=pair_id,
        )
        comparison.update({
            'evidence_batch_hash': evidence_hash,
            'branch_plan_hash': plan_bundle['plan']['plan_hash'],
            'replicate_index': control_row['replicate_index'],
            'pair_order_pattern': control_row['pair_order_pattern'],
            'control_run_id': control_row['run_id'],
            'intervention_run_id': intervention_row['run_id'],
        })
        material = dict(comparison)
        material.pop('comparison_hash', None)
        comparison['comparison_hash'] = stable_hash(material)
        verify_branch_comparison(comparison)
        comparisons.append(comparison)
        pair_index.append({
            'pair_id': pair_id,
            'pair_status': 'PAIR_MEASURED_STRUCTURALLY',
            'comparison_hash': comparison['comparison_hash'],
            'semantic_status': 'NOT_ADJUDICATED',
        })

    summary = {
        'schema': 'RB-R5R6-BRANCH-MEASUREMENT-SUMMARY-v0.1',
        'measurement_version': 'RB-TRAJECTORY-MEASUREMENT-v3.0.1',
        'evidence_batch_hash': evidence_hash,
        'branch_plan_hash': plan_bundle['plan']['plan_hash'],
        'planned_branch_runs': len(plan_bundle['branch_rows']),
        'preserved_branch_traces': len(traces),
        'measurement_record_count': len(measurements),
        'planned_pair_count': len(expected_pairs),
        'structurally_measured_pair_count': len(comparisons),
        'pair_index': pair_index,
        'semantic_review': 'DEFERRED_APPEND_ONLY',
        'C_P_R_status': 'NOT_ADJUDICATED',
        'authority_penetration_status': 'NOT_ADJUDICATED',
        'causal_effect_status': 'NOT_ADJUDICATED',
        'warning': (
            'These records are deterministic continuation measurements over frozen branch evidence. '
            'Structural deltas do not by themselves establish C/P/R, Authority Penetration, recovery, or a general causal effect.'
        ),
    }
    summary['summary_hash'] = stable_hash(summary)
    return measurements, comparisons, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--plan-dir', required=True)
    ap.add_argument('--traces', required=True)
    ap.add_argument('--evidence-batch', required=True)
    ap.add_argument('--outdir', required=True)
    args = ap.parse_args()

    measurements, comparisons, summary = derive_bundle(
        plan_dir=args.plan_dir,
        traces_path=args.traces,
        evidence_batch_path=args.evidence_batch,
    )
    out = Path(args.outdir)
    if out.exists():
        raise ValueError('refusing_to_overwrite_branch_measurement_outdir')
    out.mkdir(parents=True, exist_ok=False)
    write_jsonl(out / 'branch_measurements.jsonl', measurements)
    write_jsonl(out / 'pair_comparisons.jsonl', comparisons)
    (out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(
        f"derived {len(measurements)} branch measurements and {len(comparisons)} complete pair comparisons; "
        'semantic_review=DEFERRED_APPEND_ONLY'
    )


if __name__ == '__main__':
    main()
