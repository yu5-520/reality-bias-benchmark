#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, io, json, os, tarfile
from pathlib import Path, PurePosixPath

FORBIDDEN_PATH_TOKENS=(
    "monitor_evidence","monitor_candidates","repair_packages","runtime_bridge",
    "native_event_index","wire_index","semantic_audit_reference","cpr_prediction",
    "reference_records","blind_reference","full_context_pilot","provider_raw_cells",
    "provider_raw_attempts"
)

def sha256(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def safe_rel(path:str)->str:
    p=PurePosixPath(path)
    if p.is_absolute() or ".." in p.parts:
        raise RuntimeError(f"unsafe archive path: {path}")
    return str(p)

def member_map(ar:tarfile.TarFile):
    return {m.name.removeprefix("./"):m for m in ar.getmembers() if m.isfile()}

def read_member(ar,members,name):
    m=members.get(name)
    if not m:
        raise KeyError(name)
    f=ar.extractfile(m)
    return f.read() if f else b""

def verify_manifest(ar,members,manifest,group,cell):
    assert manifest["role"]=="MONITOR_BLIND_SEMANTIC_AUDIT_INPUT"
    assert manifest["monitor_runtime_bundle_readable_before_reference_seal"] is False
    assert manifest["group_id"]==group and manifest["cell_id"]==cell
    for row in manifest["entries"]:
        p=safe_rel(row["path"])
        low=p.lower()
        if any(tok in low for tok in FORBIDDEN_PATH_TOKENS):
            raise RuntimeError(f"forbidden reviewer input path: {p}")
        raw=read_member(ar,members,p)
        if sha256(raw)!=row["sha256"] or len(raw)!=row["bytes"]:
            raise RuntimeError(f"manifest mismatch: {group}/{cell}/{p}")

def export_cell(group,cell,cell_dir,out_dir):
    receipt_path=cell_dir/"attempt_receipt.json"
    receipt=json.loads(receipt_path.read_text())
    arc_path=cell_dir/"first_attempt.tar.gz"
    arc=arc_path.read_bytes()
    if sha256(arc)!=receipt["archive_sha256"]:
        raise RuntimeError(f"{group}/{cell}: first-attempt archive mismatch")

    target=out_dir/group/cell
    raw_root=target/"audit_raw"
    raw_root.mkdir(parents=True,exist_ok=True)

    with tarfile.open(fileobj=io.BytesIO(arc),mode="r:gz") as ar:
        members=member_map(ar)
        if "audit_raw_bundle_manifest.json" not in members:
            raise RuntimeError(f"{group}/{cell}: no audit_raw_bundle_manifest")
        manifest_raw=read_member(ar,members,"audit_raw_bundle_manifest.json")
        manifest=json.loads(manifest_raw)
        verify_manifest(ar,members,manifest,group,cell)

        exported=[]
        for row in manifest["entries"]:
            p=safe_rel(row["path"])
            raw=read_member(ar,members,p)
            dst=raw_root/p
            dst.parent.mkdir(parents=True,exist_ok=True)
            dst.write_bytes(raw)
            exported.append({
                "path":p,
                "sha256":row["sha256"],
                "bytes":row["bytes"],
                "text_utf8":_is_utf8(raw)
            })

        (target/"audit_raw_bundle_manifest.json").write_bytes(manifest_raw)
        (target/"attempt_receipt.json").write_text(
            json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
        )
        review={
            "schema":"stage2-gpt56sol-full-context-raw-review-cell-v1",
            "group_id":group,
            "cell_id":cell,
            "archive_sha256":receipt["archive_sha256"],
            "archive_bytes":receipt["archive_bytes"],
            "audit_raw_manifest_sha256":sha256(manifest_raw),
            "entry_count":len(exported),
            "entries":exported,
            "monitor_runtime_bundle_read":False,
            "blind_reference_labels_read":False,
            "blind_reference_records_read":False,
            "deepseek_full_context_pilot_outputs_read":False
        }
        (target/"review_input_manifest.json").write_text(
            json.dumps(review,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
        )
        return review

def _is_utf8(raw:bytes)->bool:
    try:
        raw.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False

def main():
    ap=argparse.ArgumentParser()
    for g in ("g2","g3","g4","g5"):
        ap.add_argument("--"+g,required=True)
    ap.add_argument("--config",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()

    cfg=json.loads(Path(a.config).read_text())
    assert cfg["status"]=="AUTHORIZED_FORMAL_LAYER_C"
    assert cfg["reviewer"]["model"]=="GPT-5.6 Sol"
    assert cfg["reviewer"]["execution_mode"]=="CHATGPT_NATIVE_REASONING"
    assert cfg["inputs"]["monitor_runtime_bundle_access"] is False
    assert cfg["inputs"]["blind_reference_labels_access"] is False
    assert cfg["inputs"]["blind_reference_records_access"] is False
    assert cfg["inputs"]["deepseek_full_context_pilot_outputs_access"] is False
    assert cfg["prohibited_actions"]["deepseek_formal_layer_c_calls"] is False

    eligible=set(cfg["population"]["eligible_cells"])
    assert len(eligible)==80
    roots={"G2":Path(a.g2),"G3":Path(a.g3),"G4":Path(a.g4),"G5":Path(a.g5)}
    out=Path(a.out)
    out.mkdir(parents=True,exist_ok=True)

    cells=[]
    for group in ("G2","G3","G4","G5"):
        root=roots[group]
        for x in range(1,8):
            for t in range(1,4):
                cell=f"X{x}-T{t}"
                full=f"{group}-{cell}"
                if full not in eligible:
                    continue
                cell_dir=root/"stage2"/"replication_v2"/group/"natural_A"/cell
                if not cell_dir.is_dir():
                    raise RuntimeError(f"missing frozen cell: {cell_dir}")
                review=export_cell(group,cell,cell_dir,out)
                cells.append({
                    "full_id":full,
                    "group_id":group,
                    "cell_id":cell,
                    "archive_sha256":review["archive_sha256"],
                    "audit_raw_manifest_sha256":review["audit_raw_manifest_sha256"],
                    "entry_count":review["entry_count"]
                })

    assert len(cells)==80
    index={
        "schema":"stage2-gpt56sol-full-context-raw-evidence-export-v1",
        "status":"SEALED_EXPORT_READY_FOR_GPT56SOL_REVIEW",
        "reviewer":"GPT-5.6 Sol",
        "execution_mode":"CHATGPT_NATIVE_REASONING",
        "cell_count":80,
        "cells":cells,
        "excluded_boundary_cells":cfg["population"]["excluded_boundary_cells"],
        "monitor_runtime_bundle_read":False,
        "blind_reference_labels_read":False,
        "blind_reference_records_read":False,
        "deepseek_full_context_pilot_outputs_read":False,
        "deepseek_api_calls":0,
        "subject_calls":0,
        "subject_reruns":0,
        "repair_calls":0,
        "monitor_evaluation":False
    }
    (out/"raw_evidence_export_index.json").write_text(
        json.dumps(index,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
    )
    print(json.dumps({
        "status":"PASS",
        "cells":80,
        "entries":sum(c["entry_count"] for c in cells)
    },sort_keys=True))

if __name__=="__main__":
    main()
