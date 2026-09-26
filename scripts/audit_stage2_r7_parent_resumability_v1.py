from __future__ import annotations

import copy
import hashlib
import io
import json
import re
import tarfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NATURAL = ROOT / "stage2/natural_v7"
FIXTURE = ROOT / "stage2/fixtures/project"
PACKAGES = ROOT / "stage2/r7_monitor_v1/monitor_derived_repair_packages.jsonl"
EVENTS = ROOT / "stage2/r7_monitor_v1/normalized_structural_events.jsonl"
SOURCE = ROOT / "configs/stage2_r7_21_path_source_freeze_v1.json"
CONTRACT = ROOT / "configs/stage2_r7_parent_resumability_contract_v1.json"
OUT = ROOT / "stage2/r7_parent_v1"


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def stable_hash(value: Any) -> str:
    if isinstance(value, bytes):
        raw = value
    else:
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(raw)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]):
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def prefix_index(ref: str) -> int:
    m = re.search(r":struct:(\d+)$", ref)
    if not m:
        raise ValueError("invalid structural ref: " + ref)
    return int(m.group(1))


class FrozenArchive:
    def __init__(self, cell: str, expected_sha256: str):
        self.cell = cell
        raw = (NATURAL / cell / "first_attempt.tar.gz").read_bytes()
        if sha256_bytes(raw) != expected_sha256:
            raise ValueError(cell + ": source archive hash mismatch")
        self.tf = tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz")
        self.members = {m.name.removeprefix("./"): m for m in self.tf.getmembers() if m.isfile()}

    def read(self, name: str) -> bytes:
        f = self.tf.extractfile(self.members[name])
        if f is None:
            raise KeyError(name)
        return f.read()

    def find_suffix(self, suffix: str) -> str | None:
        rows = [name for name in self.members if name.endswith(suffix)]
        if len(rows) > 1:
            raise ValueError(self.cell + ": ambiguous archive suffix " + suffix)
        return rows[0] if rows else None

    def names(self, prefix: str) -> list[str]:
        return sorted(name for name in self.members if name.startswith(prefix))


def parse_json(raw: bytes):
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None


