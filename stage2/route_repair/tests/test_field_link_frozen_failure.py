import copy
import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from stage2.r7_checkpoint_v1.common import digest
from stage2.route_repair.branch_fields import BranchConstraintError
from stage2.route_repair.connected_planning import OUTPUT_SCHEMA
from stage2.route_repair.native_message import ATTRIBUTION, materialize_message_action

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / 'stage2/replication_v2/message_field_link_failure_v1/frozen_failure_projection.json'


class FrozenFieldLinkFailureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f = json.loads(FIXTURE.read_bytes())

    def context(self):
        text = self.f['original_message']
        state = {'task_id': 'T2', 'queue': ['release_lead'],
                 'inbox': {'release_lead': [{'from': 'frontend', 'content': text}]},
                 'stop_reason': None}
        raw = json.dumps(state).encode()
        return SimpleNamespace(
            parent_checkpoint_hash='97b33360ed243c8c4ebda10598b708e1f69c1e375ba2a7a1001c0bba3d65fec5',
            parent={'state': state},
            raw=lambda member: raw,
            locator=lambda member: {'archive_sha256': self.f['source']['retained_sha256']['decision'],
                'member': member, 'member_sha256': digest(raw), 'json_pointer': '', 'line': None})

    def test_projection_preserves_original_failure_and_evidence_gap(self):
        self.assertEqual(self.f['source']['workflow_run_id'], 37300920836)
        self.assertEqual(self.f['source']['artifact_id'], 11342057023)
        self.assertEqual(self.f['observed_outcome']['failure']['message'], 'UNRELATED_MESSAGE_TEXT_DRIFT')
        self.assertEqual(self.f['observed_outcome']['native_actions_executed'], 0)
        self.assertFalse(self.f['observed_outcome']['repair_success'])
        self.assertEqual(self.f['query_operations'].count('select_source_witness'), 1)
        self.assertEqual(self.f['selected_witness_ids'], ['witness:1'])
        missing = sorted(k for k, ids in self.f['diagnosis_witnesses'].items() if not ids)
        self.assertEqual(missing, ['claim-2', 'claim-3'])
        self.assertFalse(self.f['regression_expectations']['may_rewrite_historical_output'])
        self.assertFalse(self.f['regression_expectations']['may_fabricate_witnesses'])

    def test_current_runtime_rejects_both_legacy_message_producer_duplicates(self):
        action = copy.deepcopy(self.f['host_message'])
        self.assertEqual(action['before_value_hash'], digest(self.f['original_message'].encode()))
        self.assertEqual(action['before_span_hash'], action['before_value_hash'])
        self.assertEqual((action['start'], action['end']), (0, len(self.f['original_message'])))
        self.assertEqual(action['value'], action['replacement'])
        self.assertTrue(action['replacement'].startswith(ATTRIBUTION))

        with self.assertRaisesRegex(BranchConstraintError, 'MESSAGE_DERIVED_VALUE_MUST_BE_OMITTED'):
            materialize_message_action(self.context(), action)

        action.pop('value')
        with self.assertRaisesRegex(BranchConstraintError, 'MESSAGE_REPLACEMENT_MUST_EXCLUDE_ATTRIBUTION'):
            materialize_message_action(self.context(), action)

        action['replacement'] = action['replacement'][len(ATTRIBUTION):]
        materialized = materialize_message_action(self.context(), action)
        self.assertTrue(materialized['value'].startswith(ATTRIBUTION))
        self.assertEqual(materialized['value'].count(ATTRIBUTION), 1)

        # Mechanical interface cleanup cannot manufacture the two missing
        # source witnesses. The historical final remains a failed proposal.
        self.assertEqual(
            sorted(k for k, ids in self.f['diagnosis_witnesses'].items() if not ids),
            self.f['regression_expectations']['claims_without_selected_witnesses'])

    def test_active_contract_has_one_message_value_producer(self):
        message = OUTPUT_SCHEMA['repair']['proposal']['host_message']
        self.assertNotIn('value', message)
        self.assertIn('replacement', message)
        self.assertTrue(self.f['regression_expectations']['legacy_full_value_present'])
        self.assertTrue(self.f['regression_expectations']['replacement_repeats_fixed_attribution'])


if __name__ == '__main__':
    unittest.main()
