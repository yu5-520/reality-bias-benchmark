"""Explicit offline repair -> host release -> captured native continuation.

The original official MCP interfaces and resume loop remain unchanged. The
older sealed one-call executor is retained only as a frozen predecessor. No
actual agent exit, live provider or semantic repair claim is enabled here.
"""
import copy
import json
from pathlib import Path

from stage2.r7_checkpoint_v1.common import digest, stable_json_bytes, file_tree_manifest
from stage2.r7_prospective_v1.engineering_b_runner import _resume_host
from stage2.route_repair.branch_fields import require, save, seal, transform, select_grant
from stage2.route_repair.mcp_same_parent import SameParentMCPBranch, decode_repair_tool_result
from stage2.route_repair.planning_actor import ReadOnlyPlanningActorSession
from stage2.route_repair.provider_capture import freeze_provider_bindings, BoundExchangeSource, OfflineWireResponses
from stage2.route_repair.system_contract import assess_continuation, read_capture_member


class _CapturedNativeSource:
    def __init__(self, branch, source): self.branch = branch; self.source = source

    @property
    def calls(self): return self.source.calls

    def complete_agent(self, messages, metadata=None):
        b = self.branch
        require(b.phase == 'OFFLINE_SUBJECT_CONTINUATION', 'SUBJECT_PROVIDER_BEFORE_HOST_RELEASE')
        require((metadata or {}).get('turn') == len(b.parent['state']['history']) + self.calls + 1,
                'BOUND_NATIVE_PROVIDER_TURN_DRIFT')
        before = self.calls
        try:
            return self.source.complete_agent(messages, metadata)
        finally:
            if self.calls > before:
                directory = self.source.out / f'{self.calls:04d}'
                for name in ['request.bin', 'response.bin', 'receipt.json']:
                    path = directory / name
                    if path.exists():
                        raw = path.read_bytes()
                        content = stable_json_bytes({'bytes_hex': raw.hex()}).decode() if name.endswith('.bin') else raw.decode()
                        b.observer.capture('native:bound_provider_exchange', content,
                            'OFFLINE_BOUND_PROVIDER_' + name.split('.')[0].upper(),
                            receipt={'exchange_member': str(path.relative_to(b.out)),
                                     'exchange_hash': digest(path.read_bytes()), 'provider_calls': 0})


