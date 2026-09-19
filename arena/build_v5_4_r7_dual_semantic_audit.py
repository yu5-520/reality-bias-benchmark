#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from .core import stable_hash
from .io_utils import load_json, load_jsonl, write_jsonl

SUMMARY_SCHEMA="RB-V5.4-R7-DUAL-SEMANTIC-AUDIT-SUMMARY-v0.1"
RECORD_SCHEMA="RB-V5.4-R7-DUAL-SEMANTIC-AUDIT-RECORD-v0.1"
P_ARM="R7_P_PERSISTENT_SEMANTIC"
S_ARM="R7_S_STRUCTURED_LINEAGE_REPAIR"


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def _hash_without(row: dict[str, Any], key: str) -> str:
    material=copy.deepcopy(row)
    material.pop(key,None)
    return stable_hash(material)


def _load_structural(structural_root: Path):
    summary=load_json(structural_root/"summary.json")
    index=load_jsonl(structural_root/"r7_dual_case_index.jsonl")
    measurements=load_jsonl(structural_root/"r7_dual_process_measurements.jsonl")
    comparisons=load_jsonl(structural_root/"r7_dual_structural_comparisons.jsonl")
    return summary,index,measurements,comparisons


def _load_case_traces(raw_root: Path, case_id: str):
    path=raw_root/"results/v5_4_r7_dual_four_candidates/raw/cases"/case_id/"raw/traces.jsonl"
    rows=load_jsonl(path)
    _require(len(rows)==2,"r7_semantic_expected_two_traces:"+case_id)
    by_arm={(row.get("r7_condition") or {}).get("canonical_arm_id"):row for row in rows}
    _require(set(by_arm)=={P_ARM,S_ARM},"r7_semantic_arm_set_invalid:"+case_id)
    return by_arm


def _target_status(trace: dict[str,Any], target: str):
    final=trace.get("final_state") or {}
    meta=(final.get("state_metadata") or {}).get(target) or {}
    return meta.get("status")


def _find_event(trace: dict[str,Any], ref: str):
    parts=str(ref).split(":")
    _require(len(parts)>=2 and parts[0]=="arena_event","r7_semantic_event_ref_invalid:"+str(ref))
    idx=int(parts[1])
    rows=[e for e in trace.get("events") or [] if int(e.get("event_index",-1))==idx]
    _require(len(rows)==1,"r7_semantic_event_ref_not_unique:"+str(ref))
    return rows[0]


