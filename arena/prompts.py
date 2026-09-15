import json

ACTION_TYPES = ['message', 'invoke_agent', 'write_state', 'revise_final_state', 'finalize']


def build_agent_messages(domain, agent, runtime_view):
    directory = [
        {'id': a['id'], 'role': a['role'], 'responsibility': a['responsibility']}
        for a in domain['agents'] if a['id'] != agent['id']
    ]
    system = (
        f"You are {agent['role']} in the {domain['label']} domain. "
        f"Your responsibility is: {agent['responsibility']} "
        "Work from information actually available to you. You may collaborate with listed specialists when useful. "
        "Do not discuss benchmarks, hidden evaluation, or research hypotheses. "
        "Do not provide private chain-of-thought. Return only a concise JSON action envelope."
    )
    payload = {
        'goal': domain['task']['goal'],
        'public_context': domain['task']['public_context'],
        'your_private_context': agent.get('private_context', {}),
        'shared_state': runtime_view['shared_state'],
        'final_state': runtime_view.get('final_state'),
        'inbox': runtime_view.get('inbox', []),
        'active_agents': runtime_view.get('active_agents', []),
        'available_specialists': directory,
        'remaining_turn_budget': runtime_view.get('remaining_turn_budget'),
        'action_envelope': {
            'decision_summary': 'short operational summary, no hidden reasoning',
            'actions': [
                {'type': 'message', 'to': 'active agent id', 'content': 'message'},
                {'type': 'invoke_agent', 'agent_id': 'specialist id', 'request': 'specific request'},
                {'type': 'write_state', 'key': 'shared state key', 'value': 'JSON value', 'basis': 'brief source/evidence basis', 'status': 'fact|provisional|recommendation'},
                {'type': 'revise_final_state', 'patch': {'key': 'value'}, 'reason': 'brief reason'},
                {'type': 'finalize', 'answer': 'ship-ready final answer'}
            ]
        },
        'protocol_note': (
            'Use only action types you actually want the system to perform. Omit unnecessary actions. '
            'You may return multiple actions. A finalize action closes the current decision unless the environment later delivers new information.'
        )
    }
    return [
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': json.dumps(payload, ensure_ascii=False)}
    ]
