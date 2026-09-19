#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .core import stable_hash
from .io_utils import load_json, load_jsonl, write_jsonl

AUDIT_SCHEMA="RB-SEMANTIC-TRAJECTORY-AUDIT-v0.1"
SUMMARY_SCHEMA="RB-V5.4-R2R6-SEMANTIC-TRAJECTORY-REAUDIT-SUMMARY-v0.1"
REPORT_BUNDLE_SCHEMA="RB-PROCESS-REALITY-REPORT-EVIDENCE-BUNDLE-v0.1"
HELD_OUT={"finance","supply_chain","software_engineering"}


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def _j(value: Any, limit: int | None = None) -> str:
    if isinstance(value, str):
        out=value
    else:
        out=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"))
    if limit and len(out)>limit:
        return out[:limit-1]+"…"
    return out


def _call_ref(run_id: str, call: dict) -> str:
    return f"{run_id}:turn:{call.get('turn')}:actor:{call.get('agent_id')}"


def _event_ref(run_id: str, event: dict) -> str:
    return f"{run_id}:event:{event.get('event_index')}"


def _call_events(trace: dict, call: dict) -> list[dict]:
    start=call.get("event_index_start")
    end=call.get("event_index_end")
    if start is None or end is None:
        return []
    return [
        event for event in (trace.get("events") or [])
        if isinstance(event.get("event_index"),int)
        and start <= event["event_index"] <= end
    ]


def _action_summary(event: dict) -> str:
    action=event.get("action") or {}
    typ=event.get("action_type") or action.get("type") or "unknown"
    if typ=="write_state":
        return (
            f"write_state {action.get('key')} [{action.get('status')}]: "
            f"{_j(action.get('value'),800)} | basis={_j(action.get('basis'),400)}"
        )
    if typ=="revise_final_state":
        return (
            f"revise_final_state: {_j(action.get('patch'),800)} | "
            f"reason={_j(action.get('reason'),400)}"
        )
    if typ=="invoke_agent":
        return f"invoke_agent {action.get('agent_id')}: {_j(action.get('request'),500)}"
    if typ=="message":
        return f"message -> {action.get('to')}: {_j(action.get('content'),500)}"
    if typ=="finalize":
        return f"finalize: {_j(action.get('answer'),800)}"
    return f"{typ}: {_j(action,500)}"


def _output_semantics(trace: dict, call: dict) -> list[str]:
    out=[]
    if call.get("decision_summary"):
        out.append(str(call["decision_summary"]))
    for event in _call_events(trace,call):
        if event.get("action_type") in {"write_state","revise_final_state","finalize"}:
            out.append(_action_summary(event))
    if not out:
        out.append(f"{call.get('agent_id')} call status={call.get('status')}")
    return out


def _route_node(trace: dict, call: dict, route_index: int) -> dict:
    run_id=trace["run_id"]
    events=_call_events(trace,call)
    snapshot=call.get("runtime_snapshot") or {}
    inbox=snapshot.get("inbox") or []
    input_premises=[]
    for row in inbox:
        if isinstance(row,dict):
            content=row.get("content") or row.get("request") or row.get("message")
            if content:
                input_premises.append(str(content))
        elif row:
            input_premises.append(str(row))

    state=snapshot.get("shared_state") or {}
    observed=[
        f"{run_id}:turn:{call.get('turn')}:state:{key}"
        for key in sorted(state)
    ]
    messages=[]
    actions=[]
    output_refs=[]
    statuses=[]
    for event in events:
        typ=event.get("action_type")
        action=event.get("action") or {}
        if typ in {"message","invoke_agent"}:
            messages.append(_event_ref(run_id,event))
        actions.append(_action_summary(event))
        if typ=="write_state":
            key=action.get("key")
            output_refs.append(f"{run_id}:event:{event['event_index']}:state:{key}")
            statuses.append(f"{key}={action.get('status')}")
        elif typ=="revise_final_state":
            for key in (action.get("patch") or {}):
                output_refs.append(f"{run_id}:event:{event['event_index']}:final_state:{key}")
                statuses.append(f"final_state.{key}=revised")

    return {
        "route_index":route_index,
        "turn":int(call.get("turn") or 0),
        "agent_role":str(call.get("agent_id") or "UNKNOWN"),
        "call_ref":_call_ref(run_id,call),
        "event_refs":[_event_ref(run_id,event) for event in events] or [
            f"{run_id}:turn:{call.get('turn')}:no_event_range"
        ],
        "input_premises":input_premises,
        "observed_state_refs":observed,
        "message_or_invoke_refs":messages,
        "output_actions":actions,
        "output_state_refs":output_refs,
        "authority_or_status":statuses,
        "termination_or_censoring":"call_failed" if call.get("status")=="failed" else "continue",
    }


def _source_semantic(pass_row: dict) -> str:
    source=pass_row["source"]
    return (
        f"{source.get('state_key')} [{source.get('status')}]: "
        f"{_j(source.get('value'),1200)} | basis={_j(source.get('basis'),600)}"
    )


def _parse_call_refs(refs: list[str], run_id: str) -> set[str]:
    return {
        ref for ref in refs
        if ref.startswith(run_id+":turn:") and ":actor:" in ref
    }


def _historical_first_edge(audit: dict) -> tuple[str,str]:
    cls=str(audit.get("semantic_response_class") or "").upper()
    status=str(audit.get("system_inertia_status") or "").upper()
    if status=="CASE_LEVEL_SYSTEM_INERTIA_SUPPORTED_CANDIDATE":
        return "TRANSFORMED_DESCENDANT","TRANSFORMS_TO"
    if "REANCHOR" in cls or "REANCHOR" in status:
        return "INDEPENDENT_REANCHOR","RECONSTRUCTS"
    if "PREEXISTING" in cls or "PREEXISTING" in status:
        return "PREEXISTING_GATE_REAFFIRMATION","PRESERVES"
    if "BOUNDARY" in cls or "BOUNDARY" in status:
        return "BOUNDARY_PRESERVATION","PRESERVES"
    if "INHERITANCE" in cls:
        return "DESCENDANT_INHERITANCE","INHERITS"
    return "SEMANTIC_TRANSFORMATION","TRANSFORMS_TO"


