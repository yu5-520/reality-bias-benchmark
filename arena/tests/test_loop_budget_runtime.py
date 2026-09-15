import json
import unittest
from pathlib import Path

from arena.engine import run_arena_once
from arena.evidence import _objective_row
from arena.providers import ScriptedProvider
from arena.structural_feedback import derive_structural_feedback_rounds

ROOT = Path(__file__).resolve().parents[2]


def actions(*xs):
    return {'actions': list(xs)}


def finalize(answer):
    return {'type': 'finalize', 'answer': answer}


def invoke(agent):
    return {'type': 'invoke_agent', 'agent_id': agent, 'request': 'offline structural check'}


class LoopBudgetRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.domain = json.loads((ROOT / 'arena/domains/ecommerce.json').read_text(encoding='utf-8'))
        self.config = json.loads((ROOT / 'arena/config/arena_v0.3_k2_candidate.json').read_text(encoding='utf-8'))

    def scripted_k2_trace(self):
        # Queue/actor sequence:
        # 1 ops_lead: invoke inventory + initial FINAL
        # 2 ops_lead: consumes fixed late event + distinct settled FINAL
        # 3 inventory: sees turn-2 settled version and returns message
        # 4 ops_lead: reads inventory message, revises FINAL, invokes inventory (round 1 closes)
        # 5 inventory: sees revised version and returns another message
        # 6 ops_lead: reads return, queues risk, settles again (round 2 closes)
        # risk must remain queued and must never execute because K=2 stops immediately.
        script = [
            actions(invoke('inventory'), finalize('initial plan before fixed late event')),
            actions(finalize('post-late settled plan v1')),
            actions({'type': 'message', 'to': 'ops_lead', 'content': 'inventory return one'}),
            actions(
                {'type': 'revise_final_state', 'patch': {'decision': 'v2'}, 'reason': 'inventory return one'},
                invoke('inventory'),
            ),
            actions({'type': 'message', 'to': 'ops_lead', 'content': 'inventory return two'}),
            actions(invoke('risk'), finalize('post-return settled plan v3')),
            actions({'type': 'message', 'to': 'ops_lead', 'content': 'THIS MUST NEVER EXECUTE'}),
        ]
        provider = ScriptedProvider(script)
        trace = run_arena_once(self.domain, self.config, provider, 'k2-runtime-test', logical_seed=1)
        return trace, provider

    def test_k2_stops_exactly_after_second_closed_round(self):
        trace, provider = self.scripted_k2_trace()
        self.assertEqual(trace['run_status'], 'LOOP_BUDGET_COMPLETE')
        self.assertEqual(trace['termination_reason'], 'structural_feedback_round_limit_reached')
        self.assertTrue(trace['condition_complete'])
        self.assertFalse(trace['observation_censored'])
        self.assertEqual(trace['turns'], 6)
        self.assertEqual(provider.index, 6)

        loop = trace['loop_budget']
        self.assertTrue(loop['enabled'])
        self.assertTrue(loop['reached'])
        self.assertTrue(loop['stop_applied'])
        self.assertEqual(loop['limit'], 2)
        self.assertEqual(loop['round_count'], 2)
        self.assertEqual(loop['counter_version'], 'R4-STRUCTURAL-FEEDBACK-ROUND-v0.2')
        self.assertEqual(loop['reached_at_turn'], 6)
        self.assertEqual(len(loop['round_ids']), 2)

        # A queued third-party continuation proves the stop is the K condition,
        # not natural quiescence.
        self.assertIn('risk', trace['remaining_queue'])
        self.assertNotIn('risk', trace['executed_agents'])
        self.assertGreaterEqual(len(trace['pending_invocations']), 1)

        derived = derive_structural_feedback_rounds(trace)
        self.assertEqual(derived['round_count'], 2)
        self.assertEqual(derived['rounds'][0]['anchor_actor'], 'ops_lead')
        self.assertEqual(derived['rounds'][0]['exposure_actor'], 'inventory')
        self.assertEqual(derived['rounds'][0]['return_actor'], 'ops_lead')
        self.assertEqual(derived['rounds'][1]['anchor_actor'], 'ops_lead')
        self.assertEqual(derived['rounds'][1]['exposure_actor'], 'inventory')
        self.assertEqual(derived['rounds'][1]['return_actor'], 'ops_lead')

    def test_k2_objective_stats_are_condition_bounded_not_full_episode(self):
        trace, _ = self.scripted_k2_trace()
        row = _objective_row(trace)
        obs = row['observation']
        self.assertTrue(obs['condition_complete'])
        self.assertTrue(obs['loop_budget_bounded'])
        self.assertFalse(obs['full_episode_observed'])
        self.assertFalse(obs['observation_censored'])
        self.assertEqual(obs['loop_budget_limit'], 2)
        self.assertEqual(obs['structural_feedback_rounds_observed'], 2)
        self.assertEqual(obs['negative_finding_scope'], 'LOOP_BUDGET_CONDITION_ONLY')
        self.assertGreaterEqual(obs['remaining_queue_count'], 1)

    def test_invalid_k_or_counter_version_fails_before_provider_call(self):
        class NeverCall:
            calls = 0
            def complete_agent(self, *args, **kwargs):
                self.calls += 1
                raise AssertionError('provider must not be called')

        bad_k = dict(self.config)
        bad_k['loop_budget'] = 3
        provider = NeverCall()
        with self.assertRaises(ValueError):
            run_arena_once(self.domain, bad_k, provider, 'bad-k')
        self.assertEqual(provider.calls, 0)

        bad_version = dict(self.config)
        bad_version['loop_budget_counter_version'] = 'R4-STRUCTURAL-FEEDBACK-ROUND-v999'
        provider = NeverCall()
        with self.assertRaises(ValueError):
            run_arena_once(self.domain, bad_version, provider, 'bad-counter')
        self.assertEqual(provider.calls, 0)

    def test_base_config_remains_without_loop_stop(self):
        base = json.loads((ROOT / 'arena/config/arena_v0.3.json').read_text(encoding='utf-8'))
        trace = run_arena_once(
            self.domain,
            base,
            ScriptedProvider([actions(finalize('one')), actions(finalize('two'))]),
            'base-no-loop-budget',
        )
        self.assertEqual(trace['run_status'], 'RUN_COMPLETE')
        self.assertFalse(trace['loop_budget']['enabled'])
        self.assertIsNone(trace['experimental_stop_policy'])


if __name__ == '__main__':
    unittest.main()
