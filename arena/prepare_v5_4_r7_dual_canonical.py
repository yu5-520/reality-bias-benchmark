#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from .core import stable_hash
from .experimental_control import verify_state_snapshot
from .io_utils import load_json, load_jsonl, write_jsonl, sha256_file
from .persistent_field_intervention import build_persistent_field_envelope
from .r7_semantic_repair_runtime import build_semantic_repair_runtime_plan, build_repaired_parent_snapshot
from .r7_lineage_monitoring import build_semantic_lineage_package, build_post_repair_watch_contract

CASE_PLAN_SCHEMA="RB-V5.4-R7-DUAL-CASE-PLAN-v0.1"
BATCH_PLAN_SCHEMA="RB-V5.4-R7-DUAL-FOUR-CANDIDATE-BATCH-PLAN-v0.1"


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def _hash_without(row,key):
    m=copy.deepcopy(row)
    m.pop(key,None)
    return stable_hash(m)


def _write(path,row):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(row,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")


def _group_for_case(cfg,case_id):
    rows=[g for g in cfg["source_r5_groups"] if case_id in g["case_ids"]]
    _require(len(rows)==1,"r7_v54_source_group_not_unique:"+case_id)
    return rows[0]


def _semantic_payload_hash(binding,envelope):
    return stable_hash({
        "target_path":f"shared_state_metadata.{binding['state_key']}.status",
        "from":envelope["from_status"],
        "to":envelope["to_status"],
        "semantic_meaning":"selected frozen source authority/status is downgraded from factual certainty to unconfirmed",
    })


def _bounded_arena_config(binding,parent,horizon):
    path=binding["config_identity"]["arena_config_path"]
    _require(sha256_file(path)==binding["config_identity"]["arena_config_hash"],"r7_v54_arena_config_hash_mismatch:"+binding["case_id"])
    source=load_json(path)
    out=copy.deepcopy(source)
    cap=int(parent["turns"])+int(horizon["post_source_turn_cap"])
    _require(int(source["max_turns"])>=cap,"r7_v54_horizon_exceeds_source_turn_budget:"+binding["case_id"])
    out["max_turns"]=cap
    out["r7_observation_horizon"]={
        "horizon_id":f"V54-R7-H1-{binding['case_id']}-POST-SOURCE-8",
        "distance_basis":horizon["distance_basis"],
        "common_reference_parent_turn":int(parent["turns"]),
        "post_source_turn_cap":int(horizon["post_source_turn_cap"]),
        "absolute_turn_cap":cap,
        "termination_policy":horizon["termination_policy"],
        "early_termination_policy":horizon["early_termination_policy"],
    }
    return out


def _build_case(cfg,source_root,lineage_root,case_id,plan_code_sha):
    group=_group_for_case(cfg,case_id)
    root=Path(source_root)/group["group_id"]/group["prepared_root"]
    bindings=load_jsonl(root/"case_bindings.jsonl")
    matches=[x for x in bindings if x["case_id"]==case_id]
    _require(len(matches)==1,"r7_v54_case_binding_not_unique:"+case_id)
    binding=matches[0]
    parent=load_json(root/"cases"/case_id/"parent_snapshot.json")
    envelope=load_json(root/"cases"/case_id/"one_shot_envelope.json")
    verify_state_snapshot(parent)

    gate=load_json(Path(lineage_root)/"results/v5_4_r6_lineage_completeness_candidates"/"cases"/case_id/"lineage_completeness_gate.json")
    packet=load_json(Path(lineage_root)/"results/v5_4_r6_lineage_completeness_candidates"/"cases"/case_id/"semantic_repair_packet.json")
    closure=load_json(Path(lineage_root)/"results/v5_4_r6_lineage_completeness_candidates"/"cases"/case_id/"semantic_lineage_closure.json")
    case_gate=load_json(Path(lineage_root)/"results/v5_4_r6_lineage_completeness_candidates"/"cases"/case_id/"case_summary.json")

    _require(gate["status"]=="COMPLETE_FOR_AUTHORIZED_REPAIR","r7_v54_lineage_not_complete:"+case_id)
    _require(gate["automatic_repair_allowed"] is False,"r7_v54_gate_must_not_auto_authorize:"+case_id)
    _require(packet["repair_authorization_status"]=="READY_FOR_SEPARATE_AUTHORIZATION","r7_v54_packet_not_ready:"+case_id)
    _require(packet["repair_anchor_ref"]==binding["candidate_ref"],"r7_v54_repair_anchor_mismatch:"+case_id)
    _require(packet["content_address"]==binding["content_address"],"r7_v54_content_address_mismatch:"+case_id)
    _require(case_gate["r7_entry_ready_for_separate_authorization"] is True,"r7_v54_case_gate_not_ready:"+case_id)
    _require(case_gate["r7_active_authorized"] is False,"r7_v54_lineage_artifact_self_authorized:"+case_id)

    _require(parent["state_hash"]==binding["parent_state_hash"],"r7_v54_parent_hash_mismatch:"+case_id)
    _require(envelope["target_jump_ref"]==binding["candidate_ref"],"r7_v54_one_shot_ref_mismatch:"+case_id)
    _require(envelope["source_event_index"]==binding["source_event_index"],"r7_v54_one_shot_event_mismatch:"+case_id)
    _require(envelope["state_key"]==binding["state_key"],"r7_v54_one_shot_key_mismatch:"+case_id)
    _require(envelope["from_status"]=="fact" and envelope["to_status"]=="unconfirmed","r7_v54_operator_mismatch:"+case_id)
    _require((parent["shared_state_metadata"][binding["state_key"]] or {}).get("status")=="fact","r7_v54_parent_target_not_fact:"+case_id)

    anchor_idx=int(binding["source_event_index"])
    events=[e for e in parent["events"] if int(e.get("event_index",-1))==anchor_idx]
    _require(len(events)==1,"r7_v54_anchor_event_not_unique:"+case_id)
    anchor=events[0]
    _require(anchor.get("action_type")=="write_state","r7_v54_anchor_not_write_state:"+case_id)
    _require((anchor.get("action") or {}).get("key")==binding["state_key"],"r7_v54_anchor_key_mismatch:"+case_id)
    _require((anchor.get("action") or {}).get("status")=="fact","r7_v54_anchor_status_mismatch:"+case_id)

    semantic_hash=_semantic_payload_hash(binding,envelope)
    bounded=_bounded_arena_config(binding,parent,cfg["horizon"])
    horizon_id=bounded["r7_observation_horizon"]["horizon_id"]
    persistent=build_persistent_field_envelope(
        target_jump_ref=envelope["target_jump_ref"],
        target_candidate_id=envelope["target_candidate_id"],
        state_key=envelope["state_key"],
        source_event_index=envelope["source_event_index"],
        from_status=envelope["from_status"],
        to_status=envelope["to_status"],
        max_direct_exposures=int(cfg["horizon"]["post_source_turn_cap"]),
    )

    # v5.4 canonical R7-S no longer requires the target write to be the first
    # event of its source turn. The exact target event inside the frozen
    # post-source parent is the repair anchor. The parent is also retained as
    # the immutable provenance checkpoint; it is not a rollback start.
    reference_checkpoint=copy.deepcopy(parent)
    alr_binding={
        "schema":"RB-V5.4-R7-STRUCTURED-REPAIR-BINDING-v0.1",
        "case_id":case_id,
        "common_reference_parent_state_hash":parent["state_hash"],
        "recovery_checkpoint_state_hash":reference_checkpoint["state_hash"],
        "reference_checkpoint_role":"IMMUTABLE_POST_SOURCE_PARENT_PROVENANCE_ONLY_NOT_ROLLBACK_START",
        "repair_anchor_ref":binding["candidate_ref"],
        "jump_source_event_index":anchor_idx,
        "state_key":binding["state_key"],
        "from_status":envelope["from_status"],
        "to_status":envelope["to_status"],
        "semantic_payload_hash":semantic_hash,
        "recovery_operator":"DIRECT_EXACT_EVENT_AUTHORITY_REPAIR_INVALIDATE_POST_ANCHOR_MATERIALIZATION_RECOMPUTE",
        "exact_target_event_may_be_mid_turn":True,
        "provider_internal_state_replayed":False,
    }
    alr_binding["binding_hash"]=_hash_without(alr_binding,"binding_hash")

    runtime_plan=build_semantic_repair_runtime_plan(
        packet=packet,
        gate=gate,
        bundle={
            "c3_alr_binding":alr_binding,
            "source_parent_snapshot":parent,
            "c3_recovery_checkpoint":reference_checkpoint,
        },
    )
    repaired_parent,repair_application=build_repaired_parent_snapshot(
        parent_snapshot=parent,
        plan=runtime_plan,
    )
    lineage_package=build_semantic_lineage_package(packet=packet,runtime_plan=runtime_plan)
    watch_contract=build_post_repair_watch_contract(runtime_plan=runtime_plan,repair_application=repair_application)

    rows=[]; manifests=[]
    arm_defs=[
        ("C2_PERSISTENT_FIELD","R7_P_PERSISTENT_SEMANTIC",1,parent["state_hash"],persistent["envelope_hash"],"PERSISTENT_RUNTIME_VIEW_OVERLAY"),
        ("C3_ALR","R7_S_STRUCTURED_LINEAGE_REPAIR",2,repaired_parent["state_hash"],repair_application["repair_application_hash"],"EXACT_EVENT_STRUCTURED_LINEAGE_REPAIR"),
    ]
    triad_id=f"v54-r7:{case_id}:dual:0001"
    for legacy,canonical,order,start_hash,binding_hash,mechanism in arm_defs:
        branch_id=f"{triad_id}:{canonical.lower()}"
        manifest={
            "schema":"RB-V5.4-R7-DUAL-ARM-MANIFEST-v0.1",
            "case_id":case_id,
            "branch_id":branch_id,
            "triad_id":triad_id,
            "replicate_index":1,
            "execution_order":order,
            "arm_id":legacy,
            "canonical_arm_id":canonical,
            "mechanism":mechanism,
            "common_reference_parent_state_hash":parent["state_hash"],
            "branch_start_state_hash":start_hash,
            "binding_hash":binding_hash,
            "semantic_payload_hash":semantic_hash,
            "observation_horizon_id":horizon_id,
            "provider_internal_state_replayed":False,
        }
        manifest["manifest_hash"]=_hash_without(manifest,"manifest_hash")
        manifests.append(manifest)
        rows.append({
            "run_id":branch_id,
            "case_id":case_id,
            "triad_id":triad_id,
            "replicate_index":1,
            "execution_order":order,
            "arm_id":legacy,
            "canonical_arm_id":canonical,
            "manifest_hash":manifest["manifest_hash"],
        })

    plan={
        "schema":CASE_PLAN_SCHEMA,
        "version":"0.1",
        "case_id":case_id,
        "domain_id":binding["domain_id"],
        "source_run_id":binding["source_run_id"],
        "source_case_hash":binding["source_case_hash"],
        "source_case_binding_hash":binding["case_binding_hash"],
        "repair_anchor_ref":binding["candidate_ref"],
        "content_address":binding["content_address"],
        "target_state_key":binding["state_key"],
        "source_event_index":anchor_idx,
        "source_turn":binding["source_turn"],
        "source_parent_state_hash":parent["state_hash"],
        "source_model_identity":binding["model_identity"],
        "source_config_identity":binding["config_identity"],
        "source_code_identity":binding["code_identity"],
        "lineage_gate_hash":gate["gate_hash"],
        "semantic_repair_packet_hash":packet["packet_hash"],
        "semantic_lineage_closure_hash":closure["closure_hash"],
        "semantic_payload_hash":semantic_hash,
        "matched_horizon":bounded["r7_observation_horizon"],
        "canonical_arm_ids":["R7_P_PERSISTENT_SEMANTIC","R7_S_STRUCTURED_LINEAGE_REPAIR"],
        "canonical_replicate_count":1,
        "branch_count":2,
        "new_provider_branch_count":2,
        "n0_reference_rerun_count":0,
        "r5_i_reference_rerun_count":0,
        "r5_reference_role":"FROZEN_CANONICAL_R5_I_REFERENCE_NOT_RERUN",
        "r7_p_persistent_field_envelope_hash":persistent["envelope_hash"],
        "r7_s_repair_application_hash":repair_application["repair_application_hash"],
        "r7_s_repaired_parent_state_hash":repaired_parent["state_hash"],
        "semantic_repair_runtime_plan_hash":runtime_plan["plan_hash"],
        "semantic_lineage_package_hash":lineage_package["package_hash"],
        "post_repair_watch_contract_hash":watch_contract["watch_hash"],
        "plan_code_sha":plan_code_sha,
        "real_subject_execution_authorized":False,
        "automatic_paid_evaluator":False,
        "semantic_cpr_status":"NOT_ADJUDICATED",
        "problematic_bias_status":"NOT_ESTABLISHED",
        "r5_unique_causal_attribution":"NOT_ESTABLISHED",
        "geometry_note":"R7-S repairs the exact target event within the frozen post-source parent; no legacy first-event-of-turn checkpoint requirement is used.",
    }
    plan["plan_hash"]=_hash_without(plan,"plan_hash")

    return {
        "plan":plan,
        "source_parent_snapshot":parent,
        "c3_recovery_checkpoint":reference_checkpoint,
        "c1_one_shot_envelope":envelope,
        "c2_persistent_field_envelope":persistent,
        "c3_alr_binding":alr_binding,
        "semantic_repair_runtime_plan":runtime_plan,
        "c3_repaired_parent_snapshot":repaired_parent,
        "c3_repair_application":repair_application,
        "semantic_repair_packet":packet,
        "semantic_lineage_closure":closure,
        "semantic_lineage_package":lineage_package,
        "post_repair_watch_contract":watch_contract,
        "lineage_completeness_gate":gate,
        "bounded_arena_config":bounded,
        "arm_manifests":manifests,
        "execution_rows":rows,
    }


def _write_bundle(out,bundle):
    out.mkdir(parents=True,exist_ok=False)
    mapping={
        "r7_plan.json":"plan",
        "source_parent_snapshot.json":"source_parent_snapshot",
        "c3_recovery_checkpoint.json":"c3_recovery_checkpoint",
        "c1_one_shot_envelope.json":"c1_one_shot_envelope",
        "c2_persistent_field_envelope.json":"c2_persistent_field_envelope",
        "c3_alr_binding.json":"c3_alr_binding",
        "semantic_repair_runtime_plan.json":"semantic_repair_runtime_plan",
        "c3_repaired_parent_snapshot.json":"c3_repaired_parent_snapshot",
        "c3_repair_application.json":"c3_repair_application",
        "semantic_repair_packet.json":"semantic_repair_packet",
        "semantic_lineage_closure.json":"semantic_lineage_closure",
        "semantic_lineage_package.json":"semantic_lineage_package",
        "post_repair_watch_contract.json":"post_repair_watch_contract",
        "lineage_completeness_gate.json":"lineage_completeness_gate",
        "r7_bounded_arena_config.json":"bounded_arena_config",
    }
    for fn,key in mapping.items():
        _write(out/fn,bundle[key])
    write_jsonl(out/"arm_manifests.jsonl",bundle["arm_manifests"])
    write_jsonl(out/"execution_rows.jsonl",bundle["execution_rows"])


def prepare(config_path,source_root,lineage_root,plan_code_sha,outdir):
    cfg=load_json(config_path)
    _require(cfg["schema"]=="RB-V5.4-R7-DUAL-FOUR-CANDIDATE-PLAN-v0.1","r7_v54_batch_config_schema_invalid")
    _require(cfg["status"]=="FROZEN_PRE_EXECUTION_PLAN","r7_v54_batch_config_not_frozen")
    _require(cfg["canonical_geometry"]["total_case_count"]==4,"r7_v54_case_count_not_four")
    _require(cfg["canonical_geometry"]["total_new_provider_trajectories"]==8,"r7_v54_branch_count_not_eight")
    _require(cfg["canonical_geometry"]["n0_rerun_count"]==0 and cfg["canonical_geometry"]["r5_i_rerun_count"]==0,"r7_v54_reference_rerun_forbidden")

    root=Path(outdir)
    if root.exists():
        raise ValueError("refusing_to_overwrite_v54_r7_plan_dir")
    root.mkdir(parents=True)
    case_rows=[]
    all_manifests=[]; all_exec=[]
    for case_id in cfg["candidate_case_ids"]:
        bundle=_build_case(cfg,source_root,lineage_root,case_id,plan_code_sha)
        _write_bundle(root/"cases"/case_id,bundle)
        case_rows.append({
            "case_id":case_id,
            "case_plan_hash":bundle["plan"]["plan_hash"],
            "domain_id":bundle["plan"]["domain_id"],
            "branch_count":2,
            "r7_p_envelope_hash":bundle["plan"]["r7_p_persistent_field_envelope_hash"],
            "r7_s_repair_application_hash":bundle["plan"]["r7_s_repair_application_hash"],
            "lineage_gate_hash":bundle["plan"]["lineage_gate_hash"],
        })
        all_manifests += bundle["arm_manifests"]
        all_exec += bundle["execution_rows"]

    batch={
        "schema":BATCH_PLAN_SCHEMA,
        "version":"0.1",
        "date":"2026-09-19",
        "case_count":4,
        "branch_count":8,
        "canonical_replicate_count":1,
        "canonical_arm_ids":["R7_P_PERSISTENT_SEMANTIC","R7_S_STRUCTURED_LINEAGE_REPAIR"],
        "n0_rerun_count":0,
        "r5_i_rerun_count":0,
        "case_rows":case_rows,
        "case_plan_hashes":[x["case_plan_hash"] for x in case_rows],
        "plan_code_sha":plan_code_sha,
        "paid_subject_authorization_status":"NOT_AUTHORIZED",
        "automatic_paid_evaluator":False,
        "semantic_cpr_status":"NOT_ADJUDICATED",
        "problematic_bias_status":"NOT_ESTABLISHED",
        "r5_unique_causal_attribution":"NOT_ESTABLISHED",
    }
    batch["batch_plan_hash"]=_hash_without(batch,"batch_plan_hash")
    _write(root/"batch_plan.json",batch)
    write_jsonl(root/"arm_manifests.jsonl",all_manifests)
    write_jsonl(root/"execution_rows.jsonl",all_exec)
    print("V5_4_R7_DUAL_PLAN=PREPARED")
    print("CASE_COUNT=4")
    print("BRANCH_COUNT=8")
    print("N0_RERUN_COUNT=0")
    print("R5_I_RERUN_COUNT=0")
    print("BATCH_PLAN_HASH="+batch["batch_plan_hash"])
    print("PAID_SUBJECT_AUTHORIZED=NO")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--config",required=True)
    ap.add_argument("--source-root",required=True)
    ap.add_argument("--lineage-root",required=True)
    ap.add_argument("--plan-code-sha",required=True)
    ap.add_argument("--outdir",required=True)
    a=ap.parse_args()
    prepare(a.config,a.source_root,a.lineage_root,a.plan_code_sha,a.outdir)


if __name__=="__main__":
    main()
