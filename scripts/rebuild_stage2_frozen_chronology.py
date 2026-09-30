#!/usr/bin/env python3
"""Rebuild frozen evidence offline from already-fetched Git source commits.

No model/provider calls and no workflow dispatch. Requires Python 3.12+ and Git.
The output directory must not exist; old evidence is never overwritten.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
BASE = "6687f2187d929fd8614df0735209a8f3efdb1450"


def run(argv):
    result = subprocess.run(argv, cwd=ROOT, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work-dir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    work = args.work_dir.resolve()
    work.mkdir(parents=True, exist_ok=False)
    sources = work / "sources"
    for group in range(2, 6):
        cfg = json.loads((ROOT / f"configs/stage2_g{group}_ab_paired_semantic_audit_v1.json").read_text())
        for arm, key, folder in (("A", "natural_A_evidence_commit", "natural_A"), ("B", "repair_B_evidence_commit", "engineering_B_v1")):
            dest = sources / f"G{group}{arm}"
            dest.mkdir(parents=True)
            prefix = f"stage2/replication_v2/G{group}/{folder}"
            raw = subprocess.check_output(["git", "archive", cfg["source"][key], prefix], cwd=ROOT)
            with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
                archive.extractall(dest, filter="data")
    corrected, baseline = work / "corrected", work / "baseline"
    source_args = [value for g in range(2, 6) for value in (f"--g{g}", str(sources / f"G{g}A"))]
    commands = []
    for group in range(2, 6):
        commands.append([sys.executable, f"arena/build_stage2_g{group}_ab_semantic_packets_v1.py",
                         "--a-root", str(sources / f"G{group}A"), "--b-root", str(sources / f"G{group}B"),
                         "--config", f"configs/stage2_g{group}_ab_paired_semantic_audit_v1.json",
                         "--out", str(corrected / f"G{group}")])
    for name, kind in (("build_stage2_full_context_semantic_packets.py", "full_context"),
                       ("build_stage2_84a_monitor_blind_audit_packets.py", "blind")):
        extra = ["--config", "configs/stage2_gpt56sol_full_context_audit_v1.json"] if kind == "full_context" else []
        commands.append([sys.executable, "arena/" + name, *source_args, *extra, "--out", str(corrected / kind)])
        original = subprocess.check_output(["git", "show", BASE + ":arena/" + name], cwd=ROOT).decode()
        # Byte-preserving decompression optimization only. Rebuilt baseline hashes
        # are checked against the original audit bindings by the packaging step.
        optimized = original.replace("import argparse", "import argparse\nimport gzip", 1).replace(
            'tarfile.open(fileobj=io.BytesIO(arc),mode="r:gz")',
            'tarfile.open(fileobj=io.BytesIO(gzip.decompress(arc)),mode="r:")')
        script = work / ("baseline_" + name)
        script.write_text(optimized)
        commands.append([sys.executable, str(script), *source_args, *extra, "--out", str(baseline / kind)])
    with ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(run, commands):
            print(result, flush=True)
    print(run([sys.executable, "scripts/package_stage2_chronology_correction.py",
               "--corrected-root", str(corrected), "--baseline-root", str(baseline),
               "--sources-root", str(sources), "--out", str(args.out.resolve())]))


if __name__ == "__main__":
    main()
