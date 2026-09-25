"""Native-boundary capture contract. No structural event makes a semantic claim."""
import hashlib
import json
from pathlib import Path

OPERATIONS = frozenset({
    "send_message", "receive_message", "shared_state", "delegate", "handoff",
    "tool_call", "resource_read", "memory_write", "memory_retrieve",
    "remote_task", "artifact_return", "retrieve", "compress",
    "file_change", "test_run", "termination",
})
PROBES = {
    "X1": {"send_message", "receive_message", "delegate", "handoff"},
    "X2": {"send_message", "receive_message", "shared_state", "delegate", "handoff"},
    "X3": {"send_message", "receive_message", "remote_task", "artifact_return"},
    "X4": {"send_message", "receive_message", "tool_call", "resource_read"},
    "X5": {"send_message", "receive_message", "retrieve"},
    "X6": {"send_message", "receive_message", "memory_write", "memory_retrieve"},
    "X7": {"send_message", "receive_message", "compress"},
}
COMMON = {"file_change", "test_run", "termination"}
PHASES = frozenset({"emitted", "delivered", "exposed", "executed", "returned", "failed"})


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


class NativeCapture:
    """Only called by an instrumented native boundary; never by an R6 auditor.

    `raw` is the original provider/framework payload as bytes. A JSON serialization
    of the already translated common event is NOT acceptable native evidence.
    `native_locator` and `hook_id` identify a concrete native log/hook location.
    """

    def __init__(self, root, probe, run_id, binding):
        if probe not in PROBES:
            raise ValueError("unknown frozen probe")
        if binding.get("probe") != probe or not binding.get("source_commit"):
            raise ValueError("native implementation binding is required")
        self.root = Path(root)
        self.probe = probe
        self.run_id = run_id
        self.binding = binding
        self.events = []
        self.ids = set()

    def capture(self, *, event_id, operation, phase, native_locator, hook_id,
                raw, actor, carrier_id, source_id, parent_ids=(), target=None,
                carrier_type=None, status=None):
        if operation not in PROBES[self.probe] | COMMON or operation not in OPERATIONS:
            raise ValueError("operation unavailable at this probe boundary")
        if phase not in PHASES:
            raise ValueError("invalid boundary phase")
        if not isinstance(raw, bytes) or not raw or not all((event_id, native_locator, hook_id, actor, carrier_id, source_id)):
            raise ValueError("missing raw bytes or addressable native locator/source/carrier")
        if event_id in self.ids or any(parent not in self.ids for parent in parent_ids):
            raise ValueError("duplicate event or dangling/forward lineage reference")
        if status not in (None, "success", "error", "censored", "blocked"):
            raise ValueError("invalid execution status")
        # Semantic authority, C/P/R, downstream adoption and inferred use are
        # deliberately absent; R6 must adjudicate those against frozen raw.
        self.root.mkdir(parents=True, exist_ok=True)
        digest = sha256(raw)
        raw_path = self.root / "raw" / digest
        raw_path.parent.mkdir(exist_ok=True)
        if raw_path.exists():
            if raw_path.read_bytes() != raw:
                raise ValueError("raw hash collision or altered evidence")
        else:
            with raw_path.open("xb") as stream:
                stream.write(raw)
        event = {
            "schema": "stage2-native-event-v1", "run_id": self.run_id,
            "probe": self.probe, "sequence": len(self.events), "event_id": event_id,
            "operation": operation, "phase": phase, "native_locator": native_locator,
            "hook_id": hook_id, "native_sha256": digest,
            "raw_path": str(raw_path.relative_to(self.root)), "actor": actor,
            "target": target, "source_id": source_id, "carrier_id": carrier_id,
            "carrier_type": carrier_type, "parent_ids": list(parent_ids),
            "status": status, "binding": self.binding,
            "semantic_assessment": "NOT_ADJUDICATED",
        }
        previous_hash = self.events[-1]["record_hash"] if self.events else None
        event["previous_hash"] = previous_hash
        event["record_hash"] = sha256(canonical_bytes(event))
        with (self.root / "events.jsonl").open("ab") as stream:
            stream.write(canonical_bytes(event) + b"\n")
            stream.flush()
        self.events.append(event)
        self.ids.add(event_id)
        return event


def check_capture(root):
    root = Path(root)
    seen, previous = set(), None
    for index, line in enumerate((root / "events.jsonl").read_bytes().splitlines()):
        event = json.loads(line)
        assert event["sequence"] == index and event["previous_hash"] == previous
        assert event["event_id"] not in seen and set(event["parent_ids"]) <= seen
        assert event["operation"] in PROBES[event["probe"]] | COMMON
        assert event["semantic_assessment"] == "NOT_ADJUDICATED"
        assert sha256((root / event["raw_path"]).read_bytes()) == event["native_sha256"]
        digest = event.pop("record_hash")
        assert sha256(canonical_bytes(event)) == digest
        previous = digest
        seen.add(event["event_id"])
    return len(seen)
