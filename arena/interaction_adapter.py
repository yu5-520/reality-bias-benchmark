"""Additive interaction evidence gateway; historical Arena traces are never rewritten.

An external substrate calls the named methods with *observed* native receipts. This
module records evidence, not semantic adoption or a simulated transport.
"""

from __future__ import annotations

import copy
from collections import defaultdict

from .core import stable_hash

SCHEMA = "RB-INTERACTION-EVENT-v1"
SURFACES = frozenset({
    "send_message", "receive_message", "shared_state", "delegate", "handoff",
    "tool_call", "resource_read", "memory_write", "memory_retrieve",
    "remote_task", "artifact_return",
})
OBSERVATIONS = frozenset({
    "PROPOSED", "RECORDED", "DELIVERED", "INPUT_EXPOSED", "EXECUTED",
    "FAILED", "UNAVAILABLE",
})


class InteractionAdapter:
    """Versioned, content-addressed observation surface for native interactions.

    Native code performs the operation; this class requires its actual raw locator
    and receipt. INPUT_EXPOSED means an input was delivered, not that the model
    semantically read or accepted it. source_refs/parent_event_ids are observed
    identifiers; the gateway does not invent inferred lineage.
    """

    def __init__(self, *, run_id: str, architecture_id: str, adapter_version: str):
        if not all(isinstance(x, str) and x for x in (run_id, architecture_id, adapter_version)):
            raise ValueError("interaction_identity_required")
        self.run_id = run_id
        self.architecture_id = architecture_id
        self.adapter_version = adapter_version
        self.events: list[dict] = []
        self._ids: set[str] = set()

    def record(self, surface: str, *, actor: str, native_ref: str, raw_ref: str,
               carrier_ref: str, observation: str, turn: int | None = None,
               payload=None, authority_status: str | None = None,
               source_refs=(), parent_event_ids=(), recipient: str | None = None):
        if surface not in SURFACES or observation not in OBSERVATIONS:
            raise ValueError("unknown_interaction_surface_or_observation")
        if not all(isinstance(x, str) and x for x in (actor, native_ref, raw_ref, carrier_ref)):
            raise ValueError("observed_actor_native_raw_and_carrier_refs_required")
        if turn is not None and (type(turn) is not int or turn < 0):
            raise ValueError("invalid_interaction_turn")
        if any(not isinstance(x, str) or not x for x in (*source_refs, *parent_event_ids)):
            raise ValueError("invalid_interaction_relation_ref")
        if len(set(source_refs)) != len(source_refs) or len(set(parent_event_ids)) != len(parent_event_ids):
            raise ValueError("duplicate_interaction_relation_ref")
        if any(ref not in self._ids for ref in parent_event_ids):
            raise ValueError("interaction_parent_must_precede_child")
        row = {
            "schema": SCHEMA, "run_id": self.run_id,
            "architecture_id": self.architecture_id,
            "adapter_version": self.adapter_version, "surface": surface,
            "actor": actor, "recipient": recipient, "turn": turn,
            "native_ref": native_ref, "raw_ref": raw_ref,
            "carrier_ref": carrier_ref,
            "content_hash": stable_hash(payload) if payload is not None else None,
            "authority_status": authority_status,
            "observation": observation,
            "source_refs": list(source_refs),
            "parent_event_ids": list(parent_event_ids),
        }
        row["event_hash"] = stable_hash(row)
        row["event_id"] = f"{self.run_id}:IE:{row['event_hash'][:20]}"
        if row["event_id"] in self._ids:
            raise ValueError("duplicate_interaction_event")
        self._ids.add(row["event_id"])
        self.events.append(row)
        return copy.deepcopy(row)

    def send_message(self, **kwargs): return self.record("send_message", **kwargs)
    def receive_message(self, **kwargs): return self.record("receive_message", **kwargs)
    def shared_state(self, **kwargs): return self.record("shared_state", **kwargs)
    def delegate(self, **kwargs): return self.record("delegate", **kwargs)
    def handoff(self, **kwargs): return self.record("handoff", **kwargs)
    def tool_call(self, **kwargs): return self.record("tool_call", **kwargs)
    def resource_read(self, **kwargs): return self.record("resource_read", **kwargs)
    def memory_write(self, **kwargs): return self.record("memory_write", **kwargs)
    def memory_retrieve(self, **kwargs): return self.record("memory_retrieve", **kwargs)
    def remote_task(self, **kwargs): return self.record("remote_task", **kwargs)
    def artifact_return(self, **kwargs): return self.record("artifact_return", **kwargs)


