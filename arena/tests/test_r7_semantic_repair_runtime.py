import copy
import unittest

from arena.r7_semantic_repair_runtime import (
    build_semantic_repair_runtime_plan,
    verify_semantic_repair_trace,
)


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
        "mechanically_required_replay_refs": ["r7:exact_pre_j0_checkpoint", "r7:authority_ancestor_turn"],
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
    checkpoint = {
        "state_hash": "CHECKPOINT",
        "turns": 7,
        "shared_state": {
            "inventory_stockout_assessment_v1": {"old": True},
            "unrelated_finance_state": {"budget": 100},
        },
        "shared_state_metadata": {
            "inventory_stockout_assessment_v1": {"status": "preliminary"},
            "unrelated_finance_state": {"status": "fact", "writer": "finance"},
        },
    }
    bundle = {
        "semantic_repair_packet": packet,
        "lineage_completeness_gate": gate,
        "c3_recovery_checkpoint": checkpoint,
        "source_parent_snapshot": {"state_hash": "PARENT"},
        "c3_alr_binding": {
            "state_key": "inventory_stockout_assessment_v1",
            "from_status": "fact",
            "to_status": "unconfirmed",
            "target_reexecution_turn": 8,
            "common_reference_parent_state_hash": "PARENT",
            "recovery_checkpoint_state_hash": "CHECKPOINT",
        },
    }
    return bundle


def fixture_trace(*, reentry=False, preserve=True):
    finance_value = {"budget": 100} if preserve else {"budget": 90}
    finance_meta = {"status": "fact", "writer": "finance"}
    events = [
        {
            "event_index": 32,
            "turn": 8,
            "realized_in_baseline": True,
            "action_type": "write_state",
            "action": {
                "type": "write_state",
                "key": "inventory_stockout_assessment_v1",
                "status": "unconfirmed",
            },
        },
        {
            "event_index": 33,
            "turn": 9,
            "realized_in_baseline": True,
            "action_type": "message",
            "action": {"type": "message", "to": "ops_lead"},
        },
    ]
    if reentry:
        events.append({
            "event_index": 34,
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
        "action_transform_records": [{
            "state_key": "inventory_stockout_assessment_v1",
            "transform_applied": True,
            "turn": 8,
        }],
        "events": events,
        "model_calls": [
            {"turn": 8, "agent_id": "inventory"},
            {"turn": 9, "agent_id": "ops_lead"},
        ],
        "final_state": {
            "state": {
                "inventory_stockout_assessment_v1": {"new": True},
                "unrelated_finance_state": finance_value,
            },
            "state_metadata": {
                "inventory_stockout_assessment_v1": {"status": "unconfirmed"},
                "unrelated_finance_state": finance_meta,
            },
        },
    }


class R7SemanticRepairRuntimeTest(unittest.TestCase):
    def test_packet_drives_runtime_plan_and_verification(self):
        bundle = fixture_bundle()
        plan = build_semantic_repair_runtime_plan(
            packet=bundle["semantic_repair_packet"],
            gate=bundle["lineage_completeness_gate"],
            bundle=bundle,
        )
        verification = verify_semantic_repair_trace(
            trace=fixture_trace(),
            plan=plan,
            transform_summary={"transform_count": 1},
        )
        self.assertTrue(verification["target_integrity_repair_executed"])
        self.assertTrue(verification["repair_closure_invalidated_at_branch_start"])
        self.assertTrue(verification["preserved_unrelated_structure"])
        self.assertFalse(verification["old_lineage_reentry_detected"])
        self.assertGreaterEqual(len(verification["recomputed_descendant_refs"]), 2)

    def test_old_lineage_reentry_is_detected(self):
        bundle = fixture_bundle()
        plan = build_semantic_repair_runtime_plan(
            packet=bundle["semantic_repair_packet"],
            gate=bundle["lineage_completeness_gate"],
            bundle=bundle,
        )
        verification = verify_semantic_repair_trace(
            trace=fixture_trace(reentry=True),
            plan=plan,
            transform_summary={"transform_count": 1},
        )
        self.assertTrue(verification["old_lineage_reentry_detected"])
        self.assertEqual(["arena_event:34"], verification["old_lineage_reentry_refs"])

    def test_unrelated_state_drift_is_not_silently_called_preserved(self):
        bundle = fixture_bundle()
        plan = build_semantic_repair_runtime_plan(
            packet=bundle["semantic_repair_packet"],
            gate=bundle["lineage_completeness_gate"],
            bundle=bundle,
        )
        verification = verify_semantic_repair_trace(
            trace=fixture_trace(preserve=False),
            plan=plan,
            transform_summary={"transform_count": 1},
        )
        self.assertFalse(verification["preserved_unrelated_structure"])


if __name__ == "__main__":
    unittest.main()
