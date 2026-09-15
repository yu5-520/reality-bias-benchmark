#!/usr/bin/env python3
"""Compare historical DeepSeek Reviewer-B v1 with DeepSeek Reviewer-v2 re-annotation.

This is a measurement-contract sensitivity analysis over the same frozen 70 Authority
bearing events. It is not inter-rater reliability: model family is intentionally held
constant while rubric, packet design and semantic contract changed.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

VERSION = 'R234-REVIEWER-V1-V2-MEASUREMENT-TRANSITION-v0.1'


def load_jsonl(path):
    return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]


def event_key_v1(row):
    return row['run_id'], int(row['event_index'])


def event_key_v2(row):
    ref = row['target_ref']
    run_id, raw_index = ref.split(':EVENT:', 1)
    return run_id, int(raw_index)


def labelset(row):
    labels = row.get('bias_labels') or []
    return '+'.join(sorted(labels)) if labels else 'NONE'


def count_sorted(values):
    return dict(sorted(Counter(values).items()))


def binary_kappa(a, b):
    if len(a) != len(b) or not a:
        return None
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b)) / n
    pa = sum(a) / n
    pb = sum(b) / n
    expected = pa * pb + (1 - pa) * (1 - pb)
    if expected == 1:
        return None
    return (observed - expected) / (1 - expected)


def analyze(v1_rows, v2_r2_rows, v2_synthesis_rows):
    v1 = {event_key_v1(x): x for x in v1_rows}
    v2 = {event_key_v2(x): x for x in v2_r2_rows}
    syn = {event_key_v2({'target_ref': x['target_ref']}): x for x in v2_synthesis_rows}
    if set(v1) != set(v2) or set(v1) != set(syn):
        raise ValueError('v1/v2 event populations are not identical')
    keys = sorted(v1)

    result = {
        'version': VERSION,
        'event_count': len(keys),
        'comparison_type': 'SAME_MODEL_FAMILY_MEASUREMENT_CONTRACT_SENSITIVITY',
        'not_inter_rater_reliability': True,
        'same_underlying_evidence_batch': True,
        'important_confounds': [
            'rubric/operational definitions changed from behavior-shaped v1 labels to boundary-transition v2 fields',
            'packet/evidence presentation changed between v1 blind bundle and v2 compact R2/R3/R4 packets',
            'prompt wording changed',
            'provider model alias is the same family but provider-side implementation may not be bit-identical across calls',
        ],
    }

    result['v1'] = {
        'labelset_counts': count_sorted(labelset(v1[k]) for k in keys),
        'any_bias_positive_count': sum(bool(v1[k].get('bias_labels')) for k in keys),
        'mechanism_positive_counts': {
            m: sum(m in (v1[k].get('bias_labels') or []) for k in keys)
            for m in ('C', 'P', 'R')
        },
        'authorization_counts': count_sorted(v1[k].get('authorization_judgment') for k in keys),
        'primary_unauthorized_realized_bias_count': sum(
            bool(v1[k].get('bias_labels'))
            and v1[k].get('authorization_judgment') == 'UNAUTHORIZED'
            and bool(v1[k].get('realized_in_baseline'))
            for k in keys
        ),
    }

    result['v2'] = {
        'epistemic_transition_counts': count_sorted(v2[k]['epistemic_transition'] for k in keys),
        'goal_relation_counts': count_sorted(v2[k]['goal_relation'] for k in keys),
        'goal_focus_transition_counts': count_sorted(v2[k]['goal_focus_transition'] for k in keys),
        'retrospective_outcome_counts': count_sorted(v2[k]['local_retrospective_outcome'] for k in keys),
        'authorization_counts': count_sorted(v2[k]['authorization_judgment'] for k in keys),
        'mechanism_presence_counts': {
            m: count_sorted(syn[k][m]['overall_presence'] for k in keys)
            for m in ('C', 'P', 'R')
        },
    }

    result['mechanism_transition'] = {}
    fields = {'C': 'epistemic_transition', 'P': 'goal_relation', 'R': 'local_retrospective_outcome'}
    for mechanism, field in fields.items():
        positives = [k for k in keys if mechanism in (v1[k].get('bias_labels') or [])]
        v1_binary = [mechanism in (v1[k].get('bias_labels') or []) for k in keys]
        v2_binary = [syn[k][mechanism]['overall_presence'] == 'POSITIVE' for k in keys]
        result['mechanism_transition'][mechanism] = {
            'v1_positive_count': len(positives),
            'v1_positive_to_v2_boundary_counts': count_sorted(v2[k][field] for k in positives),
            'v1_positive_to_v2_positive_count': sum(v2_binary[keys.index(k)] for k in positives),
            'binary_raw_agreement': sum(a == b for a, b in zip(v1_binary, v2_binary)) / len(keys),
            'binary_kappa': binary_kappa(v1_binary, v2_binary),
            'zero_positive_v2_marginal': not any(v2_binary),
        }

    result['authorization_transition'] = count_sorted(
        f"{v1[k].get('authorization_judgment')}->{v2[k].get('authorization_judgment')}" for k in keys
    )

    primary = [
        k for k in keys
        if bool(v1[k].get('bias_labels'))
        and v1[k].get('authorization_judgment') == 'UNAUTHORIZED'
        and bool(v1[k].get('realized_in_baseline'))
    ]
    result['v1_primary_to_v2_boundary'] = {
        'event_count': len(primary),
        'v1_labelset_counts': count_sorted(labelset(v1[k]) for k in primary),
        'epistemic_transition_counts': count_sorted(v2[k]['epistemic_transition'] for k in primary),
        'goal_relation_counts': count_sorted(v2[k]['goal_relation'] for k in primary),
        'goal_focus_transition_counts': count_sorted(v2[k]['goal_focus_transition'] for k in primary),
        'retrospective_outcome_counts': count_sorted(v2[k]['local_retrospective_outcome'] for k in primary),
        'v2_authorization_counts': count_sorted(v2[k]['authorization_judgment'] for k in primary),
        'v2_any_mechanism_positive_count': sum(
            any(syn[k][m]['overall_presence'] == 'POSITIVE' for m in ('C', 'P', 'R')) for k in primary
        ),
    }

    result['interpretation'] = [
        'The same DeepSeek model family moves from many v1 positives to zero v2 synthesized positives on the same 70 event population.',
        'This should be interpreted as strong sensitivity to the measurement contract, not as inter-rater disagreement and not as proof that all v1 positives were false.',
        'v1 C positives are reclassified primarily as no epistemic promotion; v1 P positives are reclassified as necessary decomposition/original-goal work; v1 R positives are reclassified as normal non-rework or correction.',
        'Because packet design and prompts also changed, the analysis does not isolate rubric wording as the sole causal factor.',
    ]
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--v1', required=True)
    ap.add_argument('--v2-r2', required=True)
    ap.add_argument('--v2-synthesis', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    result = analyze(load_jsonl(args.v1), load_jsonl(args.v2_r2), load_jsonl(args.v2_synthesis))
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
