import unittest
from pathlib import Path

from arena.anchor_selection import select_anchor
from arena.branch_plan import build_branch_plan, verify_branch_plan
from arena.engine import run_arena_once
from arena.io_utils import load_json, sha256_file
from arena.providers import ScriptedProvider
from arena.run_branch_real import AUTH_PHRASE, validate_execution_bindings


ROOT = Path(__file__).resolve().parents[2]


class R5R6BranchRealGuardTest(unittest.TestCase):
    def setUp(self):
        self.domain_path = ROOT / 'arena/domains/ecommerce.json'
        self.arena_path = ROOT / 'arena/config/arena_v0.3.json'
        self.model_path = ROOT / 'arena/config/model_deepseek_v0.2.json'
        self.rule_path = ROOT / 'arena/config/r5r6_anchor_rule_v0.1.json'
        self.domain = load_json(self.domain_path)
        self.config = load_json(self.arena_path)
        self.rule = load_json(self.rule_path)

    def _bundle(self):
        anchors = []
        trace = run_arena_once(
            self.domain,
            self.config,
            ScriptedProvider([
                {
                    'decision_summary': 'ask inventory',
                    'actions': [{'type': 'invoke_agent', 'agent_id': 'inventory', 'request': 'Check stock.'}],
                },
                {
                    'decision_summary': 'write candidate',
                    'actions': [{
                        'type': 'write_state',
                        'key': 'inventory_view',
                        'value': 'Stockout certain',
                        'status': 'fact',
                        'basis': 'guard fixture',
                    }],
                },
                {'decision_summary': 'finish', 'actions': [{'type': 'finalize', 'answer': 'Plan.'}]},
                {'decision_summary': 'finish late', 'actions': [{'type': 'finalize', 'answer': 'Plan late.'}]},
            ]),
            'r5r6-branch-guard-fixture',
            logical_seed=1,
            state_snapshot_callback=anchors.append,
        )
        trace.update({
            'provider': 'deepseek',
            'domain_hash': sha256_file(self.domain_path),
            'arena_config_path': 'arena/config/arena_v0.3.json',
            'arena_config_version': self.config['version'],
            'arena_config_hash': sha256_file(self.arena_path),
            'model_config_path': 'arena/config/model_deepseek_v0.2.json',
            'model_config_version': load_json(self.model_path).get('config_version'),
            'model_config_hash': sha256_file(self.model_path),
            'anchor_rule_path': 'arena/config/r5r6_anchor_rule_v0.1.json',
            'anchor_rule_hash': sha256_file(self.rule_path),
            'code_commit_sha': 'BASELINE_TEST_SHA',
        })
        selection = select_anchor(
            trace,
            anchors,
            self.rule,
            evidence_hash='guard-fixture-evidence',
            selection_id='GUARD-FIXTURE-SEL',
        )
        return build_branch_plan(
            selection,
            trace,
            replicates=2,
            branch_code_sha='BRANCH_TEST_SHA',
        )

    def test_authorization_phrase_is_phase_specific(self):
        self.assertEqual('CALL_REAL_R5R6_BRANCH_API', AUTH_PHRASE)
        self.assertNotEqual('CALL_REAL_R5R6_BASELINE_API', AUTH_PHRASE)
        self.assertNotEqual('CALL_REAL_R7_API', AUTH_PHRASE)

    def test_exact_frozen_bindings_validate_without_provider_call(self):
        bundle = self._bundle()
        self.assertTrue(verify_branch_plan(bundle))
        model, arena, domain = validate_execution_bindings(
            bundle,
            provider_name='deepseek',
            model_config_path='arena/config/model_deepseek_v0.2.json',
            code_sha='BRANCH_TEST_SHA',
        )
        self.assertEqual('deepseek', model['provider'])
        self.assertEqual(self.config['version'], arena['version'])
        self.assertEqual('ecommerce', domain['domain_id'])

    def test_provider_model_and_code_mismatch_are_rejected(self):
        bundle = self._bundle()
        with self.assertRaises(ValueError):
            validate_execution_bindings(
                bundle,
                provider_name='alibaba_cloud_bailian_business_space',
                model_config_path='arena/config/model_deepseek_v0.2.json',
                code_sha='BRANCH_TEST_SHA',
            )
        with self.assertRaises(ValueError):
            validate_execution_bindings(
                bundle,
                provider_name='deepseek',
                model_config_path='arena/config/model_deepseek_v0.1.json',
                code_sha='BRANCH_TEST_SHA',
            )
        with self.assertRaises(ValueError):
            validate_execution_bindings(
                bundle,
                provider_name='deepseek',
                model_config_path='arena/config/model_deepseek_v0.2.json',
                code_sha='DIFFERENT_SHA',
            )

    def test_phase_b_plan_cannot_self_authorize_or_call_evaluator(self):
        bundle = self._bundle()
        self.assertEqual('NOT_AUTHORIZED', bundle['plan']['authorization_status'])
        self.assertFalse(bundle['plan']['automatic_paid_evaluator'])
        self.assertTrue(all(row['automatic_paid_evaluator'] is False for row in bundle['branch_rows']))


if __name__ == '__main__':
    unittest.main()
