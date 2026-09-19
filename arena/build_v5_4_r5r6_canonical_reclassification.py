#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from .core import stable_hash
from .io_utils import load_json, load_jsonl, write_jsonl


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def _selected_case_map(config_paths: list[str]) -> dict[str, dict]:
    out={}
    for path in config_paths:
        cfg=load_json(path)
        for row in cfg.get("selected_cases") or []:
            case_id=f"wave-{int(row['wave_id'])}-{row['source_case_hash'][:12]}"
            _require(case_id not in out,f"canonical_reclass_case_collision:{case_id}")
            out[case_id]=row
    return out


def _canonicalize(records: list[dict], selected: dict[str,dict], wave_label:str) -> list[dict]:
    by_case={}
    for row in records:
        case_id=row["case_id"]
        by_case.setdefault(case_id,[]).append(row)
    expected={cid for cid in selected if any(r["case_id"]==cid for r in records)}
    _require(set(by_case)==expected,f"{wave_label}_semantic_case_set_mismatch")
    out=[]
    for case_id in sorted(by_case,key=lambda cid:(int(cid.split("-")[1]),cid)):
        rows=by_case[case_id]
        chosen=[r for r in rows if int(r["replicate_index"])==1]
        _require(len(chosen)==1,f"{wave_label}_replicate1_not_unique:{case_id}")
        src=selected[case_id]
        audit=chosen[0]
        record={
            "schema":"RB-V5.4-R5R6-CANONICAL-CASE-RECLASSIFICATION-v0.1",
            "case_id":case_id,
            "wave_id":audit["wave_id"],
            "domain_id":audit["domain_id"],
            "source_run_id":src["source_run_id"],
            "source_case_hash":src["source_case_hash"],
            "source_audit_hash":src.get("audit_hash"),
            "natural_reference":{
                "role":"N0_FROZEN_NATURAL_CONTINUATION",
                "run_id":src["source_run_id"],
                "rerun_required":False,
            },
            "canonical_r5_intervention":{
                "selection_rule":"REPLICATE_INDEX_1_AND_ONE_SHOT_INTERVENTION",
                "selection_is_outcome_aware":False,
                "replicate_index":1,
                "r5_run_id":audit["r5_run_id"],
                "semantic_audit_hash":audit["audit_hash"],
                "semantic_response_class":audit["semantic_response_class"],
                "downstream_read_adoption":audit["downstream_read_adoption"],
                "decision_action_dependence":audit["decision_action_dependence"],
                "post_stimulus_persistence":audit["post_stimulus_persistence"],
                "system_inertia_status":audit["system_inertia_status"],
                "problematic_bias_status":audit["problematic_bias_status"],
                "r5_unique_causal_attribution":audit["r5_unique_causal_attribution"],
                "lineage_completeness_status":audit["lineage_completeness_status"],
                "r7_status":audit["r7_status"],
                "semantic_cpr_status":audit["semantic_cpr_status"],
                "interpretation":audit["interpretation"],
                "evidence_refs":audit["evidence_refs"],
            },
            "supplementary_historical_execution":{
                "additional_intervention_replicates_role":"SUPPLEMENTARY_LOCAL_CONDITIONAL_SENSITIVITY",
                "synthetic_controls_role":"SUPPLEMENTARY_LOCAL_CONDITIONAL_SENSITIVITY",
                "canonical_branch_count_contribution":0,
            },
        }
        record["canonical_case_hash"]=stable_hash(record)
        out.append(record)
    return out


