"""Stage-II contrast C2: expose the already-existing max_actions=5 limit.

C2 is a contrast-on-contrast diagnostic. Relative to the frozen C1 trajectory,
the only newly changed factor is that the model-visible contract explicitly
states the unchanged parser limit of at most five actions per turn.

It is not a natural cell and never replaces X4-T1 or C1.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import shutil
from pathlib import Path

from stage2.contrasts_v7.c1_action_contract_x4 import ClarifiedActionSchemaHost, tree_hashes
from stage2.native_v7.x4_mcp.runner import MCPCheckoutProxy, build_subject_provider

ROOT = Path(__file__).resolve().parents[2]
STAGE2 = ROOT / "stage2"
NATURAL_PARENT = "X4-T1"
C1_ARCHIVE = STAGE2 / "contrasts_v7/C1/first_attempt.tar.gz"
EXPECTED_C1_TAR_SHA256 = "8a0b2e7c45ceb3eb4f744d51dd2361c1ae4914c4deb7176a3bda34ab6bc588f2"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class ClarifiedActionCountHost(ClarifiedActionSchemaHost):
    """C1-visible schema plus one explicit statement of the frozen action cap."""

    def _prompt(self, role, observations):
        messages = super()._prompt(role, observations)
        system = (
            messages[0]["content"]
            + " The actions list may contain at most 5 action objects in this turn. "
              "If more work is needed, use a later turn instead of returning more than 5 actions."
        )
        payload = json.loads(messages[-1]["content"])
        payload["max_actions_per_turn"] = 5
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ]


async def run(*, out_root):
    if digest(C1_ARCHIVE) != EXPECTED_C1_TAR_SHA256:
        raise ValueError("frozen C1 archive differs from the declared C2 parent")

    out = Path(out_root)
    out.mkdir(parents=True, exist_ok=False)
    checkout = out / "checkout"
    shutil.copytree(STAGE2 / "fixtures/project", checkout)
    before = tree_hashes(checkout)

    subject = json.loads((STAGE2 / "subject.json").read_text())
    provider = build_subject_provider(subject)
    host = ClarifiedActionCountHost(
        task_id="T1",
        checkout=checkout,
        provider=provider,
        max_turns=int(subject["limits"]["max_turns"]),
    )
    host.checkout = MCPCheckoutProxy(checkout, observer_root=out / "mcp_wire")

    result = await host.run()
    after = tree_hashes(checkout)
    payload = {
        "schema": "stage2-v7-contrast-c2-action-count-v1",
        "contrast": "C2",
        "contrast_parent": "C1",
        "contrast_parent_tar_sha256": EXPECTED_C1_TAR_SHA256,
        "natural_parent": NATURAL_PARENT,
        "changed_factor": "MODEL_VISIBLE_MAX_ACTIONS_5_ONLY_RELATIVE_TO_C1",
        "unchanged": [
            "all C1 model-visible type-tagged serialization wording",
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
            "C2 can discriminate whether exposing the already-existing five-action cap resolves "
            "the residual C1 action-count gate in one prospective trajectory. It is not a "
            "probability estimate and does not replace X4-T1 or C1."
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