def validate_interactions(events: list[dict], *, require_raw=True) -> dict:
    """Mechanical contract gates; semantic claims remain deferred to human/AI audit."""
    failures = []
    seen = set()
    sent = defaultdict(set)
    for i, event in enumerate(events):
        e = dict(event)
        event_id = e.pop("event_id", None)
        digest = e.pop("event_hash", None)
        if e.get("schema") != SCHEMA or e.get("surface") not in SURFACES or e.get("observation") not in OBSERVATIONS:
            failures.append(f"event_{i}:contract")
        if digest != stable_hash(e) or event_id != f"{e.get('run_id')}:IE:{str(digest)[:20]}":
            failures.append(f"event_{i}:hash")
        if event_id in seen:
            failures.append(f"event_{i}:duplicate")
        if any(p not in seen for p in e.get("parent_event_ids", [])):
            failures.append(f"event_{i}:missing_or_forward_parent")
        if not e.get("native_ref") or not e.get("carrier_ref") or (require_raw and not e.get("raw_ref")):
            failures.append(f"event_{i}:unaddressable")
        if e.get("surface") == "send_message":
            sent[e.get("carrier_ref")].add(event_id)
        if e.get("surface") == "receive_message" and e.get("observation") == "INPUT_EXPOSED":
            if not set(e.get("parent_event_ids", [])) & sent[e.get("carrier_ref")]:
                failures.append(f"event_{i}:message_without_send_parent")
        seen.add(event_id)
    return {"schema": SCHEMA, "event_count": len(events), "status": "PASS" if not failures else "FAIL", "failures": failures,
            "semantic_adjudication": "NOT_ADJUDICATED"}


