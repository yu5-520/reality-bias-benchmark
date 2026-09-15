#!/usr/bin/env python3
"""Build compact Reviewer-v2 packets plus deterministic expansion refs.

The compact layer reduces repeated runtime state while preserving the natural-language
material needed for semantic boundary review. It never selects content by C/P/R
meaning. Selection is structural only: target key/patch, incoming source refs, target
call, downstream calls, and the enclosing feedback interval.
"""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

VERSION = 'R234-REVIEWER-V2-COMPACT-PACKETS-v0.1'
R2_PACKET_VERSION = 'R234-REVIEWER-V2-R2-COMPACT-PACKET-v0.1'
R3_PACKET_VERSION = 'R234-REVIEWER-V2-R3-COMPACT-PACKET-v0.1'
R4_PACKET_VERSION = 'R234-REVIEWER-V2-R4-COMPACT-PACKET-v0.1'
MISSING = 'NOT_RECORDED_IN_SOURCE_VERSION'
NOT_ADJUDICATED = 'NOT_ADJUDICATED'


def stable_hash(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def load_jsonl(path):
    return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]


def write_jsonl(path, rows):
    Path(path).write_text(''.join(json.dumps(x, ensure_ascii=False, sort_keys=True) + '\n' for x in rows), encoding='utf-8')


def _event_ref(run_id, idx):
    return f'{run_id}:EVENT:{idx:04d}'


def _call_ref(run_id, idx):
    return f'{run_id}:CALL:{idx:04d}'


def _event_index(ref):
    if not isinstance(ref, str) or ':EVENT:' not in ref:
        return None
    try:
        return int(ref.rsplit(':', 1)[1])
    except Exception:
        return None


def _call_for_event(trace, event_index):
    for i, call in enumerate(trace.get('model_calls', [])):
        start, end = call.get('event_index_start'), call.get('event_index_end')
        if isinstance(start, int) and isinstance(end, int) and start <= event_index < end:
            return i, call
    return None, None


def _user_payload(call):
    if not isinstance(call, dict):
        return {}
    for message in call.get('messages') or []:
        if message.get('role') != 'user':
            continue
        try:
            obj = json.loads(message.get('content', ''))
        except Exception:
            continue
        if isinstance(obj, dict):
            return obj
    snap = call.get('runtime_snapshot')
    return snap if isinstance(snap, dict) else {}


def _role(payload, agent_id):
    for row in payload.get('available_specialists') or []:
        if isinstance(row, dict) and row.get('id') == agent_id:
            return row
    return None


def _action_events(trace, call_index):
    call = trace.get('model_calls', [])[call_index]
    start, end = call.get('event_index_start'), call.get('event_index_end')
    if not isinstance(start, int) or not isinstance(end, int):
        return []
    return [
        e for e in trace.get('events', [])
        if start <= e.get('event_index', -1) < end and e.get('actor') == call.get('agent_id')
    ]


def _output(call):
    envelope = call.get('parsed_envelope') if isinstance(call.get('parsed_envelope'), dict) else {}
    return {
        'decision_summary': call.get('decision_summary', envelope.get('decision_summary', MISSING)),
        'actions': envelope.get('actions', MISSING),
    }


def _relevant_keys(candidate):
    facts = candidate.get('structural_facts') or {}
    keys = []
    if facts.get('state_key'):
        keys.append(facts['state_key'])
    if isinstance(facts.get('patch_keys'), list):
        keys.extend(facts['patch_keys'])
    return list(dict.fromkeys(keys))


def _static_context(call):
    payload = _user_payload(call)
    return {
        'goal': payload.get('goal', MISSING),
        'public_context': payload.get('public_context', MISSING),
        'available_specialists': payload.get('available_specialists', MISSING),
        'protocol_note': payload.get('protocol_note', MISSING),
    }


