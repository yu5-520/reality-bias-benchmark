import copy
from collections import Counter

from .core import stable_hash
from .topology import participation_metrics, topology_metrics


SCHEMA = 'RB-ORCHESTRATION-COMPARISON-v0.1'
ALLOWED_SCIENTIFIC_STATUS = {
    'ENGINEERING_ONLY_NOT_SCIENTIFIC_EVIDENCE',
    'SUBJECT_EVIDENCE_PENDING_SEMANTIC_REVIEW',
}


def _action_type_counts(actions):
    counts = Counter()
    for action in actions:
        if isinstance(action, dict):
            counts[str(action.get('type'))] += 1
    return dict(sorted(counts.items()))


def _merge_counts(left, right):
    out = Counter(left or {})
    out.update(right or {})
    return dict(sorted(out.items()))


def proposal_summary(trace):
    proposal_counts = {}
    blocked_counts = {}
    passed_counts = {}
    proposal_records = []
    structured_call_count = 0

    for call_index, call in enumerate(trace.get('model_calls') or []):
        if call.get('status') != 'completed':
            continue
        control = (call.get('provider_response') or {}).get('structured_routing')
        if isinstance(control, dict):
            structured_call_count += 1
            original = control.get('original_subject_envelope') or {}
            original_actions = original.get('actions') or []
            blocked = control.get('blocked_actions') or []
            passed = control.get('passed_actions') or []
            proposal_counts = _merge_counts(proposal_counts, _action_type_counts(original_actions))
            blocked_counts = _merge_counts(
                blocked_counts,
                _action_type_counts([row.get('action') or {} for row in blocked]),
            )
            passed_counts = _merge_counts(passed_counts, _action_type_counts(passed))
            proposal_records.append({
                'call_index': call_index,
                'turn': call.get('turn'),
                'agent_id': call.get('agent_id'),
                'stage_id': control.get('stage_id'),
                'original_action_types': [a.get('type') for a in original_actions if isinstance(a, dict)],
                'blocked': copy.deepcopy(blocked),
                'passed_action_types': [a.get('type') for a in passed if isinstance(a, dict)],
            })
        else:
            envelope = call.get('parsed_envelope') or {}
            actions = envelope.get('actions') or []
            proposal_counts = _merge_counts(proposal_counts, _action_type_counts(actions))
            passed_counts = _merge_counts(passed_counts, _action_type_counts(actions))
            proposal_records.append({
                'call_index': call_index,
                'turn': call.get('turn'),
                'agent_id': call.get('agent_id'),
                'stage_id': None,
                'original_action_types': [a.get('type') for a in actions if isinstance(a, dict)],
                'blocked': [],
                'passed_action_types': [a.get('type') for a in actions if isinstance(a, dict)],
            })

    realized = [
        event.get('action') or {}
        for event in trace.get('events') or []
        if event.get('realized_in_baseline')
    ]
    realized_counts = _action_type_counts(realized)

    return {
        'proposal_action_counts': proposal_counts,
        'policy_passed_action_counts': passed_counts,
        'policy_blocked_action_counts': blocked_counts,
        'realized_action_counts': realized_counts,
        'proposal_invoke_count': int(proposal_counts.get('invoke_agent', 0)),
        'policy_blocked_invoke_count': int(blocked_counts.get('invoke_agent', 0)),
        'realized_invoke_count': int(realized_counts.get('invoke_agent', 0)),
        'structured_control_call_count': structured_call_count,
        'proposal_records': proposal_records,
    }


def summarize_condition(trace, condition_id):
    topo = topology_metrics(trace)
    participation = participation_metrics(trace)
    proposal = proposal_summary(trace)
    return {
        'condition_id': condition_id,
        'run_id': trace.get('run_id'),
        'run_status': trace.get('run_status'),
        'termination_reason': trace.get('termination_reason'),
        'task_hash': trace.get('task_hash'),
        'agent_registry_hash': trace.get('agent_registry_hash'),
        'turns': trace.get('turns'),
        'usage_summary': copy.deepcopy(trace.get('usage_summary') or {}),
        'orchestration_condition': copy.deepcopy(trace.get('orchestration_condition')),
        'topology': topo,
        'participation': participation,
        'proposal_realization': proposal,
        'trace_hash': stable_hash(trace),
    }


