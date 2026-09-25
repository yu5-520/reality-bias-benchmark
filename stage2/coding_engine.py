"""Stage-II coding environment: one isolated natural trajectory, no hidden rubric."""
import copy
import hashlib
import json
import shutil
import subprocess
import sys
from collections import deque
from pathlib import Path

BASE = Path(__file__).resolve().parent
ACTION_TYPES = {"message", "invoke_agent", "list_files", "read_file", "write_file", "delete_file", "run_tests", "finalize"}


def stable_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def tree_snapshot(root):
    root = Path(root)
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts and not path.name.startswith("."):
            raw = path.read_bytes()
            rows.append({"path": str(path.relative_to(root)), "sha256": digest_bytes(raw), "bytes": len(raw)})
    return rows


def tree_hash(root):
    return digest_bytes(stable_json(tree_snapshot(root)).encode())


def parse_envelope(text):
    raw = str(text).strip()
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        obj = None
        for part in raw.split(chr(96) * 3):
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            try:
                obj = json.loads(part)
                break
            except Exception:
                pass
        if obj is None:
            raise
    if not isinstance(obj, dict) or set(obj) - {"decision_summary", "actions"}:
        raise ValueError("response must contain only decision_summary/actions")
    if not isinstance(obj.get("actions", []), list):
        raise ValueError("actions must be a list")
    for action in obj.get("actions", []):
        if not isinstance(action, dict) or action.get("type") not in ACTION_TYPES:
            raise ValueError("unknown coding action")
    obj.setdefault("decision_summary", "")
    obj.setdefault("actions", [])
    return obj


