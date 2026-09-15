#!/usr/bin/env python3
"""Structurally deduplicate compact Reviewer-v2 R3 downstream calls.

This second-stage compaction removes repeated full input context from downstream calls.
It never uses semantic reviewer labels. State-read lineage retains the structurally
selected state values/metadata; message-read lineage retains the inbox. Everything
omitted remains reachable through the packet's frozen allowed expansion refs.
"""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

VERSION = 'R234-REVIEWER-V2-R3-COMPACT-v0.2'
PACKET_VERSION = 'R234-REVIEWER-V2-R3-COMPACT-PACKET-v0.2'


def stable_hash(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def load_jsonl(path):
    return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]


def write_jsonl(path, rows):
    Path(path).write_text(''.join(json.dumps(x, ensure_ascii=False, sort_keys=True) + '\n' for x in rows), encoding='utf-8')


def lineage_relation_types(packet):
    out = defaultdict(set)
    lineage = packet.get('machine_lineage') or {}
    for relation in lineage.get('outgoing_structural_relations') or []:
        target = relation.get('target_ref')
        evidence_type = relation.get('evidence_type')
        if target and evidence_type:
            out[target].add(evidence_type)
    return out


def slim_downstream_call(call, relation_types):
    visible = call.get('visible_input') or {}
    shared = visible.get('shared_state') or {}
    inbox = visible.get('inbox')
    if 'message_read_into_input' in relation_types:
        inbox_view = {
            'mode': 'FULL_FOR_STRUCTURAL_MESSAGE_READ',
            'value': inbox,
        }
    else:
        inbox_view = {
            'mode': 'HASH_ONLY_NO_DIRECT_MESSAGE_LINEAGE',
            'count': len(inbox) if isinstance(inbox, list) else None,
            'hash': stable_hash(inbox),
        }

    event_refs = []
    for event in call.get('output_events') or []:
        event_refs.append({
            'event_ref': event.get('event_ref'),
            'action_type': event.get('action_type'),
            'authority_class': event.get('authority_class'),
            'realized_in_baseline': event.get('realized_in_baseline'),
        })

    return {
        'call_ref': call.get('call_ref'),
        'agent_id': call.get('agent_id'),
        'turn': call.get('turn'),
        'role': call.get('role'),
        'input_message_ids': call.get('input_message_ids'),
        'input_invocation_ids': call.get('input_invocation_ids'),
        'structural_relation_types_from_target': sorted(relation_types),
        'lineage_input': {
            'selected_state_values': shared.get('selected_values'),
            'selected_state_metadata': shared.get('selected_metadata'),
            'shared_state_keys': shared.get('keys'),
            'shared_state_hash': shared.get('full_state_hash'),
            'inbox': inbox_view,
            'private_context_hash': stable_hash(visible.get('your_private_context')),
            'active_agents': visible.get('active_agents'),
            'remaining_turn_budget': visible.get('remaining_turn_budget'),
        },
        'output': call.get('output'),
        'output_event_refs': event_refs,
    }


def optimize_packet(packet):
    if packet.get('review_layer') != 'R3':
        raise ValueError('R3 packet required')
    relation_types = lineage_relation_types(packet)
    row = dict(packet)
    old_hash = packet.get('packet_hash')
    row['packet_version'] = PACKET_VERSION
    row['r3_compaction_version'] = VERSION
    row['source_compact_packet_hash'] = old_hash
    row['downstream_calls'] = [
        slim_downstream_call(call, relation_types.get(call.get('call_ref'), set()))
        for call in packet.get('downstream_calls') or []
    ]
    row['compaction_boundary'] = {
        'semantic_selection_used': False,
        'state_read_rule': 'retain selected structurally relevant state values/metadata; hash omitted context',
        'message_read_rule': 'retain inbox only when machine lineage records message_read_into_input',
        'output_rule': 'retain decision_summary/actions once; keep output event refs/Authority metadata without duplicate action payload',
        'expansion_rule': 'omitted full frozen call remains available only through existing allowed_refs',
    }
    row['warning'] = 'R3 v0.2 is structural deduplication only. If context is semantically insufficient, return UNCERTAIN or request the single bounded frozen-ref expansion.'
    row.pop('packet_hash', None)
    row['packet_hash'] = stable_hash(row)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--summary', required=True)
    args = ap.parse_args()

    source = load_jsonl(args.input)
    optimized = [optimize_packet(x) for x in source]
    write_jsonl(args.output, optimized)
    old_bytes = Path(args.input).stat().st_size
    new_bytes = Path(args.output).stat().st_size
    summary = {
        'version': VERSION,
        'packet_version': PACKET_VERSION,
        'packet_count': len(optimized),
        'source_bytes': old_bytes,
        'optimized_bytes': new_bytes,
        'optimized_fraction_of_source': new_bytes / old_bytes if old_bytes else None,
        'reduction_fraction': 1 - new_bytes / old_bytes if old_bytes else None,
        'semantic_selection_used': False,
        'semantic_labels_present': False,
        'provider_calls': 0,
        'bounded_expansion_preserved': all((x.get('context_expansion') or {}).get('max_attempts') == 1 for x in optimized),
        'output_hash': stable_hash(optimized),
        'warnings': [
            'Reduction is serialized byte reduction, not token or monetary reduction.',
            'Message-read lineage keeps inbox content; state-read lineage keeps structurally selected state values/metadata.',
            'Full omitted records remain available through the existing one-ref bounded expansion contract.'
        ],
    }
    Path(args.summary).write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
