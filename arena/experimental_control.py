import copy
from collections import deque

from .core import ArenaState, stable_hash


SNAPSHOT_SCHEMA = 'RB-EXPERIMENTAL-STATE-SNAPSHOT-v0.1'
BRANCH_SCHEMA_V1 = 'RB-EXPERIMENTAL-BRANCH-v0.1'
BRANCH_SCHEMA = 'RB-EXPERIMENTAL-BRANCH-v0.2'
GATE_SCHEMA = 'RB-EXPERIMENTAL-COMMIT-GATE-v0.1'


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _hash_payload(value, excluded_key):
    material = copy.deepcopy(value)
    material.pop(excluded_key, None)
    return stable_hash(material)


def capture_state(state, *, anchor_ref=None, parent_trace_hash=None):
    """Freeze the deterministic Arena environment state at an explicit boundary.

    This captures the Arena/runtime state needed for an experimental branch. It does
    not and cannot capture provider-internal randomness or hidden model state.
    """
    _require(isinstance(state, ArenaState), 'state_must_be_arena_state')
    snapshot = {
        'schema': SNAPSHOT_SCHEMA,
        'run_id': state.run_id,
        'domain_id': state.domain['domain_id'],
        'anchor_ref': anchor_ref,
        'parent_trace_hash': parent_trace_hash,
        'turns': state.turns,
        'shared_state': copy.deepcopy(state.shared_state),
        'shared_state_metadata': copy.deepcopy(state.shared_state_metadata),
        'final_state': copy.deepcopy(state.final_state),
        'active_agents': sorted(state.active_agents),
        'inboxes': {agent_id: list(copy.deepcopy(items)) for agent_id, items in state.inboxes.items()},
        'queue': list(state.queue),
        'events': copy.deepcopy(state.events),
        'total_invocations': state.total_invocations,
        'late_event_delivered': state.late_event_delivered,
        'late_event_consumed': state.late_event_consumed,
        'terminated': state.terminated,
        'termination_reason': state.termination_reason,
        'last_finalizer': state.last_finalizer,
        'failures': copy.deepcopy(state.failures),
        'budget_hits': copy.deepcopy(state.budget_hits),
        'message_ledger': copy.deepcopy(state.message_ledger),
        'invocation_ledger': copy.deepcopy(state.invocation_ledger),
        'execution_ledger': copy.deepcopy(state.execution_ledger),
        'message_seq': state._message_seq,
        'invocation_seq': state._invocation_seq,
        'last_read_message_ids': list(state.last_read_message_ids),
        'last_read_invocation_ids': list(state.last_read_invocation_ids),
        'replay_scope': 'deterministic_arena_state_only',
        'provider_internal_state_captured': False,
    }
    snapshot['state_hash'] = _hash_payload(snapshot, 'state_hash')
    return snapshot


def verify_state_snapshot(snapshot):
    _require(isinstance(snapshot, dict), 'snapshot_must_be_object')
    _require(snapshot.get('schema') == SNAPSHOT_SCHEMA, 'snapshot_schema_invalid')
    expected = _hash_payload(snapshot, 'state_hash')
    _require(snapshot.get('state_hash') == expected, 'snapshot_state_hash_mismatch')
    _require(snapshot.get('provider_internal_state_captured') is False, 'provider_state_claim_must_be_false')
    _require(isinstance(snapshot.get('queue'), list), 'snapshot_queue_missing')
    _require(isinstance(snapshot.get('inboxes'), dict), 'snapshot_inboxes_missing')
    return True


