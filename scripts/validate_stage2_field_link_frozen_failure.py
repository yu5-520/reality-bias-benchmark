#!/usr/bin/env python3
"""Validate the retained field-link failure without any provider call."""
import copy
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from stage2.route_repair.branch_fields import BranchConstraintError
from stage2.route_repair.connected_planning import OUTPUT_SCHEMA
from stage2.route_repair.native_message import ATTRIBUTION, materialize_message_action

PACK = ROOT / 'stage2/replication_v2/message_field_link_trial_v1'


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

    _, final = load('final_response.json')
    _, queries = load('query_log.json')
    _, witnesses = load('witnesses.json')
    _, outcome = load('outcome.json')

    assert final['kind'] == 'FINAL' and final['decision'] == 'REPAIR'
    assert outcome['failure']['message'] == manifest['original_failure']
    assert outcome['provider_calls'] == 7 and outcome['native_actions_executed'] == 0
    assert [q['operation'] for q in queries].count('select_source_witness') == 1
    assert list(witnesses) == ['witness:1']

    proposal = final['proposal']
    message = proposal['host_message']
    assert message['value'] == message['replacement']
    assert message['replacement'].startswith(ATTRIBUTION)
    assert 'value' not in OUTPUT_SCHEMA['repair']['proposal']['host_message']

    quote = witnesses['witness:1']['quote']
    state = {'stop_reason': None, 'queue': ['release_lead'],
             'inbox': {'release_lead': [{'from': 'frontend', 'content': quote}]}}
    context = SimpleNamespace(
        parent_checkpoint_hash=proposal['parent_checkpoint_hash'],
        parent={'state': state},
        raw=lambda member: json.dumps(state).encode(),
        locator=lambda member: {'member': member, 'json_pointer': None})

    raw_action = copy.deepcopy(message)
    assert fail_code(lambda: materialize_message_action(context, raw_action)) == 'MESSAGE_DERIVED_VALUE_MUST_BE_OMITTED'

    without_value = copy.deepcopy(raw_action)
    without_value.pop('value')
    assert fail_code(lambda: materialize_message_action(context, without_value)) == 'MESSAGE_REPLACEMENT_MUST_EXCLUDE_ATTRIBUTION'

    producer_fixed = copy.deepcopy(without_value)
    producer_fixed['replacement'] = producer_fixed['replacement'][len(ATTRIBUTION):]
    derived = materialize_message_action(context, producer_fixed)
    assert derived['value'] == message['value']

    missing = [d['claim_id'] for d in proposal['diagnoses'] if not d['witness_ids']]
    assert missing == ['claim-2', 'claim-3']
    assert proposal['diagnoses'][0]['witness_ids'] == ['witness:1']

    print(json.dumps({
        'schema': manifest['schema'],
        'source_run_id': manifest['source_run_id'],
        'source_head_sha': manifest['source_head_sha'],
        'original_failure': manifest['original_failure'],
        'current_raw_replay_rejection': 'MESSAGE_DERIVED_VALUE_MUST_BE_OMITTED',
        'after_value_removal_rejection': 'MESSAGE_REPLACEMENT_MUST_EXCLUDE_ATTRIBUTION',
        'host_derived_value_matches_original_intended_value': True,
        'remaining_model_evidence_gap_claims': missing,
        'provider_calls_added': 0
    }, sort_keys=True))


if __name__ == '__main__':
    main()
