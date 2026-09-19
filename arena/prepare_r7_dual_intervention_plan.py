#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from .core import stable_hash
from .io_utils import load_json, write_jsonl
from .prepare_r7_three_arm_plan import (
    _write_json,
    build_r7_three_arm_plan,
    load_r5_plan_bundle,
    load_recovery_checkpoint,
    verify_r7_three_arm_plan,
)

PLAN_SCHEMA="RB-R7-DUAL-INTERVENTION-EXECUTION-PLAN-v0.1"
CANONICAL_MAP={
    "C2_PERSISTENT_FIELD":"R7_P_PERSISTENT_SEMANTIC",
    "C3_ALR":"R7_S_STRUCTURED_LINEAGE_REPAIR",
}


def _require(ok,message):
    if not ok:
        raise ValueError(message)


def _hash_without(row,key):
    material=copy.deepcopy(row)
    material.pop(key,None)
    return stable_hash(material)


def prepare(*,protocol,r5,checkpoint,semantic_repair_packet,lineage_completeness_gate,plan_code_sha):
    # Reuse already validated operator construction, but request exactly one historical
    # triad only as an internal construction adapter. C1 is discarded before the
    # canonical plan exists and is never an execution row.
    legacy=build_r7_three_arm_plan(
        protocol=protocol,
        r5=r5,
        checkpoint=checkpoint,
        semantic_repair_packet=semantic_repair_packet,
        lineage_completeness_gate=lineage_completeness_gate,
        replicates=1,
        plan_code_sha=plan_code_sha,
    )
    verify_r7_three_arm_plan(legacy)

    manifests=[]
    rows=[]
    for m in legacy["arm_manifests"]:
        if m["arm_id"] not in CANONICAL_MAP:
            continue
        mm=copy.deepcopy(m)
        mm["canonical_arm_id"]=CANONICAL_MAP[mm["arm_id"]]
        manifests.append(mm)
    manifest_hashes={m["manifest_hash"] for m in manifests}
    for r in legacy["execution_rows"]:
        if r["manifest_hash"] not in manifest_hashes:
            continue
        rr=copy.deepcopy(r)
        rr["canonical_arm_id"]=CANONICAL_MAP[rr["arm_id"]]
        rows.append(rr)

    _require(len(manifests)==len(rows)==2,"r7_dual_requires_exactly_two_execution_rows")
    _require({r["canonical_arm_id"] for r in rows}==set(CANONICAL_MAP.values()),"r7_dual_arm_set_invalid")
    _require({int(r["replicate_index"]) for r in rows}=={1},"r7_dual_replicate_must_be_one")

    base=legacy["plan"]
    plan={
        "schema":PLAN_SCHEMA,
        "version":"0.1",
        "case_id":protocol.get("case_id") or base.get("protocol_id"),
        "phase":"R7_CANONICAL_DUAL_INTERVENTION_PREPARED_ONLY",
        "scientific_status":"PREPARED_NOT_EXECUTED",
        "source_binding":copy.deepcopy(base["source_binding"]),
        "semantic_payload":copy.deepcopy(base["semantic_payload"]),
        "semantic_payload_hash":base["semantic_payload_hash"],
        "matched_horizon":copy.deepcopy(base["matched_horizon"]),
        "measurement_schema":base["measurement_schema"],
        "bounded_arena_config_hash":base["bounded_arena_config_hash"],
        "canonical_arm_ids":["R7_P_PERSISTENT_SEMANTIC","R7_S_STRUCTURED_LINEAGE_REPAIR"],
        "canonical_replicate_count":1,
        "branch_count":2,
        "branch_row_count":2,
        "new_provider_branch_count":2,
        "r5_c1_reference_execution_count":0,
        "r5_one_shot_reference_hash":base["c1_one_shot_envelope_hash"],
        "r5_reference_role":"FROZEN_R5_I_REFERENCE_NOT_RERUN",
        "r7_p_persistent_field_envelope_hash":base["c2_persistent_field_envelope_hash"],
        "r7_s_repair_binding_hash":base["c3_alr_binding_hash"],
        "r7_s_repaired_parent_state_hash":base["c3_repaired_parent_state_hash"],
        "r7_s_repair_application_hash":base["c3_repair_application_hash"],
        "semantic_repair_runtime_plan_hash":base["semantic_repair_runtime_plan_hash"],
        "semantic_lineage_package_hash":base["semantic_lineage_package_hash"],
        "post_repair_watch_contract_hash":base["post_repair_watch_contract_hash"],
        "semantic_repair_packet_hash":base["semantic_repair_packet_hash"],
        "lineage_completeness_gate_hash":base["lineage_completeness_gate_hash"],
        "semantic_repair_packet_id":base["semantic_repair_packet_id"],
        "repair_closure_refs":copy.deepcopy(base["repair_closure_refs"]),
        "evidence_supported_affected_closure_refs":copy.deepcopy(base["evidence_supported_affected_closure_refs"]),
        "manifest_hashes":[m["manifest_hash"] for m in manifests],
        "condition_isolation":{
            "R7_P":"same frozen post-source parent; persistent copied-runtime-view semantic correction on eligible downstream turns",
            "R7_S":"same evidence-bound case; structured semantic-lineage repair then selective downstream recomputation",
        },
        "code_identity":copy.deepcopy(base["code_identity"]),
        "provider_internal_state_replayed":False,
        "semantic_cpr_status":"NOT_ADJUDICATED",
        "paid_subject_authorization_status":"NOT_AUTHORIZED",
        "automatic_paid_evaluator":False,
        "real_dual_runtime_mechanisms_ready":True,
        "real_three_arm_runtime_mechanisms_ready":True,
        "real_subject_execution_authorized":False,
        "legacy_operator_adapter":{
            "used_to_construct_tested_C2_C3_operators":True,
            "C1_generated_in_adapter_but_excluded_before_canonical_plan":True,
            "C1_execution_row_present":False,
        },
    }
    plan["plan_hash"]=_hash_without(plan,"plan_hash")
    bundle=copy.deepcopy(legacy)
    bundle["plan"]=plan
    bundle["arm_manifests"]=manifests
    bundle["execution_rows"]=rows
    return bundle


