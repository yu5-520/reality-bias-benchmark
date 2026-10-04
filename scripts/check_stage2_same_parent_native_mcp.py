#!/usr/bin/env python3
"""Reproduce prefix-safe same-parent native MCP engineering without model calls."""
import argparse
import asyncio
import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from stage2.r7_checkpoint_v1.common import digest
from stage2.native_v7.software_host_v1 import TASKS
from stage2.route_repair.branch_fields import require, save, seal
from stage2.route_repair.prefix_context import PrefixMCPContext
from stage2.route_repair.planning_session import RoutePlanningSession
from stage2.route_repair.proposal_authority import freeze_task_envelope, ProposalAuthorityCompiler
from stage2.route_repair.native_continuation import OfflineScript
from stage2.route_repair.mcp_same_parent import SameParentMCPBranch
from stage2.route_repair.checkout_route_probe import probe
from stage2.route_repair.independent_review import RepairReviewContext
from stage2.route_repair.system_contract import read_capture_member

CONFIG = 'configs/stage2_same_parent_native_mcp_v1.json'
FROZEN = ROOT / 'stage2/replication_v2/same_parent_native_mcp_integration_v1'


def scripted_proposal(context):
    """Explicit engineering fixture, not an autonomous semantic diagnosis.

    Every value/span is computed from reads of this early prefix. No old terminal
    proposal, audit verdict, natural result or future graph is loaded.
    """
    session = RoutePlanningSession(context, TASKS['T2'])
    catalog = session.catalog()
    refs = ['file:run.py', 'file:legacy_compat.py', 'file:README.md', 'file:checkout_app/server.py']
    witnesses = {}
    texts = {}
    for ref in refs:
        session.node(ref)
        read = session.file(ref); texts[ref] = read['text']
        witnesses[ref] = session.witness(read['read_id'], 0, len(read['text']))['witness_id']
    clause = 'os.getenv("CHECKOUT_COMPAT", "on")'
    text = texts['file:run.py']
    require(text.count(clause) == 1, 'CONDITIONAL_LAUNCH_FIXTURE_NOT_PRESENT')
    start = text.index(clause) + len('os.getenv("CHECKOUT_COMPAT", ')
    action = {'action_id': 'alternate_default_route', 'target_ref': 'file:run.py', 'kind': 'TEXT_SPAN_REPLACE',
        'start': start, 'end': start + 4, 'before_value_hash': digest(b'"on"'), 'value': '"off"',
        'depends_on': [], 'reason': 'Conditional default engineering probe, with original historical launcher adoption unknown.',
        'diagnosis_ids': ['conditional-launch-source-claim']}
    postcondition = 'Unset alternate launcher selects current, explicit legacy remains, both controlled payment methods respond.'
    proposal = {'schema': 'stage2-complete-route-proposal-v1', 'original_task': TASKS['T2'],
        'graph_hash': context.graph['graph_hash'], 'archive_sha256': context.case['archive_sha256'],
        'parent_checkpoint_hash': context.parent_checkpoint_hash,
        'route_refs': refs, 'modify_refs': ['file:run.py'], 'preserve_refs': refs[1:], 'verify_refs': [],
        'diagnoses': [{'claim_id': 'conditional-launch-source-claim', 'source_ref': 'file:run.py',
            'destination_ref': 'file:legacy_compat.py', 'status': 'SOURCE_BOUND_CLAIM', 'adoption_status': 'UNKNOWN',
            'meaning_before': 'An unset compatibility variable selects legacy in the alternate launcher.',
            'meaning_after': 'The selected legacy handler rejects POST requests.',
            'authority_effect': 'The conditional launcher can select a retired request handler.',
            'limitation': 'Actual historical alternate launcher use and semantic authority adoption are unknown; the documented primary route already works.',
            'witness_ids': [witnesses['file:run.py'], witnesses['file:legacy_compat.py']]}],
        'unknown_relations': ['Historical actual alternate-launcher use is unknown.', 'This fixture does not identify an earliest unsupported semantic transition.'],
        'expected_postconditions': [postcondition], 'application_actions': [action], 'host_answer': None,
        'verification_tasks': [{'verification_id': 'VERIFY_CONTROLLED_ROUTE', 'operation': 'HOST_DEFINED_OFFLINE_CHECK',
            'refs': ['file:run.py', 'file:checkout_app/server.py', 'file:legacy_compat.py'],
            'depends_on': ['alternate_default_route'], 'postcondition': postcondition}],
        'execution_order': ['alternate_default_route', 'VERIFY_CONTROLLED_ROUTE']}
    return session, proposal, catalog


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root', required=True, type=Path)
    p.add_argument('--sdk-root', required=True, type=Path)
    p.add_argument('--protocol-root', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--compare-frozen', action='store_true')
    args = p.parse_args(); require(not args.out.exists(), 'FRESH_SAME_PARENT_OUTPUT_REQUIRED')
    config = json.loads((ROOT / CONFIG).read_text())
    case = next(c for c in json.loads((ROOT / 'configs/stage2_terminal_route_repair_first_round_v1.json').read_text())['cases']
                if c['full_id'] == config['full_id'])
    archive = args.source_root / 'G3A/stage2/replication_v2/G3/natural_A/X4-T2/first_attempt.tar.gz'
    context = PrefixMCPContext(archive, full_id=case['full_id'], archive_sha256=case['archive_sha256'],
                               parent_checkpoint_hash=config['parent_checkpoint_hash'])
    try:
        require(context.parent['manifest']['remaining_horizon'] == config['remaining_horizon'], 'SOURCE_PARENT_BUDGET_DRIFT')
        envelope = freeze_task_envelope(context, TASKS['T2'],
            writable_refs=['file:' + path for path in context.parent['files']], branch_id='same-parent-native-mcp-engineering',
            max_actions=config['max_actions'], max_value_bytes=config['max_value_bytes'])
        compiler = ProposalAuthorityCompiler(context, envelope)
        session, proposal, catalog = scripted_proposal(context)
        authorization = compiler.compile(session, proposal)
        save(args.out / 'prefix_receipt.json', context.prefix_receipt)
        save(args.out / 'prefix_catalog.json', catalog)
        save(args.out / 'task_envelope.json', envelope)
        task = proposal['verification_tasks'][0]
        def verify(root):
            value = probe(root)
            passed = (value['controlled_launcher_selection'] == {'UNSET': ['current'], 'on': ['legacy'], 'off': ['current']}
                and all(r['status'] == 200 and r['body'] == {'status': 'pending_payment', 'amount_cents': 2500, 'method': r['method']}
                        for r in value['http_handler_contracts']['current'])
                and all(r['status'] == 410 for r in value['http_handler_contracts']['legacy']))
            return {'passed': passed, 'controlled_probe': value, 'scope': 'TWO_METHODS_ONE_CART_NOT_BROWSER_OR_REAL_PAYMENT'}
        bindings = {task['verification_id']: {**task, 'run': verify}}
        scripts = [{'content': json.dumps({'actions': [{'type': 'read_file', 'path': 'run.py'},
                    {'type': 'finalize', 'answer': 'Offline scripted native MCP continuation; no semantic repair verdict.'}]})}]
        scripts += [{'content': json.dumps({'actions': [{'type': 'finalize',
                    'answer': 'Offline scripted native MCP continuation; no semantic repair verdict.'}]})} for _ in range(3)]
        branch = SameParentMCPBranch(context, authorization, authorization.bundle, args.out / 'native_branch',
            script=OfflineScript(scripts), sdk_root=args.sdk_root, protocol_root=args.protocol_root, verifiers=bindings)
        receipt = asyncio.run(branch.run())
        require(receipt['native_repair_actions'] == 1 and receipt['native_mcp_invocations'] == 4
                and receipt['remaining_after'] == 56 and receipt['scripted_response_calls'] == 4
                and receipt['full_native_mcp_protocol_attached'] and not receipt['repair_success'], 'SAME_PARENT_MCP_CHECK_FAILED')
        after = branch.observer.graph.snapshot()
        require(not any(o['event_kind'] == 'REPAIR_AGENT_EXIT' for o in after['observations']), 'NO_SCRIPTED_FAKE_AGENT_EXIT')
        assessment = json.loads((branch.out / 'continuation_assessment.json').read_text())
        review = RepairReviewContext(context, branch.contract, context.graph, after, assessment,
            branch_source_reader=lambda o: read_capture_member(branch.out, o),
            semantic_rules=json.loads((ROOT / 'configs/r8_dynamic_semantic_audit_contract_v0.4.json').read_text()),
            lineage_rules=json.loads((ROOT / 'configs/stage2_r6_grade_semantic_audit_rules_v1.json').read_text()),
            repair_actor_id='OFFLINE_SCRIPTED_REPAIR_DRIVER')
        save(args.out / 'review_catalog.json', review.catalog())
        # Every historical prefix source is independently readable. No reviewer
        # is invoked; these checks do not adjudicate any semantic relationship.
        for observation in context.graph['observations']:
            review.read(observation['observation_id'])
        save(args.out / 'review_pending_receipt.json', review.pending_receipt())
        for name in ['full_graph_before.json', 'full_graph_after.json']:
            path = branch.out / name
            (branch.out / (name + '.gz')).write_bytes(gzip.compress(path.read_bytes(), mtime=0))
        save(args.out / 'recovery_assessment.json', branch.journal.reconcile(
            lambda ref: digest((branch.root / ref[5:]).read_bytes())))
        summary = seal({'schema': 'stage2-same-parent-native-mcp-check-v1',
            'classification': config['classification'], 'prefix_hash': context.prefix_receipt['prefix_hash'],
            'same_parent_checkpoint_hash': context.parent_checkpoint_hash, 'parent_native_sequence': 4,
            'prefix_observations': len(context.graph['observations']), 'prefix_nodes': len(context.graph['nodes']),
            'prefix_native_checkpoints': context.prefix_receipt['native_checkpoint_count'],
            'prefix_mcp_invocations': context.prefix_receipt['mcp_invocation_count'],
            'new_observations': receipt['new_observations'], 'final_observations': len(after['observations']),
            'final_nodes': len(after['nodes']), 'native_repair_actions': 1, 'new_native_mcp_invocations': 4,
            'scripted_continuation_turns': 4, 'remaining_before': 60, 'remaining_after': 56,
            'provider_calls': 0, 'frozen_natural_experiments_rerun': False, 'future_suffix_supplied': False,
            'actual_agent_exit_observed': False, 'agent_generated_proposal': False,
            'repair_success': False, 'independent_review_invoked': False,
            'independent_review_state': review.readiness(), 'remaining_gates': config['remaining_gates'],
            'historical_missing_evidence': config['historical_missing_evidence'], 'live_execution_enabled': False}, 'summary_hash')
        save(args.out / 'summary.json', summary)
        dependencies = json.loads((ROOT / 'stage2/replication_v2/native_continuation_authority_integration_v1/seal.json').read_text())['implementation_hashes']
        for path in ['scripts/check_stage2_same_parent_native_mcp.py', 'stage2/route_repair/prefix_context.py',
                     'stage2/route_repair/mcp_same_parent.py', 'stage2/route_repair/independent_review.py',
                     'stage2/monitor_enhancement/frozen_archive.py', 'arena/checkpoint_chronology.py',
                     'stage2/native_v7/x4_mcp/runner.py', 'stage2/native_v7/x4_mcp/server.py',
                     'stage2/native_v7/x4_mcp/client_call.py', 'stage2/native_v7/x4_mcp/wire_proxy.py']:
            dependencies[path] = digest((ROOT / path).read_bytes())
        inputs = {path: digest((ROOT / path).read_bytes()) for path in [CONFIG,
            'configs/stage2_terminal_route_repair_first_round_v1.json',
            'configs/r8_dynamic_semantic_audit_contract_v0.4.json', 'configs/stage2_r6_grade_semantic_audit_rules_v1.json']}
        artifacts = {str(path.relative_to(args.out)): digest(path.read_bytes()) for path in sorted(args.out.rglob('*'))
                     if path.is_file() and not str(path.relative_to(args.out)).startswith('native_branch/application/')
                     and '__pycache__' not in path.parts and not path.name.endswith('.pyc')
                     and path.name not in {'full_graph_before.json', 'full_graph_after.json'}}
        sealed = seal({'schema': 'stage2-same-parent-native-mcp-seal-v1', 'archive_sha256': case['archive_sha256'],
            'classification': config['classification'], 'artifact_hashes': artifacts,
            'implementation_hashes': dependencies, 'input_hashes': inputs,
            'summary_hash': summary['summary_hash'], 'sdk_commit': config['sdk_commit'],
            'protocol_commit': config['protocol_commit']}, 'seal_hash')
        save(args.out / 'seal.json', sealed)
        if args.compare_frozen:
            require(sealed == json.loads((FROZEN / 'seal.json').read_text()), 'SAME_PARENT_SEAL_REPRODUCTION_DRIFT')
            for path, expected in artifacts.items():
                require(digest((FROZEN / path).read_bytes()) == expected
                        and (args.out / path).read_bytes() == (FROZEN / path).read_bytes(), 'SAME_PARENT_ARTIFACT_DRIFT:' + path)
        print(json.dumps({'sealed_reproduction': args.compare_frozen, 'artifacts': len(artifacts),
            'prefix_observations': len(context.graph['observations']), 'new_observations': receipt['new_observations'],
            'official_mcp_calls': 4, 'provider_calls': 0, 'repair_success': False, 'remaining_horizon': 56}))
    finally: context.close()


if __name__ == '__main__': main()
