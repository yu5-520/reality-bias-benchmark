"""Deterministic structural feedback-round derivation.

This module deliberately does NOT inspect C/P/R labels, authorization judgments,
Authority-penetration labels, evaluator outputs, or semantic dependency labels.
It only identifies a neutral repeated structural pattern in frozen traces.
"""
from .core import stable_hash

VERSION = 'R4-STRUCTURAL-FEEDBACK-ROUND-v0.1'
CONTRIBUTION_TYPES = {'message', 'invoke_agent', 'write_state', 'revise_final_state', 'finalize'}
SETTLED_TYPES = {'finalize', 'revise_final_state'}


def _event_ref(run_id, event_index):
    return f'{run_id}:EVENT:{event_index:04d}'


def _call_ref(run_id, call_index):
    return f'{run_id}:CALL:{call_index:04d}'


def _realized(event):
    return bool(event.get('realized_in_baseline'))


def _settled_events(trace):
    return [
        e for e in trace.get('events', [])
        if _realized(e)
        and e.get('actor') != 'ENVIRONMENT'
        and e.get('action_type') in SETTLED_TYPES
        and e.get('final_state_after') is not None
    ]


def _completed_calls(trace):
    return [
        (i, c) for i, c in enumerate(trace.get('model_calls', []))
        if c.get('status', 'completed') == 'completed'
    ]


def _call_output_events(trace, call):
    start = call.get('event_index_start')
    end = call.get('event_index_end')
    if not isinstance(start, int) or not isinstance(end, int):
        return []
    return [
        e for e in trace.get('events', [])
        if start <= e.get('event_index', -1) < end
        and e.get('actor') == call.get('agent_id')
        and _realized(e)
        and e.get('action_type') in CONTRIBUTION_TYPES
    ]


def _sees_anchor(call, anchor):
    """True only when the contemporaneous runtime snapshot contains the exact settled version."""
    snapshot = call.get('runtime_snapshot')
    if not isinstance(snapshot, dict):
        return False
    return snapshot.get('final_state') == anchor.get('final_state_after')


def derive_structural_feedback_rounds(trace):
    """Return non-overlapping neutral structural feedback rounds.

    A round is counted when all of the following deterministic conditions hold:

    1. an anchor settled-state event (FINAL or revision) exists;
    2. after that anchor, a *different actor* completes a model call whose recorded
       runtime snapshot contains that exact settled version;
    3. that exposed actor produces at least one realized contribution action; and
    4. after the exposed actor's first contribution, a later settled-state event is
       realized.

    The closing settled event becomes the next anchor, so rounds are sequential and
    non-overlapping. This is a structural opportunity/return counter only. It does
    not assert that the exposed contribution caused the closing state, was biased,
    was unauthorized, or was self-reinforcing.
    """
    run_id = trace.get('run_id', 'UNKNOWN')
    calls = _completed_calls(trace)
    settled = _settled_events(trace)

    if any('runtime_snapshot' not in c for _, c in calls):
        return {
            'version': VERSION,
            'run_id': run_id,
            'counter_status': 'NOT_RECORDED_IN_SOURCE_VERSION',
            'semantic_blind': True,
            'round_count': None,
            'rounds': [],
            'open_tail': None,
            'warning': 'Runtime snapshots are required; no rounds were reconstructed from missing legacy evidence.'
        }

    rounds = []
    anchor_pos = 0
    while anchor_pos < len(settled):
        anchor = settled[anchor_pos]
        anchor_idx = anchor['event_index']
        anchor_turn = anchor.get('turn', -1)
        anchor_actor = anchor.get('actor')

        exposure = None
        for call_index, call in calls:
            if call.get('turn', -1) <= anchor_turn:
                continue
            if call.get('agent_id') == anchor_actor:
                continue
            if not _sees_anchor(call, anchor):
                continue
            outputs = [e for e in _call_output_events(trace, call) if e['event_index'] > anchor_idx]
            if not outputs:
                continue
            exposure = (call_index, call, outputs)
            break

        if exposure is None:
            break

        call_index, call, outputs = exposure
        first_output_idx = min(e['event_index'] for e in outputs)
        closing_pos = None
        closing = None
        for pos in range(anchor_pos + 1, len(settled)):
            candidate = settled[pos]
            if candidate['event_index'] > first_output_idx:
                closing_pos = pos
                closing = candidate
                break

        if closing is None:
            break

        evidence_refs = [
            _event_ref(run_id, anchor_idx),
            _call_ref(run_id, call_index),
            *[_event_ref(run_id, e['event_index']) for e in outputs],
            _event_ref(run_id, closing['event_index']),
        ]
        evidence_refs = list(dict.fromkeys(evidence_refs))
        row = {
            'round_index': len(rounds) + 1,
            'anchor_event_ref': _event_ref(run_id, anchor_idx),
            'anchor_turn': anchor_turn,
            'anchor_actor': anchor_actor,
            'anchor_action_type': anchor.get('action_type'),
            'exposure_call_ref': _call_ref(run_id, call_index),
            'exposure_turn': call.get('turn'),
            'exposure_actor': call.get('agent_id'),
            'contribution_event_refs': [_event_ref(run_id, e['event_index']) for e in outputs],
            'contribution_action_types': [e.get('action_type') for e in outputs],
            'closing_event_ref': _event_ref(run_id, closing['event_index']),
            'closing_turn': closing.get('turn'),
            'closing_actor': closing.get('actor'),
            'closing_action_type': closing.get('action_type'),
            'evidence_refs': evidence_refs,
            'semantic_dependency': 'NOT_ADJUDICATED',
            'authority_penetration': 'NOT_ADJUDICATED',
            'bias_labels': 'NOT_ADJUDICATED',
            'self_reinforcement': 'NOT_ADJUDICATED',
        }
        row['round_id'] = f"{run_id}:SFR:{row['round_index']:04d}:{stable_hash(row)[:12]}"
        rounds.append(row)
        anchor_pos = closing_pos

    open_tail = None
    if anchor_pos < len(settled):
        anchor = settled[anchor_pos]
        later_calls = [
            (i, c) for i, c in calls
            if c.get('turn', -1) > anchor.get('turn', -1)
            and c.get('agent_id') != anchor.get('actor')
            and _sees_anchor(c, anchor)
        ]
        if later_calls:
            call_index, call = later_calls[0]
            outputs = _call_output_events(trace, call)
            open_tail = {
                'anchor_event_ref': _event_ref(run_id, anchor['event_index']),
                'exposure_call_ref': _call_ref(run_id, call_index),
                'exposure_actor': call.get('agent_id'),
                'has_realized_contribution': bool(outputs),
                'closed_by_later_settled_state': False,
                'status': 'OPEN_AT_OBSERVATION_BOUNDARY' if trace.get('observation_censored') else 'OPEN_AT_RECORDED_END',
            }

    return {
        'version': VERSION,
        'run_id': run_id,
        'counter_status': 'RECORDED',
        'semantic_blind': True,
        'definition': 'settled version -> exact-version exposure to different actor -> realized contribution -> later settled version',
        'round_count': len(rounds),
        'rounds': rounds,
        'open_tail': open_tail,
        'observation_censored': trace.get('observation_censored', 'NOT_RECORDED_IN_SOURCE_VERSION'),
        'warning': 'Structural feedback rounds are neutral repeated-return opportunities, not Reality Bias loops, Authority penetration, semantic dependency, or causal self-reinforcement.'
    }
