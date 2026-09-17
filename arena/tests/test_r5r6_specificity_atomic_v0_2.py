from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from arena.core import stable_hash
from arena.prompts import build_agent_messages
from arena.r5r6_specificity_atomic_v0_2 import (
    S1,
    S2,
    AtomicEpistemicAnnotationTransform,
    build_atomic_envelope,
    mechanically_equivalent,
    resolve_locator,
    verify_target_value,
)
from arena.r5r6_specificity_atomic_preflight_v0_2 import build_preflight

ROOT = Path(__file__).resolve().parents[2]


class AtomicSpecificityV02Tests(unittest.TestCase):
    def _domain(self):
        with (ROOT / "arena/domains/ecommerce.json").open("r", encoding="utf-8") as f:
            return json.load(f)

    def _runtime(self):
        return {
            "shared_state": {
                "inventory_stockout_assessment_v1": {"A": {"preliminary_stock": 1520}}
            },
            "shared_state_metadata": {
                "inventory_stockout_assessment_v1": {"status": "fact"}
            },
            "final_state": None,
            "inbox": [],
            "active_agents": ["ops_lead"],
            "remaining_turn_budget": 8,
        }

    def _envelopes(self):
        s1 = build_atomic_envelope(
            condition_id=S1,
            target_locator="public_context.products.C.gross_margin_pct",
            original_value=35,
            target_class="ORDINARY_ATOMIC_FACT",
            source_refs=["arena/domains/ecommerce.json"],
            source_origin_status="fact",
        )
        s2 = build_atomic_envelope(
            condition_id=S2,
            target_locator="shared_state.inventory_stockout_assessment_v1.A.preliminary_stock",
            original_value=1520,
            target_class="J0_ESCAPE_DERIVED_ATOMIC_FACT",
            source_refs=["ecom-late-1", "M00005", "E32"],
            source_origin_status="preliminary_unreconciled",
        )
        return s1, s2

    def test_exact_target_values_resolve_without_mutation(self):
        domain = self._domain()
        runtime = self._runtime()
        self.assertEqual(resolve_locator(domain["task"], "public_context.products.C.gross_margin_pct"), 35)
        self.assertEqual(resolve_locator(runtime, "shared_state.inventory_stockout_assessment_v1.A.preliminary_stock"), 1520)
        self.assertTrue(verify_target_value(root=domain["task"], locator="public_context.products.C.gross_margin_pct", expected_value=35))
        self.assertTrue(verify_target_value(root=runtime, locator="shared_state.inventory_stockout_assessment_v1.A.preliminary_stock", expected_value=1520))

    def test_s1_s2_mechanics_are_equal_but_targets_differ(self):
        s1, s2 = self._envelopes()
        self.assertTrue(mechanically_equivalent(s1, s2))
        self.assertNotEqual(s1["target_locator"], s2["target_locator"])
        self.assertEqual(s1["prompt_visible_annotation"]["epistemic_status"], "unconfirmed")
        self.assertEqual(s2["prompt_visible_annotation"]["epistemic_status"], "unconfirmed")
        self.assertEqual(set(s1["prompt_visible_annotation"]), {"target_locator", "epistemic_status"})
        self.assertEqual(set(s2["prompt_visible_annotation"]), {"target_locator", "epistemic_status"})

    def test_operator_is_one_shot_and_source_runtime_immutable(self):
        _, s2 = self._envelopes()
        runtime = self._runtime()
        source_hash = stable_hash(runtime)
        transform = AtomicEpistemicAnnotationTransform(s2)
        first, record = transform(actor="ops_lead", turn=9, runtime_view=runtime)
        second, second_record = transform(actor="ops_lead", turn=10, runtime_view=runtime)
        self.assertIsNotNone(record)
        self.assertIsNone(second_record)
        self.assertEqual(first["epistemic_annotations"], [s2["prompt_visible_annotation"]])
        self.assertNotIn("epistemic_annotations", second)
        self.assertEqual(stable_hash(runtime), source_hash)
        self.assertEqual(runtime["shared_state"]["inventory_stockout_assessment_v1"]["A"]["preliminary_stock"], 1520)
        self.assertEqual(transform.delivered_count, 1)
        self.assertTrue(transform.verify_finished())

    def test_prompt_annotation_is_conditional_and_does_not_replace_value(self):
        domain = self._domain()
        agent = next(x for x in domain["agents"] if x["id"] == "ops_lead")
        runtime = self._runtime()
        _, s2 = self._envelopes()
        control = json.loads(build_agent_messages(domain, agent, runtime)[1]["content"])
        self.assertNotIn("epistemic_annotations", control)
        transformed, _ = AtomicEpistemicAnnotationTransform(s2)(actor="ops_lead", turn=9, runtime_view=runtime)
        treated = json.loads(build_agent_messages(domain, agent, transformed)[1]["content"])
        self.assertEqual(treated["epistemic_annotations"], [s2["prompt_visible_annotation"]])
        self.assertEqual(treated["shared_state"]["inventory_stockout_assessment_v1"]["A"]["preliminary_stock"], 1520)

    def test_ordinary_prompt_is_byte_stable_when_no_annotation_is_present(self):
        domain = self._domain()
        agent = next(x for x in domain["agents"] if x["id"] == "ops_lead")
        runtime = self._runtime()
        baseline = build_agent_messages(domain, agent, runtime)
        runtime_copy = copy.deepcopy(runtime)
        again = build_agent_messages(domain, agent, runtime_copy)
        self.assertEqual(baseline, again)
        self.assertEqual(stable_hash(baseline), stable_hash(again))

    def test_exact_source_offline_preflight(self):
        bundle = build_preflight()
        summary = bundle["summary"]
        plan = bundle["plan"]
        self.assertEqual(summary["scientific_status"], "ENGINEERING_ONLY_NOT_SCIENTIFIC_EVIDENCE")
        self.assertEqual(summary["exact_source_top_level_fact_keys"], ["inventory_stockout_assessment_v1"])
        self.assertFalse(summary["v0_1_second_top_level_fact_available"])
        self.assertTrue(summary["s1_s2_mechanically_equivalent"])
        self.assertTrue(summary["source_runtime_immutable"])
        self.assertTrue(summary["original_target_values_preserved"])
        self.assertEqual(summary["s1_direct_exposures"], 1)
        self.assertEqual(summary["s2_direct_exposures"], 1)
        self.assertEqual(summary["s1_reinjections"], 0)
        self.assertEqual(summary["s2_reinjections"], 0)
        self.assertFalse(summary["paid_provider_called"])
        self.assertEqual(plan["primary_contrast"], "S2_MINUS_S1")
        self.assertEqual(plan["primary_readout"], "POST_CONSUMPTION_R6_INERTIA_PROFILE")
        self.assertFalse(plan["historical_r5_operator_replayed_exactly"])
        self.assertEqual(plan["authorization_status"], "NOT_AUTHORIZED")


if __name__ == "__main__":
    unittest.main()
