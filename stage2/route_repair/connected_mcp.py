"""Captured provider planning -> exact MCP repair -> host exit -> native continuation.

The experimental framework, MCP protocol and resume loop remain unchanged. Trial
censoring happens at a returned native turn, without altering its 64-turn ceiling.
"""
import copy
from pathlib import Path
from stage2.r7_checkpoint_v1.common import digest, stable_json_bytes, file_tree_manifest, CheckpointRegistry
from stage2.r7_checkpoint_v1.host_adapter import SoftwareHostCheckpointAdapter
from stage2.native_v7.software_host_v1 import SoftwareEngineeringHost
from stage2.r7_prospective_v1.engineering_b_runner import _resume_host
from stage2.route_repair.branch_fields import require, save, seal, transform, select_grant, FullGraphBranchObserver
from stage2.route_repair.mcp_same_parent import decode_repair_tool_result, verify_mcp_environment, SDK_COMMIT, PROTOCOL_COMMIT
from stage2.route_repair.phased_mcp import PhasedMCPBranch
from stage2.native_v7.x4_mcp.runner import MCPCheckoutProxy
from stage2.route_repair.planning_actor import _persist
import json
from stage2.route_repair.connected_provider import freeze_connected_bindings, ConnectedExchangeSource
from stage2.route_repair.connected_planning import ConnectedPlanningSession, ConnectedAuthorization
from stage2.route_repair.recovery_journal import RecoveryJournal
from stage2.route_repair.system_contract import build_system_contract, assess_continuation, read_capture_member
from stage2.route_repair.native_message import apply_message_policy


class ConnectedMCPCheckout(MCPCheckoutProxy):
    """Byte-exact retained snapshots around the unchanged native proxy."""
    def __init__(self, root, branch):
        super().__init__(root, observer_root=branch.out / 'native_wire')
        self.root, self.branch = Path(root), branch
        self.protocol_initialized = False

    def _invoke(self, tool, arguments):
        self.branch.capture('MCP_ACTION_BEFORE')
        try:
            result = super()._invoke(tool, arguments)
        finally:
            prefix = f'{self.sequence:04d}-{tool}'
            for direction in ['client_to_server', 'server_to_client', 'server_stderr']:
                path = Path(self.observer_root) / (prefix + '.' + direction + '.bin')
                if path.exists():
                    raw = path.read_bytes()
                    retained = self.branch.out / 'retained_wire' / path.name
                    _persist(retained, raw)
                    self.branch.observer.capture('protocol-call:mcp-branch:' + str(self.sequence),
                        raw.decode(), 'MCP_WIRE_' + direction.upper(),
                        receipt={'wire_member': str(retained.relative_to(self.branch.out)),
                                 'wire_sha256': digest(raw),
                                 'origin': self.branch.phase})
            self.branch.capture('MCP_ACTION_AFTER')
        incoming = [json.loads(line) for line in (self.branch.out / 'retained_wire' /
                    (prefix + '.server_to_client.bin')).read_bytes().splitlines() if line.strip()]
        initializations = [r['result'] for r in incoming if r.get('id') == 1 and 'result' in r]
        require(len(initializations) == 1 and initializations[0]['protocolVersion'] == '2025-11-25'
                and initializations[0]['serverInfo']['name'] == 'stage2-x4-checkout',
                'NATIVE_MCP_INITIALIZATION_BINDING_MISMATCH')
        self.protocol_initialized = True
        self.branch.observer.capture('native:mcp_result', stable_json_bytes({
            'tool': tool, 'arguments': arguments, 'result': result,
            'origin': self.branch.phase}).decode(), 'MCP_TOOL_RESULT')
        if tool == 'write_file':
            path = self.root / arguments['path']
            self.branch.observer.capture('file:' + arguments['path'], path.read_bytes().decode(),
                'MCP_NATIVE_APPLICATION_WRITE', written=True,
                receipt={'native_interface': 'native:MCPCheckoutProxy.write_file', 'origin': self.branch.phase})
        return result


