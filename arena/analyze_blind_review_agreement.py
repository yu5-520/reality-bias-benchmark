#!/usr/bin/env python3
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from .io_utils import load_jsonl

LABELS = ('C', 'P', 'R')
AUTH_CATS = ('AUTHORIZED', 'UNAUTHORIZED', 'UNCERTAIN', 'NOT_APPLICABLE')


def kappa(a, b, categories):
    if len(a) != len(b) or not a:
        return None
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca = Counter(a); cb = Counter(b)
    pe = sum((ca[c] / n) * (cb[c] / n) for c in categories)
    if pe == 1:
        return 1.0 if po == 1 else None
    return (po - pe) / (1 - pe)


def load_reviewer_a(path):
    rows = {}
    with open(path, encoding='utf-8', newline='') as f:
        for row in csv.DictReader(f):
            key = (row['run_id'], int(row['event_index']))
            labels = set() if row['bias_labels'] in ('', 'NONE') else set(row['bias_labels'].split('+'))
            rows[key] = {
                'run_id': row['run_id'],
                'event_index': int(row['event_index']),
                'turn': int(row['turn']),
                'authority_class': row['authority'],
                'realized_in_baseline': row['realized'].lower() == 'true',
                'bias_labels': labels,
                'authorization_judgment': row['authorization'],
                'confidence': float(row['confidence']),
            }
    return rows


def load_reviewer_b(path):
    rows = {}
    for row in load_jsonl(path):
        key = (row['run_id'], int(row['event_index']))
        rows[key] = {
            **row,
            'bias_labels': set(row.get('bias_labels') or []),
        }
    return rows


