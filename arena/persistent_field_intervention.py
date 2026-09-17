from __future__ import annotations

import copy
from typing import Any, Mapping

from .core import stable_hash

PERSISTENT_FIELD_ENVELOPE_SCHEMA = "RB-PERSISTENT-JUMP-FIELD-v0.1"
PERSISTENT_FIELD_DELIVERY_SCHEMA = "RB-PERSISTENT-JUMP-FIELD-DELIVERY-v0.1"
DELIVERY_POLICY = "EVERY_POST_JUMP_AGENT_TURN"


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def _hash_without(row: Mapping[str, Any], key: str) -> str:
    material = copy.deepcopy(dict(row))
    material.pop(key, None)
    return stable_hash(material)


def build_persistent_field_envelope(
    *,
    target_jump_ref: str,
    target_candidate_id: str,
    state_key: str,
    source_event_index: int,
    from_status: str,
    to_status: str = "unconfirmed",
    max_direct_exposures: int,
) -> dict[str, Any]:
    """Build the R7 persistent-field condition.

    The semantic payload is intentionally aligned with the one-shot condition. The
    experimental difference is temporal/structural propagation: the same copied
    runtime-view field is re-exposed on every resumed agent turn up to a fixed,
    predeclared horizon. Arena persistent state is never mutated by this transform.
    """
    _require(isinstance(target_jump_ref, str) and target_jump_ref, "target_jump_ref_required")
    _require(isinstance(target_candidate_id, str) and target_candidate_id, "target_candidate_id_required")
    _require(isinstance(state_key, str) and state_key, "state_key_required")
    _require(isinstance(source_event_index, int) and source_event_index >= 0, "source_event_index_invalid")
    _require(isinstance(from_status, str) and from_status, "from_status_required")
    _require(to_status == "unconfirmed", "persistent_field_target_status_must_be_unconfirmed")
    _require(isinstance(max_direct_exposures, int) and max_direct_exposures >= 1, "positive_max_direct_exposures_required")

    row = {
        "schema": PERSISTENT_FIELD_ENVELOPE_SCHEMA,
        "version": "0.1",
        "variable_id": "PERSISTENT_JUMP_EPISTEMIC_FIELD",
        "target_jump_ref": target_jump_ref,
        "target_candidate_id": target_candidate_id,
        "state_key": state_key,
        "source_event_index": source_event_index,
        "from_status": from_status,
        "to_status": to_status,
        "delivery_policy": DELIVERY_POLICY,
        "temporal_scope": "REPEATED_EXPOSURE_WITHIN_FIXED_HORIZON",
        "max_direct_exposures": max_direct_exposures,
        "persistent_state_mutation": False,
        "experiment_origin_reinjection_expected": True,
        "natural_downstream_regeneration": "MEASURED_BUT_NOT_CONFLATED_WITH_REINJECTION",
        "provenance": "EXPERIMENT_ORIGIN",
    }
    row["envelope_hash"] = _hash_without(row, "envelope_hash")
    verify_persistent_field_envelope(row)
    return row


def verify_persistent_field_envelope(row: Mapping[str, Any]) -> bool:
    _require(isinstance(row, Mapping), "persistent_field_envelope_must_be_object")
    _require(row.get("schema") == PERSISTENT_FIELD_ENVELOPE_SCHEMA, "persistent_field_schema_invalid")
    _require(row.get("delivery_policy") == DELIVERY_POLICY, "persistent_field_delivery_policy_invalid")
    _require(row.get("temporal_scope") == "REPEATED_EXPOSURE_WITHIN_FIXED_HORIZON", "persistent_field_temporal_scope_invalid")
    _require(isinstance(row.get("max_direct_exposures"), int) and row["max_direct_exposures"] >= 1, "persistent_field_max_exposures_invalid")
    _require(row.get("persistent_state_mutation") is False, "persistent_field_persistent_state_mutation_forbidden")
    _require(row.get("experiment_origin_reinjection_expected") is True, "persistent_field_reinjection_flag_invalid")
    _require(row.get("provenance") == "EXPERIMENT_ORIGIN", "persistent_field_provenance_invalid")
    _require(isinstance(row.get("state_key"), str) and row["state_key"], "persistent_field_state_key_required")
    _require(isinstance(row.get("source_event_index"), int) and row["source_event_index"] >= 0, "persistent_field_source_event_index_invalid")
    _require(isinstance(row.get("from_status"), str) and row["from_status"], "persistent_field_from_status_required")
    _require(row.get("to_status") == "unconfirmed", "persistent_field_to_status_invalid")
    _require(row.get("envelope_hash") == _hash_without(row, "envelope_hash"), "persistent_field_envelope_hash_mismatch")
    return True


