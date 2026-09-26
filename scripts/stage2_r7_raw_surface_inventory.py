from __future__ import annotations

import io
import json
import tarfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "stage2/natural_v7"
OUT = ROOT / "stage2/r7_monitor_v1/raw_surface_inventory.json"


def decode_json(raw: bytes):
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None


def preview_value(value, depth=0):
    if depth > 2:
        return type(value).__name__
    if isinstance(value, dict):
        return {k: preview_value(v, depth + 1) for k, v in list(value.items())[:12]}
    if isinstance(value, list):
        return [preview_value(v, depth + 1) for v in value[:3]]
    if isinstance(value, str):
        return value[:300]
    return value


def summarize_archive(cell_dir: Path):
    raw = (cell_dir / "first_attempt.tar.gz").read_bytes()
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as tf:
        members = {m.name.removeprefix("./"): m for m in tf.getmembers() if m.isfile()}

        def read(name: str) -> bytes:
            return tf.extractfile(members[name]).read()

        cell = cell_dir.name
        prefix = f"{cell}/observer/"
        out = {
            "cell": cell,
            "member_count": len(members),
            "member_paths": sorted(members),
            "json_files": [],
            "jsonl_files": [],
            "observer_event_streams": [],
            "stdout_preview": None,
            "stderr_preview": None,
        }

        for name in sorted(members):
            if name.endswith(".json"):
                obj = decode_json(read(name))
                if obj is not None:
                    out["json_files"].append({
                        "path": name,
                        "type": type(obj).__name__,
                        "keys": sorted(obj.keys()) if isinstance(obj, dict) else None,
                        "preview": preview_value(obj),
                    })
            elif name.endswith(".jsonl"):
                lines = [x for x in read(name).splitlines() if x.strip()]
                parsed = []
                key_union = set()
                for line in lines:
                    obj = decode_json(line)
                    if obj is not None:
                        parsed.append(obj)
                        if isinstance(obj, dict):
                            key_union.update(obj)
                out["jsonl_files"].append({
                    "path": name,
                    "line_count": len(lines),
                    "parsed_count": len(parsed),
                    "keys": sorted(key_union),
                    "preview": [preview_value(x) for x in parsed[:3]],
                })

        for name in sorted(members):
            if not (name.startswith(prefix) and name.endswith("/events.jsonl")):
                continue
            events = [decode_json(x) for x in read(name).splitlines() if x.strip()]
            events = [x for x in events if isinstance(x, dict)]
            surfaces = Counter(str(x.get("surface")) for x in events)
            raw_preview = []
            native_root = name.removesuffix("events.jsonl")
            for event in events[:5]:
                raw_path = event.get("raw_path")
                target = native_root + str(raw_path)
                if target not in members:
                    continue
                payload = read(target)
                obj = decode_json(payload)
                if obj is not None:
                    value = preview_value(obj)
                else:
                    try:
                        value = payload.decode("utf-8", "replace")[:1200]
                    except Exception:
                        value = "<binary>"
                raw_preview.append({
                    "sequence": event.get("sequence"),
                    "surface": event.get("surface"),
                    "raw_path": raw_path,
                    "value": value,
                })
            out["observer_event_streams"].append({
                "path": name,
                "event_count": len(events),
                "surface_counts": dict(sorted(surfaces.items())),
                "first_raw_events": raw_preview,
            })

        for key in ["stdout_preview", "stderr_preview"]:
            basename = "stdout.bin" if key == "stdout_preview" else "stderr.bin"
            candidates = [n for n in members if n == prefix + basename]
            if candidates:
                text = read(candidates[0]).decode("utf-8", "replace")
                out[key] = text[-5000:]

        return out


def main():
    cells = []
    for x in range(1, 8):
        for t in range(1, 4):
            cells.append(summarize_archive(BASE / f"X{x}-T{t}"))
    payload = {
        "schema": "RB-STAGE2-R7-RAW-SURFACE-INVENTORY-v1",
        "purpose": "Offline structural surface discovery only; no semantic-audit input.",
        "cells": cells,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("RAW_SURFACE_INVENTORY=PASS")
    print("CELLS=" + str(len(cells)))


if __name__ == "__main__":
    main()