def restore_state(domain, config, run_id, snapshot, recorder=None):
    """Restore only recorded Arena state; provider state is intentionally external."""
    verify_state_snapshot(snapshot)
    _require(snapshot.get('domain_id') == domain.get('domain_id'), 'snapshot_domain_mismatch')

    state = ArenaState(domain, config, run_id, recorder=recorder)
    state.shared_state = copy.deepcopy(snapshot['shared_state'])
    state.shared_state_metadata = copy.deepcopy(snapshot['shared_state_metadata'])
    state.final_state = copy.deepcopy(snapshot['final_state'])
    state.active_agents = set(snapshot['active_agents'])
    state.inboxes = {
        agent_id: deque(copy.deepcopy(snapshot['inboxes'].get(agent_id, [])))
        for agent_id in state.inboxes
    }
    state.queue = deque(snapshot['queue'])
    state.events = copy.deepcopy(snapshot['events'])
    state.turns = int(snapshot['turns'])
    state.total_invocations = int(snapshot['total_invocations'])
    state.late_event_delivered = bool(snapshot['late_event_delivered'])
    state.late_event_consumed = bool(snapshot['late_event_consumed'])
    state.terminated = bool(snapshot['terminated'])
    state.termination_reason = snapshot.get('termination_reason')
    state.last_finalizer = snapshot.get('last_finalizer')
    state.failures = copy.deepcopy(snapshot['failures'])
    state.budget_hits = copy.deepcopy(snapshot['budget_hits'])
    state.message_ledger = copy.deepcopy(snapshot['message_ledger'])
    state.invocation_ledger = copy.deepcopy(snapshot['invocation_ledger'])
    state.execution_ledger = copy.deepcopy(snapshot['execution_ledger'])
    state._message_seq = int(snapshot['message_seq'])
    state._invocation_seq = int(snapshot['invocation_seq'])
    state.last_read_message_ids = list(snapshot['last_read_message_ids'])
    state.last_read_invocation_ids = list(snapshot['last_read_invocation_ids'])
    return state


def make_branch_manifest(
    *,
    branch_id,
    parent_trace_hash,
    parent_snapshot,
    intervention_spec,
    branch_start_snapshot=None,
    replicate_index=0,
    model_identity=None,
    config_identity=None,
    code_identity=None,
):
    """Bind a branch to both the frozen parent and the actual continuation start.

    v0.2 fixes an ambiguity in v0.1: after a state intervention, the branch start
    state is no longer identical to the parent state. Both hashes are now explicit.
    """
    verify_state_snapshot(parent_snapshot)
    branch_start_snapshot = branch_start_snapshot or parent_snapshot
    verify_state_snapshot(branch_start_snapshot)
    _require(parent_snapshot.get('domain_id') == branch_start_snapshot.get('domain_id'), 'branch_domain_mismatch')
    _require(branch_id and isinstance(branch_id, str), 'branch_id_required')
    _require(parent_trace_hash and isinstance(parent_trace_hash, str), 'parent_trace_hash_required')
    _require(isinstance(intervention_spec, dict), 'intervention_spec_must_be_object')
    _require(int(replicate_index) >= 0, 'replicate_index_invalid')

    intervention_hash = stable_hash(intervention_spec)
    parent_hash = parent_snapshot['state_hash']
    start_hash = branch_start_snapshot['state_hash']
    manifest = {
        'schema': BRANCH_SCHEMA,
        'branch_id': branch_id,
        'parent_trace_hash': parent_trace_hash,
        'parent_state_hash': parent_hash,
        'branch_start_state_hash': start_hash,
        'anchor_ref': parent_snapshot.get('anchor_ref'),
        'branch_start_anchor_ref': branch_start_snapshot.get('anchor_ref'),
        'intervention_spec': copy.deepcopy(intervention_spec),
        'intervention_hash': intervention_hash,
        'intervention_applied_before_continuation': parent_hash != start_hash,
        'replicate_index': int(replicate_index),
        'created_from_frozen_parent': True,
        'model_identity': copy.deepcopy(model_identity),
        'config_identity': copy.deepcopy(config_identity),
        'code_identity': copy.deepcopy(code_identity),
        'provider_internal_state_replayed': False,
    }
    manifest['branch_hash'] = _hash_payload(manifest, 'branch_hash')
    return manifest


def verify_branch_manifest(manifest, parent_snapshot=None, branch_start_snapshot=None):
    _require(isinstance(manifest, dict), 'branch_manifest_must_be_object')
    schema = manifest.get('schema')
    _require(schema in (BRANCH_SCHEMA_V1, BRANCH_SCHEMA), 'branch_schema_invalid')
    _require(manifest.get('created_from_frozen_parent') is True, 'branch_parent_freeze_required')
    _require(manifest.get('provider_internal_state_replayed') is False, 'provider_replay_claim_must_be_false')
    _require(manifest.get('intervention_hash') == stable_hash(manifest.get('intervention_spec')), 'branch_intervention_hash_mismatch')
    _require(manifest.get('branch_hash') == _hash_payload(manifest, 'branch_hash'), 'branch_hash_mismatch')

    if schema == BRANCH_SCHEMA:
        _require(manifest.get('branch_start_state_hash'), 'branch_start_state_hash_required')
        expected_applied = manifest.get('parent_state_hash') != manifest.get('branch_start_state_hash')
        _require(
            manifest.get('intervention_applied_before_continuation') is expected_applied,
            'branch_intervention_application_flag_mismatch',
        )

    if parent_snapshot is not None:
        verify_state_snapshot(parent_snapshot)
        _require(manifest.get('parent_state_hash') == parent_snapshot.get('state_hash'), 'branch_parent_state_hash_mismatch')

    if branch_start_snapshot is not None:
        verify_state_snapshot(branch_start_snapshot)
        expected_start = manifest.get('branch_start_state_hash') if schema == BRANCH_SCHEMA else manifest.get('parent_state_hash')
        _require(expected_start == branch_start_snapshot.get('state_hash'), 'branch_start_state_hash_mismatch')
    return True


