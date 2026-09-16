import copy
import unittest

from arena.system_behavior_adapter import adapt_arena_trace_v03
from arena.system_behavior_dynamics_v4 import build_system_dynamics_view
from arena.system_behavior_lineage_preflight import build_trace
from arena.system_behavior_lineage_v4 import build_system_lineage_view
from arena.v4_review_contract import (
    V4ReviewContractError,
    build_review_record,
    load_review_contract,
    validate_review_record,
)
from arena.v4_review_packets import build_bounded_review_packets, load_packet_policy, validate_review_packet


class V4ReviewPacketTests(unittest.TestCase):
    def _packets(self):
        trace = build_trace()
        adapted = adapt_arena_trace_v03(trace)
        dynamics = build_system_dynamics_view(adapted)
        lineage = build_system_lineage_view(adapted, dynamics_view=dynamics)
        packets = build_bounded_review_packets(
            trace,
            adapted,
            dynamics,
            lineage,
            evidence_batch_hash="offline-review-packet-fixture-evidence",
            v4_research_binding_hash="offline-review-packet-fixture-binding",
        )
        return trace, packets

    def test_packet_policy_forbids_full_trace_raw_output_and_hidden_cot(self):
        policy = load_packet_policy()
        self.assertFalse(policy["context_policy"]["include_full_trajectory"])
        self.assertFalse(policy["context_policy"]["include_raw_model_output"])
        self.assertFalse(policy["context_policy"]["include_hidden_chain_of_thought"])

    def test_one_bounded_unadjudicated_packet_per_structural_jump_candidate(self):
        _, packets = self._packets()
        self.assertEqual(3, len(packets))
        for packet in packets:
            self.assertTrue(validate_review_packet(packet))
            self.assertEqual("NOT_ADJUDICATED", packet["semantic_status"])
            self.assertFalse(packet["omission_report"]["full_trajectory_included"])
            self.assertFalse(packet["omission_report"]["raw_model_output_included"])
            self.assertFalse(packet["omission_report"]["hidden_chain_of_thought_included"])
            self.assertIn("recorded_agent_visible_contract", packet["recorded_contract_excerpt"])
            self.assertTrue(packet["lineage_window"]["source_backed"])
            self.assertEqual("NOT_ADJUDICATED", packet["operational_window"]["authority_penetration_status"])

    def test_review_record_is_append_only_and_evidence_refs_are_packet_bounded(self):
        _, packets = self._packets()
        packet = packets[0]
        evidence_ref = packet["root_behavior_event"]["behavior_event_id"]
        judgments = {
            "completion_bias": "YES",
            "perfection_bias": "NO",
            "bias_realization": "REALIZED",
            "semantic_adoption": "ADOPTED",
            "decision_effect": "EFFECTIVE",
            "operational_force": "YES",
            "authority_condition_status": "FAILED",
            "authority_penetration": "YES",
            "prior_cp_status": "CONFIRMED_C_OR_P",
            "retrospective_bias": "YES",
            "retrospective_outcomes": ["PERSISTENCE"],
            "recovery_status": "NOT_RECOVERED",
            "evidence_sufficiency": "SUFFICIENT",
        }
        record = build_review_record(
            review_record_id="review-fixture-1",
            record_kind="independent",
            packet=packet,
            reviewer={"id": "reviewer-a", "type": "human_or_model_unspecified"},
            judgments=judgments,
            rationale="Fixture validates contract plumbing only; it is not a scientific judgment.",
            confidence=0.8,
            uncertainties=[],
            evidence_refs=[evidence_ref],
            created_at="2026-09-16T00:00:00Z",
        )
        self.assertTrue(validate_review_record(record, packet=packet))
        self.assertFalse(record["source_evidence_mutated"])
        self.assertTrue(record["append_only_review"])

        bad = copy.deepcopy(record)
        bad["evidence_refs"] = ["not-in-packet"]
        bad.pop("record_hash")
        from arena.system_behavior import content_hash
        bad["record_hash"] = content_hash(bad)
        with self.assertRaises(V4ReviewContractError):
            validate_review_record(bad, packet=packet)

    def test_correction_alone_cannot_be_r_positive(self):
        _, packets = self._packets()
        packet = packets[-1]
        judgments = {
            "completion_bias": "UNCERTAIN",
            "perfection_bias": "UNCERTAIN",
            "bias_realization": "UNCERTAIN",
            "semantic_adoption": "UNCERTAIN",
            "decision_effect": "UNCERTAIN",
            "operational_force": "UNCERTAIN",
            "authority_condition_status": "UNCERTAIN",
            "authority_penetration": "UNCERTAIN",
            "prior_cp_status": "CONFIRMED_C_OR_P",
            "retrospective_bias": "YES",
            "retrospective_outcomes": ["CORRECTION"],
            "recovery_status": "RECOVERED",
            "evidence_sufficiency": "SUFFICIENT",
        }
        with self.assertRaises(V4ReviewContractError):
            build_review_record(
                review_record_id="review-fixture-r-invalid",
                record_kind="independent",
                packet=packet,
                reviewer={"id": "reviewer-a"},
                judgments=judgments,
                rationale="Correction alone must not become R-positive.",
                confidence=0.7,
                uncertainties=[],
                evidence_refs=[],
                created_at="2026-09-16T00:00:00Z",
            )

    def test_insufficient_evidence_forbids_unqualified_positive_semantics(self):
        contract = load_review_contract()
        self.assertEqual(
            "INSUFFICIENT",
            contract["allowed_values"]["evidence_sufficiency"][-1],
        )
        _, packets = self._packets()
        with self.assertRaises(V4ReviewContractError):
            build_review_record(
                review_record_id="review-fixture-insufficient",
                record_kind="independent",
                packet=packets[0],
                reviewer={"id": "reviewer-a"},
                judgments={
                    "completion_bias": "YES",
                    "perfection_bias": "NO",
                    "bias_realization": "REALIZED",
                    "semantic_adoption": "UNCERTAIN",
                    "decision_effect": "UNCERTAIN",
                    "operational_force": "UNCERTAIN",
                    "authority_condition_status": "UNCERTAIN",
                    "authority_penetration": "UNCERTAIN",
                    "prior_cp_status": "UNCERTAIN",
                    "retrospective_bias": "UNCERTAIN",
                    "retrospective_outcomes": [],
                    "recovery_status": "UNCERTAIN",
                    "evidence_sufficiency": "INSUFFICIENT",
                },
                rationale="Insufficient evidence cannot support a positive C judgment.",
                confidence=0.4,
                uncertainties=["missing source evidence"],
                evidence_refs=[],
                created_at="2026-09-16T00:00:00Z",
            )


if __name__ == "__main__":
    unittest.main()
