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
    refs=[structural["r5_intervention"]["first_call"]["call_ref"]]
    refs += [x["ref"] for x in structural["r5_intervention"].get("direct_turn_carrier_candidates") or []]
    downstream=[
        x for x in structural["r5_intervention"].get("downstream_calls") or []
        if x.get("status")=="completed"
    ][:6]
    refs += [x["call_ref"] for x in downstream]
    for x in downstream:
        refs += list(x.get("write_refs") or [])[:2]
    return list(dict.fromkeys(refs))


def build(*,structural_records_path: str, review_packages_path: str, review_manifest_path: str):
    structural=load_jsonl(structural_records_path)
    packages=load_jsonl(review_packages_path)
    review=load_json(review_manifest_path)

    _require(review.get("schema")=="RB-V5.4-R6-CANONICAL-SEMANTIC-REVIEW-MANIFEST-v0.3","v54_r6_semantic_review_schema_invalid")
    exp=int(review["expected_case_count"])
    _require(len(structural)==exp,"v54_r6_structural_count_mismatch")
    _require(len(packages)==exp,"v54_r6_review_package_count_mismatch")
    _require(len(review.get("case_decisions") or [])==exp,"v54_r6_decision_count_mismatch")

    s_by={x["case_id"]:x for x in structural}
    p_by={x["case_id"]:x for x in packages}
    d_by={x["case_id"]:x for x in review["case_decisions"]}
    _require(len(s_by)==len(p_by)==len(d_by)==exp,"v54_r6_case_collision")
    _require(set(s_by)==set(p_by)==set(d_by),"v54_r6_case_set_mismatch")

    u=review["uniform_decision"]
    audits=[]
    case_summaries=[]
    for case_id in sorted(s_by,key=lambda cid:(s_by[cid]["wave_id"],cid)):
        s=s_by[case_id]; p=p_by[case_id]; d=d_by[case_id]
        _require(s.get("semantic_audit_eligibility")=="ELIGIBLE_R6_CANONICAL_SEMANTIC_AUDIT","v54_r6_case_ineligible:"+case_id)
        _require(d["structural_observation_hash"]==s["structural_observation_hash"],"v54_r6_structural_hash_mismatch:"+case_id)
        _require(d["review_package_hash"]==p["review_package_hash"],"v54_r6_review_package_hash_mismatch:"+case_id)
        _require(p["structural_observation_hash"]==s["structural_observation_hash"],"v54_r6_package_structural_binding_mismatch:"+case_id)

        audit={
            "schema":"RB-V5.4-R6-CANONICAL-SEMANTIC-AUDIT-v0.3",
            "audit_id":f"V54-R6-W3-SA-{s['wave_id']}",
            "case_id":case_id,
            "wave_id":s["wave_id"],
            "domain_id":s["domain_id"],
            "target_state_key":s["target_state_key"],
            "structural_observation_hash":s["structural_observation_hash"],
            "review_package_hash":p["review_package_hash"],
            "reviewer":review["reviewer"],
            "semantic_response_class":d["semantic_response_class"],
            "direct_carrier_semantic_use":d["direct_carrier_semantic_use"],
            "downstream_read_adoption":u["downstream_read_adoption"],
            "decision_action_dependence":u["decision_action_dependence"],
            "post_stimulus_persistence":u["post_stimulus_persistence"],
            "system_inertia_status":d["system_inertia_status"],
            "r5_unique_causal_attribution":u["r5_unique_causal_attribution"],
            "problematic_bias_status":u["problematic_bias_status"],
            "lineage_completeness_status":u["lineage_completeness_status"],
            "interpretation":d["interpretation"],
            "evidence_refs":_evidence_refs(s),
            "r7_status":u["r7_status"],
            "semantic_cpr_status":u["semantic_cpr_status"],
        }
        audit["audit_hash"]=stable_hash(audit)
        audits.append(audit)

        item={
            "schema":"RB-V5.4-R6-CANONICAL-SEMANTIC-CASE-SUMMARY-v0.3",
            "case_id":case_id,
            "wave_id":s["wave_id"],
            "domain_id":s["domain_id"],
            "target_state_key":s["target_state_key"],
            "canonical_r5_intervention_count":1,
            "audit_hash":audit["audit_hash"],
            "case_structure_class":d["case_structure_class"],
            "semantic_adoption":"SUPPORTED",
            "decision_action_dependence":"SUPPORTED",
            "post_stimulus_persistence":"SUPPORTED",
            "case_level_system_inertia_status":d["case_level_system_inertia_status"],
            "problematic_bias_status":"NOT_ESTABLISHED",
            "r5_unique_causal_attribution":"NOT_ESTABLISHED",
            "lineage_completeness_status":"NOT_ASSESSED_THIS_PASS",
            "r7_status":"NOT_AUTHORIZED",
            "semantic_cpr_status":"NOT_ADJUDICATED",
        }
        item["case_summary_hash"]=stable_hash(item)
        case_summaries.append(item)

    inertia=[x for x in case_summaries if x["case_level_system_inertia_status"]=="CASE_LEVEL_SYSTEM_INERTIA_SUPPORTED_CANDIDATE"]
    summary={
        "schema":"RB-V5.4-R6-CANONICAL-SEMANTIC-AUDIT-SUMMARY-v0.3",
        "date":"2026-09-19",
        "source_structural_workflow_run_id":review["source_structural"]["workflow_run_id"],
        "source_structural_artifact_id":review["source_structural"]["artifact_id"],
        "source_structural_artifact_digest":review["source_structural"]["artifact_digest"],
        "source_structural_summary_hash":review["source_structural"]["structural_summary_hash"],
        "source_r5_evidence_hash":review["source_structural"]["source_r5_evidence_hash"],
        "reviewer":review["reviewer"],
        "case_count":len(case_summaries),
        "canonical_r5_intervention_count":len(case_summaries),
        "domain_case_counts":dict(sorted(Counter(x["domain_id"] for x in case_summaries).items())),
        "semantic_adoption_supported_case_count":sum(x["semantic_adoption"]=="SUPPORTED" for x in case_summaries),
        "decision_action_dependence_supported_case_count":sum(x["decision_action_dependence"]=="SUPPORTED" for x in case_summaries),
        "post_stimulus_persistence_supported_case_count":sum(x["post_stimulus_persistence"]=="SUPPORTED" for x in case_summaries),
        "system_inertia_supported_candidate_case_count":len(inertia),
        "normal_or_reanchored_persistence_case_count":len(case_summaries)-len(inertia),
        "problematic_bias_established_case_count":0,
        "r5_unique_causal_attribution_established_case_count":0,
        "lineage_completeness_assessed":False,
        "r7_authorized":False,
        "new_provider_calls":0,
        "new_paid_evaluator_calls":0,
        "semantic_cpr_status":"NOT_ADJUDICATED",
        "is_domain_probability_denominator":False,
        "claim_boundary":"This canonical Wave3 pass classifies five realized N0/R5-I case structures. It does not estimate domain prevalence, establish problematic bias, establish unique R5 causality, assess lineage completeness, authorize R7, or adjudicate CPR."
    }
    summary["summary_hash"]=stable_hash(summary)
    return audits,case_summaries,summary


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--structural-records",required=True)
    ap.add_argument("--review-packages",required=True)
    ap.add_argument("--review-manifest",required=True)
    ap.add_argument("--outdir",required=True)
    a=ap.parse_args()
    audits,cases,summary=build(
        structural_records_path=a.structural_records,
        review_packages_path=a.review_packages,
        review_manifest_path=a.review_manifest,
    )
    out=Path(a.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_v54_r6_semantic_audit")
    out.mkdir(parents=True)
    write_jsonl(out/"semantic_audit_records.jsonl",audits)
    write_jsonl(out/"case_semantic_summaries.jsonl",cases)
    (out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("V5_4_R6_CANONICAL_SEMANTIC_AUDIT=MATERIALIZED")
    print("CASE_COUNT="+str(summary["case_count"]))
    print("SYSTEM_INERTIA_CANDIDATE_CASES="+str(summary["system_inertia_supported_candidate_case_count"]))
    print("SUMMARY_HASH="+summary["summary_hash"])


if __name__=="__main__":
    main()
