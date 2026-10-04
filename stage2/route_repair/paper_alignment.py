"""Paper-bound retrospective inspection and prefix-only trial prerequisites.

The corrected judgments remain nonblind, selected historical judgments. This
module neither adjudicates semantics nor turns a graph/proxy into detection truth.
Retrospective review packets must never be supplied to a planning actor.
"""
import copy
import gzip
import json
from collections import Counter
from pathlib import Path

from stage2.r7_checkpoint_v1.common import digest
from stage2.route_repair.branch_fields import require, seal

REFERENCE = 'stage2/replication_v2/chronology_semantic_review_v1'
CORRECTION = 'stage2/replication_v2/chronology_correction_v1'
HISTORICAL = 'stage2/replication_v2/enhanced_monitor_dual_audit_comparison_v1'
INDEX = 'stage2/replication_v2/enhanced_monitor_p2_v2_index'
CONTRACT = 'configs/stage2_paper_mechanism_contract_v1.json'
COUNTS = {'SUPPORTED': 6, 'SUPPORTED_CANDIDATE': 2,
          'NOT_ESTABLISHED': 45, 'NEGATIVE_BOUNDARY': 12}


def read(path):
    return json.loads(Path(path).read_bytes())


def load_contract(root):
    contract = read(Path(root) / CONTRACT)
    require(contract['schema'] == 'stage2-paper-mechanism-contract-v1', 'PAPER_CONTRACT_SCHEMA')
    for name, expected in contract['frozen_inputs'].items():
        require(digest((Path(root) / name).read_bytes()) == expected, 'PAPER_INPUT_DRIFT:' + name)
    return contract


def split_comparison(rows, corrected_reviews):
    """Partition by actual reviewed identity, rather than a file's title."""
    reviewed = {(r['full_id'], r['event_id']): r for r in corrected_reviews}
    corrected, historical = [], []
    for row in rows:
        key = row['full_id'], row['reference_id']
        target = corrected if key in reviewed else historical
        if key in reviewed:
            require(row['input_basis'] == 'CORRECTED_TARGETED_RATIONALE_AND_EVIDENCE',
                    'CORRECTED_COMPARISON_BASIS_MISMATCH')
            require(row['corrected_status'] == reviewed[key]['reviewed_status'],
                    'CORRECTED_COMPARISON_STATUS_MISMATCH')
        else:
            require(row['input_basis'] == 'ORIGINAL_FROZEN_AUDIT_UNTARGETED',
                    'HISTORICAL_COMPARISON_BASIS_MISMATCH')
        target.append(copy.deepcopy(row))
    return {'corrected_targeted': corrected, 'historical_unreviewed': historical,
            'pooled_validated_reference': False, 'detector_accuracy_established': False}


def build_review_material(root):
    root = Path(root)
    contract = load_contract(root)
    reviews = read(root / REFERENCE / 'semantic_reviews.json')
    require(len({(r['full_id'], r['event_id']) for r in reviews}) == len(reviews) == 65,
            'PAPER_REVIEW_IDENTITY_MISMATCH')
    require(dict(Counter(r['reviewed_status'] for r in reviews)) == COUNTS, 'PAPER_REVIEW_COUNTS')
    observations = {r['full_id']: r for r in map(json.loads, gzip.decompress(
        (root / REFERENCE / 'frozen_observations.jsonl.gz').read_bytes()).splitlines())}
    packets = {r['group_id'] + '-' + r['cell_id']: r for r in map(json.loads, gzip.decompress(
        (root / CORRECTION / 'full_context_corrected_packets.jsonl.gz').read_bytes()).splitlines())}
    proxies = {(r['full_id'], r['event_id']): r for r in map(json.loads,
        (root / INDEX / 'reference_comparison.jsonl').read_text().splitlines())}
    require(set(proxies) == {(r['full_id'], r['event_id']) for r in reviews}, 'PAPER_PROXY_POPULATION')
    result = []
    for review in reviews:
        fid = review['full_id']; packet = packets[fid]; obs = observations[fid]
        require(digest(obs) == review['observation_sha256'], 'PAPER_OBSERVATION_BINDING')
        require(packet['packet_sha256'] == review['corrected_packet_sha256']
                == obs['corrected_packet_sha256'], 'PAPER_CORRECTED_PACKET_BINDING')
        evidence = {e['ref']: e for e in packet['evidence']}
        citations = [copy.deepcopy(evidence[ref]) for ref in review['corrected_evidence_refs']]
        proxy = proxies[fid, review['event_id']]
        require(proxy['reviewed_status'] == review['reviewed_status']
                and proxy['event_detection_truth_available'] is False, 'PAPER_PROXY_NOT_TRUTH')
        result.append({'reference_key': fid + ':' + review['event_id'], 'review': copy.deepcopy(review),
                       'corrected_citations': citations,
                       'observation_record': {'full_id': fid, 'sha256': review['observation_sha256'],
                                              'archive_sha256': obs['archive_sha256']},
                       'inspection_proxy': copy.deepcopy(proxy),
                       'semantic_path_independently_reviewed': False,
                       'planning_input_allowed': False})
    split = split_comparison(read(root / HISTORICAL / 'corrected_comparison.json')['records'], reviews)
    require(len(split['corrected_targeted']) == 8 and len(split['historical_unreviewed']) == 25,
            'PAPER_COMPARISON_PARTITION')
    focal = sorted(set(r['full_id'] for r in reviews if r['reviewed_status'] in
                       {'SUPPORTED', 'SUPPORTED_CANDIDATE'}) | set(contract['negative_case_ids']))
    routes = []
    for fid in focal:
        obs = observations[fid]; packet = packets[fid]
        routes.append({'full_id': fid, 'archive_sha256': obs['archive_sha256'],
            'reference_keys': [r['reference_key'] for r in result if r['review']['full_id'] == fid],
            'ordered_file_transitions': copy.deepcopy(obs['application_state_transitions']),
            'selected_claim_carriers': copy.deepcopy(obs['selected_messages']),
            'run_summary_previews': [copy.deepcopy(e) for e in packet['evidence'] if e['kind'] == 'RUN_SUMMARY'],
            'source_qualification_review': 'PENDING_INDEPENDENT_SEMANTIC_INSPECTION',
            'representation_change_review': 'PENDING_INDEPENDENT_SEMANTIC_INSPECTION',
            'downstream_read_and_adoption': 'NOT_INFERRED_FROM_SNAPSHOT_PRESENCE',
            'independent_reconstruction_or_inheritance': 'NOT_INFERRED_FROM_ENDPOINT',
            'claim_boundary': 'Retrospective source-bound material; previews are not complete raw records. '
                              'First observed checkpoint is not a send, read or adoption timestamp.'})
    summary = {'schema': 'stage2-paper-alignment-summary-v1', 'review_records': 65,
        'review_status_counts': COUNTS, 'unreviewed_historical_dimension_records': 175,
        'corrected_comparison_records': 8, 'historical_comparison_records': 25,
        'focal_routes': len(routes), 'semantic_reviewer_invoked': False,
        'validated_global_accuracy': None, 'causal_repair_success_rate': None,
        'execution': {'provider_calls': 0, 'subject_calls': 0, 'repair_calls': 0, 'natural_reruns': 0},
        'evidence_state_commit': contract['semantic_review_commit'],
        'claim_boundary': 'Selected nonblind correction subset, not a revalidated 240-record reference. '
                          'Object mention proxies and source material are not semantic detection outcomes.'}
    return {'review_packets.json': result, 'comparison_partitions.json': split,
            'case_routes.json': routes, 'summary.json': summary}


