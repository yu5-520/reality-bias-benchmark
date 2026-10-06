#!/usr/bin/env python3
"""Replay frozen trial queries and failed authorization without provider calls."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_stage2_connected_repair import load_context
from stage2.native_v7.software_host_v1 import TASKS
from stage2.route_repair.planning_session import RoutePlanningSession
from stage2.route_repair.source_navigation import SourceNavigation
from stage2.route_repair.proposal_authority import freeze_task_envelope, ProposalAuthorityCompiler
from stage2.route_repair.branch_fields import BranchConstraintError

def inspect(source_root):
    retained = json.loads((ROOT / 'stage2/replication_v2/message_version_handle_trial_v1/retained_log_records.json').read_text())
    context = load_context(source_root, 'mechanism')
    try:
        session = RoutePlanningSession(context, TASKS['T2'])
        nav = SourceNavigation(context)
        queries, usage, final = [], [], None
        for row in retained['records']:
            if not row['retained_source'].endswith('/response.bin'):
                continue
            raw = row['raw_utf8'].encode()
            assert hashlib.sha256(raw).hexdigest() == row['sha256']
            response = json.loads(raw)
            usage.append(response['usage'])
            payload = json.loads(response['choices'][0]['message']['content'])
            if payload['kind'] == 'FINAL':
                final = payload
                continue
            tool, args = payload['name'], payload['arguments']
            assert tool in {'message', 'read_version', 'node'}
            result = nav.read(session, args['version_handle']) if tool == 'read_version' else getattr(session, tool)(**args)
            query = {'tool': tool, 'arguments': args, 'accepted': True}
            if tool == 'read_version':
                query['version'] = nav._versions[args['version_handle']]
                query['source_read'] = result
                query['parent_content'] = context.read_file(result['ref'], context.parent_checkpoint_hash)['content']
            elif tool == 'message':
                query['source_read'] = result
            queries.append(query)
        assert len(usage) == 5 and len(queries) == 4 and len(session.witnesses) == 0
        envelope = freeze_task_envelope(context, TASKS['T2'], writable_refs=[],
            branch_id='connected-first-attempt', max_actions=1, max_value_bytes=65536,
            message_fields=['/inbox/release_lead/0/content'])
        try:
            ProposalAuthorityCompiler(context, envelope).compile(session, final['proposal'])
        except BranchConstraintError as exc:
            failure = str(exc)
        else:
            raise AssertionError('Frozen proposal unexpectedly accepted')
        assert failure == 'CURRENT_MESSAGE_WITNESS_REQUIRED'
        return {'schema': 'stage2-version-handle-trial-offline-inspection-v1',
            'run_id': retained['run_id'], 'failure_reproduced': failure,
            'queries': queries, 'read_count': len(session.reads), 'selected_witness_count': 0,
            'final_claimed_witness_ids': final['proposal']['diagnoses'][0]['witness_ids'],
            'original_provider_usage': usage, 'offline_provider_calls': 0,
            'native_writes': 0, 'historical_failure_reclassified': False,
            'semantic_efficacy_established': False}
    finally:
        context.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = inspect(args.source_root)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
