#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
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
from .prepare_v5_cross_domain_r5_first_wave import _event_index, _load_snapshot, _one

PLAN_SCHEMA = "RB-V5-CROSS-DOMAIN-R5-COVERAGE-EXTENSION-EXECUTION-PLAN-v0.1"


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def _hash_without(row, key):
    material=copy.deepcopy(row)
    material.pop(key,None)
    return stable_hash(material)


def prepare(*, audit_records_path, source_manifest_path, source_root, plan_config_path, branch_code_sha):
    cfg=load_json(plan_config_path)
    _require(cfg.get("schema")=="RB-V5-CROSS-DOMAIN-R5-COVERAGE-EXTENSION-PLAN-v0.1","r5_coverage_config_schema_invalid")
    audits=load_jsonl(audit_records_path)
    source_manifest=load_jsonl(source_manifest_path)
    frozen_hashes=list(cfg["selected_case_hashes"])
    _require(len(frozen_hashes)==23 and len(set(frozen_hashes))==23,"r5_coverage_frozen_hash_count_invalid")
    by_hash={a["source_case_hash"]:a for a in audits}
    _require(set(frozen_hashes).issubset(set(by_hash)),"r5_coverage_frozen_hash_missing_from_audit")
    selected=[by_hash[h] for h in frozen_hashes]
    for a in selected:
        _require(a.get("r5_scientific_eligibility")=="ELIGIBLE_R5_ATOMIC_PROBE","r5_coverage_case_not_eligible")
        _require(a.get("r5_existing_operator_compatibility")=="FACT_TO_UNCONFIRMED_COMPATIBLE","r5_coverage_case_operator_incompatible")
        _require((a.get("source") or {}).get("status")=="fact","r5_coverage_source_not_fact")
    _require(len({a["source_run_id"] for a in selected})==23,"r5_coverage_requires_unique_source_runs")
    _require(Counter(a["domain_id"] for a in selected)==Counter(cfg["domain_counts"]),"r5_coverage_domain_counts_mismatch")

    selected.sort(key=lambda a:(a["domain_id"],int(a["wave_id"]),a["source_run_id"],a["source_case_hash"]))
    manifest_by_run={row["run_id"]:row for row in source_manifest}
    _require(len(manifest_by_run)==90,"r5_coverage_source_manifest_must_have_90_rows")

    cases=[]; branches=[]; manifests=[]; payloads={}
    for index,audit in enumerate(selected,1):
        source=audit["source"]
        run_id=audit["source_run_id"]
        _require(run_id in manifest_by_run,f"r5_coverage_source_manifest_missing:{run_id}")
        mr=manifest_by_run[run_id]
        _require(mr["domain_id"]==audit["domain_id"],f"r5_coverage_domain_mismatch:{run_id}")
        _require(int(mr["wave_id"])==int(audit["wave_id"]),f"r5_coverage_wave_mismatch:{run_id}")
        _require(mr["code_commit_sha"]==cfg["source_subject"]["execution_sha"],"r5_coverage_source_sha_mismatch")

        trace_path=_one(Path(source_root).rglob(f"wave-{int(audit['wave_id'])}/raw/traces.jsonl"),f"coverage_wave_{audit['wave_id']}_traces")
        traces=[row for row in load_jsonl(trace_path) if row.get("run_id")==run_id]
        _require(len(traces)==1,f"r5_coverage_source_trace_not_unique:{run_id}")
        trace=traces[0]
        source_trace_hash=stable_hash(trace)

        event_index=_event_index(audit["candidate_ref"])
        events=[e for e in trace.get("events") or [] if e.get("event_index")==event_index]
        _require(len(events)==1,f"r5_coverage_source_event_not_unique:{run_id}:{event_index}")
        event=events[0]
        action=event.get("action") or {}
        _require(event.get("action_type")=="write_state",f"r5_coverage_requires_write_state:{run_id}")
        _require(action.get("key")==source["state_key"],f"r5_coverage_event_key_mismatch:{run_id}")
        _require(action.get("status")=="fact",f"r5_coverage_event_status_not_fact:{run_id}")
        recomputed_address=stable_hash({
            "state_key":source["state_key"],
            "value_hash":stable_hash(action.get("value")),
            "source_event_index":event_index,
            "source_actor":event.get("actor"),
        })
        _require(recomputed_address==audit["content_address"],f"r5_coverage_content_address_mismatch:{run_id}")

        anchor=f"after_turn:{int(source['turn'])}"
        snapshot_path=trace_path.parent/"snapshots"/f"{run_id}.jsonl"
        _require(snapshot_path.exists(),f"r5_coverage_snapshot_missing:{run_id}")
        parent=_load_snapshot(snapshot_path,anchor)
        _require(parent.get("terminated") is False,f"r5_coverage_parent_terminal:{run_id}")
        _require(bool(parent.get("queue")),f"r5_coverage_parent_queue_empty:{run_id}")
        key=source["state_key"]
        _require(parent.get("shared_state_metadata",{}).get(key,{}).get("status")=="fact",f"r5_coverage_parent_target_not_fact:{run_id}")

        envelope=build_one_shot_envelope(
            target_jump_ref=audit["candidate_ref"],
            target_candidate_id=audit["source_case_hash"],
            state_key=key,
            source_event_index=event_index,
            from_status="fact",
            to_status="unconfirmed",
        )
        case_id=f"coverage-{index:02d}-{audit['source_case_hash'][:12]}"
        model_identity={
            "provider":"deepseek",
            "model_config_path":mr["model_config_path"],
            "model_config_hash":mr["model_config_hash"],
        }
        config_identity={
            "arena_config_path":mr["arena_config_path"],
            "arena_config_hash":mr["arena_config_hash"],
            "domain_id":mr["domain_id"],
            "domain_hash":mr["domain_hash"],
            "task_hash":mr["task_hash"],
            "agent_pool_hash":mr["agent_pool_hash"],
        }
        code_identity={
            "source_natural_commit":mr["code_commit_sha"],
            "branch_execution_commit":branch_code_sha,
        }
        case={
            "case_id":case_id,
            "coverage_index":index,
            "wave_id":int(audit["wave_id"]),
            "domain_id":audit["domain_id"],
            "source_run_id":run_id,
            "source_case_hash":audit["source_case_hash"],
            "source_audit_hash":audit["audit_hash"],
            "source_trace_hash":source_trace_hash,
            "candidate_ref":audit["candidate_ref"],
            "content_address":audit["content_address"],
            "state_key":key,
            "source_event_index":event_index,
            "source_turn":int(source["turn"]),
            "parent_anchor_ref":anchor,
            "parent_state_hash":parent["state_hash"],
            "expected_first_resume_actor":parent["queue"][0],
            "model_identity":model_identity,
            "config_identity":config_identity,
            "code_identity":code_identity,
            "parent_snapshot_path":f"cases/{case_id}/parent_snapshot.json",
            "envelope_path":f"cases/{case_id}/one_shot_envelope.json",
        }
        case["case_binding_hash"]=stable_hash(case)
        cases.append(case)
        payloads[case_id]=(parent,envelope)

        order=(CONTROL_CONDITION,INTERVENTION_CONDITION) if index%2 else (INTERVENTION_CONDITION,CONTROL_CONDITION)
        pattern="CONTROL_FIRST" if index%2 else "INTERVENTION_FIRST"
        pair_id=f"{case_id}:pair:1"
        for execution_order,condition in enumerate(order,1):
            branch_id=f"{pair_id}:{condition.lower()}"
            bound=None if condition==CONTROL_CONDITION else envelope
            bm=make_branch_manifest_v3(
                branch_id=branch_id,
                condition_id=condition,
                parent_trace_hash=source_trace_hash,
                parent_snapshot=parent,
                envelope=bound,
                replicate_index=1,
                model_identity=model_identity,
                config_identity=config_identity,
                code_identity=code_identity,
            )
            verify_branch_manifest_v3(bm,parent_snapshot=parent,envelope=bound)
            manifests.append(bm)
            branches.append({
                "run_id":branch_id,
                "pair_id":pair_id,
                "case_id":case_id,
                "coverage_index":index,
                "wave_id":int(audit["wave_id"]),
                "domain_id":audit["domain_id"],
                "source_run_id":run_id,
                "source_case_hash":audit["source_case_hash"],
                "source_audit_hash":audit["audit_hash"],
                "replicate_index":1,
                "logical_seed":1,
                "execution_order":execution_order,
                "pair_order_pattern":pattern,
                "condition_id":condition,
                "branch_hash":bm["branch_hash"],
                "parent_state_hash":parent["state_hash"],
                "branch_execution_code_commit_sha":branch_code_sha,
                "automatic_paid_evaluator":False,
                "r6_followup_authorized":False,
                "r7_repair_authorized":False,
                "semantic_cpr_status":"NOT_ADJUDICATED",
            })

    _require(len(cases)==23 and len(branches)==46 and len(manifests)==46,"r5_coverage_geometry_invalid")
    plan={
        "schema":PLAN_SCHEMA,
        "version":"0.1",
        "status":"PREPARED_ONLY_R5_NOT_SELF_AUTHORIZED",
        "source_plan_config_hash":stable_hash(cfg),
        "source_subject_workflow_run_id":cfg["source_subject"]["workflow_run_id"],
        "source_semantic_audit_workflow_run_id":cfg["source_semantic_audit"]["workflow_run_id"],
        "branch_execution_commit":branch_code_sha,
        "case_count":23,
        "pair_count":23,
        "branch_count":46,
        "condition_ids":[CONTROL_CONDITION,INTERVENTION_CONDITION],
        "operator":cfg["operator"],
        "budget":cfg["budget"],
        "automatic_paid_evaluator":False,
        "r6_followup_authorized":False,
        "r7_repair_authorized":False,
        "semantic_cpr_status":"NOT_ADJUDICATED",
        "authorization_status":"NOT_AUTHORIZED",
        "case_binding_hashes":[x["case_binding_hash"] for x in cases],
        "branch_hashes":[x["branch_hash"] for x in manifests],
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
        audit_records_path=args.audit_records,
        source_manifest_path=args.source_manifest,
        source_root=args.source_root,
        plan_config_path=args.plan_config,
        branch_code_sha=args.branch_code_sha,
    )
    out=Path(args.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_r5_coverage_plan")
    out.mkdir(parents=True)
    (out/"plan.json").write_text(json.dumps(plan,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    write_jsonl(out/"case_bindings.jsonl",cases)
    write_jsonl(out/"branch_execution_manifest.jsonl",branches)
    write_jsonl(out/"branch_manifests.jsonl",manifests)
    for case in cases:
        d=out/"cases"/case["case_id"]
        d.mkdir(parents=True)
        parent,envelope=payloads[case["case_id"]]
        (d/"parent_snapshot.json").write_text(json.dumps(parent,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        (d/"one_shot_envelope.json").write_text(json.dumps(envelope,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("V5_CROSS_DOMAIN_R5_COVERAGE_PREPARED=YES")
    print("CASE_COUNT=23")
    print("PAIR_COUNT=23")
    print("BRANCH_COUNT=46")
    print("PLAN_HASH="+plan["plan_hash"])
    print("PAID_API_CALLED=NO")


if __name__=="__main__":
    main()
