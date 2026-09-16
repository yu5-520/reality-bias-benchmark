import json
import tempfile
import unittest
from pathlib import Path

from arena.io_utils import load_jsonl
from arena.system_behavior_adapter import adapt_arena_trace_v03
from arena.system_behavior_dynamics_v4 import build_system_dynamics_view
from arena.system_behavior_lineage_preflight import build_trace
from arena.system_behavior_lineage_v4 import build_system_lineage_view
from arena.v4_review_contract import build_review_record
from arena.v4_review_ledger import V4ReviewLedgerError, append_review_records
from arena.v4_review_packets import build_bounded_review_packets


class V4ReviewLedgerTests(unittest.TestCase):
    def _packet(self):
        trace = build_trace()
        adapted = adapt_arena_trace_v03(trace)
        dynamics = build_system_dynamics_view(adapted)
        lineage = build_system_lineage_view(adapted, dynamics_view=dynamics)
        return build_bounded_review_packets(
            trace,
            adapted,
            dynamics,
            lineage,
            evidence_batch_hash="ledger-fixture-evidence",
            v4_research_binding_hash="ledger-fixture-binding",
        )[0]

    def _record(self, packet, review_id, reviewer_id):
        return build_review_record(
            review_record_id=review_id,
            record_kind="independent",
            packet=packet,
            reviewer={"id": reviewer_id},
            judgments={
                "completion_bias": "UNCERTAIN",
                "perfection_bias": "UNCERTAIN",
                "bias_realization": "UNCERTAIN",
                "semantic_adoption": "UNCERTAIN",
                "decision_effect": "UNCERTAIN",
                "operational_force": "UNCERTAIN",
                "authority_condition_status": "UNCERTAIN",
                "authority_penetration": "UNCERTAIN",
                "prior_cp_status": "UNCERTAIN",
                "retrospective_bias": "UNCERTAIN",
                "retrospective_outcomes": [],
                "recovery_status": "UNCERTAIN",
                "evidence_sufficiency": "PARTIAL",
            },
            rationale="Ledger plumbing fixture only.",
            confidence=0.5,
            uncertainties=["fixture"],
            evidence_refs=[],
            created_at="2026-09-16T00:00:00Z",
        )

    def test_independent_reviews_append_without_overwriting_disagreement_space(self):
        packet = self._packet()
        r1 = self._record(packet, "review-1", "reviewer-a")
        r2 = self._record(packet, "review-2", "reviewer-b")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packets = root / "packets.jsonl"
            reviews1 = root / "reviews1.jsonl"
            reviews2 = root / "reviews2.jsonl"
            ledger = root / "ledger.jsonl"
            packets.write_text(json.dumps(packet, ensure_ascii=False) + "\n", encoding="utf-8")
            reviews1.write_text(json.dumps(r1, ensure_ascii=False) + "\n", encoding="utf-8")
            reviews2.write_text(json.dumps(r2, ensure_ascii=False) + "\n", encoding="utf-8")

            first = append_review_records(
                packets_path=packets,
                reviews_path=reviews1,
                ledger_path=ledger,
            )
            second = append_review_records(
                packets_path=packets,
                reviews_path=reviews2,
                ledger_path=ledger,
            )
            rows = load_jsonl(ledger)
            self.assertEqual(1, first["ledger_record_count_after"])
            self.assertEqual(2, second["ledger_record_count_after"])
            self.assertEqual(["review-1", "review-2"], [row["review_record_id"] for row in rows])
            self.assertTrue(second["review_disagreement_preserved"])
            self.assertFalse(second["source_evidence_mutated"])

    def test_duplicate_review_record_id_is_rejected_without_ledger_growth(self):
        packet = self._packet()
        record = self._record(packet, "review-duplicate", "reviewer-a")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packets = root / "packets.jsonl"
            reviews = root / "reviews.jsonl"
            ledger = root / "ledger.jsonl"
            packets.write_text(json.dumps(packet, ensure_ascii=False) + "\n", encoding="utf-8")
            reviews.write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")
            append_review_records(packets_path=packets, reviews_path=reviews, ledger_path=ledger)
            before = ledger.read_bytes()
            with self.assertRaises(V4ReviewLedgerError):
                append_review_records(packets_path=packets, reviews_path=reviews, ledger_path=ledger)
            self.assertEqual(before, ledger.read_bytes())


if __name__ == "__main__":
    unittest.main()
