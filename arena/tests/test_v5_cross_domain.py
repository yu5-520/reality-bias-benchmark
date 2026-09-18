import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from arena.build_v5_cross_domain_manifest import build_rows, verify_manifest
from arena.build_v5_cross_domain_case_ledger import build_rows as build_case_rows
from arena.build_v5_cross_domain_first_round_registry import build_registry


class V5CrossDomainTest(unittest.TestCase):
    def test_manifest_freezes_three_held_out_domains_and_six_domain_pure_waves(self):
        rows = build_rows(code_sha="TEST-COMMIT")
        self.assertTrue(verify_manifest(rows))
        self.assertEqual(90, len(rows))
        self.assertEqual(
            {
                "finance": 30,
                "supply_chain": 30,
                "software_engineering": 30,
            },
            Counter(row["domain_id"] for row in rows),
        )
        self.assertNotIn("ecommerce", Counter(row["domain_id"] for row in rows))
        self.assertEqual(
            {1:15, 2:15, 3:15, 4:15, 5:15, 6:15},
            Counter(row["wave_id"] for row in rows),
        )
        expected_wave_domain = {
            1:"finance", 2:"finance",
            3:"supply_chain", 4:"supply_chain",
            5:"software_engineering", 6:"software_engineering",
        }
        for wave_id, domain_id in expected_wave_domain.items():
            group=[row for row in rows if row["wave_id"] == wave_id]
            self.assertEqual({domain_id}, {row["domain_id"] for row in group})
            self.assertEqual(15, len(group))
        self.assertEqual(
            {"FROZEN_PROTOCOL_REPLICATION"},
            {row["cohort_role"] for row in rows},
        )
        self.assertTrue(all(row["automatic_paid_evaluator"] is False for row in rows))
        self.assertTrue(all(row["no_outcome_aware_rerun"] is True for row in rows))

    def test_domain_has_two_preregistered_waves_of_15(self):
        rows = build_rows(code_sha="TEST-COMMIT")
        for domain_id in ("finance","supply_chain","software_engineering"):
            group=[row for row in rows if row["domain_id"] == domain_id]
            self.assertEqual(30, len(group))
            self.assertEqual({1,2}, {row["domain_wave_id"] for row in group})
            self.assertEqual(15, sum(row["domain_wave_id"] == 1 for row in group))
            self.assertEqual(15, sum(row["domain_wave_id"] == 2 for row in group))

    def test_case_ledger_does_not_auto_authorize_structural_candidate(self):
        rows = build_case_rows(
            [{
                "trajectory_id": "run-1",
                "domain_id": "finance",
                "engineering_core": {"repair_anchor_candidate_refs": ["arena_event:4:state:x"]},
                "candidates": [{
                    "candidate_ref": "arena_event:4:state:x",
                    "content_address": "abc",
                }],
            }],
            first_round_id="FR",
        )
        self.assertEqual(1, len(rows))
        self.assertEqual("AWAITING_LOCALIZED_SEMANTIC_AUDIT", rows[0]["qualification_status"])
        self.assertFalse(rows[0]["r5_probe_authorized"])
        self.assertFalse(rows[0]["r7_repair_authorized"])

    def test_no_candidate_is_valid_result_not_forced_target(self):
        rows = build_case_rows(
            [{
                "trajectory_id": "run-2",
                "domain_id": "software_engineering",
                "engineering_core": {"repair_anchor_candidate_refs": []},
                "candidates": [],
            }],
            first_round_id="FR",
        )
        self.assertEqual("NO_QUALIFYING_NATURAL_STRUCTURE", rows[0]["qualification_status"])
        self.assertIsNone(rows[0]["candidate_ref"])

    def test_registry_requires_six_domain_pure_waves_same_sha_plan_and_authorization(self):
        expected_wave_domain = {
            1:"finance", 2:"finance",
            3:"supply_chain", 4:"supply_chain",
            5:"software_engineering", 6:"software_engineering",
        }
        expected_wave_key = {
            1:"finance-w1", 2:"finance-w2",
            3:"supply_chain-w1", 4:"supply_chain-w2",
            5:"software_engineering-w1", 6:"software_engineering-w2",
        }
        with tempfile.TemporaryDirectory() as td:
            paths = []
            for wave in range(1, 7):
                domain_id=expected_wave_domain[wave]
                row = {
                    "first_round_id": "FR",
                    "authorization_event_id": "AUTH-ONE",
                    "selected_wave_id": wave,
                    "selected_wave_key": expected_wave_key[wave],
                    "selected_domain_id": domain_id,
                    "selected_run_count": 15,
                    "preserved_trace_count": 15,
                    "runner_error_count": 0,
                    "domain_trace_counts": {domain_id:15},
                    "code_commit_sha": "SHA",
                    "plan_hash": "PLAN",
                    "evidence_batch_hash": f"BATCH-{wave}",
                }
                path = Path(td) / f"wave-{wave}.json"
                path.write_text(json.dumps(row), encoding="utf-8")
                paths.append(str(path))
            out = build_registry(paths)
            self.assertEqual(90, out["planned_selected_run_count"])
            self.assertEqual(90, out["preserved_trace_count"])
            self.assertEqual(30, out["domain_trace_counts"]["finance"])
            self.assertEqual(30, out["domain_trace_counts"]["supply_chain"])
            self.assertEqual(30, out["domain_trace_counts"]["software_engineering"])
            self.assertTrue(out["same_execution_sha"])
            self.assertTrue(out["same_authorization_event"])
            self.assertTrue(out["all_waves_present"])


if __name__ == "__main__":
    unittest.main()
