import asyncio
import copy
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from stage2.native_v7.software_host_v1 import SoftwareEngineeringHost, TASKS
from stage2.r7_checkpoint_v1.common import CheckpointRegistry, digest
from stage2.r7_checkpoint_v1.host_adapter import SoftwareHostCheckpointAdapter
from stage2.route_repair.branch_fields import BranchConstraintError
from stage2.route_repair.prefix_context import PrefixMCPContext
from stage2.route_repair.planning_session import RoutePlanningSession
from stage2.route_repair.proposal_authority import freeze_task_envelope, ProposalAuthorityCompiler
from stage2.route_repair.native_continuation import OfflineScript
from stage2.route_repair.mcp_same_parent import SameParentMCPBranch, decode_repair_tool_result


class PrefixMCPTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        app = self.root / 'source_application'; app.mkdir()
        (app / 'a.json').write_text('{"gate":"old","other":1}\n')
        (app / 'b.py').write_text('x=1\n')
        self.host = SoftwareEngineeringHost(task_id='T2', checkout=app, provider=None, max_turns=4)
        adapter = SoftwareHostCheckpointAdapter(); registry = CheckpointRegistry(self.root / 'checkpoints')
        self.rows = []
        def capture(boundary, event):
            m = adapter.capture(system_id='X4_MCP', host=self.host, registry=registry, application_root=app,
                group_id='OFFLINE_FIXTURE', run_id='fixture', task_id='T2', event_ref=event,
                model_visible_context={'turn': len(self.host.history)}, remaining_horizon=4-len(self.host.history),
                external_carrier_refs=[])
            self.rows.append({'boundary': boundary, 'event_ref': event, 'checkpoint_hash': m['checkpoint_hash'],
                              'model_decision_sequence': len(self.host.history)})
            return m['checkpoint_hash']
        capture('TASK_START', 'host:task-start')
        self.host.history.append({'turn': 1, 'role': 'release_lead', 'valid': True, 'actions': 1})
        self.cp = capture('AFTER_NATIVE_MODEL_TURN_AT_QUIESCENT_BOUNDARY', 'host:turn:0001:post')
        self.host.history.append({'turn': 2, 'role': 'release_lead', 'valid': True, 'actions': 1})
        (app / 'a.json').write_text('{"gate":"FUTURE_SECRET","other":1}\n')
        self.future_cp = capture('AFTER_NATIVE_MODEL_TURN_AT_QUIESCENT_BOUNDARY', 'host:turn:0002:post')
        self.host.history.append({'turn': 3, 'role': 'release_lead', 'valid': True, 'actions': 1})
        self.host.stop_reason = 'finalized'; self.host.answer = 'TERMINAL_SECRET'
        capture('TERMINAL', 'host:terminal')
        self.members = {'checkpoints/' + str(p.relative_to(registry.root)): p.read_bytes()
                        for p in registry.root.rglob('*') if p.is_file()}
        self.members['checkpoint_ledger.json'] = json.dumps({'checkpoints': self.rows}).encode()
        events = [{'sequence': i+1, 'actor': 'release_lead', 'kind': kind, 'object_refs': [ref]}
                  for i, (kind, ref) in enumerate([('ACTION_READ_FILE', 'file:a.json'),
                                                 ('ACTION_WRITE_FILE', 'file:a.json'), ('ACTION_FINALIZE', 'state:finalize')])]
        self.members['monitor_evidence.json'] = json.dumps(events).encode()
        for seq, tool in [(1, 'read_file'), (2, 'write_file')]:
            call = {'jsonrpc': '2.0', 'id': 3, 'method': 'tools/call',
                    'params': {'name': tool, 'arguments': {'path': 'a.json'}}}
            answer = {'jsonrpc': '2.0', 'id': 3, 'result': {'content': [{'text': 'old' if seq == 1 else 'FUTURE_SECRET'}]}}
            prefix = f'capability_observer/{seq:04d}-{tool}'
            self.members[prefix + '.client_to_server.bin'] = json.dumps(call).encode() + b'\n'
            self.members[prefix + '.server_to_client.bin'] = json.dumps(answer).encode() + b'\n'
        self.path = self.root / 'archive.tar.gz'; self.contexts = []

    def tearDown(self):
        for c in self.contexts: c.close()
        self.tmp.cleanup()

    def context(self, *, retain_failed_reads=False):
        with tarfile.open(self.path, 'w:gz') as stream:
            for name, raw in self.members.items():
                item = tarfile.TarInfo(name); item.size = len(raw); stream.addfile(item, io.BytesIO(raw))
        c = PrefixMCPContext(self.path, full_id='FIXTURE-X4-T2', archive_sha256=digest(self.path.read_bytes()),
                             parent_checkpoint_hash=self.cp, retain_failed_reads=retain_failed_reads)
        self.contexts.append(c); return c

    def authorization(self, c):
        e = freeze_task_envelope(c, TASKS['T2'], writable_refs=['file:a.json', 'file:b.py'],
                                branch_id='prefix-fixture', max_actions=2, max_value_bytes=1024)
        s = RoutePlanningSession(c, TASKS['T2']); ids = []
        for ref in ['file:a.json', 'file:b.py']:
            s.node(ref); r = s.file(ref); ids.append(s.witness(r['read_id'], 0, len(r['text']))['witness_id'])
        p = {'schema': 'stage2-complete-route-proposal-v1', 'original_task': TASKS['T2'],
            'graph_hash': c.graph['graph_hash'], 'archive_sha256': c.case['archive_sha256'],
            'parent_checkpoint_hash': c.parent_checkpoint_hash, 'route_refs': ['file:a.json', 'file:b.py'],
            'modify_refs': ['file:a.json'], 'preserve_refs': ['file:b.py'], 'verify_refs': [],
            'diagnoses': [{'claim_id': 'fixture', 'source_ref': 'file:a.json', 'destination_ref': 'file:b.py',
                'status': 'CANDIDATE', 'adoption_status': 'UNKNOWN', 'meaning_before': 'old fixture gate',
                'meaning_after': 'unreviewed fixture change', 'authority_effect': 'synthetic only',
                'limitation': 'No semantic finding.', 'witness_ids': ids}],
            'unknown_relations': ['Semantic adoption unknown.'], 'expected_postconditions': ['Exact fixture leaf changes.'],
            'application_actions': [{'action_id': 'a1', 'target_ref': 'file:a.json', 'kind': 'JSON_LEAF_REPLACE',
                'pointer': '/gate', 'before_value_hash': digest('old'), 'value': 'pending',
                'depends_on': [], 'reason': 'synthetic fixture', 'diagnosis_ids': ['fixture']}],
            'host_answer': None, 'verification_tasks': [], 'execution_order': ['a1']}
        return ProposalAuthorityCompiler(c, e).compile(s, p)

    def test_all_available_prefix_is_visible_and_future_suffix_is_absent(self):
        c = self.context(); catalog = c.catalog(TASKS['T2'])
        self.assertEqual(c.prefix_receipt['mcp_invocation_count'], 1)
        self.assertEqual(c.prefix_receipt['native_checkpoint_count'], 2)
        self.assertEqual(c.read_file('file:a.json')['content'], '{"gate":"old","other":1}\n')
        self.assertNotIn('FUTURE_SECRET', json.dumps(catalog))
        self.assertNotIn('TERMINAL_SECRET', json.dumps(c.graph))
        self.assertNotIn('state:terminal', catalog['all_node_refs'])
        self.assertFalse(catalog['parent_is_terminal'])
        self.assertFalse(c.prefix_receipt['semantic_lineage_complete'])

    def test_direct_future_member_and_file_and_observation_access_are_blocked(self):
        c = self.context()
        for member in ['natural_A_result.json', 'monitor_evidence.json', 'checkpoint_ledger.json',
                       'capability_observer/0002-write_file.client_to_server.bin']:
            with self.assertRaisesRegex(BranchConstraintError, 'OUTSIDE_VERIFIED_PREFIX'): c.raw(member)
        with self.assertRaisesRegex(BranchConstraintError, 'VERSION_OUTSIDE_VERIFIED_PREFIX'):
            c.read_file('file:a.json', self.future_cp)
        with self.assertRaisesRegex(BranchConstraintError, 'OBSERVATION_OUTSIDE_VERIFIED_PREFIX'):
            c.observation_source('unbound future record')

    def test_every_observation_is_readable_and_new_authority_uses_the_same_parent(self):
        c = self.context()
        for o in c.graph['observations']: c.observation_source(o['observation_id'])
        a = self.authorization(c)
        self.assertEqual(a.bundle['proposal']['parent_checkpoint_hash'], self.cp)
        self.assertEqual(a.bundle['application_plan']['actions'][0]['value'], 'pending')

    def test_wrong_tool_order_or_path_cannot_be_inferred_from_clock_position(self):
        events = json.loads(self.members['monitor_evidence.json']); events[0]['object_refs'] = ['file:b.py']
        self.members['monitor_evidence.json'] = json.dumps(events).encode()
        with self.assertRaisesRegex(BranchConstraintError, 'MCP_PATH_BINDING_MISMATCH'): self.context()

    def test_missing_wire_reply_and_rejected_native_result_fail_closed(self):
        member = 'capability_observer/0001-read_file.server_to_client.bin'
        old = self.members.pop(member)
        with self.assertRaisesRegex(BranchConstraintError, 'WIRE_GAP'): self.context()
        d = json.loads(old); d['result']['isError'] = True
        self.members[member] = json.dumps(d).encode()
        with self.assertRaisesRegex(BranchConstraintError, 'RESULT_NOT_ESTABLISHED'): self.context()

    def test_actor_mismatch_and_nonmonotonic_ledger_are_rejected(self):
        original = self.members['monitor_evidence.json']
        d = json.loads(original); d[0]['actor'] = 'unrelated'
        self.members['monitor_evidence.json'] = json.dumps(d).encode()
        with self.assertRaisesRegex(BranchConstraintError, 'CORRESPONDENCE_MISMATCH'): self.context()
        self.members['monitor_evidence.json'] = original
        rows = copy.deepcopy(self.rows); rows[-1]['model_decision_sequence'] = 0
        self.members['checkpoint_ledger.json'] = json.dumps({'checkpoints': rows}).encode()
        with self.assertRaisesRegex(BranchConstraintError, 'LEDGER_CLOCK_INVALID'): self.context()

    def test_explicit_failed_read_retention_does_not_establish_read_content(self):
        member = 'capability_observer/0001-read_file.server_to_client.bin'
        row = json.loads(self.members[member]); row['result']['isError'] = True
        row['result']['content'] = [{'text': 'Error executing tool read_file'}]
        self.members[member] = json.dumps(row).encode()
        c = self.context(retain_failed_reads=True)
        invocation = c.prefix_receipt['invocation_membership_bindings'][0]
        self.assertEqual(invocation['tool_result_status'], 'RETURNED_READ_ERROR')
        self.assertFalse(invocation['source_content_read_established'])
        self.assertFalse(invocation['semantic_dependency_established'])

    def test_native_result_decoder_is_repair_only_and_requires_exact_wrapper(self):
        self.assertEqual(decode_repair_tool_result({'result': json.dumps('native file')}, str), 'native file')
        with self.assertRaisesRegex(BranchConstraintError, 'RESULT_WRAPPER'):
            decode_repair_tool_result({'result': '"text"', 'extra': 'permission'}, str)
        with self.assertRaisesRegex(BranchConstraintError, 'RESULT_TYPE_MISMATCH'):
            decode_repair_tool_result({'result': '{}'}, str)

    def test_forged_value_and_live_provider_fail_before_branch_creation(self):
        c = self.context(); a = self.authorization(c); b = a.bundle
        b['proposal']['application_actions'][0]['value'] = 'forged'
        with self.assertRaisesRegex(BranchConstraintError, 'FROZEN_PROPOSAL_MISMATCH'):
            SameParentMCPBranch(c, a, b, self.root / 'branch', script=OfflineScript([{'content': '{}'}]),
                                sdk_root='missing', protocol_root='missing', verifiers={})
        with self.assertRaisesRegex(BranchConstraintError, 'LIVE_MCP_SUBJECT_CONTINUATION_DISABLED'):
            SameParentMCPBranch(c, a, a.bundle, self.root / 'branch', script=object(),
                                sdk_root='missing', protocol_root='missing', verifiers={})
        self.assertFalse((self.root / 'branch').exists())

    def test_missing_native_runtime_does_not_fall_back_to_local_writes(self):
        c = self.context(); a = self.authorization(c)
        with self.assertRaisesRegex(BranchConstraintError, 'MCP_FROZEN_RUNTIME_CAPABILITY_MISSING'):
            SameParentMCPBranch(c, a, a.bundle, self.root / 'branch', script=OfflineScript([{'content': '{}'}]),
                                sdk_root='missing', protocol_root='missing', verifiers={})
        self.assertFalse((self.root / 'branch').exists())
        self.assertFalse(a._dispatched)

    def test_host_authorization_is_consumed_once_across_native_dispatches(self):
        c = self.context(); a = self.authorization(c)
        with patch('stage2.route_repair.mcp_same_parent.verify_mcp_environment', return_value={'classification': 'SYNTHETIC_NO_NATIVE_CALLS'}):
            branch = SameParentMCPBranch(c, a, a.bundle, self.root / 'branch',
                script=OfflineScript([{'content': '{}'}]), sdk_root='synthetic', protocol_root='synthetic', verifiers={})
            with self.assertRaisesRegex(BranchConstraintError, 'AUTHORIZATION_ALREADY_DISPATCHED'):
                SameParentMCPBranch(c, a, a.bundle, self.root / 'second',
                    script=OfflineScript([{'content': '{}'}]), sdk_root='synthetic', protocol_root='synthetic', verifiers={})
            branch.host.queue.clear()
            with self.assertRaisesRegex(BranchConstraintError, 'PRE_RUN_PARENT_DRIFT'): asyncio.run(branch.run())
        self.assertFalse((self.root / 'second').exists())


if __name__ == '__main__': unittest.main()
