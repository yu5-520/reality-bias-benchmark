#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from .core import stable_hash
from .experimental_control import verify_state_snapshot
from .io_utils import load_json, load_jsonl, write_jsonl
from .one_shot_intervention import (
    CONTROL_CONDITION,
    INTERVENTION_CONDITION,
    build_one_shot_envelope,
    make_branch_manifest_v3,
    verify_branch_manifest_v3,
)
from .prepare_v5_cross_domain_r5_first_wave import _event_index, _hash_without, _one, _load_snapshot

PLAN_SCHEMA = "RB-V5-CROSS-DOMAIN-R5-SECOND-WAVE-EXECUTION-PLAN-v0.1"
ACTIVE_WAVES = (1,3,4,5,6)


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def _select(records: list[dict], excluded: set[str]) -> list[dict]:
    out=[]
    for wave_id in ACTIVE_WAVES:
        rows=[
            r for r in records
            if int(r.get("wave_id"))==wave_id
            and r.get("source_case_hash") not in excluded
            and r.get("r5_scientific_eligibility")=="ELIGIBLE_R5_ATOMIC_PROBE"
            and r.get("r5_existing_operator_compatibility")=="FACT_TO_UNCONFIRMED_COMPATIBLE"
            and (r.get("source") or {}).get("status")=="fact"
        ]
        _require(bool(rows),f"r5_second_no_remaining_eligible_case_for_wave:{wave_id}")
        rows.sort(key=lambda r:(_event_index(r["candidate_ref"]),r["source_run_id"],r["source_case_hash"]))
        out.append(rows[0])
    wave2=[
        r for r in records
        if int(r.get("wave_id"))==2
        and r.get("source_case_hash") not in excluded
        and r.get("r5_scientific_eligibility")=="ELIGIBLE_R5_ATOMIC_PROBE"
        and r.get("r5_existing_operator_compatibility")=="FACT_TO_UNCONFIRMED_COMPATIBLE"
        and (r.get("source") or {}).get("status")=="fact"
    ]
    _require(not wave2,"r5_second_wave2_must_be_exhausted")
    return out


