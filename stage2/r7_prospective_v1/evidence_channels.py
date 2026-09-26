from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable


AUDIT_FORBIDDEN_TOKENS = (
    "monitor_evidence",
    "monitor_candidates",
    "repair_packages",
    "runtime_bridge",
    "native_event_index",
    "wire_index",
    "semantic_audit_reference",
    "cpr_prediction",
)
MONITOR_FORBIDDEN_TOKENS = (
    "semantic_audit_reference",
    "posthoc_audit",
    "audit_verdict",
)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _entries(out_root: Path, paths: Iterable[str | Path], *, forbidden_tokens: tuple[str, ...]):
    rows = []
    seen = set()
    for item in paths:
        target = out_root / item
        if not target.exists():
            continue
        candidates = [target]
        if target.is_dir():
            candidates = sorted(path for path in target.rglob("*") if path.is_file())
        for path in candidates:
            rel = str(path.relative_to(out_root))
            lower = rel.lower()
            if any(token in lower for token in forbidden_tokens):
                raise RuntimeError(f"evidence channel contains forbidden path: {rel}")
            if rel in seen:
                continue
            seen.add(rel)
            rows.append({
                "path": rel,
                "sha256": _sha256(path),
                "bytes": path.stat().st_size,
            })
    return rows


def _write(path: Path, payload: dict):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def seal_evidence_channels(
    *,
    out_root,
    group_id: str,
    cell_id: str,
    audit_paths: Iterable[str | Path],
    monitor_paths: Iterable[str | Path],
) -> dict:
    out = Path(out_root)
    audit_entries = _entries(out, audit_paths, forbidden_tokens=AUDIT_FORBIDDEN_TOKENS)
    monitor_entries = _entries(out, monitor_paths, forbidden_tokens=MONITOR_FORBIDDEN_TOKENS)

    audit_manifest = {
        "schema": "RB-STAGE2-AUDIT-RAW-BUNDLE-MANIFEST-v1",
        "group_id": group_id,
        "cell_id": cell_id,
        "role": "MONITOR_BLIND_SEMANTIC_AUDIT_INPUT",
        "monitor_runtime_bundle_readable_before_reference_seal": False,
        "entries": audit_entries,
        "entry_count": len(audit_entries),
        "forbidden_monitor_derived_inputs": list(AUDIT_FORBIDDEN_TOKENS),
    }
    monitor_manifest = {
        "schema": "RB-STAGE2-MONITOR-RUNTIME-BUNDLE-MANIFEST-v1",
        "group_id": group_id,
        "cell_id": cell_id,
        "role": "PROSPECTIVE_MONITOR_OUTPUT",
        "posthoc_semantic_audit_input": False,
        "entries": monitor_entries,
        "entry_count": len(monitor_entries),
        "forbidden_posthoc_audit_inputs": list(MONITOR_FORBIDDEN_TOKENS),
    }
    audit_hash = hashlib.sha256(
        json.dumps(audit_manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    monitor_hash = hashlib.sha256(
        json.dumps(monitor_manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    audit_manifest["manifest_sha256"] = audit_hash
    monitor_manifest["manifest_sha256"] = monitor_hash

    _write(out / "audit_raw_bundle_manifest.json", audit_manifest)
    _write(out / "monitor_runtime_bundle_manifest.json", monitor_manifest)
    return {
        "audit_raw_bundle_manifest_sha256": audit_hash,
        "monitor_runtime_bundle_manifest_sha256": monitor_hash,
        "audit_entry_count": len(audit_entries),
        "monitor_entry_count": len(monitor_entries),
    }
