import copy
import hashlib
import json
from collections import deque

AUTHORITY_BY_ACTION = {
    'invoke_agent': 'V',
    'write_state': 'I',
    'revise_final_state': 'T',
}


def stable_hash(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def agent_map(domain):
    return {a['id']: a for a in domain['agents']}


def validate_domain(domain):
    required = ['domain_id', 'label', 'entry_agent', 'task', 'agents']
    for key in required:
        if key not in domain:
            raise ValueError(f"missing domain key: {key}")
    ids = [a['id'] for a in domain['agents']]
    if len(ids) != len(set(ids)):
        raise ValueError(f"duplicate agent id in {domain['domain_id']}")
    if domain['entry_agent'] not in ids:
        raise ValueError(f"entry_agent not found in {domain['domain_id']}")
    for a in domain['agents']:
        for k in ('id', 'role', 'responsibility'):
            if not a.get(k):
                raise ValueError(f"agent missing {k}: {a}")
    task = domain['task']
    for k in ('goal', 'public_context', 'initial_shared_state', 'late_event'):
        if k not in task:
            raise ValueError(f"task missing {k} in {domain['domain_id']}")
    return True


class ArenaState:
    def __init__(self, domain, config, run_id):
        validate_domain(domain)
        self.domain = domain
        self.config = config
        self.run_id = run_id
        self.shared_state = copy.deepcopy(domain['task']['initial_shared_state'])
        self.shared_state_metadata = {k: {'status': 'initial', 'basis': 'task.initial_shared_state', 'writer': 'ENVIRONMENT'} for k in self.shared_state}
        self.final_state = None
        self.active_agents = {domain['entry_agent']}
        self.inboxes = {a['id']: deque() for a in domain['agents']}
        self.queue = deque([domain['entry_agent']])
        self.events = []
        self.turns = 0
        self.total_invocations = 0
        self.late_event_delivered = False
        self.terminated = False
        self.last_finalizer = None
        self.late_event_consumed = False
        self.inboxes[domain['entry_agent']].append({
            'type': 'task_start',
            'content': domain['task']['goal']
        })

    def runtime_view(self, agent_id):
        inbox = list(self.inboxes[agent_id])
        self.inboxes[agent_id].clear()
        if any(m.get('type') == 'environment_late_event' for m in inbox):
            self.late_event_consumed = True
        return {
            'shared_state': copy.deepcopy(self.shared_state),
            'shared_state_metadata': copy.deepcopy(self.shared_state_metadata),
            'final_state': copy.deepcopy(self.final_state),
            'inbox': inbox,
            'active_agents': sorted(self.active_agents),
            'remaining_turn_budget': max(0, self.config['max_turns'] - self.turns),
        }

    def log_event(self, actor, action, realized=True, note=None):
        event = {
            'event_index': len(self.events),
            'actor': actor,
            'turn': self.turns,
            'action_type': action.get('type'),
            'authority_class': AUTHORITY_BY_ACTION.get(action.get('type')),
            'action': copy.deepcopy(action),
            'realized_in_baseline': bool(realized),
            'note': note,
            'shared_state_after': copy.deepcopy(self.shared_state),
            'shared_state_metadata_after': copy.deepcopy(self.shared_state_metadata),
            'final_state_after': copy.deepcopy(self.final_state),
            'active_agents_after': sorted(self.active_agents),
        }
        self.events.append(event)
        return event

    def enqueue(self, agent_id, message):
        if len(self.queue) >= self.config['max_pending_messages']:
            return False
        self.inboxes[agent_id].append(message)
        self.queue.append(agent_id)
        return True

    def apply_actions(self, actor, envelope):
        amap = agent_map(self.domain)
        actions = envelope.get('actions') or []
        if not isinstance(actions, list):
            raise ValueError('actions must be a list')
        for action in actions:
            if self.terminated:
                break
            kind = action.get('type')
            if kind == 'message':
                target = action.get('to')
                if target not in amap or target not in self.active_agents:
                    self.log_event(actor, action, realized=False, note='message_target_not_active')
                    continue
                accepted = self.enqueue(target, {'type': 'agent_message', 'from': actor, 'content': action.get('content', '')})
                self.log_event(actor, action, realized=accepted, note=None if accepted else 'queue_capacity_exhausted')
            elif kind == 'invoke_agent':
                target = action.get('agent_id')
                if target not in amap:
                    self.log_event(actor, action, realized=False, note='unknown_agent')
                    continue
                if self.total_invocations >= self.config['max_total_invocations']:
                    self.log_event(actor, action, realized=False, note='invocation_budget_exhausted')
                    continue
                accepted = self.enqueue(target, {'type': 'invocation', 'from': actor, 'request': action.get('request', '')})
                if accepted:
                    self.total_invocations += 1
                    self.active_agents.add(target)
                self.log_event(actor, action, realized=accepted, note=None if accepted else 'queue_capacity_exhausted')
            elif kind == 'write_state':
                key = action.get('key')
                if not key:
                    self.log_event(actor, action, realized=False, note='missing_state_key')
                    continue
                self.shared_state[key] = copy.deepcopy(action.get('value'))
                self.shared_state_metadata[key] = {
                    'status': action.get('status', 'unspecified'),
                    'basis': copy.deepcopy(action.get('basis')),
                    'writer': actor, 'event_index': len(self.events),
                }
                self.log_event(actor, action)
            elif kind == 'revise_final_state':
                patch = action.get('patch') or {}
                if self.final_state is None or not isinstance(patch, dict):
                    self.log_event(actor, action, realized=False, note='no_final_state_or_invalid_patch')
                    continue
                state = self.final_state.setdefault('state', {})
                for key, value in patch.items():
                    state[key] = copy.deepcopy(value)
                    self.shared_state[key] = copy.deepcopy(value)
                    self.shared_state_metadata[key] = {'status': action.get('status', 'unspecified'), 'basis': action.get('reason'), 'writer': actor, 'event_index': len(self.events)}
                    self.final_state.setdefault('state_metadata', {})[key] = copy.deepcopy(self.shared_state_metadata[key])
                self.final_state['revision_count'] = self.final_state.get('revision_count', 0) + 1
                self.log_event(actor, action)
            elif kind == 'finalize':
                if self.final_state is not None and not self.late_event_consumed:
                    self.log_event(actor, action, realized=False, note='awaiting_late_event_consumption')
                    break
                self.final_state = {
                    'state_id': f"{self.domain['domain_id']}:{self.run_id}:final",
                    'status': 'FINAL',
                    'state': copy.deepcopy(self.shared_state),
                    'state_metadata': copy.deepcopy(self.shared_state_metadata),
                    'answer': action.get('answer', ''),
                    'revision_count': (self.final_state or {}).get('revision_count', 0),
                }
                self.last_finalizer = actor
                self.log_event(actor, action)
                if not self.late_event_delivered:
                    late = copy.deepcopy(self.domain['task']['late_event'])
                    self.late_event_delivered = True
                    # Environmental delivery has a reserved slot and goes to the next turn.
                    self.inboxes[actor].append({'type': 'environment_late_event', **late})
                    self.queue.appendleft(actor)
                    self.events.append({
                        'event_index': len(self.events),
                        'actor': 'ENVIRONMENT',
                        'action_type': 'late_event',
                        'authority_class': None,
                        'action': late,
                        'realized_in_baseline': True,
                        'note': 'fixed_environment_event_after_first_finalize',
                        'shared_state_after': copy.deepcopy(self.shared_state),
                        'shared_state_metadata_after': copy.deepcopy(self.shared_state_metadata),
                        'final_state_after': copy.deepcopy(self.final_state),
                        'active_agents_after': sorted(self.active_agents),
                    })
                else:
                    self.terminated = True
                # A finalize ends this response; no unseen late-event reaction is executed.
                break
            else:
                self.log_event(actor, action, realized=False, note='unknown_action_type')

