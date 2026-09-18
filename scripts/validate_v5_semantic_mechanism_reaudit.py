from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BINDING = ROOT / "configs/v5_semantic_mechanism_reaudit_source_binding_v0.1.json"
RECORDS = ROOT / "reviews/v5_semantic_mechanism_reaudit_2026-09-18/audit_records.jsonl"
SUMMARY = ROOT / "reviews/v5_semantic_mechanism_reaudit_2026-09-18/audit_summary.json"

REQUIRED = {
    "schema","audit_id","auditor","scope","evidence_binding","source_proposition",
    "semantic_role","relation_type","structural_facts_used","interpretation",
    "claim_status","causal_design_support","boundary"
}
ROLES = {
    "OBSERVATION","UNSTABLE_INFORMATION","ADOPTION","COUPLING","SEMANTIC_TRANSFORMATION",
    "AUTHORITY_MATERIALIZATION","AMPLIFICATION","STRUCTURAL_SUPPORT","STABLE_POOL_ENTRY",
    "DIRECT_POOL_CONSUMPTION","STRUCTURAL_EXPOSURE","LEGACY_JUMP","PERTURBATION_RESPONSE",
    "DRIVER_RESPONSE","INERTIA","RECOVERY","NOT_ESTABLISHED"
}
STATUSES={"SUPPORTED","SUPPORTED_CANDIDATE","NOT_ESTABLISHED","CONTRADICTED"}

def require(ok: bool, msg: str):
    if not ok:
        raise SystemExit("FAIL: " + msg)

def blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}".encode("ascii") + b"\x00" + data).hexdigest()

def main():
    binding=json.loads(BINDING.read_text(encoding="utf-8"))
    for src in binding["sources"]:
        p=ROOT/src["path"]
        require(p.exists(), "missing source " + src["path"])
        require(blob_sha(p.read_bytes())==src["git_blob_sha"], "source blob drift " + src["path"])

    rows=[]
    for line in RECORDS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r=json.loads(line)
        rows.append(r)
        require(REQUIRED.issubset(r), "missing required audit fields in " + r.get("audit_id","?"))
        require(r["schema"]=="RB-SEMANTIC-AUDIT-RECORD-v0.2", "wrong schema")
        require(r["semantic_role"] in ROLES, "invalid role " + r["audit_id"])
        require(r["claim_status"] in STATUSES, "invalid status " + r["audit_id"])
        require(len(r["evidence_binding"]["evidence_pointers"])>=1, "missing evidence pointer " + r["audit_id"])
        require(len(r["structural_facts_used"])>=1, "missing facts " + r["audit_id"])
        if r["relation_type"]=="CAUSES" and r["causal_design_support"] is False:
            require(r["claim_status"]!="SUPPORTED", "unsupported causal claim promoted")

    summary=json.loads(SUMMARY.read_text(encoding="utf-8"))
    require(summary["record_count"]==len(rows), "summary record count mismatch")
    require(summary["new_subject_calls"]==0, "audit may not add subject calls")
    require(summary["new_paid_evaluator_calls"]==0, "audit may not add paid evaluator calls")
    require(summary["raw_evidence_mutated"] is False, "raw evidence mutation forbidden")
    require(summary["cpr_status"]=="NOT_ADJUDICATED", "CPR status changed")
    require(summary["findings"]["stable_shared_pool_existence_by_R6_continuation"]=="SUPPORTED", "pool existence conclusion missing")
    require(summary["findings"]["first_stable_pool_entry"]=="NOT_ESTABLISHED", "first-pool boundary missing")
    require(summary["findings"]["structure_only_driver"]=="NOT_ESTABLISHED", "driver overclaim")

    print("PASS: v5 semantic/mechanism re-audit is source-bound and internally consistent")
    print("AUDIT_RECORD_COUNT=" + str(len(rows)))
    print("NEW_SUBJECT_CALLS=0")
    print("NEW_PAID_EVALUATOR_CALLS=0")
    print("CPR=NOT_ADJUDICATED")

if __name__=="__main__":
    main()
