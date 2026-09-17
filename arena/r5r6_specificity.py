from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .core import stable_hash

SPECIFICITY_PLAN_SCHEMA = "RB-R5R6-SPECIFICITY-PLAN-v0.1"
SPECIFICITY_SELECTION_SCHEMA = "RB-R5R6-SPECIFICITY-FIELD-SELECTION-v0.1"
SPECIFICITY_ENVELOPE_SCHEMA = "RB-R5R6-SPECIFICITY-ONE-SHOT-ENVELOPE-v0.1"
SPECIFICITY_DELIVERY_SCHEMA = "RB-R5R6-SPECIFICITY-DELIVERY-v0.1"

S0 = "S0_NATURAL_REFERENCE"
S1 = "S1_MATCHED_FACTUAL_FIELD_DOWNGRADE"
S2 = "S2_J0_TARGETED_AUTHORITY_WITHDRAWAL"
CONDITIONS = (S0, S1, S2)

MECHANICAL_PRIMITIVE = "ONE_SHOT_EPISTEMIC_STATUS_DOWNGRADE"
RESEARCH_IDENTITY_S1 = "R5R6_S1_MATCHED_FACTUAL_FIELD"
RESEARCH_IDENTITY_S2 = "R5R6_S2_J0_TARGET"
DEFAULT_DELIVERY_POLICY = "FIRST_ELIGIBLE_POST_BOUNDARY_AGENT_TURN"


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def _hash_without(row: Mapping[str, Any], key: str) -> str:
    material = copy.deepcopy(dict(row))
    material.pop(key, None)
    return stable_hash(material)


def _as_nonempty_str(value: Any, message: str) -> str:
    _require(isinstance(value, str) and bool(value), message)
    return value


def _normalized_candidate(row: Mapping[str, Any]) -> dict[str, Any]:
    _require(isinstance(row, Mapping), "specificity_candidate_must_be_object")
    state_key = _as_nonempty_str(row.get("state_key"), "specificity_candidate_state_key_required")
    status = _as_nonempty_str(row.get("pre_status"), "specificity_candidate_pre_status_required")
    source_refs = row.get("source_refs")
    _require(isinstance(source_refs, list) and source_refs, "specificity_candidate_source_refs_required")
    _require(all(isinstance(x, str) and x for x in source_refs), "specificity_candidate_source_refs_invalid")
    match = row.get("matching_features")
    _require(isinstance(match, Mapping), "specificity_candidate_matching_features_required")
    eligible = row.get("eligible", True)
    _require(isinstance(eligible, bool), "specificity_candidate_eligible_must_be_bool")
    return {
        "state_key": state_key,
        "pre_status": status,
        "source_refs": list(source_refs),
        "matching_features": copy.deepcopy(dict(match)),
        "eligible": eligible,
        "exclusion_reason": row.get("exclusion_reason"),
    }


def _distance(j0_features: Mapping[str, Any], candidate_features: Mapping[str, Any]) -> tuple[int, str]:
    """Simple preregistrable structural mismatch count; lower is a better match.

    The score is intentionally transparent and non-semantic. It compares only
    features supplied by the frozen field-selection contract.
    """
    keys = sorted(set(j0_features) | set(candidate_features))
    mismatches = sum(1 for key in keys if j0_features.get(key) != candidate_features.get(key))
    signature = stable_hash({"keys": keys, "candidate_features": dict(candidate_features)})
    return mismatches, signature


