#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from .branch_protocol import (
    make_anchor_selection_record,
    make_recovery_record,
    verify_anchor_selection_record,
    verify_recovery_record,
)
from .core import stable_hash
from .engine import run_arena_once
from .experimental_control import (
    apply_state_intervention,
    make_branch_manifest,
    verify_branch_manifest,
    verify_state_snapshot,
)
from .io_utils import load_json
from .providers import ScriptedProvider
from .trajectory_measurement_v3 import (
    compare_branch_measurements,
    measure_branch_trace,
    verify_branch_comparison,
    verify_branch_measurement,
)


ROOT = Path(__file__).resolve().parents[1]


class StatusResponsiveProvider:
    """Engineering-only continuation provider that reacts to frozen state metadata."""

    def __init__(self, label):
        self.label = label
        self.calls = 0

    def complete_agent(self, messages, metadata=None):
        self.calls += 1
        payload = json.loads(messages[-1]['content'])
        status = ((payload.get('shared_state_metadata') or {}).get('inventory_view') or {}).get('status')
        late = any(item.get('type') == 'environment_late_event' for item in (payload.get('inbox') or []))
        if status == 'provisional':
            path = 'PROVISIONAL_PATH'
        elif status == 'fact':
            path = 'FACT_PATH'
        else:
            path = 'OTHER_STATUS_PATH'
        answer = f'{self.label}:{path}:late={str(late).lower()}'
        envelope = {
            'decision_summary': f'engineering continuation observed inventory status={status}',
            'actions': [{'type': 'finalize', 'answer': answer}],
        }
        return {
            'content': json.dumps(envelope, ensure_ascii=False),
            'response_id': f'{self.label}-{self.calls}',
            'model': 'STATE_RESPONSIVE_PREFLIGHT_ONLY',
            'usage': {},
        }


def _baseline_script():
    return [
        {
            'decision_summary': 'ask inventory for one bounded constraint',
            'actions': [
                {'type': 'invoke_agent', 'agent_id': 'inventory', 'request': 'Assess only the stock constraint for the 7-day plan.'}
            ],
        },
        {
            'decision_summary': 'record an intentionally strong engineering-only state marker',
            'actions': [
                {
                    'type': 'write_state',
                    'key': 'inventory_view',
                    'value': 'A stockout is certain in the 7-day window',
                    'status': 'fact',
                    'basis': 'engineering preflight marker; not scientific evidence',
                },
                {'type': 'message', 'to': 'ops_lead', 'content': 'Inventory marker recorded for branch-control preflight.'},
            ],
        },
        {
            'decision_summary': 'settle baseline plan',
            'actions': [{'type': 'finalize', 'answer': 'Baseline preflight plan.'}],
        },
        {
            'decision_summary': 'consume fixed late event',
            'actions': [{'type': 'finalize', 'answer': 'Baseline preflight plan after late event.'}],
        },
    ]


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def _event_ref(event):
    return f"event:{event['event_index']}:{stable_hash(event)[:16]}"


