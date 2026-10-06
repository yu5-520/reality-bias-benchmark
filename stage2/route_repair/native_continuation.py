"""Verified nonterminal host restore and passive offline continuation capture.

This binding uses the existing experiment-owned resume loop with a bounded
scripted response source. It does not run a subject model, instantiate a foreign
MCP/RAG service, expose a live provider entrypoint or fabricate a repair exit.
The historical full-trajectory graph is never used as a prospective parent graph.
"""
import copy
import json
from pathlib import Path

from stage2.r7_checkpoint_v1.common import (
    digest, stable_json_bytes, file_tree_manifest, verify_foreign_carrier_refs, CheckpointRegistry,
)
from stage2.r7_checkpoint_v1.host_adapter import SoftwareHostCheckpointAdapter, ADAPTER_ID
from stage2.native_v7.software_host_v1 import SoftwareEngineeringHost, TASKS, DIRECTORY, SUBJECT_LIMITS
from stage2.r7_prospective_v1.engineering_b_runner import _resume_host
from stage2.monitor_enhancement.evidence_graph import EvidenceGraph
from stage2.route_repair.branch_fields import (
    require, exact_path, save, seal, FullGraphBranchObserver,
)

MANIFEST_FIELDS = [
    'schema', 'system_id', 'group_id', 'run_id', 'task_id', 'event_ref', 'adapter_id',
    'framework_binding', 'native_state_sha256', 'application_state_sha256',
    'model_visible_context_sha256', 'remaining_horizon', 'external_carrier_refs',
    'restore_capability', 'replication_binding',
]


def load_host_parent(context, checkpoint_hash):
    """Verify a ledger-backed full capture without repairing absent history."""
    rows = [r for r in context.ledger['checkpoints'] if r['checkpoint_hash'] == checkpoint_hash]
    require(rows, 'PARENT_NOT_IN_NATIVE_LEDGER')
    prefix = 'checkpoints/' + checkpoint_hash + '/'
    manifest = json.loads(context.raw(prefix + 'manifest.json'))
    require(manifest['checkpoint_hash'] == checkpoint_hash
            and digest({k: manifest[k] for k in MANIFEST_FIELDS}) == checkpoint_hash,
            'PARENT_MANIFEST_CONTENT_ADDRESS_MISMATCH')
    captures = [r for r in rows if r['event_ref'] == manifest['event_ref']]
    require(captures, 'PARENT_ONLY_HAS_MONITOR_ANNOTATION')
    require(manifest['adapter_id'] == ADAPTER_ID and manifest['restore_capability'] == 'FULL_NATIVE',
            'FULL_NATIVE_HOST_PARENT_REQUIRED')
    require(manifest['schema'] == CheckpointRegistry.SCHEMA
            and manifest['framework_binding'] == SoftwareHostCheckpointAdapter.framework_binding
            and manifest['checkpoint_id'] == f"rbcp:{manifest['system_id']}:{checkpoint_hash[:24]}",
            'NATIVE_HOST_FRAMEWORK_BINDING_MISMATCH')
    require(manifest['system_id'] in {'X4_MCP', 'X5_RAG', 'X6_MEMORYBANK', 'X7_LONGLMLINGUA'},
            'UNSUPPORTED_NATIVE_HOST_SYSTEM')
    state = json.loads(context.raw(prefix + 'native_state.json'))
    model_context = json.loads(context.raw(prefix + 'model_context.json'))
    require(digest(state) == manifest['native_state_sha256'], 'PARENT_NATIVE_STATE_HASH_MISMATCH')
    require(digest(model_context) == manifest['model_visible_context_sha256'], 'PARENT_MODEL_CONTEXT_HASH_MISMATCH')
    require(state['schema'] == 'stage2-r7-software-host-state-v1'
            and state['task_id'] == manifest['task_id'] and state['task_id'] in TASKS,
            'PARENT_TASK_SCHEMA_MISMATCH')
    require(type(state['max_turns']) is int and 1 <= state['max_turns'] <= SUBJECT_LIMITS['max_total_model_invocations']
            and type(state['max_actions']) is int and 1 <= state['max_actions'] <= 8,
            'PARENT_RUNTIME_BUDGET_INVALID')
    remaining = state['max_turns'] - len(state['history'])
    require(type(manifest['remaining_horizon']) is int and manifest['remaining_horizon'] == remaining
            and remaining >= 0, 'PARENT_REMAINING_BUDGET_MISMATCH')
    require(all(h['turn'] == i for i, h in enumerate(state['history'], 1))
            and all(r['model_decision_sequence'] == len(state['history']) for r in captures),
            'PARENT_NATIVE_SEQUENCE_MISMATCH')
    require(set(state['inbox']) == set(DIRECTORY) and all(r in DIRECTORY for r in state['queue']),
            'PARENT_QUEUE_MAILBOX_SCHEMA_MISMATCH')
    files = {}
    for path, expected in manifest['application_file_hashes'].items():
        exact_path('file:' + path)
        raw = context.raw(prefix + 'application/' + path)
        require(digest(raw) == expected, 'PARENT_APPLICATION_FILE_HASH_MISMATCH')
        raw.decode('utf-8')  # Current passive graph capture uses UTF-8 native files.
        files[path] = raw
    require(digest(manifest['application_file_hashes']) == manifest['application_state_sha256'],
            'PARENT_APPLICATION_MANIFEST_HASH_MISMATCH')
    return {'manifest': copy.deepcopy(manifest), 'state': state, 'model_context': model_context,
            'files': files, 'capture_rows': copy.deepcopy(captures),
            'monitor_annotations': [copy.deepcopy(r) for r in rows if r not in captures]}


