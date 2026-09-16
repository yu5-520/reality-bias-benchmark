import copy
from collections import Counter

from .core import stable_hash
from .measurement_v2 import build_r2_candidate_index


VERSION = 'RB-TRAJECTORY-MEASUREMENT-v3.0.1'
BRANCH_RECORD_SCHEMA = 'RB-BRANCH-TRAJECTORY-MEASUREMENT-v3.0.1'
BRANCH_COMPARISON_SCHEMA = 'RB-BRANCH-TRAJECTORY-COMPARISON-v3.0.1'
NOT_ADJUDICATED = 'NOT_ADJUDICATED'


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _hash_record(record, hash_key):
    material = copy.deepcopy(record)
    material.pop(hash_key, None)
    return stable_hash(material)


def _count_action_types(events):
    counts = Counter()
    for event in events:
        counts[str(event.get('action_type'))] += 1
    return dict(sorted(counts.items()))


def _count_candidate_types(candidates):
    counts = Counter()
    for row in candidates:
        for candidate_type in row.get('candidate_types') or []:
            counts[candidate_type] += 1
    return dict(sorted(counts.items()))


def measure_branch_trace(trace, *, evidence_batch_hash=None):
    """Derive deterministic continuation-only structure from one branch trace.

    This is deliberately not a C/P/R classifier and does not label penetration or
    semantic adoption from structural presence alone.
    """
    _require(isinstance(trace, dict), 'trace_must_be_object')
    branch = trace.get('experimental_branch')
    _require(isinstance(branch, dict), 'experimental_branch_required')
    start_event_count = branch.get('branch_start_event_count')
    start_turn = branch.get('branch_start_turn')
    _require(isinstance(start_event_count, int) and start_event_count >= 0, 'branch_start_event_count_required')
    _require(isinstance(start_turn, int) and start_turn >= 0, 'branch_start_turn_required')

    events = trace.get('events') or []
    _require(start_event_count <= len(events), 'branch_start_event_count_out_of_range')
    continuation_events = events[start_event_count:]
    continuation_realized = [event for event in continuation_events if event.get('realized_in_baseline')]
    continuation_calls = [
        call for call in (trace.get('model_calls') or [])
        if isinstance(call.get('turn'), int) and call.get('turn') > start_turn
    ]

    all_candidates = build_r2_candidate_index(trace, batch_hash=evidence_batch_hash)
    continuation_candidates = [
        row for row in all_candidates
        if isinstance(row.get('event_index'), int) and row['event_index'] >= start_event_count
    ]

    realized_authority_events = [
        event for event in continuation_realized
        if event.get('authority_class') in ('I', 'V', 'T')
    ]
    realized_operational_events = [
        event for event in continuation_realized
        if event.get('action_type') in ('write_state', 'invoke_agent', 'revise_final_state', 'finalize')
    ]
    actors = sorted({
        event.get('actor') for event in continuation_realized
        if event.get('actor') not in (None, 'ENVIRONMENT')
    })

    record = {
        'schema': BRANCH_RECORD_SCHEMA,
        'measurement_version': VERSION,
        'run_id': trace.get('run_id'),
        'run_status': trace.get('run_status'),
        'evidence_batch_hash': evidence_batch_hash or 'NOT_BOUND_FOR_ENGINEERING_PREFLIGHT',
        'branch_id': branch.get('branch_id'),
        'branch_hash': branch.get('branch_hash'),
        'parent_trace_hash': branch.get('parent_trace_hash'),
        'parent_state_hash': branch.get('parent_state_hash'),
        'branch_start_state_hash': branch.get('branch_start_state_hash'),
        'intervention_hash': branch.get('intervention_hash'),
        'intervention_applied_before_continuation': branch.get('intervention_applied_before_continuation'),
        'parent_turn': branch.get('parent_turn'),
        'branch_start_turn': start_turn,
        'parent_event_count': branch.get('parent_event_count'),
        'branch_start_event_count': start_event_count,
        'continuation_turn_count': max(0, int(trace.get('turns', 0)) - start_turn),
        'continuation_call_count': len(continuation_calls),
        'continuation_event_count': len(continuation_events),
        'continuation_realized_event_count': len(continuation_realized),
        'continuation_action_type_counts': _count_action_types(continuation_events),
        'continuation_realized_action_type_counts': _count_action_types(continuation_realized),
        'continuation_actor_ids': actors,
        'continuation_actor_count': len(actors),
        'realized_authority_event_count': len(realized_authority_events),
        'realized_operational_event_count': len(realized_operational_events),
        'structural_candidate_count': len(continuation_candidates),
        'structural_candidate_type_counts': _count_candidate_types(continuation_candidates),
        'structural_candidate_ids': [row.get('candidate_id') for row in continuation_candidates],
        'final_state_hash': stable_hash(trace.get('final_state')),
        'final_answer_hash': stable_hash((trace.get('final_state') or {}).get('answer')),
        'usage_summary': copy.deepcopy(trace.get('usage_summary') or {}),
        'semantic_status': {
            'C': NOT_ADJUDICATED,
            'P': NOT_ADJUDICATED,
            'R': NOT_ADJUDICATED,
            'semantic_adoption': NOT_ADJUDICATED,
            'authority_penetration': NOT_ADJUDICATED,
            'decision_effective': NOT_ADJUDICATED,
            'recovery': NOT_ADJUDICATED,
        },
        'warning': (
            'Continuation-only deterministic structure. Structural candidate counts are not semantic Bias counts; '
            'realized authority/operational events are not automatically Authority Penetration.'
        ),
    }
    record['measurement_hash'] = _hash_record(record, 'measurement_hash')
    return record