def _compact_visible_input(call, selected_keys):
    payload = _user_payload(call)
    state = payload.get('shared_state') if isinstance(payload.get('shared_state'), dict) else {}
    metadata = payload.get('shared_state_metadata') if isinstance(payload.get('shared_state_metadata'), dict) else {}
    final_state = payload.get('final_state')

    metadata_index = {}
    for key, value in metadata.items():
        if isinstance(value, dict):
            metadata_index[key] = {
                k: value.get(k) for k in ('status', 'writer', 'event_index') if k in value
            }
        else:
            metadata_index[key] = value

    selected_metadata = {key: metadata[key] for key in selected_keys if key in metadata}
    selected_values = {key: state[key] for key in selected_keys if key in state}

    if isinstance(final_state, dict):
        final_summary = {
            'keys': sorted(final_state),
            'selected_values': {key: final_state[key] for key in selected_keys if key in final_state},
            'full_state_hash': stable_hash(final_state),
        }
    elif final_state is None:
        final_summary = None
    else:
        final_summary = {'value': final_state, 'full_state_hash': stable_hash(final_state)}

    return {
        'your_private_context': payload.get('your_private_context', MISSING),
        'inbox': payload.get('inbox', MISSING),
        'active_agents': payload.get('active_agents', MISSING),
        'remaining_turn_budget': payload.get('remaining_turn_budget', MISSING),
        'shared_state': {
            'keys': sorted(state),
            'selected_values': selected_values,
            'metadata_index': metadata_index,
            'selected_metadata': selected_metadata,
            'full_state_hash': stable_hash(state),
        },
        'final_state': final_summary,
    }


def _compact_call(trace, call_index, selected_keys):
    run_id = trace['run_id']
    call = trace.get('model_calls', [])[call_index]
    payload = _user_payload(call)
    events = _action_events(trace, call_index)
    return {
        'call_ref': _call_ref(run_id, call_index),
        'agent_id': call.get('agent_id'),
        'turn': call.get('turn'),
        'role': _role(payload, call.get('agent_id')),
        'input_message_ids': call.get('input_message_ids', MISSING),
        'input_invocation_ids': call.get('input_invocation_ids', MISSING),
        'visible_input': _compact_visible_input(call, selected_keys),
        'output': _output(call),
        'output_events': [
            {
                'event_ref': _event_ref(run_id, e['event_index']),
                'action_type': e.get('action_type'),
                'authority_class': e.get('authority_class'),
                'realized_in_baseline': e.get('realized_in_baseline'),
                'action': e.get('action'),
            }
            for e in events
        ],
    }


def _target_event(trace, candidate):
    idx = candidate['event_index']
    event = next(e for e in trace.get('events', []) if e.get('event_index') == idx)
    return {
        'event_ref': candidate['event_ref'],
        'event_index': idx,
        'turn': event.get('turn'),
        'actor': event.get('actor'),
        'action_type': event.get('action_type'),
        'authority_class': event.get('authority_class'),
        'realized_in_baseline': event.get('realized_in_baseline'),
        'action': event.get('action'),
    }


def _expansion(refs):
    return {
        'max_attempts': 1,
        'allowed_refs': list(dict.fromkeys(ref for ref in refs if isinstance(ref, str) and ref)),
        'rule': 'Expansion returns exact frozen records by explicit ref only; it does not add reviewer history or inferred semantic context.',
    }


def build_r2_packets(trace, candidates, task_goal, batch_hash):
    run_id = trace['run_id']
    rows = []
    for candidate in candidates:
        idx = candidate['event_index']
        call_index, call = _call_for_event(trace, idx)
        if call is None:
            continue
        keys = _relevant_keys(candidate)
        facts = candidate.get('structural_facts') or {}
        refs = [_call_ref(run_id, call_index), candidate['event_ref']]
        if facts.get('same_key_prior_event_ref'):
            refs.append(facts['same_key_prior_event_ref'])
        row = {
            'packet_version': R2_PACKET_VERSION,
            'compact_family_version': VERSION,
            'evidence_batch_hash': batch_hash,
            'run_id': run_id,
            'packet_id': f'{run_id}:R2V2CPKT:{idx:04d}:{stable_hash(candidate["candidate_id"])[:8]}',
            'review_layer': 'R2',
            'original_task_goal': task_goal,
            'task_context': _static_context(call),
            'target_candidate': candidate,
            'target_event': _target_event(trace, candidate),
            'target_call': _compact_call(trace, call_index, keys),
            'context_expansion': _expansion(refs),
            'boundary_fields': {
                'epistemic_transition': NOT_ADJUDICATED,
                'goal_relation': NOT_ADJUDICATED,
                'goal_focus_transition': NOT_ADJUDICATED,
                'local_retrospective_outcome': NOT_ADJUDICATED,
                'authorization_judgment': NOT_ADJUDICATED,
            },
            'prior_reviewer_outputs_included': False,
            'expected_mechanism_mapping_included': False,
            'warning': 'Structural candidate only. Natural-language boundary meaning is not machine-adjudicated.',
        }
        row['packet_hash'] = stable_hash(row)
        rows.append(row)
    return rows


