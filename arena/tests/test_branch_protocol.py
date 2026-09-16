import unittest

from arena.branch_protocol import (
    make_anchor_selection_record,
    make_recovery_record,
    verify_anchor_selection_record,
    verify_recovery_record,
)


class BranchProtocolTest(unittest.TestCase):
    def test_anchor_selection_is_structural_only_and_hashed(self):
        record = make_anchor_selection_record(
            selection_id='SEL-001',
            source_evidence_batch_hash='batch:abc',
            source_trace_hash='trace:def',
            selection_rule={
                'rule_id': 'first_realized_epistemic_status_jump_candidate',
                'tie_break': 'lowest_event_index',
            },
            candidate_event_refs=['E3', 'E7'],
            selected_anchor_ref='before_event:E3',
            selected_state_hash='state:123',
            jump_candidate_ref='E3',
        )
        self.assertTrue(verify_anchor_selection_record(record))
        self.assertFalse(record['reviewer_labels_used_for_selection'])
        self.assertFalse(record['branch_outcomes_visible_at_selection'])

    def test_anchor_selection_rejects_reviewer_driven_choice(self):
        with self.assertRaises(ValueError):
            make_anchor_selection_record(
                selection_id='SEL-002',
                source_evidence_batch_hash='batch:abc',
                source_trace_hash='trace:def',
                selection_rule={'rule_id': 'bad-rule'},
                candidate_event_refs=['E3'],
                selected_anchor_ref='before_event:E3',
                selected_state_hash='state:123',
                reviewer_labels_used_for_selection=True,
            )

    def test_recovery_record_defaults_to_not_adjudicated(self):
        record = make_recovery_record(
            recovery_id='REC-001',
            parent_branch_id='B-001',
            parent_trace_hash='trace:def',
            parent_state_hash='state:123',
            recovery_anchor_ref='after_jump:E3',
            jump_ref='E3',
            recovery_anchor_distance=2,
            recovery_strategy='CHECKPOINT_RECOVERY',
            recovery_status='PARTIAL',
            residual_descendant_count=1,
            recurrence_detected=False,
            recovery_turns=3,
            recovery_calls=3,
            recovery_tokens=1200,
            provenance_reconstruction_status='PARTIAL',
        )
        self.assertTrue(verify_recovery_record(record))
        self.assertEqual('NOT_ADJUDICATED', record['regeneration_semantic_status'])
        self.assertFalse(record['provider_internal_state_replayed'])


if __name__ == '__main__':
    unittest.main()