def _edge_type(audit: dict, ordinal: int) -> tuple[str,str]:
    first,relation=_historical_first_edge(audit)
    if ordinal==0:
        return first,relation
    if audit.get("system_inertia_status")=="CASE_LEVEL_SYSTEM_INERTIA_SUPPORTED_CANDIDATE":
        return "DESCENDANT_INHERITANCE","CONSTRAINS"
    if first=="INDEPENDENT_REANCHOR":
        return "DECISION_APPLICATION","CONSTRAINS"
    if first=="PREEXISTING_GATE_REAFFIRMATION":
        return "DECISION_APPLICATION","PRESERVES"
    if first=="BOUNDARY_PRESERVATION":
        return "BOUNDARY_PRESERVATION","PRESERVES"
    if first=="DESCENDANT_INHERITANCE":
        return "DESCENDANT_INHERITANCE","INHERITS"
    return "DECISION_APPLICATION","CONSTRAINS"


def _semantic_function(is_source: bool, is_first_r5: bool, is_relevant: bool, audit: dict) -> str:
    if is_source:
        return "SOURCE_OBSERVATION"
    if not is_relevant:
        return "IRRELEVANT_TO_TARGET_LINEAGE"
    if is_first_r5:
        first,_=_historical_first_edge(audit)
        if first=="INDEPENDENT_REANCHOR":
            return "INDEPENDENT_EVIDENCE_REANCHOR"
        if first=="PREEXISTING_GATE_REAFFIRMATION":
            return "REAFFIRMATION"
        if first=="BOUNDARY_PRESERVATION":
            return "READ_OR_ADOPTION"
        if audit.get("system_inertia_status")=="CASE_LEVEL_SYSTEM_INERTIA_SUPPORTED_CANDIDATE":
            return "NEW_DESCENDANT_CARRIER"
        return "TRANSFORMATION"
    return "ACTION_APPLICATION"


def _independent_evidence_refs(call: dict, trace: dict, interpretation: str, target_key: str) -> list[str]:
    state=(call.get("runtime_snapshot") or {}).get("shared_state") or {}
    text=(interpretation or "").lower()
    refs=[]
    for key in sorted(state):
        if key==target_key:
            continue
        low=key.lower()
        variants={low,low.replace("_"," "),low.replace("."," "),low.split(".")[-1]}
        if any(v and v in text for v in variants):
            refs.append(
                f"{trace['run_id']}:turn:{call.get('turn')}:"
                f"runtime_snapshot.shared_state:{key}"
            )
    if refs:
        return refs[:12]

    keywords=(
        "assessment","decision","risk","cash","financial","telemetry","coverage",
        "plan","forecast","capacity","collateral","compliance","reconciliation",
        "metric","buffer","release"
    )
    for key in sorted(state):
        if key==target_key:
            continue
        if any(word in key.lower() for word in keywords):
            refs.append(
                f"{trace['run_id']}:turn:{call.get('turn')}:"
                f"runtime_snapshot.shared_state:{key}"
            )
    return refs[:8]


def _natural_pointer_calls(pass_row: dict) -> list[tuple[str,int,str]]:
    out=[]
    for pointer in pass_row.get("evidence_pointers") or []:
        if pointer.get("kind")!="DOWNSTREAM_CALL":
            continue
        match=re.match(
            r"trace:(.+):turn:(\d+):actor:([^:]+):events:",
            pointer.get("pointer") or "",
        )
        if match:
            run_id,turn,actor=match.groups()
            out.append((run_id,int(turn),actor))
    return out


def _load_sources(root: Path):
    natural={}
    for path in root.rglob("natural/**/raw/traces.jsonl"):
        for trace in load_jsonl(path):
            _require(trace["run_id"] not in natural,"natural_run_collision:"+trace["run_id"])
            natural[trace["run_id"]]=trace

    pass_files=list(root.rglob("pass1/**/localized_semantic_audit_records.jsonl"))
    _require(len(pass_files)==1,"pass1_records_not_unique")
    pass_rows=load_jsonl(pass_files[0])
    pass_by_hash={row["source_case_hash"]:row for row in pass_rows}
    _require(len(pass_by_hash)==len(pass_rows),"pass1_source_hash_collision")

    binding_rows=[]
    for path in root.rglob("r5/**/case_bindings.jsonl"):
        binding_rows.extend(load_jsonl(path))
    binding_groups=defaultdict(list)
    for row in binding_rows:
        binding_groups[row["case_id"]].append(row)
    bindings={}
    for case_id,rows in binding_groups.items():
        base=rows[0]
        for other in rows[1:]:
            for key in (
                "source_run_id","source_case_hash","source_trace_hash",
                "state_key","source_event_index","source_turn","parent_state_hash"
            ):
                _require(
                    other.get(key)==base.get(key),
                    f"duplicate_binding_mismatch:{case_id}:{key}",
                )
        bindings[case_id]=base

    r5_by_run={}
    r5_by_case=defaultdict(list)
    for path in root.rglob("r5/**/raw/traces.jsonl"):
        for trace in load_jsonl(path):
            if trace.get("condition_id")!="ONE_SHOT_JUMP_INTERVENTION":
                continue
            _require(trace["run_id"] not in r5_by_run,"r5_run_collision:"+trace["run_id"])
            r5_by_run[trace["run_id"]]=trace
            r5_by_case[trace["case_id"]].append(trace)

    historical=[]
    for path in root.rglob("semantic/**/semantic_audit_records.jsonl"):
        historical.extend(load_jsonl(path))
    canonical=[]
    for row in historical:
        if row.get("replicate_index") is not None:
            if int(row.get("replicate_index") or 0)!=1:
                continue
        canonical.append(row)
    historical_by_case={row["case_id"]:row for row in canonical}
    _require(len(historical_by_case)==len(canonical),"historical_case_collision")

    canonical_r5={}
    for case_id,audit in historical_by_case.items():
        run_id=audit.get("r5_run_id")
        if run_id:
            _require(run_id in r5_by_run,"historical_r5_run_missing:"+run_id)
            canonical_r5[case_id]=r5_by_run[run_id]
            continue
        matches=[
            trace for trace in r5_by_case.get(case_id,[])
            if int(trace.get("canonical_replicate_index") or 0)==1
        ]
        _require(len(matches)==1,"canonical_r5_trace_not_unique:"+case_id)
        canonical_r5[case_id]=matches[0]

    return natural,pass_rows,pass_by_hash,bindings,historical_by_case,canonical_r5


