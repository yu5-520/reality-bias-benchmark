#!/usr/bin/env python3
"""Validate the frozen Stage-II R6-grade semantic audit without executing subjects."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
AUDIT=ROOT/"stage2"/"natural_v7"/"r6_grade_semantic_audit"
MATERIAL=ROOT/"stage2"/"natural_v7"/"r6_grade_material"

def main():
    index=json.loads((AUDIT/"audit_index.json").read_text())
    material=json.loads((MATERIAL/"index.json").read_text())
    rows=[json.loads(line) for line in (AUDIT/"case_semantic_ledgers.jsonl").read_text().splitlines() if line.strip()]
    assert index["natural_cells"] == 21
    assert index["natural_reruns"] == 0
    assert index["subject_calls"] == 0
    assert index["contrasts_spent_by_this_audit"] == 0
    assert len(rows) == 21
    expected={f"X{x}-T{t}" for t in range(1,4) for x in range(1,8)}
    assert {r["cell"] for r in rows} == expected
    assert {r["cell"] for r in rows} == {r["cell"] for r in material["cells"]}

    material_by={r["cell"]:r for r in material["cells"]}
    index_by={r["cell"]:r for r in index["cells"]}
    semantic_nodes=semantic_edges=0
    for row in rows:
        cell=row["cell"]
        assert row["audit_mode"] == "READ_ONLY_FROZEN_EVIDENCE"
        assert row["case_judgement"]["natural_rerun"] is False
        assert row["case_judgement"]["subject_calls"] == 0
        assert row["case_judgement"]["contrast_spent"] is False
        assert (ROOT/row["route_material_ref"]).is_file()
        assert (ROOT/row["posthoc_ref"]).is_file()

        m=material_by[cell]
        acct=row["complete_route_accounting"]
        assert acct["recorded_route_nodes"] == m["route_nodes"]
        assert acct["recorded_native_events"] == m["native_events"]
        assert acct["recorded_textual_observer_members"] == m["textual_observer_members"]
        assert acct["route_preserved_in_material_packet"] is True

        node_ids=[n["node_id"] for n in row["semantic_nodes"]]
        assert len(node_ids) == len(set(node_ids)), cell
        node_set=set(node_ids)
        edge_ids=[e["edge_id"] for e in row["semantic_edges"]]
        assert len(edge_ids) == len(set(edge_ids)), cell
        for edge in row["semantic_edges"]:
            assert edge["from_node"] in node_set, (cell,edge["edge_id"],"from")
            assert edge["to_node"] in node_set, (cell,edge["edge_id"],"to")
            assert edge["evidence_refs"], (cell,edge["edge_id"])
        for node in row["semantic_nodes"]:
            assert node["evidence_refs"], (cell,node["node_id"])
            assert node["semantic_before"] is not None
            assert node["semantic_after"] is not None
            assert node["semantic_delta"] is not None

        ix=index_by[cell]
        assert ix["route_nodes"] == m["route_nodes"]
        assert ix["native_events"] == m["native_events"]
        assert ix["semantic_nodes"] == len(row["semantic_nodes"])
        assert ix["semantic_edges"] == len(row["semantic_edges"])
        semantic_nodes += len(row["semantic_nodes"])
        semantic_edges += len(row["semantic_edges"])

    assert semantic_nodes == 70, semantic_nodes
    assert semantic_edges == 46, semantic_edges
    exact={
        "runner_route_nodes":sum(x["route_nodes"] for x in material["cells"]),
        "passive_native_events":sum(x["native_events"] for x in material["cells"]),
        "textual_observer_members":sum(x["textual_observer_members"] for x in material["cells"]),
        "frozen_checkout_file_entries":sum(x["checkout_files"] for x in material["cells"]),
    }
    for key,value in exact.items():
        assert index["material_accounting"][key] == value, (key,value,index["material_accounting"][key])
    print(json.dumps({
        "status":"PASS",
        "cells":len(rows),
        "semantic_nodes":semantic_nodes,
        "semantic_edges":semantic_edges,
        **exact,
        "subject_calls":0,
        "natural_reruns":0,
        "contrasts_spent":0
    },sort_keys=True))

if __name__=="__main__":
    main()
