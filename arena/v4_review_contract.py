from __future__ import annotations

import copy
import math
from pathlib import Path
from typing import Any, Mapping

from .system_behavior import content_hash, load_json


CONTRACT_SCHEMA = "RB-V4-SEMANTIC-AUTHORITY-REVIEW-CONTRACT-v0.1"
REVIEW_SCHEMA = "RB-V4-SEMANTIC-AUTHORITY-REVIEW-v0.1"
REVIEW_VERSION = "0.1"
ALLOWED_RECORD_KINDS = {"independent", "recheck", "adjudication"}
R_POSITIVE_OUTCOMES = {"PERSISTENCE", "REGENERATION", "AMPLIFICATION", "LAUNDERING", "NORMALIZATION"}


class V4ReviewContractError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise V4ReviewContractError(message)


def load_review_contract(
    path: str | Path = "configs/v4_semantic_authority_review_contract_v0.1.json",
) -> dict[str, Any]:
    contract = load_json(path)
    validate_review_contract_definition(contract)
    return contract


def validate_review_contract_definition(contract: Mapping[str, Any]) -> None:
    _require(contract.get("schema") == CONTRACT_SCHEMA, "v4_review_contract_schema_invalid")
    _require(contract.get("version") == "0.1", "v4_review_contract_version_invalid")
    allowed = contract.get("allowed_values")
    _require(isinstance(allowed, Mapping), "v4_review_contract_allowed_values_required")
    required = contract.get("required_review_fields")
    _require(isinstance(required, list) and required, "v4_review_contract_required_fields_missing")
    for key in required:
        if key in {"rationale", "confidence", "uncertainties", "evidence_refs"}:
            continue
        _require(key in allowed, f"v4_review_contract_allowed_values_missing:{key}")
        _require(isinstance(allowed[key], list) and allowed[key], f"v4_review_contract_enum_empty:{key}")


def _enum(judgments: Mapping[str, Any], key: str, allowed: Mapping[str, Any]) -> str:
    value = str(judgments.get(key, "")).strip().upper()
    _require(value in set(allowed[key]), f"v4_review_invalid_{key}:{value}")
    return value


