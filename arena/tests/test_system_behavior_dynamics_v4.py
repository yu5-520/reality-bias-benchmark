import unittest

from arena.engine import run_arena_once
from arena.io_utils import load_json
from arena.providers import ScriptedProvider
from arena.system_behavior import make_behavior_event
from arena.system_behavior_adapter import adapt_arena_trace_v03
from arena.system_behavior_dynamics_v4 import (
    build_system_dynamics_view,
    detect_structural_jump_candidates,
    load_v4_dynamics_configs,
    slice_behavior_events_for_branch,
)


class SystemBehaviorDynamicsV4Tests(unittest.TestCase):
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
            "system-behavior-dynamics-v4-test",
            19,
        )

    def test_configs_validate_and_bind_registered_boundaries(self):
        detector, operational, boundaries = load_v4_dynamics_configs()
        self.assertEqual(detector["schema"], "RB-STRUCTURAL-JUMP-DETECTOR-v0.1")
        self.assertEqual(operational["schema"], "RB-OPERATIONAL-BOUNDARY-SET-v0.1")
        registered = {row["boundary_id"] for row in boundaries["boundaries"]}
        self.assertIn("SHARED_STATE", registered)
        self.assertIn("FINAL_REOPEN", registered)

    def test_scripted_trace_yields_structural_candidates_without_semantic_promotion(self):
        adapted = adapt_arena_trace_v03(self._trace())
        view = build_system_dynamics_view(adapted)
        measurement = view["system_trajectory_measurement"]

        self.assertEqual(len(view["jump_candidates"]), 3)
        self.assertEqual(len(view["operational_crossings"]), 5)
        self.assertEqual(measurement["r2"]["jump_candidate_count"], 3)
        self.assertEqual(measurement["r2"]["first_jump_turn"], 1)
        self.assertEqual(measurement["r2"]["jump_truth_status"], "NOT_ADJUDICATED")
        self.assertEqual(measurement["r3"]["descendant_event_count"], 0)
        self.assertEqual(measurement["r3"]["affected_agent_count"], 0)
        self.assertEqual(measurement["r3"]["operational_boundary_crossing_count"], 5)
        self.assertEqual(measurement["r3"]["post_first_candidate_operational_crossing_count"], 4)
        self.assertEqual(measurement["r3"]["penetration_status"], "NOT_ADJUDICATED")
        self.assertEqual(measurement["r4"]["retrospective_window_count"], 1)
        self.assertEqual(measurement["r4"]["semantic_r_status"], "NOT_ADJUDICATED")
        self.assertEqual(view["scientific_status"], "OFFLINE_STRUCTURAL_MEASUREMENT_ONLY")

    def test_high_certainty_write_adds_candidate_type_but_not_c_label(self):
        event = make_behavior_event(
            behavior_event_id="high-cert:1",
            trajectory_id="high-cert-traj",
            event_index=1,
            turn=1,
            boundary_id="SHARED_STATE",
            actor="agent_a",
            action_type="write",
            realization_status="REALIZED",
            state_before_hash="before",
            state_after_hash="after",
            structured_diff={
                "behavior_phase": "REALIZATION",
                "action_status": "fact",
                "source_action_type": "write_state",
            },
        )
        candidates = detect_structural_jump_candidates([event])
        self.assertEqual(len(candidates), 1)
        self.assertEqual(
            set(candidates[0]["candidate_types"]),
            {
                "STATE_MUTATION_JUMP_CANDIDATE",
                "HIGH_CERTAINTY_STATE_WRITE_JUMP_CANDIDATE",
            },
        )
        self.assertEqual(candidates[0]["semantic_status"], "NOT_ADJUDICATED")
        self.assertEqual(candidates[0]["jump_truth_status"], "STRUCTURAL_CANDIDATE_ONLY")

    def test_branch_slice_excludes_parent_history_by_turn_boundary(self):
        events = [
            make_behavior_event(
                behavior_event_id=f"e:{turn}",
                trajectory_id="branch-traj",
                event_index=turn,
                turn=turn,
                boundary_id="AGENT_TURN",
                actor="agent_a",
                action_type="other",
                realization_status="REALIZED",
                state_before_hash=None,
                state_after_hash=None,
            )
            for turn in (1, 2, 3, 4)
        ]
        sliced = slice_behavior_events_for_branch(events, branch_start_turn=2)
        self.assertEqual([row["turn"] for row in sliced], [3, 4])


if __name__ == "__main__":
    unittest.main()