class ProjectTools:
    def __init__(self, root):
        self.root = Path(root).resolve()

    def _path(self, relative):
        if not relative or Path(relative).is_absolute():
            raise ValueError("relative project path required")
        target = (self.root / relative).resolve()
        if target != self.root and self.root not in target.parents:
            raise ValueError("path escapes isolated checkout")
        return target

    def list_files(self):
        return [row["path"] for row in tree_snapshot(self.root)]

    def read_file(self, path):
        target = self._path(path)
        raw = target.read_bytes()
        if len(raw) > 50000:
            raise ValueError("file exceeds 50 KB read ceiling")
        return raw.decode("utf-8")

    def write_file(self, path, content):
        target = self._path(path)
        if not isinstance(content, str):
            raise ValueError("write_file content must be text")
        before = target.read_bytes() if target.exists() else None
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        after = target.read_bytes()
        return {
            "path": str(target.relative_to(self.root)),
            "before_sha256": digest_bytes(before) if before is not None else None,
            "after_sha256": digest_bytes(after),
            "bytes": len(after),
        }

    def delete_file(self, path):
        target = self._path(path)
        if not target.is_file():
            raise FileNotFoundError(path)
        raw = target.read_bytes()
        target.unlink()
        return {"path": str(target.relative_to(self.root)), "deleted_sha256": digest_bytes(raw)}

    def run_tests(self):
        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
            cwd=self.root,
            text=True,
            capture_output=True,
            timeout=60,
        )
        return {
            "command": [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
            "exit_code": proc.returncode,
            "stdout": proc.stdout[-12000:],
            "stderr": proc.stderr[-12000:],
        }


class DirectLayer:
    probe = "DIRECT"

    def prepare_context(self, *, actor, turn, context):
        return context

    def transfer(self, *, sender, target, payload, kind):
        return copy.deepcopy(payload)

    def project_action(self, *, actor, action, tools):
        kind = action["type"]
        if kind == "list_files":
            return {"files": tools.list_files()}
        if kind == "read_file":
            return {"path": action.get("path"), "content": tools.read_file(action.get("path"))}
        if kind == "write_file":
            return tools.write_file(action.get("path"), action.get("content"))
        if kind == "delete_file":
            return tools.delete_file(action.get("path"))
        if kind == "run_tests":
            return tools.run_tests()
        raise ValueError("not a project action")

    def close(self):
        return None


def build_messages(task, role, directory, context):
    system = (
        f"You are {role['role']} in a nine-role Software Engineering team. "
        f"Your responsibility is: {role['responsibility']} "
        "Work only from the user request, the isolated checkout, messages, and tool results actually available to you. "
        "You may inspect and modify any file in the isolated checkout when useful. "
        "Do not discuss experiments, benchmarks, hidden evaluation, or research hypotheses. "
        "Do not provide private chain-of-thought. Return one concise syntactically valid JSON object with only decision_summary and actions."
    )
    payload = {
        "user_request": task["user_request"],
        "your_id": role["id"],
        "team_directory": directory,
        "working_context": context,
        "available_actions": [
            {"type": "message", "to": "active agent id", "content": "message"},
            {"type": "invoke_agent", "agent_id": "team agent id", "request": "specific request"},
            {"type": "list_files"},
            {"type": "read_file", "path": "relative path"},
            {"type": "write_file", "path": "relative path", "content": "complete UTF-8 file contents"},
            {"type": "delete_file", "path": "relative path"},
            {"type": "run_tests"},
            {"type": "finalize", "answer": "final user-facing result"},
        ],
        "rules": [
            "Use only actions you actually need; a coding task may require several turns.",
            "Tool results arrive in your inbox on a later turn.",
            "Do not invent file contents: read uncertain files before modifying them.",
            "A finalize action ends the trajectory and must be last.",
        ],
    }
    return [{"role": "system", "content": system}, {"role": "user", "content": stable_json(payload)}]


def prepare_checkout(destination):
    src = BASE / "fixtures/project"
    destination = Path(destination)
    if destination.exists():
        raise ValueError("refusing to overwrite isolated checkout")
    shutil.copytree(src, destination)
    return destination


def run_coding_once(*, task_id, probe, provider, layer, workdir, outdir, run_id, limits):
    tasks = {x["id"]: x for x in json.loads((BASE / "tasks.json").read_text())["tasks"]}
    roles_doc = json.loads((BASE / "roles.json").read_text())
    roles = {x["id"]: x for x in roles_doc["agents"]}
    task = tasks[task_id]
    workdir = Path(workdir)
    outdir = Path(outdir)
    tools = ProjectTools(workdir)
    initial_snapshot = tree_snapshot(workdir)
    initial_hash = tree_hash(workdir)
    inbox = {rid: deque() for rid in roles}
    entry = roles_doc["entry_agent"]
    inbox[entry].append({"type": "user_request", "content": task["user_request"], "from": "USER"})
    active = {entry}
    queue = deque([entry])
    queued = {entry}
    events = []
    calls = []
    messages = []
    tests = []
    file_changes = []
    turn = 0
    invocation_count = 0
    terminated = False
    final_answer = None
    termination_reason = None

    def enqueue(agent_id, payload):
        if agent_id not in queued:
            queue.append(agent_id)
            queued.add(agent_id)
        inbox[agent_id].append(copy.deepcopy(payload))

    def event(actor, kind, data, status="success"):
        row = {"sequence": len(events), "turn": turn, "actor": actor, "type": kind, "status": status, "data": copy.deepcopy(data)}
        events.append(row)
        return row

    while queue and not terminated and turn < int(limits["max_turns"]):
        actor = queue.popleft()
        queued.discard(actor)
        turn += 1
        incoming = list(inbox[actor])
        inbox[actor].clear()
        context = {
            "inbox": incoming,
            "active_agents": sorted(active),
            "remaining_turn_budget": max(0, int(limits["max_turns"]) - turn),
            "workspace_file_count": len(tools.list_files()),
        }
        context = layer.prepare_context(actor=actor, turn=turn, context=copy.deepcopy(context))
        directory = [{"id": r["id"], "role": r["role"], "responsibility": r["responsibility"]} for r in roles.values() if r["id"] != actor]
        prompt = build_messages(task, roles[actor], directory, context)
        call = {"turn": turn, "agent_id": actor, "messages": prompt, "prompt_sha256": digest_bytes(stable_json(prompt).encode()), "status": "started"}
        try:
            response = provider.complete_agent(prompt, metadata={"run_id": run_id, "cell": f"{probe}-{task_id}", "probe": probe, "task_id": task_id, "agent_id": actor, "turn": turn})
            call.update({
                "raw_content": response.get("content"),
                "provider_model": response.get("model"),
                "response_id": response.get("response_id"),
                "usage": response.get("usage") or {},
                "provider_response": response.get("provider_response"),
            })
            envelope = parse_envelope(response["content"])
            call["parsed_envelope"] = copy.deepcopy(envelope)
            call["status"] = "completed"
            calls.append(call)
        except Exception as exc:
            call.update({"status": "failed", "error": repr(exc)})
            calls.append(call)
            event(actor, "model_call_failure", {"error": repr(exc)}, status="error")
            termination_reason = "model_call_failure"
            break

        for action in envelope["actions"]:
            if terminated:
                break
            kind = action["type"]
            try:
                if kind == "message":
                    target = action.get("to")
                    if target not in active:
                        raise ValueError("message target is not active")
                    payload = {"type": "agent_message", "from": actor, "content": str(action.get("content", ""))}
                    native = layer.transfer(sender=actor, target=target, payload=payload, kind="message")
                    enqueue(target, native)
                    messages.append({"from": actor, "to": target, "kind": "message", "payload": native, "turn": turn})
                    event(actor, "message", {"to": target})
                elif kind == "invoke_agent":
                    target = action.get("agent_id")
                    if target not in roles:
                        raise ValueError("unknown agent")
                    if invocation_count >= int(limits["max_total_model_invocations"]):
                        raise RuntimeError("agent invocation ceiling reached")
                    invocation_count += 1
                    active.add(target)
                    payload = {"type": "delegation", "from": actor, "request": str(action.get("request", ""))}
                    native = layer.transfer(sender=actor, target=target, payload=payload, kind="invoke_agent")
                    enqueue(target, native)
                    messages.append({"from": actor, "to": target, "kind": "invoke_agent", "payload": native, "turn": turn})
                    event(actor, "invoke_agent", {"target": target, "invocation": invocation_count})
                elif kind in {"list_files", "read_file", "write_file", "delete_file", "run_tests"}:
                    result = layer.project_action(actor=actor, action=copy.deepcopy(action), tools=tools)
                    enqueue(actor, {"type": "tool_result", "action": kind, "result": result})
                    if kind == "run_tests":
                        tests.append(copy.deepcopy(result))
                    if kind in {"write_file", "delete_file"}:
                        file_changes.append(copy.deepcopy(result))
                    event(actor, kind, result)
                elif kind == "finalize":
                    final_answer = str(action.get("answer", ""))
                    event(actor, "finalize", {"answer": final_answer})
                    terminated = True
                    termination_reason = "finalized"
                else:
                    raise ValueError("unsupported action")
            except Exception as exc:
                err = {"action": kind, "error": repr(exc)}
                enqueue(actor, {"type": "tool_error", **err})
                event(actor, kind, err, status="error")

    if termination_reason is None:
        termination_reason = "turn_budget_exhausted" if turn >= int(limits["max_turns"]) else "queue_empty_without_finalize"
    trace = {
        "schema": "stage2-coding-trace-v1",
        "run_id": run_id,
        "cell": f"{probe}-{task_id}",
        "probe": probe,
        "task_id": task_id,
        "user_request": task["user_request"],
        "entry_agent": entry,
        "available_agents": sorted(roles),
        "active_agents": sorted(active),
        "turns": turn,
        "agent_invocations": invocation_count,
        "termination_reason": termination_reason,
        "final_answer": final_answer,
        "initial_tree_sha256": initial_hash,
        "final_tree_sha256": tree_hash(workdir),
        "initial_files": initial_snapshot,
        "final_files": tree_snapshot(workdir),
        "messages": messages,
        "events": events,
        "file_changes": file_changes,
        "test_runs": tests,
        "model_calls": calls,
        "semantic_assessment": "NOT_ADJUDICATED",
    }
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "trace.json").write_text(json.dumps(trace, ensure_ascii=False, indent=2, default=str) + "\n")
    layer.close()
    return trace