def assess_mechanism_entry(context, contract):
    """Inspect only the runtime prefix. No retrospective review is passed here.

    Current executor grants application-file writes only. Native host message
    actions exist, but no repair-actor carrier binding is implemented. A model's
    proposal cannot fill that gap or grant authority over the native host.
    """
    require(contract['target_family'] == 'PROCESS_ACCOUNTING', 'PAPER_TARGET_NOT_IMPLEMENTED')
    state = context.parent['state']
    snapshots = sorted(context.file_versions.get('file:web/app.js', []),
                       key=lambda r: r['native_sequence'])
    changed = bool(snapshots and any(r['content_sha256'] != snapshots[0]['content_sha256']
                                    for r in snapshots))
    carriers = []
    for role, messages in state['inbox'].items():
        for index, message in enumerate(messages):
            content = message.get('content', '')
            # This nominates a lexical candidate, never a semantic verdict.
            if isinstance(content, str) and any(t in content.lower() for t in
                    ('no changes were needed', 'no code changes were required', 'no new payment button')):
                carriers.append({'json_pointer': f'/inbox/{role}/{index}/content',
                                 'value_sha256': digest(content.encode()), 'text': content})
    blockers = []
    if not changed or not carriers:
        blockers.append('TARGET_TRANSITION_NOT_SUPPORTED_BY_AVAILABLE_PREFIX')
    blockers.extend(['NATIVE_REPAIR_CLAIM_CARRIER_BINDING_NOT_IMPLEMENTED',
                     'PREFIX_SEMANTIC_ENTRY_ADJUDICATION_NOT_IMPLEMENTED',
                     'MECHANISM_OBSERVATION_WINDOW_NOT_FROZEN'])
    return seal({'schema': 'stage2-paper-mechanism-entry-assessment-v1',
        'full_id': context.case['full_id'], 'archive_sha256': context.case['archive_sha256'],
        'parent_checkpoint_hash': context.parent_checkpoint_hash,
        'parent_native_sequence': len(state['history']), 'graph_hash': context.graph['graph_hash'],
        'remaining_horizon': context.parent['manifest']['remaining_horizon'],
        'prefix_file_transition_observed': changed, 'lexical_claim_candidates': carriers,
        'failed_read_invocations': [copy.deepcopy(r) for r in
            context.prefix_receipt['invocation_membership_bindings']
            if r.get('tool_result_status') == 'RETURNED_READ_ERROR'],
        'lexical_candidate_is_semantic_diagnosis': False,
        'native_host_message_action_exists': True,
        'native_repair_claim_carrier_binding_implemented': False,
        'repair_entry_ready': False, 'blockers': blockers,
        'future_evidence_used': False, 'provider_calls': 0,
        'engineering_fixture_is_mechanism_repair': False}, 'assessment_hash')
