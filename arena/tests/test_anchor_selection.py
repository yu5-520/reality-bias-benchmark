import unittest
from pathlib import Path

from arena.anchor_selection import eligible_anchor_candidates, select_anchor, validate_anchor_rule
from arena.engine import run_arena_once
from arena.io_utils import load_json
from arena.providers import ScriptedProvider


ROOT = Path(__file__).resolve().parents[2]


class AnchorSelectionTest(unittest.TestCase):
    def setUp(self):
        self.domain = load_json(ROOT / 'arena/domains/ecommerce.json')
        self.config = load_json(ROOT / 'arena/config/arena_v0.3.json')
        self.rule = load_json(ROOT / 'arena/config/r5r6_anchor_rule_v0.1.json')

    def _run_fixture(self):
        anchors = []
        script = [
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
                'decision_summary': 'finish after late event',
                'actions': [{'type': 'finalize', 'answer': 'Updated plan.'}],
            },
        ]
        trace = run_arena_once(
            self.domain,
            self.config,
            ScriptedProvider(script),
            'anchor-selection-test',
            logical_seed=1,
            state_snapshot_callback=anchors.append,
        )
        return trace, anchors

    def test_rule_is_structural_only(self):
        self.assertTrue(validate_anchor_rule(self.rule))
        self.assertFalse(self.rule['semantic_reviewer_labels_allowed'])
        self.assertFalse(self.rule['branch_outcomes_allowed_during_selection'])

    def test_selector_chooses_lowest_event_index_replayable_candidate(self):
        trace, anchors = self._run_fixture()
        eligible = eligible_anchor_candidates(trace, anchors, self.rule, evidence_hash='fixture-evidence')
        self.assertEqual(1, len(eligible))
        result = select_anchor(trace, anchors, self.rule, evidence_hash='fixture-evidence')
        self.assertEqual('ANCHOR_SELECTED', result['selection_status'])
        self.assertEqual('after_turn:2', result['selection_record']['selected_anchor_ref'])
        self.assertEqual(
            result['selected_snapshot']['state_hash'],
            result['selection_record']['selected_state_hash'],
        )
        self.assertIn(
            'HIGH_CERTAINTY_STATE_WRITE_CANDIDATE',
            result['selected_candidate']['candidate_types'],
        )
        self.assertEqual('write_state', result['selected_candidate']['action_type'])
        self.assertFalse(result['selection_record']['reviewer_labels_used_for_selection'])
        self.assertFalse(result['selection_record']['branch_outcomes_visible_at_selection'])

    def test_no_candidate_is_preserved_without_regeneration(self):
        anchors = []
        trace = run_arena_once(
            self.domain,
            self.config,
            ScriptedProvider([
                {'decision_summary': 'finish', 'actions': [{'type': 'finalize', 'answer': 'No state write.'}]},
                {'decision_summary': 'finish late', 'actions': [{'type': 'finalize', 'answer': 'Still no state write.'}]},
            ]),
            'anchor-selection-negative-test',
            logical_seed=1,
            state_snapshot_callback=anchors.append,
        )
        result = select_anchor(trace, anchors, self.rule, evidence_hash='negative-fixture')
        self.assertEqual('NO_ELIGIBLE_STRUCTURAL_ANCHOR', result['selection_status'])
        self.assertIsNone(result['selection_record'])
        self.assertIsNone(result['selected_snapshot'])


if __name__ == '__main__':
    unittest.main()