def project_legacy_trace(trace: dict) -> list[dict]:
    """Read-only projection of a Common Pool trace; never changes its raw hash.

    The historical trace is a reference sample, not a prospective architecture cell.
    A state in an input is only INPUT_EXPOSED. No semantic-use event is fabricated.
    """
    run_id = trace["run_id"]
    adapter = InteractionAdapter(run_id=run_id, architecture_id="shared_common_pool",
                                 adapter_version="arena-native-readonly-v1")
    events_by_message = {}
    state_origins = {}
    calls = sorted(enumerate(trace.get("model_calls", [])), key=lambda pair: pair[1].get("turn", 0))
    native_events = sorted(trace.get("events", []), key=lambda e: e["event_index"])
    messages = trace.get("message_ledger", [])
    # Origin events are available before the first model input. This asserts
    # exposure only and does not claim the initial task field was adopted.
    if calls:
        initial = calls[0][1].get("runtime_snapshot", {}).get("shared_state", {})
        for key, value in initial.items():
            row = adapter.shared_state(actor="ENVIRONMENT", turn=0,
                native_ref=f"{run_id}:TASK:initial_shared_state:{key}",
                raw_ref=f"{run_id}:TASK:/initial_shared_state/{key}",
                carrier_ref=f"state:{key}", observation="RECORDED", payload=value,
                authority_status="initial")
            state_origins[key] = row["event_id"]
    next_event = 0
    for call_idx, call in calls:
        turn = call.get("turn", 0)
        for msg in messages:
            mid = msg["message_id"]
            if mid not in events_by_message and msg.get("sent_turn", 0) < turn:
                row = adapter.send_message(actor=msg.get("sender") or "ENVIRONMENT",
                    recipient=msg.get("recipient"), turn=msg.get("sent_turn", 0),
                    native_ref=f"{run_id}:MESSAGE:{mid}", raw_ref=f"{run_id}:MESSAGE_LEDGER:{mid}",
                    carrier_ref=f"message:{mid}", observation="DELIVERED", payload=msg.get("content"))
                events_by_message[mid] = row["event_id"]
        for mid in call.get("input_message_ids", []):
            msg = next((m for m in messages if m["message_id"] == mid), None)
            if msg is None or mid not in events_by_message:
                raise ValueError(f"missing_native_send_or_ledger_for_input:{mid}")
            adapter.receive_message(actor=call["agent_id"], turn=turn,
                native_ref=f"{run_id}:CALL:{call_idx:04d}:inbox:{mid}",
                raw_ref=f"{run_id}:CALL:{call_idx:04d}:/runtime_snapshot/inbox",
                carrier_ref=f"message:{mid}", observation="INPUT_EXPOSED",
                payload=msg.get("content"), parent_event_ids=[events_by_message[mid]])
        view = call.get("runtime_snapshot") or {}
        for key, value in view.get("shared_state", {}).items():
            parents = [state_origins[key]] if key in state_origins else []
            adapter.shared_state(actor=call["agent_id"], turn=turn,
                native_ref=f"{run_id}:CALL:{call_idx:04d}:shared_state:{key}",
                raw_ref=f"{run_id}:CALL:{call_idx:04d}:/runtime_snapshot/shared_state/{key}",
                carrier_ref=f"state:{key}", observation="INPUT_EXPOSED", payload=value,
                authority_status=(view.get("shared_state_metadata", {}).get(key) or {}).get("status"),
                parent_event_ids=parents)
        end = call.get("event_index_end", next_event)
        while next_event < end and next_event < len(native_events):
            event = native_events[next_event]
            next_event += 1
            if not event.get("realized_in_baseline"):
                continue
            action = event.get("action") or {}
            kind = event.get("action_type")
            ref = f"{run_id}:EVENT:{event['event_index']:04d}"
            if kind == "write_state":
                key = action["key"]
                row = adapter.shared_state(actor=event["actor"], turn=turn, native_ref=ref,
                    raw_ref=ref + ":/action/value", carrier_ref=f"state:{key}",
                    observation="RECORDED", payload=action.get("value"),
                    authority_status=action.get("status"),
                    parent_event_ids=[state_origins[key]] if key in state_origins else [])
                state_origins[key] = row["event_id"]
            elif kind == "revise_final_state":
                for key, value in (action.get("patch") or {}).items():
                    row = adapter.shared_state(actor=event["actor"], turn=turn,
                        native_ref=ref + f":patch:{key}", raw_ref=ref + f":/action/patch/{key}",
                        carrier_ref=f"state:{key}", observation="RECORDED", payload=value,
                        authority_status=action.get("status", "unspecified"),
                        parent_event_ids=[state_origins[key]] if key in state_origins else [])
                    state_origins[key] = row["event_id"]
            elif kind == "invoke_agent":
                adapter.delegate(actor=event["actor"], recipient=action.get("agent_id"),
                    turn=turn, native_ref=ref, raw_ref=ref + ":/action",
                    carrier_ref=f"invocation:{action.get('invocation_id')}",
                    observation="RECORDED", payload=action.get("request"))
            elif kind in ("message", "late_event") and action.get("message_id"):
                mid = action["message_id"]
                if mid not in events_by_message:
                    msg = next((m for m in messages if m["message_id"] == mid), None)
                    row = adapter.send_message(actor=event["actor"],
                        recipient=msg.get("recipient") if msg else None, turn=turn,
                        native_ref=ref, raw_ref=ref + ":/action",
                        carrier_ref=f"message:{mid}", observation="DELIVERED",
                        payload=msg.get("content") if msg else action)
                    events_by_message[mid] = row["event_id"]
            elif kind == "finalize":
                adapter.artifact_return(actor=event["actor"], turn=turn,
                    native_ref=ref, raw_ref=ref + ":/final_state_after",
                    carrier_ref=f"final:{run_id}", observation="RECORDED",
                    payload=event.get("final_state_after"))
    return adapter.events
