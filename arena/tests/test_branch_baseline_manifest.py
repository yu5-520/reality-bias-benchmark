import unittest

from arena.build_branch_baseline_manifest import build_rows, verify_manifest


class BranchBaselineManifestTest(unittest.TestCase):
    def test_builder_freezes_structural_anchor_and_model_bindings(self):
        rows = build_rows(
            repeats=3,
            model_config_path='arena/config/model_deepseek_v0.2.json',
            code_sha='TEST_SHA',
        )
        self.assertEqual(3, len(rows))
        self.assertTrue(verify_manifest(rows))
        self.assertEqual(3, len({row['run_id'] for row in rows}))
        self.assertEqual(1, len({row['task_hash'] for row in rows}))
        self.assertEqual(1, len({row['anchor_rule_hash'] for row in rows}))
        self.assertEqual(1, len({row['model_config_hash'] for row in rows}))
        self.assertTrue(all(row['selection_scope'] == 'STRUCTURAL_ONLY' for row in rows))
        self.assertTrue(all(row['automatic_paid_evaluator'] is False for row in rows))
        self.assertTrue(all(
            row['snapshot_policy'] == 'BEFORE_AND_AFTER_EVERY_COMPLETED_ARENA_TURN'
            for row in rows
        ))

    def test_invalid_repeat_count_rejected(self):
        with self.assertRaises(ValueError):
            build_rows(
                repeats=0,
                model_config_path='arena/config/model_deepseek_v0.2.json',
                code_sha='TEST_SHA',
            )


if __name__ == '__main__':
    unittest.main()