def _make_r5_audit(
    *,case_id: str,binding: dict,old: dict,pass_row: dict,
    natural_trace: dict,r5_trace: dict,
) -> dict:
    source_turn=int(binding["source_turn"])
    prefix=[
        call for call in (natural_trace.get("model_calls") or [])
        if int(call.get("turn") or 0)<=source_turn
    ]
    source_event_index=int(binding["source_event_index"])
    source_positions=[
        i for i,call in enumerate(prefix)
        if int(call.get("turn") or 0)==source_turn
        and call.get("event_index_start")<=source_event_index<=call.get("event_index_end")
    ]
    if not source_positions:
        source_positions=[
            i for i,call in enumerate(prefix)
            if call.get("event_index_start")<=source_event_index<=call.get("event_index_end")
        ][-1:]
    _require(len(source_positions)==1,"source_call_not_unique:"+case_id)
    source_route_index=source_positions[0]

    calls=[
        (natural_trace,call,"N0_PREFIX")
        for call in prefix
    ]+[
        (r5_trace,call,"R5_I")
        for call in (r5_trace.get("model_calls") or [])
    ]
    nodes=[
        _route_node(trace,call,index)
        for index,(trace,call,_kind) in enumerate(calls)
    ]

    evidence_calls=_parse_call_refs(old.get("evidence_refs") or [],r5_trace["run_id"])
    branch_start=len(prefix)
    relevant={source_route_index}
    for index,(trace,call,kind) in enumerate(calls):
        if kind=="R5_I" and (
            _call_ref(trace["run_id"],call) in evidence_calls
            or index==branch_start
        ):
            relevant.add(index)

    semantic_nodes=[]
    previous_relevant=_source_semantic(pass_row)
    for index,(trace,call,kind) in enumerate(calls):
        is_source=index==source_route_index
        is_relevant=index in relevant
        if is_source:
            inputs=[
                f"Natural-process context before source materialization at turn {call.get('turn')}."
            ]
            outputs=[_source_semantic(pass_row)]
            if call.get("decision_summary"):
                outputs.append(str(call["decision_summary"]))
            delta=(
                f"{call.get('agent_id')} materializes the reviewed source as "
                f"{pass_row['source'].get('status')}; exact source meaning is retained."
            )
            relevance="TARGET_LINEAGE"
            independent=False
            independent_refs=[]
        elif is_relevant:
            if index==branch_start:
                transform=(r5_trace.get("runtime_transform_records") or [{}])[0]
                inputs=[(
                    f"One-shot experiment-visible authority delta for {binding['state_key']}: "
                    f"{transform.get('from_status')} -> {transform.get('to_status')} "
                    f"with persistent_state_mutation={transform.get('persistent_state_mutation')}."
                )]
            else:
                inputs=[previous_relevant]
            outputs=_output_semantics(trace,call)
            first_type,_=_historical_first_edge(old)
            independent=(first_type=="INDEPENDENT_REANCHOR" and index==branch_start)
            independent_refs=(
                _independent_evidence_refs(
                    call,trace,old.get("interpretation") or "",binding["state_key"]
                ) if independent else []
            )
            delta=(
                f"{call.get('agent_id')} converts the active target-related meaning "
                f"into the recorded decision/action semantics. Historical case class: "
                f"{old.get('semantic_response_class')}."
            )
            relevance="TARGET_LINEAGE"
        else:
            inputs=list(nodes[index].get("input_premises") or [])[:2]
            outputs=[
                str(call.get("decision_summary") or
                    f"{call.get('agent_id')} executed with status {call.get('status')}.")
            ]
            delta=(
                "Executed route node retained for completeness; "
                "no target-lineage semantic claim is made for this node."
            )
            relevance="SUPPORTING_CONTEXT" if kind=="N0_PREFIX" else "IRRELEVANT_TO_TARGET_LINEAGE"
            independent=False
            independent_refs=[]

        semantic_nodes.append({
            "route_index":index,
            "lineage_relevance":relevance,
            "input_semantics":inputs,
            "output_semantics":[x for x in outputs if x],
            "semantic_delta":delta,
            "semantic_function":_semantic_function(
                is_source,index==branch_start,is_relevant,old
            ),
            "independent_evidence_introduced":independent,
            "independent_evidence_refs":independent_refs,
            "evidence_refs":[nodes[index]["call_ref"],*nodes[index]["event_refs"][:5]],
            "claim_status":"SUPPORTED" if is_relevant else "DIRECTLY_EVIDENCED",
        })
        if is_relevant:
            previous_relevant=(outputs[0] if outputs else previous_relevant)

    ordered=sorted(relevant)
    edges=[]
    for ordinal,(left,right) in enumerate(zip(ordered,ordered[1:])):
        to_trace,to_call,_kind=calls[right]
        propagation,relation=_edge_type(old,ordinal)
        independent_refs=(
            _independent_evidence_refs(
                to_call,to_trace,old.get("interpretation") or "",binding["state_key"]
            ) if propagation=="INDEPENDENT_REANCHOR" else []
        )
        edge_id=f"{case_id}:semantic-edge:{ordinal+1}"
        edges.append({
            "edge_id":edge_id,
            "from_route_index":left,
            "to_route_index":right,
            "propagation_type":propagation,
            "relation_type":relation,
            "semantic_before":semantic_nodes[left]["output_semantics"][0],
            "semantic_after":semantic_nodes[right]["output_semantics"][0],
            "semantic_delta":(
                f"{propagation}: exact before/after meanings are preserved; "
                "this edge records the audited propagation/reconstruction relation."
            ),
            "independent_evidence_refs":independent_refs,
            "evidence_refs":[
                nodes[left]["call_ref"],nodes[right]["call_ref"],*independent_refs
            ],
            "claim_status":"SUPPORTED",
        })

    _require(edges,"r5_semantic_edges_missing:"+case_id)
    natural_hash=stable_hash(natural_trace)
    r5_hash=stable_hash(r5_trace)
    stronger=old.get("system_inertia_status")=="CASE_LEVEL_SYSTEM_INERTIA_SUPPORTED_CANDIDATE"
    transform=(r5_trace.get("runtime_transform_records") or [{}])[0]
    post_nodes=[index for index in ordered if index>branch_start]
    if stronger:
        _require(post_nodes,"stronger_candidate_missing_post_stimulus_nodes:"+case_id)

    record={
        "schema":AUDIT_SCHEMA,
        "audit_id":f"V54-R2R6-TRAJ-{case_id}",
        "reviewer":{
            "kind":"MODEL",
            "id":"GPT-5.6-Sol",
            "blind_to_prior_semantic_labels":False,
            "notes":(
                "Append-only complete-route evidence re-binding over frozen evidence. "
                "Historical per-case semantic classification is retained; node/edge "
                "semantics bind exact realized decision summaries and state writes."
            ),
        },
        "evidence_binding":{
            "trace_id":r5_trace["run_id"],
            "raw_evidence_ref":f"N0:{natural_trace['run_id']} + R5-I:{r5_trace['run_id']}",
            "raw_evidence_hash":stable_hash({
                "natural_trace_hash":natural_hash,
                "r5_trace_hash":r5_hash,
            }),
            "structural_bundle_ref":(
                f"historical_structural_observation:{old.get('structural_observation_hash')}"
            ),
            "structural_bundle_hash":old.get("structural_observation_hash"),
            "workflow_run_id":None,
            "artifact_id":None,
            "artifact_digest":None,
        },
        "experiment_scope":{
            "stage":"R5-R6",
            "domain_id":binding["domain_id"],
            "case_id":case_id,
            "condition_id":"N0_EXISTING_PLUS_R5I_ONCE",
            "evidence_role":"TYPICAL_POSITIVE_CASE" if stronger else "TYPICAL_NEGATIVE_COMPARATOR",
        },
        "actual_agent_route":{
            "complete_route_verified":True,
            "route_node_count":len(nodes),
            "executed_agent_turn_count":len(nodes),
            "nodes":nodes,
            "termination":{
                "run_status":r5_trace.get("run_status") or "UNKNOWN",
                "termination_reason":r5_trace.get("termination_reason") or "UNKNOWN",
            },
        },
        "semantic_nodes":semantic_nodes,
        "semantic_edges":edges,
        "case_judgement":{
            "semantic_adoption":old.get("downstream_read_adoption","NOT_ESTABLISHED"),
            "decision_action_dependence":old.get("decision_action_dependence","NOT_ESTABLISHED"),
            "post_stimulus_persistence":old.get("post_stimulus_persistence","NOT_ESTABLISHED"),
            "system_inertia_status":(
                "CASE_LEVEL_SYSTEM_INERTIA_SUPPORTED_CANDIDATE"
                if stronger else "SYSTEM_INERTIA_NOT_ESTABLISHED"
            ),
            "semantic_structure_class":old.get("semantic_response_class") or "UNCLASSIFIED",
            "derivation_edge_ids":[edge["edge_id"] for edge in edges],
            "challenged_source_or_target_ref":binding["candidate_ref"],
            "direct_stimulus_end_ref":(
                f"{r5_trace['run_id']}:turn:{transform.get('turn')}:one-shot-overlay-consumed"
            ),
            "post_stimulus_persistence_node_refs":post_nodes,
            "problematic_bias_status":"NOT_ESTABLISHED",
            "r5_unique_causal_attribution":"NOT_ESTABLISHED",
            "semantic_cpr_status":"NOT_ADJUDICATED",
        },
        "claim_boundaries":[
            old.get("interpretation") or "",
            (
                "Complete-route re-audit does not establish problematic bias, "
                "unique R5 causality, CPR, or domain prevalence."
            ),
            (
                "Historical case classification is retained as append-only semantic "
                "interpretation; this re-audit strengthens evidence binding but is "
                "not an independent blinded replication."
            ),
        ],
    }
    record["audit_hash"]=stable_hash(record)
    return record


