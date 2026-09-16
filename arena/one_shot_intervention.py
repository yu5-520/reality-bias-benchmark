from __future__ import annotations

import copy
from typing import Any, Mapping

from .core import stable_hash

ENVELOPE_SCHEMA = "RB-ONE-SHOT-JUMP-INTERVENTION-v0.1"
DELIVERY_SCHEMA = "RB-ONE-SHOT-INTERVENTION-DELIVERY-v0.1"
BRANCH_SCHEMA_V3 = "RB-EXPERIMENTAL-BRANCH-v0.3"
CONTROL_CONDITION = "CONTROL_CONTINUATION"
INTERVENTION_CONDITION = "ONE_SHOT_JUMP_INTERVENTION"
DELIVERY_POLICY = "FIRST_POST_JUMP_AGENT_TURN"


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def _hash_without(row: Mapping[str, Any], key: str) -> str:
    material = copy.deepcopy(dict(row))
    material.pop(key, None)
    return stable_hash(material)


def build_one_shot_envelope(
    *,
    target_jump_ref: str,
    target_candidate_id: str,
    state_key: str,
    source_event_index: int,
    from_status: str,
    to_status: str = "unconfirmed",
) -> dict[str, Any]:
    _require(isinstance(target_jump_ref, str) and target_jump_ref, "target_jump_ref_required")
    _require(isinstance(target_candidate_id, str) and target_candidate_id, "target_candidate_id_required")
    _require(isinstance(state_key, str) and state_key, "state_key_required")
    _require(isinstance(source_event_index, int) and source_event_index >= 0, "source_event_index_invalid")
    _require(isinstance(from_status, str) and from_status, "from_status_required")
    _require(to_status == "unconfirmed", "v01_target_status_must_be_unconfirmed")
    row = {
        "schema": ENVELOPE_SCHEMA,
        "version": "0.1",
        "variable_id": "ONE_SHOT_JUMP_EPISTEMIC_PERTURBATION",
        "target_jump_ref": target_jump_ref,
        "target_candidate_id": target_candidate_id,
        "state_key": state_key,
        "source_event_index": source_event_index,
        "from_status": from_status,
        "to_status": to_status,
        "delivery_policy": DELIVERY_POLICY,
        "temporal_scope": "ONE_EXPOSURE_ONLY",
        "direct_exposure_limit": 1,
        "persistent_state_mutation": False,
        "experiment_origin_reinjection_forbidden": True,
        "natural_downstream_regeneration": "ALLOWED_AND_MEASURED",
        "provenance": "EXPERIMENT_ORIGIN",
    }
    row["envelope_hash"] = _hash_without(row, "envelope_hash")
    verify_one_shot_envelope(row)
    return row


def verify_one_shot_envelope(row: Mapping[str, Any]) -> bool:
    _require(isinstance(row, Mapping), "one_shot_envelope_must_be_object")
    _require(row.get("schema") == ENVELOPE_SCHEMA, "one_shot_envelope_schema_invalid")
    _require(row.get("delivery_policy") == DELIVERY_POLICY, "one_shot_delivery_policy_invalid")
    _require(row.get("temporal_scope") == "ONE_EXPOSURE_ONLY", "one_shot_temporal_scope_invalid")
    _require(row.get("direct_exposure_limit") == 1, "one_shot_direct_exposure_limit_invalid")
    _require(row.get("persistent_state_mutation") is False, "one_shot_persistent_state_mutation_forbidden")
    _require(row.get("experiment_origin_reinjection_forbidden") is True, "one_shot_reinjection_must_be_forbidden")
    _require(row.get("provenance") == "EXPERIMENT_ORIGIN", "one_shot_provenance_invalid")
    _require(isinstance(row.get("state_key"), str) and row["state_key"], "one_shot_state_key_required")
    _require(isinstance(row.get("source_event_index"), int) and row["source_event_index"] >= 0, "one_shot_source_event_index_invalid")
    _require(isinstance(row.get("from_status"), str) and row["from_status"], "one_shot_from_status_required")
    _require(row.get("to_status") == "unconfirmed", "one_shot_to_status_invalid")
    _require(row.get("envelope_hash") == _hash_without(row, "envelope_hash"), "one_shot_envelope_hash_mismatch")
    return True


