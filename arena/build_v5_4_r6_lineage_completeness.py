#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .core import stable_hash
from .io_utils import load_json, load_jsonl, write_jsonl

SUMMARY_SCHEMA="RB-V5.4-R6-LINEAGE-COMPLETENESS-SUMMARY-v0.1"


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def _uniq(items):
    return list(dict.fromkeys(str(x) for x in items if x is not None and str(x)))


def _hash_without(row: dict, key: str) -> str:
    material=dict(row)
    material.pop(key,None)
    return stable_hash(material)


def _load_one(rows, *, case_id: str, replicate_index: int | None = None):
    out=[r for r in rows if r.get("case_id")==case_id and (replicate_index is None or int(r.get("replicate_index",0))==replicate_index)]
    _require(len(out)==1, f"lineage_source_not_unique:{case_id}:{replicate_index}")
    return out[0]


def _build_case(*, cfg: dict, group: dict, source_root: Path, case_id: str) -> tuple[dict,dict,dict,dict]:
    gid=group["group_id"]
    base=source_root/gid
    r5_root=base/"r5"/group["r5"]["plan_root"]
    bindings=load_jsonl(r5_root/"case_bindings.jsonl")
    binding=_load_one(bindings,case_id=case_id)
    envelope=load_json(r5_root/"cases"/case_id/"one_shot_envelope.json")
    parent=load_json(r5_root/"cases"/case_id/"parent_snapshot.json")

    structural=load_jsonl(base/"structural"/group["structural"]["records_path"])
    semantic=load_jsonl(base/"semantic"/group["semantic"]["records_path"])
    s=_load_one(structural,case_id=case_id,replicate_index=1)
    a=_load_one(semantic,case_id=case_id,replicate_index=1)

    # Exact source and canonical-branch binding.
    _require(binding["case_id"]==case_id,"lineage_binding_case_mismatch")
    _require(binding["source_run_id"]==s["source_run_id"],"lineage_source_run_mismatch:"+case_id)
    _require(binding["source_case_hash"]==s["source_case_hash"],"lineage_source_case_hash_mismatch:"+case_id)
    _require(binding["state_key"]==s["target_state_key"],"lineage_target_key_mismatch:"+case_id)
    _require(binding["source_event_index"]==envelope["source_event_index"],"lineage_source_event_mismatch:"+case_id)
    _require(binding["state_key"]==envelope["state_key"],"lineage_envelope_state_key_mismatch:"+case_id)
    _require(binding["candidate_ref"]==envelope["target_jump_ref"],"lineage_target_jump_ref_mismatch:"+case_id)
    _require(binding["parent_state_hash"]==parent["state_hash"],"lineage_parent_hash_mismatch:"+case_id)
    _require((parent.get("shared_state_metadata") or {}).get(binding["state_key"],{}).get("status")=="fact","lineage_parent_target_not_fact:"+case_id)

    src_events=[e for e in (parent.get("events") or []) if int(e.get("event_index",-1))==int(binding["source_event_index"])]
    _require(len(src_events)==1,"lineage_source_event_not_in_parent:"+case_id)
    src=src_events[0]
    _require(src.get("action_type")=="write_state","lineage_source_event_not_write_state:"+case_id)
    _require((src.get("action") or {}).get("key")==binding["state_key"],"lineage_source_event_state_key_mismatch:"+case_id)
    _require((src.get("action") or {}).get("status")=="fact","lineage_source_event_status_not_fact:"+case_id)

    _require(int(s["replicate_index"])==1 and int(a["replicate_index"])==1,"lineage_not_canonical_replicate:"+case_id)
    _require(a["structural_observation_hash"]==s["structural_observation_hash"],"lineage_semantic_structural_hash_mismatch:"+case_id)
    _require(a["system_inertia_status"]=="CASE_LEVEL_SYSTEM_INERTIA_SUPPORTED_CANDIDATE","lineage_case_not_stronger_candidate:"+case_id)
    _require(a["downstream_read_adoption"]=="SUPPORTED","lineage_adoption_not_supported:"+case_id)
    _require(a["decision_action_dependence"]=="SUPPORTED","lineage_dependence_not_supported:"+case_id)
    _require(a["post_stimulus_persistence"]=="SUPPORTED","lineage_persistence_not_supported:"+case_id)
    _require(a["r5_unique_causal_attribution"]=="NOT_ESTABLISHED","lineage_unique_causality_boundary_changed:"+case_id)
    _require(a["problematic_bias_status"]=="NOT_ESTABLISHED","lineage_problematic_bias_boundary_changed:"+case_id)

    carriers=list(s.get("direct_turn_carrier_candidates") or [])
    downstream=list(s.get("downstream_structural_observations") or [])
    carrier_refs=_uniq(x.get("ref") for x in carriers)
    carrier_write_refs=_uniq(x.get("ref") for x in carriers if x.get("action_type")=="write_state")
    revision_refs=_uniq(x.get("ref") for x in carriers if x.get("action_type")=="revise_final_state")
    adopted_calls=[]
    downstream_writes=[]
    target_status_refs=[]
    for row in downstream:
        if row.get("visible_direct_carrier_refs"):
            adopted_calls.append(row.get("call_ref"))
        downstream_writes.extend(row.get("downstream_write_refs") or [])
        if row.get("target_status_seen") is not None:
            target_status_refs.append(f"{row.get('call_ref')}:target_status={row.get('target_status_seen')}")
    downstream_writes=_uniq(downstream_writes)
    adopted_calls=_uniq(adopted_calls)
    target_status_refs=_uniq(target_status_refs)

    dimensions={
        "source_bound":"YES" if binding.get("candidate_ref") and binding.get("content_address") and src else "NO",
        "transformations_bound":"YES" if carriers and adopted_calls else "NO",
        "authority_history_bound":"YES" if (
            envelope.get("from_status")=="fact" and envelope.get("to_status")=="unconfirmed"
            and (s.get("authority_transition") or {}).get("direct_exposure_count")==1
        ) else "NO",
        "pool_state_bound":"YES" if carrier_write_refs and downstream_writes else "NO",
        "affected_descendants_bound":"YES" if adopted_calls and a.get("evidence_refs") else "NO",
        "evidence_pointers_bound":"YES" if (
            s.get("structural_observation_hash") and a.get("audit_hash") and binding.get("case_binding_hash")
        ) else "NO",
    }
    missing=[k for k,v in dimensions.items() if v!="YES"]
    complete=not missing
    status="COMPLETE_FOR_AUTHORIZED_REPAIR" if complete else "LINEAGE_GAP"

    source_refs=_uniq([
        binding["candidate_ref"],
        f"natural_run:{binding['source_run_id']}",
        f"parent_state:{binding['parent_state_hash']}",
        f"source_case_hash:{binding['source_case_hash']}",
    ])
    transformation_refs=_uniq(carrier_refs+downstream_writes)
    adoption_refs=_uniq(adopted_calls)
    authority_refs=_uniq([
        binding["candidate_ref"]+":status=fact",
        f"{s['r5_run_id']}:authority:fact->unconfirmed",
    ]+target_status_refs)
    pool_refs=_uniq(carrier_write_refs+downstream_writes)
    descendants=_uniq(a.get("evidence_refs") or [])
    raw_refs=[
        f"artifact:{group['r5']['artifact_id']}:{group['r5']['artifact_digest']}",
        f"artifact:{group['structural']['artifact_id']}:{group['structural']['artifact_digest']}",
        f"artifact:{group['semantic']['artifact_id']}:{group['semantic']['artifact_digest']}",
        f"case_binding_hash:{binding['case_binding_hash']}",
        f"structural_observation_hash:{s['structural_observation_hash']}",
        f"semantic_audit_hash:{a['audit_hash']}",
    ]
    if group.get("canonical_recovery"):
        raw_refs.append(f"artifact:{group['canonical_recovery']['artifact_id']}:{group['canonical_recovery']['artifact_digest']}")

    target_semantic_id=f"canonical:{binding['domain_id']}:{case_id}:{binding['state_key']}"
    closure={
        "schema":"RB-SEMANTIC-LINEAGE-CLOSURE-v0.1",
        "closure_id":f"V54-R6-LINEAGE-{case_id}-v0.1",
        "target_semantic_id":target_semantic_id,
        "repair_anchor_ref":binding["candidate_ref"],
        "content_address":binding["content_address"],
        "source_refs":source_refs,
        "transformation_refs":transformation_refs,
        "adoption_relation_refs":adoption_refs,
        "authority_transition_refs":authority_refs,
        "pool_state_refs":pool_refs,
        "revision_refs":revision_refs,
        "rejected_or_abandoned_relevant_refs":[],
        "relevant_descendant_refs":descendants,
        "raw_evidence_refs":raw_refs,
        "excluded_unrelated_refs":[f"parent_state:{binding['parent_state_hash']}:all_non_target_cells"],
        "missing_required_components":missing,
        "completeness_status":status,
        "closure_hash":None,
    }
    closure["closure_hash"]=_hash_without(closure,"closure_hash")

    gate={
        "schema":"RB-LINEAGE-COMPLETENESS-GATE-v0.1",
        "gate_id":f"V54-R6-LINEAGE-GATE-{case_id}-v0.1",
        "semantic_lineage_closure_ref":closure["closure_id"],
        "dimensions":dimensions,
        "missing_components":missing,
        "status":status,
        "automatic_repair_allowed":False,
        "boundary":(
            "Complete only for the frozen canonical N0/R5-I declared observation horizon and the case-local repair experiment. "
            "This does not establish global earliest semantic origin, domain prevalence, problematic bias, unique R5 causality, "
            "semantic CPR, or active R7 authorization."
        ),
        "gate_hash":None,
    }
    gate["gate_hash"]=_hash_without(gate,"gate_hash")

    affected=_uniq(carrier_refs+adopted_calls+downstream_writes+descendants)
    repair=_uniq([binding["candidate_ref"]+":status"]+carrier_refs+downstream_writes)
    packet={
        "schema":"RB-SEMANTIC-REPAIR-PACKET-v0.1",
        "packet_id":f"V54-R7-REPAIR-PACKET-{case_id}-v0.1",
        "repair_anchor_ref":binding["candidate_ref"],
        "target_semantic_id":target_semantic_id,
        "content_address":binding["content_address"],
        "trace_root_ref":f"natural_run:{binding['source_run_id']}:{binding['candidate_ref']}",
        "semantic_lineage_closure_ref":closure["closure_id"],
        "lineage_completeness_gate_ref":gate["gate_id"],
        "evidence_supported_affected_closure_refs":affected,
        "mechanically_required_replay_refs":[
            f"natural_snapshot:before_turn:{binding['source_turn']}",
            f"canonical_parent_state:{binding['parent_state_hash']}",
        ],
        "repair_closure_refs":repair,
        "preserved_unrelated_refs":[f"parent_state:{binding['parent_state_hash']}:all_non_target_cells"],
        "raw_evidence_refs":raw_refs,
        "allowed_repair_operations":[
            "AUTHORITY_DOWNGRADE",
            "POOL_INVALIDATION",
            "DESCENDANT_INVALIDATION",
            "SELECTIVE_RECOMPUTE",
            "DEPENDENT_DECISION_REOPEN",
        ],
        "unresolved_gaps":[
            "Global earliest semantic origin is outside this bounded completeness claim.",
            "Unique R5 causal attribution remains NOT_ESTABLISHED.",
            "Problematic bias remains NOT_ESTABLISHED pending later semantic closure.",
        ],
        "repair_authorization_status":"READY_FOR_SEPARATE_AUTHORIZATION" if complete else "AUDIT_ONLY",
        "packet_hash":None,
    }
    packet["packet_hash"]=_hash_without(packet,"packet_hash")

    case_summary={
        "schema":"RB-V5.4-R6-LINEAGE-COMPLETENESS-CASE-SUMMARY-v0.1",
        "case_id":case_id,
        "domain_id":binding["domain_id"],
        "wave_id":binding["wave_id"],
        "canonical_replicate_index":1,
        "source_run_id":binding["source_run_id"],
        "source_case_hash":binding["source_case_hash"],
        "repair_anchor_ref":binding["candidate_ref"],
        "content_address":binding["content_address"],
        "target_state_key":binding["state_key"],
        "direct_carrier_count":len(carrier_refs),
        "evidence_supported_downstream_call_count":len(adopted_calls),
        "downstream_write_ref_count":len(downstream_writes),
        "semantic_audit_hash":a["audit_hash"],
        "structural_observation_hash":s["structural_observation_hash"],
        "lineage_completeness_status":status,
        "gate_hash":gate["gate_hash"],
        "closure_hash":closure["closure_hash"],
        "repair_packet_hash":packet["packet_hash"],
        "r7_entry_ready_for_separate_authorization":complete,
        "r7_active_authorized":False,
        "problematic_bias_status":"NOT_ESTABLISHED",
        "r5_unique_causal_attribution":"NOT_ESTABLISHED",
        "semantic_cpr_status":"NOT_ADJUDICATED",
    }
    case_summary["case_summary_hash"]=stable_hash(case_summary)
    return closure,gate,packet,case_summary


