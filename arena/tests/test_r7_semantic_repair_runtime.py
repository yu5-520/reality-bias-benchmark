import copy
import unittest

from arena.core import stable_hash
from arena.r7_semantic_repair_runtime import (
    build_repaired_parent_snapshot,
    build_semantic_repair_runtime_plan,
    verify_semantic_repair_trace,
)


def make_snapshot():
    snap = {
        "schema": "RB-EXPERIMENTAL-STATE-SNAPSHOT-v0.1",
        "run_id": "fixture",
        "domain_id": "ecommerce",
        "anchor_ref": "after_turn:8",
        "parent_trace_hash": "TRACE",
        "turns": 8,
        "shared_state": {
            "inventory_stockout_assessment_v1": {"A": {"preliminary_stock": 1520}},
            "unrelated_finance_state": {"budget": 100},
        },
        "shared_state_metadata": {
            "inventory_stockout_assessment_v1": {
                "status": "fact",
                "writer": "inventory",
                "event_index": 32,
                "basis": "fixture",
            },
            "unrelated_finance_state": {"status": "fact", "writer": "finance"},
        },
        "final_state": None,
        "active_agents": ["ops_lead"],
        "inboxes": {"ops_lead": [], "inventory": [], "finance": [], "ads": []},
        "queue": ["ops_lead"],
        "events": [],
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
    snap["state_hash"] = stable_hash(snap)
    material = copy.deepcopy(snap)
    material.pop("state_hash")
    snap["state_hash"] = stable_hash(material)
    return snap


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
    parent = make_snapshot()
    binding = {
        "state_key": "inventory_stockout_assessment_v1",
        "from_status": "fact",
        "to_status": "unconfirmed",
        "jump_source_event_index": 32,
        "common_reference_parent_state_hash": parent["state_hash"],
    }
    repaired, revision = build_repaired_parent_snapshot(
        packet=packet,
        gate=gate,
        parent=parent,
        binding=binding,
    )
    binding["repaired_parent_state_hash"] = repaired["state_hash"]
    return {
        "semantic_repair_packet": packet,
        "lineage_completeness_gate": gate,
        "source_parent_snapshot": parent,
        "c3_repaired_parent_snapshot": repaired,
        "c3_direct_anchor_revision": revision,
        "c3_alr_binding": binding,
    }


def fixture_trace(*, reentry=False):
    events = [
        {
            "event_index": 33,
            "turn": 9,
            "realized_in_baseline": True,
            "action_type": "message",
            "action": {"type": "message", "to": "ads"},
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
        "events": events,
        "model_calls": [{"turn": 9, "agent_id": "ops_lead"}],
        "final_state": {
            "state": {
                "inventory_stockout_assessment_v1": {"A": {"preliminary_stock": 1520}},
                "unrelated_finance_state": {"budget": 90},
            },
            "state_metadata": {
                "inventory_stockout_assessment_v1": {"status": "unconfirmed"},
                "unrelated_finance_state": {"status": "recommendation", "writer": "finance"},
            },
        },
    }


class R7SemanticRepairRuntimeTest(unittest.TestCase):
    def test_direct_anchor_revision_preserves_target_value_and_unrelated_parent(self):
        bundle = fixture_bundle()
        parent = bundle["source_parent_snapshot"]
        repaired = bundle["c3_repaired_parent_snapshot"]
        self.assertEqual(parent["shared_state"]["inventory_stockout_assessment_v1"], repaired["shared_state"]["inventory_stockout_assessment_v1"])
        self.assertEqual("fact", parent["shared_state_metadata"]["inventory_stockout_assessment_v1"]["status"])
        self.assertEqual("unconfirmed", repaired["shared_state_metadata"]["inventory_stockout_assessment_v1"]["status"])
        self.assertEqual(parent["shared_state"]["unrelated_finance_state"], repaired["shared_state"]["unrelated_finance_state"])

    def test_packet_drives_direct_revision_and_downstream_verification(self):
        bundle = fixture_bundle()
        plan = build_semantic_repair_runtime_plan(
            packet=bundle["semantic_repair_packet"],
            gate=bundle["lineage_completeness_gate"],
            bundle=bundle,
        )
        verification = verify_semantic_repair_trace(
            trace=fixture_trace(),
            plan=plan,
            source_parent=bundle["source_parent_snapshot"],
            repaired_parent=bundle["c3_repaired_parent_snapshot"],
        )
        self.assertTrue(verification["target_integrity_repair_executed"])
        self.assertTrue(verification["repair_closure_invalidated_at_branch_start"])
        self.assertTrue(verification["preserved_unrelated_structure"])
        self.assertFalse(verification["old_lineage_reentry_detected"])
        self.assertGreaterEqual(len(verification["recomputed_descendant_refs"]), 1)
        self.assertIn("shared_state:unrelated_finance_state", verification["post_repair_unrelated_change_refs"])

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
            source_parent=bundle["source_parent_snapshot"],
            repaired_parent=bundle["c3_repaired_parent_snapshot"],
        )
        self.assertTrue(verification["old_lineage_reentry_detected"])
        self.assertEqual(["arena_event:34"], verification["old_lineage_reentry_refs"])


if __name__ == "__main__":
    unittest.main()
