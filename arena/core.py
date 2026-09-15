import copy
import hashlib
import json
from datetime import datetime, timezone
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
    def __init__(self, domain, config, run_id, recorder=None):
        validate_domain(domain)
        self.recorder = recorder
        self.budget_hits = []
        self.domain = domain
        self.config = config
        self.run_id = run_id
        self.shared_state = copy.deepcopy(domain['task']['initial_shared_state'])
        self.shared_state_metadata = {
            k: {'status': 'initial', 'basis': 'task.initial_shared_state', 'writer': 'ENVIRONMENT'}
            for k in self.shared_state
        }
        self.final_state = None
        self.active_agents = {domain['entry_agent']}
        self.inboxes = {a['id']: deque() for a in domain['agents']}
        self.queue = deque()
        self.events = []
        self.turns = 0
        self.total_invocations = 0
        self.late_event_delivered = False
        self.terminated = False
        self.last_finalizer = None
        self.late_event_consumed = False
        self.termination_reason = None
        self.failures = []

        # Evidence-v0.2 ledgers. These are append-only during a run.
        self.message_ledger = []
        self.invocation_ledger = []
        self.execution_ledger = []
        self._message_seq = 0
        self._invocation_seq = 0
        self.last_read_message_ids = []
        self.last_read_invocation_ids = []

        task_msg_id = self.enqueue(
            domain['entry_agent'],
            {'type': 'task_start', 'content': domain['task']['goal']},
            sender='ENVIRONMENT',
            queue_position='back',
        )
        if not task_msg_id:
            raise RuntimeError('failed to enqueue initial task message')

    def _next_message_id(self):
        self._message_seq += 1
        return f"M{self._message_seq:05d}"

    def _next_invocation_id(self):
        self._invocation_seq += 1
        return f"IV{self._invocation_seq:05d}"

    def _find_message_record(self, message_id):
        for row in self.message_ledger:
            if row['message_id'] == message_id:
                return row
        return None

    def _find_invocation_record(self, invocation_id):
        for row in self.invocation_ledger:
            if row['invocation_id'] == invocation_id:
                return row
        return None

    def runtime_view(self, agent_id):
        raw_inbox = list(self.inboxes[agent_id])
        self.inboxes[agent_id].clear()
        read_message_ids = []
        read_invocation_ids = []
        clean_inbox = []
        for raw in raw_inbox:
            message_id = raw.get('_message_id')
            invocation_id = raw.get('_invocation_id')
            if message_id:
                read_message_ids.append(message_id)
                rec = self._find_message_record(message_id)
                if rec and rec.get('read_turn') is None:
                    rec['read_turn'] = self.turns
                    rec['read_by'] = agent_id
            if invocation_id:
                read_invocation_ids.append(invocation_id)
                rec = self._find_invocation_record(invocation_id)
                if rec and rec.get('read_turn') is None:
                    rec['read_turn'] = self.turns
            msg = {k: copy.deepcopy(v) for k, v in raw.items() if not k.startswith('_')}
            clean_inbox.append(msg)
        self.last_read_message_ids = read_message_ids
        self.last_read_invocation_ids = read_invocation_ids
        if any(m.get('type') == 'environment_late_event' for m in clean_inbox):
            self.late_event_consumed = True
        return {
            'shared_state': copy.deepcopy(self.shared_state),
            'shared_state_metadata': copy.deepcopy(self.shared_state_metadata),
            'final_state': copy.deepcopy(self.final_state),
            'inbox': clean_inbox,
            'active_agents': sorted(self.active_agents),
            'remaining_turn_budget': max(0, self.config['max_turns'] - self.turns),
        }

    def _snapshot(self):
        return {
            'shared_state': copy.deepcopy(self.shared_state),
            'shared_state_metadata': copy.deepcopy(self.shared_state_metadata),
            'final_state': copy.deepcopy(self.final_state),
            'active_agents': sorted(self.active_agents),
            'queue': list(self.queue),
        }

    def log_event(self, actor, action, realized=True, note=None, before=None):
        before = before or self._snapshot()
        event = {
            'event_index': len(self.events),
            'recorded_at': datetime.now(timezone.utc).isoformat(),
            'actor': actor,
            'turn': self.turns,
            'action_type': action.get('type'),
            'authority_class': AUTHORITY_BY_ACTION.get(action.get('type')),
            'action': copy.deepcopy(action),
            'realized_in_baseline': bool(realized),
            'note': note,
            'shared_state_before': copy.deepcopy(before['shared_state']),
            'shared_state_metadata_before': copy.deepcopy(before['shared_state_metadata']),
            'final_state_before': copy.deepcopy(before['final_state']),
            'active_agents_before': copy.deepcopy(before['active_agents']),
            'queue_before': copy.deepcopy(before['queue']),
            'shared_state_after': copy.deepcopy(self.shared_state),
            'shared_state_metadata_after': copy.deepcopy(self.shared_state_metadata),
            'final_state_after': copy.deepcopy(self.final_state),
            'active_agents_after': sorted(self.active_agents),
            'queue_after': list(self.queue),
        }
        self.events.append(event)
        if note in ('queue_capacity_exhausted', 'invocation_budget_exhausted'):
            self.budget_hits.append({'reason': note, 'event_index': event['event_index'], 'turn': self.turns})
            if self.config.get('termination_policy') == 'observe_until_quiescent':
                self.terminated = True
                self.termination_reason = note
        if self.recorder:
            self.recorder({'record_type': 'event', 'record': event})
        return event

    def enqueue(self, agent_id, message, sender=None, queue_position='back', invocation_id=None):
        if agent_id not in self.inboxes:
            return None
        if len(self.queue) >= self.config['max_pending_messages']:
            return None
        message_id = self._next_message_id()
        stored = copy.deepcopy(message)
        stored['_message_id'] = message_id
        if invocation_id:
            stored['_invocation_id'] = invocation_id
        self.inboxes[agent_id].append(stored)
        if self.config.get('termination_policy') == 'observe_until_quiescent':
            if queue_position == 'front' and agent_id in self.queue:
                self.queue.remove(agent_id)
            if agent_id not in self.queue:
                if queue_position == 'front':
                    self.queue.appendleft(agent_id)
                else:
                    self.queue.append(agent_id)
        elif queue_position == 'front':
            self.queue.appendleft(agent_id)
        else:
            self.queue.append(agent_id)
        self.message_ledger.append({
            'message_id': message_id,
            'sender': sender,
            'recipient': agent_id,
            'message_type': message.get('type'),
            'content': copy.deepcopy({k: v for k, v in message.items() if not k.startswith('_')}),
            'sent_turn': self.turns,
            'delivered_turn': self.turns,
            'read_turn': None,
            'read_by': None,
            'invocation_id': invocation_id,
        })
        return message_id

    def mark_execution(self, agent_id, turn, success, error=None):
        record = {
            'agent_id': agent_id,
            'turn': turn,
            'status': 'completed' if success else 'failed',
            'input_message_ids': list(self.last_read_message_ids),
            'input_invocation_ids': list(self.last_read_invocation_ids),
            'error': error,
        }
        self.execution_ledger.append(record)
        for invocation_id in self.last_read_invocation_ids:
            inv = self._find_invocation_record(invocation_id)
            if inv:
                inv['execution_turn'] = turn
                inv['execution_status'] = 'completed' if success else 'failed'
                inv['execution_agent'] = agent_id
        return record

    def _has_pending_work(self):
        return bool(self.queue)

    def apply_actions(self, actor, envelope):
        amap = agent_map(self.domain)
        actions = envelope.get('actions') or []
        if not isinstance(actions, list):
            raise ValueError('actions must be a list')
        for original_action in actions:
            if self.terminated:
                break
            action = copy.deepcopy(original_action)
            kind = action.get('type')
            before = self._snapshot()
            if kind == 'message':
                target = action.get('to')
                if target not in amap or target not in self.active_agents:
                    self.log_event(actor, action, realized=False, note='message_target_not_active', before=before)
                    continue
                message_id = self.enqueue(
                    target,
                    {'type': 'agent_message', 'from': actor, 'content': action.get('content', '')},
                    sender=actor,
                )
                if message_id:
                    action['message_id'] = message_id
                self.log_event(actor, action, realized=bool(message_id), note=None if message_id else 'queue_capacity_exhausted', before=before)
            elif kind == 'invoke_agent':
                target = action.get('agent_id')
                if target not in amap:
                    self.log_event(actor, action, realized=False, note='unknown_agent', before=before)
                    continue
                if self.total_invocations >= self.config['max_total_invocations']:
                    self.log_event(actor, action, realized=False, note='invocation_budget_exhausted', before=before)
                    continue
                invocation_id = self._next_invocation_id()
                message_id = self.enqueue(
                    target,
                    {'type': 'invocation', 'from': actor, 'request': action.get('request', '')},
                    sender=actor,
                    invocation_id=invocation_id,
                )
                action['invocation_id'] = invocation_id
                if message_id:
                    action['message_id'] = message_id
                    self.total_invocations += 1
                    self.active_agents.add(target)
                event = self.log_event(actor, action, realized=bool(message_id), note=None if message_id else 'queue_capacity_exhausted', before=before)
                self.invocation_ledger.append({
                    'invocation_id': invocation_id,
                    'proposal_event_index': event['event_index'],
                    'requester': actor,
                    'target': target,
                    'request': action.get('request', ''),
                    'queued': bool(message_id),
                    'message_id': message_id,
                    'read_turn': None,
                    'execution_turn': None,
                    'execution_status': 'pending' if message_id else 'not_queued',
                    'execution_agent': None,
                })
            elif kind == 'write_state':
                key = action.get('key')
                if not key:
                    self.log_event(actor, action, realized=False, note='missing_state_key', before=before)
                    continue
                self.shared_state[key] = copy.deepcopy(action.get('value'))
                self.shared_state_metadata[key] = {
                    'status': action.get('status', 'unspecified'),
                    'basis': copy.deepcopy(action.get('basis')),
                    'writer': actor,
                    'event_index': len(self.events),
            'recorded_at': datetime.now(timezone.utc).isoformat(),
                }
                self.log_event(actor, action, before=before)
            elif kind == 'revise_final_state':
                patch = action.get('patch') or {}
                if self.final_state is None or not isinstance(patch, dict):
                    self.log_event(actor, action, realized=False, note='no_final_state_or_invalid_patch', before=before)
                    continue
                state = self.final_state.setdefault('state', {})
                for key, value in patch.items():
                    state[key] = copy.deepcopy(value)
                    self.shared_state[key] = copy.deepcopy(value)
                    self.shared_state_metadata[key] = {
                        'status': action.get('status', 'unspecified'),
                        'basis': action.get('reason'),
                        'writer': actor,
                        'event_index': len(self.events),
            'recorded_at': datetime.now(timezone.utc).isoformat(),
                    }
                    self.final_state.setdefault('state_metadata', {})[key] = copy.deepcopy(self.shared_state_metadata[key])
                self.final_state['revision_count'] = self.final_state.get('revision_count', 0) + 1
                self.log_event(actor, action, before=before)
            elif kind == 'finalize':
                if self.final_state is not None and not self.late_event_consumed:
                    self.log_event(actor, action, realized=False, note='awaiting_late_event_consumption', before=before)
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
                if not self.late_event_delivered:
                    self.log_event(actor, action, before=before)
                    late = copy.deepcopy(self.domain['task']['late_event'])
                    self.late_event_delivered = True
                    late_message_id = self.enqueue(
                        actor,
                        {'type': 'environment_late_event', **late},
                        sender='ENVIRONMENT',
                        queue_position='front',
                    )
                    late_action = copy.deepcopy(late)
                    late_action['type'] = 'late_event'
                    late_action['message_id'] = late_message_id
                    self.log_event('ENVIRONMENT', late_action, realized=bool(late_message_id), note='fixed_environment_event_after_first_finalize' if late_message_id else 'queue_capacity_exhausted', before=self._snapshot())
                    if not late_message_id:
                        self.late_event_delivered = False
                else:
                    policy = self.config.get('termination_policy', 'immediate_after_late_event')
                    if policy == 'observe_until_quiescent':
                        self.log_event(actor, action, note='plan_settled_episode_observation_continues', before=before)
                    elif policy == 'await_pending_work_before_terminal_finalize' and self._has_pending_work():
                        self.log_event(actor, action, note='terminal_finalize_deferred_pending_work', before=before)
                    else:
                        self.terminated = True
                        self.termination_reason = 'finalized_after_late_event'
                        self.log_event(actor, action, before=before)
                break
            else:
                self.log_event(actor, action, realized=False, note='unknown_action_type', before=before)

    def evidence_snapshot(self):
        unread = [copy.deepcopy(x) for x in self.message_ledger if x.get('read_turn') is None]
        pending_invocations = [copy.deepcopy(x) for x in self.invocation_ledger if x.get('queued') and x.get('execution_turn') is None]
        return {
            'remaining_queue': list(self.queue),
            'unread_messages': unread,
            'pending_invocations': pending_invocations,
            'message_ledger': copy.deepcopy(self.message_ledger),
            'invocation_ledger': copy.deepcopy(self.invocation_ledger),
            'execution_ledger': copy.deepcopy(self.execution_ledger),
            'failures': copy.deepcopy(self.failures),
        }

