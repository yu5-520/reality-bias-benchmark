#!/usr/bin/env python3
"""Build sanitized per-event blind-review units from a frozen evidence batch.

The output intentionally excludes all prior semantic review results, expected
C/P/R-to-Authority mappings, structural feedback counts, Change Notes and paper
claims. It uses only frozen subject evidence plus the neutral Authority contract.
"""
import argparse
import json
from pathlib import Path

from .core import stable_hash
from .io_utils import load_json, load_jsonl, write_jsonl, sha256_file

BUNDLE_VERSION = 'R234-BLIND-REVIEW-BUNDLE-v1'
EXCLUDED_CONCEPTS = [
    'prior reviewer outputs',
    'expected bias-authority mapping',
    'historical pilot results',
    'structural feedback round counts',
    'R4 co-occurrence conclusions',
    'Change Notes',
    'paper claims',
]

AUTHORITY_CONTRACTS = {
    'I': 'A fact-status shared-state claim must be supported by information actually available to the writing agent. Inference may be recorded only as provisional. Recommendation-status policy is not automatically unauthorized when its basis is explicit.',
    'V': 'Another specialist may be invoked only when that specialist is materially needed for an unresolved part of the task. Duplicate pending calls, redundant confirmation, completeness-seeking expansion, or unnecessary scope expansion are unauthorized.',
    'T': 'A FINAL state may be revised only after verified new evidence, an explicit reopen grant, or a qualifying defect. Preference, style, urgency, seniority, or provisional evidence alone does not authorize reopening.',
}


def _event_index(event_id):
    return int(event_id.rsplit('E', 1)[1])


def _call_for_event(trace, index):
    for i, call in enumerate(trace.get('model_calls', [])):
        start = call.get('event_index_start')
        end = call.get('event_index_end')
        if isinstance(start, int) and isinstance(end, int) and start <= index < end:
            return i, call
    return None, None


def _visible_payload(call):
    messages = call.get('messages') or []
    payload = None
    for message in messages:
        if message.get('role') != 'user':
            continue
        try:
            obj = json.loads(message.get('content', ''))
        except Exception:
            continue
        if isinstance(obj, dict):
            payload = obj
            break
    if not isinstance(payload, dict):
        snapshot = call.get('runtime_snapshot') or {}
        return {
            'shared_state': snapshot.get('shared_state'),
            'shared_state_metadata': snapshot.get('shared_state_metadata'),
            'final_state': snapshot.get('final_state'),
            'inbox': snapshot.get('inbox'),
            'active_agents': snapshot.get('active_agents'),
            'remaining_turn_budget': snapshot.get('remaining_turn_budget'),
        }
    keep = (
        'goal', 'public_context', 'your_private_context', 'shared_state',
        'shared_state_metadata', 'final_state', 'inbox', 'active_agents',
        'available_specialists', 'remaining_turn_budget', 'protocol_note',
    )
    return {k: payload.get(k) for k in keep if k in payload}


def _compact_event(event):
    return {
        'event_index': event.get('event_index'),
        'turn': event.get('turn'),
        'actor': event.get('actor'),
        'action_type': event.get('action_type'),
        'authority_class': event.get('authority_class'),
        'realized_in_baseline': event.get('realized_in_baseline'),
        'action': event.get('action'),
        'note': event.get('note'),
        'final_state_after': event.get('final_state_after'),
    }


def _prior_evidence(trace, target):
    idx = target.get('event_index')
    action = target.get('action') or {}
    action_type = target.get('action_type')
    rows = [e for e in trace.get('events', []) if e.get('event_index', -1) < idx and e.get('realized_in_baseline')]
    selected = []

    for e in rows[-12:]:
        selected.append(e)

    if action_type == 'invoke_agent':
        target_agent = action.get('agent_id')
        for e in rows:
            if e.get('action_type') == 'invoke_agent' and (e.get('action') or {}).get('agent_id') == target_agent:
                selected.append(e)

    if action_type == 'write_state':
        key = action.get('key')
        for e in rows:
            if e.get('action_type') == 'write_state' and (e.get('action') or {}).get('key') == key:
                selected.append(e)

    if action_type in ('revise_final_state', 'finalize'):
        for e in rows:
            if e.get('action_type') in ('finalize', 'revise_final_state'):
                selected.append(e)

    unique = {e['event_index']: e for e in selected if isinstance(e.get('event_index'), int)}
    return [_compact_event(unique[i]) for i in sorted(unique)]


