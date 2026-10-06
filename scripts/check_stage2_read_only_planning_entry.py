#!/usr/bin/env python3
"""Exercise actor protocol and MCP host entry without invoking a model."""
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
from stage2.route_repair.branch_fields import require, save, seal, BranchConstraintError
from stage2.route_repair.prefix_context import PrefixMCPContext
from stage2.route_repair.proposal_authority import freeze_task_envelope
from stage2.route_repair.planning_actor import OfflinePlanningScript, ReadOnlyPlanningActorSession
from stage2.route_repair.planning_entry import OfflinePlanningRepairEntry
from stage2.route_repair.native_continuation import OfflineScript
from stage2.route_repair.checkout_route_probe import probe
from scripts.check_stage2_same_parent_native_mcp import scripted_proposal

CONFIG = 'configs/stage2_read_only_planning_entry_v1.json'
FROZEN = ROOT / 'stage2/replication_v2/read_only_planning_entry_integration_v1'


def response(payload): return {'content': json.dumps(payload, ensure_ascii=False, sort_keys=True)}


def no_action(decision, refs, ids):
    return response({'kind': 'FINAL', 'decision': decision,
        'reason': 'Offline protocol fixture; no semantic repair verdict or global no-defect certification.',
        'inspected_refs': refs, 'witness_ids': ids,
        'unknown_relations': ['Actual historical launcher use and semantic adoption remain unknown.']})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['source-root', 'sdk-root', 'protocol-root', 'out']:
        p.add_argument('--' + name, required=True, type=Path)
    p.add_argument('--compare-frozen', action='store_true'); args = p.parse_args()
    require(not args.out.exists(), 'FRESH_PLANNING_ENTRY_CHECK_REQUIRED')
    config = json.loads((ROOT / CONFIG).read_text())
    native = json.loads((ROOT / config['same_parent_config']).read_text())
    case = next(c for c in json.loads((ROOT / 'configs/stage2_terminal_route_repair_first_round_v1.json').read_text())['cases']
                if c['full_id'] == native['full_id'])
    archive = args.source_root / 'G3A/stage2/replication_v2/G3/natural_A/X4-T2/first_attempt.tar.gz'
    context = PrefixMCPContext(archive, full_id=case['full_id'], archive_sha256=case['archive_sha256'],
                               parent_checkpoint_hash=native['parent_checkpoint_hash'])
    try:
        # Freeze capability envelope before constructing the explicitly scripted
        # source proposal. No proposed value is in this host capability grant.
        envelope = freeze_task_envelope(context, TASKS['T2'], writable_refs=['file:' + p for p in context.parent['files']],
            branch_id='read-only-planning-entry-engineering', max_actions=native['max_actions'],
            max_value_bytes=native['max_value_bytes'])
        fixture, proposal, _ = scripted_proposal(context)
        names = {'complete_catalog': 'catalog', 'node_context': 'node', 'read_file': 'file',
                 'observation_source': 'observation', 'select_source_witness': 'witness'}
        # These fixed responses replay engineering fixture tool requests, not a
        # model-generated diagnosis. The new session rebuilds its own ledgers.
        repair = [response({'kind': 'TOOL', 'name': names[q['operation']], 'arguments': q['request']})
                  for q in fixture.query_log]
        repair.append(response({'kind': 'FINAL', 'decision': 'REPAIR', 'proposal': proposal}))
        text = context.read_file('file:README.md')['content']
        no_repair = [response({'kind': 'TOOL', 'name': 'file', 'arguments': {'ref': 'file:README.md'}}),
                     response({'kind': 'TOOL', 'name': 'witness', 'arguments': {'read_id': 'read:1', 'start': 0, 'end': len(text)}}),
                     no_action('NO_REPAIR_NEEDED', ['file:README.md'], ['witness:1'])]
        unresolved = [response({'kind': 'TOOL', 'name': 'catalog', 'arguments': {}}), no_action('UNRESOLVED', [], [])]
        malformed = [{'content': '{"kind":"TOOL","name":"write_file","arguments":{}}'}]
        task = proposal['verification_tasks'][0]
        def verify(root):
            value = probe(root)
            passed = (value['controlled_launcher_selection'] == {'UNSET': ['current'], 'on': ['legacy'], 'off': ['current']}
                and all(r['status'] == 200 and r['body'] == {'status': 'pending_payment', 'amount_cents': 2500, 'method': r['method']}
                        for r in value['http_handler_contracts']['current'])
                and all(r['status'] == 410 for r in value['http_handler_contracts']['legacy']))
            return {'passed': passed, 'controlled_probe': value, 'scope': 'TWO_METHODS_ONE_CART_NOT_BROWSER_OR_REAL_PAYMENT'}
        verifiers = {task['verification_id']: {**task, 'run': verify}}
        scripts = [{'content': json.dumps({'actions': [{'type': 'read_file', 'path': 'run.py'},
                     {'type': 'finalize', 'answer': 'Offline scripted MCP continuation; no semantic verdict.'}]})}]
        scripts += [{'content': json.dumps({'actions': [{'type': 'finalize',
                    'answer': 'Offline scripted MCP continuation; no semantic verdict.'}]})} for _ in range(3)]
        results = {}
        for label, rows in [('repair', repair), ('no_repair', no_repair), ('unresolved', unresolved), ('malformed', malformed)]:
            session = ReadOnlyPlanningActorSession(context, envelope, OfflinePlanningScript(rows),
                args.out / label / 'planning', actor_id=config['actor_id'], max_calls=config['max_planning_calls'],
                max_response_bytes=config['max_planning_response_bytes'])
            entry = OfflinePlanningRepairEntry(session, args.out / label / 'host')
            try:
                receipt = asyncio.run(entry.run(script=OfflineScript(scripts) if label == 'repair' else None,
                    sdk_root=args.sdk_root if label == 'repair' else None,
                    protocol_root=args.protocol_root if label == 'repair' else None,
                    verifiers=verifiers if label == 'repair' else None))
                require(label != 'malformed', 'MALFORMED_PLANNING_MESSAGE_ACCEPTED')
            except BranchConstraintError as exc:
                require(label == 'malformed' and str(exc) == 'READ_ONLY_PLANNING_TOOL_REQUIRED',
                        'UNEXPECTED_PLANNING_ENTRY_FAILURE:' + str(exc))
                receipt = json.loads((entry.out / 'entry_receipt.json').read_text())
            outcome = json.loads((session.out / 'outcome.json').read_text())
            require(outcome['tools_revoked'] and not outcome['actual_repair_agent_exit'], 'FALSE_ACTOR_EXIT')
            # Verify exact transcript artifact bytes independently of the actor.
            transcript = json.loads((session.out / 'transcript.json').read_text())
            for row in transcript:
                raw = (session.out / row['member']).read_bytes()
                require(digest(raw) == row['member_hash'] and digest(gzip.decompress(raw)) == row['content_hash'],
                        'PLANNING_TRANSCRIPT_SOURCE_DRIFT')
            require(outcome['transcript_hash'] == digest(transcript), 'TRANSCRIPT_LEDGER_DRIFT')
            results[label] = {'state': receipt['state'], 'decision': receipt['decision'],
                'actor_calls': outcome['actor_calls'], 'tool_queries': outcome['tool_queries'],
                'native_branch_created': receipt['native_branch_created'], 'entry_hash': receipt['entry_hash']}
            if label == 'repair':
                native_receipt = receipt['native_branch_receipt']
                require(native_receipt['native_repair_actions'] == 1 and native_receipt['native_mcp_invocations'] == 4
                        and native_receipt['remaining_after'] == 56, 'NATIVE_BRANCH_CHECK_FAILED')
                branch = entry.out / 'native_branch'
                after = json.loads((branch / 'full_graph_after.json').read_text())
                require(not any(o['event_kind'] == 'REPAIR_AGENT_EXIT' for o in after['observations']), 'FALSE_SCRIPTED_REPAIR_EXIT')
                assessment = json.loads((branch / 'continuation_assessment.json').read_text())
                require(not assessment['repair_success'], 'FALSE_SCRIPTED_EFFECTIVENESS')
                for name in ['full_graph_before.json', 'full_graph_after.json']:
                    path = branch / name; (branch / (name + '.gz')).write_bytes(gzip.compress(path.read_bytes(), mtime=0))
            else:
                require(not receipt['native_branch_created'] and not (entry.out / 'native_branch').exists(),
                        'NO_ACTION_BRANCH_DISPATCHED')
        summary = seal({'schema': 'stage2-read-only-planning-entry-check-v1',
            'classification': config['classification'], 'same_parent_checkpoint_hash': context.parent_checkpoint_hash,
            'prefix_hash': context.prefix_receipt['prefix_hash'], 'cases': results,
            'provider_calls': 0, 'official_mcp_invocations': 4, 'native_repair_actions': 1,
            'subject_scripted_turns': 4, 'remaining_before': 60, 'remaining_after': 56,
            'actual_repair_agent_exit': False, 'agent_generated_proposal': False,
            'repair_success': False, 'independent_review_invoked': False,
            'frozen_natural_experiments_rerun': False, 'live_execution_enabled': False,
            'remaining_gates': config['remaining_gates']}, 'summary_hash')
        save(args.out / 'summary.json', summary)
        dependencies = json.loads((ROOT / 'stage2/replication_v2/same_parent_native_mcp_integration_v1/seal.json').read_text())['implementation_hashes']
        for path in ['stage2/route_repair/planning_actor.py', 'stage2/route_repair/planning_entry.py',
                     'scripts/check_stage2_read_only_planning_entry.py']:
            dependencies[path] = digest((ROOT / path).read_bytes())
        artifacts = {str(path.relative_to(args.out)): digest(path.read_bytes()) for path in sorted(args.out.rglob('*'))
            if path.is_file() and '/native_branch/application/' not in str(path.relative_to(args.out))
            and '__pycache__' not in path.parts and not path.name.endswith('.pyc')
            and path.name not in {'full_graph_before.json', 'full_graph_after.json'}}
        sealed = seal({'schema': 'stage2-read-only-planning-entry-seal-v1', 'artifact_hashes': artifacts,
            'implementation_hashes': dependencies,
            'input_hashes': {path: digest((ROOT / path).read_bytes()) for path in [CONFIG, config['same_parent_config']]},
            'archive_sha256': case['archive_sha256'], 'summary_hash': summary['summary_hash']}, 'seal_hash')
        save(args.out / 'seal.json', sealed)
        if args.compare_frozen:
            require(sealed == json.loads((FROZEN / 'seal.json').read_text()), 'PLANNING_ENTRY_SEAL_DRIFT')
            for path, expected in artifacts.items():
                require(digest((FROZEN / path).read_bytes()) == expected
                        and (args.out / path).read_bytes() == (FROZEN / path).read_bytes(), 'PLANNING_ENTRY_ARTIFACT_DRIFT:' + path)
        print(json.dumps({'sealed_reproduction': args.compare_frozen, 'artifacts': len(artifacts),
            'cases': {k: v['state'] for k, v in results.items()}, 'provider_calls': 0, 'repair_success': False}))
    finally: context.close()


if __name__ == '__main__': main()
