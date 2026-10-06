#!/usr/bin/env python3
"""Run the first paper-priority repair-efficacy contrast B arm.

The local/package arm is already frozen and is never rerun. This runner uses
the same G3-X4-T2 sequence-4 parent, a frozen prefix-only source-bound route
plan, one native MCP repair, and then the original subject provider for the
remaining native horizon. No planning-model call, retry, or paid reviewer is
performed.
"""
import argparse
import asyncio
import copy
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from stage2.r7_checkpoint_v1.common import digest, file_tree_manifest, stable_json_bytes
from stage2.native_v7.software_host_v1 import TASKS
from stage2.r7_prospective_v1.engineering_b_runner import _resume_host
from stage2.route_repair.branch_fields import require, save, seal, transform, select_grant
from stage2.route_repair.prefix_context import PrefixMCPContext
from stage2.route_repair.proposal_authority import freeze_task_envelope, ProposalAuthorityCompiler
from stage2.route_repair.native_continuation import OfflineScript
from stage2.route_repair.mcp_same_parent import SameParentMCPBranch, decode_repair_tool_result
from stage2.route_repair.checkout_route_probe import probe
from stage2.route_repair.provider_capture import freeze_provider_bindings
from stage2.route_repair.connected_provider import (
    DeepSeekHTTPTransport,
    ConnectedExchangeSource,
    transport_binding,
)
from stage2.route_repair.system_contract import assess_continuation, read_capture_member
from scripts.check_stage2_same_parent_native_mcp import scripted_proposal

CONFIG = "configs/stage2_repair_efficacy_first_contrast_v1.json"
A_AUDIT = "stage2/replication_v2/G3/paired_semantic_audit_v1/audits/X4-T2.json"


def load_contract():
    contract = json.loads((ROOT / CONFIG).read_bytes())
    require(contract["schema"] == "stage2-repair-efficacy-first-contrast-v1", "EFFICACY_CONTRACT_SCHEMA_DRIFT")
    require(contract["status"] == "FROZEN_BEFORE_SINGLE_B_EXECUTION", "EFFICACY_CONTRACT_NOT_FROZEN")
    require(contract["case"]["full_id"] == "G3-X4-T2", "EFFICACY_CASE_DRIFT")
    require(contract["arm_A_local_repair"]["rerun"] is False, "LOCAL_ARM_MUST_NOT_RERUN")
    require(contract["arm_B_enhanced_route_repair"]["automatic_retry"] is False, "ENHANCED_ARM_RETRY_FORBIDDEN")
    require(contract["arm_B_enhanced_route_repair"]["planning_provider_calls"] == 0, "AUTONOMOUS_PLANNER_NOT_PART_OF_EFFICACY_TREATMENT")
    return contract


def verify_frozen_local_arm(contract):
    audit = json.loads((ROOT / A_AUDIT).read_bytes())
    a = contract["arm_A_local_repair"]
    require(audit["cell_id"] == contract["case"]["cell_id"], "LOCAL_ARM_CELL_DRIFT")
    require(audit["pair_integrity"]["parent_checkpoint_hash"] == contract["case"]["parent_checkpoint_hash"], "LOCAL_ARM_PARENT_DRIFT")
    require(audit["pair_integrity"]["selected_package_id"] == a["selected_package_id"], "LOCAL_ARM_PACKAGE_DRIFT")
    require(audit["pair_integrity"]["canonical_B_workflow_run"] == a["canonical_workflow_run"], "LOCAL_ARM_RUN_DRIFT")
    require(audit["paired_effect"]["overall_process_effect"] == a["frozen_overall_process_effect"], "LOCAL_ARM_EFFECT_DRIFT")
    require(audit["paired_effect"]["direct_target_effect"] == a["frozen_direct_target_effect"], "LOCAL_ARM_TARGET_EFFECT_DRIFT")
    require(audit["arm_B"]["censored"] is True and audit["arm_B"]["termination_class"] == "turn_budget", "LOCAL_ARM_EXPECTED_CENSOR_DRIFT")
    return audit


def controlled_verifier(root):
    value = probe(root)
    passed = (
        value["controlled_launcher_selection"] == {"UNSET": ["current"], "on": ["legacy"], "off": ["current"]}
        and all(
            row["status"] == 200
            and row["body"] == {
                "status": "pending_payment",
                "amount_cents": 2500,
                "method": row["method"],
            }
            for row in value["http_handler_contracts"]["current"]
        )
        and all(row["status"] == 410 for row in value["http_handler_contracts"]["legacy"])
    )
    return {
        "passed": passed,
        "controlled_probe": value,
        "scope": "TWO_METHODS_ONE_CART_NOT_BROWSER_OR_REAL_PAYMENT",
    }


