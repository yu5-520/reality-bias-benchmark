import unittest
from pathlib import Path

from arena.cost_budget import BudgetExceeded, BudgetedProvider, observed_cost_from_usage, pricing_policy
from arena.io_utils import load_json
from arena.providers import ScriptedProvider


ROOT = Path(__file__).resolve().parents[2]


class CostBudgetTest(unittest.TestCase):
    def setUp(self):
        self.model = load_json(ROOT / 'arena/config/model_deepseek_v0.2.json')

    def test_deepseek_policy_uses_peak_pricing_snapshot(self):
        policy = pricing_policy(self.model)
        self.assertEqual('USD', policy['currency'])
        self.assertEqual('configured_peak_price', policy['mode'])
        self.assertGreater(policy['output_per_million'], 0)

    def test_observed_cost_uses_provider_usage(self):
        cost = observed_cost_from_usage({
            'prompt_tokens': 1000,
            'prompt_cache_hit_tokens': 200,
            'prompt_cache_miss_tokens': 800,
            'completion_tokens': 500,
        }, self.model)
        self.assertEqual('USD', cost['currency'])
        self.assertGreater(cost['estimated_cost'], 0)

    def test_budget_guard_allows_call_when_reservation_fits(self):
        upstream = ScriptedProvider([{'decision_summary': 'ok', 'actions': []}])
        wrapped = BudgetedProvider(upstream, self.model, spending_ceiling=1.0, currency='USD', max_calls=2)
        response = wrapped.complete_agent([{'role': 'user', 'content': 'short test'}], metadata={'run_id': 'x'})
        self.assertIn('content', response)
        self.assertEqual(1, wrapped.calls_completed)

    def test_budget_guard_rejects_tiny_ceiling_before_call(self):
        upstream = ScriptedProvider([{'decision_summary': 'must not run', 'actions': []}])
        wrapped = BudgetedProvider(upstream, self.model, spending_ceiling=0.000001, currency='USD', max_calls=2)
        with self.assertRaises(BudgetExceeded):
            wrapped.complete_agent([{'role': 'user', 'content': 'short test'}], metadata={'run_id': 'x'})
        self.assertEqual(0, wrapped.calls_started)
        self.assertEqual(0, upstream.index)

    def test_currency_mismatch_is_rejected(self):
        with self.assertRaises(ValueError):
            BudgetedProvider(ScriptedProvider([]), self.model, spending_ceiling=1.0, currency='CNY', max_calls=1)


if __name__ == '__main__':
    unittest.main()
