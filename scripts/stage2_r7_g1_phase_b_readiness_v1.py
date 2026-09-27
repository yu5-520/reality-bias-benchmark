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
    if package.get("repair_gate_status") != "COMPLETE_FOR_STRUCTURED_REPAIR":
        raise ValueError("package gate is not COMPLETE_FOR_STRUCTURED_REPAIR")
    payload=dict(package)
    expected=payload.pop("package_hash",None)
    if not expected or digest(payload)!=expected:
        raise ValueError("package hash mismatch")
    parent=package.get("parent_reconstruction") or {}
    if parent.get("status")!="VERIFIED" or parent.get("future_evidence_used") is not False:
        raise ValueError("parent reconstruction is not verified/future-blind")
    refs=parent.get("parent_hash_refs") or []
    if len(refs)!=1:
        raise ValueError("expected exactly one frozen parent checkpoint")
    if package.get("future_evidence_used") is not False or package.get("semantic_audit_used") is not False:
        raise ValueError("package is not prefix-only / semantic-blind")
    if package.get("cpr_label") is not None:
        raise ValueError("package contains CPR label")
    if not package.get("preserve_refs"):
        raise ValueError("package preserve set empty")
    if not package.get("allowed_repair_surface"):
        raise ValueError("package has no legal native repair surface")
    return refs[0]

def verify_checkpoint(root: Path, checkpoint_hash: str):
    cp=root/"checkpoints"/checkpoint_hash
    manifest=json.loads((cp/"manifest.json").read_text())
    if manifest.get("checkpoint_hash")!=checkpoint_hash:
        raise ValueError("checkpoint hash binding mismatch")
    if manifest.get("restore_capability")!="FULL_NATIVE":
        raise ValueError("checkpoint is not FULL_NATIVE")
    native=json.loads((cp/"native_state.json").read_text())
    context=json.loads((cp/"model_context.json").read_text())
    if digest(native)!=manifest["native_state_sha256"]:
        raise ValueError("native state hash mismatch")
    if digest(context)!=manifest["model_visible_context_sha256"]:
        raise ValueError("model context hash mismatch")
    app=cp/"application"
    observed={}
    for path in sorted(app.rglob("*")):
        if path.is_file() and not path.is_symlink() and "__pycache__" not in path.parts and not str(path).endswith(".pyc"):
            observed[str(path.relative_to(app))]=hashlib.sha256(path.read_bytes()).hexdigest()
    if observed!=manifest.get("application_file_hashes"):
        raise ValueError("application manifest mismatch")
    if digest(observed)!=manifest["application_state_sha256"]:
        raise ValueError("application state hash mismatch")
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
        raise SystemExit("expected exactly 15 eligible selected cells")
    rows=[]
    for sel in cells:
        cell=sel["cell_id"]
        archive=base/"natural_A_provider_v2"/cell/"first_attempt.tar.gz"
        if not archive.is_file():
            raise SystemExit(f"{cell}: missing A archive")
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            with tarfile.open(archive,"r:gz") as tf:
                tf.extractall(root)
            packages=json.loads((root/"repair_packages.json").read_text())
            matches=[p for p in packages if p.get("package_id")==sel.get("selected_package_id")]
            if len(matches)!=1:
                raise SystemExit(f"{cell}: selected package not uniquely present")
            pkg=matches[0]
            if pkg.get("package_hash")!=sel.get("selected_package_hash"):
                raise SystemExit(f"{cell}: selected package hash differs from frozen index")
            parent_hash=verify_package(pkg)
            manifest=verify_checkpoint(root,parent_hash)
            if sel.get("selected_repair_anchor_ref")!=pkg.get("repair_anchor_ref"):
                raise SystemExit(f"{cell}: repair anchor mismatch")
            preserve_file_refs=[]
            preserve_nonfile_refs=[]
            for ref in pkg["preserve_refs"]:
                if ref.startswith("file:"):
                    rel=ref[5:]
                    if rel not in manifest["application_file_hashes"]:
                        raise SystemExit(f"{cell}: preserve file absent from parent checkpoint: {ref}")
                    preserve_file_refs.append(ref)
                else:
                    preserve_nonfile_refs.append(ref)
            surfaces=list(pkg["allowed_repair_surface"])
            target=pkg["detection_surface"]
            if target.startswith(("rag-hit:","memory-recall:","memory-state:","compression-channel:","compression-input:","compression-output:")):
                legal_targets=[x.split(":",1)[1] if False else x for x in pkg["affected_closure_refs"][1:]]
                if not legal_targets:
                    raise SystemExit(f"{cell}: foreign detection surface lacks downstream legal target")
            rows.append({
                "cell_id":cell,
                "package_id":pkg["package_id"],
                "package_hash":pkg["package_hash"],
                "prefix_sequence":pkg["prefix_sequence"],
                "repair_anchor_ref":pkg["repair_anchor_ref"],
                "detection_surface":target,
                "affected_closure_refs":pkg["affected_closure_refs"],
                "preserve_refs":pkg["preserve_refs"],
                "preserve_file_ref_count":len(preserve_file_refs),
                "preserve_nonfile_ref_count":len(preserve_nonfile_refs),
                "allowed_repair_surface":surfaces,
                "parent_checkpoint_hash":parent_hash,
                "parent_event_ref":manifest["event_ref"],
                "parent_restore_capability":manifest["restore_capability"],
                "parent_system_id":manifest["system_id"],
                "remaining_horizon":manifest["remaining_horizon"],
                "external_carrier_refs":manifest.get("external_carrier_refs") or [],
                "future_evidence_used":False,
                "semantic_audit_used":False,
                "cpr_label_used":False,
                "status":"READY_FOR_ONE_PAIRED_B",
            })
    report={
        "schema":"stage2-r7-g1-phase-b-readiness-v1",
        "status":"PASS_ALL_15_READY_FOR_ONE_PAIRED_B",
        "source_evidence_root":"stage2/r7_g1_v1/natural_A_provider_v2",
        "source_selection_index":"stage2/r7_g1_v1/phase_a_provider_v2_b_selection_index.json",
        "eligible_cells":15,
        "ready_cells":len(rows),
        "one_B_per_cell":True,
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
    print(json.dumps({"status":report["status"],"ready_cells":len(rows)},sort_keys=True))

if __name__=="__main__":
    main()