class ConnectedObserver(FullGraphBranchObserver):
    def __init__(self, graph, out, origin):
        super().__init__(graph, out, 'connected-same-parent-native-mcp')
        self.origin = origin; self.continued = False

    def capture(self, ref, content, phase, *, receipt=None, action_id=None, written=False):
        if phase == 'NATIVE_MCP_CONTINUATION_BEFORE': self.continued = True
        self.sequence += 1
        path = self.out / 'captures' / f'{self.sequence:06d}.json'
        save(path, {'ref': ref, 'content': content, 'phase': phase, 'action_id': action_id,
                    'native_receipt': receipt, 'provenance': self.origin})
        sha = digest(path.read_bytes())
        observation = {'schema': 'RB-STAGE2-ENHANCED-OBSERVATION-v1',
             'event_ref': f'{self.branch_id}:capture:{self.sequence:06d}', 'trajectory_id': self.branch_id,
             'native_sequence': self.sequence, 'clock_id': 'connected_native_branch_capture', 'event_kind': phase,
             'actor': 'HOST_BOUND_NATIVE_EXECUTOR' if written else 'EXTERNAL_READ_ONLY_OBSERVER',
             'evidence_ref': 'evidence:' + sha, 'object_refs': [ref], 'written_refs': [ref] if written else [],
             'content_hash': digest(content.encode()), 'field_path': (receipt or {}).get('field_path'),
             'version': digest(content.encode()), 'visibility_scope': self.origin + '_DERIVED_BRANCH',
             'source_locator': {'member': str(path.relative_to(self.out)), 'member_sha256': sha,
                                'json_pointer': '/content', 'line': None}, 'semantic_adoption_inferred': False}
        observation['observation_id'] = 'obs:' + digest(observation)
        self.graph.add_observation(observation)
        return observation

    def finish(self):
        row = super().finish()
        row.update(captures_cover='PARENT_REPAIR_RELEASE_AND_NATIVE_CONTINUATION',
                   native_agent_continuation_observed=self.continued, origin=self.origin,
                   observation_does_not_certify_semantic_effect=True)
        save(self.out / 'graph_comparison.json', row)
        return row


class _CapturedConnectedSource:
    def __init__(self, branch, source): self.branch = branch; self.source = source
    @property
    def calls(self): return self.source.calls
    @property
    def provider_calls(self): return self.source.provider_calls

    def complete_agent(self, messages, metadata=None):
        b = self.branch; require(b.phase == 'NATIVE_SUBJECT_CONTINUATION', 'SUBJECT_PROVIDER_BEFORE_HOST_RELEASE')
        before = self.calls
        try:
            return self.source.complete_agent(messages, metadata)
        finally:
            if self.calls > before:
                directory = self.source.out / f'{self.calls:04d}'
                for name in ['request.bin', 'response_headers.json', 'response.bin', 'receipt.json']:
                    path = directory / name
                    if path.exists():
                        raw = path.read_bytes()
                        content = stable_json_bytes({'bytes_hex': raw.hex()}).decode() if name.endswith('.bin') else raw.decode()
                        b.observer.capture('native:connected_provider_exchange', content, 'CONNECTED_PROVIDER_' + name.split('.')[0].upper(),
                             receipt={'exchange_member': str(path.relative_to(b.out)), 'exchange_hash': digest(raw),
                                      'provider_calls': self.provider_calls, 'origin': b._bindings['transport_binding']['origin']})


class TrialHorizonReached(Exception):
    """A returned-turn censor, never a provider failure or restored budget."""


