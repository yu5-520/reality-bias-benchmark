#!/usr/bin/env python3
"""Compare Measurement v2 structural coverage with frozen Reviewer A/B v1 annotations.

This is a diagnostic, not adjudication. Reviewer v1 labels are never treated as
truth for Measurement v2.
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

VERSION = 'R234-V2-V1-COVERAGE-ANALYSIS-v0.1'
FAMILIES = {
    'STATE_WRITE': {'STATE_WRITE_CANDIDATE'},
    'INVOCATION': {'INVOCATION_EXPANSION_CANDIDATE'},
    'FINAL_REVISION': {'FINAL_REVISION_CANDIDATE'},
    'HIGH_CERTAINTY_WRITE': {'HIGH_CERTAINTY_STATE_WRITE_CANDIDATE'},
    'EXPLICIT_STATUS_JUMP': {'EPISTEMIC_STATUS_JUMP_CANDIDATE'},
    'POST_SETTLEMENT': {
        'POST_SETTLEMENT_STATE_WRITE_CANDIDATE',
        'POST_SETTLEMENT_INVOCATION_CANDIDATE',
        'POST_SETTLEMENT_REVISION_CANDIDATE',
    },
    'REPEAT_INVOCATION': {'REPEAT_SPECIALIST_INVOCATION_CANDIDATE'},
    'PENDING_DUPLICATE_INVOCATION': {'PENDING_DUPLICATE_INVOCATION_CANDIDATE'},
}


def stable_hash(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def load_jsonl(path):
    return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]


def build_coverage(r2_path, packets_path, reviewer_b_path, agreement_path):
    r2 = load_jsonl(r2_path)
    packets = load_jsonl(packets_path)
    reviewer_b = load_jsonl(reviewer_b_path)
    agreement = json.loads(Path(agreement_path).read_text(encoding='utf-8'))

    candidate_map = {(r['run_id'], r['event_index']): r for r in r2}
    packet_map = {(r['run_id'], r['target']['event_index']): r for r in packets}
    b_map = {(r['run_id'], r['event_index']): r for r in reviewer_b}
    disagreement_map = {(r['run_id'], r['event_index']): r for r in agreement['disagreements']}
    keys = set(b_map)
    if set(candidate_map) != keys or set(packet_map) != keys:
        raise ValueError(
            f'event coverage mismatch r2={len(candidate_map)} packets={len(packet_map)} reviewer_b={len(keys)}'
        )

    rows = []
    for key in sorted(keys):
        b = b_map[key]
        disagreement = disagreement_map.get(key)
        candidate = candidate_map[key]
        a_labels = list(disagreement['reviewer_a_labels']) if disagreement else list(b['bias_labels'])
        a_auth = disagreement['reviewer_a_authorization'] if disagreement else b['authorization_judgment']
        rows.append({
            'run_id': key[0],
            'event_index': key[1],
            'action_type': candidate['action_type'],
            'realized': candidate['realized_in_baseline'],
            'candidate_types': candidate['candidate_types'],
            'a_labels': a_labels,
            'b_labels': list(b['bias_labels']),
            'a_auth': a_auth,
            'b_auth': b['authorization_judgment'],
            'disagreement': key in disagreement_map,
        })

    reviewers = {}
    for tag, label_key, auth_key in (
        ('A', 'a_labels', 'a_auth'),
        ('B', 'b_labels', 'b_auth'),
    ):
        by_label = {}
        for label in ('C', 'P', 'R'):
            selected = [x for x in rows if label in x[label_key]]
            by_label[label] = {
                'positive_event_count': len(selected),
                'realized_positive_count': sum(bool(x['realized']) for x in selected),
                'action_type_counts': dict(sorted(Counter(x['action_type'] for x in selected).items())),
                'candidate_family_counts': {
                    name: sum(bool(set(x['candidate_types']) & types) for x in selected)
                    for name, types in FAMILIES.items()
                },
            }
        primary_like = [
            x for x in rows
            if x['realized'] and x[auth_key] == 'UNAUTHORIZED' and x[label_key]
        ]
        reviewers[tag] = {
            'labels': by_label,
            'realized_unauthorized_mechanism_coded_count': len(primary_like),
        }

    disagreements = [x for x in rows if x['disagreement']]
    result = {
        'version': VERSION,
        'event_count': len(rows),
        'measurement_v2_target_coverage_count': len(candidate_map),
        'reviewer_v2_packet_coverage_count': len(packet_map),
        'v1_disagreement_count': len(disagreements),
        'v1_disagreement_target_coverage_count': sum(
            (x['run_id'], x['event_index']) in candidate_map for x in disagreements
        ),
        'reviewers': reviewers,
        'disagreement_candidate_family_counts': {
            name: sum(bool(set(x['candidate_types']) & types) for x in disagreements)
            for name, types in FAMILIES.items()
        },
        'interpretation': [
            'This is a coverage/alignment diagnostic only; Reviewer v1 labels are not ground truth for Measurement v2.',
            'A v1 label outside a narrow structural family is not automatically a false positive because semantic promotion/scope/retrospective effects can be embedded in other action types.',
            'The diagnostic shows where v1 labels were behavior-shaped and whether v2 target-local packets preserve the relevant events for later boundary review.',
        ],
        'paid_api_calls': 0,
    }
    result['analysis_hash'] = stable_hash(result)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--r2', required=True)
    ap.add_argument('--packets', required=True)
    ap.add_argument('--reviewer-b', required=True)
    ap.add_argument('--agreement', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    result = build_coverage(args.r2, args.packets, args.reviewer_b, args.agreement)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
