from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
import tempfile
from pathlib import Path

def stable_json_bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def digest(value):
    return hashlib.sha256(stable_json_bytes(value)).hexdigest()

def verify_package(package):
    payload=dict(package)
    expected=payload.pop("package_hash",None)
    if package.get("repair_gate_status")!="COMPLETE_FOR_STRUCTURED_REPAIR":
        raise ValueError("PACKAGE_NOT_COMPLETE")
    if not expected or digest(payload)!=expected:
        raise ValueError("PACKAGE_HASH_MISMATCH")
    parent=package.get("parent_reconstruction") or {}
    if parent.get("status")!="VERIFIED" or parent.get("future_evidence_used") is not False:
        raise ValueError("PARENT_RECONSTRUCTION_NOT_VERIFIED")
    refs=parent.get("parent_hash_refs") or []
    if len(refs)!=1:
        raise ValueError("PARENT_HASH_CARDINALITY")
    if package.get("future_evidence_used") is not False:
        raise ValueError("FUTURE_EVIDENCE_USED")
    if package.get("semantic_audit_used") is not False or package.get("cpr_label") is not None:
        raise ValueError("SEMANTIC_SELECTION_LEAK")
    if not package.get("preserve_refs"):
        raise ValueError("EMPTY_PRESERVE_SET")
    if not package.get("allowed_repair_surface"):
        raise ValueError("NO_LEGAL_REPAIR_SURFACE")
    return refs[0]

