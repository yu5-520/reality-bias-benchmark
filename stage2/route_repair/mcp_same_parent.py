"""Same-parent exact application repair and scripted native MCP continuation.

The frozen MCP client/server/proxy and host resume loop are reused unchanged.
Only a retained host authorization permits repair writes. No model, actual
repair agent, scientific repair verdict or live provider capability is supplied.
"""
import copy
import importlib.util
import json
import subprocess
from pathlib import Path

from stage2.r7_checkpoint_v1.common import digest, stable_json_bytes, file_tree_manifest, CheckpointRegistry
from stage2.r7_checkpoint_v1.host_adapter import SoftwareHostCheckpointAdapter
from stage2.native_v7.software_host_v1 import SoftwareEngineeringHost
from stage2.native_v7.x4_mcp.runner import MCPCheckoutProxy
from stage2.r7_prospective_v1.engineering_b_runner import _resume_host
from stage2.route_repair.branch_fields import require, save, seal, FullGraphBranchObserver, transform, select_grant
from stage2.route_repair.native_continuation import OfflineScript, _ScriptedResponseSource
from stage2.route_repair.recovery_journal import RecoveryJournal
from stage2.route_repair.system_contract import build_system_contract, assess_continuation, read_capture_member

SDK_COMMIT = 'f1b6589088534632fef92238ee9750951e3c0185'
PROTOCOL_COMMIT = '5f5440bb26a62e2cf3440b92da5a667efa03b267'


def verify_mcp_environment(sdk_root, protocol_root):
    require(Path(sdk_root).is_dir() and Path(protocol_root).is_dir(), 'MCP_FROZEN_RUNTIME_CAPABILITY_MISSING')
    roots = [Path(sdk_root).resolve(strict=True), Path(protocol_root).resolve(strict=True)]
    for root, expected in zip(roots, [SDK_COMMIT, PROTOCOL_COMMIT]):
        head = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
        dirty = subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain', '--untracked-files=no'], text=True)
        require(head == expected and not dirty, 'MCP_FROZEN_SOURCE_BINDING_MISMATCH')
    spec = importlib.util.find_spec('mcp')
    require(spec is not None and spec.origin is not None
            and Path(spec.origin).resolve().is_relative_to(roots[0] / 'src'), 'MCP_RUNTIME_NOT_FROM_FROZEN_SDK')
    return seal({'schema': 'stage2-native-mcp-runtime-binding-v1',
        'sdk_commit': SDK_COMMIT, 'protocol_commit': PROTOCOL_COMMIT,
        'sdk_uv_lock_sha256': digest((roots[0] / 'uv.lock').read_bytes()),
        'runtime_source_verified': True, 'framework_source_modified': False,
        'transport': 'ORIGINAL_OFFICIAL_MCP_STDIO', 'server_lifecycle': 'ORIGINAL_ONE_INVOCATION_PER_SESSION'}, 'binding_hash')


def decode_repair_tool_result(result, expected_type):
    # The frozen SDK's structured result wraps a server's JSON string in /result.
    # Subject tool results remain exactly as returned by the original proxy.
    require(type(result) is dict and set(result) == {'result'} and type(result['result']) is str,
            'UNSUPPORTED_NATIVE_MCP_RESULT_WRAPPER')
    value = json.loads(result['result'])
    require(type(value) is expected_type, 'NATIVE_MCP_RESULT_TYPE_MISMATCH')
    return value