def build_field_selection_record(
    *,
    source_trace_hash: str,
    source_evidence_hash: str,
    common_parent_state_hash: str,
    j0_candidate_id: str,
    j0_event_ref: str,
    j0_state_key: str,
    j0_pre_status: str,
    j0_matching_features: Mapping[str, Any],
    candidates: Iterable[Mapping[str, Any]],
    selection_rule_id: str = "MIN_STRUCTURAL_MISMATCH_THEN_STATE_KEY_v1",
) -> dict[str, Any]:
    for value, message in (
        (source_trace_hash, "source_trace_hash_required"),
        (source_evidence_hash, "source_evidence_hash_required"),
        (common_parent_state_hash, "common_parent_state_hash_required"),
        (j0_candidate_id, "j0_candidate_id_required"),
        (j0_event_ref, "j0_event_ref_required"),
        (j0_state_key, "j0_state_key_required"),
        (j0_pre_status, "j0_pre_status_required"),
        (selection_rule_id, "selection_rule_id_required"),
    ):
        _as_nonempty_str(value, message)
    _require(isinstance(j0_matching_features, Mapping), "j0_matching_features_required")

    normalized = [_normalized_candidate(x) for x in candidates]
    _require(normalized, "specificity_candidate_pool_must_not_be_empty")

    eligible: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for row in normalized:
        if row["state_key"] == j0_state_key:
            row = copy.deepcopy(row)
            row["eligible"] = False
            row["exclusion_reason"] = "SELECTED_J0_TARGET_EXCLUDED_FROM_S1_POOL"
        if row["pre_status"] != j0_pre_status:
            row = copy.deepcopy(row)
            row["eligible"] = False
            row["exclusion_reason"] = row.get("exclusion_reason") or "PRE_STATUS_NOT_COMPATIBLE_WITH_J0"
        if row["eligible"]:
            score, feature_hash = _distance(j0_matching_features, row["matching_features"])
            row = copy.deepcopy(row)
            row["structural_mismatch_count"] = score
            row["matching_feature_hash"] = feature_hash
            eligible.append(row)
        else:
            excluded.append(row)

    _require(eligible, "specificity_no_eligible_s1_field")
    eligible.sort(key=lambda x: (x["structural_mismatch_count"], x["state_key"]))
    selected = copy.deepcopy(eligible[0])

    pool_material = {
        "eligible": eligible,
        "excluded": excluded,
        "j0_matching_features": copy.deepcopy(dict(j0_matching_features)),
    }
    pool_hash = stable_hash(pool_material)
    selection_rule = {
        "id": selection_rule_id,
        "score": "COUNT_MISMATCHES_ACROSS_FROZEN_MATCHING_FEATURES",
        "tie_break": "LEXICOGRAPHIC_STATE_KEY",
        "outcome_fields_used": False,
    }
    selection_rule_hash = stable_hash(selection_rule)
    selected_target_hash = stable_hash(
        {
            "state_key": selected["state_key"],
            "pre_status": selected["pre_status"],
            "source_refs": selected["source_refs"],
            "matching_features": selected["matching_features"],
            "pool_hash": pool_hash,
            "selection_rule_hash": selection_rule_hash,
        }
    )

    record = {
        "schema": SPECIFICITY_SELECTION_SCHEMA,
        "version": "0.1",
        "source_trace_hash": source_trace_hash,
        "source_evidence_hash": source_evidence_hash,
        "common_parent_state_hash": common_parent_state_hash,
        "selected_j0_candidate_id": j0_candidate_id,
        "selected_j0_event_ref": j0_event_ref,
        "selected_j0_state_key": j0_state_key,
        "selected_j0_pre_status": j0_pre_status,
        "j0_matching_features": copy.deepcopy(dict(j0_matching_features)),
        "eligible_pool": eligible,
        "excluded_pool": excluded,
        "eligible_pool_hash": pool_hash,
        "candidate_count": len(normalized),
        "eligible_candidate_count": len(eligible),
        "selection_rule": selection_rule,
        "selection_rule_hash": selection_rule_hash,
        "selected_s1_state_key": selected["state_key"],
        "selected_s1_source_refs": selected["source_refs"],
        "selected_s1_pre_status": selected["pre_status"],
        "selected_s1_matching_features": selected["matching_features"],
        "selected_s1_target_hash": selected_target_hash,
        "selector_outcome_blind_attestation": True,
        "future_s_arm_outputs_available_to_selector": False,
    }
    record["selection_record_hash"] = _hash_without(record, "selection_record_hash")
    verify_field_selection_record(record)
    return record


def verify_field_selection_record(record: Mapping[str, Any]) -> bool:
    _require(record.get("schema") == SPECIFICITY_SELECTION_SCHEMA, "specificity_selection_schema_invalid")
    _require(record.get("selector_outcome_blind_attestation") is True, "specificity_selection_must_be_outcome_blind")
    _require(record.get("future_s_arm_outputs_available_to_selector") is False, "future_s_outputs_must_not_be_available_to_selector")
    _require(record.get("selected_j0_state_key") != record.get("selected_s1_state_key"), "s1_target_must_not_equal_j0_target")
    _require(isinstance(record.get("eligible_pool"), list) and record["eligible_pool"], "specificity_eligible_pool_required")
    _require(record.get("selection_record_hash") == _hash_without(record, "selection_record_hash"), "specificity_selection_hash_mismatch")
    return True


