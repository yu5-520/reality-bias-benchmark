import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from arena.build_v5_cross_domain_manifest import build_rows, verify_manifest
from arena.build_v5_cross_domain_case_ledger import build_rows as build_case_rows
from arena.build_v5_cross_domain_first_round_registry import build_registry


class V5CrossDomainTest(unittest.TestCase):
    def test_manifest_freezes_four_domains_and_six_balanced_waves(self):
        rows = build_rows(code_sha="TEST-COMMIT")
        self.assertTrue(verify_manifest(rows))
        self.assertEqual(120, len(rows))
        self.assertEqual(
            {
                "ecommerce": 30,
                "finance": 30,
                "supply_chain": 30,
                "software_engineering": 30,
            },
            Counter(row["domain_id"] for row in rows),
        )
        self.assertEqual(
            {1: 20, 2: 20, 3: 20, 4: 20, 5: 20, 6: 20},
            Counter(row["wave_id"] for row in rows),
        )
        ecom_roles = {row["cohort_role"] for row in rows if row["domain_id"] == "ecommerce"}
        replication_roles = {
            row["cohort_role"]
            for row in rows
            if row["domain_id"] != "ecommerce"
        }
        self.assertEqual({"METHOD_DEVELOPMENT_REFERENCE_FRESH_REPLICATION"}, ecom_roles)
        self.assertEqual({"FROZEN_PROTOCOL_REPLICATION"}, replication_roles)
        self.assertTrue(all(row["automatic_paid_evaluator"] is False for row in rows))
        self.assertTrue(all(row["no_outcome_aware_rerun"] is True for row in rows))

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

    def test_registry_requires_six_waves_same_sha_and_plan(self):
        with tempfile.TemporaryDirectory() as td:
            paths = []
            for wave in range(1, 7):
                row = {
                    "first_round_id": "FR",
                    "selected_wave_id": wave,
                    "selected_run_count": 20,
                    "preserved_trace_count": 20,
                    "runner_error_count": 0,
                    "domain_trace_counts": {
                        "ecommerce": 5,
                        "finance": 5,
                        "supply_chain": 5,
                        "software_engineering": 5,
                    },
                    "code_commit_sha": "SHA",
                    "plan_hash": "PLAN",
                    "evidence_batch_hash": f"BATCH-{wave}",
                }
                path = Path(td) / f"wave-{wave}.json"
                path.write_text(json.dumps(row), encoding="utf-8")
                paths.append(str(path))
            out = build_registry(paths)
            self.assertEqual(120, out["planned_selected_run_count"])
            self.assertEqual(120, out["preserved_trace_count"])
            self.assertEqual(30, out["domain_trace_counts"]["finance"])
            self.assertTrue(out["same_execution_sha"])
            self.assertTrue(out["all_waves_present"])


if __name__ == "__main__":
    unittest.main()