def prepare(*,audit_records_path:str,source_manifest_path:str,source_root:str,plan_config_path:str,branch_code_sha:str):
    cfg=load_json(plan_config_path)
    _require(cfg.get("schema")=="RB-V5-CROSS-DOMAIN-R5-SECOND-WAVE-PLAN-v0.1","r5_second_plan_config_schema_invalid")
    _require(cfg["wave_status"]["2"]=="EXHAUSTED_AFTER_WAVE1","r5_second_wave2_status_invalid")
    excluded=set(cfg["exclude_first_wave_case_hashes"])
    _require(len(excluded)==6,"r5_second_exclusion_set_invalid")
    audits=load_jsonl(audit_records_path)
    source_manifest=load_jsonl(source_manifest_path)
    selected=_select(audits,excluded)
    frozen={int(row["wave_id"]):row for row in cfg["selected_cases"]}
    _require(set(frozen)==set(ACTIVE_WAVES),"r5_second_frozen_wave_set_invalid")
    manifest_by_run={row["run_id"]:row for row in source_manifest}
    _require(len(manifest_by_run)==90,"r5_second_source_manifest_must_have_90_rows")

    cases=[]; branches=[]; manifests=[]; payloads={}
    for audit in selected:
        wave_id=int(audit["wave_id"])
        expected=frozen[wave_id]
        for field in ("domain_id","source_run_id","source_case_hash","audit_hash","candidate_ref","content_address"):
            _require(audit.get(field)==expected.get(field),f"r5_second_frozen_selection_mismatch:{wave_id}:{field}")
        source=audit["source"]
        _require(int(source["turn"])==int(expected["source_turn"]),f"r5_second_source_turn_mismatch:{wave_id}")
        _require(source["state_key"]==expected["state_key"],f"r5_second_state_key_mismatch:{wave_id}")
        _require(source["status"]=="fact",f"r5_second_source_status_not_fact:{wave_id}")

        run_id=audit["source_run_id"]
        _require(run_id in manifest_by_run,f"r5_second_source_manifest_row_missing:{run_id}")
        manifest_row=manifest_by_run[run_id]
        _require(int(manifest_row["wave_id"])==wave_id,f"r5_second_source_wave_mismatch:{run_id}")
        _require(manifest_row["domain_id"]==audit["domain_id"],f"r5_second_source_domain_mismatch:{run_id}")
        _require(manifest_row["code_commit_sha"]==cfg["source_subject"]["execution_sha"],"r5_second_source_execution_sha_mismatch")

        trace_path=_one(Path(source_root).rglob(f"wave-{wave_id}/raw/traces.jsonl"),f"second_wave_{wave_id}_traces")
        traces=[row for row in load_jsonl(trace_path) if row.get("run_id")==run_id]
        _require(len(traces)==1,f"r5_second_source_trace_not_unique:{run_id}")
        trace=traces[0]
        source_trace_hash=stable_hash(trace)

        idx=_event_index(audit["candidate_ref"])
        events=[e for e in trace.get("events") or [] if e.get("event_index")==idx]
        _require(len(events)==1,f"r5_second_source_event_not_unique:{run_id}:{idx}")
        event=events[0]; action=event.get("action") or {}
        _require(event.get("action_type")=="write_state",f"r5_second_requires_write_state:{run_id}")
        _require(action.get("key")==source["state_key"],f"r5_second_source_event_key_mismatch:{run_id}")
        _require(action.get("status")=="fact",f"r5_second_source_event_status_not_fact:{run_id}")
        recomputed=stable_hash({
            "state_key":source["state_key"],
            "value_hash":stable_hash(action.get("value")),
            "source_event_index":idx,
            "source_actor":event.get("actor"),
        })
        _require(recomputed==audit["content_address"],f"r5_second_content_address_mismatch:{run_id}")

        snapshot_path=trace_path.parent/"snapshots"/f"{run_id}.jsonl"
        _require(snapshot_path.exists(),f"r5_second_snapshot_missing:{run_id}")
        parent=_load_snapshot(snapshot_path,expected["parent_anchor_ref"])
        _require(parent["state_hash"]==expected["parent_state_hash"],f"r5_second_parent_hash_mismatch:{run_id}")
        _require(parent.get("terminated") is False and bool(parent.get("queue")),f"r5_second_parent_not_resumable:{run_id}")
        _require(parent["queue"][0]==expected["expected_next_actor"],f"r5_second_next_actor_mismatch:{run_id}")
        _require((parent.get("shared_state_metadata") or {})[source["state_key"]].get("status")=="fact",f"r5_second_parent_target_not_fact:{run_id}")

        envelope=build_one_shot_envelope(
            target_jump_ref=audit["candidate_ref"],
            target_candidate_id=audit["source_case_hash"],
            state_key=source["state_key"],
            source_event_index=idx,
            from_status="fact",
            to_status="unconfirmed",
        )
        case_id=f"wave-{wave_id}-{audit['source_case_hash'][:12]}"
        model_identity={
            "provider":"deepseek",
            "model_config_path":manifest_row["model_config_path"],
            "model_config_hash":manifest_row["model_config_hash"],
        }
        config_identity={
            "arena_config_path":manifest_row["arena_config_path"],
            "arena_config_hash":manifest_row["arena_config_hash"],
            "domain_id":manifest_row["domain_id"],
            "domain_hash":manifest_row["domain_hash"],
            "task_hash":manifest_row["task_hash"],
            "agent_pool_hash":manifest_row["agent_pool_hash"],
        }
        code_identity={"source_natural_commit":manifest_row["code_commit_sha"],"branch_execution_commit":branch_code_sha}
        case={
            "case_id":case_id,"wave_id":wave_id,"domain_id":audit["domain_id"],
            "source_run_id":run_id,"source_case_hash":audit["source_case_hash"],
            "source_audit_hash":audit["audit_hash"],"source_trace_hash":source_trace_hash,
            "candidate_ref":audit["candidate_ref"],"content_address":audit["content_address"],
            "state_key":source["state_key"],"source_event_index":idx,"source_turn":int(source["turn"]),
            "parent_anchor_ref":expected["parent_anchor_ref"],"parent_state_hash":parent["state_hash"],
            "expected_first_resume_actor":parent["queue"][0],
            "model_identity":model_identity,"config_identity":config_identity,"code_identity":code_identity,
            "parent_snapshot_path":f"cases/{case_id}/parent_snapshot.json",
            "envelope_path":f"cases/{case_id}/one_shot_envelope.json",
        }
        case["case_binding_hash"]=stable_hash(case)
        cases.append(case); payloads[case_id]=(parent,envelope)

        for replicate in (1,2):
            order=(CONTROL_CONDITION,INTERVENTION_CONDITION) if replicate==1 else (INTERVENTION_CONDITION,CONTROL_CONDITION)
            pattern="CONTROL_FIRST" if replicate==1 else "INTERVENTION_FIRST"
            pair_id=f"{case_id}:pair:{replicate}"
            for execution_order,condition in enumerate(order,1):
                branch_id=f"{pair_id}:{condition.lower()}"
                bound=None if condition==CONTROL_CONDITION else envelope
                bm=make_branch_manifest_v3(
                    branch_id=branch_id,condition_id=condition,parent_trace_hash=source_trace_hash,
                    parent_snapshot=parent,envelope=bound,replicate_index=replicate,
                    model_identity=model_identity,config_identity=config_identity,code_identity=code_identity,
                )
                verify_branch_manifest_v3(bm,parent_snapshot=parent,envelope=bound)
                manifests.append(bm)
                branches.append({
                    "run_id":branch_id,"case_id":case_id,"wave_id":wave_id,"domain_id":audit["domain_id"],
                    "source_run_id":run_id,"source_case_hash":audit["source_case_hash"],"source_audit_hash":audit["audit_hash"],
                    "pair_id":pair_id,"replicate_index":replicate,"logical_seed":replicate,
                    "execution_order":execution_order,"pair_order_pattern":pattern,"condition_id":condition,
                    "branch_hash":bm["branch_hash"],"parent_state_hash":parent["state_hash"],
                    "branch_execution_code_commit_sha":branch_code_sha,"automatic_paid_evaluator":False,
                    "r6_new_subject_experiment":False,"r7_repair_authorized":False,"r8_cpr_adjudication":False,
                })

    cases.sort(key=lambda r:r["wave_id"])
    _require(len(cases)==5,"r5_second_case_count_must_be_5")
    _require(len(branches)==20 and len(manifests)==20,"r5_second_branch_count_must_be_20")
    plan={
        "schema":PLAN_SCHEMA,"version":"0.1","status":"PREPARED_ONLY_R5_NOT_SELF_AUTHORIZED",
        "source_plan_config_hash":stable_hash(cfg),
        "source_subject_workflow_run_id":cfg["source_subject"]["workflow_run_id"],
        "source_semantic_audit_workflow_run_id":cfg["source_semantic_audit"]["workflow_run_id"],
        "branch_execution_commit":branch_code_sha,"case_count":5,"replicate_pairs_per_case":2,"branch_count":20,
        "wave_ids":list(ACTIVE_WAVES),"exhausted_wave_ids":[2],
        "condition_ids":[CONTROL_CONDITION,INTERVENTION_CONDITION],
        "operator":cfg["operator"],"budget":cfg["budget"],"automatic_paid_evaluator":False,
        "r6_new_subject_experiment":False,"r7_repair_authorized":False,"r8_cpr_adjudication":False,
        "authorization_status":"NOT_AUTHORIZED",
        "case_binding_hashes":[c["case_binding_hash"] for c in cases],
        "branch_hashes":[m["branch_hash"] for m in manifests],
    }
    plan["plan_hash"]=_hash_without(plan,"plan_hash")
    return plan,cases,branches,manifests,payloads


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--audit-records",required=True)
    ap.add_argument("--source-manifest",required=True)
    ap.add_argument("--source-root",required=True)
    ap.add_argument("--plan-config",required=True)
    ap.add_argument("--branch-code-sha",required=True)
    ap.add_argument("--outdir",required=True)
    args=ap.parse_args()
    plan,cases,branches,manifests,payloads=prepare(
        audit_records_path=args.audit_records,source_manifest_path=args.source_manifest,
        source_root=args.source_root,plan_config_path=args.plan_config,branch_code_sha=args.branch_code_sha,
    )
    out=Path(args.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_r5_second_prepared_plan")
    out.mkdir(parents=True)
    (out/"plan.json").write_text(json.dumps(plan,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    write_jsonl(out/"case_bindings.jsonl",cases)
    write_jsonl(out/"branch_execution_manifest.jsonl",branches)
    write_jsonl(out/"branch_manifests.jsonl",manifests)
    for case in cases:
        case_dir=out/"cases"/case["case_id"]; case_dir.mkdir(parents=True)
        parent,envelope=payloads[case["case_id"]]
        (case_dir/"parent_snapshot.json").write_text(json.dumps(parent,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        (case_dir/"one_shot_envelope.json").write_text(json.dumps(envelope,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("V5_CROSS_DOMAIN_R5_SECOND_WAVE_PREPARED=YES")
    print("CASE_COUNT=5")
    print("BRANCH_COUNT=20")
    print("EXHAUSTED_WAVE_IDS=2")
    print("PLAN_HASH="+plan["plan_hash"])
    print("R5_PROVIDER_CALLS=0")


if __name__=="__main__":
    main()
