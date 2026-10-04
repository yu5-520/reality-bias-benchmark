"""Exact pending-message replacement on a copied experiment-owned host.

The original sender and every other native field stay intact. The replacement
is visibly attributed to the repair actor; it cannot masquerade as a new message
from that sender. This module does not modify a framework, protocol or archive.
"""
import copy
import json
import re

from stage2.r7_checkpoint_v1.common import digest, file_tree_manifest, stable_json_bytes
from stage2.native_v7.software_host_v1 import TASKS
from stage2.route_repair.branch_fields import require, seal, verify_seal

ATTRIBUTION = '[BRANCH REPAIR ANNOTATION; original sender retained; not a new sender statement]\n'


def message_source(context, field_path):
    match = re.fullmatch(r'/inbox/([a-z_]+)/([0-9]+)/content', field_path)
    require(match is not None, 'PENDING_MESSAGE_CONTENT_FIELD_REQUIRED')
    role, index = match.group(1), int(match.group(2))
    member = 'checkpoints/' + context.parent_checkpoint_hash + '/native_state.json'
    state = json.loads(context.raw(member))
    require(state == context.parent['state'] and state['stop_reason'] is None,
            'CURRENT_NONTERMINAL_MESSAGE_PARENT_REQUIRED')
    require(role in state['queue'] and role in state['inbox']
            and index < len(state['inbox'][role]), 'PENDING_NATIVE_MESSAGE_REQUIRED')
    message = state['inbox'][role][index]
    require(set(message) == {'from', 'content'} and isinstance(message['content'], str)
            and message['content'], 'NATIVE_MESSAGE_SHAPE_REQUIRED')
    return state, role, index, {**context.locator(member), 'json_pointer': field_path}


def build_message_policy(context, *, original_task, action, evidence):
    state, role, index, locator = message_source(context, action['field_path'])
    require(original_task == TASKS[state['task_id']], 'MESSAGE_ORIGINAL_TASK_DRIFT')
    require(action['target_ref'] == 'state:host_parent', 'MESSAGE_NATIVE_TARGET_REQUIRED')
    require(action['kind'] == 'PENDING_MESSAGE_REPLACE', 'MESSAGE_OPERATION_REQUIRED')
    value = action['value']
    before = state['inbox'][role][index]['content']
    require(isinstance(value, str) and value.startswith(ATTRIBUTION)
            and len(value) > len(ATTRIBUTION) and value != before, 'REPAIR_ATTRIBUTION_REQUIRED')
    require(action['before_value_hash'] == digest(before.encode()), 'MESSAGE_VERSION_DRIFT')
    start, end = action['start'], action['end']
    require(type(start) is int and type(end) is int and 0 <= start < end <= len(before), 'MESSAGE_EXACT_SPAN_REQUIRED')
    require(action['before_span_hash'] == digest(before[start:end].encode()), 'MESSAGE_SPAN_VERSION_DRIFT')
    require(isinstance(action['replacement'], str) and action['replacement'], 'MESSAGE_REPLACEMENT_TEXT_REQUIRED')
    require(value == ATTRIBUTION + before[:start] + action['replacement'] + before[end:],
            'UNRELATED_MESSAGE_TEXT_DRIFT')
    require(evidence and any(e == locator for e in evidence), 'EXACT_MESSAGE_SOURCE_WITNESS_REQUIRED')
    after = copy.deepcopy(state)
    after['inbox'][role][index]['content'] = value
    return seal({'schema': 'stage2-pending-message-policy-v1',
        'archive_sha256': context.case['archive_sha256'],
        'parent_checkpoint_hash': context.parent_checkpoint_hash,
        'graph_hash': context.graph['graph_hash'], 'original_task': copy.deepcopy(original_task),
        'action': copy.deepcopy(action), 'source_locator': locator,
        'before_state_hash': digest(state), 'after_state_hash': digest(after),
        'source_witnesses': copy.deepcopy(evidence), 'original_sender': state['inbox'][role][index]['from'],
        'semantic_effect_certified': False}, 'policy_hash')


def apply_message_policy(context, host, adapter, root, policy, observer):
    verify_seal(policy, 'policy_hash')
    action = policy['action']
    require(policy == build_message_policy(context, original_task=policy['original_task'],
        action=action, evidence=policy['source_witnesses']), 'MESSAGE_HOST_POLICY_DRIFT')
    before = adapter.save_state(host)
    require(digest(before) == policy['before_state_hash'], 'STALE_BRANCH_HOST_MESSAGE')
    _, role, index, _ = message_source(context, action['field_path'])
    after = copy.deepcopy(before)
    after['inbox'][role][index]['content'] = action['value']
    require(digest(after) == policy['after_state_hash'], 'MESSAGE_OUTPUT_DRIFT')
    files = file_tree_manifest(root)
    observer.capture(action['target_ref'], stable_json_bytes(before).decode(),
                     'HOST_MESSAGE_BEFORE', action_id=action['action_id'])
    adapter.load_state(host, after)
    actual = adapter.save_state(host)
    require(actual == after and file_tree_manifest(root) == files, 'MESSAGE_NATIVE_READBACK_FAILED')
    receipt = {'action_id': action['action_id'], 'target_ref': action['target_ref'],
        'field_path': action['field_path'], 'before_hash': digest(before), 'after_hash': digest(actual),
        'expected_output_hash': policy['after_state_hash'],
        'native_interface': 'native:SoftwareHostCheckpointAdapter.load_state',
        'original_sender_retained': actual['inbox'][role][index]['from'] == policy['original_sender'],
        'unrelated_host_fields_preserved': True, 'application_files_preserved': True,
        'attribution_visible_to_subject': True, 'semantic_adoption_verified': False}
    observer.capture(action['target_ref'], stable_json_bytes(actual).decode(),
        'HOST_MESSAGE_AFTER', receipt=receipt, action_id=action['action_id'], written=True)
    return actual, receipt
