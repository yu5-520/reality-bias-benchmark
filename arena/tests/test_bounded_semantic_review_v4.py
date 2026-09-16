import copy
import unittest

from arena.bounded_semantic_review_v4 import (
    build_bounded_review_packets,
    load_review_contract,
    normalize_review_output,
    verify_review_packet,
)
from arena.engine import run_arena_once
from arena.io_utils import load_json
from arena.providers import ScriptedProvider
from arena.system_behavior_adapter import adapt_arena_trace_v03
from arena.system_behavior_dynamics_v4 import build_system_dynamics_view
from arena.system_behavior_lineage_v4 import build_system_lineage_view


class BoundedSemanticReviewV4Tests(unittest.TestCase):
    def _fixture(self):
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
                        "status": "fact",
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
        trace = run_arena_once(
            domain,
            config,
            ScriptedProvider(scripted),
            "bounded-semantic-review-v4-test",
            41,
        )
        adapted = adapt_arena_trace_v03(trace)
        dynamics = build_system_dynamics_view(adapted)
        lineage = build_system_lineage_view(adapted, dynamics_view=dynamics)
        packets = build_bounded_review_packets(
            trace,
            adapted,
            dynamics,
            lineage,
            domain=domain,
        )
        return domain, trace, adapted, dynamics, lineage, packets

    def test_packets_are_bounded_and_semantically_unadjudicated(self):
        _, _, _, _, _, packets = self._fixture()
        self.assertTrue(packets)
        contract = load_review_contract()
        bounds = contract["packet_bounds"]
        for packet in packets:
            self.assertTrue(verify_review_packet(packet, contract))
            self.assertEqual(packet["review_status"], "PENDING_REVIEW")
            self.assertFalse(packet["source_context"]["hidden_chain_of_thought_included"])
            self.assertTrue(all(value == "NOT_ADJUDICATED" for value in packet["boundary_fields"].values()))
            self.assertLessEqual(len(packet["lineage_window"]["behavior_events"]), bounds["max_behavior_events"])
            self.assertLessEqual(len(packet["lineage_window"]["relations"]), bounds["max_lineage_relations"])
            self.assertLessEqual(len(packet["operational_window"]["mechanical_crossings"]), bounds["max_operational_crossings"])
            self.assertLessEqual(len(packet["source_context"]["source_model_calls"]), bounds["max_source_model_calls"])

    def test_packet_uses_exact_operational_crossing_records(self):
        _, _, _, dynamics, _, packets = self._fixture()
        crossings = {row["crossing_id"]: row for row in dynamics["operational_crossings"]}
        packet_crossings = [
            row
            for packet in packets
            for row in packet["operational_window"]["mechanical_crossings"]
        ]
        self.assertTrue(packet_crossings)
        for crossing in packet_crossings:
            self.assertIn(crossing["crossing_id"], crossings)
            self.assertEqual(crossing["crossing_hash"], crossings[crossing["crossing_id"]]["crossing_hash"])
            self.assertEqual(crossing["penetration_status"], "NOT_ADJUDICATED")

    def test_review_output_is_append_only_and_does_not_rewrite_packet(self):
        _, _, _, _, _, packets = self._fixture()
        packet = packets[0]
        before = copy.deepcopy(packet)
        output = {
            "review_status": "FINAL",
            "jump_semantic_class": "UNCERTAIN",
            "semantic_adoption": "UNCERTAIN",
            "decision_effect": "UNCERTAIN",
            "authority_penetration": "UNCERTAIN",
            "retrospective_outcome": "NOT_APPLICABLE",
            "evidence_sufficiency": "INSUFFICIENT",
            "confidence": 0.4,
            "rationale": "Engineering fixture only; no scientific semantic claim is made.",
            "evidence_refs": [packet["root_behavior_event"]["behavior_event_id"]],
            "uncertainties": ["fixture semantics are synthetic"],
        }
        record = normalize_review_output(
            packet,
            output,
            reviewer_id="offline-test-reviewer",
            review_round_id="offline-test-round-1",
        )
        self.assertEqual(record["review_status"], "FINAL")
        self.assertTrue(record["append_only"])
        self.assertTrue(record["source_evidence_unchanged"])
        self.assertEqual(packet, before)

    def test_invalid_semantic_enum_fails_closed(self):
        _, _, _, _, _, packets = self._fixture()
        packet = packets[0]
        output = {
            "review_status": "FINAL",
            "jump_semantic_class": "DEFINITELY_BIASED",
            "semantic_adoption": "UNCERTAIN",
            "decision_effect": "UNCERTAIN",
            "authority_penetration": "UNCERTAIN",
            "retrospective_outcome": "NOT_APPLICABLE",
            "evidence_sufficiency": "INSUFFICIENT",
            "confidence": 0.5,
            "rationale": "invalid enum test",
        }
        with self.assertRaises(ValueError):
            normalize_review_output(
                packet,
                output,
                reviewer_id="offline-test-reviewer",
                review_round_id="offline-test-round-invalid",
            )


if __name__ == "__main__":
    unittest.main()
