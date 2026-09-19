#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import stable_hash
from .io_utils import load_json, load_jsonl, write_jsonl
from .process_reality_dynamics_v0_4 import build_process_reality_measurement, compare_process_reality
from .system_behavior_adapter import adapt_arena_trace_v03
from .system_behavior_dynamics_v4 import build_system_dynamics_view
from .system_behavior_lineage_v4 import build_system_lineage_view
from .r7_lineage_monitoring import build_full_lineage_observation

P_ARM="R7_P_PERSISTENT_SEMANTIC"
S_ARM="R7_S_STRUCTURED_LINEAGE_REPAIR"


def _require(ok,message):
    if not ok:
        raise ValueError(message)


def _trace_arm(trace):
    return (trace.get("r7_condition") or {}).get("canonical_arm_id")


def _integrity(trace, arm, plan):
    c=trace.get("r7_condition") or {}
    runtime=[x for x in (trace.get("runtime_transform_records") or []) if x.get("experiment_origin") is True]
    actions=[x for x in (trace.get("action_transform_records") or []) if x.get("experiment_origin") is True]
    failures=[]
    if c.get("canonical_arm_id")!=arm:
        failures.append("CANONICAL_ARM_ID_MISMATCH")
    if c.get("condition_status")!="OBSERVED":
        failures.append("CONDITION_NOT_OBSERVED")
    if actions:
        failures.append("ACTION_TRANSFORM_FORBIDDEN")
    if arm==P_ARM:
        if len(runtime)<1:
            failures.append("PERSISTENT_ARM_NO_EXPOSURE")
        if len(runtime)>int(plan["matched_horizon"]["post_source_turn_cap"]):
            failures.append("PERSISTENT_ARM_EXPOSURE_OVERFLOW")
    elif arm==S_ARM:
        if runtime:
            failures.append("STRUCTURED_REPAIR_RUNTIME_OVERLAY_FORBIDDEN")
        app=trace.get("r7_repair_application")
        ver=trace.get("r7_semantic_repair_verification")
        if not isinstance(app,dict):
            failures.append("STRUCTURED_REPAIR_APPLICATION_REQUIRED")
        if not isinstance(ver,dict):
            failures.append("STRUCTURED_REPAIR_VERIFICATION_REQUIRED")
        if isinstance(ver,dict) and ver.get("authority_state_repair_applied") is not True:
            failures.append("STRUCTURED_REPAIR_AUTHORITY_REPAIR_MISSING")
        if isinstance(ver,dict) and ver.get("preserved_unrelated_structure") is not True:
            failures.append("STRUCTURED_REPAIR_UNRELATED_STRUCTURE_NOT_PRESERVED")
    else:
        failures.append("UNKNOWN_ARM")
    return {
        "ok":not failures,
        "failures":failures,
        "runtime_exposure_count":len(runtime),
        "action_transform_count":len(actions),
        "run_status":trace.get("run_status"),
        "termination_reason":trace.get("termination_reason"),
        "fixed_horizon_censored":trace.get("run_status")=="BUDGET_CENSORED" and trace.get("termination_reason")=="turn_budget_exhausted",
    }


def _measurement(trace, plan, arm):
    env=load_json(Path(plan["_case_plan_dir"])/"c1_one_shot_envelope.json")
    adapted=adapt_arena_trace_v03(trace)
    dynamics=build_system_dynamics_view(adapted)
    lineage=build_system_lineage_view(adapted,dynamics_view=dynamics)
    m=build_process_reality_measurement(
        trace=trace,
        adapter_result=adapted,
        dynamics_view=dynamics,
        lineage_view=lineage,
        target_source_event_index=int(env["source_event_index"]),
        target_state_key=env["state_key"],
        target_candidate_id=env["target_candidate_id"],
        branch_start_turn=int(load_json(Path(plan["_case_plan_dir"])/"source_parent_snapshot.json")["turns"]),
    )
    if arm==S_ARM:
        app=trace.get("r7_repair_application") or {}
        start_count=int(app.get("repaired_branch_start_event_count") or 0)
    else:
        parent=load_json(Path(plan["_case_plan_dir"])/"source_parent_snapshot.json")
        start_count=len(parent.get("events") or [])
    obs=build_full_lineage_observation(
        trace=trace,
        arm_id=arm,
        anchor_event_index=int(env["source_event_index"]),
        branch_start_event_count=start_count,
        target_state_key=env["state_key"],
    )
    integ=_integrity(trace,arm,plan)
    m.update({
        "case_id":plan["case_id"],
        "canonical_arm_id":arm,
        "condition_integrity":integ,
        "full_lineage_observation":obs,
        "full_lineage_observation_hash":obs["observation_hash"],
        "old_lineage_reentry_detected":(trace.get("r7_semantic_repair_verification") or {}).get("old_lineage_reentry_detected") if arm==S_ARM else None,
        "old_lineage_reentry_refs":list((trace.get("r7_semantic_repair_verification") or {}).get("old_lineage_reentry_refs") or []) if arm==S_ARM else [],
        "preserved_unrelated_structure":(trace.get("r7_semantic_repair_verification") or {}).get("preserved_unrelated_structure") if arm==S_ARM else None,
        "recomputed_descendant_refs":list((trace.get("r7_semantic_repair_verification") or {}).get("recomputed_descendant_refs") or []) if arm==S_ARM else [],
        "semantic_repair_verification_hash":(trace.get("r7_semantic_repair_verification") or {}).get("verification_hash") if arm==S_ARM else None,
        "semantic_status":"NOT_ADJUDICATED",
        "problematic_bias_status":"NOT_ESTABLISHED",
        "r5_unique_causal_attribution":"NOT_ESTABLISHED",
        "terminal_outcome_is_primary":False,
    })
    m["measurement_hash"]=stable_hash({k:v for k,v in m.items() if k!="measurement_hash"})
    return m