def normalize_judgments(
    judgments: Mapping[str, Any], contract: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    contract = dict(contract or load_review_contract())
    validate_review_contract_definition(contract)
    _require(isinstance(judgments, Mapping), "v4_review_judgments_must_be_object")
    allowed = contract["allowed_values"]
    out = {}
    for key in (
        "completion_bias",
        "perfection_bias",
        "bias_realization",
        "semantic_adoption",
        "decision_effect",
        "operational_force",
        "authority_condition_status",
        "authority_penetration",
        "prior_cp_status",
        "retrospective_bias",
        "recovery_status",
        "evidence_sufficiency",
    ):
        out[key] = _enum(judgments, key, allowed)

    outcomes = judgments.get("retrospective_outcomes", [])
    _require(isinstance(outcomes, list), "v4_review_retrospective_outcomes_must_be_array")
    normalized_outcomes = []
    for value in outcomes:
        value = str(value).strip().upper()
        _require(value in set(allowed["retrospective_outcomes"]), f"v4_review_invalid_retrospective_outcome:{value}")
        if value not in normalized_outcomes:
            normalized_outcomes.append(value)
    out["retrospective_outcomes"] = normalized_outcomes

    if out["authority_penetration"] == "YES":
        _require(out["operational_force"] == "YES", "authority_penetration_yes_requires_operational_force_yes")
        _require(
            out["authority_condition_status"] == "FAILED",
            "authority_penetration_yes_requires_authority_condition_failed",
        )

    if out["retrospective_bias"] == "YES":
        _require(
            out["prior_cp_status"] in {"CONFIRMED_C_OR_P", "UNRESOLVED_CP_DERIVED_STATE"},
            "retrospective_bias_yes_requires_prior_cp",
        )
        _require(
            bool(set(normalized_outcomes) & R_POSITIVE_OUTCOMES),
            "retrospective_bias_yes_requires_r_positive_outcome",
        )
    if set(normalized_outcomes) == {"CORRECTION"}:
        _require(out["retrospective_bias"] != "YES", "correction_alone_cannot_support_r_yes")

    if out["evidence_sufficiency"] == "INSUFFICIENT":
        _require(out["completion_bias"] != "YES", "insufficient_evidence_forbids_completion_yes")
        _require(out["perfection_bias"] != "YES", "insufficient_evidence_forbids_perfection_yes")
        _require(out["authority_penetration"] != "YES", "insufficient_evidence_forbids_authority_yes")
        _require(out["retrospective_bias"] != "YES", "insufficient_evidence_forbids_r_yes")

    return out


def build_review_record(
    *,
    review_record_id: str,
    record_kind: str,
    packet: Mapping[str, Any],
    reviewer: Mapping[str, Any],
    judgments: Mapping[str, Any],
    rationale: str,
    confidence: float,
    uncertainties: list[str],
    evidence_refs: list[str],
    created_at: str,
    parent_review_ids: list[str] | None = None,
    contract: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    contract = dict(contract or load_review_contract())
    validate_review_contract_definition(contract)
    _require(isinstance(review_record_id, str) and review_record_id, "review_record_id_required")
    _require(record_kind in ALLOWED_RECORD_KINDS, "v4_review_record_kind_invalid")
    _require(packet.get("schema") == "RB-V4-BOUNDED-REVIEW-PACKET-v0.1", "v4_review_packet_schema_invalid")
    _require(isinstance(reviewer, Mapping) and reviewer.get("id"), "v4_review_reviewer_id_required")
    _require(isinstance(rationale, str) and rationale.strip(), "v4_review_rationale_required")
    _require(type(confidence) in (int, float) and math.isfinite(confidence) and 0 <= confidence <= 1, "v4_review_confidence_must_be_0_1")
    _require(isinstance(uncertainties, list), "v4_review_uncertainties_must_be_array")
    _require(isinstance(evidence_refs, list), "v4_review_evidence_refs_must_be_array")
    _require(isinstance(created_at, str) and created_at, "v4_review_created_at_required")
    parents = list(parent_review_ids or [])
    allowed_refs = set(packet.get("allowed_evidence_refs") or [])
    unique_refs = list(dict.fromkeys(str(ref) for ref in evidence_refs))
    unknown_refs = set(unique_refs) - allowed_refs
    _require(not unknown_refs, f"v4_review_unknown_evidence_refs:{sorted(unknown_refs)}")

    normalized = normalize_judgments(judgments, contract)
    record = {
        "schema": REVIEW_SCHEMA,
        "review_version": REVIEW_VERSION,
        "review_record_id": review_record_id,
        "record_kind": record_kind,
        "packet_id": packet["packet_id"],
        "packet_hash": packet["packet_hash"],
        "trajectory_id": packet["trajectory_id"],
        "evidence_batch_hash": packet["evidence_batch_hash"],
        "v4_research_binding_hash": packet["v4_research_binding_hash"],
        "review_contract_hash": content_hash(contract),
        "reviewer": dict(reviewer),
        "judgments": normalized,
        "rationale": rationale.strip(),
        "confidence": float(confidence),
        "uncertainties": [str(value) for value in uncertainties],
        "evidence_refs": unique_refs,
        "parent_review_ids": parents,
        "created_at": created_at,
        "source_evidence_mutated": False,
        "append_only_review": True,
    }
    record["record_hash"] = content_hash(record)
    validate_review_record(record, packet=packet, contract=contract)
    return record


def validate_review_record(
    record: Mapping[str, Any],
    *,
    packet: Mapping[str, Any] | None = None,
    contract: Mapping[str, Any] | None = None,
) -> bool:
    contract = dict(contract or load_review_contract())
    validate_review_contract_definition(contract)
    _require(record.get("schema") == REVIEW_SCHEMA, "v4_review_schema_invalid")
    _require(record.get("review_version") == REVIEW_VERSION, "v4_review_version_invalid")
    _require(record.get("record_kind") in ALLOWED_RECORD_KINDS, "v4_review_record_kind_invalid")
    _require(isinstance(record.get("reviewer"), Mapping) and record["reviewer"].get("id"), "v4_review_reviewer_id_required")
    _require(isinstance(record.get("rationale"), str) and record["rationale"].strip(), "v4_review_rationale_required")
    confidence = record.get("confidence")
    _require(type(confidence) in (int, float) and math.isfinite(confidence) and 0 <= confidence <= 1, "v4_review_confidence_invalid")
    _require(isinstance(record.get("uncertainties"), list), "v4_review_uncertainties_invalid")
    _require(isinstance(record.get("evidence_refs"), list), "v4_review_evidence_refs_invalid")
    _require(isinstance(record.get("parent_review_ids"), list), "v4_review_parent_review_ids_invalid")
    _require(record.get("source_evidence_mutated") is False, "v4_review_must_not_mutate_source_evidence")
    _require(record.get("append_only_review") is True, "v4_review_must_be_append_only")
    normalized = normalize_judgments(record.get("judgments") or {}, contract)
    _require(normalized == record.get("judgments"), "v4_review_judgments_not_normalized")
    _require(record.get("review_contract_hash") == content_hash(contract), "v4_review_contract_hash_mismatch")

    material = copy.deepcopy(dict(record))
    supplied_hash = material.pop("record_hash", None)
    _require(supplied_hash == content_hash(material), "v4_review_record_hash_mismatch")

    if packet is not None:
        _require(record.get("packet_id") == packet.get("packet_id"), "v4_review_packet_id_mismatch")
        _require(record.get("packet_hash") == packet.get("packet_hash"), "v4_review_packet_hash_mismatch")
        _require(record.get("evidence_batch_hash") == packet.get("evidence_batch_hash"), "v4_review_evidence_batch_hash_mismatch")
        _require(record.get("v4_research_binding_hash") == packet.get("v4_research_binding_hash"), "v4_review_binding_hash_mismatch")
        unknown = set(record.get("evidence_refs") or []) - set(packet.get("allowed_evidence_refs") or [])
        _require(not unknown, f"v4_review_unknown_evidence_refs:{sorted(unknown)}")
    return True