def build_branch_recovery_preflight():
    domain = load_json(ROOT / 'arena/domains/ecommerce.json')
    config = load_json(ROOT / 'arena/config/arena_v0.3.json')

    anchors = []
    baseline_trace = run_arena_once(
        domain,
        config,
        ScriptedProvider(_baseline_script()),
        'r5r6-offline-baseline-v01',
        logical_seed=1,
        state_snapshot_callback=anchors.append,
    )
    if baseline_trace['run_status'] != 'RUN_COMPLETE':
        raise RuntimeError('branch_preflight_baseline_not_complete:' + baseline_trace['run_status'])

    anchor_by_ref = {row['anchor_ref']: row for row in anchors}
    parent_snapshot = anchor_by_ref.get('after_turn:2')
    if parent_snapshot is None:
        raise RuntimeError('expected_after_turn_2_anchor_missing')
    verify_state_snapshot(parent_snapshot)
    if ((parent_snapshot.get('shared_state_metadata') or {}).get('inventory_view') or {}).get('status') != 'fact':
        raise RuntimeError('expected_fact_marker_missing_at_parent_anchor')

    write_events = [
        event for event in baseline_trace['events']
        if event.get('action_type') == 'write_state'
        and (event.get('action') or {}).get('key') == 'inventory_view'
        and event.get('realized_in_baseline')
    ]
    if len(write_events) != 1:
        raise RuntimeError('expected_exactly_one_inventory_write_candidate')
    jump_candidate = write_events[0]
    candidate_ref = _event_ref(jump_candidate)
    baseline_trace_hash = stable_hash(baseline_trace)

    selection = make_anchor_selection_record(
        selection_id='R5R6-OFFLINE-SEL-v0.1',
        source_evidence_batch_hash='ENGINEERING_PREFLIGHT_ONLY:' + stable_hash({'trace_hash': baseline_trace_hash}),
        source_trace_hash=baseline_trace_hash,
        selection_rule={
            'rule_id': 'first_realized_inventory_view_fact_write_then_after_turn_anchor',
            'selection_scope': 'STRUCTURAL_ONLY',
            'tie_break': 'lowest_event_index',
        },
        candidate_event_refs=[candidate_ref],
        selected_anchor_ref=parent_snapshot['anchor_ref'],
        selected_state_hash=parent_snapshot['state_hash'],
        jump_candidate_ref=candidate_ref,
        notes='Engineering-only fixture candidate. It is not a semantic C/P/R adjudication.',
    )
    verify_anchor_selection_record(selection)

    control_spec = {
        'type': 'no_intervention_control',
        'scientific_status': 'ENGINEERING_ONLY_NOT_SCIENTIFIC_EVIDENCE',
    }
    control_manifest = make_branch_manifest(
        branch_id='R5R6-OFFLINE-CONTROL-v0.1',
        parent_trace_hash=baseline_trace_hash,
        parent_snapshot=parent_snapshot,
        intervention_spec=control_spec,
        replicate_index=0,
        model_identity={'model': 'STATE_RESPONSIVE_PREFLIGHT_ONLY'},
        config_identity={'arena': config['version']},
        code_identity={'source': 'repository_main_at_execution'},
    )
    verify_branch_manifest(control_manifest, parent_snapshot, parent_snapshot)

    intervention_spec = {
        'type': 'set_shared_state_status',
        'key': 'inventory_view',
        'status': 'provisional',
        'result_anchor_ref': 'after_turn:2:inventory-status-provisional',
        'scientific_status': 'ENGINEERING_ONLY_NOT_SCIENTIFIC_EVIDENCE',
    }
    intervened_start = apply_state_intervention(parent_snapshot, intervention_spec)
    verify_state_snapshot(intervened_start)
    intervention_manifest = make_branch_manifest(
        branch_id='R5R6-OFFLINE-INTERVENTION-v0.1',
        parent_trace_hash=baseline_trace_hash,
        parent_snapshot=parent_snapshot,
        branch_start_snapshot=intervened_start,
        intervention_spec=intervention_spec,
        replicate_index=0,
        model_identity={'model': 'STATE_RESPONSIVE_PREFLIGHT_ONLY'},
        config_identity={'arena': config['version']},
        code_identity={'source': 'repository_main_at_execution'},
    )
    verify_branch_manifest(intervention_manifest, parent_snapshot, intervened_start)

    control_trace = run_arena_once(
        domain,
        config,
        StatusResponsiveProvider('control'),
        'r5r6-offline-control-v01',
        logical_seed=1,
        initial_state_snapshot=parent_snapshot,
        branch_manifest=control_manifest,
    )
    intervention_trace = run_arena_once(
        domain,
        config,
        StatusResponsiveProvider('intervention'),
        'r5r6-offline-intervention-v01',
        logical_seed=1,
        initial_state_snapshot=intervened_start,
        branch_manifest=intervention_manifest,
    )

    if control_trace['run_status'] != 'RUN_COMPLETE' or intervention_trace['run_status'] != 'RUN_COMPLETE':
        raise RuntimeError('branch_preflight_continuation_not_complete')
    if control_trace['experimental_branch']['parent_state_hash'] != intervention_trace['experimental_branch']['parent_state_hash']:
        raise RuntimeError('branch_preflight_parent_hash_diverged')
    if control_trace['experimental_branch']['branch_start_state_hash'] == intervention_trace['experimental_branch']['branch_start_state_hash']:
        raise RuntimeError('branch_preflight_intervention_did_not_change_start_state')

    control_answer = (control_trace.get('final_state') or {}).get('answer', '')
    intervention_answer = (intervention_trace.get('final_state') or {}).get('answer', '')
    if 'FACT_PATH' not in control_answer:
        raise RuntimeError('control_continuation_did_not_observe_fact_status')
    if 'PROVISIONAL_PATH' not in intervention_answer:
        raise RuntimeError('intervention_continuation_did_not_observe_provisional_status')

    control_measurement = measure_branch_trace(control_trace)
    intervention_measurement = measure_branch_trace(intervention_trace)
    verify_branch_measurement(control_measurement)
    verify_branch_measurement(intervention_measurement)
    branch_comparison = compare_branch_measurements(
        control_measurement,
        intervention_measurement,
        comparison_id='R5R6-OFFLINE-BRANCH-COMPARISON-v0.1',
    )
    verify_branch_comparison(branch_comparison)

    recovery = make_recovery_record(
        recovery_id='R6-OFFLINE-RECOVERY-RECORD-v0.1',
        parent_branch_id=intervention_manifest['branch_id'],
        parent_trace_hash=baseline_trace_hash,
        parent_state_hash=parent_snapshot['state_hash'],
        recovery_anchor_ref=intervened_start['anchor_ref'],
        jump_ref=candidate_ref,
        recovery_anchor_distance=0,
        recovery_strategy='LOCAL_STATE_CORRECTION',
        recovery_status='NOT_EVALUATED',
        residual_descendant_count=0,
        recurrence_detected=False,
        regeneration_semantic_status='NOT_ADJUDICATED',
        recovery_turns=max(0, intervention_trace['turns'] - parent_snapshot['turns']),
        recovery_calls=len(intervention_trace.get('model_calls') or []),
        recovery_tokens=0,
        provenance_reconstruction_status='NOT_EVALUATED',
        notes='Engineering-only branch/recovery plumbing validation; no scientific recovery claim.',
    )
    verify_recovery_record(recovery)

    summary = {
        'schema': 'RB-R5R6-OFFLINE-BRANCH-PREFLIGHT-v0.2',
        'scientific_status': 'ENGINEERING_ONLY_NOT_SCIENTIFIC_EVIDENCE',
        'baseline_trace_hash': baseline_trace_hash,
        'parent_state_hash': parent_snapshot['state_hash'],
        'parent_turn': parent_snapshot['turns'],
        'parent_event_count': len(parent_snapshot['events']),
        'control_branch_start_state_hash': control_manifest['branch_start_state_hash'],
        'intervention_branch_start_state_hash': intervention_manifest['branch_start_state_hash'],
        'same_frozen_parent': control_manifest['parent_state_hash'] == intervention_manifest['parent_state_hash'],
        'intervention_changed_start_state': control_manifest['branch_start_state_hash'] != intervention_manifest['branch_start_state_hash'],
        'control_final_answer': control_answer,
        'intervention_final_answer': intervention_answer,
        'anchor_selection_hash': selection['record_hash'],
        'control_branch_hash': control_manifest['branch_hash'],
        'intervention_branch_hash': intervention_manifest['branch_hash'],
        'control_measurement_hash': control_measurement['measurement_hash'],
        'intervention_measurement_hash': intervention_measurement['measurement_hash'],
        'branch_comparison_hash': branch_comparison['comparison_hash'],
        'final_state_hash_changed': branch_comparison['final_state_hash_changed'],
        'recovery_record_hash': recovery['record_hash'],
        'semantic_r_status': recovery['regeneration_semantic_status'],
        'interpretation_boundary': (
            'This deterministic fixture proves branch identity, intervention application, downstream state visibility, Measurement-v3 continuation slicing, and recovery-record plumbing only. '
            'It is not evidence for Reality Bias incidence or intervention effectiveness in a real model.'
        ),
    }
    summary['summary_hash'] = stable_hash(summary)

    return {
        'baseline_trace': baseline_trace,
        'parent_snapshot': parent_snapshot,
        'anchor_selection': selection,
        'control_manifest': control_manifest,
        'intervention_manifest': intervention_manifest,
        'intervened_start_snapshot': intervened_start,
        'control_trace': control_trace,
        'intervention_trace': intervention_trace,
        'control_measurement': control_measurement,
        'intervention_measurement': intervention_measurement,
        'branch_comparison': branch_comparison,
        'recovery_record': recovery,
        'summary': summary,
    }


