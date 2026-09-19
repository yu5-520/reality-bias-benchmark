from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from .core import stable_hash
from .io_utils import load_json, load_jsonl, write_jsonl


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def _evidence_refs(structural: dict) -> list[str]:
    refs=[structural["direct_exposure"]["call_ref"]]
    refs += [row["ref"] for row in structural.get("direct_turn_carrier_candidates") or []]
    visible=[
        row for row in structural.get("downstream_structural_observations") or []
        if row.get("visible_direct_carrier_refs") and row.get("call_status")=="completed"
    ][:5]
    refs += [row["call_ref"] for row in visible]
    for row in visible:
        refs += list(row.get("downstream_write_refs") or [])[:2]
    return list(dict.fromkeys(refs))


def build(*,structural_records_path:str,review_manifest_path:str):
    structural=load_jsonl(structural_records_path)
    review=load_json(review_manifest_path)
    _require(review.get("schema")=="RB-V5-CROSS-DOMAIN-R5R6-SEMANTIC-REVIEW-MANIFEST-v0.2","semantic_review_v02_schema_invalid")
    exp_b=int(review["expected_branch_count"]); exp_c=int(review["expected_case_count"])
    _require(len(structural)==exp_b,"semantic_review_v02_structural_count_mismatch")
    _require(len(review.get("branch_decisions") or [])==exp_b,"semantic_review_v02_branch_count_mismatch")
    _require(len(review.get("case_decisions") or [])==exp_c,"semantic_review_v02_case_count_mismatch")

    structural_by={(x["case_id"],int(x["replicate_index"])):x for x in structural}
    decisions={(x["case_id"],int(x["replicate_index"])):x for x in review["branch_decisions"]}
    _require(len(structural_by)==exp_b and set(structural_by)==set(decisions),"semantic_review_v02_branch_set_mismatch")

    uniform=review["uniform_decision"]
    audits=[]
    for key in sorted(structural_by,key=lambda k:(structural_by[k]["wave_id"],k[1])):
        s=structural_by[key]; d=decisions[key]
        _require(s.get("semantic_audit_eligibility")=="ELIGIBLE_R6_PASSIVE_SEMANTIC_AUDIT","semantic_review_v02_ineligible_structural_record:"+s["r5_run_id"])
        _require(d["structural_observation_hash"]==s["structural_observation_hash"],"semantic_review_v02_hash_mismatch:"+s["r5_run_id"])
        audit={
            "schema":"RB-V5-CROSS-DOMAIN-R5R6-SEMANTIC-AUDIT-v0.2",
            "audit_id":f"R5R6-W2-SA-{s['wave_id']}-{s['replicate_index']}",
            "case_id":s["case_id"],"wave_id":s["wave_id"],"domain_id":s["domain_id"],
            "r5_run_id":s["r5_run_id"],"replicate_index":s["replicate_index"],
            "structural_observation_hash":s["structural_observation_hash"],
            "reviewer":review["reviewer"],
            "semantic_response_class":d["semantic_response_class"],
            "direct_carrier_semantic_use":d["direct_carrier_semantic_use"],
            "downstream_read_adoption":uniform["downstream_read_adoption"],
            "decision_action_dependence":uniform["decision_action_dependence"],
            "post_stimulus_persistence":uniform["post_stimulus_persistence"],
            "system_inertia_status":d["system_inertia_status"],
            "r5_unique_causal_attribution":uniform["r5_unique_causal_attribution"],
            "problematic_bias_status":uniform["problematic_bias_status"],
            "lineage_completeness_status":uniform["lineage_completeness_status"],
            "interpretation":d["interpretation"],
            "evidence_refs":_evidence_refs(s),
            "r7_status":uniform["r7_status"],
            "semantic_cpr_status":uniform["semantic_cpr_status"],
        }
        audit["audit_hash"]=stable_hash(audit)
        audits.append(audit)

    case_decisions={x["case_id"]:x for x in review["case_decisions"]}
    _require(len(case_decisions)==exp_c,"semantic_review_v02_case_collision")
    case_ids=sorted({x["case_id"] for x in audits},key=lambda cid:min(x["wave_id"] for x in audits if x["case_id"]==cid))
    _require(set(case_ids)==set(case_decisions),"semantic_review_v02_case_set_mismatch")
    case_summaries=[]
    for cid in case_ids:
        rows=sorted([x for x in audits if x["case_id"]==cid],key=lambda x:x["replicate_index"])
        _require(len(rows)==2,"semantic_review_v02_expected_two_intervention_replicates:"+cid)
        d=case_decisions[cid]
        item={
            "schema":"RB-V5-CROSS-DOMAIN-R5R6-SEMANTIC-CASE-SUMMARY-v0.2",
            "case_id":cid,"wave_id":rows[0]["wave_id"],"domain_id":rows[0]["domain_id"],
            "branch_audit_count":2,"branch_audit_hashes":[x["audit_hash"] for x in rows],
            "case_structure_class":d["case_structure_class"],
            "semantic_adoption_across_intervention_branches":"SUPPORTED_2_OF_2",
            "decision_action_dependence_across_intervention_branches":"SUPPORTED_2_OF_2",
            "post_stimulus_persistence_across_intervention_branches":"SUPPORTED_2_OF_2",
            "case_level_system_inertia_status":d["case_level_system_inertia_status"],
            "problematic_bias_status":"NOT_ESTABLISHED",
            "r5_unique_causal_attribution":"NOT_ESTABLISHED",
            "lineage_completeness_status":"NOT_ASSESSED_THIS_PASS",
            "r7_status":"NOT_AUTHORIZED",
            "semantic_cpr_status":"NOT_ADJUDICATED",
        }
        item["case_summary_hash"]=stable_hash(item)
        case_summaries.append(item)

    inertia_branches=[x for x in audits if x["system_inertia_status"]=="CASE_LEVEL_SYSTEM_INERTIA_SUPPORTED_CANDIDATE"]
    inertia_cases=[x for x in case_summaries if x["case_level_system_inertia_status"]=="CASE_LEVEL_SYSTEM_INERTIA_SUPPORTED_CANDIDATE"]
    summary={
        "schema":"RB-V5-CROSS-DOMAIN-R5R6-SEMANTIC-AUDIT-SUMMARY-v0.2",
        "date":"2026-09-19",
        "source_structural_workflow_run_id":review["source_structural"]["workflow_run_id"],
        "source_structural_artifact_id":review["source_structural"]["artifact_id"],
        "source_structural_artifact_digest":review["source_structural"]["artifact_digest"],
        "source_structural_summary_hash":review["source_structural"]["structural_summary_hash"],
        "source_effective_evidence_hash":review["source_structural"]["effective_evidence_hash"],
        "reviewer":review["reviewer"],
        "branch_audit_count":len(audits),"case_count":len(case_summaries),
        "domain_case_counts":dict(sorted(Counter(x["domain_id"] for x in case_summaries).items())),
        "semantic_adoption_supported_branch_count":sum(x["downstream_read_adoption"]=="SUPPORTED" for x in audits),
        "decision_action_dependence_supported_branch_count":sum(x["decision_action_dependence"]=="SUPPORTED" for x in audits),
        "post_stimulus_persistence_supported_branch_count":sum(x["post_stimulus_persistence"]=="SUPPORTED" for x in audits),
        "system_inertia_supported_candidate_branch_count":len(inertia_branches),
        "system_inertia_supported_candidate_case_count":len(inertia_cases),
        "normal_or_reanchored_persistence_case_count":len(case_summaries)-len(inertia_cases),
        "problematic_bias_established_case_count":0,
        "r5_unique_causal_attribution_established_case_count":0,
        "lineage_completeness_assessed":False,
        "r7_authorized":False,
        "new_provider_calls":0,
        "new_paid_evaluator_calls":0,
        "semantic_cpr_status":"NOT_ADJUDICATED",
        "claim_boundary":"This pass classifies semantic persistence in five preselected R5 second-wave cases. It does not estimate domain occurrence, establish problematic bias, establish unique R5 causality, or authorize R7."
    }
    summary["summary_hash"]=stable_hash(summary)
    return audits,case_summaries,summary


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--structural-records",required=True)
    ap.add_argument("--review-manifest",required=True)
    ap.add_argument("--outdir",required=True)
    a=ap.parse_args()
    audits,cases,summary=build(structural_records_path=a.structural_records,review_manifest_path=a.review_manifest)
    out=Path(a.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_r5r6_semantic_audit_v02")
    out.mkdir(parents=True)
    write_jsonl(out/"semantic_audit_records.jsonl",audits)
    write_jsonl(out/"case_semantic_summaries.jsonl",cases)
    (out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("V5_CROSS_DOMAIN_R5R6_SEMANTIC_AUDIT_V02=MATERIALIZED")
    print("BRANCH_AUDIT_COUNT="+str(summary["branch_audit_count"]))
    print("CASE_COUNT="+str(summary["case_count"]))
    print("SYSTEM_INERTIA_CANDIDATE_CASES="+str(summary["system_inertia_supported_candidate_case_count"]))
    print("SUMMARY_HASH="+summary["summary_hash"])


if __name__=="__main__":
    main()