def build_r3_packets(trace, candidates, windows, task_goal, batch_hash):
    run_id = trace['run_id']
    candidate_by_id = {x['candidate_id']: x for x in candidates}
    rows = []
    for window in windows:
        candidate = candidate_by_id.get(window.get('source_candidate_id'))
        if not candidate:
            continue
        idx = candidate['event_index']
        call_index, target_call = _call_for_event(trace, idx)
        if target_call is None:
            continue
        keys = _relevant_keys(candidate)
        refs = [_call_ref(run_id, call_index), candidate['event_ref']]
        refs.extend(window.get('same_key_history_refs') or [])

        downstream_calls = []
        seen_calls = set()
        for ref in window.get('downstream_output_event_refs') or []:
            event_idx = _event_index(ref)
            if not isinstance(event_idx, int):
                continue
            downstream_index, downstream_call = _call_for_event(trace, event_idx)
            if downstream_call is None or downstream_index in seen_calls:
                continue
            seen_calls.add(downstream_index)
            refs.append(_call_ref(run_id, downstream_index))
            downstream_calls.append(_compact_call(trace, downstream_index, keys))

        incoming = window.get('incoming_structural_relations') or []
        outgoing = window.get('outgoing_structural_relations') or []
        for relation in incoming + outgoing:
            source_ref = relation.get('source_ref')
            if isinstance(source_ref, str) and ':EVENT:' in source_ref:
                refs.append(source_ref)

        row = {
            'packet_version': R3_PACKET_VERSION,
            'compact_family_version': VERSION,
            'evidence_batch_hash': batch_hash,
            'run_id': run_id,
            'packet_id': f'{run_id}:R3V2CPKT:{idx:04d}:{stable_hash(window["window_id"])[:8]}',
            'review_layer': 'R3',
            'original_task_goal': task_goal,
            'task_context': _static_context(target_call),
            'target_candidate': {
                'candidate_id': candidate['candidate_id'],
                'event_ref': candidate['event_ref'],
                'event_index': idx,
                'candidate_types': candidate.get('candidate_types'),
                'effect_scope': candidate.get('effect_scope'),
                'structural_facts': candidate.get('structural_facts'),
            },
            'target_call': _compact_call(trace, call_index, keys),
            'machine_lineage': {
                'incoming_structural_relations': incoming,
                'outgoing_structural_relations': outgoing,
                'same_key_history_refs': window.get('same_key_history_refs') or [],
                'downstream_output_event_refs': window.get('downstream_output_event_refs') or [],
            },
            'downstream_calls': downstream_calls,
            'context_expansion': _expansion(refs),
            'boundary_fields': {
                'semantic_adoption': NOT_ADJUDICATED,
                'decision_effect': NOT_ADJUDICATED,
                'lineage_outcome': NOT_ADJUDICATED,
                'penetration_range_refs': NOT_ADJUDICATED,
            },
            'prior_reviewer_outputs_included': False,
            'expected_mechanism_mapping_included': False,
            'warning': 'Exposure/read/version paths are structural only. Adoption and decision effect require semantic review.',
        }
        row['packet_hash'] = stable_hash(row)
        rows.append(row)
    return rows


