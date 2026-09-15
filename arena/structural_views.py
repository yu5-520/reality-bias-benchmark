"""Deterministic exposure links and feedback projections, never semantic labels."""
from .core import stable_hash

VERSION = 'ARENA-STRUCTURAL-VIEWS-v0.1'
MISSING = 'NOT_RECORDED_IN_SOURCE_VERSION'


def build_views(trace, batch_hash):
    run = trace['run_id']
    event_ref = lambda n: f'{run}:EVENT:{n:04d}'
    call_ref = lambda n: f'{run}:CALL:{n:04d}'
    index = []
    edges = []
    events = trace.get('events', [])
    for kind in ('message_ledger', 'invocation_ledger'):
        for row in trace.get(kind, []):
            ident = row.get('message_id') or row.get('invocation_id')
            index.append({'evidence_ref': f'{run}:{ident}', 'record_type': kind, 'run_id': run, 'record': row})
    messages = {x.get('action', {}).get('message_id'): x for x in events if x.get('action', {}).get('message_id')}
    def add(source, target, kind, refs):
        edge = dict(source_ref=source, target_ref=target, evidence_type=kind, evidence_refs=refs,
                    semantic_dependency='NOT_ADJUDICATED', causal_effect='NOT_ADJUDICATED')
        edge['relation_id'] = f'{run}:REL:{stable_hash(edge)[:16]}'
        edges.append(edge)
    for i, call in enumerate(trace.get('model_calls', [])):
        target = call_ref(i)
        for mid in call.get('input_message_ids', []):
            source = messages.get(mid)
            if source is not None:
                add(event_ref(source['event_index']), target, 'message_read_into_input', [event_ref(source['event_index']), target, f'{run}:{mid}'])
        view = call.get('runtime_snapshot')
        # Legacy input can be reviewed manually; do not manufacture a runtime snapshot.
        if view:
            origins = set()
            for meta in view.get('shared_state_metadata', {}).values():
                if isinstance(meta, dict) and isinstance(meta.get('event_index'), int):
                    origins.add(meta['event_index'])
            final = view.get('final_state')
            if final is not None:
                prior = [e for e in events if e.get('turn', 0) < call.get('turn', 0) and e.get('final_state_after') == final and e.get('action_type') in ('finalize', 'revise_final_state')]
                if prior:
                    n = prior[-1]['event_index']
                    add(event_ref(n), target, 'settled_version_visible_in_input', [event_ref(n), target])
            for n in sorted(origins):
                add(event_ref(n), target, 'state_version_visible_in_input', [event_ref(n), target])
        start, end = call.get('event_index_start'), call.get('event_index_end')
        if isinstance(start, int) and isinstance(end, int):
            for e in events:
                if start <= e['event_index'] < end and e.get('actor') == call.get('agent_id'):
                    add(target, event_ref(e['event_index']), 'output_action', [target, event_ref(e['event_index'])])
    # Project read message edges onto actors. A return path is a communication candidate only.
    calls = {call_ref(i): c for i, c in enumerate(trace.get('model_calls', []))}
    by_event = {event_ref(e['event_index']): e for e in events}
    projected = []
    for edge in edges:
        if edge['evidence_type'] == 'message_read_into_input':
            src = by_event[edge['source_ref']]['actor']; dst = calls[edge['target_ref']]['agent_id']
            if src != 'ENVIRONMENT':
                projected.append(dict(source=src, target=dst, relation_id=edge['relation_id'], evidence_refs=edge['evidence_refs']))
    adjacency = {}
    candidates = []
    def path(start, end, seen):
        if start == end:
            return []
        if start in seen:
            return None
        for edge in adjacency.get(start, []):
            tail = path(edge['target'], end, seen | {start})
            if tail is not None:
                return [edge] + tail
        return None
    for edge in projected:
        return_path = path(edge['target'], edge['source'], set())
        if return_path is not None:
            cycle = return_path + [edge]
            candidates.append({'candidate_id': f'{run}:LOOP:{len(candidates):04d}',
                'projection': 'actors_over_time', 'candidate_type': 'communication_return_path',
                'relation_ids': [x['relation_id'] for x in cycle],
                'evidence_refs': sorted({r for x in cycle for r in x['evidence_refs']}),
                'authority_penetration': 'NOT_ADJUDICATED', 'self_reinforcement': 'NOT_ADJUDICATED'})
        adjacency.setdefault(edge['source'], []).append(edge)
    revisions = [event_ref(e['event_index']) for e in events if e.get('action_type') in ('finalize', 'revise_final_state')]
    return index, {'version': VERSION, 'run_id': run, 'evidence_batch_hash': batch_hash,
        'layers': {x: 'PENDING_REVIEW' for x in ('R2', 'R3', 'R4')},
        'relations': edges, 'feedback_candidates': candidates,
        'settled_state_event_refs': revisions,
        'state_read_evidence': 'RECORDED' if all('runtime_snapshot' in c for c in trace.get('model_calls', [])) else MISSING,
        'observation_censored': trace.get('observation_censored', MISSING),
        'warning': 'Exposure is not dependency. Communication return paths are not authority loops; no candidate is not a reviewed absence of loops.'}
