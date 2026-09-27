#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import tarfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from stage2.r7_checkpoint_v1.common import digest

ROOT = Path("stage2/replication_v2/engineering_eligibility_84_v1")
CONTRACT = Path("configs/stage2_g2_g5_engineering_eligibility_contract_v1.json")
GROUPS = ("G2", "G3", "G4", "G5")
XS = tuple(f"X{i}" for i in range(1, 8))
TS = ("T1", "T2", "T3")
EVIDENCE_ROOTS = {g: Path(f"_{g.lower()}") for g in GROUPS}

GATE_TO_STATE = {
    "PARENT_RECONSTRUCTION_BLOCKED": "PARENT_RECONSTRUCTION_BLOCKED",
    "LINEAGE_GAP_BLOCKED": "LINEAGE_GAP_BLOCKED",
    "NATIVE_CAPABILITY_BLOCKED": "NATIVE_CAPABILITY_BLOCKED",
    "SAFETY_BOUNDARY_BLOCKED": "SAFETY_OR_PROTOCOL_BLOCKED",
    "NO_REPAIR_REQUIRED": "NO_PROSPECTIVE_PACKAGE",
}
KNOWN_GATES = set(GATE_TO_STATE) | {"COMPLETE_FOR_STRUCTURED_REPAIR"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def tar_members_by_basename(tf: tarfile.TarFile, basename: str):
    return [m for m in tf.getmembers() if m.isfile() and Path(m.name).name == basename]


def read_json_member(tf: tarfile.TarFile, basename: str):
    matches = tar_members_by_basename(tf, basename)
    if not matches:
        return None, None, None
    if len(matches) != 1:
        raise RuntimeError(f"ambiguous {basename}: {[m.name for m in matches]}")
    member = matches[0]
    fh = tf.extractfile(member)
    if fh is None:
        raise RuntimeError(f"cannot extract {member.name}")
    raw = fh.read()
    return json.loads(raw), hashlib.sha256(raw).hexdigest(), member.name


def package_order(p: dict[str, Any]):
    seq = p.get("prefix_sequence")
    if not isinstance(seq, int):
        seq = 10**12
    return (seq, str(p.get("package_id") or ""))


def package_hash_valid(p: dict[str, Any]) -> bool:
    expected = p.get("package_hash")
    if not isinstance(expected, str) or len(expected) != 64:
        return False
    body = {k: v for k, v in p.items() if k != "package_hash"}
    return digest(body) == expected


def validate_no_semantic_leak(p: dict[str, Any], full_id: str):
    if p.get("semantic_audit_used") is not False:
        raise RuntimeError(f"{full_id}: package uses semantic audit")
    if p.get("future_evidence_used") is not False:
        raise RuntimeError(f"{full_id}: package uses future evidence")
    if p.get("cpr_label") is not None:
        raise RuntimeError(f"{full_id}: package contains CPR label")
    parent = p.get("parent_reconstruction") or {}
    if parent.get("future_evidence_used") is not False:
        raise RuntimeError(f"{full_id}: parent reconstruction uses future evidence")


def validate_selected_parent(
    *,
    full_id: str,
    package: dict[str, Any],
    ledger: dict[str, Any] | None,
):
    if ledger is None:
        raise RuntimeError(f"{full_id}: selected COMPLETE package has no checkpoint ledger")
    parent = package.get("parent_reconstruction") or {}
    if parent.get("status") != "VERIFIED":
        raise RuntimeError(f"{full_id}: selected COMPLETE package parent is not VERIFIED")
    refs = parent.get("parent_hash_refs") or []
    if len(refs) != 1 or not isinstance(refs[0], str) or not refs[0]:
        raise RuntimeError(f"{full_id}: selected COMPLETE package must bind one parent checkpoint hash")
    parent_hash = refs[0]

    checkpoints = ledger.get("checkpoints") or []
    matching = [c for c in checkpoints if c.get("checkpoint_hash") == parent_hash]
    if not matching:
        raise RuntimeError(f"{full_id}: selected parent hash does not resolve in checkpoint ledger")
    if not any(c.get("restore_capability") == "FULL_NATIVE" for c in matching):
        raise RuntimeError(f"{full_id}: selected parent checkpoint is not FULL_NATIVE")
    if ledger.get("first_eligible_checkpoint_hash") != parent_hash:
        raise RuntimeError(f"{full_id}: first eligible checkpoint hash does not match selected package")
    if ledger.get("first_eligible_event_ref") != package.get("prefix_cutoff_ref"):
        raise RuntimeError(f"{full_id}: first eligible event ref does not match selected package")

    eligible_rows = [
        c for c in matching
        if c.get("boundary") == "FIRST_MONITOR_REPAIR_ELIGIBLE_POINT"
        and c.get("event_ref") == package.get("prefix_cutoff_ref")
    ]
    if not eligible_rows:
        raise RuntimeError(f"{full_id}: selected parent lacks FIRST_MONITOR_REPAIR_ELIGIBLE ledger row")
    return {
        "checkpoint_hash": parent_hash,
        "checkpoint_id": eligible_rows[0].get("checkpoint_id"),
        "model_decision_sequence": eligible_rows[0].get("model_decision_sequence"),
        "restore_capability": eligible_rows[0].get("restore_capability"),
    }


def main():
    contract = load_json(CONTRACT)
    if contract["status"] != "FROZEN_BEFORE_84_CELL_ELIGIBILITY_EXECUTION":
        raise RuntimeError("eligibility contract is not frozen")
    if contract["population"]["natural_cells"] != 84:
        raise RuntimeError("eligibility population is not 84")
    if contract["authorization"]["subject_provider_calls"] is not False:
        raise RuntimeError("subject calls unexpectedly authorized")
    if contract["authorization"]["repair_calls"] is not False:
        raise RuntimeError("repair calls unexpectedly authorized")

    ROOT.mkdir(parents=True, exist_ok=True)
    rows = []
    selected_packages = []
    state_counts = Counter()
    package_gate_counts_total = Counter()
    by_group = defaultdict(Counter)
    by_system = defaultdict(Counter)
    by_task = defaultdict(Counter)

    for group in GROUPS:
        root = EVIDENCE_ROOTS[group]
        for x in XS:
            for t in TS:
                cell = f"{x}-{t}"
                full_id = f"{group}-{cell}"
                archive = root / f"stage2/replication_v2/{group}/natural_A/{cell}/first_attempt.tar.gz"
                if not archive.is_file():
                    raise FileNotFoundError(f"{full_id}: missing natural archive {archive}")

                archive_sha = sha256_file(archive)
                with tarfile.open(archive, "r:gz") as tf:
                    packages, package_file_sha, package_member = read_json_member(tf, "repair_packages.json")
                    candidates, candidate_file_sha, candidate_member = read_json_member(tf, "monitor_candidates.json")
                    ledger, ledger_sha, ledger_member = read_json_member(tf, "checkpoint_ledger.json")
                    seal, seal_sha, seal_member = read_json_member(tf, "seal.json")
                    manifest, manifest_sha, manifest_member = read_json_member(tf, "run_manifest.json")

                package_file_present = packages is not None
                candidate_file_present = candidates is not None
                ledger_present = ledger is not None

                if packages is not None and not isinstance(packages, list):
                    raise TypeError(f"{full_id}: repair_packages.json must be list")
                if candidates is not None and not isinstance(candidates, list):
                    raise TypeError(f"{full_id}: monitor_candidates.json must be list")
                packages = packages or []
                candidates = candidates or []

                if seal is not None:
                    if seal.get("cell_id") != cell:
                        raise RuntimeError(f"{full_id}: seal cell mismatch")
                    if seal.get("group_id") not in {group, f"StageII-{group}"}:
                        raise RuntimeError(f"{full_id}: seal group mismatch: {seal.get('group_id')}")
                    if seal.get("repair_actions_during_A") != 0:
                        raise RuntimeError(f"{full_id}: repair occurred during Natural A")

                candidate_hashes = {
                    c.get("candidate_hash") for c in candidates
                    if isinstance(c, dict) and c.get("candidate_hash")
                }
                for c in candidates:
                    if not isinstance(c, dict):
                        raise TypeError(f"{full_id}: candidate record must be object")
                    if c.get("semantic_audit_used") is not False:
                        raise RuntimeError(f"{full_id}: candidate uses semantic audit")
                    if c.get("future_evidence_used") is not False:
                        raise RuntimeError(f"{full_id}: candidate uses future evidence")
                    if c.get("cpr_label") is not None:
                        raise RuntimeError(f"{full_id}: candidate contains CPR label")

                gates = Counter()
                package_hashes = set()
                for p in packages:
                    if not isinstance(p, dict):
                        raise TypeError(f"{full_id}: package record must be object")
                    validate_no_semantic_leak(p, full_id)
                    if p.get("source_cell") != cell:
                        raise RuntimeError(f"{full_id}: package source_cell mismatch")
                    gate = p.get("repair_gate_status")
                    if gate not in KNOWN_GATES:
                        raise RuntimeError(f"{full_id}: unknown package gate {gate}")
                    if not package_hash_valid(p):
                        raise RuntimeError(f"{full_id}: invalid package hash {p.get('package_id')}")
                    ph = p["package_hash"]
                    if ph in package_hashes:
                        raise RuntimeError(f"{full_id}: duplicate package hash")
                    package_hashes.add(ph)
                    gates[gate] += 1
                    package_gate_counts_total[gate] += 1

                if seal is not None and "complete_package_count" in seal:
                    expected_complete = sum(
                        1 for p in packages
                        if p.get("repair_gate_status") == "COMPLETE_FOR_STRUCTURED_REPAIR"
                    )
                    if int(seal.get("complete_package_count", -1)) != expected_complete:
                        raise RuntimeError(f"{full_id}: seal complete-package count mismatch")

                completes = sorted(
                    [p for p in packages if p.get("repair_gate_status") == "COMPLETE_FOR_STRUCTURED_REPAIR"],
                    key=package_order,
                )

                selected = None
                selected_parent = None
                primary_blocker = None

                if completes:
                    selected = completes[0]
                    selected_parent = validate_selected_parent(
                        full_id=full_id,
                        package=selected,
                        ledger=ledger,
                    )
                    state = "ELIGIBLE_FOR_ONE_B"
                    selected_packages.append({
                        "full_id": full_id,
                        "group_id": group,
                        "cell_id": cell,
                        "package_id": selected["package_id"],
                        "package_hash": selected["package_hash"],
                        "prefix_sequence": selected.get("prefix_sequence"),
                        "prefix_cutoff_ref": selected.get("prefix_cutoff_ref"),
                        "content_address": selected.get("content_address"),
                        "repair_anchor_ref": selected.get("repair_anchor_ref"),
                        "allowed_repair_surface": selected.get("allowed_repair_surface") or [],
                        "preserve_refs": selected.get("preserve_refs") or [],
                        "parent": selected_parent,
                        "selection_rule": "EARLIEST_COMPLETE_PROSPECTIVE_PACKAGE",
                    })
                elif not package_file_present:
                    state = "OBSERVABILITY_ONLY_NON_INTERVENABLE"
                elif not packages:
                    state = "NO_PROSPECTIVE_PACKAGE"
                else:
                    earliest = sorted(packages, key=package_order)[0]
                    gate = earliest.get("repair_gate_status")
                    primary_blocker = gate
                    state = GATE_TO_STATE[gate]

                row = {
                    "full_id": full_id,
                    "group_id": group,
                    "cell_id": cell,
                    "system_id": x,
                    "task_id": t,
                    "natural_archive_sha256": archive_sha,
                    "repair_package_file_present": package_file_present,
                    "repair_package_file_sha256": package_file_sha,
                    "repair_package_member": package_member,
                    "monitor_candidate_file_present": candidate_file_present,
                    "monitor_candidate_file_sha256": candidate_file_sha,
                    "monitor_candidate_member": candidate_member,
                    "checkpoint_ledger_present": ledger_present,
                    "checkpoint_ledger_sha256": ledger_sha,
                    "checkpoint_ledger_member": ledger_member,
                    "seal_present": seal is not None,
                    "seal_sha256": seal_sha,
                    "seal_member": seal_member,
                    "run_manifest_present": manifest is not None,
                    "run_manifest_sha256": manifest_sha,
                    "run_manifest_member": manifest_member,
                    "natural_status": seal.get("status") if isinstance(seal, dict) else None,
                    "candidate_count": len(candidates),
                    "package_count": len(packages),
                    "package_gate_counts": dict(sorted(gates.items())),
                    "selected_package_id": selected.get("package_id") if selected else None,
                    "selected_package_hash": selected.get("package_hash") if selected else None,
                    "selected_prefix_sequence": selected.get("prefix_sequence") if selected else None,
                    "selected_parent": selected_parent,
                    "primary_blocker": primary_blocker,
                    "eligibility_state": state,
                    "semantic_audit_used": False,
                    "audit_backfill_used": False,
                    "maximum_B_authorized_if_later_opened": 1 if state == "ELIGIBLE_FOR_ONE_B" else 0,
                }
                rows.append(row)
                state_counts[state] += 1
                by_group[group][state] += 1
                by_system[x][state] += 1
                by_task[t][state] += 1

    if len(rows) != 84:
        raise RuntimeError(f"expected 84 eligibility rows, got {len(rows)}")
    if len({r["full_id"] for r in rows}) != 84:
        raise RuntimeError("duplicate eligibility cell identity")
    if len(selected_packages) != state_counts["ELIGIBLE_FOR_ONE_B"]:
        raise RuntimeError("selected package count != eligible cell count")

    ledger = {
        "schema": "stage2-g2-g5-engineering-eligibility-ledger-v1",
        "state": "SEALED",
        "population": "G2_G5_84_NATURAL_A",
        "cell_count": 84,
        "contract": str(CONTRACT),
        "semantic_audit_used": False,
        "audit_backfill_used": False,
        "subject_provider_calls": 0,
        "paid_evaluator_calls": 0,
        "repair_calls": 0,
        "natural_reruns": 0,
        "rows": rows,
    }
    (ROOT / "eligibility_ledger.json").write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n")

    selected = {
        "schema": "stage2-g2-g5-selected-engineering-packages-v1",
        "state": "SEALED",
        "selection_rule": "EARLIEST_COMPLETE_PROSPECTIVE_PACKAGE",
        "selected_package_count": len(selected_packages),
        "maximum_B_per_selected_package": 1,
        "packages": selected_packages,
    }
    (ROOT / "selected_packages.json").write_text(json.dumps(selected, indent=2, sort_keys=True) + "\n")

    summary = {
        "schema": "stage2-g2-g5-engineering-eligibility-summary-v1",
        "state": "SEALED",
        "population": "G2_G5_84_NATURAL_A",
        "cell_count": 84,
        "eligibility_state_counts": dict(sorted(state_counts.items())),
        "package_gate_counts": dict(sorted(package_gate_counts_total.items())),
        "selected_package_count": len(selected_packages),
        "by_group": {k: dict(sorted(v.items())) for k, v in sorted(by_group.items())},
        "by_system": {k: dict(sorted(v.items())) for k, v in sorted(by_system.items())},
        "by_task": {k: dict(sorted(v.items())) for k, v in sorted(by_task.items())},
        "evidence_availability": {
            "repair_package_file_present": sum(r["repair_package_file_present"] for r in rows),
            "repair_package_file_absent": sum(not r["repair_package_file_present"] for r in rows),
            "monitor_candidate_file_present": sum(r["monitor_candidate_file_present"] for r in rows),
            "monitor_candidate_file_absent": sum(not r["monitor_candidate_file_present"] for r in rows),
            "checkpoint_ledger_present": sum(r["checkpoint_ledger_present"] for r in rows),
            "checkpoint_ledger_absent": sum(not r["checkpoint_ledger_present"] for r in rows),
        },
        "claim_boundary": {
            "repair_efficacy_tested": False,
            "engineering_B_executed": False,
            "semantic_audit_used_to_create_package": False,
            "audit_miss_backfilled": False,
            "blocked_cells_are_not_repair_failures": True,
        },
        "next_gate": "G2_ENGINEERING_B_BATCH_AUTHORIZATION_IF_G2_ELIGIBLE_COUNT_GT_0",
    }
    (ROOT / "eligibility_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    report = [
        "# Stage-II G2-G5 84-Cell Engineering Eligibility Report v1",
        "",
        "Date: 2026-09-27  ",
        "Status: **84-CELL ELIGIBILITY SEALED / NO ENGINEERING B EXECUTED**",
        "",
        "## Population",
        "",
        "- G2-G5 Natural A: **84/84**;",
        "- semantic-audit input used for eligibility: **NO**;",
        "- audit miss backfill: **NO**;",
        "- Natural-A reruns: **0**;",
        "- subject/provider calls: **0**;",
        "- paid evaluator calls: **0**;",
        "- repair calls: **0**.",
        "",
        "## Eligibility accounting",
        "",
    ]
    for k, v in sorted(state_counts.items()):
        report.append(f"- {k}: **{v}**")
    report += [
        "",
        f"Selected earliest COMPLETE prospective packages: **{len(selected_packages)}**.",
        "",
        "## Package-gate accounting",
        "",
    ]
    for k, v in sorted(package_gate_counts_total.items()):
        report.append(f"- {k}: **{v}** packages")
    report += [
        "",
        "## Group accounting",
        "",
        "| Group | Eligible | No package | Parent blocked | Lineage blocked | Native blocked | Safety/protocol blocked | Observability-only |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for g in GROUPS:
        cnt = by_group[g]
        report.append(
            f"| {g} | {cnt['ELIGIBLE_FOR_ONE_B']} | {cnt['NO_PROSPECTIVE_PACKAGE']} | "
            f"{cnt['PARENT_RECONSTRUCTION_BLOCKED']} | {cnt['LINEAGE_GAP_BLOCKED']} | "
            f"{cnt['NATIVE_CAPABILITY_BLOCKED']} | {cnt['SAFETY_OR_PROTOCOL_BLOCKED']} | "
            f"{cnt['OBSERVABILITY_ONLY_NON_INTERVENABLE']} |"
        )
    report += [
        "",
        "## Cell ledger",
        "",
        "| Cell | Candidates | Packages | Package gates | Eligibility | Selected package |",
        "| --- | ---: | ---: | --- | --- | --- |",
    ]
    for r in rows:
        report.append(
            f"| {r['full_id']} | {r['candidate_count']} | {r['package_count']} | "
            f"`{json.dumps(r['package_gate_counts'], sort_keys=True)}` | "
            f"{r['eligibility_state']} | {r['selected_package_id'] or '-'} |"
        )
    report += [
        "",
        "## Interpretation boundary",
        "",
        "Eligibility is not repair efficacy. A blocked cell is a boundary observation, not a failed repair. "
        "Only a prospectively frozen COMPLETE package with a machine-verified FULL_NATIVE same-parent checkpoint "
        "can enter a later one-shot B authorization.",
        "",
        "## Next gate",
        "",
        "If G2 contains one or more eligible cells, freeze the exact G2 B launch population from the selected-package ledger. "
        "Do not add audit-discovered packages, do not rerun Natural A, and do not launch more than one B per selected cell.",
    ]
    (ROOT / "eligibility_report.md").write_text("\n".join(report) + "\n")

    seal = {
        "schema": "stage2-g2-g5-engineering-eligibility-seal-v1",
        "state": "SEALED",
        "cell_count": 84,
        "eligible_cell_count": state_counts["ELIGIBLE_FOR_ONE_B"],
        "selected_package_count": len(selected_packages),
        "contract_sha256": sha256_file(CONTRACT),
        "eligibility_ledger_sha256": sha256_file(ROOT / "eligibility_ledger.json"),
        "eligibility_summary_sha256": sha256_file(ROOT / "eligibility_summary.json"),
        "selected_packages_sha256": sha256_file(ROOT / "selected_packages.json"),
        "eligibility_report_sha256": sha256_file(ROOT / "eligibility_report.md"),
        "semantic_audit_used": False,
        "audit_backfill_used": False,
        "subject_provider_calls": 0,
        "repair_calls": 0,
        "next_gate": "G2_ENGINEERING_B_BATCH_AUTHORIZATION",
    }
    (ROOT / "eligibility_seal.json").write_text(json.dumps(seal, indent=2, sort_keys=True) + "\n")

    print(json.dumps({
        "status": "PASS",
        "cells": 84,
        "eligible_cells": state_counts["ELIGIBLE_FOR_ONE_B"],
        "states": dict(sorted(state_counts.items())),
        "package_gates": dict(sorted(package_gate_counts_total.items())),
        "selected_packages": len(selected_packages),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
