"""Automatic offline coordination from an inspected plan to monitored receipts.

Plans remain explicitly manual/scripted until an agent planner and native
continuation are implemented. The host supplies verification implementations and
write policies separately. No provider, legacy repair fallback or live entrypoint.
"""
import copy
import json
from pathlib import Path

from stage2.r7_checkpoint_v1.common import stable_json_bytes, file_tree_manifest
from stage2.route_repair.branch_fields import NativeFieldBranchExecutor, require, save, verify_seal, seal
from stage2.route_repair.native_host_branch import NativeHostAnswerBinding
from stage2.route_repair.planning_session import RoutePlanningSession
from stage2.route_repair.recovery_journal import RecoveryJournal
from stage2.route_repair.system_contract import build_system_contract, assess_continuation, read_capture_member


def revalidate_bundle(context, bundle, application_policy, host_policy):
    """Re-read exact sources and recompile; re-hashing a proposal grants nothing."""
    verify_seal(bundle, 'bundle_hash')
    session = RoutePlanningSession(context, bundle['proposal']['original_task'], proposal_origin=bundle['origin'])
    for row in bundle['query_log']:
        request, operation = row['request'], row['operation']
        if operation == 'complete_catalog':
            session.catalog()
        elif operation == 'node_context':
            session.node(request['ref'])
        elif operation == 'read_file':
            session.file(request['ref'], request['checkpoint_hash'])
        elif operation == 'current_host_answer':
            session.current_answer()
        elif operation == 'current_pending_message':
            session.message(request['field_path'])
        elif operation == 'observation_source':
            session.observation(request['observation_id'], request['ref'])
        elif operation == 'select_source_witness':
            session.witness(request['read_id'], request['start'], request['end'])
        else:
            require(False, 'SYSTEM_UNSUPPORTED_SOURCE_OPERATION')
        require(session.query_log[-1] == row, 'SYSTEM_SOURCE_REPLAY_DRIFT')
    canonical = session.compile(bundle['proposal'], trusted_application_policy=application_policy,
                                trusted_host_policy=host_policy)
    require(canonical == bundle, 'SYSTEM_BUNDLE_RECOMPILE_DRIFT')


