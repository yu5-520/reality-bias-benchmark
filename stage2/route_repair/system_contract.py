"""Read-only lineage obligations for a monitoring system and its repair branch.

Literal versions and graph adjacency are reconnaissance, never semantic verdicts
or write grants. This module cannot enable a provider or promote a branch.
"""
import copy
import json
from pathlib import Path

from stage2.r7_checkpoint_v1.common import digest
from stage2.monitor_enhancement.snapshot_append import AppendOnlyEvidenceGraph
from stage2.route_repair.branch_fields import require, seal, verify_seal, pointer_parts


def build_system_contract(bundle, graph):
    verify_seal(bundle, 'bundle_hash')
    AppendOnlyEvidenceGraph.from_snapshot(graph)
    proposal = bundle['proposal']
    require(bundle['source_graph_hash'] == graph['graph_hash'] == proposal['graph_hash'], 'SYSTEM_GRAPH_DRIFT')
    require(bundle['all_observed_nodes_available'] == len(graph['nodes']), 'SYSTEM_GRAPH_TRUNCATED')
    route = set(proposal['route_refs'])
    require(route <= {n['ref'] for n in graph['nodes']}, 'SYSTEM_ROUTE_OUTSIDE_GRAPH')
    obligations = []
    for claim in proposal['diagnoses']:
        endpoints = {claim['source_ref'], claim['destination_ref']}
        require(endpoints <= route, 'SYSTEM_DIAGNOSIS_OUTSIDE_ROUTE')
        obligations.append({
            'semantic_id': claim['claim_id'],
            'source_ref': claim['source_ref'], 'destination_ref': claim['destination_ref'],
            'meaning_before': claim['meaning_before'], 'meaning_after': claim['meaning_after'],
            'claimed_authority_effect': claim['authority_effect'],
            'witness_ids': copy.deepcopy(claim['witness_ids']),
            'entry_location_status': 'PROPOSED_REQUIRES_SEMANTIC_REVIEW',
            'entry_selection_rule': 'EARLIEST_EVIDENCE_SUPPORTED_UNSUPPORTED_AUTHORITY_TRANSITION_WITH_NATIVE_CAPABILITY',
            'watch_refs': sorted(endpoints),
            'checks': ['OLD_INFORMATION_AUTHORITY', 'OLD_TASK_PERMISSION', 'HISTORICAL_REENTRY',
                       'TRANSFORMED_DESCENDANTS', 'UNRELATED_SEMANTIC_PROGRESSION'],
            'adoption_status': 'UNKNOWN', 'limitation': claim['limitation'],
        })
    require(obligations, 'LINEAGE_OBLIGATIONS_REQUIRED')
    return seal({
        'schema': 'stage2-monitor-repair-system-contract-v1',
        'bundle_hash': bundle['bundle_hash'], 'source_graph_hash': graph['graph_hash'],
        'archive_sha256': proposal['archive_sha256'],
        'parent_checkpoint_hash': proposal['parent_checkpoint_hash'],
        'original_task': copy.deepcopy(proposal['original_task']),
        'route_refs': sorted(route), 'modify_refs': sorted(proposal['modify_refs']),
        'preserve_refs': sorted(proposal['preserve_refs']), 'verify_refs': sorted(proposal['verify_refs']),
        'lineage_obligations': obligations,
        'unknown_relations': copy.deepcopy(proposal['unknown_relations']),
        'whole_graph_available': True, 'graph_reachability_grants_writes': False,
        'task_boundary_precedes_diagnosis': True, 'exact_write_policy_frozen_after_proposal': True,
        'hard_policy_implementation': 'SEPARATELY_RETAINED_HOST_POLICIES',
        'historical_prefix_policy': 'IMMUTABLE_APPEND_NEW_NATIVE_RECORDS',
        'success_requires': ['NATIVE_POSTCONDITIONS', 'REPAIR_AGENT_EXIT', 'MONITORED_NATIVE_CONTINUATION',
                             'INDEPENDENT_SEMANTIC_AUTHORITY_REVIEW', 'UNRELATED_PROGRESSION_REVIEW'],
        'live_execution_enabled': False, 'branch_promotion_enabled': False,
    }, 'contract_hash')


def read_capture_member(root, observation):
    """Host-side source reader; no paths or replacement ledgers from the proposal."""
    root = Path(root).resolve(strict=True)
    member = observation['source_locator']['member']
    path = Path(member)
    require(not path.is_absolute() and '..' not in path.parts, 'WATCH_SOURCE_PATH_OUTSIDE_BRANCH')
    target = (root / path).resolve(strict=True)
    require(target.is_relative_to(root), 'WATCH_SOURCE_PATH_OUTSIDE_BRANCH')
    return target.read_bytes()