class PhasedMCPBranch(SameParentMCPBranch):
    def __init__(self, context, planning, bindings, out, *, script, repo_root, sdk_root, protocol_root, verifiers):
        require(type(planning) is ReadOnlyPlanningActorSession and planning.outcome['state'] == 'COMPLETED'
                and planning.outcome['decision'] == 'REPAIR' and planning.outcome['tools_revoked'],
                'HOST_CLOSED_REPAIR_PLANNING_REQUIRED')
        authorization = planning.authorization
        require(authorization is not None and authorization.context is context, 'PHASED_PLANNING_PARENT_DRIFT')
        require(bindings == freeze_provider_bindings(context, repo_root), 'HOST_FROZEN_PROVIDER_BINDINGS_DRIFT')
        require(planning._binding['max_calls'] <= bindings['profiles']['planning']['max_logical_calls']
                and planning._binding['actor_id'] == bindings['profiles']['planning']['actor_id'],
                'PHASED_PLANNING_ACTOR_OR_BUDGET_DRIFT')
        # Reuse the unchanged restoration and official MCP attachment. Its
        # scripted source is replaced before any exchange can be dispatched.
        super().__init__(context, authorization, authorization.bundle, out, script=script,
                         sdk_root=sdk_root, protocol_root=protocol_root, verifiers=verifiers)
        self._planning = planning; self._bindings = copy.deepcopy(bindings); self._repo_root = Path(repo_root)
        self.phase = 'RESTORED_AWAITING_REPAIR'; self._repair_attempted = False
        self._continuation_attempted = False; self._closed = False; self._completed = []
        self._actions = []; self._checks = []; self._release = None
        profile = bindings['profiles']['subject']
        wire = OfflineWireResponses([{'status': 200, 'body': json.dumps({
            'id': f'offline-subject-{i+1}', 'model': profile['model_alias'],
            'choices': [{'message': {'role': 'assistant', 'content': row['content']}, 'finish_reason': 'stop'}],
            'usage': {}}).encode()} for i, row in enumerate(script.responses)])
        bound = BoundExchangeSource(profile, wire, self.out / 'provider_exchanges',
                                    gate=lambda: self.phase == 'OFFLINE_SUBJECT_CONTINUATION' and not self._closed)
        self.source = _CapturedNativeSource(self, bound); self.host.provider = self.source
        save(self.out / 'provider_bindings.json', bindings)
        save(self.out / 'planning_outcome.json', planning.outcome)
        self._record_phase()

    async def run(self):
        require(False, 'EXPLICIT_REPAIR_RELEASE_CONTINUATION_PHASES_REQUIRED')

    def _record_phase(self, failure=None):
        after = self.adapter.save_state(self.host)
        row = seal({'schema': 'stage2-phased-native-mcp-receipt-v1', 'phase': self.phase,
            'parent_checkpoint_hash': self.context.parent_checkpoint_hash,
            'planning_outcome_hash': self._planning.outcome['outcome_hash'],
            'provider_bindings_hash': self._bindings['bindings_hash'],
            'completed_steps': self._completed, 'native_repair_actions': len(self._actions),
            'native_mcp_invocations': self.host.checkout.sequence, 'scripted_subject_calls': self.source.calls,
            'remaining_before': self.parent['manifest']['remaining_horizon'],
            'remaining_after': after['max_turns'] - len(after['history']),
            'failure': failure, 'release': self._release, 'provider_calls': 0,
            'actual_repair_agent_exit': False, 'agent_generated_proposal': False,
            'semantic_repair_effect': 'NOT_EVALUATED', 'repair_success': False,
            'automatic_replay': False, 'live_trial_ready': False}, 'phase_hash')
        save(self.out / 'phase_receipt.json', row)
        return row

    def _verify_parent_host(self):
        require(self._bindings == freeze_provider_bindings(self.context, self._repo_root), 'PHASED_PROVIDER_SOURCE_DRIFT')
        require(self.adapter.save_state(self.host) == self.parent['state'], 'PHASED_REPAIR_MUTATED_PARENT_HOST')
        require(file_tree_manifest(self.root) == self.expected, 'PHASED_APPLICATION_DRIFT')
        require(digest(Path(self.context.access.archive.name).read_bytes()) == self.context.case['archive_sha256'],
                'PHASED_ARCHIVE_DRIFT')

    def _failure(self, exc):
        self.phase = 'FAILED_NO_REPLAY'; self._closed = True
        error = {'type': type(exc).__name__, 'message': str(exc)}
        self.observer.capture('native:phase_failure', stable_json_bytes(error).decode(), 'NATIVE_FAILURE')
        self.capture('NATIVE_PHASE_FAILURE_AFTER'); self.observer.finish()
        save(self.out / 'native_state_failure.json', self.adapter.save_state(self.host))
        save(self.out / 'failure_checkpoint.json', self.checkpoint('host:offline-phase-failure'))
        self._record_phase(error)

    def repair(self):
        require(not self._repair_attempted and self.phase == 'RESTORED_AWAITING_REPAIR', 'NATIVE_REPAIR_ALREADY_ATTEMPTED')
        self._repair_attempted = True
        try:
            self._verify_parent_host(); self.phase = 'OFFLINE_REPAIR_DRIVER'
            save(self.out / 'branch_intent.json', {'parent_checkpoint_hash': self.context.parent_checkpoint_hash,
                'bundle_hash': self.bundle['bundle_hash'], 'bindings_hash': self._bindings['bindings_hash'],
                'replay_authorized': False})
            for action in self.bundle['application_plan']['actions']:
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
            save(self.out / 'after_repair_checkpoint.json', self.checkpoint('host:offline-repair:post'))
            self.phase = 'REPAIRED_PAUSED_AWAITING_HOST_RELEASE'
            self.capture('NATIVE_REPAIR_PAUSED'); self.observer.finish()
            save(self.out / 'paused_state.json', self.adapter.save_state(self.host))
            return self._record_phase()
        except BaseException as exc:
            self._failure(exc); raise

    def release(self, planning):
        require(self.phase == 'REPAIRED_PAUSED_AWAITING_HOST_RELEASE', 'NATIVE_RELEASE_REQUIRES_PAUSED_REPAIR')
        try:
            require(planning is self._planning and planning.authorization is self.authorization,
                    'HOST_RELEASE_PLANNING_IDENTITY_DRIFT')
            require(planning.outcome['tools_revoked'] and planning.outcome['state'] == 'COMPLETED',
                    'HOST_RELEASE_CLOSED_PLANNING_REQUIRED')
            self._verify_parent_host()
            require(self._completed == self.bundle['proposal']['execution_order'], 'HOST_RELEASE_STEPS_INCOMPLETE')
            self._release = seal({'schema': 'stage2-offline-host-release-v1',
                'planning_outcome_hash': planning.outcome['outcome_hash'],
                'authorization_hash': self.authorization.receipt['authorization_hash'],
                'completed_steps': self._completed, 'parent_host_state_preserved': True,
                'provider_bindings_hash': self._bindings['bindings_hash'], 'tools_revoked': True,
                'actual_repair_agent_exit': False, 'origin': 'OFFLINE_HOST_RELEASE_NOT_AGENT_EXIT'}, 'release_hash')
            self.journal.append('HOST_RELEASE', self._release)
            self.observer.capture('native:offline_host_release', stable_json_bytes(self._release).decode(),
                                  'OFFLINE_REPAIR_DRIVER_EXIT')
            self.phase = 'HOST_RELEASED_AWAITING_CONTINUATION'
            self._record_phase(); return copy.deepcopy(self._release)
        except BaseException as exc:
            self._failure(exc); raise

    async def continue_native(self):
        require(self.phase == 'HOST_RELEASED_AWAITING_CONTINUATION' and not self._continuation_attempted,
                'NATIVE_CONTINUATION_REQUIRES_HOST_RELEASE')
        self._continuation_attempted = True
        try:
            self._verify_parent_host(); self.phase = 'OFFLINE_SUBJECT_CONTINUATION'
            self.capture('NATIVE_MCP_CONTINUATION_BEFORE')
            async def boundary(**payload):
                self.capture('NATIVE_MCP_TERMINAL_RETURN' if payload['boundary'] == 'TERMINAL' else 'NATIVE_MCP_TURN_RETURN')
            result = await _resume_host(self.host, boundary)
            self.observer.capture('native:closure', stable_json_bytes(result).decode(),
                'NATIVE_CLOSURE' if self.host.stop_reason in {'finalized', 'queue_exhausted'} else 'NATIVE_CENSOR')
            self.phase = 'OFFLINE_CONTINUATION_CAPTURED_PENDING_ACTUAL_EXIT_AND_REVIEW'
            self._closed = True; self.capture('NATIVE_PHASED_BRANCH_AFTER')
            self.observer.finish()
            after = self.adapter.save_state(self.host)
            require(after['history'][:len(self.parent['state']['history'])] == self.parent['state']['history']
                and after['max_turns'] == self.parent['state']['max_turns']
                and after['max_actions'] == self.parent['state']['max_actions']
                and len(after['history']) <= after['max_turns'], 'PHASED_NATIVE_HISTORY_OR_BUDGET_DRIFT')
            require(self._bindings == freeze_provider_bindings(self.context, self._repo_root), 'PHASED_PROVIDER_SOURCE_DRIFT')
            require(digest(Path(self.context.access.archive.name).read_bytes()) == self.context.case['archive_sha256'],
                    'PHASED_ARCHIVE_DRIFT')
            save(self.out / 'native_state_after.json', after)
            save(self.out / 'final_checkpoint.json', self.checkpoint('host:terminal'))
            save(self.out / 'continuation_assessment.json', assess_continuation(self.contract, self.context.graph,
                self.observer.graph.snapshot(), source_reader=lambda o: read_capture_member(self.out, o)))
            return self._record_phase()
        except BaseException as exc:
            self._failure(exc); raise


