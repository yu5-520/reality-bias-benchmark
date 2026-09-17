from __future__ import annotations

import copy
from typing import Any, Mapping, Sequence

from .core import stable_hash

S0 = "S0_NATURAL_REFERENCE"
S1 = "S1_MATCHED_FACTUAL_FIELD_DOWNGRADE"
S2 = "S2_J0_TARGETED_AUTHORITY_WITHDRAWAL"

ATOMIC_ENVELOPE_SCHEMA = "RB-R5R6-ATOMIC-EPISTEMIC-ANNOTATION-v0.2"
ATOMIC_DELIVERY_SCHEMA = "RB-R5R6-ATOMIC-EPISTEMIC-ANNOTATION-DELIVERY-v0.2"
MECHANICAL_PRIMITIVE = "ONE_SHOT_TARGET_SCOPED_EPISTEMIC_STATUS_ANNOTATION"
PROMPT_VISIBLE_FIELD = "epistemic_annotations"
FROM_STATUS = "fact"
TO_STATUS = "unconfirmed"

RESEARCH_IDENTITIES = {
    S1: "R5R6_S1_ORDINARY_ATOMIC_FACT",
    S2: "R5R6_S2_J0_ESCAPE_DERIVED_ATOMIC_FACT",
}


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def _hash_without(row: Mapping[str, Any], key: str) -> str:
    material = copy.deepcopy(dict(row))
    material.pop(key, None)
    return stable_hash(material)


def _nonempty(value: Any, message: str) -> str:
    _require(isinstance(value, str) and bool(value), message)
    return value


def resolve_locator(root: Mapping[str, Any], locator: str) -> Any:
    """Resolve a dot-separated mapping locator without mutating the source."""
    _nonempty(locator, "atomic_target_locator_required")
    current: Any = root
    for part in locator.split("."):
        _require(isinstance(current, Mapping), f"atomic_locator_non_mapping:{part}")
        _require(part in current, f"atomic_locator_missing:{part}")
        current = current[part]
    return current


def build_atomic_envelope(
    *,
    condition_id: str,
    target_locator: str,
    original_value: Any,
    target_class: str,
    source_refs: Sequence[str],
    source_origin_status: str,
    acquired_status_at_intervention: str = FROM_STATUS,
) -> dict[str, Any]:
    _require(condition_id in (S1, S2), "atomic_condition_invalid")
    _nonempty(target_locator, "atomic_target_locator_required")
    _nonempty(target_class, "atomic_target_class_required")
    _nonempty(source_origin_status, "atomic_source_origin_status_required")
    _require(acquired_status_at_intervention == FROM_STATUS, "atomic_acquired_status_must_be_fact")
    _require(isinstance(source_refs, Sequence) and not isinstance(source_refs, (str, bytes)) and bool(source_refs), "atomic_source_refs_required")
    _require(all(isinstance(x, str) and x for x in source_refs), "atomic_source_refs_invalid")

    row = {
        "schema": ATOMIC_ENVELOPE_SCHEMA,
        "version": "0.2",
        "condition_id": condition_id,
        "research_identity": RESEARCH_IDENTITIES[condition_id],
        "mechanical_primitive": MECHANICAL_PRIMITIVE,
        "target_locator": target_locator,
        "target_class": target_class,
        "original_value_hash": stable_hash(original_value),
        "source_refs": list(source_refs),
        "source_origin_status": source_origin_status,
        "from_status": FROM_STATUS,
        "to_status": TO_STATUS,
        "prompt_visible_field": PROMPT_VISIBLE_FIELD,
        "prompt_visible_annotation": {
            "target_locator": target_locator,
            "epistemic_status": TO_STATUS,
        },
        "temporal_scope": "ONE_EXPOSURE_ONLY",
        "direct_exposure_limit": 1,
        "persistent_state_mutation": False,
        "experiment_origin_reinjection_forbidden": True,
        "original_target_value_mutation": False,
        "opposite_fact_supplied": False,
        "replacement_conclusion_supplied": False,
        "desired_terminal_answer_supplied": False,
        "provenance": "EXPERIMENT_ORIGIN",
    }
    row["envelope_hash"] = _hash_without(row, "envelope_hash")
    verify_atomic_envelope(row)
    return row


