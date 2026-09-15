"""Deterministic structural feedback-round derivation.

This module deliberately does NOT inspect C/P/R labels, authorization judgments,
Authority-penetration labels, evaluator outputs, or semantic dependency labels.
It identifies a conservative neutral return pattern in frozen traces.
"""
from .core import stable_hash

VERSION = 'R4-STRUCTURAL-FEEDBACK-ROUND-v0.2'
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


def _return_evidence_from_outputs(return_call, outputs):
    """Find deterministic evidence that a return call actually received a downstream contribution."""
    input_messages = set(return_call.get('input_message_ids') or [])
    input_invocations = set(return_call.get('input_invocation_ids') or [])
    snapshot = return_call.get('runtime_snapshot') or {}
    state_origins = {
        meta.get('event_index')
        for meta in (snapshot.get('shared_state_metadata') or {}).values()
        if isinstance(meta, dict) and isinstance(meta.get('event_index'), int)
    }
    final_state = snapshot.get('final_state')

    refs = []
    modes = []
    for event in outputs:
        action = event.get('action') or {}
        message_id = action.get('message_id')
        invocation_id = action.get('invocation_id')
        event_index = event.get('event_index')
        if message_id and message_id in input_messages:
            refs.append(('message', event_index, message_id))
            modes.append('message_read')
        if invocation_id and invocation_id in input_invocations:
            refs.append(('invocation', event_index, invocation_id))
            modes.append('invocation_read')
        if event_index in state_origins:
            refs.append(('state', event_index, None))
            modes.append('state_version_visible')
        if event.get('final_state_after') is not None and final_state == event.get('final_state_after'):
            refs.append(('settled_state', event_index, None))
            modes.append('settled_version_visible')
    return refs, sorted(set(modes))


def _closing_settled_in_call(trace, call, after_event_index):
    candidates = [
        e for e in _call_output_events(trace, call)
        if e.get('action_type') in SETTLED_TYPES
        and e.get('final_state_after') is not None
        and e.get('event_index', -1) > after_event_index
    ]
    return candidates[0] if candidates else None


def derive_structural_feedback_rounds(trace):
    """Return non-overlapping conservative structural feedback rounds.

    A round is counted only when all deterministic conditions hold:

    1. actor A creates an anchor settled-state version;
    2. a different actor B later completes a call whose recorded input contains that
       exact settled version;
    3. B produces at least one realized contribution action;
    4. A later completes a call that demonstrably receives at least one of B's
       recorded contributions (message, invocation, state version, or settled version);
    5. that same return call by A creates a new settled-state version.

    The closing settled event becomes the next anchor. Rounds are sequential and
    non-overlapping. This A -> B -> A pattern is intentionally conservative: it is a
    structural feedback opportunity, not a claim that B caused A's update or that any
    step was biased, unauthorized, or self-reinforcing.
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

    settled_pos = {e['event_index']: i for i, e in enumerate(settled)}
    rounds = []
    anchor_pos = 0
    open_tail = None

    while anchor_pos < len(settled):
        anchor = settled[anchor_pos]
        anchor_idx = anchor['event_index']
        anchor_turn = anchor.get('turn', -1)
        anchor_actor = anchor.get('actor')
        found_round = None
        partial_tail = None

        for exposure_call_index, exposure_call in calls:
            if exposure_call.get('turn', -1) <= anchor_turn:
                continue
            if exposure_call.get('agent_id') == anchor_actor:
                continue
            if not _sees_anchor(exposure_call, anchor):
                continue
            outputs = [e for e in _call_output_events(trace, exposure_call) if e['event_index'] > anchor_idx]
            if not outputs:
                continue

            first_output_idx = min(e['event_index'] for e in outputs)
            partial_tail = {
                'anchor_event_ref': _event_ref(run_id, anchor_idx),
                'exposure_call_ref': _call_ref(run_id, exposure_call_index),
                'exposure_actor': exposure_call.get('agent_id'),
                'contribution_event_refs': [_event_ref(run_id, e['event_index']) for e in outputs],
                'return_to_anchor_observed': False,
                'closed_by_anchor_settled_state': False,
            }

            for return_call_index, return_call in calls:
                if return_call.get('turn', -1) <= exposure_call.get('turn', -1):
                    continue
                if return_call.get('agent_id') != anchor_actor:
                    continue
                return_refs, return_modes = _return_evidence_from_outputs(return_call, outputs)
                if not return_refs:
                    continue
                partial_tail['return_to_anchor_observed'] = True
                closing = _closing_settled_in_call(trace, return_call, first_output_idx)
                if closing is None:
                    continue
                closing_pos = settled_pos.get(closing['event_index'])
                if closing_pos is None or closing_pos <= anchor_pos:
                    continue
                partial_tail['closed_by_anchor_settled_state'] = True
                found_round = (
                    exposure_call_index, exposure_call, outputs,
                    return_call_index, return_call, return_refs, return_modes,
                    closing_pos, closing,
                )
                break
            if found_round is not None:
                break

        if found_round is None:
            if partial_tail is not None:
                partial_tail['status'] = 'OPEN_AT_OBSERVATION_BOUNDARY' if trace.get('observation_censored') else 'OPEN_AT_RECORDED_END'
                open_tail = partial_tail
            break

        (
            exposure_call_index, exposure_call, outputs,
            return_call_index, return_call, return_refs, return_modes,
            closing_pos, closing,
        ) = found_round

        evidence_refs = [
            _event_ref(run_id, anchor_idx),
            _call_ref(run_id, exposure_call_index),
            *[_event_ref(run_id, e['event_index']) for e in outputs],
            _call_ref(run_id, return_call_index),
            _event_ref(run_id, closing['event_index']),
        ]
        evidence_refs = list(dict.fromkeys(evidence_refs))
        row = {
            'round_index': len(rounds) + 1,
            'anchor_event_ref': _event_ref(run_id, anchor_idx),
            'anchor_turn': anchor_turn,
            'anchor_actor': anchor_actor,
            'anchor_action_type': anchor.get('action_type'),
            'exposure_call_ref': _call_ref(run_id, exposure_call_index),
            'exposure_turn': exposure_call.get('turn'),
            'exposure_actor': exposure_call.get('agent_id'),
            'contribution_event_refs': [_event_ref(run_id, e['event_index']) for e in outputs],
            'contribution_action_types': [e.get('action_type') for e in outputs],
            'return_call_ref': _call_ref(run_id, return_call_index),
            'return_turn': return_call.get('turn'),
            'return_actor': return_call.get('agent_id'),
            'return_evidence_modes': return_modes,
            'return_evidence_refs': [
                _event_ref(run_id, idx) for _, idx, _ in return_refs if isinstance(idx, int)
            ],
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

    return {
        'version': VERSION,
        'run_id': run_id,
        'counter_status': 'RECORDED',
        'semantic_blind': True,
        'definition': 'A settles -> B sees exact settled version and contributes -> A demonstrably receives B contribution -> A settles again',
        'round_count': len(rounds),
        'rounds': rounds,
        'open_tail': open_tail,
        'observation_censored': trace.get('observation_censored', 'NOT_RECORDED_IN_SOURCE_VERSION'),
        'warning': 'Structural feedback rounds are conservative neutral return patterns, not Reality Bias loops, Authority penetration, semantic dependency, or causal self-reinforcement.'
    }
