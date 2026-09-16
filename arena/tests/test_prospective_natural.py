import unittest

from arena.anchor_selection import validate_anchor_rule
from arena.build_prospective_natural_manifest import build_rows, verify_manifest
from arena.io_utils import load_json


class ProspectiveNaturalTest(unittest.TestCase):
    def test_v03_anchor_rule_is_forward_valid(self):
        rule = load_json('arena/config/r5r6_anchor_rule_v0.3.json')
        self.assertTrue(validate_anchor_rule(rule))
        self.assertEqual('STRUCTURAL_ONLY_OUTCOME_BLIND', rule['selection_scope'])
        self.assertFalse(rule['persistent_state_mutation'])

    def test_manifest_freezes_four_prospective_rows(self):
        rows = build_rows(
            contract_path='configs/prospective_natural_collection_contract_v0.1.json',
            arena_config_path='arena/config/arena_v0.3.json',
            model_config_path='arena/config/model_deepseek_v0.2.json',
            code_sha='TEST-COMMIT',
        )
        self.assertEqual(4, len(rows))
        self.assertTrue(verify_manifest(rows))
        self.assertEqual(4, len({x['run_id'] for x in rows}))
        self.assertTrue(all(x['automatic_paid_evaluator'] is False for x in rows))
        self.assertTrue(all(x['no_outcome_aware_rerun'] is True for x in rows))


if __name__ == '__main__':
    unittest.main()
