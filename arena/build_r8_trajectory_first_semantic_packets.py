#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


PACKET_SCHEMA = "RB-R8-TRAJECTORY-SEMANTIC-AUDIT-PACKET-v0.1"


def stable_hash(obj):
    return hashlib.sha256(
        json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def iter_jsonl(path):
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def extract_task_goal(trace):
    for m in trace.get("message_ledger") or []:
        if m.get("message_type") == "task_start":
            c=m.get("content")
            if isinstance(c,dict) and "content" in c:
                return c["content"]
            return c
    # Fallback: recover goal from the first frozen model-call user payload.
    calls=trace.get("model_calls") or []
    if calls:
        for msg in calls[0].get("messages") or []:
            if msg.get("role")!="user":
                continue
            content=msg.get("content")
            if not isinstance(content,str):
                continue
            try:
                payload=json.loads(content)
                if isinstance(payload,dict) and "goal" in payload:
                    return payload["goal"]
            except Exception:
                pass
    return None


def extract_initial_context(trace):
    calls=trace.get("model_calls") or []
    if not calls:
        return None
    for msg in calls[0].get("messages") or []:
        if msg.get("role")!="user" or not isinstance(msg.get("content"),str):
            continue
        try:
            payload=json.loads(msg["content"])
        except Exception:
            continue
        if isinstance(payload,dict):
            return {
                "public_context":payload.get("public_context"),
                "your_private_context":payload.get("your_private_context"),
                "shared_state":payload.get("shared_state"),
                "shared_state_metadata":payload.get("shared_state_metadata"),
                "active_agents":payload.get("active_agents"),
                "available_specialists":payload.get("available_specialists"),
            }
    return None


def build_state_timeline(trace):
    out=[]
    for e in trace.get("events") or []:
        before=e.get("shared_state_before")
        after=e.get("shared_state_after")
        fbefore=e.get("final_state_before")
        fafter=e.get("final_state_after")
        if before != after or fbefore != fafter or e.get("action_type") in {"write_state","revise_final_state","finalize"}:
            out.append({
                "event_index":e.get("event_index"),
                "turn":e.get("turn"),
                "actor":e.get("actor"),
                "action_type":e.get("action_type"),
                "authority_class":e.get("authority_class"),
                "shared_state_before":before,
                "shared_state_after":after,
                "shared_state_metadata_before":e.get("shared_state_metadata_before"),
                "shared_state_metadata_after":e.get("shared_state_metadata_after"),
                "final_state_before":fbefore,
                "final_state_after":fafter,
                "note":e.get("note"),
            })
    return out


def detect_structural_retrospective_boundaries(trace):
    # These are indexing hints only. They are not R verdicts.
    rows=[]
    condition=trace.get("r7_condition")
    if condition:
        rows.append({
            "kind":"R7_CONDITION_BOUNDARY",
            "evidence":condition,
            "semantic_status":"STRUCTURAL_INDEX_ONLY",
        })
    for seq_name in ("runtime_transform_records","action_transform_records"):
        for rec in trace.get(seq_name) or []:
            text=json.dumps(rec,ensure_ascii=False).lower()
            if any(x in text for x in ("repair","reopen","recompute","rollback","invalidate","review")):
                rows.append({
                    "kind":"TRANSFORM_OR_CONTROL_BOUNDARY",
                    "source":seq_name,
                    "evidence":rec,
                    "semantic_status":"STRUCTURAL_INDEX_ONLY",
                })
    return rows


def classify_termination(trace):
    reason=trace.get("termination_reason")
    censored=bool(trace.get("observation_censored"))
    remaining=list(trace.get("remaining_queue") or [])
    pending=list(trace.get("pending_invocations") or [])
    unread=list(trace.get("unread_messages") or [])
    active=bool(remaining or pending or unread)
    if censored and active:
        cls="EXTERNALLY_CENSORED_ACTIVE_PROCESS"
    elif reason=="queue_empty_with_final_state" and not active:
        cls="NATURAL_COMPLETE"
    elif trace.get("condition_complete") and not active:
        cls="CONTROL_BOUNDARY_COMPLETE"
    elif reason and "fail" in str(reason).lower():
        cls="FAILURE_TERMINATED"
    elif censored:
        cls="EXTERNALLY_CENSORED_PROCESS"
    else:
        cls="OTHER_RECORDED_TERMINATION"
    return {
        "classification":cls,
        "termination_reason":reason,
        "run_status":trace.get("run_status"),
        "condition_complete":trace.get("condition_complete"),
        "observation_censored":censored,
        "turns":trace.get("turns"),
        "budget_hits":trace.get("budget_hits"),
        "budget_limits":trace.get("budget_limits"),
        "experimental_stop_policy":trace.get("experimental_stop_policy"),
        "observation_policy":trace.get("observation_policy"),
    }


def build_packet(trace, source_stage, source_ref):
    run_id=str(trace.get("run_id"))
    packet={
        "schema":PACKET_SCHEMA,
        "packet_id":"R8T:"+hashlib.sha256((source_stage+"|"+run_id).encode()).hexdigest()[:20],
        "run_id":run_id,
        "source_stage":source_stage,
        "domain_id":trace.get("domain_id"),
        "condition":trace.get("r7_condition") or trace.get("subject_condition"),
        "task_goal":extract_task_goal(trace),
        "initial_context":extract_initial_context(trace),
        "chronological_execution":trace.get("execution_ledger") or [],
        "message_ledger":trace.get("message_ledger") or [],
        "invocation_ledger":trace.get("invocation_ledger") or [],
        "event_ledger":trace.get("events") or [],
        "model_calls":trace.get("model_calls") or [],
        "state_timeline":build_state_timeline(trace),
        "final_result":trace.get("final_state"),
        "retrospective_boundaries":detect_structural_retrospective_boundaries(trace),
        "termination_censor_state":classify_termination(trace),
        "remaining_work":{
            "remaining_queue":trace.get("remaining_queue") or [],
            "pending_invocations":trace.get("pending_invocations") or [],
            "unread_messages":trace.get("unread_messages") or [],
            "failures":trace.get("failures") or [],
        },
        "evidence_binding":{
            "source_ref":source_ref,
            "task_hash":trace.get("task_hash"),
            "trace_schema_version":trace.get("trace_schema_version"),
            "code_commit_sha":trace.get("code_commit_sha"),
            "arena_config_hash":trace.get("arena_config_hash"),
            "theory_contract_hash":trace.get("theory_contract_hash"),
            "model_config_hash":trace.get("model_config_hash"),
            "agent_registry_hash":trace.get("agent_registry_hash"),
        },
        "semantic_status":"NOT_ADJUDICATED_TRAJECTORY_FIRST",
    }
    packet["evidence_binding"]["packet_hash"]=stable_hash(packet)
    return packet


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--trace-source",action="append",required=True,
                    help="SOURCE_STAGE:SOURCE_REF:PATH_TO_TRACES_JSONL; repeat as needed")
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    packets=[]
    for spec in a.trace_source:
        stage,source_ref,path=spec.split(":",2)
        for trace in iter_jsonl(path):
            packets.append(build_packet(trace,stage,source_ref))
    packets.sort(key=lambda x:(x["source_stage"],x["domain_id"] or "",x["run_id"]))
    out=Path(a.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(
        "".join(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n" for x in packets),
        encoding="utf-8",
    )
    censored=sum(1 for x in packets if x["termination_censor_state"]["classification"]=="EXTERNALLY_CENSORED_ACTIVE_PROCESS")
    print("R8_TRAJECTORY_PACKETS="+str(len(packets)))
    print("ACTIVE_CENSORED_PACKETS="+str(censored))
    print("SEMANTIC_VERDICTS_EMITTED=0")
    print("SUBJECT_RERUN_REQUIRED=NO")


if __name__=="__main__":
    main()
