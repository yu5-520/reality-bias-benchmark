from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "stage2/r7_monitor_v1"
CANDIDATES = BASE / "structural_candidates.jsonl"
PACKAGES = BASE / "monitor_derived_repair_packages.jsonl"
PREFLIGHTS = BASE / "parent_reconstruction_preflight.jsonl"
SUMMARY = BASE / "summary.json"
CANDIDATE_SUMMARY = BASE / "candidate_scan_summary.json"
RULES = ROOT / "configs/stage2_r7_package_assembly_rules_v1.json"
BOUNDARY = ROOT / "configs/stage2_r7_boundary_contract_v1.json"
SOURCE = ROOT / "configs/stage2_r7_21_path_source_freeze_v1.json"

FOREIGN_PREFIXES = ("rag-hit:", "memory-recall:", "compression-channel:", "compression-input:", "compression-output:")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def dump_jsonl(path: Path, rows):
    path.write_text("".join(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in rows), encoding="utf-8")


def stable_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def prefix_index(ref: str) -> int:
    m = re.search(r":struct:(\d+)$", ref)
    if not m:
        raise ValueError("unexpected prefix ref: " + ref)
    return int(m.group(1))


def family(obj: str) -> str:
    return obj.split(":", 1)[0]


def is_foreign(obj: str) -> bool:
    return obj.startswith(FOREIGN_PREFIXES)


def candidate_allowed_surface(obj: str):
    if obj.startswith("file:"):
        p = obj.removeprefix("file:")
        return [f"NATIVE_APPLICATION_FILE_REVISION:{p}"], ["write_file"], "APPLICATION_FILE"
    if obj.startswith("message:"):
        return ["NATIVE_MESSAGE_OR_TASK_SUPERSESSION"], ["message_or_task_submission"], "NATIVE_MESSAGE_OR_TASK"
    if is_foreign(obj):
        return ["DOWNSTREAM_PROCESS_REVISION_ONLY_NOT_FOREIGN_STATE"], ["downstream_native_process_surface"], "IMMUTABLE_FOREIGN_CARRIER"
    return ["NO_DIRECT_REPAIR_SURFACE"], [], "UNBOUND"


def should_merge(ep: dict, cand: dict, cfg: dict) -> bool:
    obj = cand["object_ref"]
    fam = family(obj)
    if is_foreign(obj):
        return ep["foreign"] and fam in cfg["immutable_carrier_episode"]["families"]

    if ep["foreign"]:
        return False

    if obj in ep["objects"]:
        return True

    gap = prefix_index(cand["prefix_cutoff_ref"]) - ep["last_index"]
    if gap < 0:
        return False

    if cand["rule_id"] == "TERMINAL_OPEN_WITH_REUSE":
        return bool(set(cand["support_refs"]) & ep["event_refs"])

    if gap > int(cfg["application_episode"]["maximum_prefix_gap_events"]):
        return False

    if not cfg["application_episode"]["require_actor_overlap_or_same_object"]:
        return True

    return bool(set(cand.get("actors") or []) & ep["actors"])


def new_episode(cand: dict) -> dict:
    return {
        "cell": cand["cell"],
        "candidates": [cand],
        "objects": {cand["object_ref"]},
        "actors": set(cand.get("actors") or []),
        "event_refs": set(cand.get("support_refs") or []) | set(cand.get("pressure_refs") or []),
        "first_index": prefix_index(cand["prefix_cutoff_ref"]),
        "last_index": prefix_index(cand["prefix_cutoff_ref"]),
        "foreign": is_foreign(cand["object_ref"]),
    }


def add_episode(ep: dict, cand: dict):
    ep["candidates"].append(cand)
    ep["objects"].add(cand["object_ref"])
    ep["actors"].update(cand.get("actors") or [])
    ep["event_refs"].update(cand.get("support_refs") or [])
    ep["event_refs"].update(cand.get("pressure_refs") or [])
    ep["last_index"] = max(ep["last_index"], prefix_index(cand["prefix_cutoff_ref"]))


