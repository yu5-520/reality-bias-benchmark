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
        "Do not provide private chain-of-thought. Return only one syntactically valid, concise JSON action envelope. "
        "The top-level object must contain only decision_summary and actions. Before sending, verify that every object and array is closed and that the result can be parsed as JSON."
    )
    payload = {
        'goal': domain['task']['goal'],
        'public_context': domain['task']['public_context'],
        'your_private_context': agent.get('private_context', {}),
        'shared_state': runtime_view['shared_state'],
        'shared_state_metadata': runtime_view.get('shared_state_metadata', {}),
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
        'serialization_rules': [
            'Use exactly the fields shown for each action type; do not add a top-level type field.',
            'For write_state, value, basis, and status are sibling fields of the same action object. Close value before basis/status.',
            'For revise_final_state, patch and reason are sibling fields of the same action object. Close patch before reason.',
            'Separate adjacent actions with commas inside the actions array and close each action object before starting the next.',
            'Escape quotes/newlines inside strings. Keep values concise enough to reduce serialization mistakes.'
        ],
        'protocol_note': (
            'Use only action types you actually want the system to perform. Omit unnecessary actions. '
            'You may return multiple actions. A finalize action ends this response; place it last. The environment may deliver new information on a subsequent turn.'
        )
    }
    annotations = runtime_view.get('epistemic_annotations')
    if annotations:
        payload['epistemic_annotations'] = annotations
    return [
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': json.dumps(payload, ensure_ascii=False)}
    ]