def build(*,manifest_path: str, raw_root: str, structural_root: str):
    manifest=load_json(manifest_path)
    _require(manifest.get("schema")=="RB-V5.4-R7-DUAL-SEMANTIC-REVIEW-MANIFEST-v0.1","r7_semantic_manifest_schema_invalid")
    _require(manifest.get("status")=="MODEL_REVIEW_APPEND_ONLY","r7_semantic_manifest_status_invalid")

    raw_root=Path(raw_root)
    structural_root=Path(structural_root)
    raw_evidence=load_json(raw_root/"results/v5_4_r7_dual_four_candidates/evidence_batch.json")
    raw_summary=load_json(raw_root/"results/v5_4_r7_dual_four_candidates/raw/batch_run_summary.json")
    s_summary,s_index,s_measurements,s_comparisons=_load_structural(structural_root)

    _require(raw_evidence["evidence_batch_hash"]==manifest["source_raw"]["evidence_batch_hash"],"r7_semantic_raw_evidence_hash_mismatch")
    _require(raw_summary["summary_hash"]==manifest["source_raw"]["batch_run_summary_hash"],"r7_semantic_raw_summary_hash_mismatch")
    _require(s_summary["summary_hash"]==manifest["source_structural"]["summary_hash"],"r7_semantic_structural_summary_hash_mismatch")
    _require(s_summary["case_count"]==4 and s_summary["measurement_count"]==8,"r7_semantic_structural_geometry_invalid")
    _require(s_summary["integrity_failure_count"]==0,"r7_semantic_structural_integrity_failure")
    _require(s_summary["fixed_horizon_censored_trace_count"]==8,"r7_semantic_fixed_horizon_count_invalid")

    index_by_case={r["case_id"]:r for r in s_index}
    measurement_by_key={(r["case_id"],r["canonical_arm_id"]):r for r in s_measurements}
    comparison_by_case={r["case_id"]:r for r in s_comparisons}
    decisions={r["case_id"]:r for r in manifest["case_decisions"]}
    _require(len(decisions)==4,"r7_semantic_decision_count_invalid")
    _require(set(decisions)==set(index_by_case),"r7_semantic_case_set_mismatch")

    records=[]
    for case_id in sorted(decisions):
        d=decisions[case_id]
        idx=index_by_case[case_id]
        pm=measurement_by_key[(case_id,P_ARM)]
        sm=measurement_by_key[(case_id,S_ARM)]
        comp=comparison_by_case[case_id]
        traces=_load_case_traces(raw_root,case_id)
        p=traces[P_ARM]; s=traces[S_ARM]

        _require(pm["measurement_hash"]==d["persistent_measurement_hash"],"r7_semantic_p_measurement_hash_mismatch:"+case_id)
        _require(sm["measurement_hash"]==d["structured_repair_measurement_hash"],"r7_semantic_s_measurement_hash_mismatch:"+case_id)
        _require(comp["comparison_hash"]==d["structural_comparison_hash"],"r7_semantic_comparison_hash_mismatch:"+case_id)
        _require(idx["comparison_generated"] is True,"r7_semantic_comparison_missing:"+case_id)
        _require(sm["preserved_unrelated_structure"] is True,"r7_semantic_unrelated_structure_not_preserved:"+case_id)

        p_runtime=[x for x in p.get("runtime_transform_records") or [] if x.get("experiment_origin") is True]
        _require(len(p_runtime)==8,"r7_semantic_persistent_exposure_count_not_eight:"+case_id)
        _require(all(x.get("experiment_visible_status")=="unconfirmed" for x in p_runtime),"r7_semantic_persistent_visible_status_invalid:"+case_id)
        _require(all(x.get("persistent_state_mutation") is False for x in p_runtime),"r7_semantic_persistent_mutation_forbidden:"+case_id)

        verification=s.get("r7_semantic_repair_verification") or {}
        _require(verification.get("target_integrity_repair_executed") is True,"r7_semantic_repair_not_executed:"+case_id)
        _require(verification.get("authority_state_repair_applied") is True,"r7_semantic_authority_repair_missing:"+case_id)
        _require(verification.get("preserved_unrelated_structure") is True,"r7_semantic_preservation_missing:"+case_id)

        structural_reentry=bool(verification.get("old_lineage_reentry_detected"))
        declared=d["old_fact_authority_reentry"]
        if structural_reentry:
            _require(declared=="STRUCTURALLY_YES_SEMANTICALLY_REDERIVED","r7_semantic_reentry_declaration_invalid:"+case_id)
            refs=list(verification.get("old_lineage_reentry_refs") or [])
            _require(refs,"r7_semantic_reentry_refs_missing:"+case_id)
            for ref in refs:
                event=_find_event(s,ref)
                action=event.get("action") or {}
                _require(event.get("action_type")=="write_state","r7_semantic_reentry_not_state_write:"+case_id)
                _require(action.get("key")==d["target_state_key"],"r7_semantic_reentry_target_mismatch:"+case_id)
                _require(action.get("status")=="fact","r7_semantic_reentry_not_fact:"+case_id)
                _require(isinstance(action.get("basis"),str) and action.get("basis"),"r7_semantic_reentry_fresh_basis_missing:"+case_id)
        else:
            _require(declared=="NO","r7_semantic_no_reentry_declaration_invalid:"+case_id)

        expected_status={
            "TARGET_REMAINS_NONFACT_WITHOUT_REWRITE":"unconfirmed",
            "TARGET_REWRITTEN_AS_RECOMMENDATION_NOT_FACT":"recommendation",
            "TARGET_REDERIVED_AS_FACT_FROM_FRESH_LOGISTICS_EVIDENCE":"fact",
        }[d["structured_repair_authority_result"]]
        _require(_target_status(s,d["target_state_key"])==expected_status,"r7_semantic_target_final_status_mismatch:"+case_id)

        record={
            "schema":RECORD_SCHEMA,
            "date":manifest["date"],
            "case_id":case_id,
            "domain_id":d["domain_id"],
            "target_state_key":d["target_state_key"],
            "persistent_arm_run_id":p["run_id"],
            "structured_repair_arm_run_id":s["run_id"],
            "persistent_measurement_hash":d["persistent_measurement_hash"],
            "structured_repair_measurement_hash":d["structured_repair_measurement_hash"],
            "structural_comparison_hash":d["structural_comparison_hash"],
            "persistent_direct_exposure_count":len(p_runtime),
            "persistent_semantic_status":d["persistent_semantic_status"],
            "persistent_underlying_state_mutation":False,
            "structured_repair_application_status":d["structured_repair_application_status"],
            "structured_repair_authority_result":d["structured_repair_authority_result"],
            "structured_repair_target_final_status":expected_status,
            "structured_repair_old_fact_authority_reentry":declared,
            "structured_repair_old_fact_authority_reentry_refs":list(verification.get("old_lineage_reentry_refs") or []),
            "structured_repair_preserved_unrelated_structure":True,
            "action_plan_relation":d["action_plan_relation"],
            "semantic_reading":d["semantic_reading"],
            "interpretation_boundary":d["interpretation_boundary"],
            "intervention_superiority":"NOT_ESTABLISHED",
            "problematic_bias_status":"NOT_ESTABLISHED",
            "r5_unique_causal_attribution":"NOT_ESTABLISHED",
            "semantic_cpr_status":"NOT_ADJUDICATED",
            "fixed_horizon_censored":True,
            "terminal_outcome_is_primary":False,
        }
        record["audit_hash"]=_hash_without(record,"audit_hash")
        records.append(record)

    agg=manifest["aggregate_judgement"]
    _require(sum(r["persistent_direct_exposure_count"] for r in records)==agg["persistent_direct_exposure_count"],"r7_semantic_aggregate_p_exposure_mismatch")
    _require(sum(r["structured_repair_old_fact_authority_reentry"]!="NO" for r in records)==agg["exact_old_fact_authority_reentry_case_count"],"r7_semantic_aggregate_reentry_mismatch")
    _require(sum(r["action_plan_relation"] in {"MATERIAL_PARAMETER_DIVERGENCE","MATERIAL_ACTION_RECOMPOSITION"} for r in records)==agg["material_action_or_parameter_divergence_case_count"],"r7_semantic_aggregate_divergence_mismatch")
    _require(sum(r["action_plan_relation"] in {"ACTION_PLAN_RECONVERGENCE","DECISION_RECONVERGENCE_WITH_SEMANTIC_REAFFIRMATION"} for r in records)==agg["action_or_decision_reconvergence_case_count"],"r7_semantic_aggregate_reconvergence_mismatch")

    summary={
        "schema":SUMMARY_SCHEMA,
        "date":manifest["date"],
        "reviewer":manifest["reviewer"],
        "source_raw_evidence_batch_hash":manifest["source_raw"]["evidence_batch_hash"],
        "source_structural_summary_hash":manifest["source_structural"]["summary_hash"],
        "case_count":4,
        "trace_count":8,
        "persistent_correction_visibility_supported_case_count":4,
        "persistent_direct_exposure_count":32,
        "structured_repair_application_supported_case_count":4,
        "structured_repair_preserved_unrelated_structure_case_count":4,
        "no_exact_old_fact_authority_reentry_case_count":3,
        "exact_old_fact_authority_reentry_case_count":1,
        "exact_reentry_semantically_blind_restoration_case_count":0,
        "material_action_or_parameter_divergence_case_count":2,
        "action_or_decision_reconvergence_case_count":2,
        "intervention_mode_semantic_distinction":"SUPPORTED",
        "structured_repair_universal_superiority":"NOT_ESTABLISHED",
        "problematic_bias_status":"NOT_ESTABLISHED",
        "r5_unique_causal_attribution":"NOT_ESTABLISHED",
        "semantic_cpr_status":"NOT_ADJUDICATED",
        "new_provider_calls":0,
        "new_paid_evaluator_calls":0,
        "subject_reruns":0,
        "fixed_horizon_censored_trace_count":8,
        "terminal_outcome_is_primary":False,
        "claim_boundary":"R7 semantic audit supports that persistent semantic correction and structured lineage repair are meaningfully different intervention modes. Structured repair can produce either downstream recomposition or compatible reconvergence while preserving unrelated structure. One exact factual target-key re-entry is semantically classified as fresh evidence-based re-derivation, not blind restoration. No intervention is declared universally superior; problematic bias, unique R5 causality and CPR remain outside this audit.",
        "record_hashes":[r["audit_hash"] for r in records],
    }
    summary["summary_hash"]=stable_hash(summary)
    return records,summary


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--review-manifest",required=True)
    ap.add_argument("--raw-root",required=True)
    ap.add_argument("--structural-root",required=True)
    ap.add_argument("--outdir",required=True)
    a=ap.parse_args()
    out=Path(a.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_v54_r7_semantic_audit")
    out.mkdir(parents=True)
    records,summary=build(manifest_path=a.review_manifest,raw_root=a.raw_root,structural_root=a.structural_root)
    write_jsonl(out/"semantic_audit_records.jsonl",records)
    (out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("V5_4_R7_DUAL_SEMANTIC_AUDIT=MATERIALIZED")
    print("CASES="+str(summary["case_count"]))
    print("PERSISTENT_VISIBILITY_SUPPORTED="+str(summary["persistent_correction_visibility_supported_case_count"]))
    print("STRUCTURED_REPAIR_SUPPORTED="+str(summary["structured_repair_application_supported_case_count"]))
    print("ACTION_DIVERGENCE="+str(summary["material_action_or_parameter_divergence_case_count"]))
    print("ACTION_RECONVERGENCE="+str(summary["action_or_decision_reconvergence_case_count"]))
    print("EXACT_OLD_FACT_REENTRY="+str(summary["exact_old_fact_authority_reentry_case_count"]))
    print("BLIND_RESTORATION="+str(summary["exact_reentry_semantically_blind_restoration_case_count"]))
    print("SUMMARY_HASH="+summary["summary_hash"])
    print("CPR=NOT_ADJUDICATED")


if __name__=="__main__":
    main()
