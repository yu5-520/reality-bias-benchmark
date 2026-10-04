import copy
import unittest
import tempfile
from unittest.mock import patch, Mock
from pathlib import Path
from types import SimpleNamespace

from stage2.route_repair.branch_fields import BranchConstraintError
from stage2.route_repair.paper_alignment import build_review_material, split_comparison, assess_mechanism_entry
from stage2.route_repair.prefix_context import validate_finalize_handoff

ROOT = Path(__file__).resolve().parents[3]


class PaperAlignmentTests(unittest.TestCase):
    def test_selected_reference_and_unreviewed_history_are_separate(self):
        material = build_review_material(ROOT)
        self.assertEqual(len(material['review_packets.json']), 65)
        split = material['comparison_partitions.json']
        self.assertEqual(len(split['corrected_targeted']), 8)
        self.assertEqual(len(split['historical_unreviewed']), 25)
        self.assertFalse(split['pooled_validated_reference'])
        self.assertIsNone(material['summary.json']['validated_global_accuracy'])

    def test_title_or_actor_cannot_promote_unreviewed_status(self):
        reviews = [{'full_id': 'f', 'event_id': 'e', 'reviewed_status': 'NEGATIVE_BOUNDARY'}]
        row = {'full_id': 'f', 'reference_id': 'e', 'corrected_status': 'SUPPORTED',
               'input_basis': 'CORRECTED_TARGETED_RATIONALE_AND_EVIDENCE'}
        with self.assertRaisesRegex(BranchConstraintError, 'STATUS_MISMATCH'):
            split_comparison([row], reviews)
        row['corrected_status'] = 'NEGATIVE_BOUNDARY'
        row['input_basis'] = 'ORIGINAL_FROZEN_AUDIT_UNTARGETED'
        with self.assertRaisesRegex(BranchConstraintError, 'BASIS_MISMATCH'):
            split_comparison([row], reviews)

    def context(self):
        return SimpleNamespace(parent={'state': {'history': [{}] * 4, 'inbox': {'release_lead': []}},
            'manifest': {'remaining_horizon': 60}}, file_versions={'file:web/app.js': [
                {'native_sequence': 0, 'content_sha256': 'initial'}]},
            case={'full_id': 'f', 'archive_sha256': 'archive'}, parent_checkpoint_hash='parent',
            graph={'graph_hash': 'graph'}, prefix_receipt={'invocation_membership_bindings': []})

    def test_later_historical_review_cannot_supply_missing_prefix_evidence(self):
        context = self.context()
        contract = {'target_family': 'PROCESS_ACCOUNTING', 'future_claim': 'No changes were needed'}
        result = assess_mechanism_entry(context, contract)
        self.assertFalse(result['repair_entry_ready'])
        self.assertFalse(result['future_evidence_used'])
        self.assertEqual(result['lexical_claim_candidates'], [])
        self.assertIn('TARGET_TRANSITION_NOT_SUPPORTED_BY_AVAILABLE_PREFIX', result['blockers'])

    def test_visible_contradiction_does_not_grant_native_carrier_write(self):
        context = self.context()
        context.file_versions['file:web/app.js'].append({'native_sequence': 3, 'content_sha256': 'changed'})
        context.parent['state']['inbox']['release_lead'].append({'content': 'No changes were needed.'})
        result = assess_mechanism_entry(context, {'target_family': 'PROCESS_ACCOUNTING',
            'native_claim_carrier_binding_implemented': True, 'mechanism_observation_window_frozen': True})
        self.assertTrue(result['prefix_file_transition_observed'])
        self.assertEqual(len(result['lexical_claim_candidates']), 1)
        self.assertFalse(result['repair_entry_ready'])
        self.assertFalse(result['native_repair_claim_carrier_binding_implemented'])

    def test_default_execute_stops_before_transport_or_trial_directory(self):
        from scripts import run_stage2_connected_repair as runner
        context = self.context(); context.close = Mock()
        with tempfile.TemporaryDirectory() as root:
            out = Path(root) / 'trial'
            argv = ['runner', '--source-root', root, '--sdk-root', root,
                    '--protocol-root', root, '--out', str(out), '--execute']
            with patch('sys.argv', argv), patch.object(runner, 'load_context', return_value=context), \
                    patch.object(runner, 'verify_mcp_environment'), patch.object(runner, 'DeepSeekHTTPTransport') as transport:
                with self.assertRaisesRegex(BranchConstraintError, 'PAPER_MECHANISM_ENTRY_BLOCKED'):
                    runner.main()
                transport.assert_not_called()
                self.assertFalse(out.exists())
            context.close.assert_called_once()

    def test_specialist_finalize_requires_last_action_and_observed_handoff(self):
        turn = {'role': 'frontend'}
        row = {'object_refs': ['state:finalize:frontend']}
        state = {'stop_reason': None, 'queue': ['release_lead'],
                 'inbox': {'release_lead': [{'from': 'frontend', 'content': 'result'}]}}
        validate_finalize_handoff(turn, row, 0, 1, state)
        with self.assertRaisesRegex(BranchConstraintError, 'FINALIZE_ACTION_AMBIGUITY'):
            validate_finalize_handoff(turn, row, 0, 2, state)
        with self.assertRaisesRegex(BranchConstraintError, 'FINALIZE_ACTION_AMBIGUITY'):
            validate_finalize_handoff({'role': 'release_lead'}, {'object_refs': ['state:finalize:release_lead']}, 0, 1, state)
        changed = copy.deepcopy(state); changed['inbox']['release_lead'][0]['from'] = 'unrelated'
        with self.assertRaisesRegex(BranchConstraintError, 'HANDOFF_NOT_OBSERVED'):
            validate_finalize_handoff(turn, row, 0, 1, changed)


if __name__ == '__main__':
    unittest.main()
