from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from .core import stable_hash
from .prompts import build_agent_messages
from .r5r6_specificity_atomic_v0_2 import (
    S0,
    S1,
    S2,
    AtomicEpistemicAnnotationTransform,
    build_atomic_envelope,
    mechanically_equivalent,
    verify_target_value,
)

ROOT = Path(__file__).resolve().parents[1]


def _load(rel: str):
    with (ROOT / rel).open("r", encoding="utf-8") as f:
        return json.load(f)


def _ops_agent(domain):
    return next(x for x in domain["agents"] if x["id"] == "ops_lead")


def _runtime_fixture(source_slice):
    return {
        "shared_state": {
            "inventory_stockout_assessment_v1": {
                "A": {"preliminary_stock": source_slice["j0_source"]["atomic_target_value"]}
            }
        },
        "shared_state_metadata": {
            "inventory_stockout_assessment_v1": {
                "status": source_slice["j0_source"]["container_status"],
                "writer": "inventory",
                "event_index": source_slice["j0_source"]["event_index_zero_based"],
            }
        },
        "final_state": None,
        "inbox": [],
        "active_agents": ["ops_lead"],
        "remaining_turn_budget": 8,
    }


def build_preflight() -> dict:
    domain = _load("arena/domains/ecommerce.json")
    binding = _load("configs/r5r6_specificity_exact_source_binding_v0.2.json")
    selection = _load("manifests/r5r6_specificity_s1_selection_2026-09-17_v0_2.json")
    source_slice = _load("manifests/r5r6_specificity_source_slice_2026-09-17_v0_2.json")

    statuses = source_slice["parent_shared_state_metadata_statuses"]
    non_initial_facts = sorted(k for k, v in statuses.items() if v == "fact")
    if non_initial_facts != ["inventory_stockout_assessment_v1"]:
        raise ValueError("exact_source_top_level_fact_audit_mismatch")

    s1_binding = binding["s1"]
    s2_binding = binding["s2"]
    selected = selection["selected_s1_target"]
    if selected["locator"] != s1_binding["target_locator"] or selected["value"] != s1_binding["original_value"]:
        raise ValueError("s1_selection_binding_mismatch")

    verify_target_value(
        root=domain["task"],
        locator=s1_binding["target_locator"],
        expected_value=s1_binding["original_value"],
    )
    runtime = _runtime_fixture(source_slice)
    verify_target_value(
        root=runtime,
        locator=s2_binding["target_locator"],
        expected_value=s2_binding["original_value"],
    )

    s1_envelope = build_atomic_envelope(
        condition_id=S1,
        target_locator=s1_binding["target_locator"],
        original_value=s1_binding["original_value"],
        target_class=s1_binding["target_class"],
        source_refs=s1_binding["source_refs"],
        source_origin_status=s1_binding["source_origin_status"],
        acquired_status_at_intervention=s1_binding["acquired_status_at_intervention"],
    )
    s2_envelope = build_atomic_envelope(
        condition_id=S2,
        target_locator=s2_binding["target_locator"],
        original_value=s2_binding["original_value"],
        target_class=s2_binding["target_class"],
        source_refs=s2_binding["source_refs"],
        source_origin_status=s2_binding["source_origin_status"],
        acquired_status_at_intervention=s2_binding["acquired_status_at_intervention"],
    )
    mechanically_equivalent(s1_envelope, s2_envelope)

    source_runtime_hash = stable_hash(runtime)
    s1_transform = AtomicEpistemicAnnotationTransform(s1_envelope)
    s2_transform = AtomicEpistemicAnnotationTransform(s2_envelope)
    s1_view, s1_delivery = s1_transform(actor="ops_lead", turn=9, runtime_view=runtime)
    s2_view, s2_delivery = s2_transform(actor="ops_lead", turn=9, runtime_view=runtime)
    s1_next, s1_next_delivery = s1_transform(actor="ops_lead", turn=10, runtime_view=runtime)
    s2_next, s2_next_delivery = s2_transform(actor="ops_lead", turn=10, runtime_view=runtime)

    if stable_hash(runtime) != source_runtime_hash:
        raise ValueError("atomic_operator_mutated_source_runtime")
    if s1_next_delivery is not None or s2_next_delivery is not None:
        raise ValueError("atomic_operator_reinjected")
    if "epistemic_annotations" in s1_next or "epistemic_annotations" in s2_next:
        raise ValueError("atomic_annotation_persisted_after_consumption")
    s1_transform.verify_finished()
    s2_transform.verify_finished()

    agent = _ops_agent(domain)
    control_messages = build_agent_messages(domain, agent, runtime)
    s1_messages = build_agent_messages(domain, agent, s1_view)
    s2_messages = build_agent_messages(domain, agent, s2_view)
    control_payload = json.loads(control_messages[1]["content"])
    s1_payload = json.loads(s1_messages[1]["content"])
    s2_payload = json.loads(s2_messages[1]["content"])

    if "epistemic_annotations" in control_payload:
        raise ValueError("control_prompt_must_not_have_epistemic_annotation")
    if s1_payload["epistemic_annotations"] != [s1_envelope["prompt_visible_annotation"]]:
        raise ValueError("s1_prompt_annotation_mismatch")
    if s2_payload["epistemic_annotations"] != [s2_envelope["prompt_visible_annotation"]]:
        raise ValueError("s2_prompt_annotation_mismatch")
    if s1_payload["public_context"]["products"]["C"]["gross_margin_pct"] != 35:
        raise ValueError("s1_original_target_value_changed")
    if s2_payload["shared_state"]["inventory_stockout_assessment_v1"]["A"]["preliminary_stock"] != 1520:
        raise ValueError("s2_original_target_value_changed")

    plan = {
        "schema": "RB-R5R6-SPECIFICITY-ATOMIC-PLAN-v0.2",
        "version": "0.2",
        "scientific_status": "PREPARED_ONLY_NO_SCIENTIFIC_SUBJECT_OUTCOMES",
        "source_binding_schema": binding["schema"],
        "selection_record_hash": selection["selection_record_hash"],
        "conditions": [S0, S1, S2],
        "s1_envelope_hash": s1_envelope["envelope_hash"],
        "s2_envelope_hash": s2_envelope["envelope_hash"],
        "primary_contrast": "S2_MINUS_S1",
        "auxiliary_contrasts": ["S1_MINUS_S0", "S2_MINUS_S0"],
        "primary_readout": "POST_CONSUMPTION_R6_INERTIA_PROFILE",
        "historical_r5_operator_replayed_exactly": False,
        "prospective_s2_role": "ATOMIC_TARGET_SPECIFICITY_FOLLOW_UP",
        "provider_internal_state_replayed": False,
        "semantic_cpr_status": "NOT_ADJUDICATED",
        "authorization_status": "NOT_AUTHORIZED",
        "paid_provider_authorized": False,
        "paid_evaluator_authorized": False,
    }
    plan["plan_hash"] = stable_hash(plan)

    summary = {
        "schema": "RB-R5R6-SPECIFICITY-ATOMIC-PREFLIGHT-v0.2",
        "scientific_status": "ENGINEERING_ONLY_NOT_SCIENTIFIC_EVIDENCE",
        "exact_source_top_level_fact_keys": non_initial_facts,
        "v0_1_second_top_level_fact_available": False,
        "s1_target_locator": s1_binding["target_locator"],
        "s1_original_value_hash": s1_envelope["original_value_hash"],
        "s2_target_locator": s2_binding["target_locator"],
        "s2_original_value_hash": s2_envelope["original_value_hash"],
        "s1_s2_mechanically_equivalent": True,
        "s1_direct_exposures": s1_transform.delivered_count,
        "s2_direct_exposures": s2_transform.delivered_count,
        "s1_reinjections": 0,
        "s2_reinjections": 0,
        "source_runtime_immutable": stable_hash(runtime) == source_runtime_hash,
        "original_target_values_preserved": True,
        "control_prompt_has_annotation": False,
        "s1_prompt_hash": stable_hash(s1_messages),
        "s2_prompt_hash": stable_hash(s2_messages),
        "plan_hash": plan["plan_hash"],
        "semantic_cpr_status": "NOT_ADJUDICATED",
        "paid_provider_called": False,
        "paid_evaluator_called": False,
    }
    summary["summary_hash"] = stable_hash(summary)

    return {
        "summary": summary,
        "plan": plan,
        "s1_envelope": s1_envelope,
        "s2_envelope": s2_envelope,
        "s1_delivery": s1_delivery,
        "s2_delivery": s2_delivery,
        "control_prompt_payload": control_payload,
        "s1_prompt_payload": s1_payload,
        "s2_prompt_payload": s2_payload,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()
    out = Path(args.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_atomic_specificity_preflight_dir")
    out.mkdir(parents=True)
    bundle = build_preflight()
    for key, value in bundle.items():
        (out / f"{key}.json").write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("R5R6_ATOMIC_SPECIFICITY_PREFLIGHT=PASS")
    print("S1_TARGET=" + bundle["summary"]["s1_target_locator"])
    print("S2_TARGET=" + bundle["summary"]["s2_target_locator"])
    print("PLAN_HASH=" + bundle["plan"]["plan_hash"])
    print("PAID_PROVIDER_CALLED=NO")
    print("SEMANTIC_CPR_STATUS=NOT_ADJUDICATED")


if __name__ == "__main__":
    main()