def fixture_bytes() -> dict[str, bytes]:
    out = {}
    for path in sorted(FIXTURE.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        rel = str(path.relative_to(FIXTURE))
        if "__pycache__" in rel or rel.endswith(".pyc") or rel.startswith("results/"):
            continue
        out[rel] = path.read_bytes()
    return out


def state_digest(files: dict[str, bytes]) -> str:
    rows = [(path, sha256_bytes(raw)) for path, raw in sorted(files.items())]
    return stable_hash(rows)


def archive_final_checkout(ar: FrozenArchive) -> dict[str, bytes]:
    prefix = f"{ar.cell}/checkout/"
    out = {}
    for name in ar.names(prefix):
        rel = name[len(prefix):]
        if "__pycache__" in rel or rel.endswith(".pyc") or rel.startswith("results/"):
            continue
        out[rel] = ar.read(name)
    return out


def autogen_structural_actions(ar: FrozenArchive) -> list[dict[str, Any]]:
    name = ar.find_suffix("/observer/native/events.jsonl")
    if not name:
        return []
    metas = [json.loads(line) for line in ar.read(name).splitlines() if line.strip()]
    raw_root = name.removesuffix("events.jsonl")
    staged: list[tuple[int, int, dict[str, Any]]] = []
    sub = 0
    for meta in metas:
        payload = parse_json(ar.read(raw_root + meta["raw_path"]))
        if not isinstance(payload, dict):
            continue
        seq = int(meta["sequence"])
        etype = str(payload.get("type") or "")
        actor = payload.get("source")
        content = payload.get("content")
        if etype == "ToolCallRequestEvent" and isinstance(content, list):
            for call in content:
                if not isinstance(call, dict):
                    continue
                tool = str(call.get("name") or "tool")
                args = call.get("arguments")
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except Exception:
                        args = {"raw": args}
                if not isinstance(args, dict):
                    args = {}
                staged.append((seq, sub, {
                    "kind": "TOOL_CALL",
                    "actor": actor,
                    "tool": tool,
                    "args": args,
                    "native_sequence": seq,
                }))
                sub += 1
        elif etype in {"HandoffMessage", "TextMessage"}:
            staged.append((seq, sub, {
                "kind": etype,
                "actor": actor,
                "native_sequence": seq,
            }))
            sub += 1
    staged.sort(key=lambda x: (x[0], x[1]))
    out = []
    for i, (_, _, row) in enumerate(staged, 1):
        out.append({"struct_index": i, **row})
    return out


def replay_x1_checkout(ar: FrozenArchive, cutoff: int) -> dict[str, Any]:
    actions = autogen_structural_actions(ar)
    initial = fixture_bytes()

    def apply_until(limit: int) -> tuple[dict[str, bytes], list[str], list[str]]:
        files = copy.deepcopy(initial)
        writes = []
        errors = []
        for row in actions:
            if row["struct_index"] > limit:
                break
            if row["kind"] != "TOOL_CALL" or row["tool"] != "write_file":
                continue
            args = row["args"]
            path = args.get("path")
            content = args.get("content")
            if not isinstance(path, str) or not path or Path(path).is_absolute() or ".." in Path(path).parts:
                errors.append(f"struct:{row['struct_index']:04d}:invalid_path")
                continue
            if not isinstance(content, str):
                errors.append(f"struct:{row['struct_index']:04d}:missing_content")
                continue
            files[path] = content.encode("utf-8")
            writes.append(f"struct:{row['struct_index']:04d}:file:{path}")
        return files, writes, errors

    prefix_files, prefix_writes, prefix_errors = apply_until(cutoff)
    full_files, full_writes, full_errors = apply_until(10**9)
    observed_final = archive_final_checkout(ar)
    replay_final_hash = state_digest(full_files)
    observed_final_hash = state_digest(observed_final)
    all_paths = sorted(set(full_files) | set(observed_final))
    mismatches = [
        path for path in all_paths
        if full_files.get(path) != observed_final.get(path)
    ]
    return {
        "application_state_status": "VERIFIED_FROM_FROZEN_NATIVE_TOOL_CALLS" if not prefix_errors and not full_errors and not mismatches else "PARTIAL_OR_MISMATCHED",
        "prefix_checkout_state_hash": state_digest(prefix_files),
        "prefix_file_count": len(prefix_files),
        "prefix_write_refs": prefix_writes,
        "full_replay_write_count": len(full_writes),
        "full_replay_final_state_hash": replay_final_hash,
        "frozen_archive_final_state_hash": observed_final_hash,
        "full_replay_matches_frozen_final_checkout": not mismatches and not full_errors,
        "mismatched_final_paths": mismatches,
        "replay_errors": prefix_errors + full_errors,
    }


def native_parent_audit(package: dict[str, Any], source_row: dict[str, Any]) -> dict[str, Any]:
    cell = package["source_cell"]
    x = int(cell[1])
    cutoff = prefix_index(package["prefix_cutoff_ref"])
    ar = FrozenArchive(cell, source_row["tar_sha256"])
    evidence = {
        "prefix_status": "BOUND",
        "application_state_status": "NOT_PREFIX_BOUND",
        "model_visible_context_status": "NOT_FULLY_BOUND",
        "native_runtime_state_status": "NOT_SERIALIZED_AT_PREFIX",
        "remaining_horizon_status": "PARTIALLY_BOUND",
        "public_native_restore_path_status": "NOT_PROVEN_FROM_FROZEN_EVIDENCE",
    }
    detail: dict[str, Any] = {}

    if x == 1:
        detail["x1_checkout_reconstruction"] = replay_x1_checkout(ar, cutoff)
        evidence["application_state_status"] = detail["x1_checkout_reconstruction"]["application_state_status"]
        evidence["model_visible_context_status"] = "NATIVE_EVENT_HISTORY_PRESENT_BUT_TEAM_STATE_NOT_SERIALIZED"
        evidence["remaining_horizon_status"] = "BOUND_BY_FROZEN_MAX_TURNS_AND_PREFIX_ORDER"
        evidence["native_runtime_state_status"] = "AUTOGEN_TEAM_STATE_NOT_SERIALIZED_AT_PREFIX"
    elif x == 2:
        msg = ar.find_suffix("/observer/metagpt_native/events.jsonl")
        detail["metagpt_message_copy_stream_present"] = bool(msg)
        evidence["model_visible_context_status"] = "NATIVE_MESSAGE_COPIES_PRESENT_BUT_ACTION_AND_ROLE_STATE_INCOMPLETE"
        evidence["native_runtime_state_status"] = "METAGPT_ENVIRONMENT_ROLE_QUEUE_STATE_NOT_SERIALIZED_AT_PREFIX"
        evidence["remaining_horizon_status"] = "BOUND_BY_FROZEN_TURN_HISTORY_ONLY"
    elif x == 3:
        wire = ar.names(f"{cell}/observer/a2a_native/wire/")
        detail["a2a_wire_file_count"] = len(wire)
        detail["a2a_post_requests_present"] = any(name.endswith("-post-request.bin") for name in wire)
        evidence["model_visible_context_status"] = "A2A_CALL_HISTORY_BOUND_BUT_ROLE_OBSERVATIONS_PRIVATE"
        evidence["native_runtime_state_status"] = "A2A_ROLE_SESSION_OBSERVATIONS_NOT_SERIALIZED_AS_RESTORABLE_STATE"
        evidence["remaining_horizon_status"] = "BOUND_BY_A2A_REMAINING_TURNS_FIELDS"
    else:
        raise ValueError("unexpected parent-blocked system: " + cell)

    lower = {
        "L0_PREFIX_BOUND": True,
        "L1_APPLICATION_STATE_BOUND": evidence["application_state_status"] == "VERIFIED_FROM_FROZEN_NATIVE_TOOL_CALLS",
        "L2_MODEL_VISIBLE_CONTEXT_BOUND": False,
        "L3_NATIVE_RUNTIME_STATE_BOUND": False,
        "L4_NATIVE_RESUME_VERIFIED": False,
    }
    missing = []
    if not lower["L1_APPLICATION_STATE_BOUND"]:
        missing.append("APPLICATION_STATE_AT_PREFIX")
    if not lower["L2_MODEL_VISIBLE_CONTEXT_BOUND"]:
        missing.append("EXACT_NEXT_STEP_MODEL_VISIBLE_CONTEXT")
    if not lower["L3_NATIVE_RUNTIME_STATE_BOUND"]:
        missing.append("FRAMEWORK_NATIVE_SCHEDULER_QUEUE_SESSION_STATE")
    missing.append("PUBLIC_NATIVE_RESTORE_SNAPSHOT_OR_EQUIVALENT_PROOF")

    row = {
        "schema": "RB-STAGE2-R7-PARENT-RESUMABILITY-AUDIT-v1",
        "package_id": package["package_id"],
        "source_cell": cell,
        "prefix_cutoff_ref": package["prefix_cutoff_ref"],
        "source_archive_sha256": source_row["tar_sha256"],
        "verification_levels": lower,
        "evidence_status": evidence,
        "detail": detail,
        "missing_required_components": sorted(set(missing)),
        "provider_calls": 0,
        "evaluator_calls": 0,
        "stochastic_prefix_replay": False,
        "private_runtime_state_mutation": False,
        "semantic_audit_used": False,
        "result": "PARENT_RECONSTRUCTION_BLOCKED",
    }
    row["audit_hash"] = stable_hash({k: v for k, v in row.items() if k != "audit_hash"})
    return row


def foreign_binding_audit(package: dict[str, Any], events_by_cell: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    cell = package["source_cell"]
    cutoff = prefix_index(package["prefix_cutoff_ref"])
    prefix_rows = [row for row in events_by_cell[cell] if int(row["index"]) <= cutoff]

    immutable_refs = []
    legal_refs = []
    legal_events = []
    for row in prefix_rows:
        for ref in row.get("object_refs") or []:
            if ref.startswith(("rag-hit:", "memory-recall:", "memory-state:", "compression-channel:", "compression-input:", "compression-output:")):
                immutable_refs.append(ref)
            if ref.startswith(("file:", "message:")):
                legal_refs.append(ref)
                legal_events.append(row["ref"])

    # A root user request is not a downstream repair surface. Final-state events are
    # excluded by the prefix cutoff and are not allowed to back-fill the package.
    machine_bound = bool(immutable_refs and legal_refs)
    result = "DOWNSTREAM_LEGAL_SURFACE_BOUND" if machine_bound else "LINEAGE_GAP_BLOCKED"
    row = {
        "schema": "RB-STAGE2-R7-FOREIGN-CARRIER-DOWNSTREAM-BINDING-AUDIT-v1",
        "package_id": package["package_id"],
        "source_cell": cell,
        "prefix_cutoff_ref": package["prefix_cutoff_ref"],
        "foreign_carrier_refs": sorted(set(immutable_refs)),
        "legal_downstream_object_refs_at_or_before_prefix": sorted(set(legal_refs)),
        "legal_downstream_event_refs_at_or_before_prefix": sorted(set(legal_events)),
        "foreign_state_mutation_allowed": False,
        "semantic_inference_used": False,
        "future_suffix_used": False,
        "provider_calls": 0,
        "evaluator_calls": 0,
        "machine_bound_legal_repair_surface": machine_bound,
        "result": result,
        "boundary": (
            "A foreign carrier is never itself a repair surface. Binding requires a machine-observed "
            "application/message object at or before the frozen prefix; later final state is not used "
            "to expand the frozen package."
        ),
    }
    row["audit_hash"] = stable_hash({k: v for k, v in row.items() if k != "audit_hash"})
    return row


def main():
    contract = load_json(CONTRACT)
    if contract["status"] != "FROZEN_BEFORE_RESUMABILITY_AUDIT":
        raise ValueError("resumability contract not frozen")
    if contract["authorization"]["provider_calls"] or contract["authorization"]["evaluator_calls"]:
        raise ValueError("offline authorization changed")

    packages = load_jsonl(PACKAGES)
    events = load_jsonl(EVENTS)
    source = load_json(SOURCE)
    source_by_cell = {row["cell"]: row for row in source["cells"]}
    events_by_cell: dict[str, list[dict[str, Any]]] = {}
    for row in events:
        events_by_cell.setdefault(row["cell"], []).append(row)

    parent_packages = [p for p in packages if p["repair_gate_status"] == "PARENT_RECONSTRUCTION_BLOCKED"]
    foreign_packages = [p for p in packages if p["repair_gate_status"] == "LINEAGE_GAP_BLOCKED"]

    parent_rows = [native_parent_audit(p, source_by_cell[p["source_cell"]]) for p in parent_packages]
    foreign_rows = [foreign_binding_audit(p, events_by_cell) for p in foreign_packages]

    OUT.mkdir(parents=True, exist_ok=True)
    write_jsonl(OUT / "parent_resumability_audit.jsonl", parent_rows)
    write_jsonl(OUT / "foreign_carrier_binding_audit.jsonl", foreign_rows)

    x1_verified_app = sum(
        1 for row in parent_rows
        if row["verification_levels"]["L1_APPLICATION_STATE_BOUND"]
    )
    native_verified = sum(
        1 for row in parent_rows
        if row["verification_levels"]["L4_NATIVE_RESUME_VERIFIED"]
    )
    foreign_bound = sum(1 for row in foreign_rows if row["machine_bound_legal_repair_surface"])

    summary = {
        "schema": "RB-STAGE2-R7-PARENT-RESUMABILITY-SUMMARY-v1",
        "date": "2026-09-26",
        "status": "OFFLINE_PARENT_RESUMABILITY_AND_FOREIGN_BINDING_AUDIT_COMPLETE",
        "source_packages": len(packages),
        "parent_reconstruction_packages_audited": len(parent_rows),
        "foreign_carrier_packages_audited": len(foreign_rows),
        "application_state_verified_package_count": x1_verified_app,
        "native_resume_verified_package_count": native_verified,
        "foreign_legal_surface_bound_package_count": foreign_bound,
        "parent_reconstruction_blocked_count": sum(row["result"] == "PARENT_RECONSTRUCTION_BLOCKED" for row in parent_rows),
        "lineage_gap_blocked_count": sum(row["result"] == "LINEAGE_GAP_BLOCKED" for row in foreign_rows),
        "provider_calls": 0,
        "evaluator_calls": 0,
        "natural_reruns": 0,
        "stochastic_prefix_replays": 0,
        "semantic_audit_used": False,
        "active_repair_authorized": False,
        "interpretation_boundary": (
            "This audit tests machine reconstructability and legal downstream binding only. "
            "It does not evaluate CPR meaning or repair efficacy. Partial application-state reconstruction "
            "does not satisfy the same-parent active-repair gate."
        ),
    }
    summary["summary_hash"] = stable_hash({k: v for k, v in summary.items() if k != "summary_hash"})
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = [
        "# Stage-II R7 Native-Parent Resumability / Foreign-Carrier Binding Audit v1",
        "",
        "Date: 2026-09-26  ",
        "Status: **OFFLINE AUDIT COMPLETE / ACTIVE REPAIR STILL CLOSED**",
        "",
        "## Boundary",
        "",
        "- provider calls: **0**;",
        "- evaluator calls: **0**;",
        "- natural reruns: **0**;",
        "- stochastic prefix replays: **0**;",
        "- semantic audit used: **NO**;",
        "- private native runtime state mutated: **NO**.",
        "",
        "## Parent resumability",
        "",
        f"- parent-blocked packages audited: **{len(parent_rows)}**;",
        f"- application-state reconstructions verified from frozen native tool calls: **{x1_verified_app}**;",
        f"- full native same-parent resumability verified: **{native_verified}**;",
        f"- packages remaining PARENT_RECONSTRUCTION_BLOCKED: **{sum(row['result'] == 'PARENT_RECONSTRUCTION_BLOCKED' for row in parent_rows)}**.",
        "",
        "The X1 AutoGen archives preserve enough native tool-call arguments to deterministically replay checkout writes and verify the reconstructed full checkout against the frozen final checkout. This establishes application-state reconstructability for those packages, not a resumable AutoGen team/session parent. No serialized native team state exists at the selected prefixes, so the L4 repair gate remains closed.",
        "",
        "X2 preserves native MetaGPT message-copy surfaces but not a complete prefix-bound action/role/environment restore state. X3 preserves A2A wire calls, but per-role tool observations/session state are not serialized as a public restorable parent. Both therefore remain fail-closed.",
        "",
        "## Immutable foreign-carrier binding",
        "",
        f"- foreign-carrier packages audited: **{len(foreign_rows)}**;",
        f"- machine-bound legal downstream repair surfaces at/before frozen prefix: **{foreign_bound}**;",
        f"- packages remaining LINEAGE_GAP_BLOCKED: **{sum(row['result'] == 'LINEAGE_GAP_BLOCKED' for row in foreign_rows)}**.",
        "",
        "RAG, MemoryBank and LongLLMLingua remain immutable. Their monitor surfaces expose retrieval, recall or compression carriers, but the current frozen structural prefix does not bind those carriers to a legal downstream application/message object strongly enough for repair without semantic inference or future leakage.",
        "",
        "## Consequence",
        "",
        "The same-parent R7 geometry cannot yet start an active repair continuation from the existing Stage-II natural archives without relaxing a frozen boundary. The correct result is therefore to preserve the blocked gates rather than rerun a stochastic prefix, synthesize missing state, modify a framework, or mutate an external information store.",
    ]
    (OUT / "resumability_report_v1.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    print("STAGE2_R7_PARENT_RESUMABILITY=PASS")
    print("PARENT_PACKAGES=" + str(len(parent_rows)))
    print("APPLICATION_STATE_VERIFIED=" + str(x1_verified_app))
    print("NATIVE_RESUME_VERIFIED=" + str(native_verified))
    print("FOREIGN_PACKAGES=" + str(len(foreign_rows)))
    print("FOREIGN_LEGAL_SURFACE_BOUND=" + str(foreign_bound))
    print("PROVIDER_CALLS=0")


if __name__ == "__main__":
    main()
