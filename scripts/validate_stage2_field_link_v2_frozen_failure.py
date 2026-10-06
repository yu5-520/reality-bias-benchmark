#!/usr/bin/env python3
"""Validate the retained field-link v2 failure without any provider call."""
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from stage2.route_repair.branch_fields import BranchConstraintError
from stage2.route_repair.connected_planning import OUTPUT_SCHEMA, validate_connected_repair_shape

PACK = ROOT / 'stage2/replication_v2/message_field_link_trial_v2'


def load(name):
    raw = (PACK / name).read_bytes()
    return raw, json.loads(raw)


def fail_code(fn):
    try:
        fn()
    except BranchConstraintError as exc:
        return str(exc)
    raise AssertionError('EXPECTED_BRANCH_CONSTRAINT_ERROR')


def main():
    manifest = json.loads((PACK / 'manifest.json').read_bytes())
    for name, expected in manifest['files'].items():
        raw = (PACK / name).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected, name

    _, final = load('decision.json')
    _, queries = load('query_log.json')
    _, witnesses = load('witnesses.json')
    _, outcome = load('outcome.json')

    assert final['kind'] == 'FINAL' and final['decision'] == 'REPAIR'
    assert outcome['failure']['message'] == manifest['original_failure']
    assert outcome['provider_calls'] == 8 and outcome['native_actions_executed'] == 0
    assert [q['operation'] for q in queries].count('select_source_witness') == 1
    assert list(witnesses) == ['witness:1']

    proposal = final['proposal']
    assert proposal['host_message']['target_ref'] == 'state:host_parent'
    assert len(proposal['application_actions']) == 1
    assert proposal['application_actions'][0]['target_ref'] == 'state:host_parent'
    assert proposal['application_actions'][0]['value'] == proposal['host_message']['replacement']
    assert proposal['verification_tasks'][0]['depends_on'] == ['A1']

    envelope = {'writable_refs': [], 'message_fields': ['/inbox/release_lead/0/content'], 'max_actions': 1}
    assert fail_code(lambda: validate_connected_repair_shape(envelope, proposal)) == 'CONNECTED_APPLICATION_ACTIONS_NOT_AUTHORIZED'

    action_fixed = copy.deepcopy(proposal)
    action_fixed['application_actions'] = []
    assert fail_code(lambda: validate_connected_repair_shape(envelope, action_fixed)) == 'CONNECTED_MESSAGE_VERIFICATION_DEPENDENCY_REQUIRED'

    dependency_fixed = copy.deepcopy(action_fixed)
    dependency_fixed['verification_tasks'][0]['depends_on'] = ['M1']
    validate_connected_repair_shape(envelope, dependency_fixed)

    selected_refs = {w['ref'] for w in witnesses.values()}
    diagnosis = proposal['diagnoses'][0]
    assert diagnosis['source_ref'] in selected_refs
    assert diagnosis['destination_ref'] not in selected_refs
    assert diagnosis['witness_ids'] == ['witness:1']

    app_schema = OUTPUT_SCHEMA['repair']['proposal']['application_actions'][0]
    assert 'task_capabilities.writable_refs' in app_schema['action_id']
    assert 'never state:host_parent' in app_schema['target_ref']

    print(json.dumps({
        'schema': manifest['schema'],
        'source_run_id': manifest['source_run_id'],
        'source_head_sha': manifest['source_head_sha'],
        'original_failure': manifest['original_failure'],
        'current_raw_replay_rejection': 'CONNECTED_APPLICATION_ACTIONS_NOT_AUTHORIZED',
        'after_duplicate_action_removal_rejection': 'CONNECTED_MESSAGE_VERIFICATION_DEPENDENCY_REQUIRED',
        'remaining_model_evidence_gap': {
            'claim_id': diagnosis['claim_id'],
            'missing_selected_witness_ref': diagnosis['destination_ref']
        },
        'provider_calls_added': 0
    }, sort_keys=True))


if __name__ == '__main__':
    main()