def apply_state_intervention(snapshot, intervention_spec):
    """Return a new frozen parent state after one explicit state-level intervention.

    Supported v0.1 interventions are intentionally narrow and deterministic.
    """
    verify_state_snapshot(snapshot)
    _require(isinstance(intervention_spec, dict), 'intervention_spec_must_be_object')
    kind = intervention_spec.get('type')
    out = copy.deepcopy(snapshot)

    if kind == 'set_shared_state':
        key = intervention_spec.get('key')
        _require(key, 'intervention_key_required')
        out['shared_state'][key] = copy.deepcopy(intervention_spec.get('value'))
        if 'metadata' in intervention_spec:
            out['shared_state_metadata'][key] = copy.deepcopy(intervention_spec['metadata'])
    elif kind == 'remove_shared_state_key':
        key = intervention_spec.get('key')
        _require(key, 'intervention_key_required')
        out['shared_state'].pop(key, None)
        out['shared_state_metadata'].pop(key, None)
    elif kind == 'set_shared_state_status':
        key = intervention_spec.get('key')
        _require(key in out['shared_state_metadata'], 'intervention_metadata_key_missing')
        out['shared_state_metadata'][key]['status'] = intervention_spec.get('status')
    elif kind == 'set_terminated':
        out['terminated'] = bool(intervention_spec.get('value'))
        out['termination_reason'] = intervention_spec.get('termination_reason')
    else:
        raise ValueError('unsupported_intervention_type:' + str(kind))

    out['anchor_ref'] = intervention_spec.get('result_anchor_ref', out.get('anchor_ref'))
    out['state_hash'] = _hash_payload(out, 'state_hash')
    return out


def decide_commit(proposal, policy, *, current_state_hash=None):
    """Minimal deterministic commit gate for R5-style intervention experiments.

    This gate is not enabled in the Free-Agent baseline. It exists only when an
    experiment explicitly supplies a policy and routes a proposal through it.
    """
    _require(isinstance(proposal, dict), 'proposal_must_be_object')
    _require(isinstance(policy, dict), 'policy_must_be_object')

    reasons = []
    action_type = proposal.get('action_type')
    authority_class = proposal.get('authority_class')
    allowed_actions = set(policy.get('allowed_action_types') or [])
    allowed_authorities = set(policy.get('allowed_authority_classes') or [])

    if policy.get('default_decision') != 'BLOCK':
        reasons.append('DEFAULT_MUST_BLOCK')
    if allowed_actions and action_type not in allowed_actions:
        reasons.append('ACTION_NOT_ALLOWED')
    if allowed_authorities and authority_class not in allowed_authorities:
        reasons.append('AUTHORITY_CLASS_NOT_ALLOWED')
    if policy.get('require_source_refs') and not proposal.get('source_refs'):
        reasons.append('SOURCE_REFS_REQUIRED')
    if policy.get('require_expected_state_hash'):
        expected = proposal.get('expected_state_hash')
        if not expected:
            reasons.append('EXPECTED_STATE_HASH_REQUIRED')
        elif current_state_hash is None or expected != current_state_hash:
            reasons.append('STATE_HASH_MISMATCH')

    decision = 'PASS' if not reasons else 'BLOCK'
    result = {
        'schema': GATE_SCHEMA,
        'decision': decision,
        'reasons': reasons,
        'action_type': action_type,
        'authority_class': authority_class,
        'proposal_hash': stable_hash(proposal),
        'policy_hash': stable_hash(policy),
        'current_state_hash': current_state_hash,
    }
    result['decision_hash'] = stable_hash(result)
    return result
