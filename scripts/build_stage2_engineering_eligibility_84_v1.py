#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import tarfile
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

GROUPS=("G2","G3","G4","G5")
SYSTEMS=tuple(f"X{i}" for i in range(1,8))
TASKS=("T1","T2","T3")
ROOT=Path("stage2/replication_v2/engineering_eligibility_84_v1")
EVIDENCE_ROOTS={g:Path(f"_{g.lower()}") for g in GROUPS}
CONTRACT=Path("configs/stage2_engineering_eligibility_84_contract_v1.json")

def stable_json_bytes(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")

def digest(value):
    return hashlib.sha256(stable_json_bytes(value)).hexdigest()

def sha256_file(path:Path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def load_json(path:Path):
    return json.loads(path.read_text())

def find_member(tf:tarfile.TarFile, basename:str):
    rows=[m for m in tf.getmembers() if m.isfile() and Path(m.name).name==basename]
    if not rows:
        return None
    if len(rows)!=1:
        raise ValueError(f"AMBIGUOUS_ARCHIVE_BASENAME:{basename}")
    return rows[0]

def read_member_bytes(tf:tarfile.TarFile, member):
    f=tf.extractfile(member)
    if f is None:
        raise ValueError(f"ARCHIVE_EXTRACT_FAILED:{member.name}")
    return f.read()

def classify_block(blocks, gate_statuses):
    values=set(blocks)|set(gate_statuses)
    if any("SAFETY" in x or "PROTOCOL" in x or "PRESERVE_SET" in x or "PACKAGE_HASH" in x for x in values):
        return "SAFETY_OR_PROTOCOL_BLOCKED"
    if any("PARENT" in x or "CHECKPOINT" in x or "NATIVE_STATE" in x or "MODEL_CONTEXT" in x or "APPLICATION_" in x for x in values):
        return "PARENT_RECONSTRUCTION_BLOCKED"
    if any("LINEAGE" in x for x in values):
        return "LINEAGE_GAP_BLOCKED"
    if any("NATIVE_CAPABILITY" in x or "NO_LEGAL_REPAIR_SURFACE" in x for x in values):
        return "NATIVE_CAPABILITY_BLOCKED"
    return "OBSERVABILITY_ONLY_NON_INTERVENABLE"

def verify_package(pkg):
    payload=dict(pkg)
    expected=payload.pop("package_hash",None)
    if pkg.get("repair_gate_status")!="COMPLETE_FOR_STRUCTURED_REPAIR":
        raise ValueError("PACKAGE_NOT_COMPLETE")
    if not expected or digest(payload)!=expected:
        raise ValueError("PACKAGE_HASH_MISMATCH")
    parent=pkg.get("parent_reconstruction") or {}
    if parent.get("status")!="VERIFIED":
        raise ValueError("PARENT_RECONSTRUCTION_NOT_VERIFIED")
    if parent.get("future_evidence_used") is not False:
        raise ValueError("PARENT_FUTURE_EVIDENCE_USED")
    refs=parent.get("parent_hash_refs") or []
    if len(refs)!=1:
        raise ValueError("PARENT_HASH_CARDINALITY")
    if pkg.get("future_evidence_used") is not False:
        raise ValueError("FUTURE_EVIDENCE_USED")
    if pkg.get("semantic_audit_used") is not False:
        raise ValueError("SEMANTIC_SELECTION_LEAK")
    if pkg.get("cpr_label") is not None:
        raise ValueError("CPR_LABEL_SELECTION_LEAK")
    if not pkg.get("preserve_refs"):
        raise ValueError("EMPTY_PRESERVE_SET")
    if not pkg.get("allowed_repair_surface"):
        raise ValueError("NO_LEGAL_REPAIR_SURFACE")
    return refs[0]

def checkpoint_dir(extracted:Path, checkpoint_hash:str):
    candidates=[
        extracted/"checkpoints"/checkpoint_hash,
        extracted/"checkpoint_store"/checkpoint_hash,
    ]
    for cp in candidates:
        if cp.is_dir():
            return cp
    hits=[p for p in extracted.rglob(checkpoint_hash) if p.is_dir() and (p/"manifest.json").is_file()]
    if len(hits)==1:
        return hits[0]
    raise ValueError("CHECKPOINT_DIRECTORY_MISSING")

def verify_checkpoint(extracted:Path, checkpoint_hash:str):
    cp=checkpoint_dir(extracted,checkpoint_hash)
    manifest=load_json(cp/"manifest.json")
    if manifest.get("checkpoint_hash")!=checkpoint_hash:
        raise ValueError("CHECKPOINT_HASH_BINDING_MISMATCH")
    if manifest.get("restore_capability")!="FULL_NATIVE":
        raise ValueError("CHECKPOINT_NOT_FULL_NATIVE")
    native_path=cp/"native_state.json"
    context_path=cp/"model_context.json"
    if not native_path.is_file():
        raise ValueError("NATIVE_STATE_MISSING")
    if not context_path.is_file():
        raise ValueError("MODEL_CONTEXT_MISSING")
    native=load_json(native_path)
    context=load_json(context_path)
    if digest(native)!=manifest.get("native_state_sha256"):
        raise ValueError("NATIVE_STATE_HASH_MISMATCH")
    if digest(context)!=manifest.get("model_visible_context_sha256"):
        raise ValueError("MODEL_CONTEXT_HASH_MISMATCH")

    app=cp/"application"
    if not app.is_dir():
        raise ValueError("APPLICATION_STATE_MISSING")
    observed={}
    for path in sorted(app.rglob("*")):
        if path.is_file() and not path.is_symlink() and "__pycache__" not in path.parts and not str(path).endswith(".pyc"):
            observed[str(path.relative_to(app))]=hashlib.sha256(path.read_bytes()).hexdigest()
    if observed!=manifest.get("application_file_hashes"):
        raise ValueError("APPLICATION_MANIFEST_MISMATCH")
    if digest(observed)!=manifest.get("application_state_sha256"):
        raise ValueError("APPLICATION_STATE_HASH_MISMATCH")
    return cp,manifest

def verify_external_state(extracted:Path, manifest):
    checks=[]
    blocks=[]
    for ext in manifest.get("external_carrier_refs") or []:
        family=ext.get("family")
        check={"family":family,"source_ref":ext.get("source_ref"),"sha256":ext.get("sha256")}
        if family=="memory-state":
            src=extracted/"memorybank_state"/str(ext.get("source_ref"))
            if not src.is_file():
                check["status"]="BLOCKED_PARENT_MEMORY_FILE_MISSING"
                blocks.append("FOREIGN_PARENT_STATE_RECONSTRUCTION_BLOCKED")
            else:
                observed=hashlib.sha256(src.read_bytes()).hexdigest()
                check["observed_archive_sha256"]=observed
                if observed!=ext.get("sha256"):
                    check["status"]="BLOCKED_PARENT_MEMORY_HASH_MISMATCH"
                    blocks.append("FOREIGN_PARENT_STATE_RECONSTRUCTION_BLOCKED")
                else:
                    check["status"]="RECONSTRUCTABLE_FROM_FROZEN_ARCHIVE"
        elif family=="rag-hit":
            check["status"]="IMMUTABLE_FROZEN_RAG_CORPUS_RECOMPUTABLE"
        elif family=="compression-output":
            check["status"]="RECOMPUTABLE_FROM_FROZEN_COMPRESSOR_AND_PARENT_HOST_CONTEXT"
        else:
            check["status"]="REFERENCE_BOUND"
        checks.append(check)
    return checks,sorted(set(blocks))

def main():
    contract=load_json(CONTRACT)
    assert contract["population"]["natural_cells"]==84
    assert contract["source_policy"]["semantic_audit_used"] is False
    assert contract["source_policy"]["layer_c_used"] is False
    assert contract["source_policy"]["package_selection"]=="EARLIEST_COMPLETE_PACKAGE_BY_PREFIX_SEQUENCE_THEN_PACKAGE_ID"

    ROOT.mkdir(parents=True,exist_ok=True)
    rows=[]
    group_rows=defaultdict(list)

    for group in GROUPS:
        evidence_root=EVIDENCE_ROOTS[group]
        for x in SYSTEMS:
            for t in TASKS:
                cell=f"{x}-{t}"
                full=f"{group}-{cell}"
                archive=evidence_root/f"stage2/replication_v2/{group}/natural_A/{cell}/first_attempt.tar.gz"
                if not archive.is_file():
                    raise FileNotFoundError(f"{full}:MISSING_FROZEN_NATURAL_ARCHIVE")
                row={
                    "full_id":full,
                    "group_id":group,
                    "cell_id":cell,
                    "system_id":x,
                    "task_id":t,
                    "source_archive_sha256":sha256_file(archive),
                    "semantic_audit_used":False,
                    "cpr_labels_used":False,
                    "layer_c_used":False,
                    "natural_rerun":False,
                    "B_authorized":False,
                }

                with tempfile.TemporaryDirectory() as td:
                    extracted=Path(td)
                    with tarfile.open(archive,"r:gz") as tf:
                        package_member=find_member(tf,"repair_packages.json")
                        candidate_member=find_member(tf,"monitor_candidates.json")
                        row["monitor_candidates_asset_present"]=candidate_member is not None
                        row["repair_packages_asset_present"]=package_member is not None
                        if package_member is None:
                            packages=[]
                            package_bytes=None
                        else:
                            package_bytes=read_member_bytes(tf,package_member)
                            packages=json.loads(package_bytes)
                            if not isinstance(packages,list):
                                raise ValueError(f"{full}:REPAIR_PACKAGES_NOT_LIST")
                        tf.extractall(extracted)

                    row["repair_packages_sha256"]=hashlib.sha256(package_bytes).hexdigest() if package_bytes is not None else None
                    row["package_count"]=len(packages)
                    gate_counts=Counter(str(p.get("repair_gate_status") or p.get("g1_block_code") or "UNCLASSIFIED") for p in packages)
                    row["package_gate_status_counts"]=dict(sorted(gate_counts.items()))
                    complete=[p for p in packages if p.get("repair_gate_status")=="COMPLETE_FOR_STRUCTURED_REPAIR"]
                    complete=sorted(complete,key=lambda p:(int(p.get("prefix_sequence") if p.get("prefix_sequence") is not None else 10**18),str(p.get("package_id") or "")))
                    row["complete_package_count"]=len(complete)

                    if not packages:
                        row["eligibility_state"]="NO_PROSPECTIVE_PACKAGE"
                        row["block_codes"]=["MONITOR_PACKAGE_ASSET_ABSENT"] if package_member is None else ["NO_PACKAGE_PRODUCED"]
                    elif not complete:
                        gates=sorted(gate_counts)
                        row["eligibility_state"]=classify_block([],gates)
                        row["block_codes"]=gates
                    else:
                        selected=complete[0]
                        row.update({
                            "selected_package_id":selected.get("package_id"),
                            "selected_package_hash":selected.get("package_hash"),
                            "selected_prefix_sequence":selected.get("prefix_sequence"),
                            "selected_repair_anchor_ref":selected.get("repair_anchor_ref"),
                            "selected_detection_surface":selected.get("detection_surface"),
                            "selected_allowed_repair_surface":selected.get("allowed_repair_surface") or [],
                            "selected_preserve_refs":selected.get("preserve_refs") or [],
                            "selection_rule":"EARLIEST_COMPLETE_PACKAGE_BY_PREFIX_SEQUENCE_THEN_PACKAGE_ID",
                        })
                        blocks=[]
                        checks=[]
                        try:
                            checkpoint_hash=verify_package(selected)
                            cp,manifest=verify_checkpoint(extracted,checkpoint_hash)
                            row.update({
                                "selected_parent_checkpoint_hash":checkpoint_hash,
                                "parent_event_ref":manifest.get("event_ref"),
                                "parent_restore_capability":manifest.get("restore_capability"),
                                "parent_system_id":manifest.get("system_id"),
                                "remaining_horizon":manifest.get("remaining_horizon"),
                                "external_carrier_refs":manifest.get("external_carrier_refs") or [],
                                "checkpoint_manifest_sha256":sha256_file(cp/"manifest.json"),
                            })
                            checks,external_blocks=verify_external_state(extracted,manifest)
                            blocks.extend(external_blocks)
                        except Exception as exc:
                            blocks.append(str(exc))
                        row["external_reconstruction_checks"]=checks
                        row["block_codes"]=sorted(set(blocks))
                        if blocks:
                            row["eligibility_state"]=classify_block(row["block_codes"],[])
                        else:
                            row["eligibility_state"]="ELIGIBLE_FOR_ONE_B"
                            row["B_authorized"]=False

                rows.append(row)
                group_rows[group].append(row)

    assert len(rows)==84
    outcome_counts=Counter(r["eligibility_state"] for r in rows)
    by_group={}
    for g in GROUPS:
        gr=group_rows[g]
        oc=Counter(r["eligibility_state"] for r in gr)
        eligible=[r["full_id"] for r in gr if r["eligibility_state"]=="ELIGIBLE_FOR_ONE_B"]
        by_group[g]={
            "cell_count":len(gr),
            "outcome_counts":dict(sorted(oc.items())),
            "eligible_count":len(eligible),
            "eligible_cells":eligible,
        }

    ledger={
        "schema":"stage2-engineering-eligibility-84-ledger-v1",
        "state":"SEALED",
        "population":"G2_G5_84_NATURAL_A",
        "cell_count":84,
        "selection_rule":"EARLIEST_COMPLETE_PACKAGE_BY_PREFIX_SEQUENCE_THEN_PACKAGE_ID",
        "source":"PROSPECTIVELY_FROZEN_MONITOR_CHECKPOINT_PACKAGE_PIPELINE_ONLY",
        "semantic_audit_used":False,
        "cpr_labels_used":False,
        "layer_c_used":False,
        "subject_provider_calls":0,
        "paid_evaluator_calls":0,
        "repair_calls":0,
        "natural_reruns":0,
        "one_B_per_eligible_cell":True,
        "B_executed":False,
        "outcome_counts":dict(sorted(outcome_counts.items())),
        "by_group":by_group,
        "cells":rows,
    }
    (ROOT/"eligibility_ledger.json").write_text(json.dumps(ledger,ensure_ascii=False,indent=2,sort_keys=True)+"\n")

    for g in GROUPS:
        selected=[]
        for r in group_rows[g]:
            if r["eligibility_state"]!="ELIGIBLE_FOR_ONE_B":
                continue
            selected.append({
                "full_id":r["full_id"],
                "cell_id":r["cell_id"],
                "selected_package_id":r["selected_package_id"],
                "selected_package_hash":r["selected_package_hash"],
                "selected_prefix_sequence":r["selected_prefix_sequence"],
                "selected_repair_anchor_ref":r["selected_repair_anchor_ref"],
                "selected_parent_checkpoint_hash":r["selected_parent_checkpoint_hash"],
                "remaining_horizon":r.get("remaining_horizon"),
                "B_authorized":False,
                "selection_used_semantic_audit":False,
                "selection_used_cpr_label":False,
            })
        index={
            "schema":"stage2-engineering-group-b-selection-index-v1",
            "state":"FROZEN_ELIGIBILITY_NOT_B_AUTHORIZATION",
            "group_id":g,
            "source_eligibility_ledger":"stage2/replication_v2/engineering_eligibility_84_v1/eligibility_ledger.json",
            "selector":"EARLIEST_COMPLETE_PACKAGE_BY_PREFIX_SEQUENCE_THEN_PACKAGE_ID",
            "eligible_cell_count":len(selected),
            "cells":selected,
            "B_executed":False,
            "B_authorized":False,
            "semantic_audit_used":False,
            "cpr_labels_used":False,
        }
        (ROOT/f"{g}_b_selection_index.json").write_text(json.dumps(index,ensure_ascii=False,indent=2,sort_keys=True)+"\n")

    seal={
        "schema":"stage2-engineering-eligibility-84-seal-v1",
        "state":"SEALED",
        "population":"G2_G5_84_NATURAL_A",
        "cell_count":84,
        "eligibility_ledger_sha256":sha256_file(ROOT/"eligibility_ledger.json"),
        "group_selection_sha256":{g:sha256_file(ROOT/f"{g}_b_selection_index.json") for g in GROUPS},
        "outcome_counts":dict(sorted(outcome_counts.items())),
        "semantic_audit_used":False,
        "cpr_labels_used":False,
        "layer_c_used":False,
        "subject_provider_calls":0,
        "paid_evaluator_calls":0,
        "repair_calls":0,
        "natural_reruns":0,
        "B_executed":False,
        "next_stage":"G2_ENGINEERING_B_AUTHORIZATION",
    }
    (ROOT/"eligibility_seal.json").write_text(json.dumps(seal,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "status":"PASS",
        "cells":84,
        "outcomes":dict(sorted(outcome_counts.items())),
        "eligible_by_group":{g:by_group[g]["eligible_count"] for g in GROUPS}
    },sort_keys=True))

if __name__=="__main__":
    main()
