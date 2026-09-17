from arena.r7_structural_control_preflight import build_r7_preflight
from arena.alr_recovery import verify_alr_recovery_plan, verify_revision_lineage_record
from arena.persistent_field_intervention import verify_persistent_field_envelope
from arena.one_shot_intervention import verify_one_shot_envelope


def test_r7_structural_control_preflight_condition_isolation():
    bundle = build_r7_preflight()
    summary = bundle["summary"]

    assert summary["scientific_status"] == "ENGINEERING_ONLY_NOT_SCIENTIFIC_EVIDENCE"
    assert summary["same_j0"] is True
    assert summary["semantic_payload_equivalent_c1_c2_c3"] is True
    assert summary["source_runtime_view_immutable"] is True
    assert summary["paid_api_called"] is False
    assert summary["semantic_cpr_status"] == "NOT_ADJUDICATED"

    assert summary["c1"]["direct_exposures"] == 1
    assert summary["c1"]["reinjections"] == 0
    assert summary["c1"]["persistent_state_mutation"] is False

    assert summary["c2"]["direct_exposures"] == 3
    assert summary["c2"]["reinjections"] == 2
    assert summary["c2"]["persistent_state_mutation"] is False

    verify_one_shot_envelope(bundle["one_shot_envelope"])
    verify_persistent_field_envelope(bundle["persistent_field_envelope"])
    verify_alr_recovery_plan(bundle["alr_recovery_plan"])
    verify_revision_lineage_record(bundle["alr_revision_lineage"], plan=bundle["alr_recovery_plan"])


def test_r7_alr_preserves_nodes_outside_affected_closure():
    bundle = build_r7_preflight()
    plan = bundle["alr_recovery_plan"]

    assert "event:20:unrelated_finance_state" in plan["preserve_node_refs"]
    assert "event:40:unrelated_terminal_annotation" in plan["preserve_node_refs"]
    assert plan["jump_ref"] in plan["reopen_node_refs"]
    assert set(plan["reopen_node_refs"]).isdisjoint(set(plan["preserve_node_refs"]))
