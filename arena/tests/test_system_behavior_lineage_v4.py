import unittest

from arena.engine import run_arena_once
from arena.io_utils import load_json
from arena.providers import ScriptedProvider
from arena.system_behavior_adapter import adapt_arena_trace_v03
from arena.system_behavior_dynamics_v4 import build_system_dynamics_view
from arena.system_behavior_lineage_v4 import build_system_lineage_view, load_lineage_rules


class SystemBehaviorLineageV4Tests(unittest.TestCase):
    def _trace(self):
        domain = load_json("arena/domains/ecommerce.json")
        config = load_json("arena/config/arena_v0.3.json")
        scripted = [
            {
                "decision_summary": "ask inventory",
                "actions": [
                    {
                        "type": "invoke_agent",
                        "agent_id": "inventory",
                        "request": "Check stock and replenishment risk.",
                    }
                ],
            },
            {
                "decision_summary": "share inventory",
                "actions": [
                    {
                        "type": "write_state",
                        "key": "inventory_view",
                        "value": "A stock risk elevated",
                        "basis": "supplier lead time and stock",
                        "status": "recommendation",
                    },
                    {
                        "type": "message",
                        "to": "ops_lead",
                        "content": "A has the tightest stock coverage.",
                    },
                ],
            },
            {
                "decision_summary": "finalize first plan",
                "actions": [{"type": "finalize", "answer": "Initial promotion plan."}],
            },
            {
                "decision_summary": "respond to late signal",
                "actions": [
                    {
                        "type": "revise_final_state",
                        "patch": {"inventory_view": "A stock risk critical"},
                        "reason": "new preliminary inventory signal",
                    },
                    {"type": "finalize", "answer": "Updated promotion plan."},
                ],
            },
        ]
        return run_arena_once(
            domain,
            config,
            ScriptedProvider(scripted),
            "system-behavior-lineage-v4-test",
            29,
        )

    def test_lineage_rules_are_frozen_and_source_backed(self):
        rules = load_lineage_rules()
        self.assertEqual(rules["schema"], "RB-SOURCE-LINEAGE-RULES-v0.1")
        self.assertEqual(rules["scientific_scope"], "SOURCE_BACKED_STRUCTURAL_LINEAGE_ONLY")
        relation_types = {row["relation_type"] for row in rules["relations"]}
        self.assertIn("PROPOSAL_TO_REALIZATION", relation_types)
        self.assertIn("STATE_MUTATION_TO_AGENT_TURN_VISIBILITY", relation_types)
        self.assertIn("FINAL_STATE_VERSION_TO_REVISION", relation_types)

    def test_lineage_view_derives_exact_relations_and_keeps_semantics_open(self):
        adapted = adapt_arena_trace_v03(self._trace())
        dynamics = build_system_dynamics_view(adapted)
        lineage = build_system_lineage_view(adapted, dynamics_view=dynamics)
        relation_types = set(lineage["lineage_relation_type_counts"])

        self.assertIn("AGENT_TURN_TO_ACTION_PROPOSAL", relation_types)
        self.assertIn("PROPOSAL_TO_REALIZATION", relation_types)
        self.assertIn("INVOCATION_REALIZATION_TO_INVOCATION_READ", relation_types)
        self.assertIn("MESSAGE_READ_TO_AGENT_TURN", relation_types)
        self.assertIn("STATE_MUTATION_TO_AGENT_TURN_VISIBILITY", relation_types)
        self.assertIn("FINAL_STATE_VERSION_TO_REVISION", relation_types)

        measurement = lineage["system_trajectory_measurement"]
        self.assertEqual(measurement["r3"]["lineage_status"], "SOURCE_BACKED_STRUCTURAL_LINEAGE_v0.1")
        self.assertGreater(measurement["r3"]["descendant_event_count"], 0)
        self.assertGreater(measurement["r3"]["affected_agent_count"], 0)
        self.assertGreater(
            measurement["r3"]["first_jump_mechanical_penetration_depth_candidate"],
            0,
        )
        self.assertEqual(measurement["r3"]["penetration_status"], "NOT_ADJUDICATED")
        self.assertEqual(lineage["semantic_status"], "NOT_ADJUDICATED")

    def test_shared_state_visibility_uses_exact_runtime_snapshot_origin(self):
        adapted = adapt_arena_trace_v03(self._trace())
        lineage = build_system_lineage_view(adapted)
        visibility = [
            row
            for row in lineage["lineage_relations"]
            if row["relation_type"] == "STATE_MUTATION_TO_AGENT_TURN_VISIBILITY"
        ]
        self.assertTrue(visibility)
        self.assertTrue(any("inventory_view" in row["evidence_detail"].get("visible_keys", []) for row in visibility))
        self.assertTrue(all(row["strength"] == "EXACT_RUNTIME_SNAPSHOT_ORIGIN" for row in visibility))

    def test_branch_slice_does_not_reintroduce_parent_history(self):
        adapted = adapt_arena_trace_v03(self._trace())
        dynamics = build_system_dynamics_view(adapted, branch_start_turn=1)
        lineage = build_system_lineage_view(adapted, dynamics_view=dynamics)
        self.assertEqual(lineage["behavior_slice"]["mode"], "BRANCH_CONTINUATION_ONLY")
        self.assertTrue(
            all(
                row["source_turn"] > 1 and row["target_turn"] > 1
                for row in lineage["lineage_relations"]
            )
        )


if __name__ == "__main__":
    unittest.main()
