#!/usr/bin/env python3
"""Seal offline packet corrections and dependency changes, never semantic labels.

Inputs must be independently rebuilt baseline/corrected packet directories.
This command has no provider, repair, subject-run or GitHub mutation capability.
"""
from __future__ import annotations

import argparse
from collections import Counter
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile

BASE = "6687f2187d929fd8614df0735209a8f3efdb1450"
ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(Path(path).read_text())


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def check_packet(packet):
    copy = dict(packet)
    copy["packet_sha256"] = ""
    assert packet["packet_sha256"] == sha(encoded(copy)), "packet digest mismatch"


def same_item(item):
    # References are local to a packet and may be renumbered after correction.
    return encoded({k: v for k, v in item.items() if k != "ref"})


def legacy_blind_state(cell_dir):
    """Reconstruct the old derived object even if its frozen preview was clipped."""
    raw = (cell_dir / "first_attempt.tar.gz").read_bytes()
    assert sha(raw) == read(cell_dir / "attempt_receipt.json")["archive_sha256"]
    with tarfile.open(fileobj=io.BytesIO(gzip.decompress(raw)), mode="r:") as archive:
        members = {m.name.removeprefix("./"): m for m in archive.getmembers() if m.isfile()}
        def obj(path):
            return json.load(archive.extractfile(members[path]))
        if "audit_raw_bundle_manifest.json" not in members:
            return None
        allowed = {r["path"] for r in obj("audit_raw_bundle_manifest.json")["entries"]}
        rows = []
        for path in allowed:
            if path.startswith("checkpoints/") and path.endswith("/manifest.json"):
                value = obj(path)
                if isinstance(value.get("application_file_hashes"), dict):
                    seq = value.get("model_decision_sequence", 0)
                    rows.append((seq if isinstance(seq, int) else 0, path, value))
        if not rows:
            return None
        rows.sort(key=lambda r: (r[0], r[1]))  # Deliberately reproduce the OLD defect.
        first, last = rows[0], rows[-1]
        a, b = first[2]["application_file_hashes"], last[2]["application_file_hashes"]
        changed = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
        return {"derived_from": [first[1], last[1]], "first_event_ref": first[2]["event_ref"],
                "last_event_ref": last[2]["event_ref"], "changed_files": changed,
                "first_hashes": {k: a.get(k) for k in changed}, "last_hashes": {k: b.get(k) for k in changed}}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corrected-root", type=Path, required=True)
    ap.add_argument("--baseline-root", type=Path, required=True)
    ap.add_argument("--sources-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    paired_rows, natural_rows, ref_rows, archives = [], [], [], []
    packets = {}
    legacy = ROOT / "stage2/replication_v2"
    formal = legacy / "gpt56sol_full_context_semantic_audit_v1/formal_review"
    comparison = formal.parent / "layer_b_c_comparison/cells"

    for group in ("G2", "G3", "G4", "G5"):
        files = sorted((args.corrected_root / group / "packets").glob("X*.json"))
        assert len(files) == (12 if group == "G3" else 11)
        packets[group] = []
        for file in files:
            new = read(file)
            old = read(legacy / group / "paired_semantic_audit_v1/packets" / file.name)
            check_packet(new)
            packets[group].append(new)
            for arm in ("arm_A", "arm_B"):
                a, b = old[arm]["repository_diff"], new[arm]["repository_diff"]
                paired_rows.append({
                    "group_id": group, "cell_id": new["cell_id"], "arm": arm,
                    "old_packet_sha256": old["packet_sha256"], "new_packet_sha256": new["packet_sha256"],
                    "old": a, "corrected": b,
                    "endpoint_changed": a["final_checkpoint_hash"] != b["final_checkpoint_hash"],
                    "repository_diff_changed": a["hash_transitions"] != b["hash_transitions"],
                    "legacy_effect": read(legacy / group / "paired_semantic_audit_v1/audits" / file.name)["paired_effect"]["overall_process_effect"],
                    "semantic_readjudication": "NOT_AUTOMATICALLY_PERFORMED",
                })
    for kind, expected in (("full_context", 80), ("blind", 84)):
        files = sorted((args.corrected_root / kind).glob("G*.json"))
        assert len(files) == expected
        packets[kind] = []
        for file in files:
            old = read(args.baseline_root / kind / file.name)
            new = read(file)
            check_packet(old)
            check_packet(new)
            packets[kind].append(new)
            if kind == "full_context":
                audit = read(formal / file.name)
                assert old["packet_sha256"] == audit["input_packet_sha256"], file.name
                a, b = old.get("repository_state"), new.get("repository_state")
                expected_old = audit["input_packet_sha256"]
                current_items = {same_item(x): x["ref"] for x in new["evidence"]}
                mapping = {x["ref"]: current_items.get(same_item(x)) for x in old["evidence"]}
                for event in audit["cpr_events"]:
                    refs = event.get("evidence_refs", [])
                    changed = [ref for ref in refs if mapping.get(ref) is None]
                    ref_rows.append({
                        "full_id": file.stem, "event_id": event["event_id"],
                        "dimension": event["dimension"], "legacy_status": event["status"],
                        "changed_or_missing_evidence_refs": changed,
                        "unchanged_ref_mapping": {ref: mapping[ref] for ref in refs if mapping.get(ref)},
                        "status": "REASSESS_EVIDENCE" if changed else "CITED_ITEMS_UNCHANGED_NOT_A_NEW_VERDICT",
                    })
            else:
                expected_old = read(comparison / file.name)["layer_b"]["packet_sha256"] if (comparison / file.name).exists() else None
                if expected_old:
                    assert old["packet_sha256"] == expected_old, file.name
                group, cell = new["group_id"], new["cell_id"]
                a = legacy_blind_state(args.sources_root / (group + "A") / "stage2/replication_v2" / group / "natural_A" / cell)
                b = new.get("repository_state")
            def diff(state):
                if not state: return None
                return {k: state.get(k) for k in ("changed_files", "hash_transitions", "first_hashes", "last_hashes")}
            natural_rows.append({
                "kind": kind, "full_id": file.stem,
                "baseline_packet_sha256": old["packet_sha256"], "corrected_packet_sha256": new["packet_sha256"],
                "frozen_baseline_binding_verified": expected_old is not None,
                "old_repository_state": a, "corrected_repository_state": b,
                "repository_diff_changed": diff(a) != diff(b),
                "packet_changed": old["packet_sha256"] != new["packet_sha256"],
            })
    assert len(paired_rows) == 90 and len(ref_rows) == 240

    for name, content in packets.items():
        raw = b"".join(encoded(p) + b"\n" for p in content)
        zipped = gzip.compress(raw, mtime=0)
        filename = name + "_corrected_packets.jsonl.gz"
        (args.out / filename).write_bytes(zipped)
        archives.append({"path": filename, "packet_count": len(content), "sha256": sha(zipped), "uncompressed_sha256": sha(raw)})
    for name, content in (("paired_changes", paired_rows), ("natural_changes", natural_rows), ("semantic_reference_dependencies", ref_rows)):
        (args.out / (name + ".json")).write_text(json.dumps(content, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    summary = {
        "schema": "stage2-frozen-chronology-correction-v1", "source_main_commit": BASE,
        "status": "DERIVATIONS_CORRECTED_SEMANTIC_IMPACT_REQUIRES_REVIEW",
        "subject_calls": 0, "provider_calls": 0, "repair_calls": 0, "raw_evidence_modified": False,
        "paired": {
            "pairs": 45, "arms": 90,
            "endpoint_changed": sum(r["endpoint_changed"] for r in paired_rows),
            "repository_diff_changed": sum(r["repository_diff_changed"] for r in paired_rows),
            "affected_pairs": sorted({r["group_id"] + "-" + r["cell_id"] for r in paired_rows if r["repository_diff_changed"]}),
        },
        "natural": {kind: {
            "packets": sum(r["kind"] == kind for r in natural_rows),
            "frozen_baseline_binding_verified": sum(r["kind"] == kind and r["frozen_baseline_binding_verified"] for r in natural_rows),
            "repository_diff_changed": sum(r["kind"] == kind and r["repository_diff_changed"] for r in natural_rows),
        } for kind in ("full_context", "blind")},
        "semantic_dependencies": dict(Counter(r["status"] for r in ref_rows)),
        "replacement_semantic_counts": None, "replacement_engineering_effect_counts": None,
        "replacement_monitor_performance": None,
        "claim_boundary": "Unchanged cited items do not certify a semantic judgment against newly visible counterevidence. Dependency screening is not re-adjudication.",
        "corrected_packet_archives": archives,
    }
    (args.out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