def assemble_episodes(rows: list[dict], cfg: dict) -> list[dict]:
    episodes = []
    by_cell = {}
    for row in sorted(rows, key=lambda x: (x["cell"], prefix_index(x["prefix_cutoff_ref"]), x["candidate_id"])):
        by_cell.setdefault(row["cell"], []).append(row)

    for cell, candidates in sorted(by_cell.items()):
        eps = []
        for cand in candidates:
            if is_foreign(cand["object_ref"]) and cfg["immutable_carrier_episode"]["merge_same_carrier_family_within_cell"]:
                # One immutable-carrier episode per cell. The repair system cannot edit
                # the carrier; downstream binding is evaluated as one structural scope.
                existing = next((x for x in eps if x["foreign"]), None)
                if existing is not None:
                    add_episode(existing, cand)
                    continue
            joined = False
            for ep in reversed(eps):
                if should_merge(ep, cand, cfg):
                    add_episode(ep, cand)
                    joined = True
                    break
            if not joined:
                eps.append(new_episode(cand))
        episodes.extend(eps)
    return episodes


def episode_package(ep: dict, idx: int, boundary: dict, source_row: dict) -> tuple[dict, dict]:
    cands = ep["candidates"]
    cell = ep["cell"]
    objects = sorted(ep["objects"])
    pressures = []
    supports = []
    ancestors = []
    descendants = []
    evidence = []
    allowed = []
    caps = []
    kinds = set()

    for cand in cands:
        pressures.extend(cand.get("pressure_refs") or [])
        supports.extend(cand.get("support_refs") or [])
        ancestors.extend(cand.get("ancestor_refs") or [])
        descendants.extend(cand.get("observed_descendant_refs") or [])
        evidence.append("candidate:" + cand["candidate_id"] + ":" + cand["candidate_hash"])
        surface, req, kind = candidate_allowed_surface(cand["object_ref"])
        allowed.extend(surface)
        caps.extend(req)
        kinds.add(kind)

    pressures = list(dict.fromkeys(pressures))
    supports = list(dict.fromkeys(supports)) or list(dict.fromkeys(ancestors))
    ancestors = list(dict.fromkeys(ancestors))
    descendants = list(dict.fromkeys(descendants))
    evidence = list(dict.fromkeys(evidence + supports + pressures))
    allowed = list(dict.fromkeys(allowed))
    caps = list(dict.fromkeys(caps))
    closure = list(dict.fromkeys(ancestors + supports + pressures + descendants))

    if "IMMUTABLE_FOREIGN_CARRIER" in kinds:
        gate = "LINEAGE_GAP_BLOCKED"
        parent_status = "BLOCKED"
        reason = (
            "The carrier is observable but immutable by contract, and the raw structural "
            "surface does not fully bind downstream adoption to a legal application repair anchor."
        )
    elif kinds <= {"UNBOUND"}:
        gate = "NO_REPAIR_REQUIRED"
        parent_status = "PENDING"
        reason = "The structural episode does not expose a direct application/message repair surface."
    else:
        gate = "PARENT_RECONSTRUCTION_BLOCKED"
        parent_status = "BLOCKED"
        reason = (
            "The episode exposes native application/message repair surfaces, but the frozen natural "
            "archive has no framework-native resumable runtime checkpoint at the detected prefix."
        )

    first_pressure = min(pressures, key=prefix_index)
    episode_material = {
        "cell": cell,
        "candidate_hashes": sorted(x["candidate_hash"] for x in cands),
        "objects": objects,
        "first_index": ep["first_index"],
        "last_index": ep["last_index"],
    }
    package_id = f"{cell}:monitor-episode:{idx:02d}:package:v1"
    package = {
        "schema": "RB-STAGE2-R7-MONITOR-DERIVED-REPAIR-PACKAGE-v1",
        "package_id": package_id,
        "source_cell": cell,
        "prefix_cutoff_ref": first_pressure,
        "monitor_evidence_refs": evidence,
        "pressure_refs": pressures,
        "support_refs": supports,
        "ancestor_refs": ancestors,
        "descendant_refs": descendants,
        "affected_closure_refs": closure,
        "preserve_refs": [
            f"{cell}:source-archive-sha256:{source_row['tar_sha256']}",
            f"{cell}:preserve:framework-protocol-foreign-state",
        ],
        "repair_anchor_ref": first_pressure,
        "content_address": "rbca:stage2-r7-package:" + stable_hash(episode_material),
        "detection_surface": "MONITOR_STRUCTURAL_EPISODE",
        "allowed_repair_surface": allowed,
        "native_capability_requirements": caps,
        "forbidden_mutations": boundary["repair_surface"]["forbidden"],
        "parent_reconstruction": {
            "status": parent_status,
            "parent_hash_refs": [
                "source-archive-sha256:" + source_row["tar_sha256"],
                "episode-hash:" + stable_hash(episode_material),
            ],
            "future_evidence_used": False,
        },
        "repair_gate_status": gate,
        "post_repair_watch": {
            "old_support_reentry": False,
            "new_support_emergence": False,
            "authority_regeneration": False,
            "scope_reopening": False,
            "carrier_migration": False,
        },
        "package_hash": "",
    }
    package["package_hash"] = stable_hash({k: v for k, v in package.items() if k != "package_hash"})

    preflight = {
        "schema": "RB-STAGE2-R7-PARENT-RECONSTRUCTION-PREFLIGHT-v1",
        "package_id": package_id,
        "source_cell": cell,
        "prefix_cutoff_ref": first_pressure,
        "status": parent_status,
        "repair_gate_status": gate,
        "reason": reason,
        "future_evidence_used": False,
        "source_archive_sha256": source_row["tar_sha256"],
        "candidate_count": len(cands),
        "object_count": len(objects),
        "candidate_ids": [x["candidate_id"] for x in cands],
    }
    preflight["preflight_hash"] = stable_hash({k: v for k, v in preflight.items() if k != "preflight_hash"})
    return package, preflight