def build(*,wave1_records,wave2_records,wave1_config,wave2_config):
    selected=_selected_case_map([wave1_config,wave2_config])
    w1=_canonicalize(load_jsonl(wave1_records),selected,"wave1")
    w2=_canonicalize(load_jsonl(wave2_records),selected,"wave2")
    records=w1+w2
    _require(len(records)==11,"canonical_wave12_case_count_must_be_11")
    _require(len({r["case_id"] for r in records})==11,"canonical_wave12_case_collision")
    _require(all(r["canonical_r5_intervention"]["selection_is_outcome_aware"] is False for r in records),"canonical_selection_outcome_aware_forbidden")

    inertia=[r for r in records if r["canonical_r5_intervention"]["system_inertia_status"]=="CASE_LEVEL_SYSTEM_INERTIA_SUPPORTED_CANDIDATE"]
    summary={
        "schema":"RB-V5.4-R5R6-CANONICAL-WAVE12-SUMMARY-v0.1",
        "date":"2026-09-19",
        "status":"FROZEN_CANONICAL_RECLASSIFICATION_COMPLETE",
        "case_count":11,
        "canonical_r5_intervention_count":11,
        "natural_reference_count":11,
        "natural_reference_rerun_count":0,
        "synthetic_control_count":0,
        "canonical_replicate_count":1,
        "semantic_adoption_supported_case_count":sum(r["canonical_r5_intervention"]["downstream_read_adoption"]=="SUPPORTED" for r in records),
        "decision_action_dependence_supported_case_count":sum(r["canonical_r5_intervention"]["decision_action_dependence"]=="SUPPORTED" for r in records),
        "post_stimulus_persistence_supported_case_count":sum(r["canonical_r5_intervention"]["post_stimulus_persistence"]=="SUPPORTED" for r in records),
        "system_inertia_supported_candidate_case_count":len(inertia),
        "system_inertia_candidate_case_ids":[r["case_id"] for r in inertia],
        "problematic_bias_established_case_count":sum(r["canonical_r5_intervention"]["problematic_bias_status"]=="ESTABLISHED" for r in records),
        "r5_unique_causal_attribution_established_case_count":sum(r["canonical_r5_intervention"]["r5_unique_causal_attribution"]=="ESTABLISHED" for r in records),
        "lineage_completeness_assessed":False,
        "r7_authorized":False,
        "semantic_cpr_status":"NOT_ADJUDICATED",
        "domain_case_counts":dict(sorted(Counter(r["domain_id"] for r in records).items())),
        "historical_executed_intervention_count":22,
        "historical_extra_intervention_count_reclassified_supplementary":11,
        "historical_synthetic_control_branches_reclassified_supplementary":22,
        "is_domain_probability_denominator":False,
        "new_provider_calls":0,
        "new_paid_evaluator_calls":0,
        "claim_boundary":"This is an append-only canonical reinterpretation of already-frozen R5/R6 evidence. Replicate-1 intervention is selected deterministically before outcome inspection; all additional same-parent branches remain supplementary local sensitivity. Counts are case-mechanism counts, not domain occurrence rates."
    }
    summary["summary_hash"]=stable_hash(summary)
    return records,summary


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--wave1-records",required=True)
    ap.add_argument("--wave2-records",required=True)
    ap.add_argument("--wave1-config",default="configs/v5_cross_domain_r5_first_wave_v0.1.json")
    ap.add_argument("--wave2-config",default="configs/v5_cross_domain_r5_second_wave_v0.1.json")
    ap.add_argument("--outdir",required=True)
    a=ap.parse_args()
    records,summary=build(
        wave1_records=a.wave1_records,wave2_records=a.wave2_records,
        wave1_config=a.wave1_config,wave2_config=a.wave2_config,
    )
    out=Path(a.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_v5_4_canonical_wave12")
    out.mkdir(parents=True)
    write_jsonl(out/"canonical_case_records.jsonl",records)
    (out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("V5_4_R5R6_CANONICAL_WAVE12=COMPLETE")
    print("CASE_COUNT=11")
    print("CANONICAL_R5_INTERVENTION_COUNT=11")
    print("SYSTEM_INERTIA_CANDIDATE_CASE_COUNT="+str(summary["system_inertia_supported_candidate_case_count"]))
    print("NEW_PROVIDER_CALLS=0")
    print("SUMMARY_HASH="+summary["summary_hash"])


if __name__=="__main__":
    main()
