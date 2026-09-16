import unittest

from arena.branch_recovery_preflight import build_branch_recovery_preflight
from arena.experimental_control import verify_branch_manifest, verify_state_snapshot
from arena.branch_protocol import verify_anchor_selection_record, verify_recovery_record


class BranchRecoveryPreflightTest(unittest.TestCase):
    def test_preflight_preserves_parent_and_changes_branch_start(self):
        bundle = build_branch_recovery_preflight()
        parent = bundle['parent_snapshot']
        changed = bundle['intervened_start_snapshot']
        control_manifest = bundle['control_manifest']
        intervention_manifest = bundle['intervention_manifest']

        self.assertTrue(verify_state_snapshot(parent))
        self.assertTrue(verify_state_snapshot(changed))
        self.assertTrue(verify_branch_manifest(control_manifest, parent, parent))
        self.assertTrue(verify_branch_manifest(intervention_manifest, parent, changed))
        self.assertEqual(parent['state_hash'], control_manifest['parent_state_hash'])
        self.assertEqual(parent['state_hash'], intervention_manifest['parent_state_hash'])
        self.assertEqual(parent['state_hash'], control_manifest['branch_start_state_hash'])
        self.assertNotEqual(parent['state_hash'], intervention_manifest['branch_start_state_hash'])
        self.assertFalse(control_manifest['intervention_applied_before_continuation'])
        self.assertTrue(intervention_manifest['intervention_applied_before_continuation'])

    def test_anchor_selection_is_structural_and_recovery_semantics_remain_deferred(self):
        bundle = build_branch_recovery_preflight()
        selection = bundle['anchor_selection']
        recovery = bundle['recovery_record']
        self.assertTrue(verify_anchor_selection_record(selection))
        self.assertTrue(verify_recovery_record(recovery))
        self.assertFalse(selection['reviewer_labels_used_for_selection'])
        self.assertFalse(selection['branch_outcomes_visible_at_selection'])
        self.assertEqual('NOT_ADJUDICATED', recovery['regeneration_semantic_status'])
        self.assertEqual('NOT_EVALUATED', recovery['recovery_status'])

    def test_state_intervention_is_visible_to_downstream_continuation(self):
        bundle = build_branch_recovery_preflight()
        control = bundle['control_trace']
        intervention = bundle['intervention_trace']
        self.assertEqual('RUN_COMPLETE', control['run_status'])
        self.assertEqual('RUN_COMPLETE', intervention['run_status'])
        self.assertIn('FACT_PATH', control['final_state']['answer'])
        self.assertIn('PROVISIONAL_PATH', intervention['final_state']['answer'])
        self.assertEqual(
            control['experimental_branch']['parent_state_hash'],
            intervention['experimental_branch']['parent_state_hash'],
        )
        self.assertNotEqual(
            control['experimental_branch']['branch_start_state_hash'],
            intervention['experimental_branch']['branch_start_state_hash'],
        )
        self.assertEqual(
            'ENGINEERING_ONLY_NOT_SCIENTIFIC_EVIDENCE',
            bundle['summary']['scientific_status'],
        )


if __name__ == '__main__':
    unittest.main()
