import unittest

from arena.build_orchestration_manifest import build_rows, verify_pairing


class OrchestrationManifestTest(unittest.TestCase):
    def test_builder_creates_exact_free_structured_pairs(self):
        rows = build_rows(repeats=3, code_sha='TEST_SHA')
        self.assertEqual(6, len(rows))
        self.assertTrue(verify_pairing(rows))
        pairs = {}
        for row in rows:
            pairs.setdefault(row['pair_id'], []).append(row)
        self.assertEqual(3, len(pairs))
        for pair in pairs.values():
            self.assertEqual(
                {'EMERGENT_FREE_ROUTING', 'STRUCTURED_SYSTEM_OWNED_ROUTING'},
                {row['condition_id'] for row in pair},
            )
            self.assertEqual({1, 2}, {row['pair_execution_order'] for row in pair})
            self.assertEqual(1, len({row['pair_order_pattern'] for row in pair}))
            self.assertEqual(1, len({row['logical_seed'] for row in pair}))
            self.assertEqual(1, len({row['task_hash'] for row in pair}))
            self.assertEqual(1, len({row['agent_pool_hash'] for row in pair}))
            self.assertEqual(1, len({row['structured_policy_hash'] for row in pair}))
            self.assertTrue(all(row['automatic_paid_evaluator'] is False for row in pair))
            self.assertTrue(all(
                row['scientific_status'] == 'CANDIDATE_UNTIL_EXPLICIT_REAL_RUN_FREEZE_AND_API_AUTHORIZATION'
                for row in pair
            ))

        self.assertEqual('FREE_THEN_STRUCTURED', pairs['r7-ecommerce-pair-0001'][0]['pair_order_pattern'])
        self.assertEqual('EMERGENT_FREE_ROUTING', pairs['r7-ecommerce-pair-0001'][0]['condition_id'])
        self.assertEqual('STRUCTURED_THEN_FREE', pairs['r7-ecommerce-pair-0002'][0]['pair_order_pattern'])
        self.assertEqual('STRUCTURED_SYSTEM_OWNED_ROUTING', pairs['r7-ecommerce-pair-0002'][0]['condition_id'])

    def test_explicit_model_config_binding(self):
        rows = build_rows(
            repeats=1,
            code_sha='TEST_SHA',
            model_config_path='arena/config/model_deepseek_v0.2.json',
        )
        self.assertTrue(verify_pairing(rows))
        self.assertTrue(all(row['model_config_path'] == 'arena/config/model_deepseek_v0.2.json' for row in rows))
        self.assertTrue(all(row['model_provider'] == 'deepseek' for row in rows))

    def test_invalid_repeat_count_is_rejected(self):
        with self.assertRaises(ValueError):
            build_rows(repeats=0, code_sha='TEST_SHA')


if __name__ == '__main__':
    unittest.main()
