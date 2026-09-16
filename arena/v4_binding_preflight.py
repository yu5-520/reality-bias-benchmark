from __future__ import annotations

import argparse
import json
from pathlib import Path

from arena.anchor_selection import select_anchor
from arena.branch_plan import build_branch_plan, verify_branch_plan
from arena.engine import run_arena_once
from arena.io_utils import load_json, sha256_file, write_jsonl
from arena.providers import ScriptedProvider
from arena.v4_experiment_binding import prepare_v4_binding


ROOT = Path(__file__).resolve().parents[1]


def _write_plan_dir(path: Path, bundle) -> None:
    path.mkdir(parents=True, exist_ok=False)
    (path / "branch_plan.json").write_text(
        json.dumps(bundle["plan"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (path / "parent_snapshot.json").write_text(
        json.dumps(bundle["parent_snapshot"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (path / "intervention_start_snapshot.json").write_text(
        json.dumps(bundle["intervention_start_snapshot"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_jsonl(path / "branch_execution_manifest.jsonl", bundle["branch_rows"])
    write_jsonl(path / "branch_manifests.jsonl", bundle["branch_manifests"])


def build_fixture_bundle():
    domain_path = ROOT / "arena/domains/ecommerce.json"
    arena_path = ROOT / "arena/config/arena_v0.3.json"
    model_path = ROOT / "arena/config/model_deepseek_v0.2.json"
    rule_path = ROOT / "arena/config/r5r6_anchor_rule_v0.2.json"
    domain = load_json(domain_path)
    arena_config = load_json(arena_path)
    rule = load_json(rule_path)
    anchors = []
    trace = run_arena_once(
        domain,
        arena_config,
        ScriptedProvider([
            {
                "decision_summary": "ask inventory",
                "actions": [
                    {
                        "type": "invoke_agent",
                        "agent_id": "inventory",
                        "request": "Check stock.",
                    }
                ],
            },
            {
                "decision_summary": "write branchable candidate",
                "actions": [
                    {
                        "type": "write_state",
                        "key": "inventory_view",
                        "value": "Stockout certain",
                        "status": "fact",
                        "basis": "v4 binding preflight",
                    },
                    {
                        "type": "message",
                        "to": "ops_lead",
                        "content": "Continue planning from this state.",
                    },
                ],
            },
            {
                "decision_summary": "finish",
                "actions": [{"type": "finalize", "answer": "Plan."}],
            },
            {
                "decision_summary": "finish late",
                "actions": [{"type": "finalize", "answer": "Plan late."}],
            },
        ]),
        "v4-binding-preflight",
        logical_seed=37,
        state_snapshot_callback=anchors.append,
    )
    trace.update({
        "provider": "deepseek",
        "domain_hash": sha256_file(domain_path),
        "arena_config_path": "arena/config/arena_v0.3.json",
        "arena_config_version": arena_config["version"],
        "arena_config_hash": sha256_file(arena_path),
        "model_config_path": "arena/config/model_deepseek_v0.2.json",
        "model_config_version": load_json(model_path).get("config_version"),
        "model_config_hash": sha256_file(model_path),
        "anchor_rule_path": "arena/config/r5r6_anchor_rule_v0.2.json",
        "anchor_rule_hash": sha256_file(rule_path),
        "code_commit_sha": "V4_BINDING_PREFLIGHT_BASELINE",
    })
    selection = select_anchor(
        trace,
        anchors,
        rule,
        evidence_hash="v4-binding-preflight-evidence",
        selection_id="V4-BINDING-PREFLIGHT-SEL",
    )
    if selection.get("selection_status") != "ANCHOR_SELECTED":
        raise RuntimeError("v4_binding_preflight_anchor_not_selected")
    bundle = build_branch_plan(
        selection,
        trace,
        replicates=2,
        branch_code_sha="V4_BINDING_PREFLIGHT_CODE_SHA",
    )
    verify_branch_plan(bundle)
    return bundle


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", default="results/v4_binding_preflight")
    args = parser.parse_args()
    outdir = Path(args.outdir)
    if outdir.exists():
        raise ValueError("refusing_to_overwrite_v4_binding_preflight")
    outdir.mkdir(parents=True, exist_ok=False)
    plan_dir = outdir / "plan"
    bundle = build_fixture_bundle()
    _write_plan_dir(plan_dir, bundle)
    binding = prepare_v4_binding(
        plan_dir=plan_dir,
        code_sha="V4_BINDING_PREFLIGHT_CODE_SHA",
    )
    if binding.get("authorization_status") != "NOT_AUTHORIZED":
        raise RuntimeError("v4_binding_preflight_self_authorized")
    if binding.get("paid_api_authorized") is not False:
        raise RuntimeError("v4_binding_preflight_paid_api_authorized")
    if binding.get("semantic_status") != "NOT_ADJUDICATED":
        raise RuntimeError("v4_binding_preflight_semantic_promotion")
    if len(binding.get("interface_bindings") or {}) < 9:
        raise RuntimeError("v4_binding_preflight_interface_bindings_incomplete")

    summary = (
        "V4_RESEARCH_BINDING_PREFLIGHT=PASS\n"
        "SCIENTIFIC_EVIDENCE=NO\n"
        "AUTHORIZATION_STATUS=NOT_AUTHORIZED\n"
        "PAID_API_AUTHORIZED=NO\n"
        "SEMANTIC_STATUS=NOT_ADJUDICATED\n"
        f"EXPERIMENTAL_VARIABLE_ID={binding['experimental_variable_id']}\n"
        f"INTERFACE_BINDING_COUNT={len(binding['interface_bindings'])}\n"
        f"BRANCH_PLAN_HASH={binding['branch_plan_hash']}\n"
        f"V4_RESEARCH_BINDING_HASH={binding['binding_hash']}\n"
    )
    (outdir / "SUMMARY.txt").write_text(summary, encoding="utf-8")
    print(summary, end="")


if __name__ == "__main__":
    main()