def verify_r7_dual_plan(bundle):
    p=bundle["plan"]
    _require(p.get("schema")==PLAN_SCHEMA,"r7_dual_plan_schema_invalid")
    _require(p.get("plan_hash")==_hash_without(p,"plan_hash"),"r7_dual_plan_hash_mismatch")
    _require(p.get("canonical_arm_ids")==["R7_P_PERSISTENT_SEMANTIC","R7_S_STRUCTURED_LINEAGE_REPAIR"],"r7_dual_canonical_arm_order_invalid")
    _require(p.get("canonical_replicate_count")==1,"r7_dual_replicate_count_invalid")
    _require(p.get("branch_count")==p.get("branch_row_count")==p.get("new_provider_branch_count")==2,"r7_dual_branch_count_invalid")
    _require(p.get("r5_c1_reference_execution_count")==0,"r7_dual_must_not_execute_c1")
    _require(p.get("r5_reference_role")=="FROZEN_R5_I_REFERENCE_NOT_RERUN","r7_dual_r5_reference_role_invalid")
    _require(p.get("paid_subject_authorization_status")=="NOT_AUTHORIZED","r7_dual_must_not_self_authorize")
    _require(p.get("semantic_cpr_status")=="NOT_ADJUDICATED","r7_dual_cpr_boundary_invalid")
    rows=list(bundle["execution_rows"]); manifests=list(bundle["arm_manifests"])
    _require(len(rows)==len(manifests)==2,"r7_dual_bundle_geometry_invalid")
    _require({r["arm_id"] for r in rows}=={"C2_PERSISTENT_FIELD","C3_ALR"},"r7_dual_legacy_operator_arm_set_invalid")
    _require({r["canonical_arm_id"] for r in rows}==set(p["canonical_arm_ids"]),"r7_dual_canonical_row_set_invalid")
    _require(all(int(r["replicate_index"])==1 for r in rows),"r7_dual_row_replicate_invalid")
    return True


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--protocol",default="configs/r7/r7_three_arm_fixture.example.json")
    ap.add_argument("--r5-plan-dir",required=True)
    ap.add_argument("--source-snapshots",required=True)
    ap.add_argument("--semantic-repair-packet",required=True)
    ap.add_argument("--lineage-completeness-gate",required=True)
    ap.add_argument("--plan-code-sha",default="LOCAL_OR_UNRECORDED")
    ap.add_argument("--outdir",required=True)
    args=ap.parse_args()

    protocol=load_json(args.protocol)
    r5=load_r5_plan_bundle(args.r5_plan_dir)
    checkpoint=load_recovery_checkpoint(args.source_snapshots,protocol)
    packet=load_json(args.semantic_repair_packet)
    gate=load_json(args.lineage_completeness_gate)
    bundle=prepare(
        protocol=protocol,r5=r5,checkpoint=checkpoint,
        semantic_repair_packet=packet,lineage_completeness_gate=gate,
        plan_code_sha=args.plan_code_sha,
    )
    verify_r7_dual_plan(bundle)

    out=Path(args.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_r7_dual_plan_dir")
    out.mkdir(parents=True)
    _write_json(out/"r7_plan.json",bundle["plan"])
    _write_json(out/"source_parent_snapshot.json",bundle["source_parent_snapshot"])
    _write_json(out/"c3_recovery_checkpoint.json",bundle["c3_recovery_checkpoint"])
    _write_json(out/"c1_one_shot_envelope.json",bundle["c1_one_shot_envelope"])
    _write_json(out/"c2_persistent_field_envelope.json",bundle["c2_persistent_field_envelope"])
    _write_json(out/"c3_alr_binding.json",bundle["c3_alr_binding"])
    _write_json(out/"semantic_repair_runtime_plan.json",bundle["semantic_repair_runtime_plan"])
    _write_json(out/"c3_repaired_parent_snapshot.json",bundle["c3_repaired_parent_snapshot"])
    _write_json(out/"c3_repair_application.json",bundle["c3_repair_application"])
    _write_json(out/"semantic_repair_packet.json",bundle["semantic_repair_packet"])
    _write_json(out/"semantic_lineage_package.json",bundle["semantic_lineage_package"])
    _write_json(out/"post_repair_watch_contract.json",bundle["post_repair_watch_contract"])
    _write_json(out/"lineage_completeness_gate.json",bundle["lineage_completeness_gate"])
    _write_json(out/"r7_bounded_arena_config.json",bundle["bounded_arena_config"])
    write_jsonl(out/"arm_manifests.jsonl",bundle["arm_manifests"])
    write_jsonl(out/"execution_rows.jsonl",bundle["execution_rows"])

    print("R7_DUAL_PLAN=PREPARED")
    print("BRANCH_COUNT=2")
    print("CANONICAL_REPLICATE_COUNT=1")
    print("R5_C1_EXECUTION_COUNT=0")
    print("PLAN_HASH="+bundle["plan"]["plan_hash"])
    print("PAID_SUBJECT_AUTHORIZED=NO")


if __name__=="__main__":
    main()