def continuation_blocker(parent):
    state, manifest = parent['state'], parent['manifest']
    if state['stop_reason'] is not None:
        return 'STOPPED_NATIVE_PARENT_NO_REOPEN'
    if any(r['boundary'] == 'TERMINAL' for r in parent['capture_rows']):
        return 'TERMINAL_NATIVE_PARENT_NO_REOPEN'
    if manifest['remaining_horizon'] <= 0:
        return 'NATIVE_BUDGET_EXHAUSTED'
    return None


class OfflineScript:
    """Fixed responses, not a callback or a live model/provider binding."""
    def __init__(self, responses):
        require(isinstance(responses, list) and responses
                and all(type(r) is dict and set(r) == {'content'} and isinstance(r['content'], str)
                        for r in responses), 'FIXED_OFFLINE_SCRIPT_REQUIRED')
        self.responses = copy.deepcopy(responses)


class _ScriptedResponseSource:
    def __init__(self, responses, branch):
        self.responses, self.branch, self.calls = copy.deepcopy(responses), branch, 0

    def complete_agent(self, messages, metadata=None):
        require(self.calls < len(self.responses), 'OFFLINE_SCRIPT_EXHAUSTED')
        require(self.calls < self.branch.parent['manifest']['remaining_horizon'], 'NATIVE_BUDGET_EXHAUSTED')
        self.calls += 1
        response = copy.deepcopy(self.responses[self.calls - 1])
        # Actual model-visible prompt and returned script envelope are retained;
        # the observer supplies no scheduling, permission or semantic verdict.
        self.branch.observer.capture('native:subject_exchange',
            stable_json_bytes({'messages': messages, 'metadata': metadata, 'response': response,
                               'origin': 'OFFLINE_SCRIPT_NOT_MODEL'}).decode(), 'SCRIPTED_NATIVE_EXCHANGE')
        return response


class _ObservedCheckout:
    def __init__(self, checkout, branch):
        self.checkout, self.branch, self.root = checkout, branch, checkout.root

    def _call(self, operation, *args):
        self.branch.capture('NATIVE_ACTION_BEFORE')
        try:
            result = getattr(self.checkout, operation)(*args)
        except Exception as exc:
            self.branch.observer.capture('native:action', stable_json_bytes({
                'operation': operation, 'arguments': args, 'error': {'type': type(exc).__name__, 'message': str(exc)},
            }).decode(), 'NATIVE_ACTION_FAILURE')
            self.branch.capture('NATIVE_ACTION_AFTER_FAILURE')
            raise
        self.branch.observer.capture('native:action', stable_json_bytes({
            'operation': operation, 'arguments': args, 'result': result,
        }).decode(), 'NATIVE_ACTION_RESULT')
        if operation == 'write_file':
            content = self.checkout.read_file(args[0])
            self.branch.observer.capture('file:' + args[0], content, 'SCRIPTED_SUBJECT_NATIVE_WRITE',
                receipt={'native_interface': 'native:HostCheckout.write_file',
                         'origin': 'OFFLINE_SCRIPT_NOT_REPAIR_AGENT', 'after_hash': digest(content.encode())},
                written=True)
        self.branch.capture('NATIVE_ACTION_AFTER')
        return result

    def list_files(self): return self._call('list_files')
    def read_file(self, path): return self._call('read_file', path)
    def write_file(self, path, content): return self._call('write_file', path, content)
    def run_tests(self): return self._call('run_tests')


