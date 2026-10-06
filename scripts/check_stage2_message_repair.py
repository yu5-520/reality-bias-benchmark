#!/usr/bin/env python3
"""Exercise the active message chain with loopback HTTP and official native MCP.

Scripted replies test delivery and preservation, not autonomous diagnosis or
causal efficacy. Original natural trajectories are never executed or rewritten.
"""
import argparse
import asyncio
import gzip
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from stage2.r7_checkpoint_v1.common import digest, stable_json_bytes, file_tree_manifest
from stage2.native_v7.software_host_v1 import TASKS
from stage2.route_repair.branch_fields import require, save, seal, BranchConstraintError
from stage2.route_repair.planning_session import RoutePlanningSession
from stage2.route_repair.native_message import ATTRIBUTION
from stage2.route_repair.http_fixture import FixtureHTTPServer, fixture_reply
from stage2.route_repair.source_navigation import version_handle
from stage2.route_repair.connected_provider import LoopbackHTTPTransport
from stage2.monitor_enhancement.snapshot_append import AppendOnlyEvidenceGraph
from stage2.route_repair.branch_fields import verify_seal
from scripts.run_stage2_connected_repair import load_context, execute

FROZEN = ROOT / 'stage2/replication_v2/pending_message_repair_v1'


def scripted_proposal(context):
    session = RoutePlanningSession(context, TASKS['T2']); session.catalog()
    refs = ['file:web/app.js', 'file:web/index.html', 'state:host_parent']
    witnesses = []
    for ref in refs[:2]:
        first = context.file_versions[ref][0]['checkpoint_hash']
        for cp in [first, context.parent_checkpoint_hash]:
            r = session.file(ref, cp)
            witnesses.append(session.witness(r['read_id'], 0, len(r['text']))['witness_id'])
    r = session.message('/inbox/release_lead/0/content')
    witnesses.append(session.witness(r['read_id'], 0, len(r['text']))['witness_id'])
    # Actual outgoing native write, not merely file presence or failed read.
    def actual_write(o):
        if (o['event_kind'] != 'MCP_WIRE_RECORD'
                or not o['source_locator']['member'].endswith('.client_to_server.bin')
                or o['source_locator'].get('json_pointer')): return False
        payload = json.loads(context.observation_source(o['observation_id'])['source_text'])
        return (isinstance(payload, dict) and payload.get('method') == 'tools/call' and payload['params'].get('name') == 'write_file'
                and payload['params']['arguments'].get('path') == 'web/app.js')
    row = next(o for o in context.graph['observations'] if actual_write(o))
    native_ref = row['object_refs'][0]
    refs.append(native_ref)
    native = session.observation(row['observation_id'], native_ref)
    witnesses.append(session.witness(native['read_id'], 0, len(native['text']))['witness_id'])
    test_refs = sorted('file:' + p for p in context.parent['files'] if p.startswith('tests/') and p.endswith('.py'))
    for ref in test_refs: session.node(ref)
    clause = 'No changes were needed, so I left the files untouched to avoid breaking the existing flow.'
    require(r['text'].count(clause) == 1, 'EXACT_PROCESS_CLAUSE_REQUIRED')
    start = r['text'].index(clause); end = start + len(clause)
    clause_witness = session.span(r['read_id'], clause)
    replacement = (
        'Process correction: the available prefix records a '
        'write to web/app.js and web/index.html at native decision 10; the initial snapshots lack that form '
        'and handler. Therefore the broad process statement "No changes were needed, so I left the files '
        'untouched" is not supported for this trajectory. Preserve the existing working payment flow and '
        'the original task. This annotation corrects process accounting only; it does not establish that '
        'the coordinator has read or adopted the old claim, nor certify complete functionality.')
    expected_value = ATTRIBUTION + r['text'][:start] + replacement + r['text'][end:]
    action = {'action_id': 'correct_pending_process_account', 'target_ref': 'state:host_parent',
        'kind': 'PENDING_MESSAGE_REPLACE', 'field_path': '/inbox/release_lead/0/content',
        'before_value_hash': r['text_hash'], 'depends_on': [],
        'start': clause_witness['start'], 'end': clause_witness['end'],
        'before_span_hash': clause_witness['span_hash'], 'replacement': replacement,
        'diagnosis_ids': ['prefix-process-account']}
    cap = {'verification_id': 'VERIFY_NATIVE_TESTS', 'operation': 'HOST_DEFINED_OFFLINE_CHECK',
        'refs': test_refs, 'postcondition': 'Original native application tests pass.',
        'depends_on': [action['action_id']]}
    proposal = {'schema': 'stage2-complete-route-proposal-v1', 'original_task': TASKS['T2'],
        'graph_hash': context.graph['graph_hash'], 'archive_sha256': context.case['archive_sha256'],
        'parent_checkpoint_hash': context.parent_checkpoint_hash,
        'route_refs': refs + test_refs, 'modify_refs': ['state:host_parent'],
        'preserve_refs': refs[:2] + [native_ref], 'verify_refs': test_refs,
        'diagnoses': [{'claim_id': 'prefix-process-account', 'source_ref': 'file:web/app.js',
            'destination_ref': 'state:host_parent', 'status': 'SOURCE_BOUND_CLAIM',
            'adoption_status': 'NOT_ESTABLISHED',
            'meaning_before': 'Initial file and actual native write record establish a prefix implementation change.',
            'meaning_after': 'The pending specialist handoff claims that the trajectory needed no changes.',
            'authority_effect': 'A pending process account may be used by the coordinator; use is not yet established.',
            'limitation': 'Retrospective selected checkpoint, not a certified earliest causal entry. Scripted diagnosis only.',
            'witness_ids': witnesses}],
        'unknown_relations': ['Original coordinator consumption and downstream adoption remain unestablished.',
            'No counterfactual efficacy is inferred from scripted continuation.'],
        'expected_postconditions': ['Attributed correction delivered through the original inbox; unrelated state retained.'],
        'application_actions': [], 'host_answer': None, 'host_message': action,
        'verification_tasks': [cap], 'execution_order': [action['action_id'], cap['verification_id']]}
    return session, proposal, expected_value


