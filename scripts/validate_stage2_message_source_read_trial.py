#!/usr/bin/env python3
"""Verify the complete third planning attempt; no provider or native writes."""
import hashlib
import json
import argparse
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
EVIDENCE = ROOT / 'stage2/replication_v2/message_source_read_contract_trial_v1'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path)
    args = parser.parse_args()
    seal = json.loads((EVIDENCE / 'seal.json').read_bytes())
    observation = json.loads((EVIDENCE / 'observation.json').read_bytes())
    assert sha((EVIDENCE / 'evidence.zip').read_bytes()) == seal['artifact_zip_sha256'] == observation['artifact_zip_sha256']
    assert sha((EVIDENCE / 'observation.json').read_bytes()) == seal['observation_sha256']
    assert sha((ROOT / 'configs/stage2_message_source_read_contract_trial_v1.json').read_bytes()) == seal['trial_request_sha256']
    assert sha((EVIDENCE / 'planning_path_review.json').read_bytes()) == seal['derived_review_sha256']
    with zipfile.ZipFile(EVIDENCE / 'evidence.zip') as archive:
        names = {n for n in archive.namelist() if not n.endswith('/')}
        assert len(archive.namelist()) == len(set(archive.namelist()))
        assert names == set(seal['original_member_sha256'])
        for name in names:
            assert not Path(name).is_absolute() and '..' not in Path(name).parts
            assert sha(archive.read(name)) == seal['original_member_sha256'][name], name
        prefix = 'mechanism-source-read-contract-trial/'
        outcome = json.loads(archive.read(prefix + 'planning/outcome.json'))
        assert observation['outcome'] == outcome
        assert outcome['provider_calls'] == outcome['actor_calls'] == outcome['transport_attempts'] == 7
        assert outcome['state'] == 'FAILED' and outcome['failure']['message'] == 'NO_ACTION_SOURCE_NOT_INSPECTED'
        assert outcome['authorization_hash'] is None and outcome['native_actions_executed'] == 0
        assert outcome['tools_revoked'] and not outcome['actual_repair_agent_exit']
        queries = json.loads(archive.read(prefix + 'planning/query_log.json'))
        assert queries == observation['query_log'] and len(queries) == 6
        assert [q['operation'] for q in queries] == ['complete_catalog', 'current_pending_message'] + ['read_file'] * 4
        assert json.loads(archive.read(prefix + 'planning/witnesses.json')) == {}
        assert not any(n.startswith(prefix + 'host/native_branch/') for n in names)
        for response in observation['responses']:
            directory = prefix + f"planning_http/{response['sequence']:04d}/"
            request_raw, response_raw = [archive.read(directory + n + '.bin') for n in ['request', 'response']]
            assert sha(request_raw) == response['request_sha256']
            assert sha(response_raw) == response['response_sha256']
            actual = json.loads(response_raw)
            assert response['content'] == actual['choices'][0]['message']['content']
            assert response['usage'] == actual['usage'] and response['model'] == actual['model']
        request = json.loads(json.loads(archive.read(prefix + 'planning_http/0007/request.bin'))['messages'][1]['content'])
        progress = request['source_read_state']
        assert progress == observation['actual_source_read_state_before_final']
        assert len(progress['actual_source_reads']) == 5 and progress['selected_witnesses'] == []
        final = json.loads(observation['responses'][-1]['content'])
        assert final['kind'] == 'FINAL' and final['decision'] == 'NO_REPAIR_NEEDED'
        assert final['witness_ids'] == ['read:1', 'read:2', 'read:3', 'read:5']
        assert all(i in {r['read_id'] for r in progress['actual_source_reads']} for i in final['witness_ids'])
    assert not observation['independent_semantic_review_invoked'] and observation['subject_calls'] == 0
    assert observation['repair_effect'] == 'NOT_EVALUABLE_NO_REPAIR_OR_POST_EXIT_CONTINUATION'
    if args.source_root:
        from scripts.run_stage2_connected_repair import load_context
        from stage2.route_repair.planning_session import RoutePlanningSession
        from stage2.native_v7.software_host_v1 import TASKS
        review = json.loads((EVIDENCE / 'planning_path_review.json').read_bytes())
        context = load_context(args.source_root, 'mechanism')
        try:
            assert review['archive_sha256'] == context.case['archive_sha256']
            assert review['parent_checkpoint_hash'] == context.parent_checkpoint_hash
            session = RoutePlanningSession(context, TASKS['T2'], proposal_origin='OFFLINE_MANUAL')
            operations = {'current_pending_message': 'message', 'read_file': 'file',
                          'observation_source': 'observation', 'select_source_witness': 'witness'}
            for query in review['query_log']:
                getattr(session, operations[query['operation']])(**query['request'])
                assert session.query_log[-1] == query
            assert session.reads == review['reads'] and session.witnesses == review['witnesses']
        finally:
            context.close()
    print(json.dumps({'source_bytes_verified': True, 'provider_calls': 7,
        'actual_source_reads': 5, 'selected_witnesses': 0, 'native_repair_actions': 0,
        'subject_calls': 0, 'semantic_repair_effect': 'NOT_EVALUABLE', 'validation_provider_calls': 0,
        'nonblind_prefix_review_sources_replayed': bool(args.source_root)}))


if __name__ == '__main__':
    main()