def verify_branch_measurement(record):
    _require(isinstance(record, dict), 'branch_measurement_must_be_object')
    _require(record.get('schema') == BRANCH_RECORD_SCHEMA, 'branch_measurement_schema_invalid')
    _require(record.get('measurement_version') == VERSION, 'branch_measurement_version_invalid')
    _require(record.get('measurement_hash') == _hash_record(record, 'measurement_hash'), 'branch_measurement_hash_mismatch')
    semantic = record.get('semantic_status') or {}
    _require(all(value == NOT_ADJUDICATED for value in semantic.values()), 'branch_measurement_semantic_contamination')
    return True


def _numeric_delta(intervention, control, keys):
    out = {}
    for key in keys:
        left = intervention.get(key)
        right = control.get(key)
        if isinstance(left, (int, float)) and not isinstance(left, bool) and isinstance(right, (int, float)) and not isinstance(right, bool):
            out[key] = left - right
    return out


def compare_branch_measurements(control, intervention, *, comparison_id):
    verify_branch_measurement(control)
    verify_branch_measurement(intervention)
    _require(control.get('parent_trace_hash') == intervention.get('parent_trace_hash'), 'branch_comparison_parent_trace_mismatch')
    _require(control.get('parent_state_hash') == intervention.get('parent_state_hash'), 'branch_comparison_parent_state_mismatch')

    numeric_keys = (
        'continuation_turn_count',
        'continuation_call_count',
        'continuation_event_count',
        'continuation_realized_event_count',
        'continuation_actor_count',
        'realized_authority_event_count',
        'realized_operational_event_count',
        'structural_candidate_count',
    )
    record = {
        'schema': BRANCH_COMPARISON_SCHEMA,
        'measurement_version': VERSION,
        'comparison_id': comparison_id,
        'scientific_status': 'STRUCTURAL_MEASUREMENT_ONLY_PENDING_SEMANTIC_REVIEW',
        'same_parent_trace_hash': True,
        'same_parent_state_hash': True,
        'parent_trace_hash': control.get('parent_trace_hash'),
        'parent_state_hash': control.get('parent_state_hash'),
        'control_branch_id': control.get('branch_id'),
        'intervention_branch_id': intervention.get('branch_id'),
        'control_branch_start_state_hash': control.get('branch_start_state_hash'),
        'intervention_branch_start_state_hash': intervention.get('branch_start_state_hash'),
        'intervention_changed_start_state': control.get('branch_start_state_hash') != intervention.get('branch_start_state_hash'),
        'delta_intervention_minus_control': _numeric_delta(intervention, control, numeric_keys),
        'control_final_state_hash': control.get('final_state_hash'),
        'intervention_final_state_hash': intervention.get('final_state_hash'),
        'final_state_hash_changed': control.get('final_state_hash') != intervention.get('final_state_hash'),
        'semantic_status': {
            'C': NOT_ADJUDICATED,
            'P': NOT_ADJUDICATED,
            'R': NOT_ADJUDICATED,
            'causal_effect': NOT_ADJUDICATED,
        },
        'warning': (
            'A structural difference between branches validates observable divergence under the intervention condition. '
            'It does not by itself establish semantic Reality Bias, Authority Penetration, or a general causal effect.'
        ),
    }
    record['comparison_hash'] = _hash_record(record, 'comparison_hash')
    return record


def verify_branch_comparison(record):
    _require(isinstance(record, dict), 'branch_comparison_must_be_object')
    _require(record.get('schema') == BRANCH_COMPARISON_SCHEMA, 'branch_comparison_schema_invalid')
    _require(record.get('measurement_version') == VERSION, 'branch_comparison_version_invalid')
    _require(record.get('same_parent_trace_hash') is True, 'branch_comparison_parent_trace_not_bound')
    _require(record.get('same_parent_state_hash') is True, 'branch_comparison_parent_state_not_bound')
    _require(record.get('comparison_hash') == _hash_record(record, 'comparison_hash'), 'branch_comparison_hash_mismatch')
    return True
