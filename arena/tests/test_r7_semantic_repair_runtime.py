import copy
import unittest

from arena.core import stable_hash
from arena.r7_semantic_repair_runtime import (
    build_repaired_parent_snapshot,
    build_semantic_repair_runtime_plan,
    verify_semantic_repair_trace,
)


def snapshot(*, turns, target_status, state_hash_name, queue):
    row = {
        "schema": "RB-EXPERIMENTAL-STATE-SNAPSHOT-v0.1",
        "run_id": "fixture-run",
        "domain_id": "ecommerce",
        "anchor_ref": state_hash_name,
        "parent_trace_hash": "TRACE",
        "turns": turns,
        "shared_state": {
            "inventory_stockout_assessment_v1": {"A": {"preliminary_stock": 1520}},
            "unrelated_finance_state": {"budget": 100},
        },
        "shared_state_metadata": {
            "inventory_stockout_assessment_v1": {
                "status": target_status,
                "basis": "fixture",
                "writer": "inventory",
                "event_index": 32 if turns >= 8 else 10,
            },
            "unrelated_finance_state": {"status": "fact", "writer": "finance"},
        },
        "final_state": None,
        "active_agents": ["inventory", "ops_lead"],
        "inboxes": {"inventory": [], "ops_lead": [], "ads": [], "finance": []},
        "queue": list(queue),
        "events": [{"event_index": i} for i in range(35 if turns >= 8 else 32)],
        "total_invocations": 0,
        "late_event_delivered": False,
        "late_event_consumed": False,
        "terminated": False,
        "termination_reason": None,
        "last_finalizer": None,
        "failures": [],
        "budget_hits": [],
        "message_ledger": [],
        "invocation_ledger": [],
        "execution_ledger": [],
        "message_seq": 0,
        "invocation_seq": 0,
        "last_read_message_ids": [],
        "last_read_invocation_ids": [],
        "replay_scope": "deterministic_arena_state_only",
        "provider_internal_state_captured": False,
    }
    row["state_hash"] = stable_hash({k: v for k, v in row.items() if k != "state_hash"})
    return row


def fixture_bundle():
    packet = {
        "schema": "RB-SEMANTIC-REPAIR-PACKET-v0.1",
        "packet_id": "P1",
        "packet_hash": "PACKET_HASH",
        "repair_anchor_ref": "arena_event:32:state:inventory_stockout_assessment_v1",
        "target_semantic_id": "inventory_stockout_assessment_v1::A.preliminary_stock=1520",
        "content_address": "rbca:test",
        "lineage_completeness_gate_ref": "G1",
        "repair_closure_refs": [
            "arena_event:32:state:inventory_stockout_assessment_v1:status",
            "r6:s2:stable_shared_pool",
            "r6:s2:stock_risk_cap_fallback_descendants",
        ],
        "evidence_supported_affected_closure_refs": [
            "arena_event:32:state:inventory_stockout_assessment_v1",
            "r6:s2:stable_shared_pool",
            "r6:s2:stock_risk_cap_fallback_descendants",
        ],
        "mechanically_required_replay_refs": ["r7:post_j0_parent", "r7:downstream_queue"],
        "preserved_unrelated_refs": [],
        "allowed_repair_operations": [
            "AUTHORITY_DOWNGRADE",
            "POOL_INVALIDATION",
            "DESCENDANT_INVALIDATION",
            "SELECTIVE_RECOMPUTE",
            "DEPENDENT_DECISION_REOPEN",
        ],
        "repair_authorization_status": "READY_FOR_SEPARATE_AUTHORIZATION",
    }
    gate = {
        "schema": "RB-LINEAGE-COMPLETENESS-GATE-v0.1",
        "gate_id": "G1",
        "gate_hash": "GATE_HASH",
        "status": "COMPLETE_FOR_AUTHORIZED_REPAIR",
    }
    parent = snapshot(turns=8, target_status="fact", state_hash_name="after_turn:8", queue=["ops_lead"])
    checkpoint = snapshot(turns=7, target_status="preliminary", state_hash_name="before_turn:8", queue=["inventory"])
    bundle = {
        "semantic_repair_packet": packet,
        "lineage_completeness_gate": gate,
        "c3_recovery_checkpoint": checkpoint,
        "source_parent_snapshot": parent,
        "c3_alr_binding": {
            "state_key": "inventory_stockout_assessment_v1",
            "from_status": "fact",
            "to_status": "unconfirmed",
            "common_reference_parent_state_hash": parent["state_hash"],
            "recovery_checkpoint_state_hash": checkpoint["state_hash"],
        },
    }
    return bundle


