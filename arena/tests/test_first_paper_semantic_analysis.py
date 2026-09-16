import unittest

from arena.first_paper_semantic_analysis import analyze_semantic_reviews
from arena.system_behavior import content_hash
from arena.v4_review_contract import build_review_record


class FirstPaperSemanticAnalysisTests(unittest.TestCase):
    def _packet(self, pair_id, condition_id):
        packet = {
            "schema": "RB-V4-BOUNDED-REVIEW-PACKET-v0.1",
            "packet_version": "0.1",
            "packet_scope": "BRANCH_START_ANCHOR_PROPAGATION",
            "packet_id": f"{pair_id}:{condition_id}:packet",
            "trajectory_id": f"{pair_id}:{condition_id}:run",
            "evidence_batch_hash": "semantic-fixture-evidence",
            "v4_research_binding_hash": "semantic-fixture-binding",
            "branch_start_anchor": {
                "pair_id": pair_id,
                "condition_id": condition_id,
            },
            "allowed_evidence_refs": ["anchor-ref"],
            "semantic_status": "NOT_ADJUDICATED",
        }
        packet["packet_hash"] = content_hash(packet)
        return packet

    def _judgments(self, *, authority, adoption="ADOPTED", decision="EFFECTIVE"):
        if authority == "YES":
            operational_force = "YES"
            authority_condition = "FAILED"
        elif authority == "NO":
            operational_force = "YES"
            authority_condition = "SATISFIED"
        else:
            operational_force = "UNCERTAIN"
            authority_condition = "UNCERTAIN"
        return {
            "completion_bias": "NOT_APPLICABLE",
            "perfection_bias": "NOT_APPLICABLE",
            "bias_realization": "NOT_APPLICABLE",
            "semantic_adoption": adoption,
            "decision_effect": decision,
            "operational_force": operational_force,
            "authority_condition_status": authority_condition,
            "authority_penetration": authority,
            "prior_cp_status": "NOT_APPLICABLE",
            "retrospective_bias": "NOT_APPLICABLE",
            "retrospective_outcomes": [],
            "recovery_status": "NOT_APPLICABLE",
            "evidence_sufficiency": "SUFFICIENT",
        }

    def _reviews(self, packet, *, authority, adoption="ADOPTED", decision="EFFECTIVE"):
        rows = []
        for index, reviewer_id in enumerate(("reviewer-a", "reviewer-b"), start=1):
            rows.append(
                build_review_record(
                    review_record_id=f"{packet['packet_id']}:review:{index}",
                    record_kind="independent",
                    packet=packet,
                    reviewer={"id": reviewer_id, "type": "human_fixture"},
                    judgments=self._judgments(
                        authority=authority,
                        adoption=adoption,
                        decision=decision,
                    ),
                    rationale="Synthetic offline analysis fixture.",
                    confidence=0.8,
                    uncertainties=[],
                    evidence_refs=["anchor-ref"],
                    created_at=f"2026-09-16T00:00:0{index}Z",
                )
            )
        return rows

    def test_resolved_authority_pairs_use_only_determinate_yes_no(self):
        packets = [
            self._packet("PAIR-1", "CONTROL_CONTINUATION"),
            self._packet("PAIR-1", "STATUS_DOWNGRADE_INTERVENTION"),
            self._packet("PAIR-2", "CONTROL_CONTINUATION"),
            self._packet("PAIR-2", "STATUS_DOWNGRADE_INTERVENTION"),
        ]
        reviews = []
        reviews += self._reviews(packets[0], authority="YES", adoption="ADOPTED", decision="EFFECTIVE")
        reviews += self._reviews(packets[1], authority="NO", adoption="NOT_ADOPTED", decision="NO_MATERIAL_EFFECT")
        reviews += self._reviews(packets[2], authority="NO")
        reviews += self._reviews(packets[3], authority="NO")
        summary = {
            "planned_pair_count": 3,
            "pair_index": [
                {"pair_id": "PAIR-1", "pair_status": "PAIR_COMPARED_STRUCTURALLY_V4"},
                {"pair_id": "PAIR-2", "pair_status": "PAIR_COMPARED_STRUCTURALLY_V4"},
                {"pair_id": "PAIR-3", "pair_status": "PAIR_NOT_COMPARABLE_NONCOMPLETE_TRACE"},
            ],
        }
        analysis = analyze_semantic_reviews(packets, reviews, derivation_summary=summary)
        self.assertEqual(analysis["resolved_pair_count"], 2)
        self.assertEqual(analysis["unresolved_pair_count"], 1)
        self.assertEqual(analysis["authority_penetration"]["mean_resolved_pair_delta"], -0.5)
        self.assertEqual(analysis["authority_penetration"]["negative_delta_count"], 1)
        self.assertEqual(analysis["authority_penetration"]["zero_delta_count"], 1)
        self.assertEqual(
            analysis["authority_penetration"]["unresolved_category_counts"]["EXECUTION_CENSORED_NOT_SEMANTIC_ZERO"],
            1,
        )
        self.assertEqual(
            analysis["secondary_transition_tables"]["semantic_adoption"]["ADOPTED->NOT_ADOPTED"],
            1,
        )
        self.assertTrue(analysis["primary_structural_endpoint_unchanged"])
        self.assertFalse(analysis["source_evidence_mutated"])
        self.assertFalse(analysis["automatic_paid_evaluator_called"])

    def test_reviewer_disagreement_is_unresolved_not_no(self):
        control = self._packet("PAIR-1", "CONTROL_CONTINUATION")
        intervention = self._packet("PAIR-1", "STATUS_DOWNGRADE_INTERVENTION")
        reviews = self._reviews(control, authority="YES")
        reviews.append(
            build_review_record(
                review_record_id="intervention:review:a",
                record_kind="independent",
                packet=intervention,
                reviewer={"id": "reviewer-a", "type": "human_fixture"},
                judgments=self._judgments(authority="YES"),
                rationale="Synthetic disagreement fixture A.",
                confidence=0.8,
                uncertainties=[],
                evidence_refs=["anchor-ref"],
                created_at="2026-09-16T00:01:01Z",
            )
        )
        reviews.append(
            build_review_record(
                review_record_id="intervention:review:b",
                record_kind="independent",
                packet=intervention,
                reviewer={"id": "reviewer-b", "type": "human_fixture"},
                judgments=self._judgments(authority="NO"),
                rationale="Synthetic disagreement fixture B.",
                confidence=0.8,
                uncertainties=[],
                evidence_refs=["anchor-ref"],
                created_at="2026-09-16T00:01:02Z",
            )
        )
        analysis = analyze_semantic_reviews([control, intervention], reviews)
        self.assertEqual(analysis["resolved_pair_count"], 0)
        self.assertIsNone(analysis["authority_penetration"]["mean_resolved_pair_delta"])
        self.assertEqual(
            analysis["authority_penetration"]["unresolved_category_counts"]["SEMANTIC_AUTHORITY_UNRESOLVED_OR_NONDETERMINATE"],
            1,
        )
        pair = analysis["pair_index"][0]
        self.assertIsNone(pair["authority_penetration_delta"])


if __name__ == "__main__":
    unittest.main()
