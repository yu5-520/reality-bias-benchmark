#!/usr/bin/env python3
"""Read-only Stage-II frozen evidence materializer for R6-grade semantic audit."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import tarfile
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parents[1]
NATURAL = BASE / "stage2" / "natural_v7"
SCHEMA = "stage2-r6-grade-material-packet-v1"

def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def decode_text(raw: bytes) -> str | None:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None

def parse_json_maybe(text: str) -> Any:
    try:
        return json.loads(text)
    except Exception:
        return None

def terminal_result(stdout: bytes) -> dict | None:
    text = stdout.decode("utf-8", "replace")
    candidates = []
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            candidates.append(obj)
    except Exception:
        pass
    for line in reversed([x.strip() for x in text.splitlines() if x.strip()]):
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if isinstance(obj, dict):
            candidates.append(obj)
    for obj in candidates:
        if any(k in obj for k in ("stop_reason", "answer", "history", "trace", "native_events", "compression_calls")):
            return obj
    return candidates[0] if candidates else None

def text_excerpt(text: str, limit: int = 20000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[TRUNCATED %d CHARS]" % (len(text)-limit)

def semantic_preview(obj: Any) -> dict:
    if not isinstance(obj, dict):
        return {"value": text_excerpt(json.dumps(obj, ensure_ascii=False, default=str), 6000)}
    keys = (
        "type", "source", "sender", "recipient", "role", "name", "target",
        "content", "message", "messages", "request", "response", "result",
        "tool", "tool_name", "arguments", "action", "actions", "status",
        "task", "artifact", "parts", "handoff_target", "function", "error"
    )
    out = {}
    for key in keys:
        if key in obj:
            value = obj[key]
            rendered = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str, sort_keys=True)
            out[key] = text_excerpt(rendered, 6000)
    if not out:
        out["object"] = text_excerpt(json.dumps(obj, ensure_ascii=False, default=str, sort_keys=True), 6000)
    return out

def route_skeleton(result: dict | None) -> list[dict]:
    if not result:
        return []
    rows = result.get("history")
    if not isinstance(rows, list):
        rows = result.get("trace")
    if not isinstance(rows, list):
        return []
    out = []
    for index, row in enumerate(rows, 1):
        if isinstance(row, dict):
            out.append({
                "route_index": index,
                "turn": row.get("turn", index),
                "role": row.get("role") or row.get("agent") or row.get("agent_id") or row.get("source"),
                "valid": row.get("valid"),
                "action_count": row.get("actions") if isinstance(row.get("actions"), int) else None,
                "raw": row
            })
        else:
            out.append({"route_index": index, "turn": index, "role": None, "valid": None, "action_count": None, "raw": row})
    return out

def build_packet(cell_root: Path) -> dict:
    manifest = json.loads((cell_root / "manifest.json").read_text())
    cell = manifest["cell"]
    archive_raw = (cell_root / "first_attempt.tar.gz").read_bytes()
    with tarfile.open(fileobj=io.BytesIO(archive_raw), mode="r:gz") as ar:
        members = {m.name.removeprefix("./"): m for m in ar.getmembers() if m.isfile()}
        def read(name: str) -> bytes:
            return ar.extractfile(members[name]).read()

        observer_prefix = cell + "/observer/"
        stdout_name = observer_prefix + "stdout.bin"
        stderr_name = observer_prefix + "stderr.bin"
        stdout = read(stdout_name) if stdout_name in members else b""
        stderr = read(stderr_name) if stderr_name in members else b""
        result = terminal_result(stdout)

        native_events = []
        event_streams = []
        for name in sorted(members):
            if not name.startswith(observer_prefix) or not name.endswith("events.jsonl"):
                continue
            count = 0
            for line_no, line in enumerate(read(name).splitlines(), 1):
                if not line.strip():
                    continue
                count += 1
                try:
                    row = json.loads(line)
                except Exception:
                    row = {"_unparsed": line.decode("utf-8", "replace")}
                raw_rel = row.get("raw_path") if isinstance(row, dict) else None
                raw_name = name.rsplit("/", 1)[0] + "/" + raw_rel if raw_rel else None
                raw_bytes = read(raw_name) if raw_name in members else b""
                raw_text = decode_text(raw_bytes)
                parsed = parse_json_maybe(raw_text) if raw_text is not None else None
                native_events.append({
                    "stream": name,
                    "line": line_no,
                    "sequence": row.get("sequence") if isinstance(row, dict) else None,
                    "surface": row.get("surface") if isinstance(row, dict) else None,
                    "raw_member": raw_name,
                    "raw_sha256": sha256(raw_bytes) if raw_bytes else None,
                    "raw_bytes": len(raw_bytes),
                    "parsed": parsed,
                    "preview": semantic_preview(parsed) if parsed is not None else (
                        {"text": text_excerpt(raw_text, 12000)} if raw_text is not None else {"binary": True}
                    )
                })
            event_streams.append({"member": name, "events": count})

        textual_members = []
        for name in sorted(members):
            if not name.startswith(observer_prefix):
                continue
            if "/raw/" in name or name.endswith("events.jsonl") or name.endswith("inventory.json"):
                continue
            raw = read(name)
            if len(raw) > 262144:
                continue
            text = decode_text(raw)
            if text is None:
                continue
            parsed = parse_json_maybe(text)
            textual_members.append({
                "member": name,
                "sha256": sha256(raw),
                "bytes": len(raw),
                "parsed": parsed,
                "text": None if parsed is not None else text_excerpt(text, 20000)
            })

        checkout_members = []
        checkout_prefix = cell + "/checkout/"
        for name in sorted(members):
            if not name.startswith(checkout_prefix):
                continue
            raw = read(name)
            text = decode_text(raw)
            checkout_members.append({
                "member": name,
                "relative_path": name[len(checkout_prefix):],
                "sha256": sha256(raw),
                "bytes": len(raw),
                "text": text_excerpt(text, 12000) if text is not None and len(raw) <= 131072 else None
            })

    return {
        "schema": SCHEMA,
        "cell": cell,
        "archive_sha256": sha256(archive_raw),
        "manifest": manifest,
        "terminal_result": result,
        "route_skeleton": route_skeleton(result),
        "event_streams": event_streams,
        "native_events": native_events,
        "textual_observer_members": textual_members,
        "checkout_members": checkout_members,
        "stderr_excerpt": text_excerpt(stderr.decode("utf-8", "replace"), 12000),
        "evidence_policy": {"read_only": True, "semantic_labels_assigned": False, "subject_calls": 0, "reruns": 0}
    }

def packet_markdown(packet: dict) -> str:
    lines = [
        "# %s | R6-grade frozen evidence packet" % packet["cell"],
        "",
        "- schema: %s" % packet["schema"],
        "- archive_sha256: %s" % packet["archive_sha256"],
        "- task_outcome: %s" % packet["manifest"].get("task_outcome"),
        "- stop_reason: %s" % packet["manifest"].get("stop_reason"),
        "- runner_returncode: %s" % packet["manifest"].get("runner_returncode"),
        "- native events: %d" % len(packet["native_events"]),
        "- route skeleton nodes: %d" % len(packet["route_skeleton"]),
        "",
        "## Complete recorded route skeleton",
        ""
    ]
    if packet["route_skeleton"]:
        lines += ["| idx | turn | role | valid | actions |", "|---:|---:|---|---|---:|"]
        for row in packet["route_skeleton"]:
            lines.append("| %s | %s | %s | %s | %s |" % (
                row["route_index"], row.get("turn"), row.get("role"), row.get("valid"), row.get("action_count")
            ))
    else:
        lines.append("Runner terminal object exposes no history/trace list; native event stream below is the route evidence.")

    lines += ["", "## Native passive-observer events", ""]
    for ev in packet["native_events"]:
        lines.append("### event %s | surface=%s | %s" % (ev.get("sequence"), ev.get("surface"), ev.get("raw_member")))
        lines.append("")
        lines.append("    " + json.dumps(ev["preview"], ensure_ascii=False, sort_keys=True))
        lines.append("")

    lines += ["## Other textual observer artifacts", ""]
    for item in packet["textual_observer_members"]:
        lines.append("### %s" % item["member"])
        if item["parsed"] is not None:
            rendered = text_excerpt(json.dumps(item["parsed"], ensure_ascii=False, sort_keys=True), 20000)
            lines.append("    " + rendered.replace("\n", "\n    "))
        elif item["text"]:
            lines.append("    " + item["text"].replace("\n", "\n    "))
        lines.append("")

    lines += ["## Frozen checkout files", ""]
    for item in packet["checkout_members"]:
        lines.append("### %s | sha256=%s" % (item["relative_path"], item["sha256"]))
        if item["text"] is not None:
            lines.append("    " + item["text"].replace("\n", "\n    "))
        lines.append("")
    return "\n".join(lines) + "\n"

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(NATURAL / "r6_grade_material"))
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    cells = []
    for task in range(1, 4):
        for probe in range(1, 8):
            root = NATURAL / ("X%d-T%d" % (probe, task))
            if not root.exists():
                raise SystemExit("missing frozen cell: %s" % root)
            packet = build_packet(root)
            cell = packet["cell"]
            (out / (cell + ".json")).write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
            (out / (cell + ".md")).write_text(packet_markdown(packet))
            cells.append({
                "cell": cell,
                "archive_sha256": packet["archive_sha256"],
                "route_nodes": len(packet["route_skeleton"]),
                "native_events": len(packet["native_events"]),
                "textual_observer_members": len(packet["textual_observer_members"]),
                "checkout_files": len(packet["checkout_members"]),
                "task_outcome": packet["manifest"].get("task_outcome"),
                "stop_reason": packet["manifest"].get("stop_reason")
            })

    index = {
        "schema": "stage2-r6-grade-material-index-v1",
        "cells": cells,
        "natural_cells": len(cells),
        "subject_calls": 0,
        "reruns": 0,
        "semantic_judgement": "NOT_PERFORMED_BY_MATERIALIZER"
    }
    (out / "index.json").write_text(json.dumps(index, indent=2, sort_keys=True) + "\n")
    print(json.dumps(index, sort_keys=True))

if __name__ == "__main__":
    main()
