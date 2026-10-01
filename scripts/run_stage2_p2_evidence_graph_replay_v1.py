#!/usr/bin/env python3
"""P2 offline Evidence Graph replay over the 84 frozen G2-G5 natural trajectories.

Graph construction is audit-blind. Frozen semantic reviews are read only after
all graph candidates for a cell are fixed, and are used as a separate
localization reference. No model, subject, evaluator, or repair call is made.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys
import time
import tracemalloc
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.run_stage2_r7_structural_monitor_v1 as legacy
from stage2.monitor_enhancement.evidence_graph import EvidenceGraph
from stage2.monitor_enhancement.inspection import inspect_graph
from stage2.monitor_enhancement.observation_adapter import adapt_structural_event
from stage2.monitor_enhancement.route_export import export_route_map

CONTRACT = ROOT / "configs/stage2_p2_evidence_graph_replay_v1.json"
GROUPS = ("G2", "G3", "G4", "G5")
CELLS = tuple(f"X{x}-T{t}" for x in range(1, 8) for t in range(1, 4))
IMMUTABLE_PREFIXES = (
    "rag-hit:",
    "memory-recall:",
    "memory-state:",
    "compression-channel:",
    "compression-input:",
    "compression-output:",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def json_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def member_by_basename(ar: legacy.FrozenArchive, basename: str) -> str | None:
    matches = [name for name in ar.members if Path(name).name == basename]
    if not matches:
        return None
    if len(matches) != 1:
        raise RuntimeError(f"{ar.cell}: ambiguous {basename}: {matches}")
    return matches[0]


def old_candidates(ar: legacy.FrozenArchive) -> list[dict[str, Any]]:
    name = member_by_basename(ar, "monitor_candidates.json")
    if name is None:
        return []
    value = json.loads(ar.read(name))
    if not isinstance(value, list):
        raise TypeError(f"{ar.cell}: monitor_candidates.json must be list")
    return value


def corrected_observation_index(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    raw = gzip.decompress(path.read_bytes())
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    return {row["full_id"]: row for row in rows}


def add_normalized_event(graph: EvidenceGraph, full_id: str, ev: dict[str, Any]) -> None:
    relation = str(ev.get("relation") or "")
    detail = dict(ev.get("detail") or {})
    base = {
        "sequence": int(ev["index"]),
        "event_ref": f"{full_id}:{ev['ref']}",
        "actor": str(ev.get("actor") or "SYSTEM"),
        "kind": str(ev.get("kind") or "UNKNOWN"),
        "object_refs": list(ev.get("object_refs") or []),
        "written_refs": list(ev.get("object_refs") or []) if relation == "WRITE" else [],
        "downstream_legal_refs": [],
        "preserve_refs": [],
    }
    evidence_ref = f"{full_id}:normalized:{ev['event_hash']}"
    if ev.get("kind") == "CHECKOUT_STATE" and base["object_refs"]:
        ref = base["object_refs"][0]
        for label, value in (("INITIAL", detail.get("initial_sha256")), ("FINAL", detail.get("final_sha256"))):
            if not value:
                continue
            version_event = dict(base)
            version_event["event_ref"] += ":" + label.lower()
            version_event["kind"] = "CHECKOUT_STATE_" + label
            version_event["object_refs"] = [ref]
            obs = adapt_structural_event(
                version_event,
                trajectory_id=full_id,
                evidence_ref=evidence_ref + ":" + label.lower(),
                version=label,
            )
            obs["content_hash"] = str(value)
            graph.add_observation(obs)
        return

    obs = adapt_structural_event(
        base,
        trajectory_id=full_id,
        evidence_ref=evidence_ref,
        version=None,
    )
    graph.add_observation(obs)


def add_corrected_chronology(graph: EvidenceGraph, full_id: str, row: dict[str, Any] | None) -> int:
    if not row:
        return 0
    changed = set(row.get("files_changed_at_any_observed_checkpoint") or [])
    added = 0
    for tindex, transition in enumerate(row.get("application_state_transitions") or []):
        seq = transition.get("sequence")
        seq = int(seq) if isinstance(seq, int) and seq >= 0 else tindex
        manifest = str(transition.get("manifest") or f"chronology:{tindex}")
        manifest_sha = str(transition.get("manifest_sha256") or json_hash(transition))
        initial = transition.get("initial_hashes")
        if isinstance(initial, dict):
            for path in sorted(changed & set(initial)):
                value = initial.get(path)
                if value is None:
                    continue
                ev = {
                    "sequence": seq,
                    "event_ref": f"{full_id}:chron:{tindex}:initial:{path}",
                    "actor": "SYSTEM",
                    "kind": "CHECKPOINT_INITIAL_STATE",
                    "object_refs": ["file:" + path],
                    "written_refs": [],
                    "downstream_legal_refs": [],
                    "preserve_refs": [],
                }
                obs = adapt_structural_event(
                    ev,
                    trajectory_id=full_id,
                    evidence_ref=f"{full_id}:chron:{manifest}:{manifest_sha}:initial:{path}",
                    version=f"checkpoint:{seq}:initial",
                )
                obs["content_hash"] = str(value)
                graph.add_observation(obs)
                added += 1
        for path, delta in sorted((transition.get("hash_changes") or {}).items()):
            after = delta.get("after") if isinstance(delta, dict) else None
            if after is None:
                after = "DELETED"
            ev = {
                "sequence": seq,
                "event_ref": f"{full_id}:chron:{tindex}:after:{path}",
                "actor": "SYSTEM",
                "kind": "CHECKPOINT_STATE_TRANSITION",
                "object_refs": ["file:" + path],
                "written_refs": [],
                "downstream_legal_refs": [],
                "preserve_refs": [],
            }
            obs = adapt_structural_event(
                ev,
                trajectory_id=full_id,
                evidence_ref=f"{full_id}:chron:{manifest}:{manifest_sha}:after:{path}",
                version=f"checkpoint:{seq}",
            )
            obs["content_hash"] = str(after)
            graph.add_observation(obs)
            added += 1
    return added


def candidate_rows(graph: EvidenceGraph, full_id: str, contract: dict[str, Any]) -> list[dict[str, Any]]:
    snapshot = graph.snapshot()
    edges = snapshot["edges"]
    write_targets = Counter(
        edge["destination_ref"]
        for edge in edges
        if edge["relation_type"] == "EVENT_WRITES_OBJECT"
    )
    rows = []
    min_events = int(contract["candidate_rules"]["minimum_multi_event_count"])
    min_span = int(contract["candidate_rules"]["minimum_reentry_span_events"])
    for node in snapshot["nodes"]:
        if node["node_type"] != "OBSERVED_OBJECT":
            continue
        refs = list(node.get("event_refs") or [])
        seqs = [int(x) for x in node.get("sequences") or [] if isinstance(x, int)]
        actors = list(node.get("actors") or [])
        hashes = list(node.get("content_hashes") or [])
        reasons = []
        if len(refs) >= min_events:
            reasons.append("MULTI_EVENT_REUSE")
        if len(actors) >= 2:
            reasons.append("MULTI_ACTOR_EXPOSURE")
        if len(seqs) >= 2 and max(seqs) - min(seqs) >= min_span:
            reasons.append("LONG_SPAN_REENTRY")
        if len(set(hashes)) >= 2:
            reasons.append("MULTI_VERSION_STATE")
        if node["ref"].startswith(IMMUTABLE_PREFIXES) and len(refs) >= 2:
            reasons.append("IMMUTABLE_CARRIER_REUSE")
        if write_targets[node["ref"]] and len(refs) >= 2:
            reasons.append("WRITE_AND_LATER_OBSERVATION")
        if not reasons:
            continue
        row = {
            "schema": "RB-STAGE2-P2-GRAPH-INSPECTION-CANDIDATE-v1",
            "full_id": full_id,
            "object_ref": node["ref"],
            "reasons": sorted(set(reasons)),
            "event_refs": refs,
            "evidence_refs": list(node.get("evidence_refs") or []),
            "sequences": seqs,
            "actors": actors,
            "content_hashes": hashes,
            "candidate_is_defect": False,
            "semantic_status": "NOT_ADJUDICATED",
        }
        row["candidate_hash"] = json_hash(row)
        rows.append(row)
    rows.sort(key=lambda row: (-len(row["reasons"]), row["object_ref"]))
    return rows


def add_unknown_reuse_edges(graph: EvidenceGraph, candidates: list[dict[str, Any]]) -> None:
    for row in candidates:
        events = list(row.get("event_refs") or [])
        if len(events) < 2:
            continue
        evidence_refs = list(row.get("evidence_refs") or [])
        graph.add_edge({
            "source_ref": row["object_ref"],
            "destination_ref": "event:" + events[-1],
            "relation_type": "REUSE_DEPENDENCY_UNRESOLVED",
            "status": "UNKNOWN",
            "basis": "STRUCTURAL_REUSE_REQUIRES_SEMANTIC_REVIEW",
            "evidence_refs": evidence_refs,
            "semantic_scope_status": "UNRESOLVED",
            "semantic_use_status": "UNRESOLVED",
        })


def object_tokens(ref: str, minimum: int) -> set[str]:
    value = str(ref).lower()
    parts = re.split(r"[:/\\\\]+", value)
    tokens = set()
    for part in parts + [value]:
        part = part.strip()
        if len(part) < minimum:
            continue
        if re.fullmatch(r"[0-9a-f]{20,}", part):
            continue
        tokens.add(part)
        if "." in part:
            stem = part.rsplit(".", 1)[0]
            if len(stem) >= minimum:
                tokens.add(stem)
    return tokens


def audit_event_text(audit: dict[str, Any], event: dict[str, Any]) -> str:
    node_index = {row["node_id"]: row for row in audit.get("semantic_nodes") or []}
    values = [event.get("summary"), event.get("counter_explanation")]
    for ref in event.get("semantic_node_refs") or []:
        node = node_index.get(ref)
        if node:
            values.append(node.get("semantic_state"))
    return " ".join(str(value) for value in values if value).lower()


def any_object_overlap(refs: list[str], text: str, minimum: int) -> tuple[bool, list[str]]:
    matched = []
    for ref in refs:
        if any(token in text for token in object_tokens(ref, minimum)):
            matched.append(ref)
    return bool(matched), matched


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists():
        raise FileExistsError(out)
    out.mkdir(parents=True)
    (out / "route_maps").mkdir()

    contract = load_json(CONTRACT)
    if contract["status"] != "FROZEN_BEFORE_P2_REPLAY":
        raise RuntimeError("P2 contract is not frozen")
    if contract["graph_build"]["semantic_audit_used_as_graph_input"] is not False:
        raise RuntimeError("semantic audit firewall disabled")

    horizon = load_json(ROOT / "configs/stage2_g2_g5_logical_decision_horizon_v1.json")
    max_turns = int(horizon["common_ceiling"])
    fixture = legacy.fixture_map()

    chronology = corrected_observation_index(
        ROOT / contract["inputs"]["corrected_chronology_observations"]
    )
    corrections = load_json(ROOT / contract["inputs"]["targeted_status_corrections"])
    correction_map = {
        (row["full_id"], row["event_id"]): row["reviewed_status"]
        for row in corrections
    }
    primary_old = load_json(ROOT / contract["inputs"]["primary_old_monitor_summary"])
    old_warning_expected = int(primary_old["structure_case"]["monitor_warning_count"])

    graph_rows = []
    candidate_records = []
    cell_rows = []
    audit_rows = []
    route_maps = {}
    totals = Counter()
    group_counts = defaultdict(Counter)
    system_counts = defaultdict(Counter)
    task_counts = defaultdict(Counter)
    no_positive_candidate_counts = []
    corrected_event_overlays = 0
    old_warning_hashes: set[str] = set()

    tracemalloc.start()
    for group in GROUPS:
        natural_root = ROOT / "stage2/replication_v2" / group / "natural_A"
        legacy.NATURAL = natural_root
        for cell in CELLS:
            full_id = f"{group}-{cell}"
            archive_path = natural_root / cell / "first_attempt.tar.gz"
            if not archive_path.exists():
                raise FileNotFoundError(archive_path)
            start = time.perf_counter()
            tracemalloc.reset_peak()

            archive_sha = sha256_file(archive_path)
            ar = legacy.FrozenArchive(cell, archive_sha)
            events = legacy.normalize_cell(ar, max_turns, fixture)
            frozen_old = old_candidates(ar)

            graph = EvidenceGraph()
            for ev in events:
                add_normalized_event(graph, full_id, ev)
            chronology_observation_count = add_corrected_chronology(
                graph, full_id, chronology.get(full_id)
            )
            candidates = candidate_rows(graph, full_id, contract)
            add_unknown_reuse_edges(graph, candidates)
            snapshot = graph.snapshot()
            inspection = inspect_graph(snapshot)

            elapsed = time.perf_counter() - start
            _, peak = tracemalloc.get_traced_memory()
            old_refs = sorted({
                str(row.get("object_ref"))
                for row in frozen_old
                if isinstance(row.get("object_ref"), str) and row.get("object_ref")
            })
            for row in frozen_old:
                warning_id = row.get("candidate_hash")
                if isinstance(warning_id, str) and warning_id:
                    old_warning_hashes.add(warning_id)
                else:
                    old_warning_hashes.add(json_hash({"full_id": full_id, "candidate": row}))
            new_refs = [row["object_ref"] for row in candidates]
            multi_version = sum(
                1 for node in snapshot["nodes"]
                if node["node_type"] == "OBSERVED_OBJECT"
                and len(set(node.get("content_hashes") or [])) >= 2
            )
            unknown_edges = sum(1 for edge in snapshot["edges"] if edge["status"] == "UNKNOWN")
            direct_edges = sum(
                1 for edge in snapshot["edges"]
                if edge["basis"] in {
                    "DIRECT_RUNTIME_RECORD",
                    "DIRECT_RUNTIME_RECORD_REVERSE_INDEX",
                }
            )
            supported_edges_without_evidence = sum(
                1 for edge in snapshot["edges"]
                if edge["status"] == "SUPPORTED" and not edge.get("evidence_refs")
            )
            if supported_edges_without_evidence:
                raise RuntimeError(f"{full_id}: supported edge without evidence")

            audit_path = (
                ROOT
                / contract["inputs"]["full_context_reference_dir"]
                / f"{full_id}.json"
            )
            positive_events = []
            negative_events = []
            graph_resolved = old_localized = new_localized = 0
            if audit_path.exists():
                audit = load_json(audit_path)
                positive_statuses = set(contract["evaluation"]["positive_statuses"])
                minimum = int(contract["evaluation"]["object_token_min_length"])
                graph_object_refs = [
                    node["ref"] for node in snapshot["nodes"]
                    if node["node_type"] == "OBSERVED_OBJECT"
                ]
                for event in audit.get("cpr_events") or []:
                    status = correction_map.get((full_id, event["event_id"]), event["status"])
                    if (full_id, event["event_id"]) in correction_map:
                        corrected_event_overlays += 1
                    text = audit_event_text(audit, event)
                    if status in positive_statuses:
                        g_hit, g_refs = any_object_overlap(graph_object_refs, text, minimum)
                        o_hit, o_refs = any_object_overlap(old_refs, text, minimum)
                        n_hit, n_refs = any_object_overlap(new_refs, text, minimum)
                        graph_resolved += int(g_hit)
                        old_localized += int(o_hit)
                        new_localized += int(n_hit)
                        row = {
                            "schema": "RB-STAGE2-P2-LOCALIZATION-PROXY-v1",
                            "full_id": full_id,
                            "event_id": event["event_id"],
                            "dimension": event.get("dimension"),
                            "effective_status": status,
                            "status_source": (
                                "TARGETED_CHRONOLOGY_REVIEW"
                                if (full_id, event["event_id"]) in correction_map
                                else "FROZEN_FULL_CONTEXT_REVIEW"
                            ),
                            "graph_object_resolved": g_hit,
                            "graph_object_refs": g_refs,
                            "old_monitor_object_localized": o_hit,
                            "old_monitor_object_refs": o_refs,
                            "enhanced_candidate_localized": n_hit,
                            "enhanced_candidate_refs": n_refs,
                            "metric_scope": "OBJECT_REFERENCE_LOCALIZATION_PROXY_NOT_PRIMARY_MONITOR_REPLACEMENT",
                        }
                        audit_rows.append(row)
                        positive_events.append(row)
                    else:
                        negative_events.append({
                            "event_id": event["event_id"],
                            "dimension": event.get("dimension"),
                            "effective_status": status,
                        })

            if audit_path.exists() and not positive_events:
                no_positive_candidate_counts.append(len(candidates))

            cell_row = {
                "schema": "RB-STAGE2-P2-CELL-SUMMARY-v1",
                "full_id": full_id,
                "group_id": group,
                "cell_id": cell,
                "archive_sha256": archive_sha,
                "normalized_event_count": len(events),
                "corrected_chronology_observation_count": chronology_observation_count,
                "graph_hash": snapshot["graph_hash"],
                "graph_node_count": inspection["node_count"],
                "graph_edge_count": inspection["edge_count"],
                "direct_provenance_edge_count": direct_edges,
                "unknown_relation_edge_count": unknown_edges,
                "graph_contradiction_count": len(inspection["contradictions"]),
                "multi_version_object_count": multi_version,
                "old_monitor_warning_count": len(frozen_old),
                "old_monitor_unique_object_count": len(old_refs),
                "enhanced_candidate_object_count": len(candidates),
                "full_context_reference_available": audit_path.exists(),
                "positive_reference_event_count": len(positive_events),
                "graph_resolved_positive_event_count": graph_resolved,
                "old_monitor_localized_positive_event_count": old_localized,
                "enhanced_candidate_localized_positive_event_count": new_localized,
                "replay_seconds": elapsed,
                "peak_tracemalloc_kib": peak / 1024.0,
                "provider_calls": 0,
                "evaluator_calls": 0,
                "repair_calls": 0,
            }
            cell_rows.append(cell_row)
            candidate_records.extend(candidates)
            graph_rows.append({"full_id": full_id, "graph": snapshot})

            totals["cells"] += 1
            totals["events"] += len(events)
            totals["nodes"] += inspection["node_count"]
            totals["edges"] += inspection["edge_count"]
            totals["direct_edges"] += direct_edges
            totals["unknown_edges"] += unknown_edges
            totals["multi_version_objects"] += multi_version
            totals["old_candidate_records"] += len(frozen_old)
            totals["old_unique_objects"] += len(old_refs)
            totals["new_candidates"] += len(candidates)
            totals["reference_positive_events"] += len(positive_events)
            totals["graph_resolved"] += graph_resolved
            totals["old_localized"] += old_localized
            totals["new_localized"] += new_localized
            for bucket in (group_counts[group], system_counts[cell.split("-")[0]], task_counts[cell.split("-")[1]]):
                bucket["cells"] += 1
                bucket["old_candidate_records"] += len(frozen_old)
                bucket["new_candidates"] += len(candidates)
                bucket["reference_positive_events"] += len(positive_events)
                bucket["old_localized"] += old_localized
                bucket["new_localized"] += new_localized
                bucket["graph_resolved"] += graph_resolved

            if full_id in set(contract["priority_route_maps"]):
                seeds = [row["object_ref"] for row in candidates[:3]]
                if not seeds:
                    observed = [
                        node for node in snapshot["nodes"]
                        if node["node_type"] == "OBSERVED_OBJECT"
                    ]
                    observed.sort(
                        key=lambda node: (-len(node.get("event_refs") or []), node["ref"])
                    )
                    seeds = [node["ref"] for node in observed[:1]]
                if seeds:
                    route_maps[full_id] = export_route_map(
                        snapshot,
                        seeds,
                        authorized_write_refs=[],
                        preserve_refs=[],
                        max_depth=2,
                    )

    if totals["cells"] != 84:
        raise RuntimeError(f"expected 84 cells, got {totals['cells']}")
    old_unique_warning_count = len(old_warning_hashes)
    if old_unique_warning_count != old_warning_expected:
        raise RuntimeError(
            f"old monitor unique-warning binding changed: {old_unique_warning_count} != {old_warning_expected}"
        )

    def fraction(num: int, den: int) -> dict[str, Any]:
        return {"numerator": num, "denominator": den, "value": num / den if den else None}

    summary = {
        "schema": "RB-STAGE2-P2-EVIDENCE-GRAPH-REPLAY-SUMMARY-v1",
        "status": "P2_OFFLINE_REPLAY_COMPLETE",
        "population": "G2_G5_84_FROZEN_NATURAL_A",
        "natural_trajectories": totals["cells"],
        "natural_reruns": 0,
        "provider_calls": 0,
        "evaluator_calls": 0,
        "repair_calls": 0,
        "semantic_audit_used_as_graph_input": False,
        "cpr_labels_used_as_graph_input": False,
        "graph": {
            "normalized_event_count": totals["events"],
            "node_count": totals["nodes"],
            "edge_count": totals["edges"],
            "direct_provenance_edge_count": totals["direct_edges"],
            "unknown_relation_edge_count": totals["unknown_edges"],
            "multi_version_object_count": totals["multi_version_objects"],
            "supported_edges_without_evidence": 0,
            "semantic_dependency_edges_generated_without_review": 0,
        },
        "inspection_load": {
            "old_monitor_candidate_record_count": totals["old_candidate_records"],
            "old_monitor_unique_warning_count": old_unique_warning_count,
            "old_monitor_unique_object_count_sum_by_cell": totals["old_unique_objects"],
            "enhanced_candidate_object_count": totals["new_candidates"],
            "enhanced_candidate_vs_old_unique_warning_ratio": fraction(
                totals["new_candidates"], old_unique_warning_count
            ),
        },
        "reference_localization_proxy": {
            "reference_layer": "FROZEN_FULL_CONTEXT_REVIEW_WITH_TARGETED_CHRONOLOGY_STATUS_OVERLAY",
            "replaces_primary_monitor_benchmark": False,
            "corrected_event_overlays_applied": corrected_event_overlays,
            "positive_reference_event_count": totals["reference_positive_events"],
            "graph_object_resolved": fraction(
                totals["graph_resolved"], totals["reference_positive_events"]
            ),
            "old_monitor_object_localized": fraction(
                totals["old_localized"], totals["reference_positive_events"]
            ),
            "enhanced_candidate_object_localized": fraction(
                totals["new_localized"], totals["reference_positive_events"]
            ),
            "metric_scope": "OBJECT_REFERENCE_LOCALIZATION_PROXY_ONLY",
        },
        "negative_reference_cells": {
            "full_context_cells_with_no_positive_cpr_event": len(no_positive_candidate_counts),
            "enhanced_candidate_objects_in_those_cells": sum(no_positive_candidate_counts),
            "median_candidate_objects": (
                sorted(no_positive_candidate_counts)[len(no_positive_candidate_counts) // 2]
                if no_positive_candidate_counts else None
            ),
            "interpretation": "Inspection candidates are not defect predictions; this is candidate load, not a false-positive rate.",
        },
        "priority_route_maps_written": sorted(route_maps),
        "breakdowns": {
            "by_group": {key: dict(value) for key, value in sorted(group_counts.items())},
            "by_system": {key: dict(value) for key, value in sorted(system_counts.items())},
            "by_task": {key: dict(value) for key, value in sorted(task_counts.items())},
        },
        "claim_boundary": (
            "P2 evaluates deterministic graph construction and an object-reference localization proxy over frozen evidence. "
            "It does not replace the sealed primary 84-cell monitor benchmark, does not convert structural candidates into CPR labels, "
            "and does not establish route-repair efficacy."
        ),
    }
    summary["summary_hash"] = json_hash(summary)

    with (out / "evidence_graphs.jsonl.gz").open("wb") as raw_stream:
        with gzip.GzipFile(fileobj=raw_stream, mode="wb", mtime=0) as stream:
            for row in graph_rows:
                stream.write(
                    json.dumps(row, ensure_ascii=False, sort_keys=True).encode("utf-8") + b"\n"
                )
    write_jsonl(out / "candidate_objects.jsonl", candidate_records)
    write_jsonl(out / "localization_proxy.jsonl", audit_rows)
    (out / "cell_summary.json").write_text(
        json.dumps(cell_rows, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    for full_id, route_map in sorted(route_maps.items()):
        (out / "route_maps" / f"{full_id}.json").write_text(
            json.dumps(route_map, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    report = [
        "# Stage-II P2 Offline Evidence Graph Replay Result v1",
        "",
        "Status: **P2 OFFLINE REPLAY COMPLETE**",
        "",
        "## Execution boundary",
        "",
        "- population: G2-G5 frozen Natural A, 84/84 trajectories;",
        "- natural reruns: 0;",
        "- provider/model calls: 0;",
        "- evaluator calls: 0;",
        "- repair calls: 0;",
        "- semantic audit used to build the graph: NO;",
        "- CPR labels used to select graph candidates: NO.",
        "",
        "## Graph replay",
        "",
        f"- normalized structural events: **{totals['events']}**;",
        f"- graph nodes: **{totals['nodes']}**;",
        f"- graph edges: **{totals['edges']}**;",
        f"- direct provenance/query edges: **{totals['direct_edges']}**;",
        f"- explicitly UNKNOWN reuse/dependency edges: **{totals['unknown_edges']}**;",
        f"- multi-version observed objects: **{totals['multi_version_objects']}**;",
        "- supported edges without evidence refs: **0**;",
        "- semantic dependency edges invented without semantic review: **0**.",
        "",
        "Repeated visibility or reuse is represented as UNKNOWN when a dependency cannot be established from direct evidence. "
        "This keeps the graph useful for inspection without converting temporal proximity into causality.",
        "",
        "## Old monitor versus enhanced graph inspection load",
        "",
        f"- frozen old monitor candidate records: **{totals['old_candidate_records']}**;",
        f"- frozen old monitor unique warning IDs: **{old_unique_warning_count}**;",
        f"- old monitor unique object refs summed within cells: **{totals['old_unique_objects']}**;",
        f"- enhanced graph inspection candidate objects: **{totals['new_candidates']}**.",
        "",
        "The enhanced candidate count is an inspection-object count, not an alert-accuracy estimate.",
        "",
        "## Separate localization proxy",
        "",
        "Only after each graph and candidate set was fixed, the frozen full-context review was read as a separate evaluation layer. "
        "Targeted chronology-review status changes were applied only to their exact reviewed event keys.",
        "",
        f"- positive reference events in the available full-context reference: **{totals['reference_positive_events']}**;",
        f"- relevant object resolvable somewhere in the graph: **{totals['graph_resolved']} / {totals['reference_positive_events']}**;",
        f"- old frozen monitor object localized: **{totals['old_localized']} / {totals['reference_positive_events']}**;",
        f"- enhanced graph candidate object localized: **{totals['new_localized']} / {totals['reference_positive_events']}**.",
        "",
        "This is an object-reference localization proxy, not a replacement for the sealed primary 84-cell monitor benchmark.",
        "",
        "## Priority route maps",
        "",
        "Written for: " + ", ".join(sorted(route_maps)) + ".",
        "",
        "These route maps expose observed provenance, version history and unresolved reuse edges. No node receives mutation authority from graph visibility.",
        "",
        "## P2 boundary",
        "",
        "P2 is complete as an offline graph/inspection comparison. It does not authorize P3/P4 repair runs. "
        "A later repair candidate still requires a verified same-parent checkpoint, frozen authorization scope, and separate execution approval.",
    ]
    (out / "P2_Evidence_Graph_Replay_Report_v1.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )

    files = sorted(
        path for path in out.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    )
    manifest = {
        "schema": "RB-STAGE2-P2-EVIDENCE-GRAPH-REPLAY-MANIFEST-v1",
        "status": "SEALED_OFFLINE_RESULT",
        "contract_path": str(CONTRACT.relative_to(ROOT)),
        "contract_sha256": sha256_file(CONTRACT),
        "files": [
            {
                "path": str(path.relative_to(out)),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
            for path in files
        ],
        "summary_hash": summary["summary_hash"],
    }
    manifest["manifest_hash"] = json_hash(manifest)
    (out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print("P2_EVIDENCE_GRAPH_REPLAY=PASS")
    print("CELLS=84")
    print("OLD_CANDIDATE_RECORDS=" + str(totals["old_candidate_records"]))
    print("OLD_UNIQUE_WARNINGS=" + str(old_unique_warning_count))
    print("NEW_CANDIDATES=" + str(totals["new_candidates"]))
    print("REFERENCE_POSITIVE_EVENTS=" + str(totals["reference_positive_events"]))
    print("OLD_LOCALIZED=" + str(totals["old_localized"]))
    print("NEW_LOCALIZED=" + str(totals["new_localized"]))
    print("GRAPH_RESOLVED=" + str(totals["graph_resolved"]))
    print("SUMMARY_HASH=" + summary["summary_hash"])


if __name__ == "__main__":
    main()