def bound_source_text(observation, member_bytes):
    locator = observation['source_locator']
    require(digest(member_bytes) == locator['member_sha256'], 'WATCH_SOURCE_HASH_DRIFT')
    text = member_bytes.decode('utf-8')
    pointer = locator.get('json_pointer', '')
    if pointer:
        value = json.loads(text)
        for part in pointer_parts(pointer):
            value = value[int(part)] if isinstance(value, list) else value[part]
        text = value if isinstance(value, str) else json.dumps(value, sort_keys=True)
    elif locator.get('line') is not None:
        line = locator['line']
        require(type(line) is int and 1 <= line <= len(text.splitlines()), 'WATCH_SOURCE_LINE_INVALID')
        text = text.splitlines()[line - 1]
    return text


def assess_continuation(contract, before, after, *, source_reader, exit_observation_id=None):
    """Verify evidence retention and collect literal post-exit recurrence clues.

    Every new source is read and hash-checked. A version match is explicitly not
    adoption, reactivation, or a semantic descendant. Cross-clock order stays
    unknown. Independent semantic evaluation is deliberately a pending gate.
    """
    verify_seal(contract, 'contract_hash')
    AppendOnlyEvidenceGraph.from_snapshot(before)
    AppendOnlyEvidenceGraph.from_snapshot(after)
    require(before['graph_hash'] == contract['source_graph_hash'], 'WATCH_PARENT_DRIFT')
    for collection, identity in [('observations', 'observation_id'), ('edges', 'edge_id')]:
        old = {r[identity]: r for r in before[collection]}
        current = {r[identity]: r for r in after[collection]}
        require(all(current.get(k) == v for k, v in old.items()), 'WATCH_HISTORICAL_PREFIX_DRIFT')
    require({n['ref'] for n in before['nodes']} <= {n['ref'] for n in after['nodes']}, 'WATCH_NODE_LOSS')
    old_ids = {r['observation_id'] for r in before['observations']}
    new = [r for r in after['observations'] if r['observation_id'] not in old_ids]
    texts = {}
    for row in new:
        texts[row['observation_id']] = bound_source_text(row, source_reader(row))
    exit_row = None
    if exit_observation_id is not None:
        exit_row = next((r for r in new if r['observation_id'] == exit_observation_id), None)
        require(exit_row is not None and exit_row.get('event_kind') == 'REPAIR_AGENT_EXIT', 'WATCH_NATIVE_EXIT_RECORD_REQUIRED')
        require(exit_row.get('clock_id') and type(exit_row.get('native_sequence')) is int, 'WATCH_EXIT_CLOCK_REQUIRED')
    post_exit, unordered = [], []
    for row in new:
        if exit_row is None or row is exit_row:
            continue
        if row.get('clock_id') != exit_row['clock_id']:
            unordered.append(row['observation_id'])
        elif type(row.get('native_sequence')) is int and row['native_sequence'] > exit_row['native_sequence']:
            post_exit.append(row)
    # Include all objects, not only the chosen route, to expose possible new carriers.
    old_hashes = {}
    for row in before['observations']:
        if row.get('content_hash'):
            old_hashes.setdefault(row['content_hash'], []).append(row['observation_id'])
    matches = [{'observation_id': r['observation_id'], 'object_refs': r['object_refs'],
                'historical_observation_ids': old_hashes[digest(texts[r['observation_id']].encode())],
                'classification': 'LITERAL_VERSION_REAPPEARANCE_NOT_SEMANTIC_ADOPTION'}
               for r in post_exit if digest(texts[r['observation_id']].encode()) in old_hashes]
    obligations = []
    for watch in contract['lineage_obligations']:
        relevant = [r['observation_id'] for r in post_exit if set(r['object_refs']) & set(watch['watch_refs'])]
        obligations.append({'semantic_id': watch['semantic_id'], 'post_exit_observation_ids': relevant,
                            'checks': watch['checks'], 'status': 'PENDING_INDEPENDENT_SEMANTIC_AUTHORITY_REVIEW'})
    return seal({
        'schema': 'stage2-repair-continuation-assessment-v1', 'contract_hash': contract['contract_hash'],
        'before_graph_hash': before['graph_hash'], 'after_graph_hash': after['graph_hash'],
        'historical_prefix_preserved': True, 'new_sources_verified': len(new),
        'source_text_hashes': {k: digest(v.encode()) for k, v in texts.items()},
        'repair_exit_observation_id': exit_observation_id,
        'ordered_post_exit_observation_ids': [r['observation_id'] for r in post_exit],
        'cross_clock_unordered_observation_ids': unordered,
        'literal_version_reappearance': matches, 'lineage_obligations': obligations,
        'unrelated_progression_status': 'NOT_ESTABLISHED_BY_FILE_RETENTION',
        'semantic_descendants_status': 'PENDING_INDEPENDENT_REVIEW',
        'semantic_repair_effect': 'NOT_EVALUATED', 'repair_success': False,
        'status': 'PENDING_INDEPENDENT_SEMANTIC_REVIEW' if post_exit else 'PENDING_NATIVE_CONTINUATION',
    }, 'assessment_hash')
