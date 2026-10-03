"""Host-side offline proposal authorization within a pre-diagnosis envelope.

The envelope grants native surfaces, never a correct replacement value. The
compiler freezes exact versions, fields, values and dependencies after source
inspection. Its retained authorization, rather than a re-sealed agent payload,
is required at dispatch. This is an application boundary, not an OS sandbox.
"""
import copy

from stage2.r7_checkpoint_v1.common import digest, stable_json_bytes
from stage2.native_v7.software_host_v1 import TASKS
from stage2.route_repair.branch_fields import (
    require, seal, verify_seal, exact_path, build_branch_policy, pointer_parts,
)
from stage2.route_repair.native_host_branch import build_host_answer_policy
from stage2.route_repair.offline_system import revalidate_bundle, OfflineRouteRepairSystem


def freeze_task_envelope(context, original_task, *, writable_refs, branch_id,
                         max_actions, max_value_bytes, host_answer_allowed=False):
    """Called by the host before handing evidence to a planning actor.

    The caller must decide task capabilities independently. File membership and
    semantic explanations alone do not authorize a capability. The offline
    fixture can supply the original host's existing application file surfaces.
    """
    require(original_task == TASKS.get(original_task.get('id')), 'ENVELOPE_TASK_MISMATCH')
    require(type(max_actions) is int and 1 <= max_actions <= 8, 'ENVELOPE_ACTION_BOUND_REQUIRED')
    require(type(max_value_bytes) is int and 1 <= max_value_bytes <= 1_000_000,
            'ENVELOPE_VALUE_BOUND_REQUIRED')
    require(type(host_answer_allowed) is bool and isinstance(branch_id, str) and branch_id,
            'ENVELOPE_BINDING_REQUIRED')
    refs = sorted(set(writable_refs))
    cp = context.case['terminal_checkpoint_hash']
    for ref in refs:
        path = exact_path(ref)
        require(path in context.files_by_checkpoint[cp], 'ENVELOPE_FILE_NOT_IN_PARENT')
    require(refs or host_answer_allowed, 'EMPTY_TASK_CAPABILITIES')
    return seal({'schema': 'stage2-task-capability-envelope-v1',
        'mode': 'OFFLINE_ONLY', 'original_task': copy.deepcopy(original_task),
        'branch_id': branch_id, 'graph_hash': context.graph['graph_hash'],
        'archive_sha256': context.case['archive_sha256'], 'parent_checkpoint_hash': cp,
        'writable_refs': refs, 'operations': ['JSON_LEAF_REPLACE', 'TEXT_SPAN_REPLACE'],
        'host_answer_allowed': host_answer_allowed, 'max_actions': max_actions,
        'max_value_bytes': max_value_bytes,
        'native_surface': 'EXPERIMENT_OWNED_APPLICATION_VIA_HostCheckout.write_file',
        'fixed_before_diagnosis': True, 'replacement_values_prescribed': False,
        'semantic_truth_certified': False, 'foreign_state_writable': False}, 'envelope_hash')


