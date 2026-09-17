#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from .alr_recovery import build_alr_recovery_plan, make_revision_lineage_record, verify_alr_recovery_plan
from .core import stable_hash
from .persistent_field_intervention import (
    PersistentFieldRuntimeViewTransform,
    build_persistent_field_envelope,
    verify_persistent_field_envelope,
)
from .one_shot_intervention import OneShotRuntimeViewTransform, build_one_shot_envelope, verify_one_shot_envelope


SCHEMA = "RB-R7-STRUCTURAL-CONTROL-PREFLIGHT-v0.1"


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def _write_json(path: Path, row) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(row, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _base_runtime_view(status: str = "fact") -> dict:
    return {
        "shared_state": {"inventory_stockout_assessment_v1": "fixture"},
        "shared_state_metadata": {
            "inventory_stockout_assessment_v1": {
                "status": status,
                "basis": "engineering-only R7 preflight fixture",
            }
        },
        "inbox": [],
        "pending_invocations": [],
    }


def _semantic_payload_hash(*, state_key: str, to_status: str) -> str:
    return stable_hash({
        "state_key": state_key,
        "to_status": to_status,
        "meaning": "downgrade selected J0 state from factual certainty to unconfirmed",
    })


def build_r7_preflight() -> dict:
    jump_ref = "event:32:ENGINEERING_FIXTURE_J0"
    candidate_id = "R7-PREFLIGHT-J0"
    state_key = "inventory_stockout_assessment_v1"
    source_event_index = 32
    from_status = "fact"
    to_status = "unconfirmed"
    semantic_hash = _semantic_payload_hash(state_key=state_key, to_status=to_status)

    one_shot = build_one_shot_envelope(
        target_jump_ref=jump_ref,
        target_candidate_id=candidate_id,
        state_key=state_key,
        source_event_index=source_event_index,
        from_status=from_status,
        to_status=to_status,
    )
    verify_one_shot_envelope(one_shot)

    persistent = build_persistent_field_envelope(
        target_jump_ref=jump_ref,
        target_candidate_id=candidate_id,
        state_key=state_key,
        source_event_index=source_event_index,
        from_status=from_status,
        to_status=to_status,
        max_direct_exposures=3,
    )
    verify_persistent_field_envelope(persistent)

    one_shot_semantic_hash = _semantic_payload_hash(
        state_key=one_shot["state_key"],
        to_status=one_shot["to_status"],
    )
    persistent_semantic_hash = _semantic_payload_hash(
        state_key=persistent["state_key"],
        to_status=persistent["to_status"],
    )
    _require(one_shot_semantic_hash == semantic_hash == persistent_semantic_hash, "r7_semantic_payload_not_matched")

    # Exercise copied-view behavior directly. This verifies the R7 independent
    # variable before any provider/API execution: C1 exposes once; C2 repeatedly;
    # neither mutates the source Arena-like runtime view.
    source_view = _base_runtime_view(status=from_status)
    source_hash = stable_hash(source_view)

    c1_transform = OneShotRuntimeViewTransform(one_shot)
    c1_views = []
    for turn, actor in [(9, "ops_lead"), (10, "ads"), (11, "inventory")]:
        view, record = c1_transform(actor=actor, turn=turn, runtime_view=source_view)
        c1_views.append({"turn": turn, "actor": actor, "view_hash": stable_hash(view), "delivery": record})
    c1_transform.verify_finished()
    _require(stable_hash(source_view) == source_hash, "r7_c1_mutated_source_view")
    _require(c1_transform.delivered_count == 1, "r7_c1_must_expose_once")

    c2_transform = PersistentFieldRuntimeViewTransform(persistent)
    c2_views = []
    for turn, actor in [(9, "ops_lead"), (10, "ads"), (11, "inventory")]:
        view, record = c2_transform(actor=actor, turn=turn, runtime_view=source_view)
        c2_views.append({"turn": turn, "actor": actor, "view_hash": stable_hash(view), "delivery": record})
    c2_transform.verify_finished(require_horizon_exhausted=True)
    _require(stable_hash(source_view) == source_hash, "r7_c2_mutated_source_view")
    _require(c2_transform.delivered_count == 3, "r7_c2_must_expose_every_declared_turn")

    dependency_edges = [
        {"source_ref": jump_ref, "target_ref": "event:33:message_to_ops", "relation": "state_informs_message", "evidence_ref": "E33"},
        {"source_ref": "event:33:message_to_ops", "target_ref": "event:35:ops_write", "relation": "message_informs_action", "evidence_ref": "E35"},
        {"source_ref": "event:35:ops_write", "target_ref": "event:36:ads_invoke", "relation": "action_enables_invoke", "evidence_ref": "E36"},
    ]
    known_nodes = [
        "event:20:unrelated_finance_state",
        jump_ref,
        "event:33:message_to_ops",
        "event:35:ops_write",
        "event:36:ads_invoke",
        "event:40:unrelated_terminal_annotation",
    ]
    recovery_condition = {
        "authority_class": "INFORMATION_AUTHORITY",
        "target_state_key": state_key,
        "required_status": to_status,
        "semantic_payload_hash": semantic_hash,
    }
    alr_plan = build_alr_recovery_plan(
        recovery_id="R7-PREFLIGHT-ALR-v0.1",
        parent_trace_hash="ENGINEERING_ONLY_PARENT_TRACE",
        parent_state_hash="ENGINEERING_ONLY_PARENT_STATE",
        jump_ref=jump_ref,
        authority_ancestor_ref=jump_ref,
        dependency_edges=dependency_edges,
        semantic_payload_hash=semantic_hash,
        recovery_condition=recovery_condition,
        all_known_node_refs=known_nodes,
    )
    verify_alr_recovery_plan(alr_plan)
    _require(alr_plan["semantic_payload_hash"] == persistent_semantic_hash, "r7_c2_c3_semantic_payload_not_matched")
    _require("event:20:unrelated_finance_state" in alr_plan["preserve_node_refs"], "r7_unaffected_node_not_preserved")
    _require("event:40:unrelated_terminal_annotation" in alr_plan["preserve_node_refs"], "r7_unaffected_terminal_node_not_preserved")
    _require(jump_ref in alr_plan["reopen_node_refs"], "r7_jump_not_reopened")

    revision = make_revision_lineage_record(
        plan=alr_plan,
        prior_revision_hash=None,
        recovered_state_hash="ENGINEERING_ONLY_RECOVERED_STATE",
        reopened_node_refs=list(alr_plan["reopen_node_refs"]),
        preserved_node_refs=list(alr_plan["preserve_node_refs"]),
    )

    summary = {
        "schema": SCHEMA,
        "scientific_status": "ENGINEERING_ONLY_NOT_SCIENTIFIC_EVIDENCE",
        "same_j0": True,
        "jump_ref": jump_ref,
        "semantic_payload_hash": semantic_hash,
        "semantic_payload_equivalent_c1_c2_c3": (
            one_shot_semantic_hash == persistent_semantic_hash == alr_plan["semantic_payload_hash"]
        ),
        "c1": {
            "condition": "ONE_SHOT_FREE_CONTINUATION",
            "direct_exposures": c1_transform.delivered_count,
            "reinjections": c1_transform.summary()["experiment_origin_reinjection_count"],
            "persistent_state_mutation": c1_transform.summary()["persistent_state_mutation"],
            "delivery_record_hashes": c1_transform.summary()["delivery_record_hashes"],
        },
        "c2": {
            "condition": "PERSISTENT_FIELD_PROPAGATION",
            "direct_exposures": c2_transform.delivered_count,
            "reinjections": c2_transform.summary()["experiment_origin_reinjection_count"],
            "persistent_state_mutation": c2_transform.summary()["persistent_state_mutation"],
            "delivery_record_hashes": c2_transform.summary()["delivery_record_hashes"],
        },
        "c3": {
            "condition": "ALR_STRUCTURAL_RECOVERY",
            "authority_ancestor_ref": alr_plan["authority_ancestor_ref"],
            "affected_closure": list(alr_plan["affected_dependency_closure"]),
            "preserved_nodes": list(alr_plan["preserve_node_refs"]),
            "plan_hash": alr_plan["plan_hash"],
            "revision_hash": revision["revision_hash"],
        },
        "source_runtime_view_immutable": stable_hash(source_view) == source_hash,
        "provider_internal_state_replayed": False,
        "paid_api_called": False,
        "semantic_cpr_status": "NOT_ADJUDICATED",
        "interpretation_boundary": (
            "This deterministic preflight validates condition isolation, repeated-field instrumentation, "
            "semantic-payload matching, ALR dependency-closure localization, unaffected-node preservation, "
            "and revision-lineage plumbing only. It is not scientific evidence that system inertia is steerable."
        ),
    }
    summary["summary_hash"] = stable_hash(summary)

    return {
        "one_shot_envelope": one_shot,
        "persistent_field_envelope": persistent,
        "c1_runtime_views": c1_views,
        "c2_runtime_views": c2_views,
        "alr_recovery_plan": alr_plan,
        "alr_revision_lineage": revision,
        "summary": summary,
    }


def _human_summary(bundle: dict) -> str:
    s = bundle["summary"]
    return "\n".join([
        "R7 STRUCTURAL INERTIA CONTROL PREFLIGHT v0.1",
        "STATUS: ENGINEERING ONLY — NOT SCIENTIFIC EVIDENCE",
        "",
        f"same_j0={s['same_j0']}",
        f"semantic_payload_equivalent_c1_c2_c3={s['semantic_payload_equivalent_c1_c2_c3']}",
        f"c1_direct_exposures={s['c1']['direct_exposures']}",
        f"c1_reinjections={s['c1']['reinjections']}",
        f"c2_direct_exposures={s['c2']['direct_exposures']}",
        f"c2_reinjections={s['c2']['reinjections']}",
        f"c3_affected_nodes={len(s['c3']['affected_closure'])}",
        f"c3_preserved_nodes={len(s['c3']['preserved_nodes'])}",
        f"paid_api_called={s['paid_api_called']}",
        f"semantic_cpr_status={s['semantic_cpr_status']}",
        "",
        s["interpretation_boundary"],
        "",
        "summary_hash=" + s["summary_hash"],
        "",
    ])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="results/r7_structural_control_preflight")
    args = ap.parse_args()
    bundle = build_r7_preflight()
    outdir = Path(args.outdir)
    for key, value in bundle.items():
        _write_json(outdir / f"{key}.json", value)
    text = _human_summary(bundle)
    (outdir / "SUMMARY.txt").write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
