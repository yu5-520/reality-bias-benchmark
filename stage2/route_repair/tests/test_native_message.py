import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from stage2.native_v7.software_host_v1 import SoftwareEngineeringHost, TASKS
from stage2.r7_checkpoint_v1.host_adapter import SoftwareHostCheckpointAdapter
from stage2.r7_checkpoint_v1.common import digest, file_tree_manifest
from stage2.route_repair.branch_fields import BranchConstraintError, seal
from stage2.route_repair.native_message import ATTRIBUTION, apply_message_policy
from stage2.route_repair.proposal_authority import freeze_task_envelope, ProposalAuthorityCompiler
from stage2.route_repair.planning_session import RoutePlanningSession


class NativeMessageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        (self.root / 'a.py').write_text('working = True\n')
        self.host = SoftwareEngineeringHost(task_id='T2', checkout=self.root, provider=None, max_turns=4)
        self.host.inbox['release_lead'] = [{'from': 'frontend', 'content': 'No changes were needed.'}]
        self.adapter = SoftwareHostCheckpointAdapter(); self.state = self.adapter.save_state(self.host)
        raw = json.dumps(self.state).encode()
        locator = {'member': 'checkpoints/parent/native_state.json', 'member_sha256': digest(raw),
                   'archive_sha256': 'archive', 'json_pointer': '', 'line': None}
        file_locator = {'member': 'checkpoints/parent/application/a.py', 'member_sha256': digest(b'working = True\n'),
                        'archive_sha256': 'archive', 'json_pointer': '', 'line': None}
        self.c = SimpleNamespace(parent_checkpoint_hash='parent', parent={'state': self.state},
            case={'terminal_checkpoint_hash': 'parent', 'archive_sha256': 'archive'},
            graph={'graph_hash': 'graph', 'nodes': [{'ref': 'state:host_parent'}, {'ref': 'file:a.py'}]},
            access=SimpleNamespace(nodes={'state:host_parent': {}, 'file:a.py': {}}),
            files_by_checkpoint={'parent': {'a.py': 'hash'}},
            raw=lambda member: raw, locator=lambda member: copy.deepcopy(locator),
            read_file=lambda ref, cp=None: {'ref': ref, 'checkpoint_hash': 'parent', 'content': 'working = True\n',
                                          'source_locator': copy.deepcopy(file_locator)})
        self.s = RoutePlanningSession(self.c, TASKS['T2']); ids = []
        for read in [self.s.file('file:a.py'), self.s.message('/inbox/release_lead/0/content')]:
            ids.append(self.s.witness(read['read_id'], 0, len(read['text']))['witness_id'])
        self.action = {'action_id': 'm1', 'kind': 'PENDING_MESSAGE_REPLACE', 'target_ref': 'state:host_parent',
            'field_path': '/inbox/release_lead/0/content', 'before_value_hash': digest(b'No changes were needed.'),
            'depends_on': [], 'diagnosis_ids': ['d1']}
        self.action.update(start=0, end=len('No changes were needed.'), before_span_hash=digest(b'No changes were needed.'),
                           replacement='Fixture correction with uncertainty retained.')
        self.p = {'schema': 'stage2-complete-route-proposal-v1', 'original_task': TASKS['T2'],
            'graph_hash': 'graph', 'archive_sha256': 'archive', 'parent_checkpoint_hash': 'parent',
            'route_refs': ['state:host_parent', 'file:a.py'], 'modify_refs': ['state:host_parent'],
            'preserve_refs': ['file:a.py'], 'verify_refs': [],
            'diagnoses': [{'claim_id': 'd1', 'source_ref': 'file:a.py', 'destination_ref': 'state:host_parent',
                'status': 'SOURCE_BOUND_CLAIM', 'adoption_status': 'UNKNOWN', 'meaning_before': 'Fixture source.',
                'meaning_after': 'Fixture message.', 'authority_effect': 'Candidate only.', 'limitation': 'Not semantic truth.',
                'witness_ids': ids}], 'unknown_relations': ['Adoption unknown.'],
            'expected_postconditions': ['Exact branch field only.'], 'application_actions': [], 'host_answer': None,
            'host_message': self.action, 'verification_tasks': [], 'execution_order': ['m1']}

    def tearDown(self): self.tmp.cleanup()

    def compile(self, fields=None):
        e = freeze_task_envelope(self.c, TASKS['T2'], writable_refs=['file:a.py'], branch_id='unit',
            max_actions=1, max_value_bytes=1024, message_fields=fields if fields is not None else ['/inbox/release_lead/0/content'])
        return ProposalAuthorityCompiler(self.c, e).compile(self.s, self.p)

    def observer(self):
        self.events = []
        return SimpleNamespace(capture=lambda *args, **kwargs: self.events.append((args, kwargs)))

    def test_message_only_compiles_and_preserves_every_other_native_field(self):
        auth = self.compile(); policy = auth.bundle['host_message_policy']
        files = file_tree_manifest(self.root)
        after, receipt = apply_message_policy(self.c, self.host, self.adapter, self.root, policy, self.observer())
        expected = copy.deepcopy(self.state)
        expected['inbox']['release_lead'][0]['content'] = policy['action']['value']
        self.assertEqual(policy['action']['value'], ATTRIBUTION + self.action['replacement'])
        self.assertEqual(after, expected); self.assertEqual(file_tree_manifest(self.root), files)
        self.assertTrue(receipt['original_sender_retained']); self.assertFalse(receipt['semantic_adoption_verified'])
        self.assertIsNone(auth.bundle['application_plan']); self.assertIsNone(auth.bundle['host_answer_policy'])
        self.assertTrue(self.events[-1][1]['written'])

    def test_diagnosis_or_visible_message_cannot_grant_missing_capability(self):
        with self.assertRaisesRegex(BranchConstraintError, 'MESSAGE_OUTSIDE_TASK_ENVELOPE'): self.compile([])

    def test_sender_task_budget_and_history_fields_are_not_message_capabilities(self):
        for field in ['/inbox/release_lead/0/from', '/max_turns', '/history/0/content', '/answer']:
            with self.assertRaisesRegex(BranchConstraintError, 'CONTENT_FIELD_REQUIRED'): self.compile([field])

    def test_actor_value_or_stale_replacement_is_rejected_before_write(self):
        self.action['value'] = 'Actor-computed full message.'
        with self.assertRaisesRegex(BranchConstraintError, 'DERIVED_VALUE_MUST_BE_OMITTED'): self.compile()
        self.action.pop('value')
        self.action['replacement'] = ATTRIBUTION + 'Duplicated attribution.'
        with self.assertRaisesRegex(BranchConstraintError, 'REPLACEMENT_MUST_EXCLUDE_ATTRIBUTION'): self.compile()
        self.action['replacement'] = 'Fixture correction with uncertainty retained.'
        for key, value, error in [('before_value_hash', 'stale', 'VERSION_DRIFT'),
                                  ('depends_on', ['future'], 'DEPENDENCY')]:
            original = copy.deepcopy(self.action); self.action[key] = value
            with self.assertRaisesRegex(BranchConstraintError, error): self.compile()
            self.action.clear(); self.action.update(original)
        self.assertEqual(self.adapter.save_state(self.host), self.state)

    def test_forged_read_ledger_and_resealed_policy_cannot_authorize_write(self):
        self.s.witnesses['witness:2']['quote'] = 'fabricated'
        with self.assertRaisesRegex(BranchConstraintError, 'RECOMPILE_DRIFT'): self.compile()
        self.s.witnesses['witness:2']['quote'] = 'No changes were needed.'
        policy = self.compile().bundle['host_message_policy']; policy.pop('policy_hash')
        policy['action']['value'] = ATTRIBUTION + 'Changed after authorization.'
        policy['action']['replacement'] = 'Changed after authorization.'
        with self.assertRaisesRegex(BranchConstraintError, 'POLICY_DRIFT'):
            apply_message_policy(self.c, self.host, self.adapter, self.root, seal(policy, 'policy_hash'), self.observer())

    def test_changed_branch_host_blocks_stale_pending_message(self):
        policy = self.compile().bundle['host_message_policy']
        self.host.inbox['release_lead'][0]['content'] = 'New native message'
        with self.assertRaisesRegex(BranchConstraintError, 'STALE_BRANCH_HOST_MESSAGE'):
            apply_message_policy(self.c, self.host, self.adapter, self.root, policy, self.observer())
        self.assertEqual(self.host.inbox['release_lead'][0]['content'], 'New native message')

    def test_host_derived_value_preserves_text_outside_the_selected_clause(self):
        self.action['start'] = 3
        self.action['before_span_hash'] = digest(b'changes were needed.')
        policy = self.compile().bundle['host_message_policy']
        self.assertEqual(policy['action']['value'], ATTRIBUTION + 'No ' + self.action['replacement'])

    def test_source_quote_selection_derives_offsets_hash_without_write_authority(self):
        read = self.s.message('/inbox/release_lead/0/content')
        witness = self.s.span(read['read_id'], 'changes were needed.')
        self.assertEqual((witness['start'], witness['end']), (3, read['text_length']))
        self.assertEqual(witness['span_hash'], digest(b'changes were needed.'))
        self.assertEqual(self.adapter.save_state(self.host), self.state)
        with self.assertRaisesRegex(BranchConstraintError, 'QUOTE_NOT_PRESENT'):
            self.s.span(read['read_id'], 'invented source content')
        with self.assertRaisesRegex(BranchConstraintError, 'NOT_INSPECTED'):
            self.s.span('unread', 'changes')
        self.s.reads[read['read_id']]['text'] = 'aaa'
        with self.assertRaisesRegex(BranchConstraintError, 'QUOTE_AMBIGUOUS'):
            self.s.span(read['read_id'], 'aa')

    def test_fabricated_span_hash_cannot_replace_native_source_replay(self):
        self.s.witnesses['witness:2']['span_hash'] = digest(b'invented')
        with self.assertRaisesRegex(BranchConstraintError, 'RECOMPILE_DRIFT'): self.compile()


if __name__ == '__main__': unittest.main()