class ProposalAuthorityCompiler:
    """Host-owned compiler, kept outside the planner's tool interface."""
    def __init__(self, context, envelope):
        verify_seal(envelope, 'envelope_hash')
        require(envelope == freeze_task_envelope(context, envelope['original_task'],
            writable_refs=envelope['writable_refs'], branch_id=envelope['branch_id'],
            max_actions=envelope['max_actions'], max_value_bytes=envelope['max_value_bytes'],
            host_answer_allowed=envelope['host_answer_allowed']), 'ENVELOPE_REVALIDATION_FAILED')
        self.context = context
        self._envelope = copy.deepcopy(envelope)
        self._compiled = False

    def compile(self, session, proposal):
        require(not self._compiled, 'ENVELOPE_PROPOSAL_ALREADY_FROZEN')
        require(session.context is self.context and session.task == self._envelope['original_task'],
                'PLANNING_SESSION_BINDING_MISMATCH')
        # Do not trust writable_refs or an envelope returned by the actor.
        e = self._envelope
        actions = proposal['application_actions']
        host_action = proposal.get('host_answer')
        require(0 < len(actions) + bool(host_action) <= e['max_actions'], 'PROPOSAL_ACTION_BUDGET')
        require(not host_action or e['host_answer_allowed'], 'HOST_ANSWER_CAPABILITY_MISSING')
        grants, evidence = [], []
        for action in actions:
            ref = action['target_ref']
            require(ref in e['writable_refs'], 'PROPOSAL_WRITE_OUTSIDE_TASK_ENVELOPE')
            require(action['kind'] in e['operations'], 'PROPOSAL_OPERATION_OUTSIDE_ENVELOPE')
            require(len(stable_json_bytes(action['value'])) <= e['max_value_bytes'], 'PROPOSAL_VALUE_BUDGET')
            current = self.context.read_file(ref)
            locator = current['source_locator']
            witnesses = [w for w in session.witnesses.values() if w['ref'] == ref
                         and w['source_locator'] == locator]
            require(witnesses, 'CURRENT_TARGET_WITNESS_REQUIRED')
            if action['kind'] == 'TEXT_SPAN_REPLACE':
                start, end = action['start'], action['end']
                require(any(w['start'] <= start < end <= w['end'] for w in witnesses),
                        'MUTATION_SPAN_NOT_INSPECTED')
                grant = {'target_ref': ref, 'kind': action['kind'], 'start': start, 'end': end}
            else:
                pointer_parts(action['pointer'])
                # The current JSON document must be read as a whole; a quote of
                # an unrelated leaf cannot silently authorize another field.
                require(any(w['start'] == 0 and w['end'] == len(current['content']) for w in witnesses),
                        'JSON_DOCUMENT_WITNESS_REQUIRED')
                grant = {'target_ref': ref, 'kind': action['kind'], 'pointer': action['pointer']}
            grants.append(grant)
            evidence.append(locator)
        application_policy = None
        if actions:
            application_policy = build_branch_policy(self.context, original_task=session.task,
                branch_id=e['branch_id'], semantic_id='source-inspected-proposal-not-adjudicated',
                route_refs=proposal['route_refs'], grants=grants, evidence=evidence)
        host_policy = None
        if host_action:
            require(isinstance(host_action['value'], str)
                    and len(host_action['value'].encode()) <= e['max_value_bytes'], 'PROPOSAL_VALUE_BUDGET')
            current = [w for w in session.witnesses.values() if w['ref'] == 'state:terminal'
                       and w['source_locator'].get('json_pointer') == '/answer']
            require(current, 'CURRENT_ANSWER_WITNESS_REQUIRED')
            host_policy = build_host_answer_policy(self.context, original_task=session.task,
                answer=host_action['value'], evidence=[w['source_locator'] for w in current],
                depends_on=host_action['depends_on'])
        bundle = session.compile(proposal, trusted_application_policy=application_policy,
                                 trusted_host_policy=host_policy)
        # Reconstruct reads and witnesses from native sources; the actor cannot
        # enlarge permission by editing the in-memory query/read ledger.
        revalidate_bundle(self.context, bundle, application_policy, host_policy)
        self._compiled = True
        return BoundProposalAuthorization(self.context, e, bundle, application_policy, host_policy)


class BoundProposalAuthorization:
    def __init__(self, context, envelope, bundle, application_policy, host_policy):
        self.context = context
        self._bundle = copy.deepcopy(bundle)
        self._application_policy = copy.deepcopy(application_policy)
        self._host_policy = copy.deepcopy(host_policy)
        self._dispatched = False
        self._receipt = seal({'schema': 'stage2-bound-proposal-authorization-v1',
            'envelope_hash': envelope['envelope_hash'], 'proposal_hash': digest(bundle['proposal']),
            'bundle_hash': bundle['bundle_hash'],
            'application_policy_hash': (application_policy or {}).get('policy_hash'),
            'host_policy_hash': (host_policy or {}).get('policy_hash'),
            'exact_actions_hash': digest(bundle['application_plan']['actions'] if bundle['application_plan'] else []),
            'exact_host_answer_hash': digest(host_policy['value']) if host_policy else None,
            'execution_order': copy.deepcopy(bundle['proposal']['execution_order']),
            'permission_source': 'PRE_DIAGNOSIS_HOST_TASK_CAPABILITIES',
            'exact_values_frozen_after_proposal': True, 'semantic_claims_grant_extra_permissions': False,
            'live_execution_enabled': False, 'semantic_repair_effect': 'NOT_EVALUATED'}, 'authorization_hash')

    @property
    def bundle(self):
        return copy.deepcopy(self._bundle)

    @property
    def receipt(self):
        return copy.deepcopy(self._receipt)

    def system(self, supplied_bundle, out, *, verifiers):
        require(not self._dispatched, 'AUTHORIZATION_ALREADY_DISPATCHED')
        require(supplied_bundle == self._bundle, 'HOST_FROZEN_PROPOSAL_MISMATCH')
        require(self._application_policy is not None, 'APPLICATION_COORDINATOR_CAPABILITY_REQUIRED')
        system = OfflineRouteRepairSystem(self.context, copy.deepcopy(supplied_bundle), out,
            application_policy=self._application_policy, host_policy=self._host_policy, verifiers=verifiers)
        self._dispatched = True
        return system