def derive(plan_root,raw_root,evidence_path):
    plan_root=Path(plan_root); raw_root=Path(raw_root)
    batch_plan=load_json(plan_root/"batch_plan.json")
    evidence=load_json(evidence_path)
    _require(evidence["evidence_batch_hash"]=="15da67c93f7b9cac5bd1e2000ddecadef229f5a7f08e735fab2626f66c039d74","r7_v54_unexpected_evidence_hash")
    _require(evidence["raw_evidence_frozen_before_derived_analysis"] is True,"r7_v54_raw_not_frozen")
    _require(evidence["batch_plan_hash"]==batch_plan["batch_plan_hash"],"r7_v54_plan_evidence_mismatch")
    measurements=[]; comparisons=[]; case_rows=[]; integrity_failures=[]
    for row in batch_plan["case_rows"]:
        cid=row["case_id"]
        case_dir=plan_root/"cases"/cid
        plan=load_json(case_dir/"r7_plan.json")
        plan["_case_plan_dir"]=str(case_dir)
        traces=load_jsonl(raw_root/"cases"/cid/"raw"/"traces.jsonl")
        by_arm={_trace_arm(t):t for t in traces}
        _require(set(by_arm)=={P_ARM,S_ARM},"r7_v54_case_arm_set_invalid:"+cid)
        pm=_measurement(by_arm[P_ARM],plan,P_ARM)
        sm=_measurement(by_arm[S_ARM],plan,S_ARM)
        measurements += [pm,sm]
        for m in (pm,sm):
            for failure in (m["condition_integrity"]["failures"]):
                integrity_failures.append({"case_id":cid,"arm_id":m["canonical_arm_id"],"failure":failure})
        comparable=(
            pm.get("mechanism_measurement_status")=="ROOT_RESOLVED"
            and sm.get("mechanism_measurement_status")=="ROOT_RESOLVED"
            and pm["condition_integrity"]["ok"]
            and sm["condition_integrity"]["ok"]
        )
        comparison=None
        if comparable:
            comparison=compare_process_reality(pm,sm,comparison_id=f"{cid}:R7P_vs_R7S:v0.1")
            comparison.update({
                "schema":"RB-V5.4-R7-DUAL-STRUCTURAL-COMPARISON-v0.1",
                "case_id":cid,
                "left_arm_id":P_ARM,
                "right_arm_id":S_ARM,
                "source_raw_evidence_batch_hash":evidence["evidence_batch_hash"],
                "persistent_runtime_exposure_count":pm["condition_integrity"]["runtime_exposure_count"],
                "structured_repair_old_lineage_reentry_detected":sm["old_lineage_reentry_detected"],
                "structured_repair_preserved_unrelated_structure":sm["preserved_unrelated_structure"],
                "structured_repair_recomputed_descendant_count":len(sm["recomputed_descendant_refs"]),
                "semantic_status":"NOT_ADJUDICATED",
                "interpretation_boundary":"Mechanical R7-P versus R7-S process comparison only. It does not establish semantic repair success, problematic bias, unique R5 causality, CPR, or a superior intervention.",
            })
            comparison["comparison_hash"]=stable_hash({k:v for k,v in comparison.items() if k!="comparison_hash"})
            comparisons.append(comparison)
        case_rows.append({
            "case_id":cid,
            "persistent_measurement_hash":pm["measurement_hash"],
            "structured_repair_measurement_hash":sm["measurement_hash"],
            "persistent_root_status":pm.get("mechanism_measurement_status"),
            "structured_repair_root_status":sm.get("mechanism_measurement_status"),
            "persistent_fixed_horizon_censored":pm["condition_integrity"]["fixed_horizon_censored"],
            "structured_repair_fixed_horizon_censored":sm["condition_integrity"]["fixed_horizon_censored"],
            "persistent_runtime_exposure_count":pm["condition_integrity"]["runtime_exposure_count"],
            "structured_repair_old_lineage_reentry_detected":sm["old_lineage_reentry_detected"],
            "structured_repair_preserved_unrelated_structure":sm["preserved_unrelated_structure"],
            "comparison_generated":comparison is not None,
            "comparison_hash":comparison.get("comparison_hash") if comparison else None,
        })
    summary={
        "schema":"RB-V5.4-R7-DUAL-STRUCTURAL-SUMMARY-v0.1",
        "date":"2026-09-19",
        "source_raw_evidence_batch_hash":evidence["evidence_batch_hash"],
        "case_count":4,
        "measurement_count":len(measurements),
        "comparison_count":len(comparisons),
        "integrity_failure_count":len(integrity_failures),
        "fixed_horizon_censored_trace_count":sum(m["condition_integrity"]["fixed_horizon_censored"] for m in measurements),
        "persistent_total_direct_exposure_count":sum(m["condition_integrity"]["runtime_exposure_count"] for m in measurements if m["canonical_arm_id"]==P_ARM),
        "structured_repair_old_lineage_reentry_case_count":sum(1 for r in case_rows if r["structured_repair_old_lineage_reentry_detected"] is True),
        "structured_repair_no_old_lineage_reentry_case_count":sum(1 for r in case_rows if r["structured_repair_old_lineage_reentry_detected"] is False),
        "structured_repair_preserved_unrelated_structure_case_count":sum(1 for r in case_rows if r["structured_repair_preserved_unrelated_structure"] is True),
        "case_rows":case_rows,
        "new_provider_calls":0,
        "new_paid_evaluator_calls":0,
        "n0_reruns":0,
        "r5_i_reruns":0,
        "semantic_cpr_status":"NOT_ADJUDICATED",
        "problematic_bias_status":"NOT_ESTABLISHED",
        "r5_unique_causal_attribution":"NOT_ESTABLISHED",
        "interpretation_boundary":"All eight traces reached the preregistered eight-post-source-turn cap and are fixed-horizon censored rather than monetary failures. This pass is structural only.",
    }
    summary["summary_hash"]=stable_hash(summary)
    return measurements,comparisons,case_rows,integrity_failures,summary


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--plan-root",required=True)
    ap.add_argument("--raw-root",required=True)
    ap.add_argument("--evidence-batch",required=True)
    ap.add_argument("--outdir",required=True)
    a=ap.parse_args()
    out=Path(a.outdir)
    if out.exists():
        raise ValueError("refusing_to_overwrite_v54_r7_structural")
    out.mkdir(parents=True)
    ms,cs,rows,failures,summary=derive(a.plan_root,a.raw_root,a.evidence_batch)
    write_jsonl(out/"r7_dual_process_measurements.jsonl",ms)
    write_jsonl(out/"r7_dual_structural_comparisons.jsonl",cs)
    write_jsonl(out/"r7_dual_case_index.jsonl",rows)
    write_jsonl(out/"integrity_failures.jsonl",failures)
    (out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("V5_4_R7_DUAL_STRUCTURAL=MATERIALIZED")
    print("MEASUREMENTS="+str(summary["measurement_count"]))
    print("COMPARISONS="+str(summary["comparison_count"]))
    print("INTEGRITY_FAILURES="+str(summary["integrity_failure_count"]))
    print("FIXED_HORIZON_CENSORED="+str(summary["fixed_horizon_censored_trace_count"]))
    print("OLD_LINEAGE_REENTRY_CASES="+str(summary["structured_repair_old_lineage_reentry_case_count"]))
    print("PRESERVED_UNRELATED_CASES="+str(summary["structured_repair_preserved_unrelated_structure_case_count"]))
    print("SUMMARY_HASH="+summary["summary_hash"])


if __name__=="__main__":
    main()