class OfflineRouteRepairSystem:
    """One offline copied branch; reuse the contract, bind each native capability.

    Host-defined verifiers are injected callables, never shell operations or
    completion claims from a proposed plan. Unsupported bindings block before
    creating the branch. Interrupted runs require read-only reconciliation.
    """
    def __init__(self, context, bundle, out, *, application_policy, host_policy=None, verifiers=None):
        self.context, self.bundle = context, copy.deepcopy(bundle)
        self.application_policy = copy.deepcopy(application_policy)
        self.host_policy = copy.deepcopy(host_policy)
        self.verifiers = dict(verifiers or {})
        self.out = Path(out)
        require(not self.out.exists(), 'SYSTEM_FRESH_BRANCH_REQUIRED')
        revalidate_bundle(context, bundle, application_policy, host_policy)
        self.contract = build_system_contract(bundle, context.graph)
        require(bundle['application_plan'] is not None, 'SYSTEM_NATIVE_APPLICATION_BINDING_REQUIRED')
        for task in bundle['proposal']['verification_tasks']:
            binding = self.verifiers.get(task['verification_id'])
            require(binding is not None, 'SYSTEM_VERIFICATION_CAPABILITY_MISSING')
            require(binding['operation'] == task['operation'] == 'HOST_DEFINED_OFFLINE_CHECK', 'SYSTEM_VERIFICATION_OPERATION_DRIFT')
            require(set(binding['refs']) == set(task['refs']) and binding['postcondition'] == task['postcondition'],
                    'SYSTEM_VERIFICATION_SCOPE_DRIFT')
            require(callable(binding['run']), 'SYSTEM_HOST_VERIFIER_REQUIRED')
        # Executor construction copies frozen state but performs no plan action.
        self.executor = NativeFieldBranchExecutor(context, bundle['application_plan'], self.out,
                                                  trusted_policy=application_policy)
        self.host = None
        if bundle['proposal'].get('host_answer'):
            self.host = NativeHostAnswerBinding(context, self.executor.root, bundle['host_answer_policy'],
                                                trusted_policy=host_policy)
        binding = {'bundle_hash': bundle['bundle_hash'], 'contract_hash': self.contract['contract_hash'],
                   'parent_checkpoint_hash': self.contract['parent_checkpoint_hash']}
        self.journal = RecoveryJournal(self.out / 'recovery_journal', binding)
        self.executed = False
        save(self.out / 'system_contract.json', self.contract)
        save(self.out / 'planning_bundle.json', bundle)
        self.journal.append('COMPLETE_PLAN_AND_NATIVE_BINDINGS_VALIDATED', {'origin': bundle['origin']})

    def execute(self):
        require(not self.executed, 'SYSTEM_ALREADY_EXECUTED')
        self.executed = True
        executor, completed = self.executor, []
        error, app_result, host_receipt = None, None, None
        verification_results = []

        def intent(action, _root):
            self.journal.intent(action['action_id'], action['target_ref'],
                                action['before_file_hash'], action['expected_output_hash'])

        try:
            self.journal.append('NATIVE_APPLICATION_EXECUTION_STARTED', {})
            app_result = executor.execute(before_action=intent)
            receipts_path = self.out / 'native_action_receipts.json'
            if receipts_path.exists():
                for receipt in json.loads(receipts_path.read_text()):
                    self.journal.complete(receipt['action_id'], receipt['after_hash'], receipt)
            require(app_result['status'] == 'PASS_OFFLINE_NATIVE_EXECUTION', 'SYSTEM_APPLICATION_EXECUTION_BLOCKED')
            require(app_result['unrelated_application_preserved'], 'SYSTEM_APPLICATION_PRESERVATION_FAILED')
            completed.extend(app_result['applied_action_ids'])
            for task in self.bundle['proposal']['verification_tasks']:
                require(set(task['depends_on']) <= set(completed), 'SYSTEM_VERIFICATION_DEPENDENCY_BLOCKED')
                result = self.verifiers[task['verification_id']]['run'](executor.root)
                require(isinstance(result, dict) and type(result.get('passed')) is bool, 'SYSTEM_VERIFIER_RECEIPT_REQUIRED')
                row = {'verification_id': task['verification_id'], 'result': result,
                       'origin': 'SEPARATELY_BOUND_HOST_VERIFIER_NOT_AGENT_COMPLETION_CLAIM'}
                verification_results.append(row)
                save(self.out / 'system_verification_receipts.json', verification_results)
                for ref in task['refs']:
                    executor.observer.capture(ref, stable_json_bytes(row).decode(), 'HOST_VERIFICATION_RESULT', receipt=row)
                self.journal.append('HOST_VERIFICATION_RESULT', row)
                require(result['passed'], 'SYSTEM_VERIFICATION_POSTCONDITION_FAILED')
                require(file_tree_manifest(executor.root) == app_result['application_manifest'],
                        'SYSTEM_VERIFICATION_MUTATED_APPLICATION')
                completed.append(task['verification_id'])
            if self.host is not None:
                policy = self.host.policy
                self.journal.intent('host_answer', 'state:terminal', policy['before_state_hash'], policy['after_state_hash'])
                host_receipt = self.host.apply(completed_actions=completed, observer=executor.observer)
                self.journal.complete('host_answer', host_receipt['after_hash'], host_receipt)
                require(host_receipt['error'] is None and host_receipt['unrelated_host_fields_preserved']
                        and host_receipt['application_files_preserved'], 'SYSTEM_HOST_POSTCONDITION_FAILED')
                completed.append('host_answer')
            self.journal.append('NATIVE_POSTCONDITIONS_COMPLETE_AWAITING_CONTINUATION', {'completed_steps': completed})
        except Exception as exc:
            error = {'type': type(exc).__name__, 'message': str(exc)}
            self.journal.append('BLOCKED_RETAIN_PARTIAL_EVIDENCE', error)
        # Always freeze the full observed graph after any partial native actions.
        for path in file_tree_manifest(executor.root):
            executor.observer.capture('file:' + path, executor.checkout.read_file(path), 'SYSTEM_BRANCH_AFTER')
        comparison = executor.observer.finish()
        comparison['captures_cover'] = 'APPLICATION_VERIFICATION_AND_CURRENT_HOST_BRANCH_BEFORE_DURING_AFTER'
        save(self.out / 'graph_comparison.json', comparison)
        after = executor.observer.graph.snapshot()
        assessment = assess_continuation(self.contract, self.context.graph, after,
                                          source_reader=lambda row: read_capture_member(self.out, row))
        save(self.out / 'continuation_assessment.json', assessment)
        result = seal({
            'schema': 'stage2-monitor-repair-system-receipt-v1',
            'classification': 'AUTOMATIC_OFFLINE_COORDINATION_OF_MANUAL_OR_SCRIPTED_PLAN',
            'status': 'BLOCKED_WITH_PARTIAL_EVIDENCE' if error else 'AWAITING_NATIVE_CONTINUATION',
            'error': error, 'contract_hash': self.contract['contract_hash'],
            'bundle_hash': self.bundle['bundle_hash'], 'completed_steps': completed,
            'native_application_writes': app_result['native_write_attempts'] if app_result else 0,
            'native_host_answer_supersessions': int(host_receipt is not None),
            'graph_comparison': comparison, 'continuation_assessment_hash': assessment['assessment_hash'],
            'safe_execution': 'PASS_OFFLINE_BOUNDARIES' if error is None else 'BLOCKED_REVIEW_RECEIPTS',
            'effective_repair': 'NOT_EVALUATED', 'automation': 'PLAN_REVALIDATION_EXECUTION_VERIFICATION_CAPTURE_AND_PENDING_GATE',
            'reuse': 'CONTRACT_AND_HOST_CAPABILITY_BINDINGS_NOT_UNIFIED_FRAMEWORK_PROTOCOL',
            'repair_agent_generated': False, 'live_provider_calls': 0,
            'native_agent_continuation_executed': False, 'repair_success': False,
            'branch_promoted': False, 'rollback_performed': False, 'automatic_retry': False,
        }, 'system_receipt_hash')
        save(self.out / 'system_receipt.json', result)
        return result
