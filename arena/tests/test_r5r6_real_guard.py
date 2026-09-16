import unittest
from pathlib import Path

from arena.build_branch_baseline_manifest import build_rows, verify_manifest
from arena.run_branch_baseline_real import AUTH_PHRASE, _validate_bindings


ROOT = Path(__file__).resolve().parents[2]


class R5R6RealGuardTest(unittest.TestCase):
    def setUp(self):
        self.arena_path = ROOT / 'arena/config/arena_v0.3.json'
        self.model_path = ROOT / 'arena/config/model_deepseek_v0.2.json'
        self.rule_path = ROOT / 'arena/config/r5r6_anchor_rule_v0.1.json'
        self.rows = build_rows(
            repeats=2,
            model_config_path='arena/config/model_deepseek_v0.2.json',
            code_sha='TEST_SHA',
        )

    def test_exact_authorization_phrase_is_phase_specific(self):
        self.assertEqual('CALL_REAL_R5R6_BASELINE_API', AUTH_PHRASE)
        self.assertNotEqual('CALL_REAL_R7_API', AUTH_PHRASE)

    def test_manifest_bindings_validate_without_provider_call(self):
        self.assertTrue(verify_manifest(self.rows))
        model, rule = _validate_bindings(
            self.rows,
            self.arena_path,
            self.model_path,
            self.rule_path,
            'deepseek',
        )
        self.assertEqual('deepseek', model['provider'])
        self.assertEqual('STRUCTURAL_ONLY', rule['selection_scope'])

    def test_provider_mismatch_is_rejected_before_execution(self):
        with self.assertRaises(ValueError):
            _validate_bindings(
                self.rows,
                self.arena_path,
                self.model_path,
                self.rule_path,
                'alibaba_cloud_bailian_business_space',
            )

    def test_manifest_never_authorizes_branch_continuation_or_evaluator(self):
        self.assertTrue(all(row['phase'] == 'BASELINE_SNAPSHOT_COLLECTION' for row in self.rows))
        self.assertTrue(all(row['automatic_paid_evaluator'] is False for row in self.rows))
        self.assertTrue(all(
            row['scientific_status'] == 'CANDIDATE_UNTIL_EXPLICIT_REAL_RUN_FREEZE_AND_API_AUTHORIZATION'
            for row in self.rows
        ))


if __name__ == '__main__':
    unittest.main()
