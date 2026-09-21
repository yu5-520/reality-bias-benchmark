#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import os
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "evidence" / "frozen_raw"
REGISTRY = ROOT / "configs" / "frozen_raw_public_release_registry_v1.json"
MANIFEST = FROZEN / "release_manifest_v1.json"
SUMS = FROZEN / "SHA256SUMS_v1.txt"

def fail(msg: str) -> None:
    raise SystemExit("FROZEN_RAW_IMMUTABILITY_FAILED: " + msg)

def git_exists(ref: str, path: str) -> bool:
    p = subprocess.run(
        ["git", "cat-file", "-e", f"{ref}:{path}"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return p.returncode == 0

def check_history(base: str | None) -> None:
    if not base or set(base) == {"0"}:
        return
    frozen_paths = [
        "evidence/frozen_raw/release_manifest_v1.json",
        "evidence/frozen_raw/SHA256SUMS_v1.txt",
    ]
    for path in frozen_paths:
        if git_exists(base, path):
            p = subprocess.run(
                ["git", "diff", "--quiet", base, "HEAD", "--", path],
                cwd=ROOT,
            )
            if p.returncode != 0:
                fail("v1 frozen registry file modified after publication: " + path)

    if git_exists(base, "evidence/frozen_raw/catalog_v1"):
        out = subprocess.check_output(
            ["git", "diff", "--name-status", base, "HEAD", "--", "evidence/frozen_raw/catalog_v1"],
            cwd=ROOT,
            text=True,
        ).strip()
        if out:
            fail("catalog_v1 changed after publication; publish catalog_v2 instead: " + out.replace("\n", "; "))

def api_release(repo: str, token: str) -> dict:
    url = f"https://api.github.com/repos/{repo}/releases/tags/frozen-raw-evidence-v1"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "reality-bias-frozen-raw-validator",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=None)
    args = ap.parse_args()

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    sums_rows = {}
    for line in SUMS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split(None, 1)
        sums_rows[name.strip()] = digest.strip()

    if manifest["artifact_count"] != len(registry["artifacts"]):
        fail("manifest artifact count differs from frozen registry")
    if manifest["artifact_count"] != 24:
        fail("v1 artifact count must remain 24")

    for row in manifest["artifacts"]:
        name = row["release_asset_name"]
        if sums_rows.get(name) != row["sha256"]:
            fail("SHA256SUMS mismatch for " + name)

    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for required in ("results/raw/", "results/scored/", "results/runs/"):
        if required not in gitignore:
            fail("runtime ignore removed: " + required)

    check_history(args.base)

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if token and repo:
        rel = api_release(repo, token)
        assets = {a["name"]: a for a in rel.get("assets", [])}
        for row in manifest["artifacts"]:
            name = row["release_asset_name"]
            if name not in assets:
                fail("release asset missing: " + name)
            remote_digest = (assets[name].get("digest") or "").removeprefix("sha256:")
            if remote_digest and remote_digest != row["sha256"]:
                fail("release asset digest mismatch: " + name)

    print("FROZEN_RAW_IMMUTABILITY=PASS")
    print("FROZEN_RAW_PUBLIC_ASSET_COUNT=24")
    print("RUNTIME_RAW_IGNORE=PASS")
    print("VERSION_RULE=APPEND_ONLY_NEW_VERSION")

if __name__ == "__main__":
    main()