def run(args):
    require(not args.out.exists(), 'FRESH_MESSAGE_REPAIR_RUN_REQUIRED')
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    context = load_context(args.source_root, 'mechanism')
    try:
        session, proposal, expected_value = scripted_proposal(context)
        names = {'complete_catalog': 'catalog', 'node_context': 'node', 'read_file': 'file',
            'current_pending_message': 'message', 'observation_source': 'observation', 'select_source_witness': 'witness'}
        contents = []
        for q in session.query_log:
            tool, arguments = names[q['operation']], q['request']
            if q['operation'] == 'read_file':
                ref = arguments['ref']
                row = next(r for r in context.file_versions[ref] if r['checkpoint_hash'] == arguments['checkpoint_hash'])
                tool, arguments = 'read_version', {'version_handle': version_handle(context, ref, row)}
            contents.append(json.dumps({'kind': 'TOOL', 'name': tool, 'arguments': arguments}))
        contents.append(json.dumps({'kind': 'FINAL', 'decision': 'REPAIR', 'proposal': proposal}))
        require(len(contents) <= 16, 'MESSAGE_FIXTURE_PLANNING_BUDGET')
        # Five original queued roles run before the coordinator. Their normal
        # read actions keep the queue order intact; no role is skipped or forced.
        read = json.dumps({'actions': [{'type': 'read_file', 'path': 'web/app.js'}]})
        terminal = json.dumps({'actions': [{'type': 'finalize', 'answer':
            'Scripted delivery check: the feature exists after changes in this trajectory; preserve the working flow.'}]})
        rows = [fixture_reply(c) for c in contents] + [fixture_reply(read)] * 5 + [fixture_reply(terminal)]
        # Fixed port makes sealed bindings independent of local socket allocation.
        with FixtureHTTPServer(rows, port=18082) as server:
            result = asyncio.run(execute(context, LoopbackHTTPTransport(server.port), args.out,
                                        args.sdk_root, args.protocol_root))
            branch = args.out / 'host/native_branch'
            before = context.parent['state']
            paused = json.loads((branch / 'paused_state.json').read_bytes())
            after = json.loads((branch / 'native_state_after.json').read_bytes())
            expected = json.loads(json.dumps(before))
            expected['inbox']['release_lead'][0]['content'] = expected_value
            require(paused == expected, 'MESSAGE_ONLY_NATIVE_FIELD_PRESERVATION')
            require(file_tree_manifest(branch / 'application') == context.parent['manifest']['application_file_hashes'],
                    'MESSAGE_REPAIR_CHANGED_APPLICATION')
            require(after['history'][:15] == before['history'] and len(after['history']) == 21
                    and after['max_turns'] == 64 and after['stop_reason'] == 'finalized', 'MESSAGE_NATIVE_CLOSURE_DRIFT')
            subject = branch / 'provider_exchanges'
            prompt = json.loads((subject / '0006/request.bin').read_bytes())
            native_prompt = json.loads(prompt['messages'][1]['content'])
            delivered = [m['content'] for m in native_prompt['inbox']]
            require(expected_value in delivered, 'CORRECTION_NOT_DELIVERED_TO_COORDINATOR')
            require(before['inbox']['release_lead'][0]['content'] not in delivered,
                    'UNREPAIRED_CLAIM_STILL_DELIVERED')
            release = json.loads((branch / 'phase_receipt.json').read_bytes())['release']
            require(not release['actual_repair_agent_exit'] and not result['repair_success'], 'SCRIPT_CANNOT_CERTIFY_EFFECT')
            require(server.position == len(rows) and result['subject_calls'] == 6, 'MESSAGE_NATIVE_CALL_COUNT')
        require(digest(Path(context.access.archive.name).read_bytes()) == context.case['archive_sha256'], 'NATURAL_ARCHIVE_CHANGED')
        summary = seal({'schema': 'stage2-pending-message-repair-summary-v1',
            'classification': 'SCRIPTED_HTTP_OFFICIAL_MCP_NATIVE_DELIVERY_CHECK_NOT_MODEL_EFFICACY',
            'parent_checkpoint_hash': context.parent_checkpoint_hash, 'archive_sha256': context.case['archive_sha256'],
            'planning_http_exchanges': len(contents), 'subject_http_exchanges': 6,
            'native_host_message_writes': 1, 'native_application_writes': 0,
            'native_mcp_invocations': result['native_mcp_invocations'],
            'native_history_before': 15, 'native_history_after': 21,
            'native_ceiling': 64, 'remaining_before': 49, 'remaining_after': 43,
            'native_stop_reason': 'finalized', 'original_sender_preserved': True,
            'correction_present_in_actual_native_request': True,
            'unrelated_fields_and_files_preserved': True, 'frozen_archive_preserved': True,
            'original_framework_and_protocol_modified': False,
            'provider_calls': 0, 'actual_repair_agent_exit': False, 'repair_success': False,
            'independent_semantic_review_invoked': False, 'natural_reruns': 0,
            'counterfactual_effect_established': False}, 'summary_hash')
        save(args.out / 'summary.json', summary)
        # Retain exact HTTP/MCP bytes, captures, checkpoints and receipts once.
        # Prefix graph comes from the frozen archive; graph_delta reconstructs
        # the after snapshot. Duplicate planning captures and derived catalogs
        # are retained in the CI artifact, not duplicated in this evidence pack.
        old_obs = {r['observation_id'] for r in context.graph['observations']}
        old_edges = {r['edge_id'] for r in context.graph['edges']}
        after_graph = json.loads((branch / 'full_graph_after.json').read_bytes())
        delta = {**after_graph,
            'observations': [r for r in after_graph['observations'] if r['observation_id'] not in old_obs],
            'edges': [r for r in after_graph['edges'] if r['edge_id'] not in old_edges],
            'base_graph_hash': context.graph['graph_hash']}
        save(args.out / 'graph_delta.json', delta)
        packed = {str(p.relative_to(args.out)): p.read_bytes().hex() for p in sorted(args.out.rglob('*'))
            if p.is_file() and not any(x in p.parts for x in ['application', 'native_wire', '__pycache__'])
            and not str(p.relative_to(args.out)).startswith('planning/exchanges/')
            and p.name not in {'full_graph_before.json', 'full_graph_after.json', 'independent_review_catalog.json'}
            and not p.name.endswith('.pyc')}
        (args.out / 'evidence.json.gz').write_bytes(gzip.compress(stable_json_bytes(packed), mtime=0))
        sources = ['stage2/route_repair/' + n + '.py' for n in ['native_message', 'proposal_authority',
            'planning_session', 'offline_system', 'connected_planning', 'connected_mcp', 'connected_provider', 'prefix_context', 'source_navigation']]
        sources += ['scripts/check_stage2_message_repair.py', 'scripts/run_stage2_connected_repair.py',
            'configs/stage2_connected_mechanism_v1.json']
        receipt = seal({'schema': 'stage2-pending-message-repair-seal-v1',
            'implementation_hashes': {n: digest((ROOT / n).read_bytes()) for n in sources},
            'artifact_hashes': {n: digest((args.out / n).read_bytes()) for n in ['summary.json', 'evidence.json.gz']},
            'archive_sha256': context.case['archive_sha256']}, 'seal_hash')
        save(args.out / 'seal.json', receipt)
        if args.compare_frozen:
            frozen = json.loads((FROZEN / 'seal.json').read_bytes()); verify_seal(frozen, 'seal_hash')
            for name, expected_hash in frozen['artifact_hashes'].items():
                require(digest((FROZEN / name).read_bytes()) == expected_hash, 'MESSAGE_FROZEN_ARTIFACT_DRIFT')
            require(receipt['implementation_hashes'] == frozen['implementation_hashes']
                    and receipt['archive_sha256'] == frozen['archive_sha256'], 'MESSAGE_REPAIR_IMPLEMENTATION_DRIFT')
            require((FROZEN / 'summary.json').read_bytes() == (args.out / 'summary.json').read_bytes(),
                    'MESSAGE_REPAIR_STABLE_POSTCONDITIONS_DRIFT')
            # Native unittest timing stays unmodified in both evidence packs;
            # raw exchange hashes are not required to match across executions.
            packed_frozen = json.loads(gzip.decompress((FROZEN / 'evidence.json.gz').read_bytes()))
            delta = json.loads(bytes.fromhex(packed_frozen['graph_delta.json']))
            require(delta.pop('base_graph_hash') == context.graph['graph_hash'], 'MESSAGE_FROZEN_GRAPH_BASE_DRIFT')
            delta['observations'] = sorted(context.graph['observations'] + delta['observations'], key=lambda r: r['observation_id'])
            delta['edges'] = sorted(context.graph['edges'] + delta['edges'],
                key=lambda r: (r['source_ref'], r['relation_type'], r['destination_ref'], r['edge_id']))
            AppendOnlyEvidenceGraph.from_snapshot(delta)
            save(args.out / 'comparison_receipt.json', {'stable_postconditions_match': True,
                'frozen_graph_and_artifacts_verified': True,
                'raw_pack_byte_identical': receipt['artifact_hashes'] == frozen['artifact_hashes'],
                'native_timing_or_bytes_normalized': False})
        print(json.dumps(summary))
    finally: context.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['source-root', 'sdk-root', 'protocol-root', 'out']:
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--compare-frozen', action='store_true')
    run(parser.parse_args())
