from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from .core import stable_hash
from .r5r6_specificity import (
    S0,
    S1,
    S2,
    SpecificityOneShotRuntimeViewTransform,
    build_field_selection_record,
    build_specificity_plan,
    rotated_condition_order,
    verify_specificity_plan,
)


def _fixture_parent() -> dict:
    return {
        "turns": 8,
        "anchor_ref": "after_turn:8",
        "shared_state_metadata": {
            "inventory_stockout_assessment_v1": {
                "status": "fact",
                "source": "inventory",
                "interface_family": "inventory_assessment",
                "visible_to": ["ops_lead", "inventory"],
            },
            "promotion_calendar_assessment_v1": {
                "status": "fact",
                "source": "ops_lead",
                "interface_family": "operational_assessment",
                "visible_to": ["ops_lead", "ads"],
            },
            "budget_baseline_assessment_v1": {
                "status": "fact",
                "source": "ads",
                "interface_family": "operational_assessment",
                "visible_to": ["ops_lead", "ads"],
            },
            "draft_note_v1": {
                "status": "provisional",
                "source": "ops_lead",
                "interface_family": "note",
                "visible_to": ["ops_lead"],
            },
        },
    }


def build_preflight() -> dict:
    parent = _fixture_parent()
    parent_hash = stable_hash(parent)
    j0_features = {
        "pre_intervention_status_class": "fact",
        "runtime_visibility_boundary": "POST_J0_SHARED_STATE",
        "temporal_distance_from_common_parent": 0,
        "state_or_interface_family": "operational_assessment",
        "actor_or_role_accessibility": "ops_lead_visible",
        "downstream_opportunity_for_inheritance": "available_next_turn",
        "source_evidence_completeness": "complete",
    }
    candidates = [
        {
            "state_key": "promotion_calendar_assessment_v1",
            "pre_status": "fact",
            "source_refs": ["FIXTURE:E20"],
            "matching_features": copy.deepcopy(j0_features),
            "eligible": True,
        },
        {
            "state_key": "budget_baseline_assessment_v1",
            "pre_status": "fact",
            "source_refs": ["FIXTURE:E21"],
            "matching_features": {
                **j0_features,
                "actor_or_role_accessibility": "ads_visible",
            },
            "eligible": True,
        },
        {
            "state_key": "draft_note_v1",
            "pre_status": "provisional",
            "source_refs": ["FIXTURE:E22"],
            "matching_features": {
                **j0_features,
                "pre_intervention_status_class": "provisional",
                "state_or_interface_family": "note",
            },
            "eligible": True,
        },
        {
            "state_key": "inventory_stockout_assessment_v1",
            "pre_status": "fact",
            "source_refs": ["FIXTURE:E32"],
            "matching_features": copy.deepcopy(j0_features),
            "eligible": True,
        },
    ]
    selection = build_field_selection_record(
        source_trace_hash="fixture-source-trace-hash",
        source_evidence_hash="fixture-source-evidence-hash",
        common_parent_state_hash=parent_hash,
        j0_candidate_id="FIXTURE-J0",
        j0_event_ref="FIXTURE:E32",
        j0_state_key="inventory_stockout_assessment_v1",
        j0_pre_status="fact",
        j0_matching_features=j0_features,
        candidates=candidates,
    )
    bundle = build_specificity_plan(
        selection_record=selection,
        j0_source_refs=["FIXTURE:E32"],
        post_consumption_turn_cap=8,
        replicates=3,
        code_identity={"mode": "OFFLINE_PREFLIGHT"},
        model_identity={"provider": "OFFLINE_DETERMINISTIC_FIXTURE"},
        config_identity={"arena": "OFFLINE_SPECIFICITY_FIXTURE_v0.1"},
    )
    verify_specificity_plan(bundle)

    source_parent_before = stable_hash(parent)
    s1_transform = SpecificityOneShotRuntimeViewTransform(bundle["s1_envelope"])
    s2_transform = SpecificityOneShotRuntimeViewTransform(bundle["s2_envelope"])
    s1_view, s1_delivery = s1_transform(actor="ops_lead", turn=9, runtime_view=parent)
    s2_view, s2_delivery = s2_transform(actor="ops_lead", turn=9, runtime_view=parent)
    s1_second_view, s1_second_delivery = s1_transform(actor="ads", turn=10, runtime_view=parent)
    s2_second_view, s2_second_delivery = s2_transform(actor="inventory", turn=10, runtime_view=parent)
    source_parent_after = stable_hash(parent)

    assert source_parent_before == source_parent_after
    assert s1_view["shared_state_metadata"][selection["selected_s1_state_key"]]["status"] == "unconfirmed"
    assert s2_view["shared_state_metadata"][selection["selected_j0_state_key"]]["status"] == "unconfirmed"
    assert parent["shared_state_metadata"][selection["selected_s1_state_key"]]["status"] == "fact"
    assert parent["shared_state_metadata"][selection["selected_j0_state_key"]]["status"] == "fact"
    assert s1_delivery is not None and s2_delivery is not None
    assert s1_second_delivery is None and s2_second_delivery is None
    assert stable_hash(s1_second_view) == source_parent_after
    assert stable_hash(s2_second_view) == source_parent_after
    s1_transform.verify_finished()
    s2_transform.verify_finished()

    summary = {
        "schema": "RB-R5R6-SPECIFICITY-OFFLINE-PREFLIGHT-v0.1",
        "scientific_status": "ENGINEERING_ONLY_NOT_SCIENTIFIC_EVIDENCE",
        "plan_hash": bundle["plan"]["plan_hash"],
        "selection_record_hash": selection["selection_record_hash"],
        "eligible_pool_hash": selection["eligible_pool_hash"],
        "selected_s1_state_key": selection["selected_s1_state_key"],
        "selected_s2_state_key": selection["selected_j0_state_key"],
        "s1_s2_targets_distinct": selection["selected_s1_state_key"] != selection["selected_j0_state_key"],
        "s1_s2_mechanical_primitive_equal": bundle["s1_envelope"]["mechanical_primitive"] == bundle["s2_envelope"]["mechanical_primitive"],
        "s1_s2_to_status_equal": bundle["s1_envelope"]["to_status"] == bundle["s2_envelope"]["to_status"],
        "s1_s2_delivery_policy_equal": bundle["s1_envelope"]["delivery_policy"] == bundle["s2_envelope"]["delivery_policy"],
        "s1_direct_exposures": s1_transform.delivered_count,
        "s2_direct_exposures": s2_transform.delivered_count,
        "s1_reinjections": 0,
        "s2_reinjections": 0,
        "source_parent_immutable": source_parent_before == source_parent_after,
        "outcome_blind_selection": selection["selector_outcome_blind_attestation"],
        "specificity_conditions": [S0, S1, S2],
        "execution_orders": [list(rotated_condition_order(i)) for i in (1, 2, 3)],
        "namespace_aliasing_forbidden": bundle["plan"]["namespace_guard"]["aliasing_forbidden"],
        "paid_api_called": False,
        "paid_evaluator_called": False,
        "semantic_cpr_status": "NOT_ADJUDICATED",
        "provider_internal_state_replayed": False,
    }
    summary["summary_hash"] = stable_hash(summary)
    return {
        "summary": summary,
        "selection_record": selection,
        "plan_bundle": bundle,
        "s1_delivery": s1_delivery,
        "s2_delivery": s2_delivery,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()
    out = Path(args.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_specificity_preflight_dir")
    out.mkdir(parents=True)
    bundle = build_preflight()
    for name in ("summary", "selection_record", "s1_delivery", "s2_delivery"):
        (out / f"{name}.json").write_text(json.dumps(bundle[name], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    plan_bundle = bundle["plan_bundle"]
    (out / "specificity_plan.json").write_text(json.dumps(plan_bundle["plan"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "s1_envelope.json").write_text(json.dumps(plan_bundle["s1_envelope"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "s2_envelope.json").write_text(json.dumps(plan_bundle["s2_envelope"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("R5R6_SPECIFICITY_PREFLIGHT=PASS")
    print("PLAN_HASH=" + plan_bundle["plan"]["plan_hash"])
    print("SELECTED_S1_FIELD=" + bundle["selection_record"]["selected_s1_state_key"])
    print("PAID_API_CALLED=NO")
    print("SEMANTIC_CPR_STATUS=NOT_ADJUDICATED")


if __name__ == "__main__":
    main()
