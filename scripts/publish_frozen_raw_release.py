#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import tarfile
import urllib.request
import zipfile
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def slug(s: str) -> str:
    s = re.sub(r"[^A-Za-z0-9._-]+", "-", s.strip())
    return s.strip("-") or "artifact"

def api_json(url: str, token: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "reality-bias-frozen-raw-publisher",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)

def download_artifact_zip(repo: str, artifact_id: int, token: str, out: Path) -> None:
    url = f"https://api.github.com/repos/{repo}/actions/artifacts/{artifact_id}/zip"
    subprocess.run(
        [
            "curl", "--fail", "--silent", "--show-error", "--location",
            "-H", f"Authorization: Bearer {token}",
            "-H", "Accept: application/vnd.github+json",
            "-H", "X-GitHub-Api-Version: 2022-11-28",
            "-o", str(out), url,
        ],
        check=True,
    )

def nested_tar_catalog(zf: zipfile.ZipFile, info: zipfile.ZipInfo) -> list[dict]:
    data = zf.read(info)
    items: list[dict] = []
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as tf:
            for member in tf.getmembers():
                if not member.isfile():
                    continue
                items.append({
                    "path": member.name,
                    "bytes": member.size,
                    "kind": "tar_member",
                    "is_raw_trace": member.name.endswith("traces.jsonl"),
                    "is_journal": "/journals/" in member.name,
                    "is_snapshot": "/snapshots/" in member.name,
                })
    except tarfile.TarError:
        return []
    return items