def build(*,config_path: str, source_root: str):
    cfg=load_json(config_path)
    _require(cfg.get("schema")=="RB-V5.4-R6-LINEAGE-COMPLETENESS-CANDIDATE-PLAN-v0.1","lineage_config_schema_invalid")
    root=Path(source_root)
    closures=[]; gates=[]; packets=[]; cases=[]
    expected=set(cfg["candidate_case_ids"])
    seen=set()
    for group in cfg["groups"]:
        for case_id in group["candidate_case_ids"]:
            _require(case_id in expected,"lineage_group_case_not_expected:"+case_id)
            _require(case_id not in seen,"lineage_duplicate_case:"+case_id)
            closure,gate,packet,summary=_build_case(cfg=cfg,group=group,source_root=root,case_id=case_id)
            closures.append(closure); gates.append(gate); packets.append(packet); cases.append(summary); seen.add(case_id)
    _require(seen==expected,"lineage_candidate_set_mismatch")
    complete=sum(x["lineage_completeness_status"]=="COMPLETE_FOR_AUTHORIZED_REPAIR" for x in cases)
    summary={
        "schema":SUMMARY_SCHEMA,
        "date":"2026-09-19",
        "candidate_case_count":len(cases),
        "complete_for_authorized_repair_count":complete,
        "lineage_gap_count":len(cases)-complete,
        "case_ids":[x["case_id"] for x in cases],
        "case_summary_hashes":[x["case_summary_hash"] for x in cases],
        "all_candidates_ready_for_separate_r7_authorization":complete==len(cases),
        "new_provider_calls":0,
        "new_paid_evaluator_calls":0,
        "n0_reruns":0,
        "r5_i_reruns":0,
        "r7_active_authorized":False,
        "problematic_bias_established_case_count":0,
        "r5_unique_causality_established_case_count":0,
        "semantic_cpr_status":"NOT_ADJUDICATED",
        "claim_boundary":(
            "Completeness is assessed only for each frozen canonical candidate's relevant lineage inside the declared N0/R5-I "
            "observation horizon. Passing this gate prepares a bounded R7 repair package but does not itself authorize R7, "
            "establish problematic bias, unique R5 causality, CPR, or domain prevalence."
        ),
    }
    summary["summary_hash"]=stable_hash(summary)
    return closures,gates,packets,cases,summary


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--config",required=True)
    ap.add_argument("--source-root",required=True)
    ap.add_argument("--outdir",required=True)
    a=ap.parse_args()
    closures,gates,packets,cases,summary=build(config_path=a.config,source_root=a.source_root)
    out=Path(a.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_lineage_completeness_outdir")
    out.mkdir(parents=True)
    write_jsonl(out/"semantic_lineage_closures.jsonl",closures)
    write_jsonl(out/"lineage_completeness_gates.jsonl",gates)
    write_jsonl(out/"semantic_repair_packets.jsonl",packets)
    write_jsonl(out/"case_summaries.jsonl",cases)
    (out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    for closure,gate,packet,case in zip(closures,gates,packets,cases):
        d=out/"cases"/case["case_id"]
        d.mkdir(parents=True)
        for name,row in [
            ("semantic_lineage_closure.json",closure),
            ("lineage_completeness_gate.json",gate),
            ("semantic_repair_packet.json",packet),
            ("case_summary.json",case),
        ]:
            (d/name).write_text(json.dumps(row,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("V5_4_R6_LINEAGE_COMPLETENESS=MATERIALIZED")
    print("CANDIDATES="+str(summary["candidate_case_count"]))
    print("COMPLETE_FOR_AUTHORIZED_REPAIR="+str(summary["complete_for_authorized_repair_count"]))
    print("LINEAGE_GAP="+str(summary["lineage_gap_count"]))
    print("SUMMARY_HASH="+summary["summary_hash"])
    print("R7_ACTIVE_AUTHORIZED=NO")


if __name__=="__main__":
    main()
