import json
from .core import ArenaState, stable_hash
from .prompts import build_agent_messages


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


def run_arena_once(domain, config, provider, run_id, logical_seed=None):
    state = ArenaState(domain, config, run_id)
    amap = {a['id']: a for a in domain['agents']}
    model_calls = []

    while state.queue and not state.terminated and state.turns < config['max_turns']:
        actor = state.queue.popleft()
        state.turns += 1
        view = state.runtime_view(actor)
        messages = build_agent_messages(domain, amap[actor], view)
        response = provider.complete_agent(messages, metadata={
            'run_id': run_id,
            'domain_id': domain['domain_id'],
            'agent_id': actor,
            'turn': state.turns,
            'logical_seed': logical_seed,
        })
        envelope = parse_envelope(response['content'])
        model_calls.append({
            'agent_id': actor,
            'turn': state.turns,
            'prompt_hash': stable_hash(messages),
            'response_id': response.get('response_id'),
            'provider_model': response.get('model'),
            'usage': response.get('usage') or {},
            'decision_summary': envelope.get('decision_summary', ''),
            'raw_content': response['content'],
        })
        state.apply_actions(actor, envelope)

    termination_reason = 'finalized_after_late_event' if state.terminated else (
        'turn_budget_exhausted' if state.turns >= config['max_turns'] else 'queue_empty'
    )
    return {
        'run_id': run_id,
        'domain_id': domain['domain_id'],
        'domain_label': domain['label'],
        'logical_seed': logical_seed,
        'task_hash': stable_hash(domain['task']),
        'agent_registry_hash': stable_hash(domain['agents']),
        'turns': state.turns,
        'activated_agents': sorted(state.active_agents),
        'activated_agent_count': len(state.active_agents),
        'total_invocations': state.total_invocations,
        'late_event_delivered': state.late_event_delivered,
        'termination_reason': termination_reason,
        'final_state': state.final_state,
        'events': state.events,
        'model_calls': model_calls,
    }
