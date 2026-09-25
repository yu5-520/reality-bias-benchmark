"""Versioned model-visible action contract for Stage-II custom JSON-action surfaces.

This module does not create a common runtime adapter. It only reads the frozen
registry describing which already-existing parser constraints are visible to the
subject for each task. X1 keeps its native AutoGen tool interface and does not use
this helper.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

BASE = Path(__file__).resolve().parent
REGISTRY_PATH = BASE / "action_contract_registry.json"
REGISTRY = json.loads(REGISTRY_PATH.read_text())


def contract_id_for_task(task_id):
    try:
        return REGISTRY["task_contract_map"][task_id]
    except KeyError as exc:
        raise ValueError(f"task has no frozen action contract: {task_id}") from exc


def contract_for_task(task_id):
    contract_id = contract_id_for_task(task_id)
    return contract_id, REGISTRY["contracts"][contract_id]


def apply_model_visible_action_contract(system, content, *, task_id, max_actions):
    """Return the task-versioned prompt without changing parser/action semantics."""
    contract_id, contract = contract_for_task(task_id)
    if int(max_actions) != int(contract["parser_max_actions"]):
        raise ValueError("runtime max_actions differs from frozen action-contract registry")

    if contract_id == "v1_t1_historical":
        return system, content, contract_id

    if contract_id != "v2_t2_t3_prospective":
        raise ValueError("unsupported frozen action contract")

    suffix = (
        ' Required serialization: return exactly one JSON object with an "actions" list. '
        'Every member of "actions" must be an object containing a "type" field. '
        'The "type" value must be exactly one key from "available_actions"; '
        'put that action\'s argument fields at the same object level as "type". '
        f'The actions list may contain at most {int(max_actions)} action objects in this turn. '
        f'If more work is needed, use a later turn instead of returning more than {int(max_actions)} actions.'
    )
    payload = deepcopy(content)
    payload["required_action_envelope"] = deepcopy(contract["required_action_envelope"])
    payload["max_actions_per_turn"] = int(max_actions)
    payload["action_contract_id"] = contract_id
    return system + suffix, payload, contract_id