def verify_atomic_envelope(row: Mapping[str, Any]) -> bool:
    _require(row.get("schema") == ATOMIC_ENVELOPE_SCHEMA, "atomic_envelope_schema_invalid")
    condition_id = row.get("condition_id")
    _require(condition_id in (S1, S2), "atomic_condition_invalid")
    _require(row.get("research_identity") == RESEARCH_IDENTITIES[condition_id], "atomic_research_identity_invalid")
    _require(row.get("mechanical_primitive") == MECHANICAL_PRIMITIVE, "atomic_mechanical_primitive_invalid")
    _require(row.get("from_status") == FROM_STATUS, "atomic_from_status_invalid")
    _require(row.get("to_status") == TO_STATUS, "atomic_to_status_invalid")
    _require(row.get("prompt_visible_field") == PROMPT_VISIBLE_FIELD, "atomic_prompt_field_invalid")
    annotation = row.get("prompt_visible_annotation")
    _require(isinstance(annotation, Mapping), "atomic_prompt_annotation_required")
    _require(set(annotation) == {"target_locator", "epistemic_status"}, "atomic_prompt_annotation_must_be_minimal")
    _require(annotation.get("target_locator") == row.get("target_locator"), "atomic_prompt_target_mismatch")
    _require(annotation.get("epistemic_status") == TO_STATUS, "atomic_prompt_status_invalid")
    _require(row.get("temporal_scope") == "ONE_EXPOSURE_ONLY", "atomic_temporal_scope_invalid")
    _require(row.get("direct_exposure_limit") == 1, "atomic_exposure_limit_invalid")
    _require(row.get("persistent_state_mutation") is False, "atomic_persistent_mutation_forbidden")
    _require(row.get("experiment_origin_reinjection_forbidden") is True, "atomic_reinjection_must_be_forbidden")
    _require(row.get("original_target_value_mutation") is False, "atomic_original_value_mutation_forbidden")
    _require(row.get("opposite_fact_supplied") is False, "atomic_opposite_fact_forbidden")
    _require(row.get("replacement_conclusion_supplied") is False, "atomic_replacement_conclusion_forbidden")
    _require(row.get("desired_terminal_answer_supplied") is False, "atomic_terminal_target_forbidden")
    _require(row.get("provenance") == "EXPERIMENT_ORIGIN", "atomic_provenance_invalid")
    _require(row.get("envelope_hash") == _hash_without(row, "envelope_hash"), "atomic_envelope_hash_mismatch")
    return True


def verify_target_value(*, root: Mapping[str, Any], locator: str, expected_value: Any) -> bool:
    observed = resolve_locator(root, locator)
    _require(stable_hash(observed) == stable_hash(expected_value), "atomic_target_value_mismatch")
    return True


def mechanically_equivalent(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    """Verify S1/S2 differ only in target/provenance identity, not operator mechanics."""
    verify_atomic_envelope(left)
    verify_atomic_envelope(right)
    mechanical_fields = (
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
    for field in mechanical_fields:
        _require(left.get(field) == right.get(field), f"atomic_mechanical_mismatch:{field}")
    _require(left.get("target_locator") != right.get("target_locator"), "atomic_s1_s2_target_must_differ")
    return True


class AtomicEpistemicAnnotationTransform:
    """Expose exactly one minimal target-scoped epistemic annotation on a copied view."""

    def __init__(self, envelope: Mapping[str, Any]):
        verify_atomic_envelope(envelope)
        self.envelope = copy.deepcopy(dict(envelope))
        self.delivery_records: list[dict[str, Any]] = []

    @property
    def delivered_count(self) -> int:
        return len(self.delivery_records)

    def __call__(self, *, actor: str, turn: int, runtime_view: Mapping[str, Any]):
        view = copy.deepcopy(dict(runtime_view))
        if self.delivered_count:
            return view, None
        _require(PROMPT_VISIBLE_FIELD not in view, "atomic_existing_epistemic_annotations_forbidden")
        before_hash = stable_hash(view)
        annotation = copy.deepcopy(self.envelope["prompt_visible_annotation"])
        view[PROMPT_VISIBLE_FIELD] = [annotation]
        after_hash = stable_hash(view)
        _require(before_hash != after_hash, "atomic_overlay_must_change_copied_view")

        record = {
            "schema": ATOMIC_DELIVERY_SCHEMA,
            "version": "0.2",
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
        _require(self.delivered_count == 1, "atomic_exactly_one_delivery_required")
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
