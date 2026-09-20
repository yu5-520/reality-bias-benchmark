#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/r8a_dynamic_cpr_first_round_source_binding_v0.1.json"


def require(cond, msg):
    if not cond:
        raise SystemExit("R8A_VALIDATION_FAILED: " + msg)


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_config():
    cfg=load(CONFIG)
    require(cfg["schema"]=="RB-R8A-DYNAMIC-CPR-FIRST-ROUND-SOURCE-BINDING-v0.1","config schema")
    require(cfg["expected"]["complete_route_audits"]==32,"complete route count")
    require(cfg["expected"]["canonical_r5_r6_audits"]==29,"R5/R6 count")
    require(cfg["expected"]["route_nodes"]==908,"route node count")
    require(cfg["expected"]["semantic_edges"]==194,"semantic edge count")
    require(cfg["expected"]["lineage_closures"]==4,"lineage closure count")
    require(cfg["expected"]["r7_overlay_arms"]==8,"R7 arm count")
    e=cfg["execution_boundary"]
    require(e["new_provider_calls"]==0,"provider calls must be zero")
    require(e["new_paid_evaluator_calls"]==0,"paid evaluator calls must be zero")
    require(e["subject_reruns"]==0,"subject reruns must be zero")
    require(e["mutate_raw_evidence"] is False,"raw evidence mutation forbidden")
    require(e["adjudicate_cpr"] is False,"R8-A must not adjudicate CPR")
    for rel in [
        "docs/R_Plan_v5.5.md",
        "theory/theory_contract_v0.16.md",
        "docs/R8_Dynamic_CPR_Permission_Penetration_Protocol_v0.3.md",
        "configs/cpr_definition_contract_v0.3.json",
        "configs/cpr_adjudication_contract_v0.3.json",
        "arena/build_r8a_dynamic_cpr_first_round.py",
    ]:
        require((ROOT/rel).exists(),"missing "+rel)


def validate_result(result_dir):
    cfg=load(CONFIG)
    out=Path(result_dir)
    s=load(out/"summary.json")
    m=load(out/"manifest.json")
    exp=cfg["expected"]
    require(s["source_complete_route_audit_count"]==exp["complete_route_audits"],"source audit count")
    require(s["natural_audit_count"]==exp["natural_audits"],"natural audit count")
    require(s["r5_r6_audit_count"]==exp["canonical_r5_r6_audits"],"R5/R6 audit count")
    require(s["permission_review_packet_count"]==exp["permission_review_packets"],"packet count")
    require(s["r7_overlay_case_count"]==exp["r7_overlay_cases"],"R7 case count")
    require(s["r6_lineage_closure_case_count"]==exp["lineage_closures"],"lineage count")
    require(s["ledger_event_kind_counts"]["ROUTE_NODE"]==exp["route_nodes"],"route ledger count")
    require(s["ledger_event_kind_counts"]["SEMANTIC_EDGE"]==exp["semantic_edges"],"edge ledger count")
    require(s["ledger_event_kind_counts"]["R7_CONTROL_OVERLAY"]==exp["r7_overlay_arms"],"R7 overlay count")
    require(s["stronger_system_inertia_packet_count"]==exp["stronger_system_inertia_cases"],"stronger case count")
    require(s["semantic_cpr_adjudicated_case_count"]==0,"R8-A CPR adjudication forbidden")
    require(s["semantic_cpr_status"]=="NOT_ADJUDICATED","semantic status")
    require(s["execution_boundary"]["new_provider_calls"]==0,"result provider calls")
    require(s["execution_boundary"]["new_paid_evaluator_calls"]==0,"result evaluator calls")
    require(s["execution_boundary"]["subject_reruns"]==0,"result reruns")
    require(s["execution_boundary"]["raw_evidence_mutated"] is False,"result raw mutation")
    require(m["status"]=="FROZEN_DERIVATIVE_R8A_MATERIAL","manifest status")
    for name in ["case_index.jsonl","semantic_event_ledger.jsonl","permission_review_packets.jsonl","summary.json"]:
        require((out/name).exists(),"missing output "+name)
        require(name in m["outputs"],"manifest output missing "+name)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--config-only",action="store_true")
    ap.add_argument("--result-dir")
    a=ap.parse_args()
    validate_config()
    if a.result_dir:
        validate_result(a.result_dir)
    print("R8A_VALIDATION=PASS")
    print("CPR_ADJUDICATION=NO")
    print("SUBJECT_RERUN_REQUIRED=NO")


if __name__=="__main__":
    main()
