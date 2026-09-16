import unittest
from pathlib import Path

from arena.io_utils import load_json
from arena.providers import ScriptedProvider
from arena.structured_routing import (
    prepare_structured_state,
    run_structured_once,
    validate_structured_policy,
)


ROOT = Path(__file__).resolve().parents[2]


class StructuredRoutingTest(unittest.TestCase):
    def setUp(self):
        self.domain = load_json(ROOT / 'arena/domains/ecommerce.json')
        self.config = load_json(ROOT / 'arena/config/arena_v0.3.json')
        self.policy = load_json(ROOT / 'arena/config/structured_ecommerce_v0.1.json')

    def test_policy_and_queue_are_system_owned(self):
        self.assertTrue(validate_structured_policy(self.domain, self.policy))
        state = prepare_structured_state(
            self.domain,
            self.config,
            'structured-policy-test',
            self.policy,
        )
        self.assertEqual(
            ['ads', 'inventory', 'finance', 'ops_lead'],
            list(state.queue),
        )
        self.assertEqual(
            {'ads', 'inventory', 'finance', 'ops_lead'},
            state.active_agents,
        )

    def test_structured_run_blocks_dynamic_invocation_and_keeps_subject_proposal(self):
        scripted = ScriptedProvider([
            {
                'decision_summary': 'media assessment plus attempted extra call',
                'actions': [
                    {'type': 'invoke_agent', 'agent_id': 'pricing', 'request': 'Check pricing too.'},
                    {
                        'type': 'write_state',
                        'key': 'media_view',
                        'value': 'A strongest incremental media candidate',
                        'status': 'provisional',
                        'basis': 'incremental ROAS',
                    },
                ],
            },
            {
                'decision_summary': 'inventory assessment',
                'actions': [
                    {
                        'type': 'write_state',
                        'key': 'inventory_view',
                        'value': 'A stock requires conservative allocation',
                        'status': 'provisional',
                        'basis': 'stock and lead time',
                    }
                ],
            },
            {
                'decision_summary': 'finance assessment',
                'actions': [
                    {
                        'type': 'write_state',
                        'key': 'finance_view',
                        'value': 'Protect blended ROAS and contribution floor',
                        'status': 'provisional',
                        'basis': 'margin and ROAS constraints',
                    }
                ],
            },
            {
                'decision_summary': 'integrate and finalize',
                'actions': [
                    {
                        'type': 'write_state',
                        'key': 'integrated_plan',
                        'value': 'Executable 7-day plan based on recorded stage evidence',
                        'status': 'recommendation',
                        'basis': 'media + inventory + finance stage contributions',
                    },
                    {'type': 'finalize', 'answer': 'Initial structured plan.'},
                ],
            },
            {
                'decision_summary': 'handle late event without new routing',
                'actions': [
                    {
                        'type': 'revise_final_state',
                        'patch': {'inventory_view': 'A preliminary stock signal requires bounded adjustment'},
                        'reason': 'late preliminary inventory signal',
                        'status': 'provisional',
                    },
                    {'type': 'finalize', 'answer': 'Updated structured plan.'},
                ],
            },
        ])
        anchors = []
        trace = run_structured_once(
            self.domain,
            self.config,
            scripted,
            self.policy,
            'structured-run-test',
            logical_seed=1,
            state_snapshot_callback=anchors.append,
        )

        self.assertEqual('RUN_COMPLETE', trace['run_status'])
        self.assertEqual('system_owned_routing', trace['orchestration_condition']['mode'])
        self.assertEqual(0, trace['total_invocations'])
        self.assertEqual(
            ['S1_media', 'S2_inventory', 'S3_finance', 'S4_integrate'],
            trace['orchestration_condition']['stage_ids'],
        )
        self.assertGreaterEqual(len(anchors), 8)

        first_call_control = trace['model_calls'][0]['provider_response']['structured_routing']
        self.assertEqual('S1_media', first_call_control['stage_id'])
        self.assertEqual(1, len(first_call_control['blocked_actions']))
        self.assertEqual(
            'SYSTEM_OWNS_INVOCATION_GRAPH',
            first_call_control['blocked_actions'][0]['reason'],
        )
        self.assertEqual('invoke_agent', first_call_control['blocked_actions'][0]['action']['type'])
        self.assertFalse(any(e['action_type'] == 'invoke_agent' for e in trace['events']))


if __name__ == '__main__':
    unittest.main()
