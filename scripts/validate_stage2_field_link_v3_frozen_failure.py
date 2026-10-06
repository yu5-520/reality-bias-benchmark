#!/usr/bin/env python3
"""Validate the retained field-link v3 failure without any provider call."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from stage2.route_repair.connected_planning import OUTPUT_SCHEMA, validate_connected_repair_shape

PACK = ROOT / 'stage2/replication_v2/message_field_link_trial_v3'


def load(name):
    raw = (PACK / name).read_bytes()
    return raw, json.loads(raw)


def main():
    manifest = json.loads((PACK / 'manifest.json').read_bytes())
    for name, expected in manifest['files'].items():
        raw = (PACK / name).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected, name

    _, final = load('decision.json')
    _, queries = load('query_log.json')
    _, witnesses = load('witnesses.json')
    _, outcome = load('outcome.json')

    assert outcome['failure']['message'] == 'CURRENT_MESSAGE_WITNESS_REQUIRED'
    assert outcome['provider_calls'] == 2
    assert outcome['tool_queries'] == 1
    assert outcome['native_actions_executed'] == 0
    assert not outcome['repair_success']
    assert [q['operation'] for q in queries] == ['current_pending_message']
    assert witnesses == {}

    proposal = final['proposal']
    envelope = {'writable_refs': [], 'message_fields': ['/inbox/release_lead/0/content'], 'max_actions': 1}
    validate_connected_repair_shape(envelope, proposal)

    assert proposal['application_actions'] == []
    assert proposal['host_message']['target_ref'] == 'state:host_parent'
    assert 'value' not in proposal['host_message']
    assert proposal['verification_tasks'][0]['depends_on'] == ['MSG_REPAIR_1']
    assert proposal['execution_order'] == ['MSG_REPAIR_1', 'VERIFY_NATIVE_TESTS']

    diagnosis = proposal['diagnoses'][0]
    assert diagnosis['status'] == 'SOURCE_BOUND_CLAIM'
    assert diagnosis['witness_ids'] == []
    assert diagnosis['source_ref'] == 'state:host_parent'
    assert diagnosis['destination_ref'] == 'file:web/index.html'
    assert 'not verified' in diagnosis['limitation']
    assert 'only the message text was read' in diagnosis['limitation']

    message_schema = OUTPUT_SCHEMA['repair']['proposal']['host_message']
    app_schema = OUTPUT_SCHEMA['repair']['proposal']['application_actions'][0]
    assert 'value' not in message_schema
    assert 'task_capabilities.writable_refs' in app_schema['action_id']

    print(json.dumps({
        'schema': manifest['schema'],
        'source_run_id': manifest['source_run_id'],
        'original_failure': manifest['original_failure'],
        'provider_calls_in_frozen_trial': outcome['provider_calls'],
        'message_action_shape_valid_under_current_interface': True,
        'selected_witness_count': len(witnesses),
        'diagnosis_declared_source_bound_without_selected_witness': True,
        'model_self_reported_unverified_file_evidence': True,
        'classification': manifest['classification'],
        'field_link_infrastructure_status': 'CLOSED',
        'provider_calls_added': 0
    }, sort_keys=True))


if __name__ == '__main__':
    main()