def build_specificity_envelope(
    *,
    condition_id: str,
    state_key: str,
    from_status: str,
    target_source_refs: list[str],
    to_status: str = "unconfirmed",
    delivery_policy: str = DEFAULT_DELIVERY_POLICY,
) -> dict[str, Any]:
    _require(condition_id in (S1, S2), "specificity_envelope_condition_invalid")
    _as_nonempty_str(state_key, "specificity_envelope_state_key_required")
    _as_nonempty_str(from_status, "specificity_envelope_from_status_required")
    _as_nonempty_str(to_status, "specificity_envelope_to_status_required")
    _as_nonempty_str(delivery_policy, "specificity_envelope_delivery_policy_required")
    _require(isinstance(target_source_refs, list) and target_source_refs, "specificity_target_source_refs_required")
    identity = RESEARCH_IDENTITY_S1 if condition_id == S1 else RESEARCH_IDENTITY_S2
    row = {
        "schema": SPECIFICITY_ENVELOPE_SCHEMA,
        "version": "0.1",
        "condition_id": condition_id,
        "research_identity": identity,
        "mechanical_primitive": MECHANICAL_PRIMITIVE,
        "state_key": state_key,
        "target_source_refs": list(target_source_refs),
        "from_status": from_status,
        "to_status": to_status,
        "delivery_policy": delivery_policy,
        "temporal_scope": "ONE_EXPOSURE_ONLY",
        "direct_exposure_limit": 1,
        "persistent_state_mutation": False,
        "experiment_origin_reinjection_forbidden": True,
        "opposite_factual_claim_supplied": False,
        "replacement_answer_supplied": False,
        "terminal_answer_target_supplied": False,
        "provenance": "EXPERIMENT_ORIGIN",
    }
    row["envelope_hash"] = _hash_without(row, "envelope_hash")
    verify_specificity_envelope(row)
    return row


def verify_specificity_envelope(row: Mapping[str, Any]) -> bool:
    _require(row.get("schema") == SPECIFICITY_ENVELOPE_SCHEMA, "specificity_envelope_schema_invalid")
    _require(row.get("condition_id") in (S1, S2), "specificity_envelope_condition_invalid")
    expected_identity = RESEARCH_IDENTITY_S1 if row.get("condition_id") == S1 else RESEARCH_IDENTITY_S2
    _require(row.get("research_identity") == expected_identity, "specificity_research_identity_invalid")
    _require(row.get("mechanical_primitive") == MECHANICAL_PRIMITIVE, "specificity_mechanical_primitive_invalid")
    _require(row.get("direct_exposure_limit") == 1, "specificity_direct_exposure_limit_invalid")
    _require(row.get("temporal_scope") == "ONE_EXPOSURE_ONLY", "specificity_temporal_scope_invalid")
    _require(row.get("persistent_state_mutation") is False, "specificity_persistent_mutation_forbidden")
    _require(row.get("experiment_origin_reinjection_forbidden") is True, "specificity_reinjection_must_be_forbidden")
    _require(row.get("opposite_factual_claim_supplied") is False, "specificity_opposite_fact_forbidden")
    _require(row.get("replacement_answer_supplied") is False, "specificity_replacement_answer_forbidden")
    _require(row.get("terminal_answer_target_supplied") is False, "specificity_terminal_target_forbidden")
    _require(row.get("provenance") == "EXPERIMENT_ORIGIN", "specificity_provenance_invalid")
    _require(row.get("envelope_hash") == _hash_without(row, "envelope_hash"), "specificity_envelope_hash_mismatch")
    return True


