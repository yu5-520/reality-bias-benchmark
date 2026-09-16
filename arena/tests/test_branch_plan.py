import copy
import unittest
from pathlib import Path

from arena.anchor_selection import select_anchor
from arena.branch_plan import build_branch_plan, verify_branch_plan
from arena.engine import run_arena_once
from arena.io_utils import load_json, sha256_file
from arena.providers import ScriptedProvider


ROOT = Path(__file__).resolve().parents[2]


class BranchPlanTest(unittest.TestCase):
    def setUp(self):
        self.domain_path = ROOT / 'arena/domains/ecommerce.json'
        self.arena_path = ROOT / 'arena/config/arena_v0.3.json'
        self.model_path = ROOT / 'arena/config/model_deepseek_v0.2.json'
        self.rule_path = ROOT / 'arena/config/r5r6_anchor_rule_v0.1.json'
        self.domain = load_json(self.domain_path)
        self.config = load_json(self.arena_path)
        self.rule = load_json(self.rule_path)

    def _phase_a_fixture(self):
        anchors = []
        trace = run_arena_once(
            self.domain,
            self.config,
            ScriptedProvider([
                {
                    'decision_summary': 'ask inventory',
                    'actions': [{'type': 'invoke_agent', 'agent_id': 'inventory', 'request': 'Check one stock constraint.'}],
                },
                {
                    'decision_summary': 'write high-certainty candidate',
                    'actions': [
                        {
                            'type': 'write_state',
                            'key': 'inventory_view',
                            'value': 'A stockout is certain',
                            'status': 'fact',
                            'basis': 'test fixture only',
                        },
                        {'type': 'message', 'to': 'ops_lead', 'content': 'Fixture state written.'},
                    ],
                },
                {
                    'decision_summary': 'finish',
                    'actions': [{'type': 'finalize', 'answer': 'Initial plan.'}],
                },
                {
                    'decision_summary': 'finish late',
                    'actions': [{'type': 'finalize', 'answer': 'Updated plan.'}],
                },
            ]),
            'branch-plan-phase-a-fixture',
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
            'code_commit_sha': 'TEST_BASELINE_SHA',
        })
        selection = select_anchor(
            trace,
            anchors,
            self.rule,
            evidence_hash='phase-a-fixture-evidence-hash',
            selection_id='PHASE-A-FIXTURE-ANCHOR-v0.1',
        )
        self.assertEqual('ANCHOR_SELECTED', selection['selection_status'])
        return trace, selection

    def test_plan_builds_counterbalanced_control_intervention_pairs(self):
        trace, selection = self._phase_a_fixture()
        bundle = build_branch_plan(
            selection,
            trace,
            replicates=2,
            branch_code_sha='TEST_BRANCH_SHA',
        )
        self.assertTrue(verify_branch_plan(bundle))
        self.assertEqual(4, len(bundle['branch_rows']))
        self.assertEqual('NOT_AUTHORIZED', bundle['plan']['authorization_status'])
        self.assertFalse(bundle['plan']['automatic_paid_evaluator'])
        self.assertEqual('TEST_BASELINE_SHA', bundle['plan']['code_identity']['source_baseline_commit'])
        self.assertEqual('TEST_BRANCH_SHA', bundle['plan']['code_identity']['branch_execution_commit'])

        by_pair = {}
        for row in bundle['branch_rows']:
            by_pair.setdefault(row['pair_id'], []).append(row)
        self.assertEqual(2, len(by_pair))
        patterns = {rows[0]['replicate_index']: rows[0]['pair_order_pattern'] for rows in by_pair.values()}
        self.assertEqual('CONTROL_FIRST', patterns[1])
        self.assertEqual('INTERVENTION_FIRST', patterns[2])
        for rows in by_pair.values():
            self.assertEqual(1, len({row['logical_seed'] for row in rows}))
            self.assertEqual(1, len({row['parent_state_hash'] for row in rows}))
            self.assertEqual(
                {'CONTROL_CONTINUATION', 'STATUS_DOWNGRADE_INTERVENTION'},
                {row['condition_id'] for row in rows},
            )

    def test_intervention_changes_only_selected_status_in_branch_visible_snapshot(self):
        trace, selection = self._phase_a_fixture()
        bundle = build_branch_plan(selection, trace, replicates=1, branch_code_sha='TEST_BRANCH_SHA')
        parent = copy.deepcopy(bundle['parent_snapshot'])
        changed = copy.deepcopy(bundle['intervention_start_snapshot'])
        self.assertEqual(parent['anchor_ref'], changed['anchor_ref'])
        self.assertEqual(parent['turns'], changed['turns'])
        self.assertEqual(parent['events'], changed['events'])
        self.assertEqual(parent['shared_state'], changed['shared_state'])
        self.assertNotEqual(parent['state_hash'], changed['state_hash'])

        key = bundle['plan']['intervention_spec']['key']
        self.assertEqual('fact', parent['shared_state_metadata'][key]['status'])
        self.assertEqual('provisional', changed['shared_state_metadata'][key]['status'])
        p_meta = copy.deepcopy(parent['shared_state_metadata'][key])
        c_meta = copy.deepcopy(changed['shared_state_metadata'][key])
        p_meta.pop('status')
        c_meta.pop('status')
        self.assertEqual(p_meta, c_meta)

    def test_phase_b_rejects_nonselected_phase_a_package(self):
        trace, selection = self._phase_a_fixture()
        selection['selection_status'] = 'NO_ELIGIBLE_STRUCTURAL_ANCHOR'
        with self.assertRaises(ValueError):
            build_branch_plan(selection, trace, replicates=1, branch_code_sha='TEST_BRANCH_SHA')


if __name__ == '__main__':
    unittest.main()