class PhasedPlanningRepairEntry:
    """Current host entry: a repair decision returns at the paused boundary.

    Previous one-call entry code is used only to reproduce frozen predecessors;
    this entry has no fallback to it. No-action outcomes create no native branch.
    """
    def __init__(self, context, planning, bindings, out, *, repo_root):
        require(type(planning) is ReadOnlyPlanningActorSession, 'HOST_PHASED_PLANNING_SESSION_REQUIRED')
        require(bindings == freeze_provider_bindings(context, repo_root), 'HOST_FROZEN_PROVIDER_BINDINGS_DRIFT')
        require(planning._session.context is context and planning._binding['actor_id'] == bindings['profiles']['planning']['actor_id']
                and planning._binding['max_calls'] <= bindings['profiles']['planning']['max_logical_calls'],
                'PHASED_ENTRY_PLANNING_BINDING_DRIFT')
        self.context = context; self._planning = planning; self._bindings = copy.deepcopy(bindings)
        self._repo_root = Path(repo_root); self.out = Path(out)
        require(not self.out.exists(), 'FRESH_PHASED_ENTRY_REQUIRED')
        self.out.mkdir(parents=True); self._started = False; self._branch = None; self._state = 'PREPARED'

    def _record_entry(self, failure=None):
        outcome = self._planning._outcome or {}
        row = seal({'schema':'stage2-phased-planning-entry-v1', 'state':self._state,
            'planning_outcome_hash':outcome.get('outcome_hash'), 'decision':outcome.get('decision'),
            'provider_bindings_hash':self._bindings['bindings_hash'],
            'native_branch_created':(self.out/'native_branch').exists(), 'failure':failure,
            'provider_calls':0, 'actual_repair_agent_exit':False, 'repair_success':False,
            'automatic_replay':False, 'live_trial_ready':False},'entry_hash')
        save(self.out/'entry_receipt.json',row); return row

    async def plan_and_repair(self, *, script=None, sdk_root=None, protocol_root=None, verifiers=None):
        require(not self._started,'PHASED_ENTRY_ALREADY_STARTED'); self._started=True
        try:
            # A completed host session may be handed to the dispatcher. A failed
            # or unfinished session is never rerun to make a proposal available.
            outcome = self._planning.outcome if self._planning._started else await self._planning.run()
            require(outcome['state']=='COMPLETED','HOST_COMPLETED_PHASED_PLANNING_REQUIRED')
            if outcome['decision']=='REPAIR':
                self._branch=PhasedMCPBranch(self.context,self._planning,self._bindings,self.out/'native_branch',
                    script=script,repo_root=self._repo_root,sdk_root=sdk_root,protocol_root=protocol_root,
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