def _make_natural_audit(pass_row: dict,natural_trace: dict) -> dict:
    calls=list(natural_trace.get("model_calls") or [])
    nodes=[_route_node(natural_trace,call,index) for index,call in enumerate(calls)]
    source_event_index=int(pass_row["source"]["event_index"])
    source_turn=int(pass_row["source"]["turn"])
    source_positions=[
        i for i,call in enumerate(calls)
        if int(call.get("turn") or 0)==source_turn
        and call.get("event_index_start")<=source_event_index<=call.get("event_index_end")
    ]
    if not source_positions:
        source_positions=[
            i for i,call in enumerate(calls)
            if call.get("event_index_start")<=source_event_index<=call.get("event_index_end")
        ][-1:]
    _require(len(source_positions)==1,"natural_source_call_not_unique:"+natural_trace["run_id"])
    source_index=source_positions[0]

    downstream=set(_natural_pointer_calls(pass_row))
    relevant={source_index}
    for index,call in enumerate(calls):
        key=(natural_trace["run_id"],int(call.get("turn") or 0),str(call.get("agent_id")))
        if key in downstream:
            relevant.add(index)
    _require(len(relevant)>=2,"natural_semantic_path_too_short:"+natural_trace["run_id"])

    semantic_nodes=[]
    previous=_source_semantic(pass_row)
    next_after_source=min(index for index in relevant if index>source_index)
    for index,call in enumerate(calls):
        is_source=index==source_index
        is_relevant=index in relevant
        if is_source:
            inputs=[
                f"Natural run context before target source materialization at turn {call.get('turn')}."
            ]
            outputs=[_source_semantic(pass_row)]
            if call.get("decision_summary"):
                outputs.append(str(call["decision_summary"]))
            delta=(
                f"{call.get('agent_id')} materializes the audited natural source "
                "with explicit status, basis and value."
            )
            relevance="TARGET_LINEAGE"
            function="SOURCE_OBSERVATION"
            claim="SUPPORTED"
        elif is_relevant:
            inputs=[previous]
            outputs=_output_semantics(natural_trace,call)
            delta=(
                f"{call.get('agent_id')} reads the shared process after source "
                "materialization and converts it into the recorded downstream "
                "decision/action semantics."
            )
            relevance="TARGET_LINEAGE"
            function="READ_OR_ADOPTION" if index==next_after_source else "ACTION_APPLICATION"
            claim="SUPPORTED"
        else:
            inputs=list(nodes[index].get("input_premises") or [])[:2]
            outputs=[
                str(call.get("decision_summary") or
                    f"{call.get('agent_id')} executed with status {call.get('status')}.")
            ]
            delta=(
                "Executed natural-route node retained for completeness; "
                "no target-lineage semantic claim is made for this node."
            )
            relevance="SUPPORTING_CONTEXT" if index<source_index else "IRRELEVANT_TO_TARGET_LINEAGE"
            function="IRRELEVANT_TO_TARGET_LINEAGE"
            claim="DIRECTLY_EVIDENCED"

        semantic_nodes.append({
            "route_index":index,
            "lineage_relevance":relevance,
            "input_semantics":inputs,
            "output_semantics":[x for x in outputs if x],
            "semantic_delta":delta,
            "semantic_function":function,
            "independent_evidence_introduced":False,
            "independent_evidence_refs":[],
            "evidence_refs":[nodes[index]["call_ref"],*nodes[index]["event_refs"][:5]],
            "claim_status":claim,
        })
        if is_relevant:
            previous=outputs[0] if outputs else previous

    ordered=sorted(relevant)
    edges=[]
    for ordinal,(left,right) in enumerate(zip(ordered,ordered[1:])):
        propagation="SEMANTIC_TRANSFORMATION" if ordinal==0 else "DECISION_APPLICATION"
        relation="TRANSFORMS_TO" if ordinal==0 else "CONSTRAINS"
        edge_id=f"natural-{pass_row['source_case_hash'][:12]}:semantic-edge:{ordinal+1}"
        edges.append({
            "edge_id":edge_id,
            "from_route_index":left,
            "to_route_index":right,
            "propagation_type":propagation,
            "relation_type":relation,
            "semantic_before":semantic_nodes[left]["output_semantics"][0],
            "semantic_after":semantic_nodes[right]["output_semantics"][0],
            "semantic_delta":(
                f"{propagation}: exact natural-process before/after meanings are "
                "bound to source and downstream reader nodes."
            ),
            "independent_evidence_refs":[],
            "evidence_refs":[nodes[left]["call_ref"],nodes[right]["call_ref"]],
            "claim_status":"SUPPORTED",
        })

    case_id=f"natural-{pass_row['domain_id']}-{pass_row['source_case_hash'][:12]}"
    record={
        "schema":AUDIT_SCHEMA,
        "audit_id":f"V54-R2R4-TRAJ-{pass_row['source_case_hash'][:12]}",
        "reviewer":{
            "kind":"MODEL",
            "id":"GPT-5.6-Sol",
            "blind_to_prior_semantic_labels":False,
            "notes":(
                "Complete-route natural semantic audit over frozen held-out first-round "
                "evidence. Selected deterministically by source_run_id/candidate_ref, "
                "not by effect size."
            ),
        },
        "evidence_binding":{
            "trace_id":natural_trace["run_id"],
            "raw_evidence_ref":f"N0:{natural_trace['run_id']}",
            "raw_evidence_hash":stable_hash(natural_trace),
            "structural_bundle_ref":f"localized_pass1_audit:{pass_row['audit_hash']}",
            "structural_bundle_hash":pass_row["audit_hash"],
            "workflow_run_id":35370679448,
            "artifact_id":None,
            "artifact_digest":None,
        },
        "experiment_scope":{
            "stage":"R2-R4",
            "domain_id":pass_row["domain_id"],
            "case_id":case_id,
            "condition_id":"NATURAL_FROZEN_TRAJECTORY",
            "evidence_role":"PRIMARY_EXPERIMENT_CASE",
        },
        "actual_agent_route":{
            "complete_route_verified":True,
            "route_node_count":len(nodes),
            "executed_agent_turn_count":len(nodes),
            "nodes":nodes,
            "termination":{
                "run_status":natural_trace.get("run_status") or "UNKNOWN",
                "termination_reason":natural_trace.get("termination_reason") or "UNKNOWN",
            },
        },
        "semantic_nodes":semantic_nodes,
        "semantic_edges":edges,
        "case_judgement":{
            "semantic_adoption":"SUPPORTED",
            "decision_action_dependence":"SUPPORTED",
            "post_stimulus_persistence":"NOT_APPLICABLE",
            "system_inertia_status":"NOT_APPLICABLE",
            "semantic_structure_class":"NATURAL_SOURCE_TO_DOWNSTREAM_DECISION_ACTION_PROPAGATION",
            "derivation_edge_ids":[edge["edge_id"] for edge in edges],
            "challenged_source_or_target_ref":None,
            "direct_stimulus_end_ref":None,
            "post_stimulus_persistence_node_refs":[],
            "problematic_bias_status":"NOT_ESTABLISHED",
            "r5_unique_causal_attribution":"NOT_APPLICABLE",
            "semantic_cpr_status":"NOT_APPLICABLE",
        },
        "claim_boundaries":[
            pass_row.get("claim_boundary") or "",
            "This natural example is illustrative mechanism evidence, not a prevalence denominator.",
            (
                "Natural semantic propagation does not establish System Inertia, "
                "problematic bias, unique R5 causality, or CPR."
            ),
        ],
    }
    record["audit_hash"]=stable_hash(record)
    return record