class SpecificityOneShotRuntimeViewTransform:
    """Apply one copied-view factual-status downgrade and never mutate Arena state."""

    def __init__(self, envelope: Mapping[str, Any]):
        verify_specificity_envelope(envelope)
        self.envelope = copy.deepcopy(dict(envelope))
        self.delivery_records: list[dict[str, Any]] = []

    @property
    def delivered_count(self) -> int:
        return len(self.delivery_records)

    def __call__(self, *, actor: str, turn: int, runtime_view: Mapping[str, Any]):
        view = copy.deepcopy(dict(runtime_view))
        if self.delivered_count:
            return view, None
        metadata = view.get("shared_state_metadata")
        _require(isinstance(metadata, dict), "specificity_runtime_shared_state_metadata_required")
        key = self.envelope["state_key"]
        _require(key in metadata and isinstance(metadata[key], dict), "specificity_runtime_target_metadata_missing")
        observed_from = metadata[key].get("status")
        _require(observed_from == self.envelope["from_status"], "specificity_runtime_from_status_mismatch")
        before_hash = stable_hash(view)
        metadata[key] = copy.deepcopy(metadata[key])
        metadata[key]["status"] = self.envelope["to_status"]
        after_hash = stable_hash(view)
        _require(before_hash != after_hash, "specificity_runtime_overlay_must_change_view")
        record = {
            "schema": SPECIFICITY_DELIVERY_SCHEMA,
            "version": "0.1",
            "condition_id": self.envelope["condition_id"],
            "research_identity": self.envelope["research_identity"],
            "mechanical_primitive": self.envelope["mechanical_primitive"],
            "envelope_hash": self.envelope["envelope_hash"],
            "actor": actor,
            "turn": int(turn),
            "state_key": key,
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
            "condition_id": self.envelope["condition_id"],
            "research_identity": self.envelope["research_identity"],
            "envelope_hash": self.envelope["envelope_hash"],
            "direct_experiment_origin_exposure_count": self.delivered_count,
            "consumed": self.delivered_count == 1,
            "experiment_origin_reinjection_count": 0,
            "persistent_state_mutation": False,
            "delivery_record_hashes": [x["delivery_hash"] for x in self.delivery_records],
        }

    def verify_finished(self) -> bool:
        _require(self.delivered_count == 1, "specificity_exactly_one_delivery_required")
        return True


