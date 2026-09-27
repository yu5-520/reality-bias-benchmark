#!/usr/bin/env python3
import hashlib
import json
import tarfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("stage2/replication_v2/primary_monitor_benchmark_84_v1")
BROOT = Path("_layer_b_reference/stage2/replication_v2/semantic_audit_reference_v1/audit")
EVIDENCE_ROOTS = {
    "G2": Path("_g2"),
    "G3": Path("_g3"),
    "G4": Path("_g4"),
    "G5": Path("_g5"),
}
GROUPS = ("G2", "G3", "G4", "G5")
XS = tuple(f"X{i}" for i in range(1, 8))
TS = ("T1", "T2", "T3")
POSITIVE_STATUS = {"SUPPORTED", "SUPPORTED_CANDIDATE"}

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def load_json(path: Path):
    return json.loads(path.read_text())

def tar_member_by_basename(tf: tarfile.TarFile, basename: str):
    matches = [m for m in tf.getmembers() if m.isfile() and Path(m.name).name == basename]
    if not matches:
        return None
    if len(matches) != 1:
        raise RuntimeError(f"ambiguous {basename}: {[m.name for m in matches]}")
    return matches[0]

def load_json_from_tar(tf: tarfile.TarFile, basename: str):
    member = tar_member_by_basename(tf, basename)
    if member is None:
        return None, None
    fh = tf.extractfile(member)
    if fh is None:
        raise RuntimeError(f"cannot extract {member.name}")
    data = fh.read()
    return json.loads(data), sha256_bytes(data)

