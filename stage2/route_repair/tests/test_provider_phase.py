import asyncio
import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from stage2.r7_checkpoint_v1.common import digest
from stage2.route_repair.branch_fields import BranchConstraintError
from stage2.route_repair.native_continuation import OfflineScript
from stage2.route_repair.planning_actor import OfflinePlanningScript, ReadOnlyPlanningActorSession
from stage2.route_repair.proposal_authority import freeze_task_envelope
from stage2.route_repair.provider_capture import freeze_provider_bindings, BoundExchangeSource, OfflineWireResponses, PlanningRequestAdapter
from stage2.route_repair.phased_mcp import PhasedMCPBranch, PhasedPlanningRepairEntry
from stage2.route_repair.tests import test_prefix_mcp as prefix_fixture
from stage2.route_repair.tests import test_planning_actor as planning_fixture

ROOT = Path(__file__).resolve().parents[3]


def wire_body(content='{"actions": []}', model='deepseek-flash', finish='stop'):
    return json.dumps({'id': 'offline-response', 'model': model, 'choices': [
        {'message': {'role': 'assistant', 'content': content}, 'finish_reason': finish}],
        'usage': {'prompt_tokens': 7, 'completion_tokens': 3, 'total_tokens': 10}}).encode()


class ProviderPhaseTests(unittest.TestCase):
    def setUp(self):
        self.fixture = prefix_fixture.PrefixMCPTests(); self.fixture.setUp()
        self.root = self.fixture.root; self.c = self.fixture.context()
        self.bindings = freeze_provider_bindings(self.c, ROOT)
        self.profile = self.bindings['profiles']['subject']
        self.envelope = freeze_task_envelope(self.c, self.fixture.host.task,
            writable_refs=['file:a.json','file:b.py'], branch_id='phase-test', max_actions=2, max_value_bytes=1024)

    def tearDown(self): self.fixture.tearDown()

    def source(self, rows, gate=lambda: True, name='provider'):
        return BoundExchangeSource(self.profile, OfflineWireResponses(rows), self.root / name, gate=gate)

    def planning(self):
        old = self.fixture.authorization(self.c).bundle
        rows = planning_fixture.tools_from_queries(old['query_log']) + [planning_fixture.response(
            {'kind': 'FINAL', 'decision': 'REPAIR', 'proposal': old['proposal']})]
        session = ReadOnlyPlanningActorSession(self.c, self.envelope, OfflinePlanningScript(rows),
            self.root / 'planning', actor_id=self.bindings['profiles']['planning']['actor_id'],max_calls=16)
        asyncio.run(session.run()); return session

    def branch(self, planning, verifiers=None):
        scripts = [{'content': json.dumps({'actions': [{'type':'finalize','answer':'offline'}]})} for _ in range(3)]
        with patch('stage2.route_repair.mcp_same_parent.verify_mcp_environment', return_value={'origin':'SYNTHETIC_UNIT_NO_PROTOCOL'}):
            return PhasedMCPBranch(self.c, planning, self.bindings, self.root / 'branch',
                script=OfflineScript(scripts), repo_root=ROOT, sdk_root='fixture', protocol_root='fixture', verifiers=verifiers or {})

    def mcp(self):
        def read(proxy, path): return {'result': json.dumps((proxy.root / path).read_text())}
        def write(proxy, path, content):
            (proxy.root / path).write_text(content); return {'result': '{}'}
        return patch.multiple('stage2.route_repair.mcp_same_parent.ObservedMCPCheckout', read_file=read, write_file=write)

    def test_exact_request_matches_existing_repository_adapter_and_raw_reply_is_unchanged(self):
        raw = wire_body(); source = self.source([{'status':200,'body':raw}])
        messages = [{'role':'user','content':'中文 source'}]
        result = source.complete_agent(messages, {'role':'qa','turn':2})
        self.assertEqual((source.out / '0001/response.bin').read_bytes(), raw)
        request = (source.out / '0001/request.bin').read_bytes()
        model = json.loads((ROOT / 'arena/config/model_deepseek_v0.2.json').read_text())
        from adapters.deepseek_chat import chat_completion
        observed = {}
        def post(url, api_key, payload, **kwargs):
            observed['request'] = json.dumps(payload, ensure_ascii=False).encode(); return json.loads(raw)
        with patch.dict('os.environ', {'DEEPSEEK_API_KEY':'offline-test-only'}), patch('adapters.deepseek_chat._post_json', side_effect=post):
            chat_completion(model, messages, response_format_json=True)
        self.assertEqual(request, observed['request'])
        self.assertEqual(result['provider_response'], json.loads(raw))
        self.assertFalse(json.loads((source.out / '0001/receipt.json').read_text())['backend_identity_verified'])

    def test_phase_gate_blocks_before_any_attempt_or_request_artifact(self):
        source = self.source([{'status':200,'body':wire_body()}], gate=lambda: False)
        with self.assertRaisesRegex(BranchConstraintError, 'BEFORE_HOST_RELEASE'): source.complete_agent([])
        self.assertEqual(source.calls, 0); self.assertFalse((source.out / '0001').exists())

    def test_http_failure_preserves_exact_bytes_and_never_refunds_or_retries(self):
        raw = b'{"error":{"message":"fixture unavailable"}}'
        source = self.source([{'status':503,'body':raw}, {'status':200,'body':wire_body()}])
        with self.assertRaisesRegex(BranchConstraintError, 'HTTP_FAILURE'): source.complete_agent([])
        self.assertEqual(source.calls, 1); self.assertEqual((source.out / '0001/response.bin').read_bytes(), raw)
        with self.assertRaisesRegex(BranchConstraintError, 'FAILED_NO_REPLAY'): source.complete_agent([])
        self.assertFalse((source.out / '0002').exists())

    def test_invalid_reply_wrong_model_and_incomplete_output_retain_raw_failure(self):
        for i, (raw, error) in enumerate([(b'not JSON', 'JSON'), (wire_body(model='foreign-model'), 'MODEL_DRIFT'),
                                         (wire_body(finish='length'), 'INCOMPLETE_RESPONSE'),
                                         (b'{"model":"deepseek-flash","model":"other"}', 'DUPLICATE_PROVIDER')]):
            with self.subTest(error=error):
                source = self.source([{'status':200,'body':raw}], name='provider-' + str(i))
                with self.assertRaises(Exception): source.complete_agent([])
                self.assertEqual((source.out / '0001/response.bin').read_bytes(), raw)
                self.assertTrue(source.failed)

    def test_malformed_model_content_is_not_repaired_or_resampled(self):
        source = self.source([{'status':200,'body':wire_body(content='MALFORMED MODEL JSON')}])
        result = source.complete_agent([])
        self.assertEqual(result['content'], 'MALFORMED MODEL JSON'); self.assertEqual(source.calls, 1)

    def test_budget_and_stale_output_prevent_extra_dispatch(self):
        source = self.source([{'status':200,'body':wire_body()}] * 4)
        for _ in range(self.profile['max_logical_calls']): source.complete_agent([])
        with self.assertRaisesRegex(BranchConstraintError, 'BUDGET_EXHAUSTED'): source.complete_agent([])
        self.assertEqual(source.calls, self.profile['remaining_horizon'])
        with self.assertRaisesRegex(BranchConstraintError, 'FRESH_PROVIDER_EXCHANGES'):
            self.source([{'status':200,'body':wire_body()}])

    def test_live_transport_and_resealed_foreign_bindings_are_rejected(self):
        with self.assertRaisesRegex(BranchConstraintError, 'LIVE_PROVIDER_TRANSPORT_NOT_BOUND'):
            BoundExchangeSource(self.profile, object(), self.root / 'live', gate=lambda: True)
        planning = self.planning(); forged = copy.deepcopy(self.bindings)
        forged['profiles']['subject']['parameters']['max_tokens'] += 1
        with self.assertRaisesRegex(BranchConstraintError, 'FROZEN_PROVIDER_BINDINGS_DRIFT'):
            PhasedMCPBranch(self.c, planning, forged, self.root / 'branch', script=OfflineScript([{'content':'{}'}]),
                repo_root=ROOT, sdk_root='missing', protocol_root='missing', verifiers={})
        self.assertFalse((self.root / 'branch').exists())

    def test_repair_pause_spends_no_subject_calls_and_keeps_original_host_state(self):
        planning = self.planning(); branch = self.branch(planning)
        with self.mcp(): paused = branch.repair()
        self.assertEqual(paused['phase'], 'REPAIRED_PAUSED_AWAITING_HOST_RELEASE')
        self.assertEqual(branch.adapter.save_state(branch.host), self.c.parent['state'])
        self.assertEqual(branch.source.calls, 0)
        with self.assertRaisesRegex(BranchConstraintError, 'BEFORE_HOST_RELEASE'):
            branch.source.complete_agent([], {'role':'release_lead','turn':2})
        with self.assertRaisesRegex(BranchConstraintError, 'REQUIRES_HOST_RELEASE'): asyncio.run(branch.continue_native())
        with self.assertRaisesRegex(BranchConstraintError, 'EXPLICIT_REPAIR_RELEASE'): asyncio.run(branch.run())
        with self.assertRaisesRegex(BranchConstraintError, 'ALREADY_ATTEMPTED'): branch.repair()
        release = branch.release(planning); self.assertFalse(release['actual_repair_agent_exit'])
        completed = asyncio.run(branch.continue_native())
        self.assertEqual(completed['scripted_subject_calls'], 1)
        self.assertEqual(completed['remaining_after'], 2)
        self.assertFalse(completed['actual_repair_agent_exit'])
        self.assertFalse(any(o['event_kind'] == 'REPAIR_AGENT_EXIT' for o in branch.observer.graph.snapshot()['observations']))
        with self.assertRaisesRegex(BranchConstraintError, 'REQUIRES_HOST_RELEASE'): asyncio.run(branch.continue_native())

    def test_changed_parent_state_cannot_release_after_successful_application_write(self):
        planning = self.planning(); branch = self.branch(planning)
        with self.mcp(): branch.repair()
        branch.host.queue.clear()
        with self.assertRaisesRegex(BranchConstraintError, 'MUTATED_PARENT_HOST'): branch.release(planning)
        self.assertEqual(branch.phase, 'FAILED_NO_REPLAY'); self.assertEqual(branch.source.calls, 0)
        self.assertIsNone(branch._release)

    def test_actor_json_cannot_substitute_for_retained_planning_identity(self):
        planning = self.planning(); branch = self.branch(planning)
        with self.mcp(): branch.repair()
        with self.assertRaisesRegex(BranchConstraintError, 'PLANNING_IDENTITY_DRIFT'): branch.release({'tools_revoked':True})
        self.assertEqual(branch.source.calls, 0); self.assertEqual(branch.phase, 'FAILED_NO_REPLAY')

    def test_unexpected_metadata_and_cross_role_adapter_fail_before_any_attempt(self):
        source = self.source([{'status':200,'body':wire_body()}])
        with self.assertRaisesRegex(BranchConstraintError, 'METADATA_KEYS_REQUIRED'):
            source.complete_agent([], {'authorization':'forbidden fixture metadata'})
        self.assertEqual(source.calls,0)
        with self.assertRaisesRegex(BranchConstraintError, 'PLANNING_PROVIDER_REQUIRED'): PlanningRequestAdapter(source)

    def test_source_hash_drift_and_native_budget_drift_are_rejected(self):
        with patch('stage2.route_repair.provider_capture.digest', return_value='changed'):
            with self.assertRaisesRegex(BranchConstraintError, 'FROZEN_SOURCE_DRIFT'): freeze_provider_bindings(self.c,ROOT)
        self.c.parent['manifest']['remaining_horizon'] += 1
        with self.assertRaisesRegex(BranchConstraintError, 'SUBJECT_HORIZON_DRIFT'): freeze_provider_bindings(self.c,ROOT)

    def test_provider_failure_after_release_retains_full_native_failure_checkpoint(self):
        planning = self.planning(); branch = self.branch(planning)
        with self.mcp(): branch.repair()
        branch.release(planning)
        branch.source.source._wire._rows[0] = {'status':503,'body':b'\xffoffline binary failure'}
        with self.assertRaisesRegex(BranchConstraintError, 'HTTP_FAILURE'): asyncio.run(branch.continue_native())
        self.assertEqual(branch.phase,'FAILED_NO_REPLAY'); self.assertEqual(branch.source.calls,1)
        self.assertTrue((branch.out / 'failure_checkpoint.json').exists())
        self.assertEqual((branch.out / 'provider_exchanges/0001/response.bin').read_bytes(),b'\xffoffline binary failure')
        with self.assertRaisesRegex(BranchConstraintError, 'REQUIRES_HOST_RELEASE'): asyncio.run(branch.continue_native())
        self.assertFalse(any(o['event_kind']=='REPAIR_AGENT_EXIT' for o in branch.observer.graph.snapshot()['observations']))

    def test_current_entry_retains_no_action_result_without_native_runtime(self):
        payload={'kind':'FINAL','decision':'UNRESOLVED','reason':'Offline unknown semantics.',
                 'inspected_refs':[],'witness_ids':[],'unknown_relations':['Actual adoption unknown.']}
        planning=ReadOnlyPlanningActorSession(self.c,self.envelope,OfflinePlanningScript([planning_fixture.response(payload)]),
            self.root/'planning',actor_id=self.bindings['profiles']['planning']['actor_id'],max_calls=16)
        entry=PhasedPlanningRepairEntry(self.c,planning,self.bindings,self.root/'entry',repo_root=ROOT)
        receipt=asyncio.run(entry.plan_and_repair())
        self.assertEqual(receipt['state'],'CLOSED_WITHOUT_REPAIR'); self.assertFalse(receipt['native_branch_created'])
        with self.assertRaisesRegex(BranchConstraintError,'ALREADY_STARTED'): asyncio.run(entry.plan_and_repair())
        with self.assertRaisesRegex(BranchConstraintError,'REQUIRES_PAUSED_REPAIR'): entry.release()

    def test_planning_actor_budget_mismatch_cannot_enter_native_repair(self):
        planning=self.planning(); planning._binding['max_calls']=17
        with self.assertRaisesRegex(BranchConstraintError,'PLANNING_ACTOR_OR_BUDGET_DRIFT'):
            self.branch(planning)
        self.assertFalse((self.root/'branch').exists())


if __name__ == '__main__': unittest.main()