def verify_checkpoint(root: Path, checkpoint_hash: str):
    cp=root/"checkpoints"/checkpoint_hash
    manifest=json.loads((cp/"manifest.json").read_text())
    if manifest.get("checkpoint_hash")!=checkpoint_hash:
        raise ValueError("CHECKPOINT_HASH_BINDING_MISMATCH")
    if manifest.get("restore_capability")!="FULL_NATIVE":
        raise ValueError("CHECKPOINT_NOT_FULL_NATIVE")
    native=json.loads((cp/"native_state.json").read_text())
    context=json.loads((cp/"model_context.json").read_text())
    if digest(native)!=manifest["native_state_sha256"]:
        raise ValueError("NATIVE_STATE_HASH_MISMATCH")
    if digest(context)!=manifest["model_visible_context_sha256"]:
        raise ValueError("MODEL_CONTEXT_HASH_MISMATCH")
    app=cp/"application"
    observed={}
    for path in sorted(app.rglob("*")):
        if path.is_file() and not path.is_symlink() and "__pycache__" not in path.parts and not str(path).endswith(".pyc"):
            observed[str(path.relative_to(app))]=hashlib.sha256(path.read_bytes()).hexdigest()
    if observed!=manifest.get("application_file_hashes"):
        raise ValueError("APPLICATION_MANIFEST_MISMATCH")
    if digest(observed)!=manifest["application_state_sha256"]:
        raise ValueError("APPLICATION_STATE_HASH_MISMATCH")
    return manifest

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--evidence-root",required=True)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    base=Path(args.evidence_root)
    selection=json.loads((base/"phase_a_provider_v2_b_selection_index.json").read_text())
    if selection.get("state")!="FROZEN_AFTER_ALL_15_PROVIDER_BACKED_A_V2":
        raise SystemExit("selection index is not frozen")
    cells=selection.get("cells") or []
    if selection.get("eligible_cell_count")!=15 or len(cells)!=15:
        raise SystemExit("expected 15 structural-package-eligible cells")

    rows=[]
    for sel in cells:
        cell=sel["cell_id"]
        row={"cell_id":cell,"structural_package_eligible":True,"execution_ready":False,"block_codes":[]}
        try:
            archive=base/"natural_A_provider_v2"/cell/"first_attempt.tar.gz"
            if not archive.is_file():
                raise ValueError("MISSING_A_ARCHIVE")
            with tempfile.TemporaryDirectory() as td:
                root=Path(td)
                with tarfile.open(archive,"r:gz") as tf:
                    tf.extractall(root)
                packages=json.loads((root/"repair_packages.json").read_text())
                matches=[p for p in packages if p.get("package_id")==sel.get("selected_package_id")]
                if len(matches)!=1:
                    raise ValueError("SELECTED_PACKAGE_NOT_UNIQUE")
                pkg=matches[0]
                if pkg.get("package_hash")!=sel.get("selected_package_hash"):
                    raise ValueError("SELECTION_PACKAGE_HASH_MISMATCH")
                parent_hash=verify_package(pkg)
                manifest=verify_checkpoint(root,parent_hash)
                if sel.get("selected_repair_anchor_ref")!=pkg.get("repair_anchor_ref"):
                    raise ValueError("REPAIR_ANCHOR_MISMATCH")

                preserve_files=[]
                for ref in pkg["preserve_refs"]:
                    if ref.startswith("file:"):
                        rel=ref[5:]
                        if rel not in manifest["application_file_hashes"]:
                            raise ValueError("PRESERVE_FILE_ABSENT:"+ref)
                        preserve_files.append(ref)

                external_checks=[]
                for ext in manifest.get("external_carrier_refs") or []:
                    family=ext.get("family")
                    check={"family":family,"source_ref":ext.get("source_ref"),"sha256":ext.get("sha256")}
                    if family=="memory-state":
                        src=root/"memorybank_state"/str(ext.get("source_ref"))
                        if not src.is_file():
                            check["status"]="BLOCKED_PARENT_MEMORY_FILE_MISSING"
                            row["block_codes"].append("FOREIGN_PARENT_STATE_RECONSTRUCTION_BLOCKED")
                        else:
                            observed=hashlib.sha256(src.read_bytes()).hexdigest()
                            check["observed_archive_sha256"]=observed
                            if observed!=ext.get("sha256"):
                                check["status"]="BLOCKED_PARENT_MEMORY_HASH_NO_LONGER_PRESENT"
                                row["block_codes"].append("FOREIGN_PARENT_STATE_RECONSTRUCTION_BLOCKED")
                            else:
                                check["status"]="RECONSTRUCTABLE_FROM_FROZEN_ARCHIVE"
                    elif family=="rag-hit":
                        check["status"]="IMMUTABLE_FROZEN_RAG_CORPUS_RECOMPUTABLE"
                    elif family=="compression-output":
                        check["status"]="RECOMPUTABLE_FROM_FROZEN_COMPRESSOR_AND_PARENT_HOST_CONTEXT"
                    else:
                        check["status"]="REFERENCE_BOUND"
                    external_checks.append(check)

                row.update({
                    "package_id":pkg["package_id"],
                    "package_hash":pkg["package_hash"],
                    "prefix_sequence":pkg["prefix_sequence"],
                    "repair_anchor_ref":pkg["repair_anchor_ref"],
                    "detection_surface":pkg["detection_surface"],
                    "affected_closure_refs":pkg["affected_closure_refs"],
                    "preserve_refs":pkg["preserve_refs"],
                    "preserve_file_ref_count":len(preserve_files),
                    "allowed_repair_surface":pkg["allowed_repair_surface"],
                    "parent_checkpoint_hash":parent_hash,
                    "parent_event_ref":manifest["event_ref"],
                    "parent_restore_capability":manifest["restore_capability"],
                    "parent_system_id":manifest["system_id"],
                    "remaining_horizon":manifest["remaining_horizon"],
                    "external_carrier_refs":manifest.get("external_carrier_refs") or [],
                    "external_reconstruction_checks":external_checks,
                    "future_evidence_used":False,
                    "semantic_audit_used":False,
                    "cpr_label_used":False,
                })
                row["block_codes"]=sorted(set(row["block_codes"]))
                row["execution_ready"]=not row["block_codes"]
                row["status"]="READY_FOR_ONE_PAIRED_B" if row["execution_ready"] else "FAIL_CLOSED_BEFORE_B"
        except Exception as exc:
            row["block_codes"]=sorted(set(row["block_codes"]+[str(exc)]))
            row["status"]="FAIL_CLOSED_BEFORE_B"
        rows.append(row)

    ready=[r["cell_id"] for r in rows if r["execution_ready"]]
    blocked=[{"cell_id":r["cell_id"],"block_codes":r["block_codes"]} for r in rows if not r["execution_ready"]]
    report={
        "schema":"stage2-r7-g1-phase-b-readiness-v2",
        "status":"PASS_WITH_FAIL_CLOSED_SUBSET" if blocked else "PASS_ALL_READY",
        "supersedes":"stage2/r7_g1_v1/control/phase_b_readiness_v1.json",
        "supersession_reason":"v1 validated package/checkpoint geometry but did not test reconstructability of mutable foreign parent state.",
        "source_evidence_root":"stage2/r7_g1_v1/natural_A_provider_v2",
        "source_selection_index":"stage2/r7_g1_v1/phase_a_provider_v2_b_selection_index.json",
        "structural_package_eligible_cells":15,
        "execution_ready_count":len(ready),
        "execution_ready_cells":ready,
        "execution_blocked_count":len(blocked),
        "execution_blocked_cells":blocked,
        "one_B_per_ready_cell":True,
        "same_parent_checkpoint_required":True,
        "semantic_audit_used":False,
        "cpr_labels_used":False,
        "provider_calls":0,
        "repair_actions":0,
        "cells":rows,
    }
    out=Path(args.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":report["status"],"ready":len(ready),"blocked":len(blocked),"blocked_cells":[x["cell_id"] for x in blocked]},sort_keys=True))

if __name__=="__main__":
    main()
