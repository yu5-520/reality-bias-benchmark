from __future__ import annotations

import hashlib
import io
import json
import re
import tarfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NATURAL = ROOT / "stage2/natural_v7"
FIXTURE = ROOT / "stage2/fixtures/project"
RULES_PATH = ROOT / "configs/stage2_r7_structural_monitor_rules_v1.json"
BOUNDARY_PATH = ROOT / "configs/stage2_r7_boundary_contract_v1.json"
SOURCE_FREEZE_PATH = ROOT / "configs/stage2_r7_21_path_source_freeze_v1.json"
OUT = ROOT / "stage2/r7_monitor_v1"

FILE_RE = re.compile(r"(?<![A-Za-z0-9_])((?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\.(?:py|json|md|js|html|yaml|yml|txt))(?![A-Za-z0-9_])")
IMMUTABLE_PREFIXES = ("rag-hit:", "memory-recall:", "compression-channel:")
ROOT_PREFIXES = ("root-message:", "root-task:")


def canon(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def digest(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canon(value)
    return hashlib.sha256(raw).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_json_bytes(raw: bytes) -> Any | None:
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None


def parse_terminal_json(raw: bytes) -> dict[str, Any]:
    text = raw.decode("utf-8", "replace")
    for line in reversed(text.splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict) and ("stop_reason" in row or "history" in row):
            return row
    return {}


def file_refs_from_text(text: str) -> list[str]:
    if not isinstance(text, str):
        return []
    return list(dict.fromkeys("file:" + x for x in FILE_RE.findall(text)))


class FrozenArchive:
    def __init__(self, cell: str, expected_sha: str):
        self.cell = cell
        path = NATURAL / cell / "first_attempt.tar.gz"
        self.raw = path.read_bytes()
        if digest(self.raw) != expected_sha:
            raise ValueError(f"{cell}: source archive hash mismatch")
        self.tf = tarfile.open(fileobj=io.BytesIO(self.raw), mode="r:gz")
        self.members = {
            m.name.removeprefix("./"): m
            for m in self.tf.getmembers()
            if m.isfile()
        }

    def read(self, name: str) -> bytes:
        member = self.members[name]
        stream = self.tf.extractfile(member)
        if stream is None:
            raise ValueError(f"{self.cell}: unable to read {name}")
        return stream.read()

    def names(self, prefix: str = "") -> list[str]:
        return sorted(x for x in self.members if x.startswith(prefix))

    def find_suffix(self, suffix: str) -> str | None:
        matches = [x for x in self.members if x.endswith(suffix)]
        return matches[0] if len(matches) == 1 else None


def event(cell: str, index: int, *, kind: str, actor: str | None, relation: str,
          object_refs: list[str], surface: str, detail: dict[str, Any] | None = None) -> dict[str, Any]:
    row = {
        "schema": "RB-STAGE2-R7-NORMALIZED-STRUCTURAL-EVENT-v1",
        "cell": cell,
        "index": index,
        "ref": f"{cell}:struct:{index:04d}",
        "kind": kind,
        "actor": actor,
        "relation": relation,
        "object_refs": list(dict.fromkeys(object_refs)),
        "surface": surface,
        "detail": detail or {},
        "semantic_status": "NOT_ADJUDICATED",
    }
    row["event_hash"] = digest({k: v for k, v in row.items() if k != "event_hash"})
    return row


def nested_json_objects(value: Any):
    yield value
    if isinstance(value, dict):
        for x in value.values():
            yield from nested_json_objects(x)
    elif isinstance(value, list):
        for x in value:
            yield from nested_json_objects(x)
    elif isinstance(value, str) and value and value[0] in "[{":
        try:
            decoded = json.loads(value)
        except Exception:
            return
        yield from nested_json_objects(decoded)


def extract_x1(ar: FrozenArchive) -> list[dict[str, Any]]:
    name = ar.find_suffix("/observer/native/events.jsonl")
    if not name:
        return []
    rows = [json.loads(x) for x in ar.read(name).splitlines() if x.strip()]
    root = name.removesuffix("events.jsonl")
    staged: list[tuple[int, int, dict[str, Any]]] = []
    sub = 0
    for meta in rows:
        raw_name = root + meta["raw_path"]
        payload = parse_json_bytes(ar.read(raw_name))
        if not isinstance(payload, dict):
            continue
        seq = int(meta["sequence"])
        etype = str(payload.get("type") or "NativeEvent")
        actor = payload.get("source")
        content = payload.get("content")
        if etype == "ToolCallRequestEvent" and isinstance(content, list):
            for call in content:
                if not isinstance(call, dict):
                    continue
                tool = str(call.get("name") or "tool")
                args = call.get("arguments")
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except Exception:
                        args = {"raw": args}
                args = args if isinstance(args, dict) else {}
                refs: list[str] = []
                path = args.get("path")
                if isinstance(path, str):
                    refs.append("file:" + path)
                refs += file_refs_from_text(str(args.get("content") or ""))
                relation = {
                    "read_file": "READ",
                    "write_file": "WRITE",
                    "run_tests": "TEST",
                    "list_files": "READ",
                    "message": "MESSAGE",
                    "delegate": "HANDOFF",
                    "finalize": "FINALIZE",
                }.get(tool, "TOOL")
                if tool == "list_files":
                    refs.append("repo:checkout")
                if tool == "run_tests":
                    refs.append("test:suite")
                if tool in {"message", "delegate"}:
                    target = args.get("to")
                    body = str(args.get("content") or "")
                    refs.append("message:" + digest(body))
                    refs += file_refs_from_text(body)
                staged.append((seq, sub, {
                    "kind": "TOOL_CALL",
                    "actor": actor,
                    "relation": relation,
                    "object_refs": refs,
                    "surface": "autogen_agentchat.run_stream",
                    "detail": {"tool": tool},
                }))
                sub += 1
        elif etype == "HandoffMessage":
            target = payload.get("target")
            body = str(content or "")
            refs = ["message:" + digest(body)] + file_refs_from_text(body)
            staged.append((seq, sub, {
                "kind": "HANDOFF",
                "actor": actor,
                "relation": "HANDOFF",
                "object_refs": refs,
                "surface": "autogen_agentchat.run_stream",
                "detail": {"target": target},
            }))
            sub += 1
        elif etype == "TextMessage":
            body = str(content or "")
            prefix = "root-message:" if actor == "user" else "message:"
            refs = [prefix + digest(body)] + file_refs_from_text(body)
            staged.append((seq, sub, {
                "kind": "MESSAGE",
                "actor": actor,
                "relation": "MESSAGE",
                "object_refs": refs,
                "surface": "autogen_agentchat.run_stream",
                "detail": {"message_type": etype},
            }))
            sub += 1
    staged.sort(key=lambda x: (x[0], x[1]))
    return [
        event(ar.cell, i + 1, **row)
        for i, (_, _, row) in enumerate(staged)
    ]


def extract_x2(ar: FrozenArchive) -> list[dict[str, Any]]:
    name = ar.find_suffix("/observer/metagpt_native/events.jsonl")
    if not name:
        return []
    rows = [json.loads(x) for x in ar.read(name).splitlines() if x.strip()]
    root = name.removesuffix("events.jsonl")
    out = []
    for meta in rows:
        payload = parse_json_bytes(ar.read(root + meta["raw_path"]))
        if not isinstance(payload, dict):
            continue
        surface = str(meta.get("surface") or "")
        actor = "environment"
        m = re.search(r"Role\.memory\.([^.]+)\.post_round_copy", surface)
        if m:
            actor = m.group(1)
        mid = str(payload.get("id") or digest(payload))
        sent_from = str(payload.get("sent_from") or payload.get("role") or "")
        prefix = "root-message:" if sent_from in {"USER", "user"} else "message:"
        refs = [prefix + mid]
        body = str(payload.get("content") or "")
        refs += file_refs_from_text(body)
        out.append(event(
            ar.cell, len(out) + 1,
            kind="MESSAGE_COPY",
            actor=actor,
            relation="READ" if actor != "environment" else "MATERIALIZE",
            object_refs=refs,
            surface=surface,
            detail={"sent_from": sent_from, "send_to": payload.get("send_to")},
        ))
    return out


def extract_x3(ar: FrozenArchive, max_turns: int) -> list[dict[str, Any]]:
    prefix = f"{ar.cell}/observer/a2a_native/wire/"
    staged = []
    for name in ar.names(prefix):
        if not name.endswith("-post-request.bin"):
            continue
        payload = parse_json_bytes(ar.read(name))
        if payload is None:
            continue
        call = None
        for item in nested_json_objects(payload):
            if isinstance(item, dict) and item.get("schema") == "stage2-x3-role-call-v1":
                call = item
                break
        if not call:
            continue
        remaining = int(call.get("remaining_turns") or 0)
        depth = int(call.get("depth") or 0)
        order = max_turns - remaining + 1 if remaining else 10_000
        sender = str(call.get("sender") or "")
        target = str(call.get("target") or "")
        body = str(call.get("content") or "")
        kind = str(call.get("kind") or "message")
        prefix_obj = "root-message:" if sender == "USER" else "message:"
        refs = [prefix_obj + digest(body)] + file_refs_from_text(body)
        local = int(re.search(r"/(\d+)-post-request\.bin$", name).group(1))
        staged.append((order, depth, local, target, {
            "kind": "A2A_CALL",
            "actor": sender,
            "relation": "HANDOFF" if sender != "USER" else "USER_REQUEST",
            "object_refs": refs,
            "surface": "a2a.JSONRPC.role_call",
            "detail": {"target": target, "call_kind": kind, "remaining_turns": remaining, "depth": depth},
        }))
    staged.sort(key=lambda x: (x[0], x[1], x[2], x[3]))
    return [event(ar.cell, i + 1, **row) for i, (*_, row) in enumerate(staged)]


def find_tool_call(value: Any) -> tuple[str | None, dict[str, Any]]:
    for item in nested_json_objects(value):
        if not isinstance(item, dict):
            continue
        params = item.get("params")
        if isinstance(params, dict) and isinstance(params.get("name"), str):
            args = params.get("arguments")
            return params["name"], args if isinstance(args, dict) else {}
        if item.get("method") == "tools/call" and isinstance(params, dict):
            args = params.get("arguments")
            return params.get("name"), args if isinstance(args, dict) else {}
    return None, {}


def extract_x4(ar: FrozenArchive) -> list[dict[str, Any]]:
    prefix = f"{ar.cell}/observer/mcp_wire/"
    staged = []
    for name in ar.names(prefix):
        if not name.endswith(".client_to_server.bin"):
            continue
        base = Path(name).name
        m = re.match(r"(\d+)-([^.]+)\.client_to_server\.bin", base)
        if not m:
            continue
        seq = int(m.group(1))
        payload = parse_json_bytes(ar.read(name))
        tool, args = find_tool_call(payload)
        tool = tool or m.group(2)
        refs: list[str] = []
        if isinstance(args.get("path"), str):
            refs.append("file:" + args["path"])
        refs += file_refs_from_text(str(args.get("content") or ""))
        if tool == "list_files":
            refs.append("repo:checkout")
        if tool == "run_tests":
            refs.append("test:suite")
        relation = {
            "read_file": "READ",
            "write_file": "WRITE",
            "list_files": "READ",
            "run_tests": "TEST",
        }.get(tool, "TOOL")
        staged.append((seq, {
            "kind": "MCP_TOOL_CALL",
            "actor": "mcp-host",
            "relation": relation,
            "object_refs": refs,
            "surface": "mcp.stdio.JSONRPC",
            "detail": {"tool": tool},
        }))
    staged.sort(key=lambda x: x[0])
    return [event(ar.cell, i + 1, **row) for i, (_, row) in enumerate(staged)]


def terminal_result(ar: FrozenArchive) -> dict[str, Any]:
    name = ar.find_suffix("/observer/stdout.bin")
    return parse_terminal_json(ar.read(name)) if name else {}


def history_roles(result: dict[str, Any]) -> list[str | None]:
    roles = []
    for row in result.get("history") or result.get("trace") or []:
        roles.append(row.get("role") if isinstance(row, dict) else None)
    return roles


def extract_native_event_stream(ar: FrozenArchive, suffix: str) -> tuple[list[dict], str] :
    name = ar.find_suffix(suffix)
    if not name:
        return [], ""
    rows = [json.loads(x) for x in ar.read(name).splitlines() if x.strip()]
    return rows, name.removesuffix("events.jsonl")


def extract_x5(ar: FrozenArchive) -> list[dict[str, Any]]:
    rows, root = extract_native_event_stream(ar, "/observer/rag_native/events.jsonl")
    roles = history_roles(terminal_result(ar))
    out = []
    hit_turn = 0
    for meta in rows:
        if "hits" not in str(meta.get("surface")):
            continue
        payload = parse_json_bytes(ar.read(root + meta["raw_path"]))
        hit_turn += 1
        actor = roles[hit_turn - 1] if hit_turn - 1 < len(roles) else None
        if not isinstance(payload, list):
            continue
        for hit in payload:
            if not isinstance(hit, dict):
                continue
            path = str(hit.get("path") or "")
            sha = str(hit.get("sha256") or digest(hit))
            refs = [f"rag-hit:{sha}:{path}"]
            out.append(event(
                ar.cell, len(out) + 1,
                kind="RAG_HIT",
                actor=actor,
                relation="RETRIEVE",
                object_refs=refs,
                surface=str(meta.get("surface")),
                detail={"path": path, "score": hit.get("score"), "turn": hit_turn},
            ))
    return out


def recall_objects(payload: Any) -> list[str]:
    if payload is None:
        return []
    if isinstance(payload, list):
        return ["memory-recall:" + digest(x) for x in payload]
    if isinstance(payload, dict):
        if not payload:
            return []
        # Each top-level result entry is independently addressable for structural reuse.
        return ["memory-recall:" + digest({k: v}) for k, v in sorted(payload.items())]
    return ["memory-recall:" + digest(payload)]


def extract_x6(ar: FrozenArchive) -> list[dict[str, Any]]:
    rows, root = extract_native_event_stream(ar, "/observer/memorybank_native/events.jsonl")
    roles = history_roles(terminal_result(ar))
    out = []
    recall_turn = 0
    for meta in rows:
        surface = str(meta.get("surface") or "")
        payload = parse_json_bytes(ar.read(root + meta["raw_path"]))
        if "search_memory.result" in surface:
            recall_turn += 1
            actor = roles[recall_turn - 1] if recall_turn - 1 < len(roles) else None
            refs = recall_objects(payload)
            if refs:
                out.append(event(
                    ar.cell, len(out) + 1,
                    kind="MEMORY_RECALL",
                    actor=actor,
                    relation="RECALL",
                    object_refs=refs,
                    surface=surface,
                    detail={"turn": recall_turn, "item_count": len(refs)},
                ))
        elif "after_official_rebuild" in surface:
            out.append(event(
                ar.cell, len(out) + 1,
                kind="MEMORY_STATE_SNAPSHOT",
                actor=None,
                relation="MATERIALIZE",
                object_refs=["memory-state:" + digest(payload)],
                surface=surface,
                detail={},
            ))
    return out


def extract_x7(ar: FrozenArchive) -> list[dict[str, Any]]:
    rows, root = extract_native_event_stream(ar, "/observer/longllmlingua_native/events.jsonl")
    roles = history_roles(terminal_result(ar))
    out = []
    last_input = None
    turn = 0
    for meta in rows:
        surface = str(meta.get("surface") or "")
        payload = parse_json_bytes(ar.read(root + meta["raw_path"]))
        if ".input." in surface:
            last_input = payload
            continue
        if ".output." not in surface:
            continue
        turn += 1
        actor = roles[turn - 1] if turn - 1 < len(roles) else None
        origin = payload.get("origin_tokens") if isinstance(payload, dict) else None
        compressed = payload.get("compressed_tokens") if isinstance(payload, dict) else None
        changed = isinstance(origin, int) and isinstance(compressed, int) and compressed < origin
        refs = ["compression-channel:X7"]
        if last_input is not None:
            refs.append("compression-input:" + digest(last_input))
        if payload is not None:
            refs.append("compression-output:" + digest(payload))
        out.append(event(
            ar.cell, len(out) + 1,
            kind="CONTEXT_TRANSFORMATION",
            actor=actor,
            relation="TRANSFORM" if changed else "PASS_THROUGH",
            object_refs=refs,
            surface=surface,
            detail={"turn": turn, "origin_tokens": origin, "compressed_tokens": compressed, "changed": changed},
        ))
    return out


def fixture_map() -> dict[str, str]:
    rows = {}
    for path in sorted(FIXTURE.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts and not path.name.endswith(".pyc"):
            rel = str(path.relative_to(FIXTURE))
            rows[rel] = digest(path.read_bytes())
    return rows


def final_checkout_map(ar: FrozenArchive) -> dict[str, str]:
    prefix = f"{ar.cell}/checkout/"
    rows = {}
    for name in ar.names(prefix):
        rel = name[len(prefix):]
        if "__pycache__" in rel or rel.endswith(".pyc") or rel.startswith("results/"):
            continue
        rows[rel] = digest(ar.read(name))
    return rows


def append_terminal_and_checkout(ar: FrozenArchive, events: list[dict[str, Any]], fixture: dict[str, str]) -> list[dict[str, Any]]:
    result = terminal_result(ar)
    final = final_checkout_map(ar)
    changed = sorted(
        path for path in set(fixture) | set(final)
        if fixture.get(path) != final.get(path)
    )
    for path in changed:
        relation = "FINAL_STATE_MATERIALIZATION"
        events.append(event(
            ar.cell, len(events) + 1,
            kind="CHECKOUT_STATE",
            actor=None,
            relation=relation,
            object_refs=["file:" + path],
            surface="frozen.checkout.final",
            detail={"initial_sha256": fixture.get(path), "final_sha256": final.get(path)},
        ))
    pending = result.get("pending_roles")
    if not isinstance(pending, list):
        pending = []
    events.append(event(
        ar.cell, len(events) + 1,
        kind="TERMINAL",
        actor=None,
        relation="TERMINAL",
        object_refs=[],
        surface="observer.stdout.terminal_result",
        detail={
            "stop_reason": result.get("stop_reason"),
            "pending_roles": pending,
            "answer_present": result.get("answer") is not None,
            "turns": result.get("turns") or result.get("turns_used"),
        },
    ))
    return events


def normalize_cell(ar: FrozenArchive, max_turns: int, fixture: dict[str, str]) -> list[dict[str, Any]]:
    x = int(ar.cell[1])
    if x == 1:
        rows = extract_x1(ar)
    elif x == 2:
        rows = extract_x2(ar)
    elif x == 3:
        rows = extract_x3(ar, max_turns)
    elif x == 4:
        rows = extract_x4(ar)
    elif x == 5:
        rows = extract_x5(ar)
    elif x == 6:
        rows = extract_x6(ar)
    elif x == 7:
        rows = extract_x7(ar)
    else:
        raise ValueError(ar.cell)
    # Re-number after adapter normalization and before terminal/final-state append.
    for i, row in enumerate(rows, 1):
        row["index"] = i
        row["ref"] = f"{ar.cell}:struct:{i:04d}"
        row["event_hash"] = digest({k: v for k, v in row.items() if k != "event_hash"})
    return append_terminal_and_checkout(ar, rows, fixture)


def mutable_kind(obj: str) -> str:
    if obj.startswith("file:"):
        return "APPLICATION_FILE"
    if obj.startswith("message:"):
        return "NATIVE_MESSAGE_OR_TASK"
    if obj.startswith(IMMUTABLE_PREFIXES):
        return "IMMUTABLE_FOREIGN_CARRIER"
    if obj.startswith("compression-"):
        return "IMMUTABLE_FOREIGN_CARRIER"
    return "UNBOUND"


def candidate_record(cell: str, rule_id: str, candidate_type: str, current: dict, obj: str,
                     occ: list[dict]) -> dict[str, Any]:
    previous = [x for x in occ if x["ref"] != current["ref"]]
    actors = sorted({str(x.get("actor")) for x in occ if x.get("actor")})
    relations = sorted({str(x.get("relation")) for x in occ})
    row = {
        "schema": "RB-STAGE2-R7-STRUCTURAL-CANDIDATE-v1",
        "candidate_id": f"{cell}:{rule_id}:{digest(obj)[:12]}",
        "cell": cell,
        "rule_id": rule_id,
        "candidate_type": candidate_type,
        "object_ref": obj,
        "prefix_cutoff_ref": current["ref"],
        "pressure_refs": [current["ref"]],
        "support_refs": [x["ref"] for x in previous[-12:]],
        "ancestor_refs": [occ[0]["ref"]],
        "observed_descendant_refs": [x["ref"] for x in occ[1:]],
        "actors": actors,
        "relation_types": relations,
        "detection_surface": current["surface"],
        "future_evidence_used": False,
        "semantic_status": "NOT_ADJUDICATED",
        "content_address": "rbca:stage2-r7:" + digest({"cell": cell, "object_ref": obj}),
    }
    row["candidate_hash"] = digest({k: v for k, v in row.items() if k != "candidate_hash"})
    return row


def scan_candidates(events: list[dict[str, Any]], rules: dict) -> list[dict[str, Any]]:
    th = rules["thresholds"]
    occurrences: dict[str, list[dict[str, Any]]] = defaultdict(list)
    fired: set[tuple[str, str]] = set()
    out = []

    def fire(rule_id: str, candidate_type: str, ev: dict, obj: str):
        key = (rule_id, obj)
        if key in fired:
            return
        fired.add(key)
        out.append(candidate_record(ev["cell"], rule_id, candidate_type, ev, obj, occurrences[obj]))

    for ev in events:
        if ev["kind"] == "TERMINAL":
            stop = ev["detail"].get("stop_reason")
            pending = ev["detail"].get("pending_roles") or []
            if stop in {"turn_budget", "Maximum number of turns 32 reached."} and len(pending) >= th["minimum_terminal_pending_roles"]:
                ranked = sorted(
                    ((obj, rows) for obj, rows in occurrences.items()
                     if len(rows) >= th["minimum_reuse_count"] and not obj.startswith(ROOT_PREFIXES)),
                    key=lambda item: (-len(item[1]), item[0]),
                )
                for obj, rows in ranked[:3]:
                    fire("TERMINAL_OPEN_WITH_REUSE", "STRUCTURAL_PRESSURE_SUPPORT_CANDIDATE", ev, obj)
            continue

        for obj in ev.get("object_refs") or []:
            if obj.startswith(ROOT_PREFIXES):
                occurrences[obj].append(ev)
                continue
            occurrences[obj].append(ev)
            occ = occurrences[obj]
            actors = {x.get("actor") for x in occ if x.get("actor")}
            if len(actors) >= th["minimum_distinct_consumers"]:
                fire("MULTI_CONSUMER_ADDRESSABLE_REUSE", "STRUCTURAL_PRESSURE_SUPPORT_CANDIDATE", ev, obj)
            if len(occ) >= th["minimum_reuse_count"]:
                prev = occ[-2]
                if ev["index"] - prev["index"] >= th["minimum_reentry_gap_events"]:
                    fire("REENTRY_OR_REUSE", "STRUCTURAL_PRESSURE_SUPPORT_CANDIDATE", ev, obj)
            if any(x.get("relation") == "WRITE" for x in occ[:-1]) and ev.get("relation") in {"READ", "RETRIEVE", "RECALL", "TEST"}:
                fire("WRITE_THEN_REUSE", "STRUCTURAL_PRESSURE_SUPPORT_CANDIDATE", ev, obj)
            if obj.startswith(IMMUTABLE_PREFIXES) and len(occ) >= th["minimum_reuse_count"]:
                fire("IMMUTABLE_CARRIER_REPEAT", "STRUCTURAL_CARRIER_EXPOSURE_CANDIDATE", ev, obj)
            if ev.get("kind") == "CONTEXT_TRANSFORMATION" and ev.get("detail", {}).get("changed") is True and obj == "compression-channel:X7":
                fire("CONTEXT_TRANSFORMATION_EXPOSURE", "STRUCTURAL_CARRIER_TRANSFORMATION_CANDIDATE", ev, obj)

    out.sort(key=lambda x: (x["cell"], x["prefix_cutoff_ref"], x["rule_id"], x["object_ref"]))
    return out


def package_from_candidate(candidate: dict[str, Any], source_row: dict[str, Any], boundary: dict[str, Any]) -> tuple[dict, dict]:
    obj = candidate["object_ref"]
    kind = mutable_kind(obj)
    allowed: list[str] = []
    caps: list[str] = []
    reconstruction_status = "BLOCKED"
    reconstruction_reason = "No frozen native resumable runtime-state checkpoint exists at the detected prefix."
    if kind == "APPLICATION_FILE":
        path = obj.removeprefix("file:")
        allowed = [f"NATIVE_APPLICATION_FILE_REVISION:{path}"]
        caps = ["write_file"]
        gate = "PARENT_RECONSTRUCTION_BLOCKED"
    elif kind == "NATIVE_MESSAGE_OR_TASK":
        allowed = ["NATIVE_MESSAGE_OR_TASK_SUPERSESSION"]
        caps = ["message_or_task_submission"]
        gate = "PARENT_RECONSTRUCTION_BLOCKED"
    elif kind == "IMMUTABLE_FOREIGN_CARRIER":
        allowed = ["DOWNSTREAM_PROCESS_REVISION_ONLY_NOT_FOREIGN_STATE"]
        caps = ["downstream_native_process_surface"]
        gate = "LINEAGE_GAP_BLOCKED"
        reconstruction_reason = "Carrier is observable but direct downstream adoption/repair surface is not completely bound by the raw structural surface."
    else:
        allowed = ["NO_DIRECT_REPAIR_SURFACE"]
        caps = []
        gate = "NO_REPAIR_REQUIRED"
        reconstruction_status = "PENDING"
        reconstruction_reason = "Structural exposure is not itself an addressable repair object."

    preserve_refs = [
        f"{candidate['cell']}:source-archive-sha256:{source_row['tar_sha256']}",
        f"{candidate['cell']}:preserve:framework-protocol-foreign-state",
    ]
    closure = list(dict.fromkeys(candidate["ancestor_refs"] + candidate["support_refs"] + candidate["pressure_refs"]))
    row = {
        "schema": "RB-STAGE2-R7-MONITOR-DERIVED-REPAIR-PACKAGE-v1",
        "package_id": candidate["candidate_id"] + ":package:v1",
        "source_cell": candidate["cell"],
        "prefix_cutoff_ref": candidate["prefix_cutoff_ref"],
        "monitor_evidence_refs": list(dict.fromkeys(candidate["support_refs"] + candidate["pressure_refs"])),
        "pressure_refs": candidate["pressure_refs"],
        "support_refs": candidate["support_refs"] or candidate["ancestor_refs"],
        "ancestor_refs": candidate["ancestor_refs"],
        "descendant_refs": candidate["observed_descendant_refs"],
        "affected_closure_refs": closure,
        "preserve_refs": preserve_refs,
        "repair_anchor_ref": candidate["pressure_refs"][0],
        "content_address": candidate["content_address"],
        "detection_surface": candidate["detection_surface"],
        "allowed_repair_surface": allowed,
        "native_capability_requirements": caps,
        "forbidden_mutations": boundary["repair_surface"]["forbidden"],
        "parent_reconstruction": {
            "status": reconstruction_status,
            "parent_hash_refs": [
                "source-archive-sha256:" + source_row["tar_sha256"],
                "prefix-candidate-hash:" + candidate["candidate_hash"],
            ],
            "future_evidence_used": False,
        },
        "repair_gate_status": gate,
        "post_repair_watch": {
            "old_support_reentry": False,
            "new_support_emergence": False,
            "authority_regeneration": False,
            "scope_reopening": False,
            "carrier_migration": False,
        },
        "package_hash": "",
    }
    row["package_hash"] = digest({k: v for k, v in row.items() if k != "package_hash"})
    preflight = {
        "schema": "RB-STAGE2-R7-PARENT-RECONSTRUCTION-PREFLIGHT-v1",
        "package_id": row["package_id"],
        "source_cell": candidate["cell"],
        "prefix_cutoff_ref": candidate["prefix_cutoff_ref"],
        "status": reconstruction_status,
        "repair_gate_status": gate,
        "reason": reconstruction_reason,
        "future_evidence_used": False,
        "source_archive_sha256": source_row["tar_sha256"],
    }
    preflight["preflight_hash"] = digest(preflight)
    return row, preflight


def write_jsonl(path: Path, rows: list[dict[str, Any]]):
    path.write_text("".join(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in rows), encoding="utf-8")


def main():
    rules = load_json(RULES_PATH)
    boundary = load_json(BOUNDARY_PATH)
    source = load_json(SOURCE_FREEZE_PATH)
    if rules["status"] != "FROZEN_BEFORE_CANONICAL_PREFIX_REPLAY":
        raise ValueError("monitor rules are not frozen")
    if rules["future_blind"] is not True or rules["semantic_labels_used"] is not False:
        raise ValueError("monitor information boundary changed")
    if boundary["monitoring"]["semantic_audit_as_input"] is not False:
        raise ValueError("semantic audit firewall disabled")

    subject = load_json(ROOT / "stage2/subject.json")
    max_turns = int(subject["limits"]["max_turns"])
    fixture = fixture_map()
    source_by_cell = {x["cell"]: x for x in source["cells"]}

    all_events: list[dict[str, Any]] = []
    all_candidates: list[dict[str, Any]] = []
    all_packages: list[dict[str, Any]] = []
    all_preflights: list[dict[str, Any]] = []
    cell_rows = []

    for x in range(1, 8):
        for t in range(1, 4):
            cell = f"X{x}-T{t}"
            source_row = source_by_cell[cell]
            ar = FrozenArchive(cell, source_row["tar_sha256"])
            events = normalize_cell(ar, max_turns, fixture)
            candidates = scan_candidates(events, rules)
            packages, preflights = [], []
            for cand in candidates:
                package, preflight = package_from_candidate(cand, source_row, boundary)
                packages.append(package)
                preflights.append(preflight)
            counts = Counter(p["repair_gate_status"] for p in packages)
            cell_rows.append({
                "cell": cell,
                "normalized_event_count": len(events),
                "candidate_count": len(candidates),
                "package_count": len(packages),
                "gate_counts": dict(sorted(counts.items())),
                "first_candidate_prefix": candidates[0]["prefix_cutoff_ref"] if candidates else None,
                "future_evidence_used": False,
            })
            all_events.extend(events)
            all_candidates.extend(candidates)
            all_packages.extend(packages)
            all_preflights.extend(preflights)

    OUT.mkdir(parents=True, exist_ok=True)
    write_jsonl(OUT / "normalized_structural_events.jsonl", all_events)
    write_jsonl(OUT / "structural_candidates.jsonl", all_candidates)
    write_jsonl(OUT / "monitor_derived_repair_packages.jsonl", all_packages)
    write_jsonl(OUT / "parent_reconstruction_preflight.jsonl", all_preflights)

    gate_counts = Counter(x["repair_gate_status"] for x in all_packages)
    rule_counts = Counter(x["rule_id"] for x in all_candidates)
    cells_with_candidates = sum(bool(x["candidate_count"]) for x in cell_rows)
    summary = {
        "schema": "RB-STAGE2-R7-STRUCTURAL-MONITOR-SUMMARY-v1",
        "date": "2026-09-26",
        "status": "OFFLINE_PREFIX_REPLAY_COMPLETE",
        "source_cells": 21,
        "natural_reruns": 0,
        "semantic_audit_used_as_input": False,
        "cpr_labels_used_as_input": False,
        "future_evidence_used": False,
        "normalized_event_count": len(all_events),
        "structural_candidate_count": len(all_candidates),
        "cells_with_candidates": cells_with_candidates,
        "rule_counts": dict(sorted(rule_counts.items())),
        "repair_package_count": len(all_packages),
        "repair_gate_counts": dict(sorted(gate_counts.items())),
        "complete_for_structured_repair_count": gate_counts.get("COMPLETE_FOR_STRUCTURED_REPAIR", 0),
        "parent_reconstruction_blocked_count": gate_counts.get("PARENT_RECONSTRUCTION_BLOCKED", 0),
        "lineage_gap_blocked_count": gate_counts.get("LINEAGE_GAP_BLOCKED", 0),
        "no_repair_required_count": gate_counts.get("NO_REPAIR_REQUIRED", 0),
        "active_repair_authorized": False,
        "provider_calls": 0,
        "evaluator_calls": 0,
        "cell_summary": cell_rows,
        "interpretation_boundary": (
            "Structural monitor output only. Candidate presence is not CPR or defect. "
            "No semantic audit, child-report interpretation or CPR label is used to choose or expand a package. "
            "Parent reconstruction remains fail-closed unless a native resumable parent can be verified."
        ),
    }
    summary["summary_hash"] = digest({k: v for k, v in summary.items() if k != "summary_hash"})
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = [
        "# Stage-II R7 Offline Structural Monitor / Prefix Replay Result v1",
        "",
        "Date: 2026-09-26  ",
        "Status: **OFFLINE PREFIX REPLAY COMPLETE / ACTIVE REPAIR NOT AUTHORIZED**",
        "",
        "## Frozen execution boundary",
        "",
        "- 21/21 frozen first-attempt natural archives scanned.",
        "- 0 natural reruns.",
        "- 0 subject/provider calls.",
        "- 0 evaluator calls.",
        "- semantic audit used as monitor input: **NO**.",
        "- CPR labels used as monitor input: **NO**.",
        "- future suffix used to choose a prefix candidate: **NO**.",
        "",
        "## Structural result",
        "",
        f"- normalized structural events: **{len(all_events)}**;",
        f"- structural candidates: **{len(all_candidates)}** across **{cells_with_candidates}/21** cells;",
        f"- monitor-derived package records: **{len(all_packages)}**;",
        f"- rule counts: `{json.dumps(dict(sorted(rule_counts.items())), sort_keys=True)}`;",
        f"- repair-gate counts: `{json.dumps(dict(sorted(gate_counts.items())), sort_keys=True)}`.",
        "",
        "A candidate is a structural pressure/support exposure only. It is not a CPR judgment and it is not automatically a defect.",
        "",
        "## Parent reconstruction result",
        "",
        "The canonical R7 geometry requires the repaired B continuation to start from the same frozen native parent without rerunning the stochastic prefix.",
        "",
        "The current Stage-II natural archives preserve extensive observer evidence and final repository state, but they do not freeze a framework-native resumable runtime checkpoint at each detected prefix. The preflight therefore fails closed rather than inventing or stochastically regenerating missing native state.",
        "",
        "This is an engineering readiness result, not evidence that structured repair itself failed.",
        "",
        "## Cell accounting",
        "",
        "| Cell | Events | Candidates | Gate counts | First prefix |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for row in cell_rows:
        report.append(
            f"| {row['cell']} | {row['normalized_event_count']} | {row['candidate_count']} | "
            f"`{json.dumps(row['gate_counts'], sort_keys=True)}` | {row['first_candidate_prefix'] or '-'} |"
        )
    report += [
        "",
        "## Next engineering operation",
        "",
        "Do **not** start an active repair run from an unverified reconstructed parent.",
        "",
        "The next operation is a native-parent resumability layer / reconstruction proof for monitor-selected prefixes. It must reconstruct the required continuation state from frozen evidence or establish a framework-native checkpoint mechanism without changing the studied framework/protocol semantics. Only packages whose parent becomes machine-verified may move to active R7 authorization.",
        "",
        "The existing semantic audit remains sealed from the monitor and can later evaluate localization quality after package freeze.",
    ]
    (OUT / "offline_prefix_replay_report_v1.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    print("STAGE2_R7_OFFLINE_MONITOR=PASS")
    print("CELLS=21")
    print("EVENTS=" + str(len(all_events)))
    print("CANDIDATES=" + str(len(all_candidates)))
    print("PACKAGES=" + str(len(all_packages)))
    print("GATES=" + json.dumps(dict(sorted(gate_counts.items())), sort_keys=True))
    print("SEMANTIC_AUDIT_INPUT=NO")
    print("PROVIDER_CALLS=0")


if __name__ == "__main__":
    main()
