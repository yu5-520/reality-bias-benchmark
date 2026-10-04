import asyncio
import copy
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

from stage2.route_repair.branch_fields import BranchConstraintError, seal
from stage2.route_repair.connected_provider import DeepSeekHTTPTransport, LoopbackHTTPTransport, ConnectedExchangeSource, freeze_connected_bindings
from stage2.route_repair.connected_planning import ConnectedPlanningSession, freeze_connected_envelope
from stage2.route_repair.connected_mcp import ConnectedMCPBranch, ConnectedPlanningRepairEntry
from stage2.route_repair.http_fixture import FixtureHTTPServer, fixture_reply
from stage2.route_repair.tests import test_prefix_mcp as prefix_fixture
from stage2.route_repair.tests.test_planning_actor import tools_from_queries
ROOT = Path(__file__).resolve().parents[3]


def final(decision='UNRESOLVED'):
    return json.dumps({'kind': 'FINAL', 'decision': decision, 'reason': 'Fixture scope only.',
        'inspected_refs': [], 'witness_ids': [], 'unknown_relations': ['Actual semantic adoption unknown.']})


class ConnectedProviderTests(unittest.TestCase):
    def setUp(self):
        self.fixture = prefix_fixture.PrefixMCPTests(); self.fixture.setUp(); self.root = self.fixture.root; self.c = self.fixture.context()
        self.cap = {'verification_id': 'v1', 'operation': 'HOST_DEFINED_OFFLINE_CHECK',
                    'refs': ['file:b.py'], 'postcondition': 'Synthetic host check.'}
        self.envelope = freeze_connected_envelope(self.c, self.c.catalog(self.fixture.host.task)['original_task'],
            writable_refs=['file:a.json', 'file:b.py'], branch_id='connected-unit', max_actions=2, max_value_bytes=1024)

    def tearDown(self): self.fixture.tearDown()

    def source(self, server, *, role='subject', gate=lambda: True, name='http', profile=None):
        self.transport = LoopbackHTTPTransport(server.port)
        self.bindings = freeze_connected_bindings(self.c, ROOT, self.transport)
        return ConnectedExchangeSource(profile or self.bindings['profiles'][role], self.transport, self.root/name, gate=gate)

    def planner(self, server):
        source = self.source(server, role='planning')
        return ConnectedPlanningSession(self.c, self.envelope, source, self.root/'planning', verification_capabilities=[self.cap])

    def repair_rows(self, *, alter=None):
        bundle = self.fixture.authorization(self.c).bundle; proposal = bundle['proposal']
        proposal['verification_tasks'] = [{**self.cap, 'depends_on': ['a1']}]; proposal['execution_order'].append('v1')
        if alter: alter(proposal)
        return [fixture_reply(r['content']) for r in tools_from_queries(bundle['query_log'])] + [
            fixture_reply(json.dumps({'kind':'FINAL','decision':'REPAIR','proposal':proposal}))]

    def branch(self, planning, verifier=lambda root: {'passed': True}):
        with patch('stage2.route_repair.connected_mcp.verify_mcp_environment', return_value={'origin':'MOCK_NATIVE_UNIT_ONLY'}):
            return ConnectedMCPBranch(self.c, planning, self.bindings, self.root/'branch', transport=self.transport,
                repo_root=ROOT, sdk_root='mock', protocol_root='mock', verifiers={'v1': {**self.cap, 'run': verifier}})

    def mcp(self):
        def read(proxy, path): return {'result': json.dumps((proxy.root/path).read_text())}
        def write(proxy, path, content): (proxy.root/path).write_text(content); return {'result':'{}'}
        return patch.multiple('stage2.route_repair.connected_mcp.ConnectedMCPCheckout', read_file=read, write_file=write)

    def test_actual_socket_body_and_unchanged_message_are_captured_before_parse(self):
        row = fixture_reply('NOT MODEL JSON')
        with FixtureHTTPServer([row]) as server:
            source = self.source(server); result = source.complete_agent([{'role':'user','content':'中文'}])
        self.assertEqual(result['content'], 'NOT MODEL JSON')
        self.assertEqual(server.requests, [(source.out/'0001/request.bin').read_bytes()])
        self.assertEqual((source.out/'0001/response.bin').read_bytes(), row['body'])
        self.assertEqual(source.provider_calls, 0); self.assertEqual(source.transport_attempts, 1)
        self.assertFalse(json.loads((source.out/'0001/receipt.json').read_bytes())['backend_identity_verified'])

    def test_missing_key_blocks_before_any_http_or_capture(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(BranchConstraintError, 'CREDENTIAL_UNAVAILABLE'): DeepSeekHTTPTransport()
        self.assertFalse((self.root/'http').exists())

    def test_gate_blocks_before_budget_or_request(self):
        with FixtureHTTPServer([fixture_reply('{}')]) as server:
            source = self.source(server, gate=lambda: False)
            with self.assertRaisesRegex(BranchConstraintError, 'BEFORE_HOST_RELEASE'): source.complete_agent([])
            self.assertEqual(source.calls, 0); self.assertEqual(server.requests, [])
            self.assertFalse((source.out/'0001').exists())

    def test_http_error_and_invalid_reply_cannot_retry(self):
        for i, row in enumerate([{'status':503,'body':b'raw unavailable'}, {'status':200,'body':b'not JSON'},
                                 fixture_reply('{}', model='other-model')]):
            with FixtureHTTPServer([row, fixture_reply('{}')]) as server:
                source = self.source(server, name='http'+str(i))
                with self.assertRaises(Exception): source.complete_agent([])
                with self.assertRaisesRegex(BranchConstraintError, 'NO_REPLAY'): source.complete_agent([])
                self.assertEqual(len(server.requests), 1)
                self.assertEqual((source.out/'0001/response.bin').read_bytes(), row['body'])

    def test_truncated_body_is_retained_as_incomplete_and_not_resampled(self):
        row = {'status':200, 'body':b'{"partial":', 'declared_length':100}
        with FixtureHTTPServer([row]) as server:
            source = self.source(server)
            with self.assertRaisesRegex(BranchConstraintError, 'TRUNCATED'): source.complete_agent([])
        self.assertEqual((source.out/'0001/response.bin').read_bytes(), row['body'])
        receipt = json.loads((source.out/'0001/receipt.json').read_bytes())
        self.assertFalse(receipt['response_body_complete']); self.assertEqual(receipt['transport_attempts'], 1)

    def test_oversized_body_prefix_is_retained_without_followup(self):
        with FixtureHTTPServer([{'status':200,'body':b'123456789'}]) as server:
            transport = LoopbackHTTPTransport(server.port); bindings = freeze_connected_bindings(self.c, ROOT, transport)
            p = copy.deepcopy(bindings['profiles']['subject']); p.pop('profile_hash'); p['max_response_bytes'] = 4
            source = ConnectedExchangeSource(seal(p,'profile_hash'), transport, self.root/'http', gate=lambda: True)
            with self.assertRaisesRegex(BranchConstraintError, 'BODY_LIMIT'): source.complete_agent([])
        self.assertEqual((source.out/'0001/response.bin').read_bytes(), b'12345')
        self.assertTrue(source.failed)

    def test_mutated_transport_or_profile_cannot_dispatch(self):
        with FixtureHTTPServer([fixture_reply('{}')]) as server:
            source = self.source(server); source._transport.port += 1
            with self.assertRaisesRegex(BranchConstraintError, 'TRANSPORT_MUTATED'): source.complete_agent([])
            source._transport.port -= 1; source._profile['max_logical_calls'] += 1
            with self.assertRaisesRegex(BranchConstraintError, 'PROFILE_MUTATED'): source.complete_agent([])
            self.assertEqual(server.requests, [])

    def test_budget_and_native_turn_bound_prevent_extra_requests(self):
        with FixtureHTTPServer([fixture_reply('{}')]*4) as server:
            source = self.source(server)
            with self.assertRaisesRegex(BranchConstraintError, 'TURN_DRIFT'): source.complete_agent([], {'turn':99})
            for turn in range(2, 5): source.complete_agent([], {'turn':turn})
            with self.assertRaisesRegex(BranchConstraintError, 'BUDGET_EXHAUSTED'): source.complete_agent([])
            self.assertEqual(len(server.requests),3)

    def test_unresolved_does_not_create_native_branch_or_claim_exit(self):
        with FixtureHTTPServer([fixture_reply(final())]) as server:
            planning = self.planner(server)
            entry = ConnectedPlanningRepairEntry(self.c, planning, self.bindings, self.root/'host', repo_root=ROOT, transport=self.transport)
            result = asyncio.run(entry.plan_and_repair())
        self.assertEqual(result['state'], 'CLOSED_WITHOUT_REPAIR'); self.assertFalse(result['native_branch_created'])
        self.assertFalse(planning.outcome['agent_generated_proposal']); self.assertEqual(planning.outcome['provider_calls'],0)
        self.assertFalse(planning.outcome['actual_repair_agent_exit'])
        with self.assertRaisesRegex(BranchConstraintError, 'BEFORE_HOST_RELEASE'): planning._source.complete_agent([])
        with self.assertRaisesRegex(BranchConstraintError, 'TOOLS_REVOKED'): planning.tool('catalog', {})
        with self.assertRaisesRegex(BranchConstraintError, 'ALREADY_STARTED'): asyncio.run(entry.plan_and_repair())

    def test_malformed_or_injected_actor_fields_close_the_first_attempt(self):
        for i, content in enumerate(['{"kind":"FINAL","kind":"TOOL"}', final().replace('"UNRESOLVED"','NaN'),
                                     json.dumps({'kind':'TOOL','name':'write_file','arguments':{}})]):
            with FixtureHTTPServer([fixture_reply(content)]) as server:
                source = self.source(server, role='planning', name='http'+str(i))
                planning = ConnectedPlanningSession(self.c, self.envelope, source, self.root/('planning'+str(i)), verification_capabilities=[self.cap])
                with self.assertRaises(Exception): asyncio.run(planning.run())
                self.assertEqual(planning.outcome['state'], 'FAILED'); self.assertTrue(planning.outcome['tools_revoked'])
                self.assertEqual(source.calls,1); self.assertEqual(len(server.requests),1)

    def test_http_generated_repair_retains_host_authority_and_loopback_never_claims_real_exit(self):
        rows = self.repair_rows() + [fixture_reply(json.dumps({'actions':[{'type':'finalize','answer':'unit fixture'}]}))]
        with FixtureHTTPServer(rows) as server:
            planning = self.planner(server); asyncio.run(planning.run())
            authorization = planning.authorization; self.assertEqual(authorization.bundle['origin'], 'LOOPBACK_HTTP_FIXTURE')
            self.assertFalse(authorization.bundle['repair_agent_generated'])
            branch = self.branch(planning)
            with self.mcp(): paused = branch.repair()
            self.assertEqual(paused['subject_calls'],0); self.assertEqual(branch.adapter.save_state(branch.host),self.c.parent['state'])
            with self.assertRaisesRegex(BranchConstraintError,'BEFORE_HOST_RELEASE'): branch.source.complete_agent([])
            release = branch.release(planning); self.assertFalse(release['actual_repair_agent_exit'])
            result = asyncio.run(branch.continue_native())
            self.assertEqual(result['subject_calls'],1); self.assertFalse(result['repair_success'])
            self.assertFalse(any(o['event_kind']=='REPAIR_AGENT_EXIT' for o in branch.observer.graph.snapshot()['observations']))
        with self.assertRaisesRegex(BranchConstraintError,'REQUIRES_HOST_RELEASE'): asyncio.run(branch.continue_native())
        with self.assertRaisesRegex(BranchConstraintError,'ONE_USE_AUTHORIZATION'): self.branch(planning)

    def test_unbound_verification_cannot_become_a_native_command(self):
        rows = self.repair_rows(alter=lambda p: p['verification_tasks'][0].update(postcondition='Actor-chosen arbitrary check'))
        with FixtureHTTPServer(rows) as server:
            planning = self.planner(server)
            with self.assertRaisesRegex(BranchConstraintError,'VERIFICATION_NOT_HOST_BOUND'): asyncio.run(planning.run())
        self.assertIsNone(planning._authorization)

    def test_resealed_actor_proposal_does_not_replace_retained_native_authorization(self):
        with FixtureHTTPServer(self.repair_rows()) as server:
            planning = self.planner(server); asyncio.run(planning.run()); branch = self.branch(planning)
            branch.bundle['proposal']['application_actions'][0]['value'] = 'forged'
            with self.assertRaisesRegex(BranchConstraintError,'AUTHORIZATION_DRIFT'): branch.repair()
        self.assertEqual(branch.phase,'FAILED_NO_REPLAY'); self.assertEqual(branch.source.calls,0)
        self.assertTrue((branch.out/'failure_checkpoint.json').exists())

    def test_failed_verifier_prevents_release_and_subject_calls(self):
        with FixtureHTTPServer(self.repair_rows()) as server:
            planning = self.planner(server); asyncio.run(planning.run()); branch = self.branch(planning, lambda r: {'passed':False})
            with self.mcp(), self.assertRaisesRegex(BranchConstraintError,'VERIFICATION_FAILED'): branch.repair()
        self.assertEqual(branch.phase,'FAILED_NO_REPLAY'); self.assertEqual(branch.source.calls,0)
        with self.assertRaisesRegex(BranchConstraintError,'REQUIRES_PAUSED_REPAIR'): branch.release(planning)

    def test_simulated_live_exit_requires_closed_session_and_opens_only_review_readiness(self):
        # A mocked live driver validates host gates, never empirical live evidence.
        rows = self.repair_rows() + [fixture_reply(json.dumps({'actions':[{'type':'finalize','answer':'simulated'}]}))]
        with FixtureHTTPServer(rows) as server, patch.dict(os.environ, {'DEEPSEEK_API_KEY':'unit-placeholder'}):
            loop = LoopbackHTTPTransport(server.port); self.transport = DeepSeekHTTPTransport()
            self.bindings = freeze_connected_bindings(self.c, ROOT, self.transport)
            with patch.object(DeepSeekHTTPTransport, 'send', side_effect=loop.send):
                source = ConnectedExchangeSource(self.bindings['profiles']['planning'], self.transport, self.root/'http', gate=lambda:True)
                planning = ConnectedPlanningSession(self.c, self.envelope, source, self.root/'planning', verification_capabilities=[self.cap])
                asyncio.run(planning.run()); branch = self.branch(planning)
                with self.mcp(): branch.repair()
                release = branch.release(planning); self.assertTrue(release['actual_repair_agent_exit'])
                result = asyncio.run(branch.continue_native()); self.assertFalse(result['repair_success'])
                assessment = json.loads((branch.out/'continuation_assessment.json').read_bytes())
                self.assertEqual(assessment['status'], 'PENDING_INDEPENDENT_SEMANTIC_REVIEW')
                self.assertEqual(assessment['repair_exit_observation_id'],branch._exit_observation_id)
                self.assertTrue(assessment['ordered_post_exit_observation_ids'])
        for path in self.root.rglob('*'):
            if path.is_file() and path.suffix in {'.json','.bin'}: self.assertNotIn(b'unit-placeholder',path.read_bytes())

    def test_inflight_planning_cannot_certify_exit_or_dispatch_subject(self):
        with FixtureHTTPServer(self.repair_rows()) as server:
            planning = self.planner(server); asyncio.run(planning.run()); branch = self.branch(planning)
            with self.mcp(): branch.repair()
            planning._source.in_flight=True
            with self.assertRaisesRegex(BranchConstraintError,'CLOSED_VALID_PLANNING'): branch.release(planning)
            self.assertIsNone(branch._release); self.assertEqual(branch.source.calls,0)

    def test_future_source_and_binding_injection_are_blocked_without_second_attempt(self):
        payload=json.dumps({'kind':'TOOL','name':'file','arguments':{'ref':'file:a.json','checkpoint_hash':self.fixture.future_cp}})
        with FixtureHTTPServer([fixture_reply(payload)]) as server:
            planning=self.planner(server)
            with self.assertRaisesRegex(BranchConstraintError,'OUTSIDE_VERIFIED_PREFIX'): asyncio.run(planning.run())
            self.assertEqual(planning.outcome['state'],'FAILED'); self.assertEqual(len(server.requests),1)
        with FixtureHTTPServer([fixture_reply(final())]) as server:
            source=self.source(server,role='planning',name='other-http')
            planning=ConnectedPlanningSession(self.c,self.envelope,source,self.root/'other-planning',verification_capabilities=[self.cap])
            planning._binding['actor_id']='actor-supplied'
            with self.assertRaisesRegex(BranchConstraintError,'BINDING_MUTATED'): asyncio.run(planning.run())
            self.assertEqual(server.requests,[])

    def test_retained_first_attempt_type_spelling_stays_rejected_without_replay(self):
        # Actual first-attempt content from the captured model response. Preserve
        # this failure; a clearer prompt must not silently convert it to a tool.
        content = '{"type": "TOOL", "name": "message", "arguments": {"field_path": "/inbox/release_lead/0/content"}}'
        with FixtureHTTPServer([fixture_reply(content), fixture_reply(final())]) as server:
            planning = self.planner(server)
            with self.assertRaisesRegex(BranchConstraintError, 'EXACT_READ_ONLY_TOOL_MESSAGE_REQUIRED'):
                asyncio.run(planning.run())
            self.assertEqual(server.position, 1)
            self.assertEqual(planning.outcome['tool_queries'], 0)
            self.assertEqual(planning.outcome['native_actions_executed'], 0)
            self.assertEqual(planning.outcome['state'], 'FAILED')
            self.assertTrue(planning.outcome['tools_revoked'])
            response = json.loads((planning._source.out / '0001/response.bin').read_bytes())
            self.assertEqual(response['choices'][0]['message']['content'], content)

    def test_root_contract_and_literal_kind_example_match_the_read_only_parser(self):
        catalog = json.dumps({'kind': 'TOOL', 'name': 'catalog', 'arguments': {}})
        with FixtureHTTPServer([fixture_reply(catalog), fixture_reply(final())]) as server:
            planning = self.planner(server); result = asyncio.run(planning.run())
            request = json.loads(server.requests[0])
            host_request = json.loads(request['messages'][1]['content'])
            self.assertIn('"kind":"TOOL"', host_request['instructions'])
            self.assertEqual(host_request['response_contract']['oneOf'][0]['required'], ['kind', 'name', 'arguments'])
            self.assertFalse(host_request['response_contract']['oneOf'][0]['additionalProperties'])
            self.assertEqual(result['state'], 'COMPLETED')
            self.assertEqual(result['tool_queries'], 1)
            self.assertEqual(result['actor_calls'], 2)

    def test_late_process_log_changes_cannot_mutate_retained_wire_snapshots(self):
        from stage2.route_repair.connected_mcp import ConnectedMCPCheckout
        from stage2.r7_checkpoint_v1.common import digest
        root=self.root/'wire-branch'; root.mkdir(); captured=[]
        class Observer:
            def capture(self, ref, content, phase, **kwargs): captured.append((phase,content,kwargs))
        branch=SimpleNamespace(out=root,phase='NATIVE_REPAIR_EXECUTION',capture=lambda phase:None,observer=Observer())
        proxy=ConnectedMCPCheckout(self.root,branch)
        def native(client,tool,arguments):
            client.sequence+=1; wire=Path(client.observer_root);wire.mkdir()
            bodies={'client_to_server':b'{"jsonrpc":"2.0","method":"tools/call"}\n',
                    'server_to_client':b'{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-11-25","serverInfo":{"name":"stage2-x4-checkout"}}}\n',
                    'server_stderr':b''}
            for direction,raw in bodies.items(): (wire/('0001-read_file.'+direction+'.bin')).write_bytes(raw)
            return {'result':'"original"'}
        with patch('stage2.route_repair.connected_mcp.MCPCheckoutProxy._invoke',new=native):
            self.assertEqual(proxy.read_file('a.json'),{'result':'"original"'})
        retained=root/'retained_wire/0001-read_file.client_to_server.bin'; original=retained.read_bytes()
        (root/'native_wire/0001-read_file.client_to_server.bin').write_bytes(b'late partial process log')
        self.assertEqual(retained.read_bytes(),original)
        receipts=[kwargs['receipt'] for phase,content,kwargs in captured if phase.startswith('MCP_WIRE_')]
        self.assertEqual(len(receipts),3)
        for receipt in receipts: self.assertEqual(digest((root/receipt['wire_member']).read_bytes()),receipt['wire_sha256'])


if __name__ == '__main__': unittest.main()
