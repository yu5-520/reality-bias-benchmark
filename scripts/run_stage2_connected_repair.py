#!/usr/bin/env python3
"""Execute a single captured provider trial on the frozen nonterminal MCP parent.

Default is a mechanism preflight. --purpose engineering explicitly selects the
transport/application trial, which cannot establish paper-mechanism repair.
Failed or censored trials are never replayed. No paid reviewer is invoked.
"""
import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from stage2.native_v7.software_host_v1 import TASKS
from stage2.route_repair.branch_fields import require, save, seal
from stage2.route_repair.prefix_context import PrefixMCPContext
from stage2.route_repair.connected_provider import DeepSeekHTTPTransport, LoopbackHTTPTransport, ConnectedExchangeSource, freeze_connected_bindings
from stage2.route_repair.connected_planning import ConnectedPlanningSession, freeze_connected_envelope
from stage2.route_repair.connected_mcp import ConnectedPlanningRepairEntry
from stage2.route_repair.mcp_same_parent import verify_mcp_environment, decode_repair_tool_result
from stage2.route_repair.independent_review import RepairReviewContext
from stage2.route_repair.system_contract import read_capture_member
from stage2.route_repair.paper_alignment import load_contract, assess_mechanism_entry


def load_context(source_root):
    native = json.loads((ROOT / 'configs/stage2_same_parent_native_mcp_v1.json').read_bytes())
    config = json.loads((ROOT / 'configs/stage2_connected_provider_v1.json').read_bytes())
    require(config['frozen_parent_checkpoint'] == native['parent_checkpoint_hash'], 'CONNECTED_FROZEN_PARENT_DRIFT')
    case = next(c for c in json.loads((ROOT / 'configs/stage2_terminal_route_repair_first_round_v1.json').read_bytes())['cases']
                if c['full_id'] == native['full_id'])
    return PrefixMCPContext(source_root / 'G3A/stage2/replication_v2/G3/natural_A/X4-T2/first_attempt.tar.gz',
          full_id=case['full_id'], archive_sha256=case['archive_sha256'], parent_checkpoint_hash=native['parent_checkpoint_hash'])


def prepare_review(context, branch):
    assessment = json.loads((branch.out / 'continuation_assessment.json').read_bytes())
    review = RepairReviewContext(context, branch.contract, context.graph, branch.observer.graph.snapshot(), assessment,
          branch_source_reader=lambda o: read_capture_member(branch.out, o),
          semantic_rules=json.loads((ROOT / 'configs/r8_dynamic_semantic_audit_contract_v0.4.json').read_bytes()),
          lineage_rules=json.loads((ROOT / 'configs/stage2_r6_grade_semantic_audit_rules_v1.json').read_bytes()),
          repair_actor_id=branch._planning._binding['actor_id'])
    save(branch.out / 'independent_review_catalog.json', review.catalog())
    save(branch.out / 'independent_review_pending.json', review.pending_receipt())


async def execute(context, transport, out, sdk_root, protocol_root):
    bindings = freeze_connected_bindings(context, ROOT, transport)
    save(out / 'provider_bindings.json', bindings); save(out / 'prefix_receipt.json', context.prefix_receipt)
    native = json.loads((ROOT / 'configs/stage2_same_parent_native_mcp_v1.json').read_bytes())
    envelope = freeze_connected_envelope(context, TASKS['T2'], writable_refs=['file:' + p for p in context.parent['files'] if not p.startswith('tests/')],
          branch_id='connected-first-attempt', max_actions=native['max_actions'], max_value_bytes=native['max_value_bytes'])
    # Fixed native test command, fixed original test-file scope. The actor cannot
    # supply a checker, command or passing result. Test absence blocks release.
    test_refs = sorted('file:' + p for p in context.parent['files'] if p.startswith('tests/') and p.endswith('.py'))
    require(test_refs, 'ORIGINAL_NATIVE_APPLICATION_TESTS_REQUIRED')
    cap = {'verification_id': 'VERIFY_NATIVE_TESTS', 'operation': 'HOST_DEFINED_OFFLINE_CHECK',
           'refs': test_refs, 'postcondition': 'Original native application tests pass.'}
    source = ConnectedExchangeSource(bindings['profiles']['planning'], transport, out / 'planning_http', gate=lambda: True)
    planning = ConnectedPlanningSession(context, envelope, source, out / 'planning', verification_capabilities=[cap])
    entry = ConnectedPlanningRepairEntry(context, planning, bindings, out / 'host', repo_root=ROOT, transport=transport)
    def check(root):
        # Use the attached original proxy; preserve subject result representation.
        value = decode_repair_tool_result(entry._branch.host.checkout.run_tests(), dict)
        return {'passed': value.get('returncode') == 0, 'native_result': value,
                'scope': 'ORIGINAL_TEST_SUITE_NOT_SEMANTIC_ADJUDICATION'}
    paused = await entry.plan_and_repair(sdk_root=sdk_root, protocol_root=protocol_root, verifiers={cap['verification_id']: {**cap, 'run': check}})
    save(out / 'paused_receipt.json', paused)
    if entry._branch is not None:
        entry.release(); result = await entry.continue_native(); prepare_review(context, entry._branch)
    else:
        result = paused
    save(out / 'result.json', result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['source-root', 'sdk-root', 'protocol-root', 'out']: p.add_argument('--'+name, required=True, type=Path)
    p.add_argument('--purpose', choices=['mechanism', 'engineering'], default='mechanism')
    p.add_argument('--execute', action='store_true'); args = p.parse_args()
    require(not args.out.exists(), 'FRESH_CONNECTED_TRIAL_OUTPUT_REQUIRED_NO_REPLAY')
    context = load_context(args.source_root)
    try:
        verify_mcp_environment(args.sdk_root, args.protocol_root)
        contract = load_contract(ROOT)
        mechanism = assess_mechanism_entry(context, contract)
        if not args.execute:
            bindings = freeze_connected_bindings(context, ROOT, LoopbackHTTPTransport(18081))
            summary = seal({'schema': 'stage2-connected-trial-preflight-v1', 'provider_calls': 0,
                'credentials_read': False, 'credential_available': bool(os.environ.get('DEEPSEEK_API_KEY', '').strip()),
                'parent_checkpoint_hash': context.parent_checkpoint_hash, 'remaining_horizon': context.parent['manifest']['remaining_horizon'],
                'planning_limit': 16, 'subject_trial_limit': 4, 'native_ceiling': context.parent['state']['max_turns'],
                'execution_armed': False, 'repair_success': False, 'automatic_paid_reviewer': False,
                'trial_purpose': args.purpose, 'mechanism_entry': mechanism,
                'transport_binding': 'PLANNED_HTTPS_ENDPOINT_NOT_A_PROVIDER_CALL'}, 'preflight_hash')
            save(args.out / 'preflight.json', summary); print(json.dumps(summary)); return
        if args.purpose == 'mechanism':
            require(mechanism['repair_entry_ready'], 'PAPER_MECHANISM_ENTRY_BLOCKED:' + ','.join(mechanism['blockers']))
        # A missing credential fails before directories, requests or model attempts.
        transport = DeepSeekHTTPTransport()
        # The bound driver retains its key; application subprocesses do not
        # receive this provider credential through their inherited environment.
        os.environ.pop('DEEPSEEK_API_KEY', None)
        os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
        result = asyncio.run(execute(context, transport, args.out, args.sdk_root, args.protocol_root))
        print(json.dumps({'phase': result.get('phase', result.get('state')), 'provider_calls': result['provider_calls'], 'repair_success': False}))
    finally: context.close()


if __name__ == '__main__': main()