def main():
    protocol = load_json(Path("configs/stage2_monitor_evaluation_protocol_v1.json"))
    rule_path = Path("configs/stage2_monitor_source_bound_matching_rule_v1.json")
    rule = load_json(rule_path)
    bindex = load_json(BROOT / "reference_set_index.json")

    assert protocol["primary_population"]["natural_trajectories"] == 84
    assert protocol["primary_population"]["groups"] == list(GROUPS)
    assert protocol["monitor_freeze"]["posthoc_threshold_tuning_for_primary_result"] is False
    assert rule["no_posthoc_tuning"] is True
    assert bindex["cell_count"] == 84
    assert bindex["population"] == "G2_G5_84_NATURAL_A"
    assert bindex["status"] == "SEALED_MONITOR_BLIND_REFERENCE_SET"
    assert bindex["monitor_blind"] is True
    assert bindex["monitor_runtime_bundle_read"] is False

    fammap = {k: set(v) for k, v in rule["monitor_rule_to_compatible_structure_families"].items()}
    minlen = int(rule["object_matching"]["minimum_token_length"])

    def tail(obj):
        if not obj:
            return ""
        s = str(obj).strip().lower()
        if ":" in s:
            s = s.split(":", 1)[1]
        return s.strip()

    def object_tokens(obj):
        s = tail(obj)
        vals = set()
        if len(s) >= minlen:
            vals.add(s)
        base = s.rsplit("/", 1)[-1]
        if len(base) >= minlen:
            vals.add(base)
        stem = base.rsplit(".", 1)[0]
        if len(stem) >= minlen:
            vals.add(stem)
        return vals

    def ref_text(rr):
        vals = [
            rr.get("semantic_before"),
            rr.get("semantic_after"),
            rr.get("semantic_delta"),
            rr.get("source_ref"),
            rr.get("carrier_ref"),
            rr.get("consequence_ref"),
            rr.get("decision_or_action_ref"),
        ]
        return " ".join(str(x) for x in vals if x is not None).lower()

    def compatible(c, rr):
        return rr.get("structure_family") in fammap.get(c.get("rule_id"), set())

    def overlap(c, rr):
        txt = ref_text(rr)
        return any(tok in txt for tok in object_tokens(c.get("object_ref")))

    def temporal_ok(c, rr):
        cs = c.get("prefix_sequence")
        rs = rr.get("first_consequence_sequence")
        if cs is None or rs is None:
            return True
        return int(cs) <= int(rs)

    def score(c, rr):
        if not compatible(c, rr) or not temporal_ok(c, rr):
            return -1
        return 2 if overlap(c, rr) else 1

    ROOT.mkdir(parents=True, exist_ok=True)
    records = []
    source_rows = []
    cell_rows = []
    warning_state = {}
    by_group = defaultdict(Counter)
    by_x = defaultdict(Counter)
    by_t = defaultdict(Counter)
    by_family = defaultdict(Counter)

    for group in GROUPS:
        evidence_root = EVIDENCE_ROOTS[group]
        for x in XS:
            for t in TS:
                cell = f"{x}-{t}"
                full = f"{group}-{cell}"
                arc = evidence_root / f"stage2/replication_v2/{group}/natural_A/{cell}/first_attempt.tar.gz"
                if not arc.exists():
                    raise FileNotFoundError(f"{full}: missing {arc}")

                candidate_present = False
                runtime_manifest_present = False
                candidates = []
                candidate_sha = None
                with tarfile.open(arc, "r:gz") as tf:
                    loaded, candidate_sha = load_json_from_tar(tf, "monitor_candidates.json")
                    if loaded is not None:
                        if not isinstance(loaded, list):
                            raise TypeError(f"{full}: monitor_candidates.json must be a list")
                        candidates = loaded
                        candidate_present = True
                    runtime_manifest_present = tar_member_by_basename(tf, "monitor_runtime_bundle_manifest.json") is not None

                for c in candidates:
                    if c.get("semantic_audit_used") not in (False, None):
                        raise AssertionError(f"{full}: semantic audit leaked into monitor candidate")
                    if c.get("cpr_label") is not None:
                        raise AssertionError(f"{full}: CPR label leaked into monitor candidate")
                    if c.get("future_evidence_used") not in (False, None):
                        raise AssertionError(f"{full}: future evidence used by monitor candidate")
                    if not c.get("candidate_hash"):
                        raise AssertionError(f"{full}: candidate missing hash")

                source_rows.append({
                    "full_id": full,
                    "group_id": group,
                    "cell_id": cell,
                    "source_archive_path": f"stage2/replication_v2/{group}/natural_A/{cell}/first_attempt.tar.gz",
                    "source_archive_sha256": sha256_file(arc),
                    "monitor_candidates_present": candidate_present,
                    "monitor_candidates_sha256": candidate_sha,
                    "monitor_candidate_count": len(candidates),
                    "monitor_runtime_bundle_manifest_present": runtime_manifest_present,
                })

                bf = BROOT / "cell_audits" / f"{full}.json"
                if not bf.exists():
                    raise FileNotFoundError(f"{full}: missing Layer-B cell audit")
                b = load_json(bf)
                assert b["group_id"] == group and b["cell_id"] == cell
                assert b["monitor_blind"] is True
                assert b["monitor_runtime_bundle_read"] is False

                positives = [
                    rr for rr in b["reference_records"]
                    if (not rr.get("negative_case")) and rr.get("claim_status") in POSITIVE_STATUS
                ]
                negatives = [
                    rr for rr in b["reference_records"]
                    if rr.get("negative_case") or rr.get("claim_status") == "NEGATIVE_BOUNDARY"
                ]

                matched_warning_ids = set()
                strict_hits = broad_hits = observable_pos = unobservable_pos = 0

                for rr in positives:
                    options = sorted(
                        ((score(c, rr), c) for c in candidates),
                        key=lambda z: (z[0], -(z[1].get("prefix_sequence") or 0)),
                        reverse=True,
                    )
                    best_score, best = options[0] if options else (-1, None)
                    observable = bool(rr.get("evidence_surface_available", True))
                    observable_pos += int(observable)
                    unobservable_pos += int(not observable)

                    if best_score == 2:
                        klass = "SUPPORTED_MATCH"
                        strict_hits += 1
                        broad_hits += 1
                    elif best_score == 1:
                        klass = "PARTIAL_LOCALIZATION"
                        broad_hits += 1
                    else:
                        klass = "MISS" if observable else "UNOBSERVABLE_REFERENCE"

                    wid = best.get("candidate_hash") if best_score >= 1 and best else None
                    if wid:
                        matched_warning_ids.add(wid)
                        warning_state[wid] = "SUPPORTED"
                    first_warn = best.get("prefix_sequence") if wid else None
                    first_cons = rr.get("first_consequence_sequence")
                    lead = (
                        first_cons - first_warn
                        if isinstance(first_cons, int) and isinstance(first_warn, int)
                        else None
                    )

                    records.append({
                        "evaluation_id": f"AB84:{full}:{rr['reference_id']}",
                        "group_id": group,
                        "cell_id": cell,
                        "monitor_version": "RB-STAGE2-R7-G1-ONLINE-MONITOR-CONTRACT-v1",
                        "matching_rule_version": "stage2-monitor-source-bound-matching-rule-v1",
                        "reference_id": rr["reference_id"],
                        "warning_id": wid,
                        "structure_family": rr.get("structure_family"),
                        "match_class": klass,
                        "observable_reference": observable,
                        "source_match": True if best_score == 2 else (False if best_score == 1 else None),
                        "carrier_match": True if best_score == 2 else (False if best_score == 1 else None),
                        "consumer_match": None,
                        "decision_link_match": None,
                        "lineage_node_reference_count": None,
                        "lineage_node_matched_count": None,
                        "lineage_edge_reference_count": None,
                        "lineage_edge_matched_count": None,
                        "first_warning_sequence": first_warn,
                        "first_consequence_sequence": first_cons,
                        "lead_decisions": lead,
                        "notes": "Frozen source-bound match over the 84-cell primary population; no Layer-C verdict or posthoc CPR label used.",
                    })
                    by_group[group][klass] += 1
                    by_x[x][klass] += 1
                    by_t[t][klass] += 1
                    by_family[rr.get("structure_family") or "NULL"][klass] += 1

                for c in candidates:
                    wid = c.get("candidate_hash")
                    if wid in matched_warning_ids:
                        continue
                    rejected = any(
                        compatible(c, rr) and temporal_ok(c, rr) and overlap(c, rr)
                        for rr in negatives
                    )
                    klass = "AUDIT_REJECTED_WARNING" if rejected else "UNSUPPORTED_WARNING"
                    if warning_state.get(wid) != "SUPPORTED":
                        warning_state[wid] = "REJECTED" if rejected else "UNSUPPORTED"
                    records.append({
                        "evaluation_id": f"AB84:{full}:WARN:{wid[:16]}",
                        "group_id": group,
                        "cell_id": cell,
                        "monitor_version": "RB-STAGE2-R7-G1-ONLINE-MONITOR-CONTRACT-v1",
                        "matching_rule_version": "stage2-monitor-source-bound-matching-rule-v1",
                        "reference_id": None,
                        "warning_id": wid,
                        "structure_family": None,
                        "match_class": klass,
                        "observable_reference": False,
                        "source_match": None,
                        "carrier_match": None,
                        "consumer_match": None,
                        "decision_link_match": None,
                        "lineage_node_reference_count": None,
                        "lineage_node_matched_count": None,
                        "lineage_edge_reference_count": None,
                        "lineage_edge_matched_count": None,
                        "first_warning_sequence": c.get("prefix_sequence"),
                        "first_consequence_sequence": None,
                        "lead_decisions": None,
                        "notes": f"Unmatched frozen warning; rule_id={c.get('rule_id')} object_ref={c.get('object_ref')}.",
                    })

                target_pos = len(positives)
                cell_rows.append({
                    "full_id": full,
                    "group_id": group,
                    "cell_id": cell,
                    "positive_reference_count": target_pos,
                    "observable_positive_reference_count": observable_pos,
                    "unobservable_positive_reference_count": unobservable_pos,
                    "strict_matched_reference_count": strict_hits,
                    "broad_matched_reference_count": broad_hits,
                    "monitor_warning_count": len(candidates),
                    "monitor_candidates_present": candidate_present,
                    "trajectory_positive": target_pos > 0,
                    "trajectory_hit": bool(target_pos > 0 and broad_hits > 0),
                })

    assert len(source_rows) == 84
    assert len(cell_rows) == 84

    supported = sum(1 for v in warning_state.values() if v == "SUPPORTED")
    rejected = sum(1 for v in warning_state.values() if v == "REJECTED")
    unsupported = sum(1 for v in warning_state.values() if v == "UNSUPPORTED")
    warn_total = len(warning_state)
    pos_refs = sum(r["positive_reference_count"] for r in cell_rows)
    obs_refs = sum(r["observable_positive_reference_count"] for r in cell_rows)
    unobs_refs = sum(r["unobservable_positive_reference_count"] for r in cell_rows)
    strict = sum(r["strict_matched_reference_count"] for r in cell_rows)
    broad = sum(r["broad_matched_reference_count"] for r in cell_rows)
    pos_traj = sum(1 for r in cell_rows if r["trajectory_positive"])
    hit_traj = sum(1 for r in cell_rows if r["trajectory_hit"])
    matched_observable = sum(
        1 for r in records
        if r["reference_id"] is not None
        and r["observable_reference"]
        and r["match_class"] in {"SUPPORTED_MATCH", "PARTIAL_LOCALIZATION"}
    )

    def frac(n, d):
        return {"numerator": n, "denominator": d, "value": (n / d if d else None)}

    summary = {
        "schema": "stage2-primary-monitor-benchmark-84-summary-v1",
        "state": "SEALED",
        "population": "G2_G5_84_NATURAL_A_PRIMARY",
        "cell_count": 84,
        "primary_population_contract_satisfied": True,
        "layer_b_monitor_blind": True,
        "layer_c_used": False,
        "monitor_generation_used_cpr_labels": False,
        "matching_rule_version": "stage2-monitor-source-bound-matching-rule-v1",
        "matching_rule_sha256": sha256_file(rule_path),
        "monitor_output_availability": {
            "cells_with_monitor_candidates_file": sum(1 for r in source_rows if r["monitor_candidates_present"]),
            "cells_without_monitor_candidates_file": sum(1 for r in source_rows if not r["monitor_candidates_present"]),
            "cells_with_monitor_runtime_bundle_manifest": sum(1 for r in source_rows if r["monitor_runtime_bundle_manifest_present"]),
            "cells_without_monitor_runtime_bundle_manifest": sum(1 for r in source_rows if not r["monitor_runtime_bundle_manifest_present"]),
        },
        "trajectory": {
            "audit_target_positive_trajectories": pos_traj,
            "monitor_hit_trajectories": hit_traj,
            "trajectory_detection_rate": frac(hit_traj, pos_traj),
            "trajectory_miss_rate": frac(pos_traj - hit_traj, pos_traj),
        },
        "structure_case": {
            "audit_confirmed_structure_count": pos_refs,
            "strict_matched_structure_count": strict,
            "broad_matched_structure_count": broad,
            "strict_structure_recall": frac(strict, pos_refs),
            "broad_structure_recall": frac(broad, pos_refs),
            "structure_miss_rate_broad": frac(pos_refs - broad, pos_refs),
            "monitor_warning_count": warn_total,
            "audit_supported_warning_count": supported,
            "warning_precision": frac(supported, warn_total),
            "audit_rejected_warning_count": rejected,
            "audit_rejected_warning_rate": frac(rejected, warn_total),
            "unsupported_warning_count": unsupported,
            "unsupported_warning_rate": frac(unsupported, warn_total),
        },
        "observability": {
            "all_audit_reference_structures": pos_refs,
            "observable_reference_structures": obs_refs,
            "unobservable_reference_structures": unobs_refs,
            "end_to_end_capture_rate_full_reference_set": frac(broad, pos_refs),
            "conditional_detector_recall_observable_reference_set": frac(matched_observable, obs_refs),
            "unobservable_reference_rate": frac(unobs_refs, pos_refs),
        },
        "breakdowns": {
            "by_group": {k: dict(v) for k, v in sorted(by_group.items())},
            "by_system": {k: dict(v) for k, v in sorted(by_x.items())},
            "by_task": {k: dict(v) for k, v in sorted(by_t.items())},
            "by_structure_family": {k: dict(v) for k, v in sorted(by_family.items())},
        },
        "scope_statement": protocol["publication_boundary"]["required_scope_statement"],
        "interpretation_rules": [
            "This is the primary 84-cell A↔B prospective monitor benchmark required by the frozen protocol.",
            "Layer B is a sealed monitor-blind within-study reference, not universal ground truth.",
            "Layer C is not read or used to define this benchmark population or its matches.",
            "A missing monitor-candidate file remains an observed monitor-output boundary and is not silently removed from the primary population.",
            "SUPPORTED_MATCH requires frozen family compatibility, source/carrier object overlap, and valid temporal ordering.",
            "PARTIAL_LOCALIZATION is reported separately and is not counted as strict localization.",
            "References with unavailable required evidence are distinguished from detector misses.",
            "Warnings are counted once by frozen candidate_hash, preserving the previously frozen matching implementation.",
        ],
    }

    source_index = {
        "schema": "stage2-primary-monitor-benchmark-84-source-index-v1",
        "state": "SEALED_INPUT_BINDING",
        "cell_count": 84,
        "source_population": "G2_G5_84_FIRST_ATTEMPT_NATURAL_A",
        "layer_b_reference_index_sha256": sha256_file(BROOT / "reference_set_index.json"),
        "matching_rule_sha256": sha256_file(rule_path),
        "layer_c_used": False,
        "records": source_rows,
    }

    (ROOT / "monitor_source_index.json").write_text(json.dumps(source_index, indent=2, sort_keys=True) + "\n")
    with (ROOT / "evaluation_records.jsonl").open("w") as f:
        for r in records:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    (ROOT / "cell_summary.json").write_text(json.dumps(cell_rows, indent=2, sort_keys=True) + "\n")
    (ROOT / "evaluation_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    disposition = {
        "schema": "stage2-layer-a-b-80-subset-disposition-v1",
        "state": "FROZEN_DISPOSITION",
        "legacy_path": "stage2/replication_v2/gpt56sol_full_context_semantic_audit_v1/layer_a_b_monitor_evaluation_v1",
        "legacy_population": "G2_G5_LAYER_C_ELIGIBLE_80_CELLS",
        "role": "LAYER_C_ALIGNED_SUBSET_DIAGNOSTIC",
        "primary_benchmark": False,
        "reason": "The frozen monitor-evaluation protocol preregistered all 84 G2-G5 Natural-A trajectories as the primary prospective monitor population. Layer-C process-surface eligibility cannot redefine the A↔B primary denominator.",
        "primary_replacement_path": "stage2/replication_v2/primary_monitor_benchmark_84_v1",
        "legacy_artifacts_modified": False,
    }
    (ROOT / "legacy_80_subset_disposition.json").write_text(json.dumps(disposition, indent=2, sort_keys=True) + "\n")

    seal = {
        "schema": "stage2-primary-monitor-benchmark-84-seal-v1",
        "state": "SEALED",
        "cell_count": 84,
        "primary_population": "G2_G5_84_NATURAL_A",
        "matching_rule_frozen_before_evaluation": True,
        "monitor_cpr_label_freeze_confirmed": True,
        "layer_b_monitor_blind_confirmed": True,
        "layer_c_used": False,
        "evaluation_summary_sha256": sha256_file(ROOT / "evaluation_summary.json"),
        "evaluation_records_sha256": sha256_file(ROOT / "evaluation_records.jsonl"),
        "monitor_source_index_sha256": sha256_file(ROOT / "monitor_source_index.json"),
        "legacy_80_subset_disposition_sha256": sha256_file(ROOT / "legacy_80_subset_disposition.json"),
        "next_stage": "ENGINEERING_ELIGIBILITY_FREEZE",
    }
    (ROOT / "benchmark_seal.json").write_text(json.dumps(seal, indent=2, sort_keys=True) + "\n")

    print(json.dumps({
        "status": "PASS",
        "cells": 84,
        "positive_references": pos_refs,
        "warnings": warn_total,
        "strict_matches": strict,
        "broad_matches": broad,
        "supported_warnings": supported,
        "rejected_warnings": rejected,
        "unsupported_warnings": unsupported,
        "candidate_files_present": summary["monitor_output_availability"]["cells_with_monitor_candidates_file"],
    }, sort_keys=True))

if __name__ == "__main__":
    main()