class OneShotRuntimeViewTransform:
    """Overlay one copied runtime view exactly once; never mutate Arena state."""

    def __init__(self, envelope: Mapping[str, Any]):
        verify_one_shot_envelope(envelope)
        self.envelope = copy.deepcopy(dict(envelope))
        self.delivery_records: list[dict[str, Any]] = []

    @property
    def delivered_count(self) -> int:
        return len(self.delivery_records)

    def __call__(self, *, actor: str, turn: int, runtime_view: Mapping[str, Any]):
        view = copy.deepcopy(dict(runtime_view))
        if self.delivered_count:
            return view, None
        key = self.envelope["state_key"]
        metadata = view.get("shared_state_metadata")
        _require(isinstance(metadata, dict), "runtime_shared_state_metadata_required")
        _require(key in metadata and isinstance(metadata[key], dict), "one_shot_target_metadata_missing")
        observed_from = metadata[key].get("status")
        _require(observed_from == self.envelope["from_status"], "one_shot_runtime_from_status_mismatch")
        before_hash = stable_hash(view)
        metadata[key] = copy.deepcopy(metadata[key])
        metadata[key]["status"] = self.envelope["to_status"]
        after_hash = stable_hash(view)
        _require(before_hash != after_hash, "one_shot_runtime_overlay_must_change_view")
        record = {
            "schema": DELIVERY_SCHEMA,
            "version": "0.1",
            "envelope_hash": self.envelope["envelope_hash"],
            "variable_id": self.envelope["variable_id"],
            "delivery_policy": self.envelope["delivery_policy"],
            "actor": actor,
            "turn": int(turn),
            "target_jump_ref": self.envelope["target_jump_ref"],
            "target_candidate_id": self.envelope["target_candidate_id"],
            "state_key": key,
            "source_event_index": self.envelope["source_event_index"],
            "from_status": observed_from,
            "to_status": self.envelope["to_status"],
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
            "consumed": self.delivered_count == 1,
            "experiment_origin_reinjection_count": 0,
            "persistent_state_mutation": False,
            "delivery_record_hashes": [x["delivery_hash"] for x in self.delivery_records],
        }

    def verify_finished(self) -> bool:
        _require(self.delivered_count == 1, "one_shot_exactly_one_delivery_required")
        return True