def fixture_trace(*, repaired_hash, reentry=False, unrelated_final_budget=100):
    events = [
        {
            "event_index": 35,
            "turn": 9,
            "realized_in_baseline": True,
            "action_type": "message",
            "action": {"type": "message", "to": "inventory"},
        },
    ]
    if reentry:
        events.append({
            "event_index": 36,
            "turn": 10,
            "realized_in_baseline": True,
            "action_type": "write_state",
            "action": {
                "type": "write_state",
                "key": "inventory_stockout_assessment_v1",
                "status": "fact",
            },
        })
    return {
        "r7_condition": {
            "arm_id": "C3_ALR",
            "condition_status": "OBSERVED",
            "branch_start_state_hash": repaired_hash,
        },
        "runtime_transform_records": [],
        "action_transform_records": [],
        "events": events,
        "model_calls": [{"turn": 9, "agent_id": "ops_lead"}],
        "final_state": {
            "state": {
                "inventory_stockout_assessment_v1": {"A": {"preliminary_stock": 1520}},
                "unrelated_finance_state": {"budget": unrelated_final_budget},
            },
            "state_metadata": {
                "inventory_stockout_assessment_v1": {
                    "status": "unconfirmed",
                    "basis": "fixture",
                    "writer": "inventory",
                    "event_index": 32,
                },
                "unrelated_finance_state": {"status": "fact", "writer": "finance"},
            },
        },
    }


class R7SemanticRepairRuntimeTest(unittest.TestCase):
    def _build(self):
        bundle = fixture_bundle()
        plan = build_semantic_repair_runtime_plan(
            packet=bundle["semantic_repair_packet"],
            gate=bundle["lineage_completeness_gate"],
            bundle=bundle,
        )
        repaired, application = build_repaired_parent_snapshot(
            parent_snapshot=bundle["source_parent_snapshot"],
            plan=plan,
        )
        return bundle, plan, repaired, application

    def test_repair_snapshot_changes_only_target_authority(self):
        bundle, plan, repaired, application = self._build()
        parent = bundle["source_parent_snapshot"]
        self.assertEqual(parent["shared_state"], repaired["shared_state"])
        self.assertEqual("fact", parent["shared_state_metadata"][plan["target_state_key"]]["status"])
        self.assertEqual("unconfirmed", repaired["shared_state_metadata"][plan["target_state_key"]]["status"])
        self.assertEqual(["shared_state_metadata.inventory_stockout_assessment_v1.status"], application["changed_paths"])
        self.assertTrue(application["direct_unrelated_parent_state_preserved"])

    def test_packet_drives_runtime_plan_and_verification(self):
        _, plan, repaired, application = self._build()
        verification = verify_semantic_repair_trace(
            trace=fixture_trace(repaired_hash=repaired["state_hash"]),
            plan=plan,
            repair_application=application,
        )
        self.assertTrue(verification["target_integrity_repair_executed"])
        self.assertTrue(verification["authority_state_repair_applied"])
        self.assertTrue(verification["repair_closure_invalidated_at_branch_start"])
        self.assertTrue(verification["preserved_unrelated_structure"])
        self.assertFalse(verification["old_lineage_reentry_detected"])
        self.assertGreaterEqual(len(verification["recomputed_descendant_refs"]), 1)

    def test_old_lineage_reentry_is_detected(self):
        _, plan, repaired, application = self._build()
        verification = verify_semantic_repair_trace(
            trace=fixture_trace(repaired_hash=repaired["state_hash"], reentry=True),
            plan=plan,
            repair_application=application,
        )
        self.assertTrue(verification["old_lineage_reentry_detected"])
        self.assertEqual(["arena_event:36"], verification["old_lineage_reentry_refs"])

    def test_downstream_unrelated_drift_is_descriptive_not_direct_repair_collateral(self):
        _, plan, repaired, application = self._build()
        verification = verify_semantic_repair_trace(
            trace=fixture_trace(repaired_hash=repaired["state_hash"], unrelated_final_budget=90),
            plan=plan,
            repair_application=application,
        )
        self.assertTrue(verification["preserved_unrelated_structure"])
        self.assertIn("unrelated_finance_state", verification["post_recompute_unrelated_changed_keys"])
        self.assertEqual("DIRECT_REPAIR_APPLICATION_SURFACE", verification["preservation_scope"])


if __name__ == "__main__":
    unittest.main()