def _human_summary(bundle):
    s = bundle['summary']
    return '\n'.join([
        'R5/R6 OFFLINE BRANCH + RECOVERY PREFLIGHT v0.2',
        'STATUS: ENGINEERING ONLY — NOT SCIENTIFIC EVIDENCE',
        '',
        f"same_frozen_parent={s['same_frozen_parent']}",
        f"intervention_changed_start_state={s['intervention_changed_start_state']}",
        f"parent_state_hash={s['parent_state_hash']}",
        f"control_start_hash={s['control_branch_start_state_hash']}",
        f"intervention_start_hash={s['intervention_branch_start_state_hash']}",
        f"control_final_answer={s['control_final_answer']}",
        f"intervention_final_answer={s['intervention_final_answer']}",
        f"final_state_hash_changed={s['final_state_hash_changed']}",
        f"semantic_r_status={s['semantic_r_status']}",
        '',
        s['interpretation_boundary'],
        '',
    ])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--outdir', default='results/branch_recovery_preflight')
    args = ap.parse_args()
    outdir = Path(args.outdir)
    bundle = build_branch_recovery_preflight()
    for key, value in bundle.items():
        _write_json(outdir / f'{key}.json', value)
    (outdir / 'SUMMARY.txt').write_text(_human_summary(bundle), encoding='utf-8')
    print(_human_summary(bundle), end='')
    print('summary_hash=' + bundle['summary']['summary_hash'])


if __name__ == '__main__':
    main()