def make_live_subject_profile(context, transport, contract):
    frozen = freeze_provider_bindings(context, ROOT)["profiles"]["subject"]
    row = {k: copy.deepcopy(v) for k, v in frozen.items() if k != "profile_hash"}
    remaining = context.parent["manifest"]["remaining_horizon"]
    require(remaining == contract["case"]["remaining_horizon"], "EFFICACY_SUBJECT_HORIZON_DRIFT")
    require(remaining == contract["arm_B_enhanced_route_repair"]["subject_provider_calls_max"], "EFFICACY_SUBJECT_BUDGET_DRIFT")
    row.update(
        schema="stage2-connected-provider-profile-v1",
        live_transport_enabled=True,
        transport_binding=transport_binding(transport),
        connected_config_hash=digest((ROOT / CONFIG).read_bytes()),
        max_logical_calls=remaining,
        max_transport_attempts=remaining,
        max_request_bytes=8_000_000,
        max_response_bytes=8_000_000,
        horizon_is_trial_censor_not_native_ceiling=False,
    )
    return seal(row, "profile_hash")


def execute_frozen_route_repair(branch):
    bundle = branch.bundle
    actions = []
    completed = []
    branch.phase = "FROZEN_SOURCE_BOUND_ROUTE_REPAIR"
    branch.capture("REPAIR_EFFICACY_B_BEFORE")
    for action in bundle["application_plan"]["actions"]:
        require(file_tree_manifest(branch.root) == branch.expected, "EFFICACY_APPLICATION_VERSION_DRIFT")
        require(set(action.get("depends_on", [])) <= set(completed), "EFFICACY_REPAIR_DEPENDENCY_NOT_COMPLETE")
        path = action["target_ref"][5:]
        before = decode_repair_tool_result(branch.host.checkout.read_file(path), str)
        require(digest(before.encode()) == action["before_file_hash"], "EFFICACY_NATIVE_READ_VERSION_DRIFT")
        output, invariant = transform(before, action, select_grant(bundle["application_plan"]["policy"], action))
        require(digest(output.encode()) == action["expected_output_hash"], "EFFICACY_EXPECTED_OUTPUT_DRIFT")
        branch.journal.intent(action["action_id"], action["target_ref"], action["before_file_hash"], action["expected_output_hash"])
        native = branch.host.checkout.write_file(path, output)
        actual = decode_repair_tool_result(branch.host.checkout.read_file(path), str)
        receipt = {
            "action_id": action["action_id"],
            "target_ref": action["target_ref"],
            "native_interface": "native:MCPCheckoutProxy.write_file",
            "native_result": native,
            "before_hash": digest(before.encode()),
            "after_hash": digest(actual.encode()),
            "expected_output_hash": action["expected_output_hash"],
            **invariant,
        }
        actions.append(receipt)
        save(branch.out / "native_repair_receipts.json", actions)
        branch.journal.complete(action["action_id"], receipt["after_hash"], receipt)
        require(actual == output, "EFFICACY_NATIVE_WRITE_POSTCONDITION_FAILED")
        branch.expected[path] = digest(actual.encode())
        require(file_tree_manifest(branch.root) == branch.expected, "EFFICACY_NATIVE_WRITE_SCOPE_DRIFT")
        require(branch.adapter.save_state(branch.host) == branch.parent["state"], "EFFICACY_REPAIR_MUTATED_HOST_STATE")
        completed.append(action["action_id"])

    checks = []
    for task in bundle["proposal"]["verification_tasks"]:
        require(set(task["depends_on"]) <= set(completed), "EFFICACY_VERIFICATION_DEPENDENCY_NOT_COMPLETE")
        before_manifest = file_tree_manifest(branch.root)
        value = controlled_verifier(branch.root)
        require(file_tree_manifest(branch.root) == before_manifest, "EFFICACY_VERIFIER_MUTATED_APPLICATION")
        row = {
            "verification_id": task["verification_id"],
            "result": value,
            "classification": "HOST_DEFINED_ENGINEERING_CHECK_NOT_SEMANTIC_REVIEW",
        }
        checks.append(row)
        save(branch.out / "verification_receipts.json", checks)
        require(value["passed"] is True, "EFFICACY_HOST_VERIFICATION_FAILED")
        completed.append(task["verification_id"])

    require(completed == bundle["proposal"]["execution_order"], "EFFICACY_REPAIR_STEPS_INCOMPLETE")
    checkpoint = branch.checkpoint("host:repair-efficacy-b:post")
    save(branch.out / "after_repair_checkpoint.json", checkpoint)
    exit_row = seal(
        {
            "schema": "stage2-frozen-route-repair-executor-exit-v1",
            "parent_checkpoint_hash": branch.context.parent_checkpoint_hash,
            "bundle_hash": bundle["bundle_hash"],
            "completed_steps": completed,
            "native_repair_actions": len(actions),
            "agent_generated_plan": False,
            "planning_provider_calls": 0,
            "semantic_effect_certified": False,
            "classification": "FROZEN_PREFIX_ONLY_SOURCE_BOUND_PLAN_EXECUTED_FOR_METHOD_EFFICACY",
        },
        "exit_hash",
    )
    save(branch.out / "repair_executor_exit.json", exit_row)
    branch.observer.capture(
        "native:frozen_route_repair_executor",
        stable_json_bytes(exit_row).decode(),
        "FROZEN_ROUTE_REPAIR_EXECUTOR_EXIT",
    )
    branch.capture("REPAIR_EFFICACY_B_AFTER")
    return actions, checks, exit_row