def make_branch_manifest_v3(
    *,
    branch_id: str,
    condition_id: str,
    parent_trace_hash: str,
    parent_snapshot: Mapping[str, Any],
    envelope: Mapping[str, Any] | None,
    replicate_index: int,
    model_identity: Mapping[str, Any] | None = None,
    config_identity: Mapping[str, Any] | None = None,
    code_identity: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    from .experimental_control import verify_state_snapshot

    verify_state_snapshot(dict(parent_snapshot))
    _require(condition_id in (CONTROL_CONDITION, INTERVENTION_CONDITION), "one_shot_condition_invalid")
    _require(isinstance(branch_id, str) and branch_id, "branch_id_required")
    _require(isinstance(parent_trace_hash, str) and parent_trace_hash, "parent_trace_hash_required")
    _require(isinstance(replicate_index, int) and replicate_index >= 1, "replicate_index_invalid")
    if condition_id == CONTROL_CONDITION:
        _require(envelope is None, "control_must_not_bind_one_shot_envelope")
        spec = {"type": "no_intervention_control", "scope": "UNCHANGED_FROZEN_PARENT_STATE", "temporal_scope": "NO_DIRECT_EXPOSURE"}
        envelope_hash = None
        direct_limit = 0
        temporal_scope = "NO_DIRECT_EXPOSURE"
    else:
        _require(envelope is not None, "intervention_envelope_required")
        verify_one_shot_envelope(envelope)
        spec = {
            "type": "one_shot_runtime_metadata_overlay",
            "variable_id": envelope["variable_id"],
            "state_key": envelope["state_key"],
            "from_status": envelope["from_status"],
            "to_status": envelope["to_status"],
            "delivery_policy": envelope["delivery_policy"],
            "scope": "ONE_PROMPT_VISIBLE_METADATA_STATUS_FIELD_ONLY",
        }
        envelope_hash = envelope["envelope_hash"]
        direct_limit = 1
        temporal_scope = "ONE_EXPOSURE_ONLY"
    state_hash = parent_snapshot["state_hash"]
    manifest = {
        "schema": BRANCH_SCHEMA_V3,
        "version": "0.3",
        "branch_id": branch_id,
        "condition_id": condition_id,
        "parent_trace_hash": parent_trace_hash,
        "parent_state_hash": state_hash,
        "branch_start_state_hash": state_hash,
        "parent_turn": int(parent_snapshot["turns"]),
        "branch_start_turn": int(parent_snapshot["turns"]),
        "parent_event_count": len(parent_snapshot["events"]),
        "branch_start_event_count": len(parent_snapshot["events"]),
        "anchor_ref": parent_snapshot.get("anchor_ref"),
        "branch_start_anchor_ref": parent_snapshot.get("anchor_ref"),
        "intervention_spec": spec,
        "intervention_hash": stable_hash(spec),
        "one_shot_intervention_envelope_hash": envelope_hash,
        "intervention_temporal_scope": temporal_scope,
        "direct_exposure_limit": direct_limit,
        "persistent_state_mutation": False,
        "experiment_origin_reinjection_forbidden": True,
        "intervention_applied_before_continuation": False,
        "replicate_index": replicate_index,
        "created_from_frozen_parent": True,
        "model_identity": copy.deepcopy(dict(model_identity or {})),
        "config_identity": copy.deepcopy(dict(config_identity or {})),
        "code_identity": copy.deepcopy(dict(code_identity or {})),
        "provider_internal_state_replayed": False,
    }
    manifest["branch_hash"] = _hash_without(manifest, "branch_hash")
    verify_branch_manifest_v3(manifest, parent_snapshot=parent_snapshot, envelope=envelope)
    return manifest


def verify_branch_manifest_v3(manifest: Mapping[str, Any], *, parent_snapshot=None, envelope=None) -> bool:
    _require(manifest.get("schema") == BRANCH_SCHEMA_V3, "one_shot_branch_schema_invalid")
    _require(manifest.get("branch_hash") == _hash_without(manifest, "branch_hash"), "one_shot_branch_hash_mismatch")
    _require(manifest.get("parent_state_hash") == manifest.get("branch_start_state_hash"), "one_shot_parent_start_state_must_match")
    _require(manifest.get("intervention_applied_before_continuation") is False, "one_shot_precontinuation_state_mutation_forbidden")
    _require(manifest.get("persistent_state_mutation") is False, "one_shot_persistent_state_mutation_forbidden")
    _require(manifest.get("provider_internal_state_replayed") is False, "provider_hidden_state_replay_claim_forbidden")
    condition = manifest.get("condition_id")
    _require(condition in (CONTROL_CONDITION, INTERVENTION_CONDITION), "one_shot_branch_condition_invalid")
    if condition == CONTROL_CONDITION:
        _require(manifest.get("direct_exposure_limit") == 0, "control_direct_exposure_limit_must_be_zero")
        _require(manifest.get("one_shot_intervention_envelope_hash") is None, "control_envelope_hash_must_be_null")
    else:
        _require(manifest.get("direct_exposure_limit") == 1, "intervention_direct_exposure_limit_must_be_one")
        _require(envelope is not None, "intervention_envelope_required_for_verification")
        verify_one_shot_envelope(envelope)
        _require(manifest.get("one_shot_intervention_envelope_hash") == envelope.get("envelope_hash"), "intervention_envelope_hash_mismatch")
    if parent_snapshot is not None:
        from .experimental_control import verify_state_snapshot
        verify_state_snapshot(parent_snapshot)
        _require(manifest.get("parent_state_hash") == parent_snapshot.get("state_hash"), "one_shot_parent_hash_mismatch")
        _require(manifest.get("parent_turn") == parent_snapshot.get("turns"), "one_shot_parent_turn_mismatch")
    return True
