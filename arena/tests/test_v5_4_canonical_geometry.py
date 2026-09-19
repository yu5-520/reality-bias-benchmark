from __future__ import annotations

import json
import unittest
from pathlib import Path

from arena.core import stable_hash
from arena.prepare_r7_dual_intervention_plan import verify_r7_dual_plan


ROOT=Path(__file__).resolve().parents[2]


class CanonicalGeometryTests(unittest.TestCase):
    def test_machine_contract_geometry(self):
        p=json.loads((ROOT/"configs/process_reality_canonical_experiment_geometry_v1.0.json").read_text())
        self.assertEqual(p["r5"]["new_control_branches_per_case"],0)
        self.assertEqual(p["r5"]["new_intervention_branches_per_case"],1)
        self.assertEqual(p["r5"]["canonical_replicate_count"],1)
        self.assertFalse(p["r5"]["natural_reference_must_be_rerun"])
        self.assertEqual(p["r6"]["new_subject_provider_branches_per_case"],0)
        self.assertEqual(
            p["r7"]["canonical_arms"],
            ["R7_P_PERSISTENT_SEMANTIC","R7_S_STRUCTURED_LINEAGE_REPAIR"],
        )
        self.assertEqual(p["r7"]["new_c1_one_shot_branches_per_case"],0)
        self.assertEqual(p["r7"]["new_provider_branches_per_case"],2)
        self.assertEqual(p["full_case_to_r7_new_provider_trajectory_count"],3)

    def test_reclassification_is_append_only(self):
        p=json.loads((ROOT/"manifests/v5_4_r5_r7_canonical_reclassification_2026-09-19_v0_1.json").read_text())
        self.assertFalse(p["historical_evidence_mutated"])
        self.assertFalse(p["frozen_evidence_mutated"])
        self.assertFalse(p["r5"]["forward_canonical_rule"]["selection_is_outcome_aware"])
        self.assertEqual(p["r5"]["canonical_r5_intervention_count_first_two_waves"],11)
        self.assertEqual(p["r7"]["forward_new_branch_count_per_case"],2)

    def test_dual_plan_verifier_rejects_c1_or_replicates(self):
        plan={
            "schema":"RB-R7-DUAL-INTERVENTION-EXECUTION-PLAN-v0.1",
            "canonical_arm_ids":["R7_P_PERSISTENT_SEMANTIC","R7_S_STRUCTURED_LINEAGE_REPAIR"],
            "canonical_replicate_count":1,
            "branch_count":2,
            "branch_row_count":2,
            "new_provider_branch_count":2,
            "r5_c1_reference_execution_count":0,
            "r5_reference_role":"FROZEN_R5_I_REFERENCE_NOT_RERUN",
            "paid_subject_authorization_status":"NOT_AUTHORIZED",
            "semantic_cpr_status":"NOT_ADJUDICATED",
        }
        plan["plan_hash"]=stable_hash(plan)
        rows=[
            {"arm_id":"C2_PERSISTENT_FIELD","canonical_arm_id":"R7_P_PERSISTENT_SEMANTIC","replicate_index":1},
            {"arm_id":"C3_ALR","canonical_arm_id":"R7_S_STRUCTURED_LINEAGE_REPAIR","replicate_index":1},
        ]
        bundle={"plan":plan,"execution_rows":rows,"arm_manifests":[{},{}]}
        self.assertTrue(verify_r7_dual_plan(bundle))

        bad=json.loads(json.dumps(bundle))
        bad["execution_rows"][0]["replicate_index"]=2
        with self.assertRaises(ValueError):
            verify_r7_dual_plan(bad)


if __name__=="__main__":
    unittest.main()
