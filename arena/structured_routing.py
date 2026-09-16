import copy
import json

from .core import ArenaState, stable_hash
from .engine import run_arena_once
from .experimental_control import capture_state


POLICY_SCHEMA = 'RB-STRUCTURED-ROUTING-POLICY-v0.1'


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _decode_envelope(content):
    if isinstance(content, dict):
        obj = copy.deepcopy(content)
    else:
        raw = str(content).strip()
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            obj = None
            if '```' in raw:
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
        raise ValueError('structured routing subject response must be JSON object')
    obj.setdefault('decision_summary', '')
    obj.setdefault('actions', [])
    if not isinstance(obj['actions'], list):
        raise ValueError('structured routing actions must be a list')
    return obj


def validate_structured_policy(domain, policy):
    _require(isinstance(policy, dict), 'structured_policy_must_be_object')
    _require(policy.get('schema') == POLICY_SCHEMA, 'structured_policy_schema_invalid')
    _require(policy.get('mode') == 'system_owned_routing', 'structured_policy_mode_invalid')
    _require(policy.get('dynamic_invocation_allowed') is False, 'dynamic_invocation_must_be_false')
    stages = policy.get('stages')
    _require(isinstance(stages, list) and stages, 'structured_policy_stages_required')

    agent_ids = {a['id'] for a in domain['agents']}
    stage_ids = []
    for idx, stage in enumerate(stages):
        _require(isinstance(stage, dict), f'stage_{idx}_must_be_object')
        _require(stage.get('stage_id'), f'stage_{idx}_id_required')
        _require(stage.get('agent_id') in agent_ids, f'stage_{idx}_unknown_agent')
        _require(stage.get('goal'), f'stage_{idx}_goal_required')
        allowed = stage.get('allowed_action_types')
        _require(isinstance(allowed, list) and allowed, f'stage_{idx}_allowed_actions_required')
        stage_ids.append(stage['stage_id'])
    _require(len(stage_ids) == len(set(stage_ids)), 'duplicate_stage_id')

    final_stage = policy.get('final_stage_id')
    _require(final_stage in set(stage_ids), 'final_stage_id_invalid')
    final_spec = next(x for x in stages if x['stage_id'] == final_stage)
    _require('finalize' in final_spec['allowed_action_types'], 'final_stage_must_allow_finalize')
    return True


def _stage_message(domain, policy, stage, stage_index):
    return {
        'type': 'system_stage_assignment',
        'stage_id': stage['stage_id'],
        'stage_index': stage_index,
        'stage_count': len(policy['stages']),
        'overall_goal': domain['task']['goal'],
        'stage_goal': stage['goal'],
        'handoff_policy': 'Use the shared state produced by earlier stages. Do not create new stages or Agents; the experiment system owns routing and handoff order.',
        'allowed_action_types': list(stage['allowed_action_types']),
    }


def prepare_structured_state(domain, config, run_id, policy, recorder=None):
    """Create a deterministic stage queue while leaving Agent reasoning inside each stage free."""
    validate_structured_policy(domain, policy)
    state = ArenaState(domain, config, run_id, recorder=recorder)

    # Keep the original task_start message in the entry Agent inbox as provenance,
    # but replace the default execution queue with the system-owned stage order.
    state.queue.clear()
    stage_agents = [stage['agent_id'] for stage in policy['stages']]
    state.active_agents = set(stage_agents)

    for idx, stage in enumerate(policy['stages']):
        message_id = state.enqueue(
            stage['agent_id'],
            _stage_message(domain, policy, stage, idx),
            sender='ENVIRONMENT',
            queue_position='back',
        )
        _require(message_id is not None, f'failed_to_enqueue_stage:{stage["stage_id"]}')

    return state