def build_specificity_plan(
    *,
    selection_record: Mapping[str, Any],
    j0_source_refs: list[str],
    to_status: str = "unconfirmed",
    delivery_policy: str = DEFAULT_DELIVERY_POLICY,
    observation_policy_id: str = "MATCHED_POST_CONSUMPTION_HORIZON_v1",
    post_consumption_turn_cap: int = 8,
    replicates: int = 1,
    code_identity: Mapping[str, Any] | None = None,
    model_identity: Mapping[str, Any] | None = None,
    config_identity: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    verify_field_selection_record(selection_record)
    _require(isinstance(j0_source_refs, list) and j0_source_refs, "j0_source_refs_required")
    _require(isinstance(post_consumption_turn_cap, int) and post_consumption_turn_cap >= 1, "post_consumption_turn_cap_invalid")
    _require(isinstance(replicates, int) and replicates >= 1, "specificity_replicates_invalid")

    s1 = build_specificity_envelope(
        condition_id=S1,
        state_key=selection_record["selected_s1_state_key"],
        from_status=selection_record["selected_s1_pre_status"],
        target_source_refs=selection_record["selected_s1_source_refs"],
        to_status=to_status,
        delivery_policy=delivery_policy,
    )
    s2 = build_specificity_envelope(
        condition_id=S2,
        state_key=selection_record["selected_j0_state_key"],
        from_status=selection_record["selected_j0_pre_status"],
        target_source_refs=j0_source_refs,
        to_status=to_status,
        delivery_policy=delivery_policy,
    )

    plan = {
        "schema": SPECIFICITY_PLAN_SCHEMA,
        "version": "0.1",
        "scientific_status": "PREPARED_ONLY_NO_SUBJECT_OUTCOMES",
        "source_binding": {
            "source_trace_hash": selection_record["source_trace_hash"],
            "source_evidence_hash": selection_record["source_evidence_hash"],
            "common_parent_state_hash": selection_record["common_parent_state_hash"],
            "selected_j0_candidate_id": selection_record["selected_j0_candidate_id"],
            "selected_j0_event_ref": selection_record["selected_j0_event_ref"],
            "selected_j0_state_key": selection_record["selected_j0_state_key"],
            "selected_j0_pre_status": selection_record["selected_j0_pre_status"],
        },
        "field_selection": {
            "contract_schema": "RB-R5R6-SPECIFICITY-FIELD-SELECTION-CONTRACT-v0.1",
            "eligible_pool_hash": selection_record["eligible_pool_hash"],
            "selection_rule_hash": selection_record["selection_rule_hash"],
            "selection_record_hash": selection_record["selection_record_hash"],
            "selected_s1_state_key": selection_record["selected_s1_state_key"],
            "selected_s1_target_hash": selection_record["selected_s1_target_hash"],
            "outcome_blind_attestation": True,
        },
        "mechanical_primitive": {
            "id": MECHANICAL_PRIMITIVE,
            "to_status": to_status,
            "delivery_policy": delivery_policy,
            "direct_exposure_limit": 1,
            "persistent_state_mutation": False,
            "reinjection_forbidden": True,
        },
        "conditions": list(CONDITIONS),
        "condition_specs": {
            S0: {"research_identity": "R5R6_S0_NATURAL_REFERENCE", "experiment_origin_exposure_count": 0},
            S1: {"research_identity": RESEARCH_IDENTITY_S1, "envelope_hash": s1["envelope_hash"], "target_state_key": s1["state_key"]},
            S2: {"research_identity": RESEARCH_IDENTITY_S2, "envelope_hash": s2["envelope_hash"], "target_state_key": s2["state_key"]},
        },
        "contrasts": {
            "generic_uncertainty": "S1_MINUS_S0",
            "total_j0_targeted": "S2_MINUS_S0",
            "primary_target_specificity": "S2_MINUS_S1",
        },
        "measurement_contract": "RB-PROCESS-REALITY-MEASUREMENT-CONTRACT-v0.7",
        "observation_horizon": {
            "policy_id": observation_policy_id,
            "post_consumption_turn_cap": post_consumption_turn_cap,
            "natural_early_termination_is_censoring": True,
        },
        "replicates": replicates,
        "execution_order_policy": "ROTATE_S0_S1_S2_BY_REPLICATE_INDEX",
        "namespace_guard": {"specificity_namespace": "S", "r7_namespace": "C", "aliasing_forbidden": True},
        "model_identity": copy.deepcopy(dict(model_identity or {})),
        "config_identity": copy.deepcopy(dict(config_identity or {})),
        "code_identity": copy.deepcopy(dict(code_identity or {})),
        "authorization_status": "NOT_AUTHORIZED",
        "paid_evaluator_authorized": False,
        "semantic_cpr_status": "NOT_ADJUDICATED",
        "provider_internal_state_replayed": False,
    }
    plan["plan_hash"] = _hash_without(plan, "plan_hash")
    bundle = {"plan": plan, "selection_record": copy.deepcopy(dict(selection_record)), "s1_envelope": s1, "s2_envelope": s2}
    verify_specificity_plan(bundle)
    return bundle


def verify_specificity_plan(bundle: Mapping[str, Any]) -> bool:
    plan = bundle.get("plan")
    _require(isinstance(plan, Mapping), "specificity_plan_required")
    _require(plan.get("schema") == SPECIFICITY_PLAN_SCHEMA, "specificity_plan_schema_invalid")
    _require(plan.get("conditions") == list(CONDITIONS), "specificity_conditions_invalid")
    _require(plan.get("authorization_status") == "NOT_AUTHORIZED", "specificity_plan_must_not_self_authorize")
    _require(plan.get("paid_evaluator_authorized") is False, "specificity_paid_evaluator_must_be_off")
    _require(plan.get("semantic_cpr_status") == "NOT_ADJUDICATED", "specificity_semantic_status_invalid")
    _require(plan.get("provider_internal_state_replayed") is False, "specificity_hidden_state_replay_claim_forbidden")
    _require(plan.get("namespace_guard", {}).get("aliasing_forbidden") is True, "specificity_namespace_aliasing_must_be_forbidden")
    _require(plan.get("plan_hash") == _hash_without(plan, "plan_hash"), "specificity_plan_hash_mismatch")
    verify_field_selection_record(bundle["selection_record"])
    verify_specificity_envelope(bundle["s1_envelope"])
    verify_specificity_envelope(bundle["s2_envelope"])
    _require(bundle["s1_envelope"]["state_key"] != bundle["s2_envelope"]["state_key"], "specificity_s1_s2_targets_must_differ")
    for field in ("to_status", "delivery_policy", "direct_exposure_limit", "persistent_state_mutation", "experiment_origin_reinjection_forbidden"):
        _require(bundle["s1_envelope"][field] == bundle["s2_envelope"][field], f"specificity_s1_s2_mechanics_mismatch:{field}")
    return True


def rotated_condition_order(replicate_index: int) -> tuple[str, str, str]:
    _require(isinstance(replicate_index, int) and replicate_index >= 1, "replicate_index_invalid")
    shift = (replicate_index - 1) % 3
    order = CONDITIONS[shift:] + CONDITIONS[:shift]
    return order
