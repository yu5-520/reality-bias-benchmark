"""Structural inspection candidates, separated from semantic evaluation."""
import re
from collections import defaultdict


def select_candidates(graph, minimum_events=3, minimum_span=4):
    grouped = defaultdict(list)
    for row in graph['observations']:
        for ref in row['object_refs']: grouped[ref].append(row)
    result = []
    for ref, rows in sorted(grouped.items()):
        native = [r for r in rows if r['source_kind'] == 'NATIVE_RECORD']
        events = {r['event_ref'] for r in native}
        actors = {r['actor'] for r in native} - {'UNKNOWN', 'SYSTEM'}
        clocks = defaultdict(list)
        for r in native: clocks[r['clock_id']].append(r['native_sequence'])
        states = {(r['content_hash'], r.get('state_presence')) for r in rows if r['event_kind'] == 'CHECKPOINT_FILE_STATE'}
        reasons = []
        if len(events) >= minimum_events: reasons.append('MULTI_EVENT_EXPOSURE')
        if len(actors) >= 2: reasons.append('MULTI_ACTOR_EXPOSURE')
        if any(max(seq)-min(seq) >= minimum_span for seq in clocks.values()):
            reasons.append('LONG_SPAN_REEXPOSURE_WITHIN_ONE_CLOCK')
        if len(states) >= 2: reasons.append('MULTI_VERSION_STATE')
        if reasons:
            result.append({'object_ref': ref, 'reasons': reasons, 'native_event_count': len(events),
                           'event_refs': sorted(events), 'candidate_is_defect': False,
                           'semantic_status': 'NOT_ADJUDICATED'})
    return result


def add_unknown_edges(builder, graph, candidates):
    refs = {r['object_ref'] for r in candidates}
    grouped = defaultdict(list)
    for r in graph['observations']:
        if r['source_kind'] == 'NATIVE_RECORD':
            for ref in set(r['object_refs']) & refs:
                grouped[(ref, r['clock_id'])].append(r)
    for (ref, clock), rows in sorted(grouped.items()):
        if len({r['event_ref'] for r in rows}) < 2: continue
        last = max(r['native_sequence'] for r in rows)
        # Tied sequences are unresolved: retain all, never break ties by hash.
        for r in rows:
            if r['native_sequence'] != last: continue
            builder.add_edge({'source_ref': ref, 'destination_ref': 'event:' + r['event_ref'],
                              'relation_type': 'REUSE_DEPENDENCY_UNRESOLVED', 'status': 'UNKNOWN',
                              'basis': 'EXPOSURE_IS_NOT_ADOPTION', 'evidence_refs': [r['evidence_ref']]})


def exact_file_mentions(refs, text):
    return sorted(ref for ref in refs if ref.startswith('file:') and
                  re.search(r'(?<![\w./-])' + re.escape(ref[5:]) + r'(?![\w./-])', text))


def evaluate_corrected_reference(reviews, ref_sets):
    result = []
    for r in reviews:
        sets = ref_sets[r['full_id']]
        result.append({'full_id': r['full_id'], 'event_id': r['event_id'],
                       'reviewed_status': r['reviewed_status'],
                       'metric': 'EXACT_FILE_MENTION_PROXY_NOT_NODE_LOCALIZATION',
                       'event_detection_truth_available': False,
                       'matches': {k: exact_file_mentions(v, r['reviewed_rationale']) for k,v in sets.items()}})
    return result
