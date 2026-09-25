"""Redownload an exact pretrained revision and verify a committed study manifest."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from .prepare import ASSETS


ROOT = Path(__file__).resolve().parents[2]
MANIFESTS = {
    "X6": ROOT / "stage2/native_v7/study/x6_embedding_manifest.json",
    "X7": ROOT / "stage2/native_v7/study/x7_checkpoint_manifest.json",
}


def validate(probe, out_root):
    from huggingface_hub import snapshot_download

    spec = ASSETS[probe]
    manifest = json.loads(MANIFESTS[probe].read_text())
    if (manifest.get("schema") != spec["schema"] or
            manifest.get("purpose") != "STAGE2_NATURAL_STUDY" or
            manifest.get("model_id") != spec["model_id"] or
            not isinstance(manifest.get("revision"), str) or
            len(manifest["revision"]) != 40):
        raise ValueError("committed study manifest identity differs from asset selection")
    snapshot = Path(snapshot_download(
        repo_id=manifest["model_id"],
        revision=manifest["revision"],
        allow_patterns=spec["allow_patterns"],
        ignore_patterns=spec["ignore_patterns"],
    ))
    target = Path(out_root) / "checkpoint"
    shutil.copytree(snapshot, target, symlinks=False)
    observed = {
        str(p.relative_to(target)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(target.rglob("*")) if p.is_file()
    }
    if observed != manifest["files_sha256"]:
        raise ValueError("downloaded study checkpoint differs from committed file hashes")
    if any(p.is_symlink() for p in target.rglob("*")):
        raise ValueError("study checkpoint contains symlinks")
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", required=True, choices=sorted(ASSETS))
    parser.add_argument("--out-root", required=True)
    args = parser.parse_args()
    print(f"PASS: {args.probe} checkpoint at {validate(args.probe, args.out_root)}")
