from __future__ import annotations

import copy
from typing import Any, Mapping

from .core import stable_hash

S2 = "S2_J0_TARGETED_ESCAPE_DERIVED_AUTHORITY_WITHDRAWAL"
S3 = "S3_MATCHED_ORDINARY_STOCK_B_DOWNGRADE"
S4 = "S4_MATCHED_ORDINARY_STOCK_C_DOWNGRADE"
CONDITIONS = [S2, S3, S4]

ATOMIC_ENVELOPE_SCHEMA = "RB-R5R6-ATOMIC-EPISTEMIC-ANNOTATION-v0.2"
ATOMIC_DELIVERY_SCHEMA = "RB-R6D-MATCHED-STOCK-ATOMIC-EPISTEMIC-ANNOTATION-DELIVERY-v0.1"
MECHANICAL_PRIMITIVE = "ONE_SHOT_TARGET_SCOPED_EPISTEMIC_STATUS_ANNOTATION"
PROMPT_VISIBLE_FIELD = "epistemic_annotations"
FROM_STATUS = "fact"
TO_STATUS = "unconfirmed"

RESEARCH_IDENTITIES = {
    S2: "R5R6_S2_J0_ESCAPE_DERIVED_ATOMIC_FACT",
    S3: "R6D_ROBUSTNESS_S3_MATCHED_ORDINARY_STOCK_B",
    S4: "R6D_ROBUSTNESS_S4_MATCHED_ORDINARY_STOCK_C",
}


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def _hash_without(row: Mapping[str, Any], key: str) -> str:
    material = copy.deepcopy(dict(row))
    material.pop(key, None)
    return stable_hash(material)


def verify_envelope(row: Mapping[str, Any]) -> bool:
    _require(row.get("schema") == ATOMIC_ENVELOPE_SCHEMA, "matched_atomic_schema_invalid")
    condition = row.get("condition_id")
    _require(condition in CONDITIONS, "matched_atomic_condition_invalid")
    _require(row.get("research_identity") == RESEARCH_IDENTITIES[condition], "matched_atomic_research_identity_invalid")
    _require(row.get("mechanical_primitive") == MECHANICAL_PRIMITIVE, "matched_atomic_mechanical_primitive_invalid")
    _require(row.get("from_status") == FROM_STATUS and row.get("to_status") == TO_STATUS, "matched_atomic_status_transition_invalid")
    _require(row.get("prompt_visible_field") == PROMPT_VISIBLE_FIELD, "matched_atomic_prompt_field_invalid")
    annotation = row.get("prompt_visible_annotation")
    _require(isinstance(annotation, Mapping), "matched_atomic_annotation_required")
    _require(set(annotation) == {"target_locator", "epistemic_status"}, "matched_atomic_annotation_must_be_minimal")
    _require(annotation.get("target_locator") == row.get("target_locator"), "matched_atomic_target_mismatch")
    _require(annotation.get("epistemic_status") == TO_STATUS, "matched_atomic_annotation_status_invalid")
    _require(row.get("temporal_scope") == "ONE_EXPOSURE_ONLY", "matched_atomic_temporal_scope_invalid")
    _require(row.get("direct_exposure_limit") == 1, "matched_atomic_exposure_limit_invalid")
    _require(row.get("persistent_state_mutation") is False, "matched_atomic_persistent_mutation_forbidden")
    _require(row.get("experiment_origin_reinjection_forbidden") is True, "matched_atomic_reinjection_guard_missing")
    _require(row.get("original_target_value_mutation") is False, "matched_atomic_original_value_mutation_forbidden")
    _require(row.get("opposite_fact_supplied") is False, "matched_atomic_opposite_fact_forbidden")
    _require(row.get("replacement_conclusion_supplied") is False, "matched_atomic_replacement_conclusion_forbidden")
    _require(row.get("desired_terminal_answer_supplied") is False, "matched_atomic_terminal_target_forbidden")
    _require(row.get("provenance") == "EXPERIMENT_ORIGIN", "matched_atomic_provenance_invalid")
    _require(row.get("envelope_hash") == _hash_without(row, "envelope_hash"), "matched_atomic_envelope_hash_mismatch")
    return True


