import asyncio
import copy
import gzip
import json
import unittest

from stage2.route_repair.branch_fields import BranchConstraintError
from stage2.route_repair.planning_actor import OfflinePlanningScript, ReadOnlyPlanningActorSession
from stage2.route_repair.planning_entry import OfflinePlanningRepairEntry
from stage2.route_repair.proposal_authority import freeze_task_envelope
from stage2.route_repair.tests import test_prefix_mcp as prefix_fixture


def response(payload):
    return {'content': json.dumps(payload)}


def tools_from_queries(queries):
    names = {'complete_catalog': 'catalog', 'node_context': 'node', 'read_file': 'file',
             'observation_source': 'observation', 'select_source_witness': 'witness'}
    return [response({'kind': 'TOOL', 'name': names[row['operation']], 'arguments': row['request']})
            for row in queries]


class PlanningActorTests(unittest.TestCase):
    def setUp(self):
        self.fixture = prefix_fixture.PrefixMCPTests(); self.fixture.setUp()
        self.root = self.fixture.root; self.c = self.fixture.context()
        self.envelope = freeze_task_envelope(self.c, self.fixture.host.task,
            writable_refs=['file:a.json', 'file:b.py'], branch_id='planning-test',
            max_actions=2, max_value_bytes=1024)

    def tearDown(self): self.fixture.tearDown()

    def session(self, responses, **kwargs):
        return ReadOnlyPlanningActorSession(self.c, self.envelope, OfflinePlanningScript(responses),
            self.root / 'planning', actor_id='HOST_BOUND_OFFLINE_FIXTURE', **kwargs)

    def no_action(self, decision='UNRESOLVED', refs=None, witnesses=None):
        return response({'kind': 'FINAL', 'decision': decision, 'reason': 'Insufficient fixture semantics.',
                         'inspected_refs': refs or [], 'witness_ids': witnesses or [],
                         'unknown_relations': ['Actual semantic adoption unknown.']})

    def test_repair_compiles_only_after_tools_close_and_identity_cannot_be_supplied(self):
        old = self.fixture.authorization(self.c).bundle
        messages = tools_from_queries(old['query_log'])
        messages.append(response({'kind': 'FINAL', 'decision': 'REPAIR', 'proposal': old['proposal']}))
        session = self.session(messages); outcome = asyncio.run(session.run())
        self.assertEqual(outcome['decision'], 'REPAIR')
        self.assertFalse(outcome['actual_repair_agent_exit'])
        self.assertFalse(outcome['agent_generated_proposal'])
        self.assertEqual(session.authorization.bundle['proposal'], old['proposal'])
        with self.assertRaisesRegex(BranchConstraintError, 'TOOLS_REVOKED'): session.tool('catalog', {})
        with self.assertRaisesRegex(BranchConstraintError, 'ALREADY_STARTED'): asyncio.run(session.run())
        first = json.loads(gzip.decompress((session.out / 'exchanges/0001-request.json.gz').read_bytes()))
        self.assertEqual(first['binding']['actor_id'], 'HOST_BOUND_OFFLINE_FIXTURE')

    def test_unresolved_never_requires_native_runtime_or_creates_branch(self):
        session = self.session([self.no_action()]); entry = OfflinePlanningRepairEntry(session, self.root / 'entry')
        receipt = asyncio.run(entry.run())
        self.assertFalse(receipt['native_branch_created']); self.assertIsNone(session.authorization)
        self.assertFalse(receipt['independent_review_invoked'])
        with self.assertRaisesRegex(BranchConstraintError, 'ALREADY_STARTED'): asyncio.run(entry.run())

    def test_no_repair_is_a_scoped_inspected_claim_not_an_empty_success(self):
        text = self.c.read_file('file:a.json')['content']
        session = self.session([
            response({'kind': 'TOOL', 'name': 'file', 'arguments': {'ref': 'file:a.json'}}),
            response({'kind': 'TOOL', 'name': 'witness', 'arguments': {'read_id': 'read:1', 'start': 0, 'end': len(text)}}),
            self.no_action('NO_REPAIR_NEEDED', ['file:a.json'], ['witness:1'])])
        receipt = asyncio.run(OfflinePlanningRepairEntry(session, self.root / 'entry').run())
        self.assertEqual(receipt['decision'], 'NO_REPAIR_NEEDED')
        self.assertFalse(receipt['repair_success']); self.assertFalse(receipt['native_branch_created'])

    def test_empty_no_repair_fails_with_raw_response_retained(self):
        session = self.session([self.no_action('NO_REPAIR_NEEDED')])
        with self.assertRaisesRegex(BranchConstraintError, 'INSPECTED_SCOPE_REQUIRED'): asyncio.run(session.run())
        self.assertTrue((session.out / 'exchanges/0001-response.json.gz').exists())
        self.assertEqual(json.loads((session.out / 'outcome.json').read_text())['state'], 'FAILED')
        with self.assertRaisesRegex(BranchConstraintError, 'COMPLETED_PLANNING'): _ = session.authorization

    def test_no_command_write_or_extra_tool_arguments_are_available(self):
        for name, args in [('write_file', {'path': 'a.json', 'content': 'oops'}),
                           ('file', {'ref': 'file:a.json', 'command': 'shell'})]:
            with self.subTest(name=name):
                path = self.root / 'planning'
                if path.exists():
                    import shutil; shutil.rmtree(path)
                session = self.session([response({'kind': 'TOOL', 'name': name, 'arguments': args})])
                with self.assertRaises(BranchConstraintError): asyncio.run(session.run())
                self.assertEqual(self.c.read_file('file:a.json')['content'], '{"gate":"old","other":1}\n')

    def test_future_version_access_fails_and_tools_remain_revoked(self):
        session = self.session([response({'kind': 'TOOL', 'name': 'file',
            'arguments': {'ref': 'file:a.json', 'checkpoint_hash': self.fixture.future_cp}})])
        with self.assertRaisesRegex(BranchConstraintError, 'VERSION_OUTSIDE_VERIFIED_PREFIX'): asyncio.run(session.run())
        with self.assertRaisesRegex(BranchConstraintError, 'TOOLS_REVOKED'): session.tool('catalog', {})

    def test_budget_exhaustion_retains_last_tool_response_and_does_not_retry(self):
        session = self.session([response({'kind': 'TOOL', 'name': 'catalog', 'arguments': {}})], max_calls=1)
        with self.assertRaisesRegex(BranchConstraintError, 'CALL_BUDGET'): asyncio.run(session.run())
        self.assertTrue((session.out / 'exchanges/0001-tool-result.json.gz').exists())
        outcome = json.loads((session.out / 'outcome.json').read_text())
        self.assertEqual(outcome['actor_calls'], 1); self.assertEqual(outcome['provider_calls'], 0)
        self.assertIsNone(outcome['authorization_hash'])

    def test_response_size_and_ambiguous_json_are_rejected_after_capture(self):
        for raw, size, error in [('{"kind":"FINAL","kind":"TOOL"}', 1000, 'DUPLICATE_ACTOR_JSON_FIELD'),
                                 ('{"kind":"FINAL","value":NaN}', 1000, 'NONFINITE_ACTOR_JSON'),
                                 ('not json', 2, 'RESPONSE_BUDGET')]:
            with self.subTest(error=error):
                path = self.root / 'planning'
                if path.exists():
                    import shutil; shutil.rmtree(path)
                session = self.session([{'content': raw}], max_response_bytes=size)
                with self.assertRaisesRegex(BranchConstraintError, error): asyncio.run(session.run())
                captured = json.loads(gzip.decompress((path / 'exchanges/0001-response.json.gz').read_bytes()))
                self.assertEqual(captured['content'], raw)

    def test_unknown_diagnosis_cannot_be_promoted_to_write_by_actor(self):
        old = self.fixture.authorization(self.c).bundle; p = copy.deepcopy(old['proposal'])
        p['diagnoses'][0]['status'] = 'UNKNOWN'
        session = self.session(tools_from_queries(old['query_log']) + [response({'kind': 'FINAL', 'decision': 'REPAIR', 'proposal': p})])
        with self.assertRaisesRegex(BranchConstraintError, 'UNKNOWN_CLAIM_CANNOT'): asyncio.run(session.run())
        self.assertTrue((session.out / 'decision.json').exists())
        self.assertFalse((session.out / 'authorization.json').exists())

    def test_live_actor_and_actor_identity_spoof_are_rejected(self):
        with self.assertRaisesRegex(BranchConstraintError, 'LIVE_PLANNING_ACTOR_DISABLED'):
            ReadOnlyPlanningActorSession(self.c, self.envelope, object(), self.root / 'live', actor_id='live')
        self.assertFalse((self.root / 'live').exists())
        payload = json.loads(self.no_action()['content']); payload['actor_origin'] = 'LIVE_AGENT'
        session = self.session([response(payload)])
        with self.assertRaisesRegex(BranchConstraintError, 'EXACT_NO_ACTION'): asyncio.run(session.run())

    def test_missing_native_binding_fails_without_replay_or_local_write(self):
        old = self.fixture.authorization(self.c).bundle
        session = self.session(tools_from_queries(old['query_log']) + [response({'kind': 'FINAL', 'decision': 'REPAIR', 'proposal': old['proposal']})])
        entry = OfflinePlanningRepairEntry(session, self.root / 'entry')
        with self.assertRaisesRegex(BranchConstraintError, 'LIVE_MCP_SUBJECT_CONTINUATION_DISABLED'):
            asyncio.run(entry.run())
        receipt = json.loads((entry.out / 'entry_receipt.json').read_text())
        self.assertFalse(receipt['native_branch_created']); self.assertEqual(receipt['state'], 'FAILED')

    def test_forged_no_action_witness_cannot_certify_no_repair(self):
        session = self.session([self.no_action('NO_REPAIR_NEEDED', ['file:a.json'], ['witness:forged'])])
        with self.assertRaisesRegex(BranchConstraintError, 'NO_ACTION_SOURCE_NOT_INSPECTED'): asyncio.run(session.run())
        self.assertIsNone(session.outcome['authorization_hash'])

    def test_failed_planning_is_linked_to_host_receipt_and_cannot_be_reused(self):
        session = self.session([{'content': 'malformed JSON'}])
        entry = OfflinePlanningRepairEntry(session, self.root / 'entry')
        with self.assertRaises(json.JSONDecodeError): asyncio.run(entry.run())
        receipt = json.loads((entry.out / 'entry_receipt.json').read_text())
        self.assertEqual(receipt['planning_outcome_hash'], session.outcome['outcome_hash'])
        with self.assertRaisesRegex(BranchConstraintError, 'FRESH_HOST_PLANNING_SESSION'):
            OfflinePlanningRepairEntry(session, self.root / 'second')
        with self.assertRaisesRegex(BranchConstraintError, 'FRESH_PLANNING_ACTOR'):
            ReadOnlyPlanningActorSession(self.c, self.envelope, session._actor, self.root / 'other', actor_id='other')


if __name__ == '__main__': unittest.main()