def inspect_archive(path: Path) -> dict:
    entries: list[dict] = []
    nested: list[dict] = []
    with zipfile.ZipFile(path, "r") as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            row = {
                "path": info.filename,
                "bytes": info.file_size,
                "compressed_bytes": info.compress_size,
                "kind": "zip_member",
                "is_raw_trace": info.filename.endswith("traces.jsonl"),
                "is_journal": "/journals/" in info.filename,
                "is_snapshot": "/snapshots/" in info.filename,
            }
            entries.append(row)
            if info.filename.endswith((".tar.gz", ".tgz", ".tar")):
                members = nested_tar_catalog(zf, info)
                if members:
                    nested.append({"container": info.filename, "members": members})
    return {"zip_entries": entries, "nested_archives": nested}

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", default="configs/frozen_raw_public_release_registry_v1.json")
    ap.add_argument("--dist", default="dist/frozen_raw_release_v1")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        raise SystemExit("GITHUB_TOKEN/GITHUB_REPOSITORY required")

    registry = json.loads((ROOT / args.registry).read_text(encoding="utf-8"))
    tag = registry["release_tag"]
    dist = ROOT / args.dist
    assets_dir = dist / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    public_root = ROOT / "evidence" / "frozen_raw"
    catalog_dir = public_root / "catalog_v1"
    catalog_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for spec in registry["artifacts"]:
        artifact_id = int(spec["artifact_id"])
        expected = spec["digest"].removeprefix("sha256:")
        meta = api_json(f"https://api.github.com/repos/{repo}/actions/artifacts/{artifact_id}", token)
        if meta.get("expired"):
            raise SystemExit(f"artifact expired before publication: {artifact_id}")
        api_digest = (meta.get("digest") or "").removeprefix("sha256:")
        if api_digest and api_digest != expected:
            raise SystemExit(f"artifact API digest mismatch {artifact_id}: {api_digest} != {expected}")

        original_name = meta["name"]
        asset_name = f"{slug(spec['category'])}__{artifact_id}__{slug(original_name)}.zip"
        local = assets_dir / asset_name
        download_artifact_zip(repo, artifact_id, token, local)
        actual = sha256_file(local)
        if actual != expected:
            raise SystemExit(f"downloaded artifact digest mismatch {artifact_id}: {actual} != {expected}")

        release_url = f"https://github.com/{repo}/releases/download/{tag}/{quote(asset_name)}"
        archive_catalog = inspect_archive(local)
        raw_trace_paths = []
        journal_paths = []
        snapshot_paths = []
        for ent in archive_catalog["zip_entries"]:
            if ent["is_raw_trace"]:
                raw_trace_paths.append(ent["path"])
            if ent["is_journal"]:
                journal_paths.append(ent["path"])
            if ent["is_snapshot"]:
                snapshot_paths.append(ent["path"])
        for nested in archive_catalog["nested_archives"]:
            for ent in nested["members"]:
                p = f"{nested['container']}::{ent['path']}"
                if ent["is_raw_trace"]:
                    raw_trace_paths.append(p)
                if ent["is_journal"]:
                    journal_paths.append(p)
                if ent["is_snapshot"]:
                    snapshot_paths.append(p)

        row = {
            "artifact_id": artifact_id,
            "category": spec["category"],
            "role": spec["role"],
            "original_artifact_name": original_name,
            "release_asset_name": asset_name,
            "release_asset_url": release_url,
            "sha256": actual,
            "bytes": local.stat().st_size,
            "historical_created_at": meta.get("created_at"),
            "historical_expires_at": meta.get("expires_at"),
            "historical_actions_artifact_expired": bool(meta.get("expired")),
            "raw_trace_paths": raw_trace_paths,
            "journal_path_count": len(journal_paths),
            "snapshot_path_count": len(snapshot_paths),
            "archive_catalog": archive_catalog,
        }
        rows.append(row)
        (catalog_dir / f"artifact_{artifact_id}.json").write_text(
            json.dumps(row, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"FROZEN_RAW_VERIFIED artifact={artifact_id} sha256={actual}")

    release_manifest = {
        "schema": "RB-FROZEN-RAW-PUBLIC-RELEASE-MANIFEST-v1",
        "date": "2026-09-21",
        "status": "VERIFIED_FOR_PUBLIC_RELEASE",
        "repository": repo,
        "release_tag": tag,
        "release_url": f"https://github.com/{repo}/releases/tag/{tag}",
        "artifact_count": len(rows),
        "policy": registry["policy"],
        "artifacts": [
            {k: row[k] for k in (
                "artifact_id", "category", "role", "original_artifact_name",
                "release_asset_name", "release_asset_url", "sha256", "bytes",
                "raw_trace_paths", "journal_path_count", "snapshot_path_count"
            )}
            for row in rows
        ],
    }
    (public_root / "release_manifest_v1.json").write_text(
        json.dumps(release_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (dist / "release_manifest_v1.json").write_text(
        json.dumps(release_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    sums = "\n".join(f"{row['sha256']}  {row['release_asset_name']}" for row in rows) + "\n"
    (public_root / "SHA256SUMS_v1.txt").write_text(sums, encoding="utf-8")
    (dist / "SHA256SUMS_v1.txt").write_text(sums, encoding="utf-8")

    lines = [
        "# Frozen raw evidence — public access",
        "",
        "These archives are the byte-preserved raw evidence packages originally frozen as GitHub Actions artifacts during the experiments.",
        "",
        "**Frozen means immutable evidence, not hidden evidence.** Runtime working directories remain ignored so experiments cannot accidentally overwrite raw outputs, while completed frozen packages are published as public release assets and locked by SHA-256 in this repository.",
        "",
        f"Public release: https://github.com/{repo}/releases/tag/{tag}",
        "",
        "The historical Actions copies had retention expiry dates. The release assets below remove that expiry dependency. Historical artifact IDs and digests remain recorded for provenance.",
        "",
        "## Evidence packages",
        "",
        "| Category | Role | Artifact ID | Raw trace paths | Public asset | SHA-256 |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['category']} | {row['role']} | {row['artifact_id']} | "
            f"{len(row['raw_trace_paths'])} | [download]({row['release_asset_url']}) | "
            f"{row['sha256']} |"
        )
    lines += [
        "",
        "## How to inspect without modifying evidence",
        "",
        "1. Download an archive from the table.",
        "2. Verify it against SHA256SUMS_v1.txt.",
        "3. Use unzip -l on the asset to list the outer package.",
        "4. Use the matching catalog_v1/artifact_<id>.json to locate traces.jsonl, journals and snapshots.",
        "5. Extract to a separate local directory for inspection. Do not write derived analysis back into the frozen archive.",
        "",
        "Nested tar.gz raw bundles are preserved byte-for-byte. Their internal file listings are included in the per-artifact catalog files.",
        "",
        "## Version rule",
        "",
        "A correction never replaces a frozen archive. It must be published as a new version with a new digest, as with the historical malformed/recovered R8 pair.",
        "",
    ]
    (public_root / "README.md").write_text("\n".join(lines), encoding="utf-8")

    release_notes = [
        "# Frozen Raw Evidence v1",
        "",
        "Public, byte-preserved raw evidence packages for the first Process Reality study.",
        "",
        f"Artifacts: {len(rows)}",
        "",
        "Every uploaded archive was downloaded from its historical GitHub Actions artifact ID and verified against the SHA-256 digest frozen in the repository source registries before publication.",
        "",
        "Runtime raw directories remain ignored to prevent accidental mutation. This release is the public read/download surface for completed frozen evidence.",
        "",
        "Use release_manifest_v1.json and SHA256SUMS_v1.txt to verify identity.",
    ]
    (dist / "RELEASE_NOTES.md").write_text("\n".join(release_notes) + "\n", encoding="utf-8")
    print(f"FROZEN_RAW_PUBLICATION_PREPARED={len(rows)}")
    print(f"RELEASE_TAG={tag}")

if __name__ == "__main__":
    main()
