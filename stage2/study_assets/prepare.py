"""Non-study download and fingerprint of real public pretrained assets.

No task, subject-model call, cell reservation or registry mutation occurs here.
"""

import argparse
import hashlib
import json
import shutil
from pathlib import Path


ASSETS = {
    "X6": {
        "model_id": "sentence-transformers/all-MiniLM-L6-v2",
        "schema": "stage2-x6-embedding-manifest-v1",
        "allow_patterns": ["*.json", "*.txt", "*.bin", "*.safetensors", "*.model"],
        "ignore_patterns": ["onnx/**", "openvino/**"],
    },
    "X7": {
        "model_id": "distilbert/distilgpt2",
        "schema": "stage2-x7-checkpoint-manifest-v1",
        "allow_patterns": ["*.json", "*.txt", "*.safetensors", "*.model"],
        "ignore_patterns": [],
    },
}


def prepare(probe, out_root):
    from huggingface_hub import HfApi, snapshot_download

    spec = ASSETS[probe]
    revision = HfApi().model_info(spec["model_id"]).sha
    if not revision or len(revision) != 40:
        raise ValueError("source revision is not an exact commit")
    snapshot = Path(snapshot_download(
        repo_id=spec["model_id"],
        revision=revision,
        allow_patterns=spec["allow_patterns"],
        ignore_patterns=spec["ignore_patterns"],
    ))
    target = Path(out_root) / "checkpoint"
    shutil.copytree(snapshot, target, symlinks=False)
    files = {
        str(p.relative_to(target)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(target.rglob("*")) if p.is_file()
    }
    if not files or not any(name.endswith((".bin", ".safetensors")) for name in files):
        raise ValueError("real pretrained weights were not downloaded")
    manifest = {
        "schema": spec["schema"],
        "purpose": "STAGE2_NATURAL_STUDY",
        "model_id": spec["model_id"],
        "revision": revision,
        "files_sha256": files,
    }
    destination = Path(out_root) / "study_manifest.json"
    destination.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", required=True, choices=sorted(ASSETS))
    parser.add_argument("--out-root", required=True)
    args = parser.parse_args()
    result = prepare(args.probe, args.out_root)
    print(json.dumps({"probe": args.probe, "model_id": result["model_id"],
                      "revision": result["revision"], "files": len(result["files_sha256"])}, sort_keys=True))
