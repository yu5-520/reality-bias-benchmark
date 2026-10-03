#!/usr/bin/env python3
"""Verify early native host restoration and automatic proposal authority offline."""
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
from stage2.route_repair.branch_fields import require, save, seal, verify_seal
from stage2.route_repair.route_context import CompleteRouteContext
from stage2.route_repair.planning_session import RoutePlanningSession
from stage2.route_repair.proposal_authority import freeze_task_envelope, ProposalAuthorityCompiler
from stage2.route_repair.native_continuation import (
    load_host_parent, continuation_blocker, OfflineScript, OfflineNativeContinuation,
)

CONFIG = 'configs/stage2_native_continuation_authority_v1.json'
FROZEN = ROOT / 'stage2/replication_v2/native_continuation_authority_integration_v1'


def replay_inspection(context, old_bundle):
    session = RoutePlanningSession(context, old_bundle['proposal']['original_task'], proposal_origin=old_bundle['origin'])
    for row in old_bundle['query_log']:
        op, r = row['operation'], row['request']
        if op == 'complete_catalog': session.catalog()
        elif op == 'node_context': session.node(r['ref'])
        elif op == 'read_file': session.file(r['ref'], r['checkpoint_hash'])
        elif op == 'current_host_answer': session.current_answer()
        elif op == 'observation_source': session.observation(r['observation_id'], r['ref'])
        elif op == 'select_source_witness': session.witness(r['read_id'], r['start'], r['end'])
        else: require(False, 'UNKNOWN_PRIOR_QUERY')
        require(session.query_log[-1] == row, 'PRIOR_SOURCE_INSPECTION_DRIFT')
    return session


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', required=True, type=Path)
    parser.add_argument('--graph-root', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--compare-frozen', action='store_true')
    args = parser.parse_args()
    require(not args.out.exists(), 'FRESH_ENGINEERING_OUTPUT_REQUIRED')
    config = json.loads((ROOT / CONFIG).read_text())
    case = next(c for c in json.loads((ROOT / 'configs/stage2_terminal_route_repair_first_round_v1.json').read_text())['cases']
                if c['full_id'] == config['full_id'])
    with gzip.open(args.graph_root / (case['full_id'] + '.json.gz')) as stream:
        graph = json.load(stream)['graph']
    archive = args.source_root / 'G3A/stage2/replication_v2/G3/natural_A/X4-T2/first_attempt.tar.gz'
    context = CompleteRouteContext(graph, archive, case)
    try:
        # Task-native capability envelope is frozen before retrieving the old
        # actor proposal. No field position or replacement value is preselected.
        limits = config['task_envelope']
        envelope = freeze_task_envelope(context, TASKS['T2'],
            writable_refs=['file:' + p for p in context.files_by_checkpoint[case['terminal_checkpoint_hash']]],
            branch_id='automatic-source-proposal-terminal-fixture', max_actions=limits['max_actions'],
            max_value_bytes=limits['max_value_bytes'], host_answer_allowed=limits['host_answer_allowed'])
        compiler = ProposalAuthorityCompiler(context, envelope)
        prior_root = ROOT / 'stage2/replication_v2/route_planning_session_integration_v1'
        prior_seal = json.loads((prior_root / 'seal.json').read_text())
        verify_seal(prior_seal, 'seal_hash')
        for path, expected in prior_seal['artifact_hashes'].items():
            require(digest((prior_root / path).read_bytes()) == expected, 'PRIOR_ARTIFACT_DRIFT')
        for path, expected in {**prior_seal['implementation_hashes'], **prior_seal['input_hashes']}.items():
            require(digest((ROOT / path).read_bytes()) == expected, 'PRIOR_DEPENDENCY_DRIFT:' + path)
        old_bundle = json.loads((ROOT / config['terminal_proposal_source']).read_text())
        session = replay_inspection(context, old_bundle)
        authorization = compiler.compile(session, old_bundle['proposal'])
        save(args.out / 'task_envelope.json', envelope)
        save(args.out / 'bound_proposal_authorization.json', authorization.receipt)
        save(args.out / 'automatically_compiled_bundle.json', authorization.bundle)

        # Retrospective engineering inventory, not evidence exposed to a future
        # planner. Each parent is verified independently, not joined by inferred
        # cross-clock chronology. Duplicate monitor annotations stay annotations.
        inventory = []
        for cp in dict.fromkeys(r['checkpoint_hash'] for r in context.ledger['checkpoints']):
            p = load_host_parent(context, cp)
            inventory.append({'checkpoint_hash': cp, 'event_ref': p['manifest']['event_ref'],
                'native_sequence': len(p['state']['history']), 'remaining_horizon': p['manifest']['remaining_horizon'],
                'stop_reason': p['state']['stop_reason'], 'host_continuation_blocker': continuation_blocker(p),
                'application_files_verified': len(p['files']), 'monitor_annotations': p['monitor_annotations'],
                'manifest_source': context.locator('checkpoints/' + cp + '/manifest.json'),
                'native_state_source': context.locator('checkpoints/' + cp + '/native_state.json'),
                'full_foreign_runtime_attached': False})
        save(args.out / 'verified_host_parent_inventory.json', inventory)
        cp = config['native_parent_checkpoint_hash']
        selected = load_host_parent(context, cp)
        require(len(selected['state']['history']) == config['native_parent_sequence']
                and selected['manifest']['remaining_horizon'] == config['native_parent_remaining_horizon'],
                'PINNED_EARLY_PARENT_DRIFT')
        require(any(r['boundary'] == 'FIRST_MONITOR_REPAIR_ELIGIBLE_POINT'
                    for r in selected['monitor_annotations']), 'PINNED_ELIGIBILITY_ANNOTATION_MISSING')
        # A fixed specialist/entry-agent finalize probe exercises the original
        # routing semantics; it makes no assessment or repair recommendation.
        content = json.dumps({'actions': [{'type': 'finalize',
            'answer': 'Offline scripted host continuation probe; no repair efficacy claim.'}]}, ensure_ascii=False)
        script = OfflineScript([{'content': content} for _ in range(4)])
        branch = OfflineNativeContinuation(context, cp, args.out / 'native_host_branch', script=script,
            observed_foreign_refs=selected['manifest']['external_carrier_refs'])
        receipt = asyncio.run(branch.run())
        require(receipt['scripted_response_calls'] == 4 and receipt['continued_turns'] == 4
                and receipt['remaining_after'] == 56 and receipt['stop_reason'] == 'finalized',
                'NATIVE_HOST_SCRIPTED_CONTINUATION_DRIFT')
        for name in ['full_graph_before.json', 'full_graph_after.json']:
            path = branch.out / name
            (branch.out / (name + '.gz')).write_bytes(gzip.compress(path.read_bytes(), mtime=0))
        graph_after = branch.observer.graph.snapshot()
        require(not any(o['event_kind'] == 'REPAIR_AGENT_EXIT' for o in graph_after['observations']),
                'SCRIPT_MUST_NOT_FABRICATE_ACTUAL_REPAIR_EXIT')
        terminal = next(r for r in inventory if r['checkpoint_hash'] == case['terminal_checkpoint_hash'])
        require(terminal['host_continuation_blocker'] == 'STOPPED_NATIVE_PARENT_NO_REOPEN'
                and terminal['remaining_horizon'] == 28, 'TERMINAL_REOPEN_GATE_DRIFT')
        summary = seal({'schema': 'stage2-native-continuation-authority-check-v1',
            'classification': 'TWO_SEPARATE_OFFLINE_ENGINEERING_CHECKS_NOT_END_TO_END_AGENT_REPAIR',
            'terminal_proposal': {'authorization_hash': authorization.receipt['authorization_hash'],
                'application_actions_compiled': len(authorization.bundle['application_plan']['actions']),
                'host_answer_fields_compiled': ['/answer'], 'native_repair_actions_executed': 0,
                'agent_generated': False, 'field_values_prescribed_by_envelope': False},
            'early_native_host': {'checkpoint_hash': cp, 'native_sequence_before': 4,
                'native_sequence_after': 8, 'remaining_before': 60, 'remaining_after': 56,
                'scripted_response_calls': 4, 'new_observations': len(graph_after['observations']),
                'round_trip_verified': True, 'future_graph_used': False,
                'full_foreign_runtime_attached': False, 'actual_repair_agent_exit_observed': False},
            'verified_host_parent_count': len(inventory),
            'terminal_with_remaining_budget_refused': True, 'provider_calls': 0,
            'natural_experiments_rerun': False, 'repair_success': False,
            'independent_semantic_review_invoked': False, 'live_execution_enabled': False,
            'remaining_gates': config['remaining_gates']}, 'summary_hash')
        save(args.out / 'summary.json', summary)
        # Every retained artifact is reproduced, including every source capture.
        implementations = {
            **json.loads((ROOT / 'stage2/replication_v2/monitor_repair_system_integration_v1/seal.json').read_text())['implementation_hashes'],
            **prior_seal['implementation_hashes'],
        }
        for path in ['scripts/check_stage2_native_continuation_authority.py',
                     'stage2/route_repair/proposal_authority.py', 'stage2/route_repair/native_continuation.py',
                     'stage2/r7_prospective_v1/engineering_b_runner.py']:
            implementations[path] = digest((ROOT / path).read_bytes())
        inputs = {CONFIG: digest((ROOT / CONFIG).read_bytes()),
                  'configs/stage2_terminal_route_repair_first_round_v1.json': digest((ROOT / 'configs/stage2_terminal_route_repair_first_round_v1.json').read_bytes())}
        for path in [config['terminal_proposal_source'], 'stage2/replication_v2/route_planning_session_integration_v1/seal.json']:
            inputs[path] = digest((ROOT / path).read_bytes())
        artifacts = {str(p.relative_to(args.out)): digest(p.read_bytes()) for p in sorted(args.out.rglob('*'))
                     if p.is_file() and not str(p.relative_to(args.out)).startswith('native_host_branch/application/')
                     and p.name not in {'full_graph_before.json', 'full_graph_after.json'}}
        sealed = seal({'schema': 'stage2-native-continuation-authority-seal-v1',
            'archive_sha256': case['archive_sha256'], 'artifact_hashes': artifacts,
            'implementation_hashes': implementations, 'input_hashes': inputs,
            'classification': summary['classification'], 'summary_hash': summary['summary_hash']}, 'seal_hash')
        save(args.out / 'seal.json', sealed)
        if args.compare_frozen:
            require(sealed == json.loads((FROZEN / 'seal.json').read_text()), 'ENGINEERING_SEAL_REPRODUCTION_DRIFT')
            for path, expected in sealed['artifact_hashes'].items():
                require(digest((FROZEN / path).read_bytes()) == expected
                        and (args.out / path).read_bytes() == (FROZEN / path).read_bytes(),
                        'ENGINEERING_ARTIFACT_REPRODUCTION_DRIFT:' + path)
        print(json.dumps({'sealed_reproduction': args.compare_frozen,
            'artifacts': len(artifacts), 'provider_calls': 0, 'repair_success': False,
            'early_native_turns': 4, 'remaining_horizon': 56, 'summary_hash': summary['summary_hash']}))
    finally:
        context.close()


if __name__ == '__main__': main()