def _numeric_delta(structured, free, keys):
    out = {}
    for key in keys:
        left = structured.get(key)
        right = free.get(key)
        if isinstance(left, (int, float)) and not isinstance(left, bool) and isinstance(right, (int, float)) and not isinstance(right, bool):
            out[key] = left - right
    return out


def build_comparison_record(
    free_trace,
    structured_trace,
    *,
    comparison_id,
    fixture_identity=None,
    code_identity=None,
    scientific_status='ENGINEERING_ONLY_NOT_SCIENTIFIC_EVIDENCE',
):
    if scientific_status not in ALLOWED_SCIENTIFIC_STATUS:
        raise ValueError('comparison_scientific_status_invalid')

    free = summarize_condition(free_trace, 'EMERGENT_FREE_ROUTING')
    structured = summarize_condition(structured_trace, 'STRUCTURED_SYSTEM_OWNED_ROUTING')

    same_task = free['task_hash'] == structured['task_hash']
    same_registry = free['agent_registry_hash'] == structured['agent_registry_hash']
    if not same_task:
        raise ValueError('orchestration_comparison_task_hash_mismatch')
    if not same_registry:
        raise ValueError('orchestration_comparison_agent_registry_hash_mismatch')

    interpretation = (
        'Mechanical deltas validate evidence shape and proposal-versus-realization accounting only. '
        'They are not an estimate that either orchestration condition is safer, better, or lower-bias.'
        if scientific_status == 'ENGINEERING_ONLY_NOT_SCIENTIFIC_EVIDENCE'
        else
        'This record contains frozen real-subject structural evidence pending semantic review. '
        'Mechanical deltas describe the paired conditions; they do not rank either architecture as safer, better, or lower-bias.'
    )

    record = {
        'schema': SCHEMA,
        'comparison_id': comparison_id,
        'scientific_status': scientific_status,
        'same_task_hash': same_task,
        'same_agent_registry_hash': same_registry,
        'task_hash': free['task_hash'],
        'agent_registry_hash': free['agent_registry_hash'],
        'fixture_identity': copy.deepcopy(fixture_identity),
        'code_identity': copy.deepcopy(code_identity),
        'conditions': {
            'free': free,
            'structured': structured,
        },
        'mechanical_deltas_structured_minus_free': {
            'topology': _numeric_delta(
                structured['topology'],
                free['topology'],
                [
                    'agent_count',
                    'edge_count',
                    'message_count',
                    'state_write_count',
                    'revision_count',
                    'activated_agent_count',
                    'executed_agent_count',
                    'returned_agent_count',
                    'execution_edge_count',
                ],
            ),
            'proposal_realization': _numeric_delta(
                structured['proposal_realization'],
                free['proposal_realization'],
                [
                    'proposal_invoke_count',
                    'policy_blocked_invoke_count',
                    'realized_invoke_count',
                    'structured_control_call_count',
                ],
            ),
            'turns': structured['turns'] - free['turns'] if isinstance(structured['turns'], int) and isinstance(free['turns'], int) else None,
        },
        'interpretation_boundary': interpretation,
    }
    material = copy.deepcopy(record)
    record['comparison_hash'] = stable_hash(material)
    return record


def verify_comparison_record(record):
    if not isinstance(record, dict):
        raise ValueError('comparison_record_must_be_object')
    if record.get('schema') != SCHEMA:
        raise ValueError('comparison_schema_invalid')
    if record.get('scientific_status') not in ALLOWED_SCIENTIFIC_STATUS:
        raise ValueError('comparison_scientific_status_invalid')
    if record.get('same_task_hash') is not True:
        raise ValueError('comparison_task_binding_invalid')
    if record.get('same_agent_registry_hash') is not True:
        raise ValueError('comparison_registry_binding_invalid')
    material = copy.deepcopy(record)
    actual = material.pop('comparison_hash', None)
    if actual != stable_hash(material):
        raise ValueError('comparison_hash_mismatch')
    return True
