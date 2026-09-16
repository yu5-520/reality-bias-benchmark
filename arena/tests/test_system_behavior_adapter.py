import copy
import unittest

from arena.engine import run_arena_once
from arena.io_utils import load_json
from arena.providers import ScriptedProvider
from arena.system_behavior_adapter import (
    SystemBehaviorAdapterError,
    adapt_arena_trace_v03,
)


class SystemBehaviorAdapterTests(unittest.TestCase):
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
            "system-behavior-adapter-test",
            7,
        )

    def test_adapter_preserves_source_trace_and_separates_proposal_realization(self):
        trace = self._trace()
        frozen = copy.deepcopy(trace)
        result = adapt_arena_trace_v03(trace)
        self.assertEqual(trace, frozen)

        events = result["behavior_events"]
        phases = {row.get("behavior_phase") for row in events}
        self.assertIn("PROPOSAL", phases)
        self.assertIn("REALIZATION", phases)
        self.assertIn("READ", phases)
        self.assertIn("NODE_EXECUTION", phases)

        write_rows = [
            row
            for row in events
            if row["boundary_id"] == "SHARED_STATE"
            and row["structured_diff"].get("source_action_type") == "write_state"
        ]
        self.assertEqual({row["realization_status"] for row in write_rows}, {"PROPOSAL", "REALIZED"})
        realized_write = next(row for row in write_rows if row["realization_status"] == "REALIZED")
        self.assertNotEqual(realized_write["state_before_hash"], realized_write["state_after_hash"])

        invocation_rows = [row for row in events if row["boundary_id"] == "INVOCATION"]
        self.assertTrue(invocation_rows)
        self.assertTrue(any(row["action_type"] == "read" for row in invocation_rows))

        message_reads = [
            row
            for row in events
            if row["boundary_id"] == "MESSAGE_HANDOFF" and row["action_type"] == "read"
        ]
        self.assertTrue(message_reads)

    def test_adapter_builds_synchronized_v4_measurement_without_semantic_overclaim(self):
        result = adapt_arena_trace_v03(self._trace())
        measurement = result["system_trajectory_measurement"]
        self.assertEqual(measurement["semantic_status"], "NOT_ADJUDICATED")
        self.assertEqual(measurement["r2"]["jump_candidate_count"], 0)
        self.assertEqual(
            measurement["r2"]["jump_detection_status"],
            "NOT_RUN_DETECTOR_NOT_FROZEN",
        )
        self.assertEqual(
            measurement["r3"]["lineage_status"],
            "STRUCTURAL_BEHAVIOR_INDEX_AVAILABLE_JUMP_ANCHOR_NOT_FROZEN",
        )
        self.assertEqual(
            measurement["r4"]["retrospective_detection_status"],
            "NOT_RUN_JUMP_ANCHOR_NOT_FROZEN",
        )
        self.assertEqual(
            measurement["behavior_event_count"],
            len(result["behavior_events"]),
        )
        self.assertEqual(result["summary"]["unsupported_source_actions"], [])

    def test_adapter_fails_closed_on_unregistered_source_trace_schema(self):
        trace = self._trace()
        trace["trace_schema_version"] = "R2-ARENA-TRACE-v9.9"
        with self.assertRaises(SystemBehaviorAdapterError):
            adapt_arena_trace_v03(trace)


if __name__ == "__main__":
    unittest.main()