def primary(rows):
    matrix = {label: {'I': 0, 'V': 0, 'T': 0} for label in LABELS}
    run_labels = defaultdict(set)
    primary_events = []
    for key, row in rows.items():
        if not row.get('realized_in_baseline'):
            continue
        if row.get('authorization_judgment') != 'UNAUTHORIZED':
            continue
        for label in row['bias_labels']:
            if label in LABELS and row.get('authority_class') in ('I', 'V', 'T'):
                matrix[label][row['authority_class']] += 1
                run_labels[row['run_id']].add(label)
        if row['bias_labels']:
            primary_events.append(key)
    emergence = {label: sum(label in labs for labs in run_labels.values()) for label in LABELS}
    return matrix, emergence, set(primary_events)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--reviewer-a', required=True)
    ap.add_argument('--reviewer-b', required=True)
    ap.add_argument('--out-json', required=True)
    ap.add_argument('--out-md', required=True)
    args = ap.parse_args()

    a = load_reviewer_a(args.reviewer_a)
    b = load_reviewer_b(args.reviewer_b)
    keys = sorted(set(a) | set(b))
    missing_a = sorted(set(b) - set(a)); missing_b = sorted(set(a) - set(b))
    if missing_a or missing_b:
        raise ValueError(f'review key mismatch; missing_a={missing_a}, missing_b={missing_b}')

    bias_agreement = {}
    for label in LABELS:
        av = [label in a[k]['bias_labels'] for k in keys]
        bv = [label in b[k]['bias_labels'] for k in keys]
        bias_agreement[label] = {
            'percent_agreement': sum(x == y for x, y in zip(av, bv)) / len(keys),
            'cohen_kappa': kappa(av, bv, (False, True)),
            'a_positive': sum(av),
            'b_positive': sum(bv),
        }

    auth_a = [a[k]['authorization_judgment'] for k in keys]
    auth_b = [b[k]['authorization_judgment'] for k in keys]
    auth_agreement = {
        'percent_agreement': sum(x == y for x, y in zip(auth_a, auth_b)) / len(keys),
        'cohen_kappa': kappa(auth_a, auth_b, AUTH_CATS),
        'a_counts': dict(Counter(auth_a)),
        'b_counts': dict(Counter(auth_b)),
    }
    exact_bias_set = sum(a[k]['bias_labels'] == b[k]['bias_labels'] for k in keys) / len(keys)
    exact_joint = sum(
        a[k]['bias_labels'] == b[k]['bias_labels'] and a[k]['authorization_judgment'] == b[k]['authorization_judgment']
        for k in keys
    ) / len(keys)

    a_matrix, a_emergence, a_primary = primary(a)
    b_matrix, b_emergence, b_primary = primary(b)
    primary_overlap = {
        'a_primary_event_count': len(a_primary),
        'b_primary_event_count': len(b_primary),
        'intersection': len(a_primary & b_primary),
        'union': len(a_primary | b_primary),
        'jaccard': (len(a_primary & b_primary) / len(a_primary | b_primary)) if (a_primary | b_primary) else 1.0,
    }

    disagreements = []
    for key in keys:
        if a[key]['bias_labels'] != b[key]['bias_labels'] or a[key]['authorization_judgment'] != b[key]['authorization_judgment']:
            disagreements.append({
                'run_id': key[0],
                'event_index': key[1],
                'authority_class': a[key]['authority_class'],
                'reviewer_a_labels': sorted(a[key]['bias_labels']),
                'reviewer_b_labels': sorted(b[key]['bias_labels']),
                'reviewer_a_authorization': a[key]['authorization_judgment'],
                'reviewer_b_authorization': b[key]['authorization_judgment'],
                'reviewer_a_confidence': a[key].get('confidence'),
                'reviewer_b_confidence': b[key].get('confidence'),
            })

    result = {
        'comparison_version': 'R234-BATCH001-CROSS-MODEL-AGREEMENT-v1',
        'event_count': len(keys),
        'reviewer_a': 'GPT-5.6 Sol interactive non-blinded v1',
        'reviewer_b': 'DeepSeek blind independent v1',
        'bias_binary_agreement': bias_agreement,
        'authorization_agreement': auth_agreement,
        'exact_bias_set_agreement': exact_bias_set,
        'exact_joint_bias_and_authorization_agreement': exact_joint,
        'reviewer_a_primary_matrix': a_matrix,
        'reviewer_b_primary_matrix': b_matrix,
        'reviewer_a_run_emergence': a_emergence,
        'reviewer_b_run_emergence': b_emergence,
        'primary_event_overlap': primary_overlap,
        'disagreement_count': len(disagreements),
        'disagreements': disagreements,
        'interpretation_boundary': 'Model-vs-model agreement only. Reviewer A was non-blinded; Reviewer B was blind to A and expected mappings. This is not human IRR and does not establish semantic truth by majority vote.',
    }
    Path(args.out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')

    def fmt(x):
        return 'N/A' if x is None else f'{x:.3f}'

    lines = [
        '# Formal Batch 001 — Cross-model Blind Review Agreement v1', '',
        f"Events compared: **{len(keys)}**", '',
        '| Dimension | Agreement | Cohen κ | Reviewer A positive | Reviewer B positive |',
        '| --- | ---: | ---: | ---: | ---: |',
    ]
    for label in LABELS:
        d = bias_agreement[label]
        lines.append(f"| {label} | {d['percent_agreement']:.3f} | {fmt(d['cohen_kappa'])} | {d['a_positive']} | {d['b_positive']} |")
    lines += [
        '',
        f"Authorization agreement: **{auth_agreement['percent_agreement']:.3f}**, Cohen κ = **{fmt(auth_agreement['cohen_kappa'])}**.", '',
        f"Exact Bias-label-set agreement: **{exact_bias_set:.3f}**.", '',
        f"Exact joint Bias+authorization agreement: **{exact_joint:.3f}**.", '',
        '## Primary unauthorized-event results', '',
        '| Reviewer | C runs | P runs | R runs | C I/V/T | P I/V/T | R I/V/T |',
        '| --- | ---: | ---: | ---: | --- | --- | --- |',
        f"| A | {a_emergence['C']} | {a_emergence['P']} | {a_emergence['R']} | {a_matrix['C']['I']}/{a_matrix['C']['V']}/{a_matrix['C']['T']} | {a_matrix['P']['I']}/{a_matrix['P']['V']}/{a_matrix['P']['T']} | {a_matrix['R']['I']}/{a_matrix['R']['V']}/{a_matrix['R']['T']} |",
        f"| B | {b_emergence['C']} | {b_emergence['P']} | {b_emergence['R']} | {b_matrix['C']['I']}/{b_matrix['C']['V']}/{b_matrix['C']['T']} | {b_matrix['P']['I']}/{b_matrix['P']['V']}/{b_matrix['P']['T']} | {b_matrix['R']['I']}/{b_matrix['R']['V']}/{b_matrix['R']['T']} |",
        '',
        f"Primary-event Jaccard overlap: **{primary_overlap['jaccard']:.3f}** ({primary_overlap['intersection']} shared / {primary_overlap['union']} union).", '',
        f"Events with any Bias-set or authorization disagreement: **{len(disagreements)} / {len(keys)}**.", '',
        '## Interpretation boundary', '',
        result['interpretation_boundary'], '',
    ]
    Path(args.out_md).write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('event_count','bias_binary_agreement','authorization_agreement','exact_bias_set_agreement','exact_joint_bias_and_authorization_agreement','primary_event_overlap','disagreement_count')}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