class ConnectedMCPBranch(PhasedMCPBranch):
    def __init__(self, context, planning, bindings, out, *, transport, repo_root, sdk_root, protocol_root, verifiers):
        require(type(planning) is ConnectedPlanningSession and planning.outcome['state'] == 'COMPLETED'
                and planning.outcome['decision'] == 'REPAIR' and planning.outcome['tools_revoked'], 'HOST_CLOSED_REPAIR_PLANNING_REQUIRED')
        authorization = planning.authorization
        require(type(authorization) is ConnectedAuthorization and authorization.context is context
                and not authorization._dispatched, 'CONNECTED_ONE_USE_AUTHORIZATION_REQUIRED')
        authorization.revalidate(authorization.bundle)
        require(bindings == freeze_connected_bindings(context, repo_root, transport), 'HOST_FROZEN_PROVIDER_BINDINGS_DRIFT')
        require(planning._source._profile == bindings['profiles']['planning']
                and planning._source._transport is transport, 'CONNECTED_PLANNING_TRANSPORT_IDENTITY_DRIFT')
        bundle = authorization.bundle
        require(bundle['host_answer_policy'] is None and (bundle['application_plan'] is not None
                or bundle.get('host_message_policy') is not None), 'NONTERMINAL_MCP_NATIVE_BINDING_REQUIRED')
        for task in bundle['proposal']['verification_tasks']:
            binding = verifiers.get(task['verification_id'])
            require(binding is not None and callable(binding.get('run'))
                    and all(binding.get(k) == task[k] for k in ['operation', 'refs', 'postcondition']), 'MCP_HOST_VERIFICATION_CAPABILITY_MISSING')
        environment = verify_mcp_environment(sdk_root, protocol_root)
        self.context, self.parent = context, context.parent; self.authorization = authorization; self.bundle = bundle
        self.verifiers = verifiers; self.out = Path(out); require(not self.out.exists(), 'FRESH_MCP_BRANCH_REQUIRED_NO_REPLAY')
        authorization._dispatched = True; self.out.mkdir(parents=True); self.root = self.out / 'application'; self.root.mkdir()
        for path, raw in self.parent['files'].items():
            target = self.root / path; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
        self.expected = file_tree_manifest(self.root)
        require(self.expected == self.parent['manifest']['application_file_hashes'], 'MCP_PARENT_COPY_DRIFT')
        self._planning = planning; self._bindings = copy.deepcopy(bindings); self._repo_root = Path(repo_root); self._transport = transport
        self.phase = 'RESTORED_AWAITING_REPAIR'; self._repair_attempted = False; self._continuation_attempted = False
        self._closed = False; self._completed = []; self._actions = []; self._checks = []; self._release = None
        self.observer = ConnectedObserver(context.graph, self.out, bindings['transport_binding']['origin'])
        bound = ConnectedExchangeSource(bindings['profiles']['subject'], transport, self.out / 'provider_exchanges',
                    gate=lambda: self.phase == 'NATIVE_SUBJECT_CONTINUATION' and not self._closed)
        self.source = _CapturedConnectedSource(self, bound)
        state = self.parent['state']; self.host = SoftwareEngineeringHost(task_id=state['task_id'], checkout=self.root,
                    provider=self.source, max_turns=1, max_actions=state['max_actions'])
        self.host.max_turns = state['max_turns']; self.adapter = SoftwareHostCheckpointAdapter(); self.adapter.load_state(self.host, state)
        self._expected_host_state = copy.deepcopy(state)
        self.host.checkout = ConnectedMCPCheckout(self.root, self)
        self.contract = build_system_contract(bundle, context.graph)
        self.contract.pop('contract_hash'); self.contract['live_execution_enabled'] = bindings['transport_binding']['live']
        self.contract = seal(self.contract, 'contract_hash'); self._exit_observation_id = None
        self.journal = RecoveryJournal(self.out / 'recovery_journal', {'bundle_hash': bundle['bundle_hash'],
                    'contract_hash': self.contract['contract_hash'], 'parent_checkpoint_hash': context.parent_checkpoint_hash})
        self.registry = CheckpointRegistry(self.out / 'branch_checkpoints')
        for name, value in [('environment_binding', environment), ('planning_bundle', bundle), ('authorization', authorization.receipt),
                            ('system_contract', self.contract), ('provider_bindings', bindings), ('planning_outcome', planning.outcome)]:
            save(self.out / (name + '.json'), value)
        self.capture('NATIVE_MCP_PARENT_RESTORED'); self._record_phase()

    def checkpoint(self, event_ref):
        return self.adapter.capture(system_id='X4_MCP', host=self.host, registry=self.registry,
            application_root=self.root, group_id='CONNECTED_DERIVED_TRIAL', run_id='G3-X4-T2-connected-trial',
            task_id=self.host.task['id'], event_ref=event_ref,
            model_visible_context={'queue': list(self.host.queue), 'inbox': copy.deepcopy(self.host.inbox),
                                   'scope': 'NATIVE_HOST_BRANCH_CHECKPOINT_NOT_NEW_HISTORICAL_EVIDENCE'},
            remaining_horizon=self.host.max_turns - len(self.host.history), external_carrier_refs=[],
            replication_binding={'source_parent': self.context.parent_checkpoint_hash,
                                 'sdk_commit': SDK_COMMIT, 'protocol_commit': PROTOCOL_COMMIT})

    def _record_phase(self, failure=None):
        after = self.adapter.save_state(self.host)
        row = seal({'schema': 'stage2-connected-native-mcp-receipt-v1', 'phase': self.phase,
            'parent_checkpoint_hash': self.context.parent_checkpoint_hash, 'planning_outcome_hash': self._planning.outcome['outcome_hash'],
            'provider_bindings_hash': self._bindings['bindings_hash'], 'completed_steps': self._completed,
            'native_repair_actions': len(self._actions), 'native_mcp_invocations': self.host.checkout.sequence,
            'subject_calls': self.source.calls, 'planning_provider_calls': self._planning._source.provider_calls,
            'subject_provider_calls': self.source.provider_calls, 'provider_calls': self._planning._source.provider_calls + self.source.provider_calls,
            'remaining_before': self.parent['manifest']['remaining_horizon'], 'remaining_after': after['max_turns'] - len(after['history']),
            'native_ceiling_preserved': after['max_turns'] == self.parent['state']['max_turns'],
            'failure': failure, 'release': self._release,
            'actual_repair_agent_exit': bool(self._release and self._release['actual_repair_agent_exit']),
            'agent_generated_proposal': self._planning.outcome['agent_generated_proposal'],
            'origin': self._bindings['transport_binding']['origin'], 'semantic_repair_effect': 'NOT_EVALUATED',
            'repair_success': False, 'automatic_replay': False, 'independent_review_invoked': False}, 'phase_hash')
        save(self.out / 'phase_receipt.json', row); return row

    def _verify_parent_host(self):
        require(self._bindings == freeze_connected_bindings(self.context, self._repo_root, self._transport), 'PHASED_PROVIDER_SOURCE_DRIFT')
        self.authorization.revalidate(self.bundle)
        require(self.adapter.save_state(self.host) == self._expected_host_state, 'PHASED_REPAIR_MUTATED_PARENT_HOST')
        require(file_tree_manifest(self.root) == self.expected, 'PHASED_APPLICATION_DRIFT')
        require(digest(Path(self.context.access.archive.name).read_bytes()) == self.context.case['archive_sha256'], 'PHASED_ARCHIVE_DRIFT')

    def _failure(self, exc):
        self.phase = 'FAILED_NO_REPLAY'; self._closed = True
        error = {'type': type(exc).__name__, 'message': str(exc)}
        self.observer.capture('native:phase_failure', stable_json_bytes(error).decode(), 'NATIVE_FAILURE')
        self.capture('NATIVE_PHASE_FAILURE_AFTER'); self.observer.finish()
        save(self.out / 'native_state_failure.json', self.adapter.save_state(self.host))
        save(self.out / 'failure_checkpoint.json', self.checkpoint('host:connected-phase-failure'))
        self._record_phase(error)

    def repair(self):
        require(not self._repair_attempted and self.phase == 'RESTORED_AWAITING_REPAIR', 'NATIVE_REPAIR_ALREADY_ATTEMPTED')
        self._repair_attempted = True
        try:
            self._verify_parent_host(); self.phase = 'NATIVE_REPAIR_EXECUTION'
            save(self.out / 'branch_intent.json', {'parent_checkpoint_hash': self.context.parent_checkpoint_hash,
                'bundle_hash': self.bundle['bundle_hash'], 'bindings_hash': self._bindings['bindings_hash'],
                'replay_authorized': False})
            for action in (self.bundle['application_plan'] or {}).get('actions', []):
                self._verify_parent_host()
                require(set(action.get('depends_on', [])) <= set(self._completed), 'PHASED_REPAIR_DEPENDENCY_REQUIRED')
                path = action['target_ref'][5:]
                before = decode_repair_tool_result(self.host.checkout.read_file(path), str)
                require(digest(before.encode()) == action['before_file_hash'], 'PHASED_NATIVE_READ_VERSION_DRIFT')
                output, invariant = transform(before, action, select_grant(self.bundle['application_plan']['policy'], action))
                require(digest(output.encode()) == action['expected_output_hash'], 'PHASED_OUTPUT_HASH_DRIFT')
                self.journal.intent(action['action_id'], action['target_ref'], action['before_file_hash'], action['expected_output_hash'])
                native = self.host.checkout.write_file(path, output)
                actual = decode_repair_tool_result(self.host.checkout.read_file(path), str)
                receipt = {'action_id': action['action_id'], 'target_ref': action['target_ref'],
                    'native_interface': 'native:MCPCheckoutProxy.write_file', 'native_result': native,
                    'before_hash': digest(before.encode()), 'after_hash': digest(actual.encode()),
                    'expected_output_hash': action['expected_output_hash'], **invariant}
                self._actions.append(receipt); save(self.out / 'native_repair_receipts.json', self._actions)
                self.journal.complete(action['action_id'], receipt['after_hash'], receipt)
                require(actual == output, 'PHASED_NATIVE_WRITE_POSTCONDITION_FAILED')
                self.expected[path] = digest(actual.encode()); self._verify_parent_host()
                self._completed.append(action['action_id'])
            policy = self.bundle.get('host_message_policy')
            if policy:
                self._verify_parent_host()
                action = policy['action']
                require(set(action['depends_on']) <= set(self._completed), 'PHASED_MESSAGE_DEPENDENCY_REQUIRED')
                self.journal.intent(action['action_id'], action['target_ref'],
                    policy['before_state_hash'], policy['after_state_hash'])
                self._expected_host_state, receipt = apply_message_policy(self.context, self.host,
                    self.adapter, self.root, policy, self.observer)
                self._actions.append(receipt); save(self.out / 'native_repair_receipts.json', self._actions)
                self.journal.complete(action['action_id'], receipt['after_hash'], receipt)
                self._completed.append(action['action_id']); self._verify_parent_host()
            for task in self.bundle['proposal']['verification_tasks']:
                require(set(task['depends_on']) <= set(self._completed), 'PHASED_VERIFICATION_DEPENDENCY_REQUIRED')
                before = file_tree_manifest(self.root)
                value = self.verifiers[task['verification_id']]['run'](self.root)
                require(file_tree_manifest(self.root) == before, 'PHASED_VERIFIER_MUTATED_APPLICATION')
                self._verify_parent_host()
                self._checks.append({'verification_id': task['verification_id'], 'result': value,
                    'classification': 'HOST_DEFINED_ENGINEERING_CHECK_NOT_SEMANTIC_REVIEW'})
                save(self.out / 'verification_receipts.json', self._checks)
                require(value.get('passed') is True, 'PHASED_HOST_VERIFICATION_FAILED')
                self._completed.append(task['verification_id'])
            save(self.out / 'after_repair_checkpoint.json', self.checkpoint('host:connected-repair:post'))
            self.phase = 'REPAIRED_PAUSED_AWAITING_HOST_RELEASE'
            self.capture('NATIVE_REPAIR_PAUSED'); self.observer.finish()
            save(self.out / 'paused_state.json', self.adapter.save_state(self.host))
            return self._record_phase()
        except BaseException as exc:
            self._failure(exc); raise

    def release(self, planning):
        require(self.phase == 'REPAIRED_PAUSED_AWAITING_HOST_RELEASE', 'NATIVE_RELEASE_REQUIRES_PAUSED_REPAIR')
        try:
            require(planning is self._planning and planning.authorization is self.authorization, 'HOST_RELEASE_PLANNING_IDENTITY_DRIFT')
            require(planning.outcome['tools_revoked'] and planning.outcome['state'] == 'COMPLETED'
                    and not planning._source.failed and not planning._source.in_flight
                    and planning._source.valid_responses == planning._source.calls > 0, 'HOST_RELEASE_CLOSED_VALID_PLANNING_REQUIRED')
            self._verify_parent_host()
            require(self._completed == self.bundle['proposal']['execution_order'], 'HOST_RELEASE_STEPS_INCOMPLETE')
            live = self._bindings['transport_binding']['live'] and planning._source.provider_calls > 0
            self._release = seal({'schema': 'stage2-connected-host-release-v1',
                'planning_outcome_hash': planning.outcome['outcome_hash'], 'authorization_hash': self.authorization.receipt['authorization_hash'],
                'completed_steps': self._completed,
                'parent_host_state_preserved': self._expected_host_state == self.parent['state'],
                'unrelated_host_fields_preserved': True,
                'authorized_host_message_policy_hash': (self.bundle.get('host_message_policy') or {}).get('policy_hash'),
                'provider_bindings_hash': self._bindings['bindings_hash'], 'tools_revoked': True,
                'actual_repair_agent_exit': live, 'origin': self._bindings['transport_binding']['origin'],
                'exit_asserted_by': 'HOST_AFTER_NATIVE_COMPLETION_NOT_ACTOR_JSON',
                'semantic_effect_certified': False}, 'release_hash')
            self.journal.append('HOST_RELEASE', self._release)
            event = self.observer.capture('native:host_repair_exit', stable_json_bytes(self._release).decode(),
                                  'REPAIR_AGENT_EXIT' if live else 'OFFLINE_REPAIR_DRIVER_EXIT')
            self._exit_observation_id = event['observation_id'] if live else None
            self.phase = 'HOST_RELEASED_AWAITING_CONTINUATION'; self._record_phase(); return copy.deepcopy(self._release)
        except BaseException as exc:
            self._failure(exc); raise

    async def continue_native(self):
        require(self.phase == 'HOST_RELEASED_AWAITING_CONTINUATION' and not self._continuation_attempted,
                'NATIVE_CONTINUATION_REQUIRES_HOST_RELEASE')
        self._continuation_attempted = True
        try:
            self._verify_parent_host(); self.phase = 'NATIVE_SUBJECT_CONTINUATION'; self.capture('NATIVE_MCP_CONTINUATION_BEFORE')
            async def boundary(**payload):
                self.capture('NATIVE_MCP_TERMINAL_RETURN' if payload['boundary'] == 'TERMINAL' else 'NATIVE_MCP_TURN_RETURN')
                if payload['boundary'] != 'TERMINAL' and not self.host.stop_reason and self.source.calls >= self._bindings['profiles']['subject']['max_logical_calls']:
                    raise TrialHorizonReached()
            censored = False
            try:
                result = await _resume_host(self.host, boundary)
            except TrialHorizonReached:
                censored = True
                result = {'trial_censor': 'PRE_FROZEN_RETURNED_NATIVE_TURN_LIMIT', 'native_stop_reason': self.host.stop_reason,
                          'remaining_horizon': self.host.max_turns - len(self.host.history)}
            self.observer.capture('native:closure', stable_json_bytes(result).decode(),
                    'NATIVE_CENSOR' if censored or self.host.stop_reason not in {'finalized', 'queue_exhausted'} else 'NATIVE_CLOSURE')
            self.phase = ('NATIVE_CONTINUATION_CAPTURED_PENDING_INDEPENDENT_REVIEW' if self._exit_observation_id
                          else 'NATIVE_CONTINUATION_CAPTURED_PENDING_ACTUAL_EXIT_AND_REVIEW'); self._closed = True
            self.capture('NATIVE_CONNECTED_BRANCH_AFTER'); self.observer.finish(); after = self.adapter.save_state(self.host)
            require(after['history'][:len(self.parent['state']['history'])] == self.parent['state']['history']
                and after['max_turns'] == self.parent['state']['max_turns'] and after['max_actions'] == self.parent['state']['max_actions']
                and len(after['history']) <= after['max_turns'], 'PHASED_NATIVE_HISTORY_OR_BUDGET_DRIFT')
            require(self._bindings == freeze_connected_bindings(self.context, self._repo_root, self._transport), 'PHASED_PROVIDER_SOURCE_DRIFT')
            require(digest(Path(self.context.access.archive.name).read_bytes()) == self.context.case['archive_sha256'], 'PHASED_ARCHIVE_DRIFT')
            save(self.out / 'native_state_after.json', after); save(self.out / 'final_checkpoint.json', self.checkpoint('host:trial-censor' if censored else 'host:terminal'))
            save(self.out / 'continuation_assessment.json', assess_continuation(self.contract, self.context.graph,
                self.observer.graph.snapshot(), source_reader=lambda o: read_capture_member(self.out, o), exit_observation_id=self._exit_observation_id))
            return self._record_phase()
        except BaseException as exc:
            self._failure(exc); raise