class OfflineNativeContinuation:
    def __init__(self, context, checkpoint_hash, out, *, script, observed_foreign_refs):
        require(type(script) is OfflineScript, 'LIVE_CONTINUATION_BINDING_DISABLED')
        self.context = context
        self.parent = load_host_parent(context, checkpoint_hash)
        blocker = continuation_blocker(self.parent)
        require(blocker is None, blocker or 'PARENT_BLOCKED')
        require(verify_foreign_carrier_refs(self.parent['manifest']['external_carrier_refs'], observed_foreign_refs),
                'CHECKPOINT_ENVIRONMENT_MISMATCH')
        require(len(script.responses) <= self.parent['manifest']['remaining_horizon'], 'SCRIPT_EXCEEDS_NATIVE_BUDGET')
        self.out = Path(out)
        require(not self.out.exists(), 'FRESH_CONTINUATION_BRANCH_REQUIRED_NO_REPLAY')
        self.out.mkdir(parents=True)
        self.root = self.out / 'application'
        self.root.mkdir()
        for path, raw in self.parent['files'].items():
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        require(file_tree_manifest(self.root) == self.parent['manifest']['application_file_hashes'],
                'RESTORED_APPLICATION_DRIFT')
        # Separate observation graph: no terminal/future evidence is introduced
        # into this early-parent continuation engineering check.
        self.observer = FullGraphBranchObserver(EvidenceGraph().snapshot(), self.out,
                                               'offline-native-parent-' + checkpoint_hash[:16])
        self.source = _ScriptedResponseSource(script.responses, self)
        state = self.parent['state']
        self.host = SoftwareEngineeringHost(task_id=state['task_id'], checkout=self.root,
            provider=self.source, max_turns=1, max_actions=state['max_actions'])
        self.host.max_turns = state['max_turns']  # Exact saved budget, never increased.
        self.adapter = SoftwareHostCheckpointAdapter()
        self.adapter.load_state(self.host, state)
        require(self.adapter.save_state(self.host) == state, 'NATIVE_RESTORE_ROUND_TRIP_FAILED')
        self.host.checkout = _ObservedCheckout(self.host.checkout, self)
        self.executed = False
        save(self.out / 'parent_manifest.json', self.parent['manifest'])
        save(self.out / 'parent_native_state.json', state)
        save(self.out / 'parent_model_context.json', self.parent['model_context'])
        save(self.out / 'script.json', script.responses)
        save(self.out / 'restore_receipt.json', seal({
            'schema': 'stage2-native-parent-restore-v1', 'checkpoint_hash': checkpoint_hash,
            'native_state_hash': digest(state), 'application_state_hash': digest(file_tree_manifest(self.root)),
            'remaining_horizon': self.parent['manifest']['remaining_horizon'],
            'round_trip_verified': True, 'queue_inbox_history_stop_budget_preserved': True,
            'monitor_annotations': self.parent['monitor_annotations'],
            'original_task': copy.deepcopy(self.host.task), 'future_trajectory_used': False,
            'foreign_reference_hashes_match': True, 'full_foreign_runtime_attached': False,
            'classification': 'OFFLINE_HOST_RESTORE_NOT_FULL_FRAMEWORK_CONTINUATION'}, 'receipt_hash'))
        self.capture('NATIVE_PARENT_RESTORED')
        self.restored_capture_hash = digest(self.adapter.save_state(self.host))
        self.restored_file_manifest = file_tree_manifest(self.root)

    def capture(self, phase):
        state = self.adapter.save_state(self.host)
        self.observer.capture('native:host_state', stable_json_bytes(state).decode(), phase)
        for path in file_tree_manifest(self.root):
            self.observer.capture('file:' + path, (self.root / path).read_bytes().decode('utf-8'), phase)

    async def run(self):
        require(not self.executed, 'NATIVE_CONTINUATION_ALREADY_ATTEMPTED_NO_REPLAY')
        require(digest(self.adapter.save_state(self.host)) == self.restored_capture_hash
                and file_tree_manifest(self.root) == self.restored_file_manifest, 'RESTORED_BRANCH_PRE_RUN_DRIFT')
        self.executed = True
        # Persist before any response is consumed. Existing output always blocks
        # a reconstructed driver; interrupted attempts need read-only review.
        save(self.out / 'continuation_intent.json', {'checkpoint_hash': self.parent['manifest']['checkpoint_hash'],
            'before_hash': self.restored_capture_hash, 'script_hash': digest(self.source.responses),
            'replay_authorized': False})
        self.observer.capture('native:driver', 'Offline scripted driver released the restored host.',
                              'OFFLINE_DRIVER_RELEASE')
        self.capture('NATIVE_CONTINUATION_BEFORE')
        async def boundary(**payload):
            self.capture('NATIVE_TERMINAL_RETURN' if payload['boundary'] == 'TERMINAL' else 'NATIVE_TURN_RETURN')
        status, error, result = 'OFFLINE_NATIVE_HOST_CONTINUATION_CAPTURED', None, None
        try:
            result = await _resume_host(self.host, boundary)
            kind = 'NATIVE_CLOSURE' if self.host.stop_reason in {'finalized', 'queue_exhausted'} else 'NATIVE_CENSOR'
            self.observer.capture('native:closure', stable_json_bytes(result).decode(), kind)
        except BaseException as exc:
            status = 'INTERRUPTED_OR_FAILED_REQUIRES_READ_ONLY_REVIEW'
            error = {'type': type(exc).__name__, 'message': str(exc)}
            self.observer.capture('native:closure', stable_json_bytes(error).decode(), 'NATIVE_FAILURE')
            raise
        finally:
            self.capture('NATIVE_CONTINUATION_AFTER')
            self.observer.finish()
            after = self.adapter.save_state(self.host)
            before = self.parent['state']
            require(after['history'][:len(before['history'])] == before['history'], 'NATIVE_HISTORY_PREFIX_DRIFT')
            require(after['max_turns'] == before['max_turns'] and after['max_actions'] == before['max_actions']
                    and len(after['history']) <= before['max_turns'], 'NATIVE_BUDGET_DRIFT')
            require(digest(Path(self.context.access.archive.name).read_bytes()) == self.context.case['archive_sha256'],
                    'HISTORICAL_ARCHIVE_DRIFT')
            save(self.out / 'native_state_after.json', after)
            receipt = seal({'schema': 'stage2-offline-native-continuation-v1', 'status': status,
                'parent_checkpoint_hash': self.parent['manifest']['checkpoint_hash'],
                'remaining_before': self.parent['manifest']['remaining_horizon'],
                'remaining_after': after['max_turns'] - len(after['history']),
                'scripted_response_calls': self.source.calls, 'provider_calls': 0,
                'continued_turns': len(after['history']) - len(before['history']),
                'history_prefix_preserved': True, 'historical_archive_preserved': True,
                'error': error, 'stop_reason': after['stop_reason'],
                'new_observations': len(self.observer.graph.snapshot()['observations']),
                'capture_scope': 'LOCAL_NATIVE_HOST_AND_APPLICATION_ACTIONS_PLUS_EXCHANGES',
                'native_resume_implementation': 'stage2.r7_prospective_v1.engineering_b_runner._resume_host',
                'actual_repair_agent_exit_observed': False, 'repair_actions_executed': 0,
                'full_foreign_runtime_attached': False, 'semantic_repair_effect': 'NOT_EVALUATED',
                'repair_success': False, 'branch_promoted': False, 'live_execution_ready': False,
                'independent_review_status': 'PENDING_ACTUAL_REPAIR_EXIT_AND_SUBJECT_CONTINUATION'}, 'receipt_hash')
            save(self.out / 'continuation_receipt.json', receipt)
        return receipt