class StructuredRoutingProvider:
    """External deterministic action gate for the structured-routing condition.

    The upstream subject output is preserved inside provider_response while only
    policy-allowed actions are passed into ArenaState. This separates proposal from
    realized system effect without changing the baseline engine or subject labels.
    """

    def __init__(self, upstream, policy):
        self.upstream = upstream
        self.policy = copy.deepcopy(policy)
        self._stages_by_agent = {}
        for stage in self.policy['stages']:
            self._stages_by_agent.setdefault(stage['agent_id'], []).append(stage)

    def _stage_for_call(self, agent_id, messages):
        for message in messages:
            content = message.get('content')
            if isinstance(content, dict) and content.get('type') == 'system_stage_assignment':
                stage_id = content.get('stage_id')
                for stage in self.policy['stages']:
                    if stage['stage_id'] == stage_id:
                        return stage
            if isinstance(content, str) and 'system_stage_assignment' in content:
                # The current prompt renderer may serialize inbox objects to text.
                # Agent identity remains a deterministic fallback.
                break
        candidates = self._stages_by_agent.get(agent_id) or []
        if len(candidates) == 1:
            return candidates[0]
        final_stage_id = self.policy.get('final_stage_id')
        for stage in candidates:
            if stage['stage_id'] == final_stage_id:
                return stage
        raise ValueError(f'cannot_resolve_structured_stage_for_agent:{agent_id}')

    def complete_agent(self, messages, metadata=None):
        metadata = metadata or {}
        agent_id = metadata.get('agent_id')
        stage = self._stage_for_call(agent_id, messages)
        response = self.upstream.complete_agent(messages, metadata=metadata)
        original_content = response.get('content')
        envelope = _decode_envelope(original_content)

        allowed_types = set(stage.get('allowed_action_types') or [])
        allowed_targets = set(stage.get('allowed_invocation_targets') or [])
        allowed_message_targets = set(stage.get('allowed_message_targets') or [])
        passed_actions = []
        blocked_actions = []

        for action in envelope.get('actions') or []:
            kind = action.get('type')
            reason = None
            if kind not in allowed_types:
                reason = 'ACTION_TYPE_NOT_ALLOWED_IN_STAGE'
            elif kind == 'invoke_agent':
                if not self.policy.get('dynamic_invocation_allowed'):
                    reason = 'SYSTEM_OWNS_INVOCATION_GRAPH'
                elif allowed_targets and action.get('agent_id') not in allowed_targets:
                    reason = 'INVOCATION_EDGE_NOT_ALLOWED'
            elif kind == 'message' and allowed_message_targets:
                if action.get('to') not in allowed_message_targets:
                    reason = 'MESSAGE_EDGE_NOT_ALLOWED'

            if reason:
                blocked_actions.append({'action': copy.deepcopy(action), 'reason': reason})
            else:
                passed_actions.append(copy.deepcopy(action))

        realized_envelope = {
            'decision_summary': envelope.get('decision_summary', ''),
            'actions': passed_actions,
        }
        wrapped = copy.deepcopy(response)
        wrapped['content'] = json.dumps(realized_envelope, ensure_ascii=False, separators=(',', ':'))
        wrapped['provider_response'] = {
            'upstream_provider_response': copy.deepcopy(response.get('provider_response')),
            'structured_routing': {
                'policy_schema': self.policy['schema'],
                'policy_hash': stable_hash(self.policy),
                'stage_id': stage['stage_id'],
                'agent_id': agent_id,
                'original_subject_content': original_content,
                'original_subject_envelope': envelope,
                'passed_actions': passed_actions,
                'blocked_actions': blocked_actions,
            },
        }
        return wrapped


def run_structured_once(
    domain,
    config,
    provider,
    policy,
    run_id,
    logical_seed=None,
    recorder=None,
    state_snapshot_callback=None,
):
    validate_structured_policy(domain, policy)
    state = prepare_structured_state(domain, config, run_id, policy, recorder=recorder)
    snapshot = capture_state(
        state,
        anchor_ref='structured_condition_start',
        parent_trace_hash='structured-condition:' + stable_hash({
            'task': domain['task'],
            'agents': domain['agents'],
            'policy': policy,
            'config_version': config.get('version'),
        }),
    )
    controlled_provider = StructuredRoutingProvider(provider, policy)
    trace = run_arena_once(
        domain,
        config,
        controlled_provider,
        run_id,
        logical_seed=logical_seed,
        recorder=recorder,
        initial_state_snapshot=snapshot,
        state_snapshot_callback=state_snapshot_callback,
    )
    trace['orchestration_condition'] = {
        'mode': 'system_owned_routing',
        'policy_schema': policy['schema'],
        'policy_hash': stable_hash(policy),
        'stage_ids': [x['stage_id'] for x in policy['stages']],
        'stage_agents': [x['agent_id'] for x in policy['stages']],
        'dynamic_invocation_allowed': False,
        'start_state_hash': snapshot['state_hash'],
    }
    return trace
