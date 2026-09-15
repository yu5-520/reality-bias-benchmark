import json
from collections import defaultdict
from .core import ArenaState, stable_hash
from .prompts import build_agent_messages

TRACE_SCHEMA_VERSION = 'R2-ARENA-TRACE-v0.2'


def parse_envelope(text):
    if isinstance(text, dict):
        obj = text
    else:
        raw = str(text).strip()
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            if '```' not in raw:
                raise
            obj = None
            for piece in raw.split('```'):
                piece = piece.strip()
                if piece.startswith('json'):
                    piece = piece[4:].strip()
                try:
                    obj = json.loads(piece)
                    break
                except Exception:
                    pass
            if obj is None:
                raise
    if not isinstance(obj, dict):
        raise ValueError('agent response must be JSON object')
    obj.setdefault('decision_summary', '')
    obj.setdefault('actions', [])
    return obj


def _sum_usage(model_calls):
    totals = defaultdict(float)
    for call in model_calls:
        for key, value in (call.get('usage') or {}).items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                totals[key] += value
    out = {}
    for key, value in totals.items():
        out[key] = int(value) if float(value).is_integer() else value
    return dict(sorted(out.items()))


def _returned_agents(events):
    contribution_types = {'message', 'write_state', 'revise_final_state', 'finalize'}
    return sorted({
        e.get('actor') for e in events
        if e.get('actor') not in (None, 'ENVIRONMENT')
        and e.get('realized_in_baseline')
        and e.get('action_type') in contribution_types
    })


def run_arena_once(domain, config, provider, run_id, logical_seed=None):
    state = ArenaState(domain, config, run_id)
    amap = {a['id']: a for a in domain['agents']}
    model_calls = []

    while state.queue and not state.terminated and state.turns < config['max_turns']:
        actor = state.queue.popleft()
        state.turns += 1
        view = state.runtime_view(actor)
        messages = build_agent_messages(domain, amap[actor], view)
        call = {
            'agent_id': actor,
            'turn': state.turns,
            'status': 'started',
            'prompt_hash': stable_hash(messages),
            'messages': messages,
            'input_message_ids': list(state.last_read_message_ids),
            'input_invocation_ids': list(state.last_read_invocation_ids),
            'event_index_start': len(state.events),
        }
        try:
            response = provider.complete_agent(messages, metadata={
                'run_id': run_id,
                'domain_id': domain['domain_id'],
                'agent_id': actor,
                'turn': state.turns,
                'logical_seed': logical_seed,
            })
            call.update({
                'response_id': response.get('response_id'),
                'provider_model': response.get('model'),
                'usage': response.get('usage') or {},
                'raw_content': response.get('content'),
            })
            envelope = parse_envelope(response['content'])
            call['parsed_envelope'] = envelope
            call['decision_summary'] = envelope.get('decision_summary', '')
            call['status'] = 'completed'
            state.mark_execution(actor, state.turns, True)
            state.apply_actions(actor, envelope)
            call['event_index_end'] = len(state.events)
            model_calls.append(call)
        except Exception as err:
            call['status'] = 'failed'
            call['error'] = repr(err)
            call['event_index_end'] = len(state.events)
            model_calls.append(call)
            state.mark_execution(actor, state.turns, False, repr(err))
            state.failures.append({
                'turn': state.turns,
                'agent_id': actor,
                'stage': 'provider_or_parse',
                'error': repr(err),
                'input_message_ids': list(state.last_read_message_ids),
            })
            state.termination_reason = 'model_call_failure'
            break

    if state.termination_reason:
        termination_reason = state.termination_reason
    elif state.turns >= config['max_turns']:
        termination_reason = 'turn_budget_exhausted'
    elif not state.queue and state.final_state is not None:
        termination_reason = 'queue_empty_with_final_state'
    else:
        termination_reason = 'queue_empty_without_final_state'

    executed_agents = sorted({x['agent_id'] for x in state.execution_ledger if x['status'] == 'completed'})
    model_response_agents = sorted({x['agent_id'] for x in model_calls if x.get('status') == 'completed'})
    returned_agents = _returned_agents(state.events)
    if state.failures:
        run_status = 'RUN_FAILED'
    elif state.final_state is None:
        run_status = 'RUN_INCOMPLETE'
    else:
        run_status = 'RUN_COMPLETE'

    evidence = state.evidence_snapshot()
    return {
        'trace_schema_version': TRACE_SCHEMA_VERSION,
        'run_id': run_id,
        'domain_id': domain['domain_id'],
        'domain_label': domain['label'],
        'logical_seed': logical_seed,
        'task_hash': stable_hash(domain['task']),
        'agent_registry_hash': stable_hash(domain['agents']),
        'run_status': run_status,
        'review_status': 'PENDING_REVIEW',
        'turns': state.turns,
        'available_agents': sorted(amap),
        'available_agent_count': len(amap),
        'activated_agents': sorted(state.active_agents),
        'activated_agent_count': len(state.active_agents),
        'executed_agents': executed_agents,
        'executed_agent_count': len(executed_agents),
        'model_response_agents': model_response_agents,
        'model_response_agent_count': len(model_response_agents),
        'returned_agents': returned_agents,
        'returned_agent_count': len(returned_agents),
        'total_invocations': state.total_invocations,
        'late_event_delivered': state.late_event_delivered,
        'late_event_consumed': state.late_event_consumed,
        'termination_reason': termination_reason,
        'final_state': state.final_state,
        'remaining_queue': evidence['remaining_queue'],
        'unread_messages': evidence['unread_messages'],
        'pending_invocations': evidence['pending_invocations'],
        'message_ledger': evidence['message_ledger'],
        'invocation_ledger': evidence['invocation_ledger'],
        'execution_ledger': evidence['execution_ledger'],
        'failures': evidence['failures'],
        'usage_summary': _sum_usage(model_calls),
        'events': state.events,
        'model_calls': model_calls,
    }
