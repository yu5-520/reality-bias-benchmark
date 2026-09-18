from __future__ import annotations

import argparse
import json
from pathlib import Path

from .build_v5_whole_process_manifest import build_rows, verify_manifest
from .v5_whole_process_index import derive_v5_structural_index


def _fixture_trace() -> dict:
    return {
        "run_id": "v5-whole-process-preflight",
        "run_status": "RUN_COMPLETE",
        "events": [
            {
                "event_index": 0,
                "turn": 1,
                "actor": "inventory",
                "action_type": "write_state",
                "realized_in_baseline": True,
                "action": {"type": "write_state", "key": "inventory_assessment", "value": {"stock": 1520}, "status": "preliminary"},
                "shared_state_metadata_after": {
                    "inventory_assessment": {
                        "status": "preliminary",
                        "writer": "inventory",
                        "event_index": 0,
                    }
                },
            },
            {
                "event_index": 1,
                "turn": 2,
                "actor": "ads",
                "action_type": "write_state",
                "realized_in_baseline": True,
                "action": {"type": "write_state", "key": "ads_guardrail", "value": {"uplift_cap": 8}, "status": "derived"},
                "shared_state_metadata_after": {
                    "ads_guardrail": {"status": "derived", "writer": "ads", "event_index": 1}
                },
            },
        ],
        "model_calls": [
            {
                "turn": 2,
                "agent_id": "ads",
                "status": "completed",
                "event_index_start": 1,
                "event_index_end": 2,
                "runtime_snapshot": {
                    "shared_state_metadata": {
                        "inventory_assessment": {
                            "status": "preliminary",
                            "writer": "inventory",
                            "event_index": 0,
                        }
                    }
                },
            },
            {
                "turn": 3,
                "agent_id": "finance",
                "status": "completed",
                "event_index_start": 2,
                "event_index_end": 3,
                "runtime_snapshot": {
                    "shared_state_metadata": {
                        "inventory_assessment": {
                            "status": "preliminary",
                            "writer": "inventory",
                            "event_index": 0,
                        },
                        "ads_guardrail": {
                            "status": "derived",
                            "writer": "ads",
                            "event_index": 1,
                        },
                    }
                },
            },
        ],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="results/v5_whole_process_preflight")
    ap.add_argument("--code-sha", default="OFFLINE-PREFLIGHT")
    args = ap.parse_args()

    rows = build_rows(
        design_path="configs/v5_whole_process_ecommerce_batch001_v0.2.json",
        code_sha=args.code_sha,
    )
    assert verify_manifest(rows)
    assert len(rows) == 3

    index = derive_v5_structural_index(_fixture_trace())
    assert index["engineering_core"]["first_repair_anchor_candidate_ref"] == "arena_event:0:state:inventory_assessment"
    assert index["engineering_core"]["content_address_count"] >= 1
    assert index["engineering_core"]["pool_visibility_ledger_count"] >= 1
    assert index["engineering_core"]["first_node_localization_required_for_repair"] is False
    assert index["mechanism_observables"]["engineering_requirement"] is False
    assert index["direct_pool_consumption_semantic_status"] == "NOT_ADJUDICATED"

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "manifest_candidate.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows),
        encoding="utf-8",
    )
    (out / "fixture_structural_index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary = {
        "schema": "RB-V5-WHOLE-PROCESS-PREFLIGHT-SUMMARY-v0.1",
        "status": "PASS",
        "planned_subject_runs": len(rows),
        "provider_calls": 0,
        "evaluator_calls": 0,
        "active_recovery": False,
        "agent_runtime_modified": False,
        "pool_visibility_mechanical": True,
        "direct_pool_consumption_semantic": "DEFERRED_APPEND_ONLY",
        "repair_anchor_candidate_fixture": index["engineering_core"]["first_repair_anchor_candidate_ref"],
        "content_address_count": index["engineering_core"]["content_address_count"],
        "pool_visibility_ledger_count": index["engineering_core"]["pool_visibility_ledger_count"],
        "first_node_localization_required_for_repair": False,
        "optional_first_support_candidate_fixture": index["first_support_candidate_ref"],
        "optional_first_pool_candidate_fixture": index["first_pool_candidate_ref"],
        "optional_first_exposure_candidate_fixture": index["first_exposure_candidate_ref"],
    }
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("V5_WHOLE_PROCESS_PREFLIGHT=PASS")
    print("PLANNED_SUBJECT_RUNS=3")
    print("PROVIDER_CALLS=0")
    print("REPAIR_ANCHOR_DERIVATION=PASS")
    print("FIRST_NODE_LOCALIZATION_REQUIRED_FOR_REPAIR=NO")
    print("DIRECT_POOL_CONSUMPTION_SEMANTIC=DEFERRED_APPEND_ONLY")


if __name__ == "__main__":
    main()