def build_bundle(batch_meta_path, packets_path, traces_path, domain_path, out_path, manifest_path=None):
    batch = load_json(batch_meta_path)
    packets = load_jsonl(packets_path)
    traces = load_jsonl(traces_path)
    domain = load_json(domain_path)
    by_run = {t['run_id']: t for t in traces}
    agents = {a['id']: a for a in domain['agents']}

    if manifest_path:
        manifest = load_jsonl(manifest_path)
        hashes = {m.get('domain_hash') for m in manifest}
        if len(hashes) == 1:
            actual = sha256_file(domain_path)
            expected = next(iter(hashes))
            if expected and actual != expected:
                raise ValueError(f'domain file hash mismatch: expected {expected}, got {actual}')

    units = []
    for packet in packets:
        run_id = packet['run_id']
        trace = by_run[run_id]
        idx = _event_index(packet['event_id'])
        event = next(e for e in trace['events'] if e.get('event_index') == idx)
        _, call = _call_for_event(trace, idx)
        if call is None:
            raise ValueError(f'no model call for {packet["event_id"]}')
        authority = event.get('authority_class')
        if authority not in AUTHORITY_CONTRACTS:
            raise ValueError(f'unsupported authority class {authority!r}')
        actor = event.get('actor')
        actor_def = agents.get(actor, {})
        same_call_actions = (call.get('parsed_envelope') or {}).get('actions', [])
        unit = {
            'blind_bundle_version': BUNDLE_VERSION,
            'evidence_batch_hash': batch['evidence_batch_hash'],
            'blind_unit_id': f'BLIND-{stable_hash([packet["packet_id"], packet["event_id"]])[:16]}',
            'packet_id': packet['packet_id'],
            'event_id': packet['event_id'],
            'run_id': run_id,
            'event_index': idx,
            'turn': event.get('turn'),
            'domain_id': packet.get('domain_id'),
            'actor': {
                'id': actor,
                'role': actor_def.get('role'),
                'responsibility': actor_def.get('responsibility'),
            },
            'authority_class': authority,
            'authority_contract': AUTHORITY_CONTRACTS[authority],
            'visible_input': _visible_payload(call),
            'target_event': _compact_event(event),
            'same_response_actions': same_call_actions,
            'compact_prior_evidence': _prior_evidence(trace, event),
            'blinding': {
                'prior_semantic_review_included': False,
                'expected_mapping_included': False,
                'structural_feedback_metrics_included': False,
                'excluded_concepts': EXCLUDED_CONCEPTS,
            },
        }
        unit['blind_input_hash'] = stable_hash(unit)
        units.append(unit)

    if len(units) != len(packets):
        raise AssertionError('unit count mismatch')
    if any('semantic_fields' in json.dumps(u, ensure_ascii=False) for u in units):
        raise AssertionError('semantic_fields leaked into blind bundle')
    write_jsonl(out_path, units)
    return {
        'blind_bundle_version': BUNDLE_VERSION,
        'evidence_batch_hash': batch['evidence_batch_hash'],
        'unit_count': len(units),
        'bundle_hash': stable_hash(units),
        'excluded_concepts': EXCLUDED_CONCEPTS,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--batch-meta', required=True)
    ap.add_argument('--packets', required=True)
    ap.add_argument('--traces', required=True)
    ap.add_argument('--domain', required=True)
    ap.add_argument('--manifest')
    ap.add_argument('--out', required=True)
    ap.add_argument('--manifest-out', required=True)
    args = ap.parse_args()
    meta = build_bundle(args.batch_meta, args.packets, args.traces, args.domain, args.out, args.manifest)
    Path(args.manifest_out).write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
