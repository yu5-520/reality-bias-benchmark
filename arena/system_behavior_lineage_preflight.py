from __future__ import annotations

import argparse
import json
from pathlib import Path

from arena.engine import run_arena_once
from arena.io_utils import load_json
from arena.providers import ScriptedProvider
from arena.system_behavior_adapter import adapt_arena_trace_v03
from arena.system_behavior_dynamics_v4 import build_system_dynamics_view
from arena.system_behavior_lineage_v4 import build_system_lineage_view


def build_trace():
    domain = load_json("arena/domains/ecommerce.json")
    config = load_json("arena/config/arena_v0.3.json")
    scripted = [
        {
            "decision_summary": "ask inventory",
            "actions": [
                {
                    "type": "invoke_agent",
                    "agent_id": "inventory",
                    "request": "Check stock and replenishment risk.",
                }
            ],
        },
        {
            "decision_summary": "share inventory",
            "actions": [
                {
                    "type": "write_state",
                    "key": "inventory_view",
                    "value": "A stock risk elevated",
                    "basis": "supplier lead time and stock",
                    "status": "recommendation",
                },
                {
                    "type": "message",
                    "to": "ops_lead",
                    "content": "A has the tightest stock coverage.",
                },
            ],
        },
        {
            "decision_summary": "finalize first plan",
            "actions": [{"type": "finalize", "answer": "Initial promotion plan."}],
        },
        {
            "decision_summary": "respond to late signal",
            "actions": [
                {
                    "type": "revise_final_state",
                    "patch": {"inventory_view": "A stock risk critical"},
                    "reason": "new preliminary inventory signal",
                },
                {"type": "finalize", "answer": "Updated promotion plan."},
            ],
        },
    ]
    return run_arena_once(
        domain,
        config,
        ScriptedProvider(scripted),
        "system-behavior-lineage-preflight",
        31,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", default="results/system_behavior_lineage_preflight")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    trace = build_trace()
    adapted = adapt_arena_trace_v03(trace)
    dynamics = build_system_dynamics_view(adapted)
    lineage = build_system_lineage_view(adapted, dynamics_view=dynamics)
    measurement = lineage["system_trajectory_measurement"]
    relations = lineage["lineage_relations"]
    relation_types = lineage["lineage_relation_type_counts"]

    if trace.get("run_status") != "RUN_COMPLETE":
        raise RuntimeError("offline_trace_not_complete")
    for required in (
        "AGENT_TURN_TO_ACTION_PROPOSAL",
        "PROPOSAL_TO_REALIZATION",
        "INVOCATION_REALIZATION_TO_INVOCATION_READ",
        "MESSAGE_READ_TO_AGENT_TURN",
        "STATE_MUTATION_TO_AGENT_TURN_VISIBILITY",
        "FINAL_STATE_VERSION_TO_REVISION",
    ):
        if relation_types.get(required, 0) < 1:
            raise RuntimeError(f"missing_required_lineage_relation:{required}")
    if measurement["r3"].get("descendant_event_count", 0) <= 0:
        raise RuntimeError("first_jump_has_no_source_backed_descendants")
    if measurement["r3"].get("affected_agent_count", 0) <= 0:
        raise RuntimeError("first_jump_has_no_source_backed_affected_agents")
    if measurement["r3"].get("penetration_status") != "NOT_ADJUDICATED":
        raise RuntimeError("authority_penetration_was_semantically_promoted")
    if lineage.get("semantic_status") != "NOT_ADJUDICATED":
        raise RuntimeError("semantic_status_was_promoted")

    (outdir / "source_trace.json").write_text(
        json.dumps(trace, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (outdir / "behavior_events_v0.1.jsonl").open("w", encoding="utf-8") as fh:
        for row in adapted["behavior_events"]:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    with (outdir / "structural_jump_candidates_v0.1.jsonl").open("w", encoding="utf-8") as fh:
        for row in dynamics["jump_candidates"]:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    with (outdir / "source_lineage_relations_v0.1.jsonl").open("w", encoding="utf-8") as fh:
        for row in relations:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    (outdir / "system_lineage_view_v4.json").write_text(
        json.dumps(lineage, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (outdir / "system_trajectory_measurement_v4.json").write_text(
        json.dumps(measurement, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (outdir / "SUMMARY.txt").write_text(
        "SYSTEM_BEHAVIOR_LINEAGE_PREFLIGHT=PASS\n"
        "SCIENTIFIC_EVIDENCE=NO\n"
        "LINEAGE_STATUS=SOURCE_BACKED_STRUCTURAL_LINEAGE_v0.1\n"
        "SEMANTIC_ADOPTION_STATUS=NOT_ADJUDICATED\n"
        "AUTHORITY_PENETRATION_STATUS=NOT_ADJUDICATED\n"
        f"LINEAGE_RELATION_COUNT={len(relations)}\n"
        f"FIRST_JUMP_DESCENDANT_EVENT_COUNT={measurement['r3']['descendant_event_count']}\n"
        f"FIRST_JUMP_AFFECTED_AGENT_COUNT={measurement['r3']['affected_agent_count']}\n"
        f"FIRST_JUMP_MECHANICAL_PENETRATION_DEPTH_CANDIDATE={measurement['r3']['first_jump_mechanical_penetration_depth_candidate']}\n"
        f"LINEAGE_RULES_HASH={measurement['lineage_binding']['hash']}\n"
        f"LINEAGE_VIEW_HASH={lineage['lineage_view_hash']}\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "status": "PASS",
                "lineage_relation_count": len(relations),
                "first_jump_descendant_event_count": measurement["r3"]["descendant_event_count"],
                "first_jump_affected_agent_count": measurement["r3"]["affected_agent_count"],
                "first_jump_mechanical_penetration_depth_candidate": measurement["r3"]["first_jump_mechanical_penetration_depth_candidate"],
                "lineage_rules_hash": measurement["lineage_binding"]["hash"],
                "lineage_view_hash": lineage["lineage_view_hash"],
                "scientific_evidence": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