def main():
    cfg = load(RULES)
    boundary = load(BOUNDARY)
    source = load(SOURCE)
    if cfg["status"] != "FROZEN_BEFORE_CANONICAL_PACKAGE_ASSEMBLY":
        raise ValueError("package assembly rules not frozen")
    if cfg["semantic_audit_used"] is not False or cfg["case_specific_rules"] is not False:
        raise ValueError("package assembly information boundary changed")

    candidates = load_jsonl(CANDIDATES)
    episodes = assemble_episodes(candidates, cfg)
    source_by_cell = {x["cell"]: x for x in source["cells"]}

    packages = []
    preflights = []
    per_cell_index = Counter()
    for ep in episodes:
        per_cell_index[ep["cell"]] += 1
        p, pf = episode_package(ep, per_cell_index[ep["cell"]], boundary, source_by_cell[ep["cell"]])
        packages.append(p)
        preflights.append(pf)

    dump_jsonl(PACKAGES, packages)
    dump_jsonl(PREFLIGHTS, preflights)

    old = load(SUMMARY)
    if not CANDIDATE_SUMMARY.exists():
        CANDIDATE_SUMMARY.write_text(json.dumps(old, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    gate_counts = Counter(x["repair_gate_status"] for x in packages)
    package_cell_counts = Counter(x["source_cell"] for x in packages)
    summary = dict(old)
    summary["status"] = "OFFLINE_PREFIX_REPLAY_AND_PACKAGE_ASSEMBLY_COMPLETE"
    summary["candidate_scan_summary_hash"] = old["summary_hash"]
    summary["monitor_derived_repair_package_count"] = len(packages)
    summary["repair_package_count"] = len(packages)
    summary["repair_gate_counts"] = dict(sorted(gate_counts.items()))
    summary["complete_for_structured_repair_count"] = gate_counts.get("COMPLETE_FOR_STRUCTURED_REPAIR", 0)
    summary["parent_reconstruction_blocked_count"] = gate_counts.get("PARENT_RECONSTRUCTION_BLOCKED", 0)
    summary["lineage_gap_blocked_count"] = gate_counts.get("LINEAGE_GAP_BLOCKED", 0)
    summary["no_repair_required_count"] = gate_counts.get("NO_REPAIR_REQUIRED", 0)
    summary["package_cells"] = len(package_cell_counts)
    summary["package_cell_counts"] = dict(sorted(package_cell_counts.items()))
    package_gates_by_cell = {}
    for package in packages:
        package_gates_by_cell.setdefault(package["source_cell"], Counter())
        package_gates_by_cell[package["source_cell"]][package["repair_gate_status"]] += 1
    rewritten_cells = []
    for row in summary.get("cell_summary", []):
        item = dict(row)
        item["candidate_gate_counts_preassembly"] = item.pop("gate_counts", {})
        item["candidate_record_count_preassembly"] = item.pop("package_count", item.get("candidate_count", 0))
        item["repair_package_count"] = package_cell_counts.get(item["cell"], 0)
        item["repair_package_gate_counts"] = dict(sorted(package_gates_by_cell.get(item["cell"], {}).items()))
        rewritten_cells.append(item)
    summary["cell_summary"] = rewritten_cells
    summary["package_assembly"] = {
        "schema": cfg["schema"],
        "semantic_audit_used": False,
        "case_specific_rules": False,
        "candidate_signals_retained": len(candidates),
        "structural_episodes": len(episodes),
        "principle": cfg["principle"],
    }
    summary["active_repair_authorized"] = False
    summary.pop("summary_hash", None)
    summary["summary_hash"] = stable_hash(summary)
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md = [
        "# Stage-II R7 Monitor-Derived Package Assembly v1",
        "",
        "Date: 2026-09-26  ",
        "Status: **STRUCTURAL EPISODES FROZEN / ACTIVE REPAIR NOT AUTHORIZED**",
        "",
        f"- raw structural candidates retained: **{len(candidates)}**;",
        f"- structurally merged repair episodes/packages: **{len(packages)}**;",
        f"- cells represented by packages: **{len(package_cell_counts)}/21**;",
        f"- repair gate counts: `{json.dumps(dict(sorted(gate_counts.items())), sort_keys=True)}`;",
        "- semantic audit used in assembly: **NO**;",
        "- case-specific package rule: **NO**.",
        "",
        "Candidate rows are not discarded. Package assembly only merges structurally connected signals so R7 operates on pressure/support episodes rather than treating each repeated file, message or carrier observation as an independent repair experiment.",
        "",
        "## Package accounting",
        "",
        "| Package | Cell | Pressure refs | Support refs | Allowed surfaces | Gate |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for p in packages:
        md.append(
            f"| {p['package_id']} | {p['source_cell']} | {len(p['pressure_refs'])} | "
            f"{len(p['support_refs'])} | {len(p['allowed_repair_surface'])} | {p['repair_gate_status']} |"
        )
    md += [
        "",
        "The gate remains fail-closed. No package may enter active repair until its parent reconstruction is machine-verified and any lineage gap between an immutable foreign carrier and a legal downstream repair surface is resolved without modifying the foreign system.",
    ]
    (BASE / "package_assembly_report_v1.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    final_report = [
        "# Stage-II R7 Offline Structural Monitor / Prefix Replay Result v1",
        "",
        "Date: 2026-09-26  ",
        "Status: **OFFLINE PREFIX REPLAY + PACKAGE ASSEMBLY COMPLETE / ACTIVE REPAIR NOT AUTHORIZED**",
        "",
        "## Frozen execution boundary",
        "",
        "- 21/21 frozen first-attempt natural archives scanned.",
        "- 0 natural reruns.",
        "- 0 subject/provider calls.",
        "- 0 evaluator calls.",
        "- semantic audit used as monitor input: **NO**.",
        "- CPR labels used as monitor input: **NO**.",
        "- future suffix used to choose a prefix candidate: **NO**.",
        "",
        "## Structural monitor result",
        "",
        f"- normalized structural events: **{summary['normalized_event_count']}**;",
        f"- raw structural candidate signals retained: **{len(candidates)}** across **{summary['cells_with_candidates']}/21** cells;",
        f"- structurally assembled repair episodes/packages: **{len(packages)}** across **{len(package_cell_counts)}/21** cells;",
        f"- raw candidate rule counts: `{json.dumps(summary['rule_counts'], sort_keys=True)}`;",
        f"- final repair-gate counts: `{json.dumps(dict(sorted(gate_counts.items())), sort_keys=True)}`.",
        "",
        "Raw candidate signals remain individually auditable. They are not counted as separate repair experiments. Generic structural assembly merges connected pressure/support signals into lineage-bounded package episodes without semantic labels.",
        "",
        "## Parent reconstruction / lineage gate",
        "",
        f"- PARENT_RECONSTRUCTION_BLOCKED: **{gate_counts.get('PARENT_RECONSTRUCTION_BLOCKED', 0)}** packages;",
        f"- LINEAGE_GAP_BLOCKED: **{gate_counts.get('LINEAGE_GAP_BLOCKED', 0)}** packages;",
        f"- NO_REPAIR_REQUIRED: **{gate_counts.get('NO_REPAIR_REQUIRED', 0)}** packages;",
        f"- COMPLETE_FOR_STRUCTURED_REPAIR: **{gate_counts.get('COMPLETE_FOR_STRUCTURED_REPAIR', 0)}** packages.",
        "",
        "The current frozen archives preserve rich process evidence but do not freeze framework-native resumable runtime checkpoints at the monitor-selected prefixes. Immutable RAG / MemoryBank / compression carriers are also deliberately not treated as writable repair surfaces; where a legal downstream adoption anchor is not fully bound by raw structural evidence, the package remains LINEAGE_GAP_BLOCKED.",
        "",
        "The monitor therefore fails closed. This is an engineering readiness result, not an R7 repair-efficacy result.",
        "",
        "## Cell accounting",
        "",
        "| Cell | Events | Raw candidates | Packages | Package gates | First prefix |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in summary["cell_summary"]:
        final_report.append(
            f"| {row['cell']} | {row['normalized_event_count']} | {row['candidate_count']} | "
            f"{row['repair_package_count']} | `{json.dumps(row['repair_package_gate_counts'], sort_keys=True)}` | "
            f"{row['first_candidate_prefix'] or '-'} |"
        )
    final_report += [
        "",
        "## Next engineering operation",
        "",
        "Do **not** start an active repair continuation from an unverified parent.",
        "",
        "Next: build and audit framework-specific native-parent resumability/reconstruction proofs for monitor-selected prefixes, without modifying upstream framework/protocol semantics and without rerunning the stochastic natural prefix. For immutable foreign information carriers, bind the observed carrier to the nearest legal downstream application/process repair surface without mutating the foreign store.",
        "",
        "Only machine-verified packages may later move to active R7 authorization. The existing complete semantic audit remains sealed from this engineering path until package freeze and later validation.",
    ]
    (BASE / "offline_prefix_replay_report_v1.md").write_text("\n".join(final_report) + "\n", encoding="utf-8")

    print("STAGE2_R7_PACKAGE_ASSEMBLY=PASS")
    print("CANDIDATES=" + str(len(candidates)))
    print("PACKAGES=" + str(len(packages)))
    print("GATES=" + json.dumps(dict(sorted(gate_counts.items())), sort_keys=True))


if __name__ == "__main__":
    main()
