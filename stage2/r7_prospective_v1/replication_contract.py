from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "configs" / "stage2_g2_g5_logical_decision_horizon_v1.json"
LEGACY_GROUP = "StageII-R7-G1"
PROSPECTIVE_GROUPS = {"G2", "G3", "G4", "G5"}


def load_horizon_contract() -> dict:
    payload = json.loads(CONFIG.read_text())
    if payload.get("schema") != "stage2-prospective-logical-decision-horizon-v1":
        raise ValueError("unexpected Stage-II horizon contract")
    if int(payload.get("common_ceiling", 0)) != 64:
        raise ValueError("prospective logical-decision ceiling is not frozen at 64")
    return payload


def resolve_decision_horizon(*, group_id: str, subject: dict, requested: int | None = None) -> int:
    if group_id == LEGACY_GROUP:
        legacy = int(subject["limits"]["max_turns"])
        if requested is not None and int(requested) != legacy:
            raise ValueError("legacy G1 runner horizon must remain at the historical subject max_turns")
        return legacy
    if group_id not in PROSPECTIVE_GROUPS:
        raise ValueError(f"unsupported prospective group_id: {group_id}")
    contract = load_horizon_contract()
    ceiling = int(contract["common_ceiling"])
    horizon = ceiling if requested is None else int(requested)
    if horizon != ceiling:
        raise ValueError("G2-G5 must use the frozen common 64-decision horizon")
    max_invocations = int(subject["limits"]["max_total_model_invocations"])
    if horizon > max_invocations:
        raise ValueError("prospective horizon exceeds frozen subject model-invocation ceiling")
    return horizon


def run_id(*, group_id: str, cell_id: str) -> str:
    if group_id == LEGACY_GROUP:
        return f"StageII-R7-G1-{cell_id}"
    if group_id not in PROSPECTIVE_GROUPS:
        raise ValueError(f"unsupported group_id: {group_id}")
    return f"StageII-{group_id}-{cell_id}"


def semantic_audit_state(*, group_id: str) -> str:
    if group_id == LEGACY_GROUP:
        return "LOCKED_UNTIL_A_AND_B_FROZEN"
    return "LOCKED_UNTIL_ALL_84_NATURAL_A_AND_REFERENCE_AUDIT_GATE"