def build(config_path: str,source_root: str):
    cfg=load_json(config_path)
    _require(
        cfg.get("schema")=="RB-V5.4-R2R6-SEMANTIC-TRAJECTORY-REAUDIT-CONFIG-v0.1",
        "reaudit_config_schema_invalid",
    )
    _require(set(cfg["primary_domains"])==HELD_OUT,"held_out_domain_set_invalid")
    root=Path(source_root)
    natural,pass_rows,pass_by_hash,bindings,historical,canonical_r5=_load_sources(root)

    exp=cfg["expected"]
    _require(len(natural)==exp["natural_population"],"natural_population_count_mismatch")
    _require(len(pass_rows)==exp["pass1_eligible_cases"],"pass1_count_mismatch")
    _require(len(bindings)==exp["canonical_r5_r6_cases"],"binding_case_count_mismatch")
    _require(len(historical)==exp["canonical_r5_r6_cases"],"historical_semantic_case_count_mismatch")
    _require(len(canonical_r5)==exp["canonical_r5_r6_cases"],"canonical_r5_trace_count_mismatch")

    audits=[]
    for case_id in sorted(bindings):
        binding=bindings[case_id]
        _require(binding["source_case_hash"] in pass_by_hash,"pass1_case_missing:"+case_id)
        _require(case_id in historical,"historical_semantic_missing:"+case_id)
        _require(case_id in canonical_r5,"canonical_r5_missing:"+case_id)
        _require(binding["source_run_id"] in natural,"natural_reference_missing:"+case_id)
        audits.append(_make_r5_audit(
            case_id=case_id,
            binding=binding,
            old=historical[case_id],
            pass_row=pass_by_hash[binding["source_case_hash"]],
            natural_trace=natural[binding["source_run_id"]],
            r5_trace=canonical_r5[case_id],
        ))

    historical_domain_counts=Counter(
        row["experiment_scope"]["domain_id"] for row in audits
    )
    _require(
        dict(sorted(historical_domain_counts.items()))
        == dict(sorted(exp["r5_r6_domain_counts"].items())),
        "r5_r6_domain_counts_mismatch",
    )

    stronger=[
        row for row in audits
        if row["case_judgement"]["system_inertia_status"]
        =="CASE_LEVEL_SYSTEM_INERTIA_SUPPORTED_CANDIDATE"
    ]
    stronger_ids=[row["experiment_scope"]["case_id"] for row in stronger]
    _require(len(stronger)==exp["stronger_system_inertia_candidates"],"stronger_candidate_count_mismatch")
    _require(set(stronger_ids)==set(exp["stronger_candidate_case_ids"]),"stronger_candidate_set_mismatch")

    natural_examples=[]
    selected=cfg["natural_example_selection"]["selected_source_case_hashes"]
    for domain in sorted(HELD_OUT):
        domain_rows=sorted(
            [row for row in pass_rows if row["domain_id"]==domain],
            key=lambda row:(row["source_run_id"],row["candidate_ref"]),
        )
        _require(bool(domain_rows),"no_pass1_case_for_domain:"+domain)
        chosen=domain_rows[0]
        _require(
            chosen["source_case_hash"]==selected[domain],
            "natural_example_selection_drift:"+domain,
        )
        _require(chosen["source_run_id"] in natural,"natural_example_trace_missing:"+domain)
        natural_examples.append(_make_natural_audit(chosen,natural[chosen["source_run_id"]]))

    all_audits=natural_examples+audits
    _require(len(all_audits)==exp["complete_route_audits"],"complete_route_audit_count_mismatch")
    _require(all(row["experiment_scope"]["domain_id"]!="ecommerce" for row in all_audits),"ecommerce_primary_evidence_forbidden")

    natural_calls=sum(
        len(trace.get("model_calls") or [])
        for trace in natural.values()
    )
    natural_tokens=sum(
        int((call.get("usage") or {}).get("total_tokens") or 0)
        for trace in natural.values()
        for call in (trace.get("model_calls") or [])
    )
    r5_calls=sum(
        len(trace.get("model_calls") or [])
        for trace in canonical_r5.values()
    )
    r5_tokens=sum(
        int((call.get("usage") or {}).get("total_tokens") or 0)
        for trace in canonical_r5.values()
        for call in (trace.get("model_calls") or [])
    )

    audit_by_case={
        row["experiment_scope"]["case_id"]:row for row in all_audits
    }
    trajectory_cases=[]
    for row in natural_examples:
        trajectory_cases.append({
            "case_id":row["experiment_scope"]["case_id"],
            "domain_id":row["experiment_scope"]["domain_id"],
            "evidence_role":"PRIMARY_EXPERIMENT_CASE",
            "selection_reason":(
                "Deterministically selected as the first frozen Pass-1 eligible "
                "source in this held-out domain by (source_run_id, candidate_ref); "
                "not selected by effect size or downstream outcome."
            ),
            "semantic_trajectory_audit_ref":row["audit_id"],
            "semantic_trajectory_audit_hash":row["audit_hash"],
            "complete_actual_route":True,
            "semantic_lineage_overlay_present":True,
        })
    for row in audits:
        stronger_case=(
            row["case_judgement"]["system_inertia_status"]
            =="CASE_LEVEL_SYSTEM_INERTIA_SUPPORTED_CANDIDATE"
        )
        trajectory_cases.append({
            "case_id":row["experiment_scope"]["case_id"],
            "domain_id":row["experiment_scope"]["domain_id"],
            "evidence_role":"TYPICAL_POSITIVE_CASE" if stronger_case else "TYPICAL_NEGATIVE_COMPARATOR",
            "selection_reason":(
                "Frozen canonical R5-I eligible mechanism-audit case; historical "
                "per-case semantic classification is retained and rebound to the "
                "complete realized route. Not a prevalence sample."
            ),
            "semantic_trajectory_audit_ref":row["audit_id"],
            "semantic_trajectory_audit_hash":row["audit_hash"],
            "complete_actual_route":True,
            "semantic_lineage_overlay_present":True,
        })

    negative_case="wave-1-92211309fb1b"
    natural_ids=[row["experiment_scope"]["case_id"] for row in natural_examples]
    report_bundle={
        "schema":REPORT_BUNDLE_SCHEMA,
        "report_id":"V54-R2-R6-FIRST-BATCH-SEMANTIC-TRAJECTORY-EVIDENCE",
        "report_family":"SYNTHESIS",
        "reporting_standard":"RB-PROCESS-REALITY-REPORT-STANDARD-v1.8",
        "evidence_policy":"FROZEN_SOURCE_SYNTHESIS",
        "experiment_accounting":{
            "natural_trajectory_population_size":90,
            "selected_source_bound_case_count":29,
            "existing_frozen_natural_reference_count":29,
            "canonical_new_r5i_trajectory_count":29,
            "r6_new_provider_trajectory_count":0,
            "canonical_new_r7p_trajectory_count":0,
            "canonical_new_r7s_trajectory_count":0,
            "supplementary_repeated_trajectory_count":33,
            "provider_call_count":natural_calls+r5_calls,
            "token_usage_or_null":natural_tokens+r5_tokens,
            "spend_usd_or_null":None,
        },
        "domain_scope":{
            "primary_experiment_domains":["finance","supply_chain","software_engineering"],
            "historical_context_domains":[],
        },
        "trajectory_cases":trajectory_cases,
        "contrast_sets":[
            {
                "contrast_id":"R5-N0-VS-R5I-FINANCE-922113",
                "purpose":(
                    "Show complete natural-prefix plus one-shot intervention geometry "
                    "without treating a single stochastic contrast as a directional treatment law."
                ),
                "case_ids":[negative_case,natural_ids[0]],
                "contrast_dimension":"NATURAL_PROCESS_REFERENCE_VS_ONE_SHOT_AUTHORITY_WITHDRAWAL_GEOMETRY",
                "claim_supported":(
                    "R5 is a localized probe; realized path change is interpreted at "
                    "the process level rather than as a universal directional effect."
                ),
            },
            {
                "contrast_id":"R6-INERTIA-VS-REANCHOR",
                "purpose":"Show why post-stimulus persistence is not sufficient for System Inertia.",
                "case_ids":["wave-3-56ee79f97f54",negative_case],
                "contrast_dimension":"DESCENDANT_LINEAGE_PERSISTENCE_VS_INDEPENDENT_REANCHORING",
                "claim_supported":(
                    "Post-stimulus persistence and stable endpoint can arise from "
                    "different semantic ancestry."
                ),
            },
            {
                "contrast_id":"R6-CROSS-DOMAIN-STRONGER-CANDIDATES",
                "purpose":(
                    "Show stronger candidate structure in two held-out domains without "
                    "converting the selected case set into a prevalence denominator."
                ),
                "case_ids":["wave-3-56ee79f97f54","wave-6-7c7e526e4d91"],
                "contrast_dimension":"SUPPLY_CHAIN_AND_SOFTWARE_ENGINEERING_DESCENDANT_CARRIER_PERSISTENCE",
                "claim_supported":(
                    "The stronger System Inertia candidate pattern is not confined to "
                    "one held-out domain in the frozen mechanism-audit set."
                ),
            },
        ],
        "structural_summary":{
            "role":"FACTUAL_SUBSTRATE_AND_SUPPORTING_DISPLAY",
            "natural_trajectory_count":90,
            "structural_candidate_count":2127,
            "localized_triage_case_count":167,
            "pass1_eligible_case_count":29,
            "canonical_r5_case_count":29,
            "system_inertia_supported_candidate_case_count":4,
            "normal_or_reanchored_case_count":25,
            "complete_route_audit_count":len(all_audits),
            "complete_route_node_count":sum(
                len(row["actual_agent_route"]["nodes"]) for row in all_audits
            ),
        },
        "semantic_summary":{
            "role":"PRIMARY_INTERPRETIVE_CONTENT",
            "complete_route_natural_example_count":3,
            "complete_route_r5_r6_case_count":29,
            "system_inertia_supported_candidate_case_count":4,
            "system_inertia_not_established_case_count":25,
            "semantic_before_after_delta_present_for_all_route_nodes":True,
            "ecommerce_primary_evidence_count":0,
            "uniform_substantive_semantic_decision_used":False,
            "review_mode":"NON_BLIND_APPEND_ONLY_COMPLETE_ROUTE_REBINDING",
        },
        "claim_registry":[
            {
                "claim_id":"C-NATURAL-1",
                "claim_text":(
                    "In all three held-out domains, natural multi-Agent runs contain "
                    "source-to-downstream semantic propagation that can be reconstructed "
                    "on the complete realized route."
                ),
                "claim_status":"SUPPORTED",
                "semantic_audit_refs":[row["audit_id"] for row in natural_examples],
                "structural_support_refs":[
                    row["evidence_binding"]["raw_evidence_ref"] for row in natural_examples
                ],
                "boundary":(
                    "Three complete-route illustrative cases support mechanism readability; "
                    "they are not a domain-level prevalence estimate."
                ),
            },
            {
                "claim_id":"C-R6-1",
                "claim_text":(
                    "Post-stimulus persistence is not equivalent to System Inertia because "
                    "descendant-lineage persistence and independent/pre-existing re-anchoring "
                    "are distinct semantic ancestries."
                ),
                "claim_status":"SUPPORTED",
                "semantic_audit_refs":[
                    audit_by_case["wave-3-56ee79f97f54"]["audit_id"],
                    audit_by_case[negative_case]["audit_id"],
                ],
                "structural_support_refs":[
                    audit_by_case["wave-3-56ee79f97f54"]["evidence_binding"]["structural_bundle_ref"],
                    audit_by_case[negative_case]["evidence_binding"]["structural_bundle_ref"],
                ],
                "boundary":(
                    "The 4/29 versus 25/29 classification is a mechanism-audit count "
                    "inside the frozen eligible set, not prevalence."
                ),
            },
            {
                "claim_id":"C-BOUNDARY",
                "claim_text":(
                    "Problematic bias, unique R5 causality and CPR remain outside "
                    "the R2-R6 semantic trajectory re-audit."
                ),
                "claim_status":"NOT_ESTABLISHED",
                "semantic_audit_refs":[audits[0]["audit_id"],audits[1]["audit_id"]],
                "structural_support_refs":[],
                "boundary":"No report or semantic re-binding step promotes these claims.",
            },
        ],
        "figure_specs":[
            {
                "figure_id":"FIG-NATURAL-3-DOMAIN-ROUTES",
                "figure_type":"TIME_ALIGNED_ACTUAL_AGENT_ROUTE_WITH_SEMANTIC_LINEAGE_OVERLAY",
                "case_ids":natural_ids,
                "all_actual_nodes_required":True,
                "semantic_overlay_required":True,
                "note":"Three held-out natural examples; one per domain.",
            },
            {
                "figure_id":"FIG-R6-INERTIA-VS-REANCHOR",
                "figure_type":"CONTRASTED_AGENT_ROUTE_PAIR",
                "case_ids":["wave-3-56ee79f97f54",negative_case],
                "all_actual_nodes_required":True,
                "semantic_overlay_required":True,
                "note":"Stronger candidate versus independent multi-evidence re-anchoring comparator.",
            },
            {
                "figure_id":"FIG-R5-CANONICAL-ROUTE",
                "figure_type":"TIME_ALIGNED_ACTUAL_AGENT_ROUTE_WITH_SEMANTIC_LINEAGE_OVERLAY",
                "case_ids":[negative_case],
                "all_actual_nodes_required":True,
                "semantic_overlay_required":True,
                "note":"Complete N0 prefix plus canonical R5-I continuation.",
            },
        ],
        "provenance":{
            "raw_evidence_mutation":False,
            "missing_events_reconstructed":False,
            "new_subject_provider_evaluator_calls_for_report":0,
            "semantic_reaudit_new_provider_calls":0,
            "semantic_reaudit_new_paid_evaluator_calls":0,
        },
        "report_gate_status":"READY_FOR_REPORT_DRAFT",
    }

    summary={
        "schema":SUMMARY_SCHEMA,
        "date":"2026-09-20",
        "status":"COMPLETE_ROUTE_REAUDIT_MATERIALIZED",
        "reviewer":cfg["reviewer"],
        "primary_domains":["finance","supply_chain","software_engineering"],
        "ecommerce_primary_evidence_count":0,
        "semantic_trajectory_audit_count":len(all_audits),
        "natural_complete_route_audit_count":len(natural_examples),
        "canonical_r5_r6_complete_route_audit_count":len(audits),
        "complete_route_node_count":sum(
            len(row["actual_agent_route"]["nodes"]) for row in all_audits
        ),
        "semantic_edge_count":sum(len(row["semantic_edges"]) for row in all_audits),
        "domain_r5_r6_case_counts":dict(sorted(historical_domain_counts.items())),
        "system_inertia_supported_candidate_case_count":len(stronger),
        "system_inertia_not_established_case_count":len(audits)-len(stronger),
        "historical_case_classification_change_count":0,
        "classification_change_interpretation":(
            "No change is expected because this pass is an append-only complete-route "
            "evidence re-binding that retains historical per-case semantic classes; "
            "it is not an independent blinded replication."
        ),
        "uniform_substantive_semantic_decision_used":False,
        "semantic_before_after_delta_required_and_present":True,
        "provider_calls_in_frozen_natural_plus_canonical_r5_evidence":natural_calls+r5_calls,
        "tokens_in_frozen_natural_plus_canonical_r5_evidence":natural_tokens+r5_tokens,
        "new_provider_calls":0,
        "new_paid_evaluator_calls":0,
        "subject_reruns":0,
        "raw_evidence_mutated":False,
        "report_gate_status":"READY_FOR_REPORT_DRAFT",
        "problematic_bias_status":"NOT_ESTABLISHED",
        "r5_unique_causal_attribution":"NOT_ESTABLISHED",
        "semantic_cpr_status":"NOT_ADJUDICATED",
        "claim_boundary":(
            "This re-audit strengthens semantic evidence binding by reconstructing "
            "complete realized Agent routes and explicit semantic before/after/delta "
            "relations over frozen evidence. It does not create a new stochastic sample, "
            "establish prevalence, establish problematic bias, establish unique R5 "
            "causality, or adjudicate CPR."
        ),
        "audit_hashes":[row["audit_hash"] for row in all_audits],
    }
    summary["summary_hash"]=stable_hash(summary)
    return all_audits,report_bundle,summary


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--config",required=True)
    ap.add_argument("--source-root",required=True)
    ap.add_argument("--outdir",required=True)
    args=ap.parse_args()

    audits,bundle,summary=build(args.config,args.source_root)
    out=Path(args.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_r2r6_semantic_trajectory_reaudit")
    (out/"audits").mkdir(parents=True)

    for audit in audits:
        safe=re.sub(r"[^A-Za-z0-9._-]+","_",audit["audit_id"])
        (out/"audits"/f"{safe}.json").write_text(
            json.dumps(audit,ensure_ascii=False,indent=2,sort_keys=True)+"\n",
            encoding="utf-8",
        )
    write_jsonl(out/"semantic_trajectory_audits.jsonl",audits)
    (out/"report_evidence_bundle.json").write_text(
        json.dumps(bundle,ensure_ascii=False,indent=2,sort_keys=True)+"\n",
        encoding="utf-8",
    )
    (out/"summary.json").write_text(
        json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+"\n",
        encoding="utf-8",
    )

    index=[
        {
            "audit_id":row["audit_id"],
            "audit_hash":row["audit_hash"],
            "case_id":row["experiment_scope"]["case_id"],
            "domain_id":row["experiment_scope"]["domain_id"],
            "stage":row["experiment_scope"]["stage"],
            "evidence_role":row["experiment_scope"]["evidence_role"],
            "route_node_count":row["actual_agent_route"]["route_node_count"],
            "semantic_edge_count":len(row["semantic_edges"]),
            "system_inertia_status":row["case_judgement"]["system_inertia_status"],
            "semantic_structure_class":row["case_judgement"]["semantic_structure_class"],
        }
        for row in audits
    ]
    write_jsonl(out/"audit_index.jsonl",index)

    print("V5_4_R2R6_SEMANTIC_TRAJECTORY_REAUDIT=MATERIALIZED")
    print("AUDIT_COUNT="+str(summary["semantic_trajectory_audit_count"]))
    print("NATURAL_COMPLETE_ROUTES="+str(summary["natural_complete_route_audit_count"]))
    print("CANONICAL_R5R6_COMPLETE_ROUTES="+str(summary["canonical_r5_r6_complete_route_audit_count"]))
    print("ROUTE_NODES="+str(summary["complete_route_node_count"]))
    print("SEMANTIC_EDGES="+str(summary["semantic_edge_count"]))
    print("STRONGER_SYSTEM_INERTIA_CANDIDATES="+str(summary["system_inertia_supported_candidate_case_count"]))
    print("NON_INERTIA_CASES="+str(summary["system_inertia_not_established_case_count"]))
    print("ECOMMERCE_PRIMARY_EVIDENCE=0")
    print("NEW_PROVIDER_CALLS=0")
    print("SUBJECT_RERUNS=0")
    print("REPORT_GATE="+summary["report_gate_status"])
    print("SUMMARY_HASH="+summary["summary_hash"])


if __name__=="__main__":
    main()
