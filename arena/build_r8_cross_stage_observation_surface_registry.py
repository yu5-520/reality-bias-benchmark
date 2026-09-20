#!/usr/bin/env python3
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path


def stable_hash(obj):
    return hashlib.sha256(
        json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def iter_jsonl(path):
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def build_surface(trace, wave_id):
    exe=trace.get("execution_ledger") or []
    roles=[x.get("agent_id") for x in exe]
    counts=collections.Counter(roles)
    role_reentry_count=sum(max(0,n-1) for n in counts.values())

    reviewer_turns=[x.get("turn") for x in exe if x.get("agent_id")=="reviewer"]
    first_review=min(reviewer_turns) if reviewer_turns else None
    before={x.get("agent_id") for x in exe if first_review and x.get("turn") < first_review}
    after=[x for x in exe if first_review and x.get("turn") > first_review]
    post_review_reentry=sorted({x.get("agent_id") for x in after if x.get("agent_id") in before})
    post_review_new=sorted({
        x.get("agent_id") for x in after
        if x.get("agent_id") not in before and x.get("agent_id") != "reviewer"
    })

    events=trace.get("events") or []
    action_counts=collections.Counter(x.get("action_type") for x in events)
    post_review_invokes=sum(
        1 for x in events
        if first_review and x.get("turn") and x.get("turn") > first_review
        and x.get("action_type")=="invoke_agent"
    )
    reviewer_invokes=sum(
        1 for x in events
        if x.get("actor")=="reviewer" and x.get("action_type")=="invoke_agent"
    )

    row={
        "schema":"RB-R8-CROSS-STAGE-NATURAL-TRACE-SURFACE-v0.1",
        "wave_id":wave_id,
        "run_id":trace.get("run_id"),
        "domain_id":trace.get("domain_id"),
        "turn_count":len(exe),
        "available_agent_count":trace.get("available_agent_count"),
        "activated_agent_count":trace.get("activated_agent_count"),
        "total_invocations":trace.get("total_invocations"),
        "role_reentry_count":role_reentry_count,
        "reviewer_turn_count":len(reviewer_turns),
        "first_reviewer_turn":first_review,
        "post_review_reentry_agents":post_review_reentry,
        "post_review_new_agents":post_review_new,
        "reviewer_invoke_count":reviewer_invokes,
        "post_review_invoke_count":post_review_invokes,
        "write_state_event_count":action_counts.get("write_state",0),
        "revise_final_state_event_count":action_counts.get("revise_final_state",0),
        "invoke_agent_event_count":action_counts.get("invoke_agent",0),
        "send_message_event_count":action_counts.get("send_message",0),
        "observation_surfaces":{
            "C_information":"NATURAL_SHARED_STATE_AND_SEMANTIC_PROPAGATION_SURFACE",
            "P_collaboration_execution":(
                "NATURAL_AGENT_SCOPE_REENTRY_AND_EXPANSION_SURFACE"
                if role_reentry_count or post_review_new else "NATURAL_PROCESS_SURFACE"
            ),
            "R_temporal":(
                "NATURAL_REVIEW_REENTRY_SURFACE"
                if first_review and (post_review_reentry or post_review_new or post_review_invokes)
                else ("NATURAL_REVIEW_SURFACE" if first_review else "NO_EXPLICIT_REVIEW_BOUNDARY_IN_STRUCTURAL_SCAN")
            ),
        },
        "semantic_cpr_status":"NOT_ADJUDICATED",
    }
    row["surface_hash"]=stable_hash(row)
    return row


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--natural-traces", action="append", required=True,
                    help="wave_id:path/to/traces.jsonl; repeat six times")
    ap.add_argument("--out", required=True)
    a=ap.parse_args()

    rows=[]
    for spec in a.natural_traces:
        wave_s,path=spec.split(":",1)
        for trace in iter_jsonl(path):
            rows.append(build_surface(trace,int(wave_s)))

    rows.sort(key=lambda x:(x["domain_id"],x["wave_id"],x["run_id"]))
    if len(rows)!=90:
        raise SystemExit(f"expected_90_natural_traces_got_{len(rows)}")

    out=Path(a.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(
        "".join(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n" for x in rows),
        encoding="utf-8",
    )
    print("NATURAL_TRACE_SURFACES=90")
    print("SEMANTIC_CPR_STATUS=NOT_ADJUDICATED")
    print("SUBJECT_RERUN_REQUIRED=NO")


if __name__=="__main__":
    main()
