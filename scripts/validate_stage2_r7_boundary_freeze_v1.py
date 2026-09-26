from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BOUNDARY = ROOT / "configs/stage2_r7_boundary_contract_v1.json"
FIREWALL = ROOT / "configs/stage2_r7_monitor_input_firewall_v1.json"
SOURCE_FREEZE = ROOT / "configs/stage2_r7_21_path_source_freeze_v1.json"
PACKAGE_SCHEMA = ROOT / "schemas/stage2_r7_monitor_derived_repair_package_v1.schema.json"
PROTOCOL = ROOT / "docs/StageII_R7_External_Process_Integrity_Repair_Protocol_v1.0.md"
PLAN = ROOT / "docs/R_Plan_v7.36.md"

EXPECTED_CELLS = [f"X{x}-T{t}" for x in range(1, 8) for t in range(1, 4)]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def require(ok: bool, message: str):
    if not ok:
        raise AssertionError(message)


def main():
    boundary = load(BOUNDARY)
    firewall = load(FIREWALL)
    freeze = load(SOURCE_FREEZE)
    schema = load(PACKAGE_SCHEMA)

    require(boundary["schema"] == "RB-STAGE2-R7-BOUNDARY-CONTRACT-v1", "boundary schema")
    require(boundary["status"] == "FROZEN_PRE_EXECUTION_NO_ACTIVE_REPAIR", "boundary status")
    require(boundary["core_principle"] == "OBSERVE_ACROSS_BOUNDARIES_REPAIR_ONLY_THROUGH_BOUNDARIES", "core principle")
    require(boundary["natural_evidence"]["cells"] == 21, "21 cells")
    require(boundary["natural_evidence"]["natural_reruns"] == 0, "no natural reruns")
    require(boundary["monitoring"]["future_blindness"] is True, "future blindness")
    require(boundary["monitoring"]["semantic_audit_as_input"] is False, "semantic audit firewall")
    require(boundary["monitoring"]["cpr_labels_as_input"] is False, "CPR firewall")
    require(boundary["repair_geometry"]["new_repair_continuations_per_package"] == 1, "one B continuation")
    require(boundary["repair_geometry"]["resampling"] is False, "no resampling")
    require(boundary["repair_geometry"]["best_of_n_selection"] is False, "no best-of-N")
    require(boundary["repair_geometry"]["repair_executor_exit_after_package"] is True, "repair executor exit")
    require(boundary["authorization"]["new_subject_provider_call"] is False, "provider disabled")
    require(boundary["authorization"]["active_repair_execution"] is False, "active repair disabled")

    forbidden = set(boundary["repair_surface"]["forbidden"])
    for token in [
        "MODIFY_FRAMEWORK_SOURCE_TO_ENABLE_REPAIR",
        "MODIFY_PROTOCOL_OR_SERIALIZATION_SEMANTICS_TO_ENABLE_REPAIR",
        "BYPASS_NATIVE_TOOL_OR_PERMISSION_BOUNDARY",
        "MUTATE_RAG_CORPUS_INDEX_EMBEDDING_OR_RETRIEVAL_STRUCTURE",
        "MUTATE_MEMORYBANK_INTERNAL_MEMORY_INDEX_STRENGTH_OR_RECALL_MECHANISM",
        "MODIFY_LONGLMLINGUA_MODEL_CHECKPOINT_ALGORITHM_OR_COMPRESSION_INTERFACE",
        "USE_POSTHOC_SEMANTIC_AUDIT_TO_CHOOSE_OR_EXPAND_REPAIR_SCOPE",
    ]:
        require(token in forbidden, "missing forbidden mutation: " + token)

    require(freeze["schema"] == "RB-STAGE2-R7-21-PATH-SOURCE-FREEZE-v1", "source freeze schema")
    require(freeze["matrix"]["cells"] == 21, "source freeze 21")
    require(freeze["matrix"]["natural_reruns"] == 0, "source freeze no rerun")
    require(freeze["semantic_audit_policy"] == "POSTHOC_VALIDATION_ONLY_NOT_MONITOR_INPUT", "posthoc only")
    require(freeze["repair_selection_encoded"] is False, "no repair selection encoded")

    rows = freeze["cells"]
    require(len(rows) == 21, "freeze row count")
    require([r["cell"] for r in rows] == EXPECTED_CELLS, "matrix order/coverage")
    require(len({r["cell"] for r in rows}) == 21, "unique cells")

    compare_fields = [
        "tar_sha256",
        "artifact_zip_sha256",
        "execution_sha",
        "workflow_run_id",
        "artifact_id",
        "natural_attempts_for_cell",
    ]
    for row in rows:
        cell = row["cell"]
        manifest = load(ROOT / f"stage2/natural_v7/{cell}/manifest.json")
        require(manifest["natural_attempts_for_cell"] == 1, cell + ": must remain first attempt")
        for field in compare_fields:
            require(manifest.get(field) == row.get(field), f"{cell}: frozen {field} mismatch")

    require(firewall["schema"] == "RB-STAGE2-R7-MONITOR-INPUT-FIREWALL-v1", "firewall schema")
    forbidden_inputs = "\n".join(firewall["forbidden_inputs"])
    for token in [
        "r6_grade_semantic_audit",
        "r6_grade_material",
        "cross_task_cross_layer_audit",
        "stage2_cross_task_synthesis_evidence_bundle",
        "stage2_paper_figure_table_registry",
    ]:
        require(token in forbidden_inputs, "missing forbidden semantic source: " + token)

    forbidden_output = set(firewall["forbidden_semantic_fields_in_monitor_output"])
    require("cpr_label" in forbidden_output, "cpr_label must be forbidden")
    require("cpr_direction" in forbidden_output, "cpr_direction must be forbidden")

    require(schema["$id"] == "RB-STAGE2-R7-MONITOR-DERIVED-REPAIR-PACKAGE-v1", "package schema id")
    required = set(schema["required"])
    for field in [
        "prefix_cutoff_ref",
        "pressure_refs",
        "support_refs",
        "affected_closure_refs",
        "preserve_refs",
        "repair_anchor_ref",
        "allowed_repair_surface",
        "native_capability_requirements",
        "forbidden_mutations",
        "parent_reconstruction",
        "repair_gate_status",
        "post_repair_watch",
    ]:
        require(field in required, "package missing field: " + field)
    props = set(schema["properties"])
    require("cpr_label" not in props and "cpr_direction" not in props, "repair package must not encode CPR answer")

    protocol = PROTOCOL.read_text(encoding="utf-8")
    plan = PLAN.read_text(encoding="utf-8")
    for token in [
        "Observe across boundaries; repair only through boundaries.",
        "Semantic audit validates the monitor; semantic audit does not guide the monitor.",
        "Prefix-causal replay",
        "In-repair boundary watch",
        "Post-repair native-continuation watch",
        "one new B continuation per package",
    ]:
        require(token in protocol, "protocol missing: " + token)
    for token in [
        "STAGE-II R7 BOUNDARIES FROZEN",
        "21 NATURAL PATHS FROZEN AS R7 SOURCE POPULATION",
        "OFFLINE STRUCTURAL MONITOR NEXT",
        "No natural A branch is regenerated.",
    ]:
        require(token in plan, "plan missing: " + token)

    print("STAGE2_R7_BOUNDARY_FREEZE=PASS")
    print("NATURAL_SOURCE_PATHS=21")
    print("NATURAL_RERUNS=0")
    print("SEMANTIC_AUDIT_MONITOR_INPUT=NO")
    print("ACTIVE_REPAIR_AUTHORIZED=NO")
    print("NEXT=OFFLINE_STRUCTURAL_MONITOR_IMPLEMENTATION_AND_PREFIX_REPLAY")


if __name__ == "__main__":
    main()
