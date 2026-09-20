#!/usr/bin/env python3
from __future__ import annotations

import argparse, gzip, hashlib, json, zipfile
from pathlib import Path

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]

def pct(n, d):
    return round(100.0*n/d, 4) if d else None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--triage-zip", required=True)
    ap.add_argument("--r8-records", required=True)
    ap.add_argument("--r8-manifest", required=True)
    ap.add_argument("--triage-summary", required=True)
    ap.add_argument("--r8-summary", required=True)
    ap.add_argument("--legacy-b2-summary", required=True)
    ap.add_argument("--outdir", required=True)
    args=ap.parse_args()

    out=Path(args.outdir); out.mkdir(parents=True, exist_ok=True)
    triage_dir=out/"triage_extract"; triage_dir.mkdir(exist_ok=True)
    with zipfile.ZipFile(args.triage_zip) as z:
        z.extractall(triage_dir)

    triage_cases=load_jsonl(triage_dir/"semantic_triage_cases.jsonl")
    triage_trajs=load_jsonl(triage_dir/"trajectory_triage_summary.jsonl")
    triage_summary=load_json(Path(args.triage_summary))
    r8_summary=load_json(Path(args.r8_summary))
    b2=load_json(Path(args.legacy_b2_summary))
    manifest=load_json(Path(args.r8_manifest))

    raw=Path(args.r8_records).read_bytes()
    declared=manifest["outputs"]["full_records_gzip"]
    actual_sha=sha256_bytes(raw)
    magic=raw[:16].hex()
    gzip_magic=raw[:2] == b"\x1f\x8b"
    gzip_readable=False
    gzip_error=None
    uncompressed_sha=None
    uncompressed_size=None
    line_count=None
    try:
        plain=gzip.decompress(raw)
        gzip_readable=True
        uncompressed_sha=sha256_bytes(plain)
        uncompressed_size=len(plain)
        line_count=sum(1 for x in plain.splitlines() if x.strip())
    except Exception as e:
        gzip_error=f"{type(e).__name__}: {e}"

    integrity={
      "path":str(args.r8_records),
      "actual_size_bytes":len(raw),
      "actual_sha256":actual_sha,
      "actual_magic_hex_first16":magic,
      "gzip_magic_present":gzip_magic,
      "gzip_readable":gzip_readable,
      "gzip_error":gzip_error,
      "declared_git_blob":declared.get("git_blob"),
      "declared_compressed_sha256":declared.get("compressed_sha256"),
      "compressed_sha_matches_manifest":actual_sha == declared.get("compressed_sha256"),
      "declared_uncompressed_sha256":declared.get("uncompressed_sha256"),
      "declared_uncompressed_size_bytes":declared.get("uncompressed_size_bytes"),
      "actual_uncompressed_sha256":uncompressed_sha,
      "actual_uncompressed_size_bytes":uncompressed_size,
      "actual_jsonl_line_count":line_count,
      "exact_episode_recall_computable": bool(gzip_readable and line_count == 141)
    }

    structural_candidate_rows=2127
    selected_cases=int(triage_summary["selected_unique_case_count"])
    heldout=90
    b2_selected=int(b2["structurally_selected_unique_trajectories"])
    p_nat=int(r8_summary["P"]["supported_source_counts"]["R2-R4_NATURAL"])
    r_nat=int(r8_summary["R"]["supported_source_counts"]["R2-R4_NATURAL"])

    calibration={
      "heldout_natural_trajectory_count":heldout,
      "structural_candidate_row_count":structural_candidate_rows,
      "triage_selected_unique_case_count":selected_cases,
      "candidate_surface_retention_percent":pct(selected_cases,structural_candidate_rows),
      "candidate_surface_compression_percent":pct(structural_candidate_rows-selected_cases,structural_candidate_rows),
      "authority_review_trajectory_count":sum(triage_summary["authority_review_trajectory_counts"].values()),
      "authority_review_trajectory_coverage_percent":pct(sum(triage_summary["authority_review_trajectory_counts"].values()),heldout),
      "legacy_b2_selected_unique_trajectory_count":b2_selected,
      "legacy_b2_selected_trajectory_percent":pct(b2_selected,heldout),
      "legacy_b2_window_counts":b2["selected_windows"],
      "legacy_b2_supported_counts":b2["adjudication"],
      "later_full_trajectory_supported_P_in_heldout_natural":p_nat,
      "later_full_trajectory_supported_R_in_heldout_natural":r_nat,
      "later_full_trajectory_supported_P_count_fraction_of_90_percent":pct(p_nat,heldout),
      "later_full_trajectory_supported_R_count_fraction_of_90_percent":pct(r_nat,heldout),
      "important_boundary":[
        "The P/R percentages are counts within the 90 held-out cohort, not a new prevalence claim.",
        "Legacy B2 zero P/R versus later full-trajectory P=13/R=12 demonstrates window-level semantic insufficiency, but does not by itself identify structural-scout miss rate.",
        "Exact episode-level structural-scout recall/miss rate requires the per-trajectory R8 records to be readable."
      ]
    }

    triage_binding={
      "artifact_trajectory_rows":len(triage_trajs),
      "artifact_selected_case_rows":len(triage_cases),
      "unique_source_run_ids":len({x["source_run_id"] for x in triage_trajs}),
      "formation_assignments":triage_summary["role_assignment_counts"]["FORMATION_ANCHOR"],
      "propagation_assignments":triage_summary["role_assignment_counts"]["PROPAGATION_ANCHOR"],
      "authority_review_assignments":triage_summary["role_assignment_counts"]["AUTHORITY_REVIEW_ANCHOR"],
    }

    result={
      "schema":"RB-NMI-P4-STRUCTURAL-SCOUT-RECALL-INTEGRITY-CALIBRATION-v0.1",
      "date":"2026-09-20",
      "status":"EXACT_EPISODE_RECALL_READY" if integrity["exact_episode_recall_computable"] else "EXACT_EPISODE_RECALL_BLOCKED_BY_R8_RECORD_INTEGRITY",
      "r8_full_record_integrity":integrity,
      "triage_binding":triage_binding,
      "summary_level_calibration":calibration,
      "scientific_boundary":{
        "candidate_surface_retention_is_semantic_recall":False,
        "legacy_window_zero_equals_structural_scout_zero_recall":False,
        "exact_miss_rate_claim_allowed":integrity["exact_episode_recall_computable"],
        "new_subject_run":False,
        "new_provider_call":False,
        "new_evaluator_call":False,
        "raw_evidence_mutation":False
      }
    }
    (out/"integrity_and_calibration.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

    md=f"""# NMI-P4 Structural Scout Recall Attack — Integrity & Calibration Result

Status: **{result['status']}**

## Summary-level calibration

- Held-out natural trajectories: **{heldout}**
- Structural repair-anchor candidate rows: **{structural_candidate_rows}**
- Triage selected unique cases: **{selected_cases}**
- Candidate-surface retention: **{calibration['candidate_surface_retention_percent']}%**
- Candidate-surface compression: **{calibration['candidate_surface_compression_percent']}%**
- Authority-review anchors present in **{calibration['authority_review_trajectory_count']}/{heldout} = {calibration['authority_review_trajectory_coverage_percent']}%** trajectories
- Legacy B2 structurally selected trajectories: **{b2_selected}/{heldout} = {calibration['legacy_b2_selected_trajectory_percent']}%**
- Legacy B2 semantic window adjudication: **P=0, R=0**
- Later full-trajectory R8: **P={p_nat}, R={r_nat}** among the same 90 held-out natural cohort

These figures do **not** yet yield the structural-scout recall/miss rate. They establish that narrow-window semantic adjudication was insufficient and that final R8 had to review complete trajectories.

## Full-record integrity gate

- Actual file size: **{len(raw)} bytes**
- Actual SHA-256: `{actual_sha}`
- Manifest compressed SHA-256: `{declared.get('compressed_sha256')}`
- SHA match: **{integrity['compressed_sha_matches_manifest']}**
- First 16 bytes (hex): `{magic}`
- gzip magic present: **{gzip_magic}**
- gzip readable: **{gzip_readable}**
- read error: `{gzip_error}`

Exact episode-level recall is {'READY' if integrity['exact_episode_recall_computable'] else 'BLOCKED'}.

## Interpretation

The 7.85%-class candidate retention is a compression statistic, not recall. Likewise, the legacy window audit's zero P/R cannot be interpreted as zero structural recall because later full-trajectory verdicts may depend on context outside the selected window.

The correct next step is to recover a byte-identical valid copy matching the frozen R8 manifest if one exists. The current repository object must remain immutable. If no valid original can be recovered, the manuscript must report structural scouting as non-exhaustive prioritization and must not claim a calibrated exact miss rate.
"""
    (out/"integrity_and_calibration.md").write_text(md,encoding="utf-8")

    print("NMI_P4_SCOUT_RECALL_INTEGRITY_CALIBRATION=COMPLETE")
    print(f"STATUS={result['status']}")
    print(f"CANDIDATE_SURFACE_RETENTION_PERCENT={calibration['candidate_surface_retention_percent']}")
    print(f"CANDIDATE_SURFACE_COMPRESSION_PERCENT={calibration['candidate_surface_compression_percent']}")
    print(f"LEGACY_B2_SELECTED_TRAJECTORY_PERCENT={calibration['legacy_b2_selected_trajectory_percent']}")
    print(f"LATER_FULL_TRAJECTORY_NATURAL_P={p_nat}")
    print(f"LATER_FULL_TRAJECTORY_NATURAL_R={r_nat}")
    print(f"R8_GZIP_READABLE={gzip_readable}")
    print(f"R8_COMPRESSED_SHA_MATCH={integrity['compressed_sha_matches_manifest']}")
    print(f"EXACT_MISS_RATE_ALLOWED={integrity['exact_episode_recall_computable']}")

if __name__=="__main__":
    main()
