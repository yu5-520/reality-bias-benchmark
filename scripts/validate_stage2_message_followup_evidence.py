#!/usr/bin/env python3
"""Validate captured follow-up bytes and conclusions without executing a trial."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'stage2/replication_v2/message_corrected_contract_followup_v1'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    seal = json.loads((EVIDENCE / 'seal.json').read_bytes())
    raw = (EVIDENCE / 'evidence.zip').read_bytes()
    assert sha(raw) == seal['artifact_zip_sha256']
    assert sha((EVIDENCE / 'observation.json').read_bytes()) == seal['observation_sha256']
    assert sha((ROOT / 'configs/stage2_message_corrected_contract_followup_v1.json').read_bytes()) == seal['trial_request_sha256']
    observation = json.loads((EVIDENCE / 'observation.json').read_bytes())
    assert observation['artifact_zip_sha256'] == sha(raw)
    with zipfile.ZipFile(EVIDENCE / 'evidence.zip') as archive:
        assert len(archive.namelist()) == len(set(archive.namelist()))
        names = {n for n in archive.namelist() if not n.endswith('/')}
        assert names == set(seal['original_member_sha256'])
        for name in names:
            assert not Path(name).is_absolute() and '..' not in Path(name).parts
            assert sha(archive.read(name)) == seal['original_member_sha256'][name], name
        prefix = 'mechanism-corrected-contract-followup/'
        outcome = json.loads(archive.read(prefix + 'planning/outcome.json'))
        assert observation['outcome'] == outcome
        assert outcome['state'] == 'FAILED' and outcome['failure']['message'] == 'NO_ACTION_SOURCE_NOT_INSPECTED'
        assert outcome['provider_calls'] == outcome['actor_calls'] == outcome['transport_attempts'] == 2
        assert outcome['tool_queries'] == 1 and outcome['native_actions_executed'] == 0
        assert outcome['authorization_hash'] is None and outcome['tools_revoked']
        assert not outcome['actual_repair_agent_exit'] and not outcome['repair_success']
        assert json.loads(archive.read(prefix + 'planning/witnesses.json')) == {}
        queries = json.loads(archive.read(prefix + 'planning/query_log.json'))
        assert len(queries) == 1 and queries[0]['operation'] == 'complete_catalog'
        assert not any(n.startswith(prefix + 'host/native_branch/') for n in names)
        for response in observation['responses']:
            directory = prefix + f"planning_http/{response['sequence']:04d}/"
            request_raw, response_raw = [archive.read(directory + n + '.bin') for n in ['request', 'response']]
            assert sha(request_raw) == response['request_sha256']
            assert sha(response_raw) == response['response_sha256']
            actual = json.loads(response_raw)
            assert response['content'] == actual['choices'][0]['message']['content']
            assert response['usage'] == actual['usage'] and response['model'] == actual['model']
        first, second = [json.loads(r['content']) for r in observation['responses']]
        assert first == {'kind': 'TOOL', 'name': 'catalog', 'arguments': {}}
        assert second['kind'] == 'FINAL' and second['decision'] == 'NO_REPAIR_NEEDED'
        assert second['inspected_refs'] and second['witness_ids'] == []
    assert observation['actual_source_reads'] == observation['selected_source_witnesses'] == observation['subject_calls'] == 0
    assert not observation['independent_semantic_review_invoked']
    assert observation['repair_effect'] == 'NOT_EVALUABLE_NO_REPAIR_OR_POST_EXIT_CONTINUATION'
    print(json.dumps({'source_bytes_verified': True, 'provider_calls': 2,
        'catalog_queries': 1, 'actual_source_reads': 0, 'native_repair_actions': 0,
        'subject_calls': 0, 'semantic_repair_effect': 'NOT_EVALUABLE', 'validation_provider_calls': 0}))


if __name__ == '__main__':
    main()
