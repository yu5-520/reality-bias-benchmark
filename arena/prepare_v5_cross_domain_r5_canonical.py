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
    INTERVENTION_CONDITION,
    build_one_shot_envelope,
    make_branch_manifest_v3,
    verify_branch_manifest_v3,
)
from .prepare_v5_cross_domain_r5_first_wave import _event_index, _load_snapshot, _one

PLAN_SCHEMA="RB-V5-CROSS-DOMAIN-R5-CANONICAL-EXECUTION-PLAN-v0.1"


def _require(ok,message):
    if not ok:
        raise ValueError(message)


def _hash_without(row,key):
    material=copy.deepcopy(row)
    material.pop(key,None)
    return stable_hash(material)


def prepare(*,case_config_path:str,source_manifest_path:str,source_root:str,branch_code_sha:str):
    cfg=load_json(case_config_path)
    selected=list(cfg.get("selected_cases") or [])
    provider_name=((cfg.get("budget") or {}).get("provider") or "deepseek")
    _require(bool(selected),"r5_canonical_selected_cases_required")
    source_manifest=load_jsonl(source_manifest_path)
    manifest_by_run={row["run_id"]:row for row in source_manifest}
    _require(len(manifest_by_run)==len(source_manifest),"r5_canonical_source_manifest_run_collision")

    cases=[]; rows=[]; manifests=[]; payloads={}
    for expected in selected:
        wave_id=int(expected["wave_id"])
        run_id=expected["source_run_id"]
        _require(run_id in manifest_by_run,f"r5_canonical_source_manifest_missing:{run_id}")
        manifest_row=manifest_by_run[run_id]
        _require(int(manifest_row["wave_id"])==wave_id,f"r5_canonical_wave_mismatch:{run_id}")
        _require(manifest_row["domain_id"]==expected["domain_id"],f"r5_canonical_domain_mismatch:{run_id}")

        trace_path=_one(Path(source_root).rglob(f"wave-{wave_id}/raw/traces.jsonl"),f"r5_canonical_wave_{wave_id}_traces")
        traces=[row for row in load_jsonl(trace_path) if row.get("run_id")==run_id]
        _require(len(traces)==1,f"r5_canonical_source_trace_not_unique:{run_id}")
        trace=traces[0]
        source_trace_hash=stable_hash(trace)

        idx=_event_index(expected["candidate_ref"])
        events=[e for e in trace.get("events") or [] if e.get("event_index")==idx]
        _require(len(events)==1,f"r5_canonical_source_event_not_unique:{run_id}:{idx}")
        event=events[0]; action=event.get("action") or {}
        state_key=expected["state_key"]
        _require(event.get("action_type")=="write_state",f"r5_canonical_requires_write_state:{run_id}")
        _require(action.get("key")==state_key,f"r5_canonical_state_key_mismatch:{run_id}")
        _require(action.get("status")=="fact",f"r5_canonical_source_status_not_fact:{run_id}")
        recomputed=stable_hash({
            "state_key":state_key,
            "value_hash":stable_hash(action.get("value")),
            "source_event_index":idx,
            "source_actor":event.get("actor"),
        })
        _require(recomputed==expected["content_address"],f"r5_canonical_content_address_mismatch:{run_id}")

        snapshot_path=trace_path.parent/"snapshots"/f"{run_id}.jsonl"
        _require(snapshot_path.exists(),f"r5_canonical_snapshot_missing:{run_id}")
        parent=_load_snapshot(snapshot_path,expected["parent_anchor_ref"])
        verify_state_snapshot(parent)
        _require(parent["state_hash"]==expected["parent_state_hash"],f"r5_canonical_parent_hash_mismatch:{run_id}")
        _require(parent.get("terminated") is False and bool(parent.get("queue")),f"r5_canonical_parent_not_resumable:{run_id}")
        _require(parent["queue"][0]==expected["expected_next_actor"],f"r5_canonical_next_actor_mismatch:{run_id}")
        _require((parent.get("shared_state_metadata") or {})[state_key].get("status")=="fact",f"r5_canonical_parent_target_not_fact:{run_id}")

        envelope=build_one_shot_envelope(
            target_jump_ref=expected["candidate_ref"],
            target_candidate_id=expected["source_case_hash"],
            state_key=state_key,
            source_event_index=idx,
            from_status="fact",
            to_status="unconfirmed",
        )
        case_id=f"wave-{wave_id}-{expected['source_case_hash'][:12]}"
        model_identity={
            "provider":provider_name,
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
        code_identity={
            "source_natural_commit":manifest_row["code_commit_sha"],
            "branch_execution_commit":branch_code_sha,
        }
        branch_id=f"r5-canonical:{case_id}:one-shot"
        bm=make_branch_manifest_v3(
            branch_id=branch_id,
            condition_id=INTERVENTION_CONDITION,
            parent_trace_hash=source_trace_hash,
            parent_snapshot=parent,
            envelope=envelope,
            replicate_index=1,
            model_identity=model_identity,
            config_identity=config_identity,
            code_identity=code_identity,
        )
        verify_branch_manifest_v3(bm,parent_snapshot=parent,envelope=envelope)

        case={
            "schema":"RB-R5-CANONICAL-CASE-PLAN-v0.1",
            "case_id":case_id,
            "wave_id":wave_id,
            "domain_id":expected["domain_id"],
            "source_run_id":run_id,
            "source_case_hash":expected["source_case_hash"],
            "source_audit_hash":expected.get("audit_hash"),
            "source_trace_hash":source_trace_hash,
            "candidate_ref":expected["candidate_ref"],
            "content_address":expected["content_address"],
            "state_key":state_key,
            "source_event_index":idx,
            "source_turn":int(expected["source_turn"]),
            "natural_reference":{
                "run_id":run_id,
                "trace_hash":source_trace_hash,
                "role":"N0_FROZEN_NATURAL_CONTINUATION",
                "rerun_required":False,
            },
            "parent_anchor_ref":expected["parent_anchor_ref"],
            "parent_state_hash":parent["state_hash"],
            "expected_first_resume_actor":parent["queue"][0],
            "one_shot_envelope_hash":envelope["envelope_hash"],
            "branch_hash":bm["branch_hash"],
            "model_identity":model_identity,
            "config_identity":config_identity,
            "code_identity":code_identity,
            "parent_snapshot_path":f"cases/{case_id}/parent_snapshot.json",
            "envelope_path":f"cases/{case_id}/one_shot_envelope.json",
        }
        case["case_binding_hash"]=stable_hash(case)
        row={
            "run_id":branch_id,
            "case_id":case_id,
            "wave_id":wave_id,
            "domain_id":expected["domain_id"],
            "source_run_id":run_id,
            "source_case_hash":expected["source_case_hash"],
            "source_audit_hash":expected.get("audit_hash"),
            "natural_reference_run_id":run_id,
            "natural_reference_trace_hash":source_trace_hash,
            "condition_id":INTERVENTION_CONDITION,
            "replicate_index":1,
            "logical_seed":1,
            "branch_hash":bm["branch_hash"],
            "parent_state_hash":parent["state_hash"],
            "branch_execution_code_commit_sha":branch_code_sha,
            "canonical_r5":True,
            "synthetic_control":False,
            "automatic_paid_evaluator":False,
            "r6_new_subject_experiment":False,
            "r7_repair_authorized":False,
            "r8_cpr_adjudication":False,
        }
        cases.append(case); rows.append(row); manifests.append(bm); payloads[case_id]=(parent,envelope)

    cases.sort(key=lambda r:(r["wave_id"],r["case_id"]))
    rows.sort(key=lambda r:(r["wave_id"],r["case_id"]))
    _require(len({c["case_id"] for c in cases})==len(cases),"r5_canonical_case_collision")
    _require(len(rows)==len(cases) and len(manifests)==len(cases),"r5_canonical_branch_count_must_equal_case_count")
    plan={
        "schema":PLAN_SCHEMA,
        "version":"0.1",
        "status":"PREPARED_CANONICAL_R5_NOT_SELF_AUTHORIZED",
        "branch_execution_commit":branch_code_sha,
        "case_count":len(cases),
        "branch_count":len(rows),
        "existing_natural_reference_count":len(cases),
        "synthetic_control_branch_count":0,
        "canonical_intervention_branch_count":len(cases),
        "canonical_replicate_count":1,
        "new_provider_branches_per_case":1,
        "natural_reference_rerun_required":False,
        "condition_ids":[INTERVENTION_CONDITION],
        "automatic_paid_evaluator":False,
        "r6_new_subject_experiment":False,
        "r7_repair_authorized":False,
        "r8_cpr_adjudication":False,
        "authorization_status":"NOT_AUTHORIZED",
        "case_binding_hashes":[c["case_binding_hash"] for c in cases],
        "branch_hashes":[m["branch_hash"] for m in manifests],
    }
    plan["plan_hash"]=_hash_without(plan,"plan_hash")
    return plan,cases,rows,manifests,payloads


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--case-config",required=True)
    ap.add_argument("--source-manifest",required=True)
    ap.add_argument("--source-root",required=True)
    ap.add_argument("--branch-code-sha",required=True)
    ap.add_argument("--outdir",required=True)
    args=ap.parse_args()
    plan,cases,rows,manifests,payloads=prepare(
        case_config_path=args.case_config,
        source_manifest_path=args.source_manifest,
        source_root=args.source_root,
        branch_code_sha=args.branch_code_sha,
    )
    out=Path(args.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_r5_canonical_plan")
    out.mkdir(parents=True)
    (out/"plan.json").write_text(json.dumps(plan,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    write_jsonl(out/"case_bindings.jsonl",cases)
    write_jsonl(out/"branch_execution_manifest.jsonl",rows)
    write_jsonl(out/"branch_manifests.jsonl",manifests)
    for case in cases:
        d=out/"cases"/case["case_id"]; d.mkdir(parents=True)
        parent,envelope=payloads[case["case_id"]]
        (d/"parent_snapshot.json").write_text(json.dumps(parent,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        (d/"one_shot_envelope.json").write_text(json.dumps(envelope,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("V5_R5_CANONICAL_PREPARED=YES")
    print("CASE_COUNT="+str(plan["case_count"]))
    print("BRANCH_COUNT="+str(plan["branch_count"]))
    print("SYNTHETIC_CONTROL_BRANCH_COUNT=0")
    print("CANONICAL_REPLICATE_COUNT=1")
    print("PLAN_HASH="+plan["plan_hash"])


if __name__=="__main__":
    main()