def build_r4_packets(trace, candidates, windows, task_goal, batch_hash):
    run_id = trace['run_id']
    rows = []
    for window in windows:
        interval = window.get('interval') or {}
        start, end = interval.get('event_index_start'), interval.get('event_index_end')
        if not isinstance(start, int) or not isinstance(end, int):
            continue
        interval_candidates = [c for c in candidates if start <= c.get('event_index', -1) <= end]
        keys = []
        for candidate in interval_candidates:
            keys.extend(_relevant_keys(candidate))
        keys = list(dict.fromkeys(keys))

        calls = []
        refs = list(window.get('evidence_refs') or [])
        static_context = None
        for call_index, call in enumerate(trace.get('model_calls', [])):
            call_start, call_end = call.get('event_index_start'), call.get('event_index_end')
            if not isinstance(call_start, int) or not isinstance(call_end, int):
                continue
            if call_end > start and call_start <= end:
                if static_context is None:
                    static_context = _static_context(call)
                calls.append(_compact_call(trace, call_index, keys))
                refs.append(_call_ref(run_id, call_index))

        row = {
            'packet_version': R4_PACKET_VERSION,
            'compact_family_version': VERSION,
            'evidence_batch_hash': batch_hash,
            'run_id': run_id,
            'packet_id': f'{run_id}:R4V2CPKT:{window.get("round_index", 0):04d}:{stable_hash(window["window_id"])[:8]}',
            'review_layer': 'R4',
            'original_task_goal': task_goal,
            'task_context': static_context or {'goal': task_goal},
            'structural_window': window,
            'candidate_context': [
                {
                    'candidate_id': c['candidate_id'],
                    'event_ref': c['event_ref'],
                    'event_index': c['event_index'],
                    'candidate_types': c.get('candidate_types'),
                    'effect_scope': c.get('effect_scope'),
                }
                for c in interval_candidates
            ],
            'interval_calls': calls,
            'context_expansion': _expansion(refs),
            'boundary_fields': {
                'correction': NOT_ADJUDICATED,
                'persistence': NOT_ADJUDICATED,
                'regeneration': NOT_ADJUDICATED,
                'amplification': NOT_ADJUDICATED,
                'laundering': NOT_ADJUDICATED,
                'normalization': NOT_ADJUDICATED,
                'black_hole': NOT_ADJUDICATED,
            },
            'prior_reviewer_outputs_included': False,
            'expected_mechanism_mapping_included': False,
            'warning': 'Neutral structural feedback window only; CPR, laundering and black-hole semantics remain unadjudicated.',
        }
        row['packet_hash'] = stable_hash(row)
        rows.append(row)
    return rows


def build_batch(traces_path, manifest_path, r2_path, r3_path, r4_path, outdir, batch_hash):
    traces = load_jsonl(traces_path)
    manifest = {x['run_id']: x for x in load_jsonl(manifest_path)}
    candidates, lineages, dynamics = load_jsonl(r2_path), load_jsonl(r3_path), load_jsonl(r4_path)
    candidates_by_run, lineages_by_run, dynamics_by_run = defaultdict(list), defaultdict(list), defaultdict(list)
    for row in candidates:
        candidates_by_run[row['run_id']].append(row)
    for row in lineages:
        lineages_by_run[row['run_id']].append(row)
    for row in dynamics:
        dynamics_by_run[row['run_id']].append(row)

    r2_packets, r3_packets, r4_packets = [], [], []
    for trace in traces:
        run_id = trace['run_id']
        goal = manifest.get(run_id, {}).get('task_goal', MISSING)
        r2_packets.extend(build_r2_packets(trace, candidates_by_run[run_id], goal, batch_hash))
        r3_packets.extend(build_r3_packets(trace, candidates_by_run[run_id], lineages_by_run[run_id], goal, batch_hash))
        r4_packets.extend(build_r4_packets(trace, candidates_by_run[run_id], dynamics_by_run[run_id], goal, batch_hash))

    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    paths = {
        'r2': out / 'compact_r2_packets.jsonl',
        'r3': out / 'compact_r3_packets.jsonl',
        'r4': out / 'compact_r4_packets.jsonl',
    }
    write_jsonl(paths['r2'], r2_packets)
    write_jsonl(paths['r3'], r3_packets)
    write_jsonl(paths['r4'], r4_packets)

    summary = {
        'compact_packet_version': VERSION,
        'evidence_batch_hash': batch_hash,
        'r2_packet_count': len(r2_packets),
        'r3_packet_count': len(r3_packets),
        'r4_packet_count': len(r4_packets),
        'serialized_bytes': {key: path.stat().st_size for key, path in paths.items()},
        'semantic_labels_present': False,
        'paid_api_calls': 0,
        'context_expansion_max_attempts': 1,
        'warnings': [
            'Compaction is structural, not semantic: omitted full call/state records remain available only through explicit expansion refs.',
            'A compact packet that is semantically insufficient should yield UNCERTAIN or request its single bounded context expansion, not trigger guesswork.',
        ],
    }
    summary['output_hash'] = stable_hash({'r2': r2_packets, 'r3': r3_packets, 'r4': r4_packets})
    (out / 'compact_packet_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True), encoding='utf-8')
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--traces', required=True)
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--r2', required=True)
    ap.add_argument('--r3', required=True)
    ap.add_argument('--r4', required=True)
    ap.add_argument('--batch-hash', required=True)
    ap.add_argument('--outdir', required=True)
    args = ap.parse_args()
    print(json.dumps(build_batch(args.traces, args.manifest, args.r2, args.r3, args.r4, args.outdir, args.batch_hash), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