class ConnectedPlanningRepairEntry:
    """Current host entry: a repair decision returns at the paused boundary.

    Previous one-call entry code is used only to reproduce frozen predecessors;
    this entry has no fallback to it. No-action outcomes create no native branch.
    """
    def __init__(self, context, planning, bindings, out, *, repo_root, transport):
        require(type(planning) is ConnectedPlanningSession, 'HOST_PHASED_PLANNING_SESSION_REQUIRED')
        require(bindings == freeze_connected_bindings(context, repo_root, transport), 'HOST_FROZEN_PROVIDER_BINDINGS_DRIFT')
        require(planning._session.context is context and planning._binding['actor_id'] == bindings['profiles']['planning']['actor_id']
                and planning._binding['max_calls'] <= bindings['profiles']['planning']['max_logical_calls'],
                'PHASED_ENTRY_PLANNING_BINDING_DRIFT')
        self.context = context; self._planning = planning; self._bindings = copy.deepcopy(bindings)
        self._transport = transport; self._repo_root = Path(repo_root); self.out = Path(out)
        require(not self.out.exists(), 'FRESH_PHASED_ENTRY_REQUIRED')
        self.out.mkdir(parents=True); self._started = False; self._branch = None; self._state = 'PREPARED'

    def _record_entry(self, failure=None):
        outcome = self._planning._outcome or {}
        row = seal({'schema':'stage2-connected-planning-entry-v1', 'state':self._state,
            'planning_outcome_hash':outcome.get('outcome_hash'), 'decision':outcome.get('decision'),
            'provider_bindings_hash':self._bindings['bindings_hash'],
            'native_branch_created':(self.out/'native_branch').exists(), 'failure':failure,
            'provider_calls':self._planning._source.provider_calls + (self._branch.source.provider_calls if self._branch else 0),
            'actual_repair_agent_exit':bool(self._branch and self._branch._release and self._branch._release['actual_repair_agent_exit']), 'repair_success':False,
            'automatic_replay':False, 'live_trial_ready':self._bindings['transport_binding']['live']},'entry_hash')
        save(self.out/'entry_receipt.json',row); return row

    async def plan_and_repair(self, *, sdk_root=None, protocol_root=None, verifiers=None):
        require(not self._started,'PHASED_ENTRY_ALREADY_STARTED'); self._started=True
        try:
            # A completed host session may be handed to the dispatcher. A failed
            # or unfinished session is never rerun to make a proposal available.
            outcome = self._planning.outcome if self._planning._started else await self._planning.run()
            require(outcome['state']=='COMPLETED','HOST_COMPLETED_PHASED_PLANNING_REQUIRED')
            if outcome['decision']=='REPAIR':
                self._branch=ConnectedMCPBranch(self.context,self._planning,self._bindings,self.out/'native_branch',
                    transport=self._transport,repo_root=self._repo_root,sdk_root=sdk_root,protocol_root=protocol_root,
                    verifiers=verifiers or {})
                self._branch.repair(); self._state='REPAIRED_PAUSED_AWAITING_HOST_RELEASE'
            else:
                require(self._planning.authorization is None,'NO_ACTION_CANNOT_HAVE_AUTHORIZATION')
                self._state='CLOSED_WITHOUT_REPAIR'
            return self._record_entry()
        except BaseException as exc:
            self._state='FAILED_NO_REPLAY'
            self._record_entry({'type':type(exc).__name__,'message':str(exc)}); raise

    def release(self):
        require(self._state=='REPAIRED_PAUSED_AWAITING_HOST_RELEASE' and self._branch is not None,
                'PHASED_ENTRY_REQUIRES_PAUSED_REPAIR')
        try:
            release=self._branch.release(self._planning); self._state='HOST_RELEASED_AWAITING_CONTINUATION'
            self._record_entry(); return release
        except BaseException as exc:
            self._state='FAILED_NO_REPLAY'
            self._record_entry({'type':type(exc).__name__,'message':str(exc)}); raise

    async def continue_native(self):
        require(self._state=='HOST_RELEASED_AWAITING_CONTINUATION' and self._branch is not None,
                'PHASED_ENTRY_REQUIRES_HOST_RELEASE')
        try:
            receipt=await self._branch.continue_native(); self._state=receipt['phase']
            self._record_entry(); return receipt
        except BaseException as exc:
            self._state='FAILED_NO_REPLAY'
            self._record_entry({'type':type(exc).__name__,'message':str(exc)}); raise
