"""Offline ordering of frozen checkpoints; content hashes are never clocks.

Natural-A ordering is bound to the controller's frozen ledger. Legacy B
archives lack that ledger: only the explicitly supported native event grammar
is accepted. Unknown or ambiguous order fails closed, without using mtime,
archive order, remaining budget, or lexicographic hash order.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re


class ChronologyError(ValueError):
    pass


def ordered_checkpoints(archive, members, prefix="checkpoints/", *, allowed=None):
    def read(path):
        stream = archive.extractfile(members[path])
        if stream is None:
            raise ChronologyError(f"unreadable evidence: {path}")
        return stream.read()

    visible = set(members) if allowed is None else set(allowed)
    rows = {}
    for path in members:
        if path not in visible or not path.startswith(prefix) or not path.endswith("/manifest.json"):
            continue
        obj = json.loads(read(path))
        if not isinstance(obj.get("application_file_hashes"), dict):
            continue
        identity = obj.get("checkpoint_hash")
        if not identity or path != f"{prefix}{identity}/manifest.json":
            raise ChronologyError(f"checkpoint identity/path mismatch: {path}")
        rows[identity] = (path, obj)
    if not rows:
        return []

    ledger_path = "checkpoint_ledger.json" if prefix == "checkpoints/" else "post_repair_checkpoint_ledger.json"
    ordered = []
    if ledger_path in visible and ledger_path in members:
        raw = read(ledger_path)
        ledger = json.loads(raw)
        previous = -1
        seen = {}
        for index, item in enumerate(ledger["checkpoints"]):
            seq = item.get("model_decision_sequence")
            if type(seq) is not int or seq < previous:
                raise ChronologyError(f"invalid ledger order: {ledger_path} entry {index}")
            previous = seq
            identity = item.get("checkpoint_hash")
            if identity not in rows:
                continue  # A legal evidence view may omit unobservable snapshots.
            path, obj = rows[identity]
            if identity in seen:
                if seen[identity] != seq:
                    raise ChronologyError(f"checkpoint rebound to another time: {identity}")
                continue  # First-eligible pointers can alias an existing checkpoint.
            if item.get("event_ref") != obj.get("event_ref"):
                raise ChronologyError(f"ledger/manifest event mismatch: {path}")
            seen[identity] = seq
            ordered.append((path, obj, {
                "basis": "FROZEN_CHECKPOINT_LEDGER",
                "clock": "model_decision_sequence",
                "sequence": seq,
                "ledger_index": index,
                "ledger_path": ledger_path,
                "ledger_sha256": hashlib.sha256(raw).hexdigest(),
            }))
        missing = set(rows) - set(seen)
        if missing:
            raise ChronologyError(f"manifests absent from ledger: {sorted(missing)}")
    else:
        # These event formats are emitted by the frozen host and MetaGPT runners.
        # Native rounds/turns are not relabelled as model-decision counts.
        positions = {}
        families = set()
        for path, obj in rows.values():
            ref = obj.get("event_ref", "")
            match = re.fullmatch(r"(host|x[123]):(?:(turn|round):(\d+):post|(task-start|terminal))", ref)
            if not match:
                raise ChronologyError(f"no supported frozen clock: {path}: {ref}")
            system, unit, number, boundary = match.groups()
            if unit:
                expected = "turn" if system == "host" else "round"
                if unit != expected:
                    raise ChronologyError(f"inconsistent native clock: {ref}")
                position = (1, int(number))
            else:
                position = (0, 0) if boundary == "task-start" else (2, 0)
            families.add(system)
            if position in positions:
                raise ChronologyError(f"ambiguous native checkpoint position: {ref}")
            positions[position] = (path, obj, {
                "basis": "FROZEN_NATIVE_EVENT_REF",
                "clock": "native_turn" if system == "host" else "native_round",
                "sequence": int(number) if number else None,
                "boundary": boundary or "post",
                "event_ref": ref,
            })
        if len(families) != 1:
            raise ChronologyError("mixed native clocks in one checkpoint set")
        ordered = [positions[pos] for pos in sorted(positions)]

    result = []
    for rank, (path, obj, provenance) in enumerate(ordered):
        derived = copy.deepcopy(obj)
        derived["_chronology"] = {**provenance, "rank": rank}
        result.append((rank, path, derived))
    return result
