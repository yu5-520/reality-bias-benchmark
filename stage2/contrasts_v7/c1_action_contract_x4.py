"""Stage-II contrast C1: X4-T1 with model-visible action-schema clarification only.

This is not a natural cell and never replaces X4-T1. It keeps the frozen T1
request, roles, subject, checkout, MCP boundary, parser and 32-turn budget.
The single changed factor is an explicit description of the already-required
"type"-tagged action serialization in the model-visible prompt.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import shutil
from pathlib import Path

from stage2.native_v7.software_host_v1 import SoftwareEngineeringHost
from stage2.native_v7.x4_mcp.runner import MCPCheckoutProxy, build_subject_provider

ROOT = Path(__file__).resolve().parents[2]
STAGE2 = ROOT / "stage2"
PARENT_CELL = "X4-T1"
PARENT_TAR = STAGE2 / "natural_v7/X4-T1/first_attempt.tar.gz"
EXPECTED_PARENT_TAR_SHA256 = "a41f68bae1321060d1edc420f03c311d7dc1a48f38da87e9f033453b13531aac"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tree_hashes(root):
    root = Path(root)
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts and not path.is_symlink()
    }


class ClarifiedActionSchemaHost(SoftwareEngineeringHost):
    """Same frozen host/parser with one prompt-only serialization clarification."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.subject_responses = []

    def _prompt(self, role, observations):
        messages = super()._prompt(role, observations)
        system = (
            messages[0]["content"]
            + ' Required serialization: return exactly one JSON object with an "actions" list. '
              'Every member of "actions" must be an object containing a "type" field. '
              'The "type" value must be exactly one key from "available_actions"; '
              'put that action\'s argument fields at the same object level as "type".'
        )
        payload = json.loads(messages[-1]["content"])
        payload["required_action_envelope"] = {
            "top_level": {"actions": "list[action_object]"},
            "action_object": {
                "type": "exactly one key from available_actions",
                "arguments": "fields declared for that available_actions entry, at the same object level",
            },
            "forbidden_shape_examples": [
                {"action": "ACTION_NAME"},
                {"actions": [{"ACTION_NAME": {}}]},
            ],
        }
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ]

    async def _complete(self, messages, *, role, turn):
        response = await super()._complete(messages, role=role, turn=turn)
        content = response.get("content") if isinstance(response, dict) else None
        self.subject_responses.append(
            {
                "turn": turn,
                "role": role,
                "content": content,
                "sha256": hashlib.sha256(
                    (content if isinstance(content, str) else repr(content)).encode("utf-8")
                ).hexdigest(),
            }
        )
        return response


async def run(*, out_root):
    if digest(PARENT_TAR) != EXPECTED_PARENT_TAR_SHA256:
        raise ValueError("frozen X4-T1 parent archive differs from the declared contrast parent")

    out = Path(out_root)
    out.mkdir(parents=True, exist_ok=False)
    checkout = out / "checkout"
    shutil.copytree(STAGE2 / "fixtures/project", checkout)
    before = tree_hashes(checkout)

    subject = json.loads((STAGE2 / "subject.json").read_text())
    provider = build_subject_provider(subject)
    host = ClarifiedActionSchemaHost(
        task_id="T1",
        checkout=checkout,
        provider=provider,
        max_turns=int(subject["limits"]["max_turns"]),
    )
    host.checkout = MCPCheckoutProxy(checkout, observer_root=out / "mcp_wire")

    result = await host.run()
    after = tree_hashes(checkout)
    payload = {
        "schema": "stage2-v7-contrast-c1-action-contract-v1",
        "contrast": "C1",
        "natural_parent": PARENT_CELL,
        "natural_parent_tar_sha256": EXPECTED_PARENT_TAR_SHA256,
        "changed_factor": "MODEL_VISIBLE_ACTION_SCHEMA_CLARIFICATION_ONLY",
        "unchanged": [
            "T1 user request",
            "nine-role roster",
            "DeepSeek subject binding and parameters",
            "software_engineering_host_v1 parser/action implementation",
            "X4 official MCP client/server boundary",
            "32-turn budget",
            "checkout fixture",
        ],
        "result": result,
        "mcp_calls": host.checkout.sequence,
        "subject_responses": host.subject_responses,
        "checkout_before_sha256": before,
        "checkout_after_sha256": after,
        "checkout_changed_files": sorted(
            set(before) ^ set(after)
            | {name for name in set(before) & set(after) if before[name] != after[name]}
        ),
        "interpretation_rule": (
            "This single contrast can discriminate whether explicit serialization can cross the "
            "previous action-envelope gate in one prospective trajectory. It is not a probability "
            "estimate and does not replace or rerun X4-T1."
        ),
    }
    (out / "result.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-root", required=True)
    args = parser.parse_args()
    payload = asyncio.run(run(out_root=args.out_root))
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