class ObservedMCPCheckout(MCPCheckoutProxy):
    """Passive observation around the original proxy; no extra native read calls."""
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
                    self.branch.observer.capture('protocol-call:mcp-branch:' + str(self.sequence),
                        path.read_bytes().decode(), 'MCP_WIRE_' + direction.upper(),
                        receipt={'wire_member': str(path.relative_to(self.branch.out.resolve())),
                                 'wire_sha256': digest(path.read_bytes()),
                                 'origin': self.branch.phase})
            self.branch.capture('MCP_ACTION_AFTER')
        incoming = [json.loads(line) for line in (Path(self.observer_root) /
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


class SameParentMCPBranch:
    def __init__(self, context, authorization, supplied_bundle, out, *, script, sdk_root, protocol_root, verifiers):
        require(type(script) is OfflineScript, 'LIVE_MCP_SUBJECT_CONTINUATION_DISABLED')
        require(authorization.context is context and supplied_bundle == authorization.bundle,
                'MCP_HOST_FROZEN_PROPOSAL_MISMATCH')
        require(not authorization._dispatched, 'MCP_AUTHORIZATION_ALREADY_DISPATCHED')
        bundle = authorization.bundle
        require(bundle['host_answer_policy'] is None and bundle['application_plan'] is not None,
                'NONTERMINAL_MCP_APPLICATION_BINDING_REQUIRED')
        require(bundle['proposal']['parent_checkpoint_hash'] == context.parent_checkpoint_hash,
                'MCP_SAME_PARENT_BINDING_MISMATCH')
        require(len(script.responses) <= context.parent['manifest']['remaining_horizon'], 'SCRIPT_EXCEEDS_NATIVE_BUDGET')
        for task in bundle['proposal']['verification_tasks']:
            binding = verifiers.get(task['verification_id'])
            require(binding is not None and callable(binding.get('run'))
                    and all(binding.get(k) == task[k] for k in ['operation', 'refs', 'postcondition']),
                    'MCP_HOST_VERIFICATION_CAPABILITY_MISSING')
        environment = verify_mcp_environment(sdk_root, protocol_root)
        self.context, self.parent = context, context.parent
        self.bundle, self.authorization = copy.deepcopy(bundle), authorization
        self.verifiers = verifiers
        self.out = Path(out)
        require(not self.out.exists(), 'FRESH_MCP_BRANCH_REQUIRED_NO_REPLAY')
        # Share the host-held one-use token with the older dispatch wrapper.
        # This token is never a field in an actor-supplied/re-sealed payload.
        authorization._dispatched = True
        self.out.mkdir(parents=True)
        self.root = self.out / 'application'
        self.root.mkdir()
        for path, raw in self.parent['files'].items():
            target = self.root / path; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
        self.expected = file_tree_manifest(self.root)
        require(self.expected == self.parent['manifest']['application_file_hashes'], 'MCP_PARENT_COPY_DRIFT')
        self.observer = FullGraphBranchObserver(context.graph, self.out, 'same-parent-native-mcp-engineering')
        self.source = _ScriptedResponseSource(script.responses, self)
        state = self.parent['state']
        self.host = SoftwareEngineeringHost(task_id=state['task_id'], checkout=self.root,
            provider=self.source, max_turns=1, max_actions=state['max_actions'])
        self.host.max_turns = state['max_turns']
        self.adapter = SoftwareHostCheckpointAdapter()
        self.adapter.load_state(self.host, state)
        self.host.checkout = ObservedMCPCheckout(self.root, self)
        self.contract = build_system_contract(bundle, context.graph)
        self.journal = RecoveryJournal(self.out / 'recovery_journal', {
            'bundle_hash': bundle['bundle_hash'], 'contract_hash': self.contract['contract_hash'],
            'parent_checkpoint_hash': context.parent_checkpoint_hash})
        self.registry = CheckpointRegistry(self.out / 'branch_checkpoints')
        self.phase = 'RESTORE'
        self.executed = False
        save(self.out / 'environment_binding.json', environment)
        save(self.out / 'planning_bundle.json', bundle)
        save(self.out / 'authorization.json', authorization.receipt)
        save(self.out / 'system_contract.json', self.contract)
        save(self.out / 'script.json', script.responses)
        self.capture('NATIVE_MCP_PARENT_RESTORED')

    def capture(self, phase):
        self.observer.capture('state:host_parent', stable_json_bytes(self.adapter.save_state(self.host)).decode(), phase)
        for path in file_tree_manifest(self.root):
            self.observer.capture('file:' + path, (self.root / path).read_bytes().decode(), phase)

    def checkpoint(self, event_ref):
        return self.adapter.capture(system_id='X4_MCP', host=self.host, registry=self.registry,
            application_root=self.root, group_id='OFFLINE_SAME_PARENT_MCP', run_id='G3-X4-T2-engineering',
            task_id=self.host.task['id'], event_ref=event_ref,
            model_visible_context={'queue': list(self.host.queue), 'inbox': copy.deepcopy(self.host.inbox),
                                   'scope': 'NATIVE_HOST_BRANCH_CHECKPOINT_NOT_NEW_HISTORICAL_EVIDENCE'},
            remaining_horizon=self.host.max_turns - len(self.host.history), external_carrier_refs=[],
            replication_binding={'source_parent': self.context.parent_checkpoint_hash,
                                 'sdk_commit': SDK_COMMIT, 'protocol_commit': PROTOCOL_COMMIT})

    async def run(self):
        require(not self.executed, 'MCP_BRANCH_ALREADY_ATTEMPTED_NO_REPLAY')
        require(self.bundle == self.authorization.bundle, 'MCP_HOST_FROZEN_PROPOSAL_MISMATCH')
        require(self.adapter.save_state(self.host) == self.parent['state']
                and file_tree_manifest(self.root) == self.expected, 'MCP_PRE_RUN_PARENT_DRIFT')
        self.executed = True
        save(self.out / 'branch_intent.json', {'parent_checkpoint_hash': self.context.parent_checkpoint_hash,
            'bundle_hash': self.bundle['bundle_hash'], 'script_hash': digest(self.source.responses), 'replay_authorized': False})
        actions, verifications, completed = [], [], []
        status, error = 'OFFLINE_SAME_PARENT_MCP_CAPTURED_PENDING_AGENT_AND_REVIEW', None
        try:
            self.phase = 'OFFLINE_REPAIR_DRIVER'
            for action in self.bundle['application_plan']['actions']:
                require(file_tree_manifest(self.root) == self.expected, 'MCP_APPLICATION_VERSION_DRIFT')
                require(set(action.get('depends_on', [])) <= set(completed), 'MCP_REPAIR_DEPENDENCY_NOT_COMPLETE')
                path = action['target_ref'][5:]
                before = decode_repair_tool_result(self.host.checkout.read_file(path), str)
                require(digest(before.encode()) == action['before_file_hash'], 'MCP_NATIVE_READ_VERSION_DRIFT')
                output, invariant = transform(before, action, select_grant(self.bundle['application_plan']['policy'], action))
                require(digest(output.encode()) == action['expected_output_hash'], 'MCP_EXPECTED_OUTPUT_DRIFT')
                self.journal.intent(action['action_id'], action['target_ref'], action['before_file_hash'], action['expected_output_hash'])
                native = self.host.checkout.write_file(path, output)
                actual = decode_repair_tool_result(self.host.checkout.read_file(path), str)
                receipt = {'action_id': action['action_id'], 'target_ref': action['target_ref'],
                    'native_interface': 'native:MCPCheckoutProxy.write_file', 'native_result': native,
                    'before_hash': digest(before.encode()), 'after_hash': digest(actual.encode()),
                    'expected_output_hash': action['expected_output_hash'], **invariant}
                actions.append(receipt); save(self.out / 'native_repair_receipts.json', actions)
                self.journal.complete(action['action_id'], receipt['after_hash'], receipt)
                require(actual == output, 'MCP_NATIVE_WRITE_POSTCONDITION_FAILED')
                self.expected[path] = digest(actual.encode())
                require(file_tree_manifest(self.root) == self.expected, 'MCP_NATIVE_WRITE_SCOPE_DRIFT')
                require(self.adapter.save_state(self.host) == self.parent['state'], 'MCP_REPAIR_MUTATED_HOST_STATE')
                completed.append(action['action_id'])
            for task in self.bundle['proposal']['verification_tasks']:
                require(set(task['depends_on']) <= set(completed), 'MCP_VERIFICATION_DEPENDENCY_NOT_COMPLETE')
                before = file_tree_manifest(self.root)
                value = self.verifiers[task['verification_id']]['run'](self.root)
                require(file_tree_manifest(self.root) == before, 'MCP_VERIFIER_MUTATED_APPLICATION')
                row = {'verification_id': task['verification_id'], 'result': value,
                       'classification': 'HOST_DEFINED_ENGINEERING_CHECK_NOT_SEMANTIC_REVIEW'}
                verifications.append(row); save(self.out / 'verification_receipts.json', verifications)
                require(value.get('passed') is True, 'MCP_HOST_VERIFICATION_FAILED')
                completed.append(task['verification_id'])
            after_repair = self.checkpoint('host:offline-repair:post')
            save(self.out / 'after_repair_checkpoint.json', after_repair)
            self.observer.capture('native:offline_repair_driver', 'Scripted repair driver released the native host.',
                                  'OFFLINE_REPAIR_DRIVER_EXIT')
            self.phase = 'SCRIPTED_SUBJECT_CONTINUATION'
            self.capture('NATIVE_MCP_CONTINUATION_BEFORE')
            async def boundary(**payload):
                self.capture('NATIVE_MCP_TERMINAL_RETURN' if payload['boundary'] == 'TERMINAL' else 'NATIVE_MCP_TURN_RETURN')
            result = await _resume_host(self.host, boundary)
            kind = 'NATIVE_CLOSURE' if self.host.stop_reason in {'finalized', 'queue_exhausted'} else 'NATIVE_CENSOR'
            self.observer.capture('native:closure', stable_json_bytes(result).decode(), kind)
        except BaseException as exc:
            status = 'BLOCKED_OR_INTERRUPTED_WITH_PARTIAL_NATIVE_EVIDENCE'
            error = {'type': type(exc).__name__, 'message': str(exc)}
            self.observer.capture('native:closure', stable_json_bytes(error).decode(), 'NATIVE_FAILURE')
            raise
        finally:
            self.capture('NATIVE_MCP_BRANCH_AFTER')
            comparison = self.observer.finish()
            comparison.update(captures_cover='PREFIX_AND_NATIVE_MCP_REPAIR_AND_SCRIPTED_HOST_CONTINUATION',
                              native_agent_continuation_observed=False, scripted_native_host_continuation_observed=True)
            save(self.out / 'graph_comparison.json', comparison)
            after = self.adapter.save_state(self.host)
            require(after['history'][:len(self.parent['state']['history'])] == self.parent['state']['history'],
                    'MCP_HOST_HISTORY_PREFIX_DRIFT')
            require(after['max_turns'] == self.parent['state']['max_turns']
                    and after['max_actions'] == self.parent['state']['max_actions']
                    and len(after['history']) <= after['max_turns'], 'MCP_HOST_BUDGET_DRIFT')
            require(digest(Path(self.context.access.archive.name).read_bytes()) == self.context.case['archive_sha256'],
                    'MCP_FROZEN_ARCHIVE_DRIFT')
            save(self.out / 'native_state_after.json', after)
            assessment = assess_continuation(self.contract, self.context.graph, self.observer.graph.snapshot(),
                source_reader=lambda observation: read_capture_member(self.out, observation))
            save(self.out / 'continuation_assessment.json', assessment)
            save(self.out / 'final_checkpoint.json', self.checkpoint('host:terminal' if error is None else 'host:offline-branch-failure'))
            receipt = seal({'schema': 'stage2-same-parent-native-mcp-branch-v1', 'status': status,
                'parent_checkpoint_hash': self.context.parent_checkpoint_hash, 'completed_steps': completed,
                'native_repair_actions': len(actions), 'native_mcp_invocations': self.host.checkout.sequence,
                'remaining_before': self.parent['manifest']['remaining_horizon'],
                'remaining_after': after['max_turns'] - len(after['history']),
                'scripted_response_calls': self.source.calls, 'provider_calls': 0,
                'history_prefix_preserved': True, 'archive_preserved': True,
                'error': error, 'stop_reason': after['stop_reason'],
                'full_native_mcp_protocol_attached': self.host.checkout.protocol_initialized, 'framework_source_modified': False,
                'future_suffix_supplied': False, 'actual_repair_agent_exit_observed': False,
                'agent_proposal_generated': False, 'semantic_repair_effect': 'NOT_EVALUATED',
                'repair_success': False, 'branch_promoted': False, 'live_execution_ready': False,
                'continuation_assessment_status': assessment['status'],
                'new_observations': comparison['new_observations']}, 'receipt_hash')
            save(self.out / 'same_parent_receipt.json', receipt)
        return receipt