def retain_provider_observations(branch, source):
    for directory in sorted(source.out.glob("[0-9][0-9][0-9][0-9]")):
        for name in ["request.bin", "response_headers.json", "response.bin", "receipt.json"]:
            path = directory / name
            if not path.exists():
                continue
            raw = path.read_bytes()
            content = stable_json_bytes({"bytes_hex": raw.hex()}).decode() if name.endswith(".bin") else raw.decode()
            branch.observer.capture(
                "native:subject_provider_exchange",
                content,
                "CONNECTED_SUBJECT_" + name.split(".")[0].upper(),
                receipt={
                    "exchange_member": str(path.relative_to(branch.out)),
                    "exchange_hash": digest(raw),
                    "provider_calls": source.provider_calls,
                    "origin": "LIVE_PROVIDER_HTTP",
                },
            )


async def run_live_branch(context, authorization, bundle, out, sdk_root, protocol_root, contract):
    dummy = OfflineScript([{"content": '{"actions":[{"type":"finalize","answer":"unused"}]}'}])
    task = bundle["proposal"]["verification_tasks"][0]
    verifier_binding = {task["verification_id"]: {**task, "run": controlled_verifier}}
    branch = SameParentMCPBranch(
        context,
        authorization,
        bundle,
        out / "native_branch",
        script=dummy,
        sdk_root=sdk_root,
        protocol_root=protocol_root,
        verifiers=verifier_binding,
    )
    actions, checks, exit_row = execute_frozen_route_repair(branch)

    transport = DeepSeekHTTPTransport()
    profile = make_live_subject_profile(context, transport, contract)
    source = ConnectedExchangeSource(
        profile,
        transport,
        branch.out / "provider_exchanges",
        gate=lambda: branch.phase == "NATIVE_SUBJECT_CONTINUATION",
    )
    os.environ.pop("DEEPSEEK_API_KEY", None)
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    branch.source = source
    branch.host.provider = source
    branch.phase = "NATIVE_SUBJECT_CONTINUATION"
    branch.capture("NATIVE_MCP_CONTINUATION_BEFORE")

    async def boundary(**payload):
        branch.capture("NATIVE_MCP_TERMINAL_RETURN" if payload["boundary"] == "TERMINAL" else "NATIVE_MCP_TURN_RETURN")

    error = None
    result = None
    try:
        result = await _resume_host(branch.host, boundary)
        kind = "NATIVE_CLOSURE" if branch.host.stop_reason in {"finalized", "queue_exhausted"} else "NATIVE_CENSOR"
        branch.observer.capture("native:closure", stable_json_bytes(result).decode(), kind)
    except BaseException as exc:
        error = {"type": type(exc).__name__, "message": str(exc)}
        branch.observer.capture("native:closure", stable_json_bytes(error).decode(), "NATIVE_FAILURE")
        raise
    finally:
        retain_provider_observations(branch, source)
        branch.capture("NATIVE_MCP_BRANCH_AFTER")
        comparison = branch.observer.finish()
        after = branch.adapter.save_state(branch.host)
        save(branch.out / "native_state_after.json", after)
        require(
            after["history"][: len(branch.parent["state"]["history"])] == branch.parent["state"]["history"],
            "EFFICACY_HOST_HISTORY_PREFIX_DRIFT",
        )
        require(
            after["max_turns"] == branch.parent["state"]["max_turns"]
            and after["max_actions"] == branch.parent["state"]["max_actions"]
            and len(after["history"]) <= after["max_turns"],
            "EFFICACY_HOST_BUDGET_DRIFT",
        )
        assessment = assess_continuation(
            branch.contract,
            context.graph,
            branch.observer.graph.snapshot(),
            source_reader=lambda observation: read_capture_member(branch.out, observation),
        )
        save(branch.out / "continuation_assessment.json", assessment)
        review_state = "PENDING_SEPARATE_SOURCE_BOUND_REVIEW"
        receipt = seal(
            {
                "schema": "stage2-repair-efficacy-b-first-attempt-v1",
                "status": "CAPTURED_PENDING_INDEPENDENT_SEMANTIC_REVIEW" if error is None else "FAILED_WITH_PARTIAL_EVIDENCE",
                "parent_checkpoint_hash": context.parent_checkpoint_hash,
                "parent_native_sequence": contract["case"]["parent_native_sequence"],
                "remaining_before": contract["case"]["remaining_horizon"],
                "remaining_after": after["max_turns"] - len(after["history"]),
                "native_ceiling": after["max_turns"],
                "native_repair_actions": len(actions),
                "verification_checks": len(checks),
                "subject_provider_calls": source.provider_calls,
                "subject_logical_calls": source.calls,
                "planning_provider_calls": 0,
                "automatic_retry": False,
                "local_arm_rerun": False,
                "agent_generated_plan": False,
                "frozen_plan_exit_hash": exit_row["exit_hash"],
                "stop_reason": after["stop_reason"],
                "history_length_after": len(after["history"]),
                "graph_new_observations": comparison["new_observations"],
                "semantic_effect": review_state,
                "repair_success": False,
                "error": error,
            },
            "receipt_hash",
        )
        save(branch.out / "efficacy_receipt.json", receipt)
        save(branch.out / "final_checkpoint.json", branch.checkpoint("host:repair-efficacy-b:terminal"))
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ["source-root", "sdk-root", "protocol-root", "out"]:
        p.add_argument("--" + name, required=True, type=Path)
    p.add_argument("--execute", action="store_true")
    args = p.parse_args()
    require(not args.out.exists(), "FRESH_EFFICACY_OUTPUT_REQUIRED_NO_REPLAY")

    contract = load_contract()
    audit = verify_frozen_local_arm(contract)
    case = next(
        c
        for c in json.loads((ROOT / "configs/stage2_terminal_route_repair_first_round_v1.json").read_bytes())["cases"]
        if c["full_id"] == contract["case"]["full_id"]
    )
    archive = args.source_root / "G3A/stage2/replication_v2/G3/natural_A/X4-T2/first_attempt.tar.gz"
    context = PrefixMCPContext(
        archive,
        full_id=case["full_id"],
        archive_sha256=case["archive_sha256"],
        parent_checkpoint_hash=contract["case"]["parent_checkpoint_hash"],
    )
    try:
        require(context.parent["manifest"]["remaining_horizon"] == contract["case"]["remaining_horizon"], "EFFICACY_PARENT_HORIZON_DRIFT")
        envelope = freeze_task_envelope(
            context,
            TASKS["T2"],
            writable_refs=["file:" + path for path in context.parent["files"]],
            branch_id="repair-efficacy-first-contrast-b",
            max_actions=contract["arm_B_enhanced_route_repair"]["max_actions"],
            max_value_bytes=contract["arm_B_enhanced_route_repair"]["max_value_bytes"],
        )
        compiler = ProposalAuthorityCompiler(context, envelope)
        session, proposal, catalog = scripted_proposal(context)
        require(proposal["parent_checkpoint_hash"] == contract["case"]["parent_checkpoint_hash"], "EFFICACY_B_PLAN_PARENT_DRIFT")
        require(proposal["modify_refs"] == contract["arm_B_enhanced_route_repair"]["modify_refs"], "EFFICACY_B_PLAN_TARGET_DRIFT")
        authorization = compiler.compile(session, proposal)
        bundle = authorization.bundle

        summary = seal(
            {
                "schema": "stage2-repair-efficacy-first-contrast-preflight-v1",
                "case_id": contract["case"]["full_id"],
                "same_parent_checkpoint_hash": context.parent_checkpoint_hash,
                "parent_native_sequence": contract["case"]["parent_native_sequence"],
                "remaining_horizon": context.parent["manifest"]["remaining_horizon"],
                "local_arm_canonical_run": audit["pair_integrity"]["canonical_B_workflow_run"],
                "local_arm_effect": audit["paired_effect"]["overall_process_effect"],
                "enhanced_plan_hash": bundle["application_plan"]["plan_hash"],
                "enhanced_modify_refs": proposal["modify_refs"],
                "prefix_observations": len(context.graph["observations"]),
                "prefix_nodes": len(context.graph["nodes"]),
                "planning_provider_calls": 0,
                "subject_provider_calls": 0,
                "automatic_retry": False,
                "execution_armed": bool(args.execute),
            },
            "preflight_hash",
        )
        save(args.out / "preflight.json", summary)
        save(args.out / "enhanced_route_proposal.json", proposal)
        save(args.out / "enhanced_route_authorization.json", authorization.receipt)
        save(args.out / "prefix_catalog.json", catalog)
        if not args.execute:
            print(json.dumps(summary))
            return
        asyncio.run(run_live_branch(context, authorization, bundle, args.out, args.sdk_root, args.protocol_root, contract))
        receipt = json.loads((args.out / "native_branch/efficacy_receipt.json").read_bytes())
        print(json.dumps(receipt))
    finally:
        context.close()


if __name__ == "__main__":
    main()