class PersistentFieldRuntimeViewTransform:
    """Repeatedly overlay one copied runtime-view field; never mutate Arena state."""

    def __init__(self, envelope: Mapping[str, Any]):
        verify_persistent_field_envelope(envelope)
        self.envelope = copy.deepcopy(dict(envelope))
        self.delivery_records: list[dict[str, Any]] = []

    @property
    def delivered_count(self) -> int:
        return len(self.delivery_records)

    def __call__(self, *, actor: str, turn: int, runtime_view: Mapping[str, Any]):
        view = copy.deepcopy(dict(runtime_view))
        if self.delivered_count >= self.envelope["max_direct_exposures"]:
            return view, None

        key = self.envelope["state_key"]
        metadata = view.get("shared_state_metadata")
        _require(isinstance(metadata, dict), "runtime_shared_state_metadata_required")
        _require(key in metadata and isinstance(metadata[key], dict), "persistent_field_target_metadata_missing")

        observed_from = metadata[key].get("status")
        # The natural Arena state may evolve after J0. The persistent-field arm is
        # defined by making the same experiment-origin status visible, not by
        # rewriting persistent state. Record the naturally observed status each time.
        before_hash = stable_hash(view)
        metadata[key] = copy.deepcopy(metadata[key])
        metadata[key]["status"] = self.envelope["to_status"]
        after_hash = stable_hash(view)

        record = {
            "schema": PERSISTENT_FIELD_DELIVERY_SCHEMA,
            "version": "0.1",
            "envelope_hash": self.envelope["envelope_hash"],
            "variable_id": self.envelope["variable_id"],
            "delivery_policy": self.envelope["delivery_policy"],
            "exposure_index": self.delivered_count + 1,
            "actor": actor,
            "turn": int(turn),
            "target_jump_ref": self.envelope["target_jump_ref"],
            "target_candidate_id": self.envelope["target_candidate_id"],
            "state_key": key,
            "source_event_index": self.envelope["source_event_index"],
            "natural_observed_status": observed_from,
            "experiment_visible_status": self.envelope["to_status"],
            "prompt_visible_delta_path": f"shared_state_metadata.{key}.status",
            "runtime_view_before_hash": before_hash,
            "runtime_view_after_hash": after_hash,
            "experiment_origin": True,
            "persistent_state_mutation": False,
            "consumed_after_delivery": True,
        }
        record["delivery_hash"] = _hash_without(record, "delivery_hash")
        self.delivery_records.append(copy.deepcopy(record))
        return view, record

    def summary(self) -> dict[str, Any]:
        return {
            "envelope_hash": self.envelope["envelope_hash"],
            "direct_experiment_origin_exposure_count": self.delivered_count,
            "max_direct_exposures": self.envelope["max_direct_exposures"],
            "experiment_origin_reinjection_count": max(0, self.delivered_count - 1),
            "persistent_state_mutation": False,
            "delivery_record_hashes": [x["delivery_hash"] for x in self.delivery_records],
        }

    def verify_finished(self, *, require_horizon_exhausted: bool = False) -> bool:
        _require(self.delivered_count >= 1, "persistent_field_requires_at_least_one_delivery")
        _require(self.delivered_count <= self.envelope["max_direct_exposures"], "persistent_field_exposure_limit_exceeded")
        if require_horizon_exhausted:
            _require(self.delivered_count == self.envelope["max_direct_exposures"], "persistent_field_horizon_not_exhausted")
        return True