def mechanically_equivalent(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    verify_envelope(left)
    verify_envelope(right)
    fields = (
        "schema",
        "version",
        "mechanical_primitive",
        "from_status",
        "to_status",
        "prompt_visible_field",
        "temporal_scope",
        "direct_exposure_limit",
        "persistent_state_mutation",
        "experiment_origin_reinjection_forbidden",
        "original_target_value_mutation",
        "opposite_fact_supplied",
        "replacement_conclusion_supplied",
        "desired_terminal_answer_supplied",
        "provenance",
    )
    for field in fields:
        _require(left.get(field) == right.get(field), "matched_atomic_mechanical_mismatch:" + field)
    _require(left.get("target_locator") != right.get("target_locator"), "matched_atomic_targets_must_differ")
    return True


class MatchedStockAtomicEpistemicAnnotationTransform:
    def __init__(self, envelope: Mapping[str, Any]):
        verify_envelope(envelope)
        self.envelope = copy.deepcopy(dict(envelope))
        self.delivery_records: list[dict[str, Any]] = []

    @property
    def delivered_count(self) -> int:
        return len(self.delivery_records)

    def __call__(self, *, actor: str, turn: int, runtime_view: Mapping[str, Any]):
        view = copy.deepcopy(dict(runtime_view))
        if self.delivered_count:
            return view, None
        _require(PROMPT_VISIBLE_FIELD not in view, "matched_atomic_existing_annotations_forbidden")
        before_hash = stable_hash(view)
        annotation = copy.deepcopy(self.envelope["prompt_visible_annotation"])
        view[PROMPT_VISIBLE_FIELD] = [annotation]
        after_hash = stable_hash(view)
        _require(before_hash != after_hash, "matched_atomic_overlay_must_change_copied_view")
        record = {
            "schema": ATOMIC_DELIVERY_SCHEMA,
            "version": "0.1",
            "condition_id": self.envelope["condition_id"],
            "research_identity": self.envelope["research_identity"],
            "mechanical_primitive": self.envelope["mechanical_primitive"],
            "envelope_hash": self.envelope["envelope_hash"],
            "actor": actor,
            "turn": int(turn),
            "target_locator": self.envelope["target_locator"],
            "original_value_hash": self.envelope["original_value_hash"],
            "from_status": FROM_STATUS,
            "to_status": TO_STATUS,
            "prompt_visible_delta_path": f"{PROMPT_VISIBLE_FIELD}[0]",
            "prompt_visible_annotation": annotation,
            "runtime_view_before_hash": before_hash,
            "runtime_view_after_hash": after_hash,
            "direct_experiment_origin_exposure_index": 1,
            "consumed_after_delivery": True,
            "persistent_state_mutation": False,
            "experiment_origin_reinjection_count": 0,
            "original_target_value_mutation": False,
        }
        record["delivery_hash"] = _hash_without(record, "delivery_hash")
        self.delivery_records.append(copy.deepcopy(record))
        return view, record

    def verify_finished(self) -> bool:
        _require(self.delivered_count == 1, "matched_atomic_exactly_one_delivery_required")
        return True

    def summary(self) -> dict[str, Any]:
        return {
            "condition_id": self.envelope["condition_id"],
            "research_identity": self.envelope["research_identity"],
            "target_locator": self.envelope["target_locator"],
            "envelope_hash": self.envelope["envelope_hash"],
            "direct_experiment_origin_exposure_count": self.delivered_count,
            "consumed": self.delivered_count == 1,
            "experiment_origin_reinjection_count": 0,
            "persistent_state_mutation": False,
            "original_target_value_mutation": False,
            "delivery_record_hashes": [x["delivery_hash"] for x in self.delivery_records],
        }
