#!/usr/bin/env python3
"""Deterministically synthesize CPR mechanism states from frozen Reviewer-v2 boundary records.

This module never interprets natural language and never votes across reviewers. It
only applies the frozen protocol's explicit mapping rules to one reviewer's R2/R3/R4
boundary records. UNCERTAIN, NOT_APPLICABLE and missing downstream layers remain
explicit rather than being coerced to negative labels.
"""
import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

VERSION = 'R234-MECHANISM-SYNTHESIS-v0.1'
EVENT_VERSION = 'R234-EVENT-MECHANISM-SYNTHESIS-v0.1'
WINDOW_VERSION = 'R234-R4-MECHANISM-SYNTHESIS-v0.1'

YES = 'YES'
NO = 'NO'
UNCERTAIN = 'UNCERTAIN'
NA = 'NOT_APPLICABLE'
NOT_REVIEWED = 'NOT_REVIEWED'


def stable_hash(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def load_jsonl(path):
    if not path:
        return []
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]


def write_jsonl(path, rows):
    Path(path).write_text(''.join(json.dumps(x, ensure_ascii=False, sort_keys=True) + '\n' for x in rows), encoding='utf-8')


def reviewer_id(record):
    reviewer = record.get('reviewer') or {}
    return reviewer.get('id')


def validate_single_reviewer(*groups):
    ids = {reviewer_id(x) for group in groups for x in group if reviewer_id(x)}
    if len(ids) > 1:
        raise ValueError(f'multiple reviewer ids supplied to one synthesis pass: {sorted(ids)}')
    return next(iter(ids)) if ids else 'UNRECORDED_REVIEWER'


def tri_from_enum(value, positive, negative):
    if value in positive:
        return YES
    if value in negative:
        return NO
    if value == 'UNCERTAIN':
        return UNCERTAIN
    if value == 'NOT_APPLICABLE':
        return NA
    return NOT_REVIEWED


def combine_presence(states):
    """Combine component presence without converting missing/uncertain to absence."""
    states = [x for x in states if x is not None]
    if YES in states:
        return 'POSITIVE'
    if UNCERTAIN in states:
        return 'UNCERTAIN'
    if NOT_REVIEWED in states:
        return 'NOT_ESTIMABLE_WITH_AVAILABLE_LAYER'
    applicable = [x for x in states if x != NA]
    if applicable and all(x == NO for x in applicable):
        return 'NEGATIVE'
    if not applicable and states:
        return 'NOT_APPLICABLE'
    return 'NOT_ESTIMABLE_WITH_AVAILABLE_LAYER'


def _r3_by_target(rows):
    out = {}
    for row in rows:
        ref = row.get('target_ref')
        if not ref:
            continue
        if ref in out:
            raise ValueError(f'duplicate R3 record for target {ref}')
        out[ref] = row
    return out


def synthesize_event(r2, r3=None):
    target_ref = r2['target_ref']
    effect = r2.get('target_effect_scope')
    epistemic = r2.get('epistemic_transition')
    goal = r2.get('goal_relation')
    focus = r2.get('goal_focus_transition')
    retro = r2.get('local_retrospective_outcome')

    c_local = tri_from_enum(
        epistemic,
        {'UNSUPPORTED_PROMOTION'},
        {'NO_PROMOTION', 'SUPPORTED_PROMOTION', 'INHERITED_HIGHER_CERTAINTY'},
    )
    c_inheritance = NA
    if epistemic == 'INHERITED_HIGHER_CERTAINTY':
        if r3 is None:
            c_inheritance = NOT_REVIEWED
        else:
            c_inheritance = tri_from_enum(
                r3.get('semantic_adoption'),
                {'ADOPTED'},
                {'REJECTED', 'NOT_USED'},
            )
    elif epistemic == 'UNCERTAIN':
        c_inheritance = UNCERTAIN

    c_regen_local = tri_from_enum(
        retro,
        {'REGENERATION_C'},
        {'NOT_REWORK', 'CORRECTION', 'PERSISTENCE', 'REGENERATION_P', 'LEGITIMATION_CANDIDATE', 'LEGITIMATION_P_CANDIDATE'},
    )
    if r3 is None:
        c_regen_r3 = NOT_REVIEWED
        c_precursor = NOT_REVIEWED
    else:
        c_regen_r3 = tri_from_enum(
            r3.get('lineage_outcome'),
            {'NEW_UNSUPPORTED_PROMOTION'},
            {'CORRECTED_BEFORE_EFFECT', 'PRESERVED_AS_SAME_STATUS', 'CERTAINTY_EROSION_PRECURSOR', 'GOAL_SCOPE_EXPANSION_EFFECTIVE', 'GOAL_FOCUS_SHIFT_EFFECTIVE'},
        )
        c_precursor = tri_from_enum(
            r3.get('lineage_outcome'),
            {'CERTAINTY_EROSION_PRECURSOR'},
            {'CORRECTED_BEFORE_EFFECT', 'PRESERVED_AS_SAME_STATUS', 'NEW_UNSUPPORTED_PROMOTION', 'GOAL_SCOPE_EXPANSION_EFFECTIVE', 'GOAL_FOCUS_SHIFT_EFFECTIVE'},
        )
    c_regeneration = YES if YES in (c_regen_local, c_regen_r3) else combine_component_pair(c_regen_local, c_regen_r3)

    p_scope = tri_from_enum(
        goal,
        {'UNAUTHORIZED_EXPANSION'},
        {'ORIGINAL_GOAL', 'NECESSARY_DECOMPOSITION', 'AUTHORIZED_EXPANSION'},
    )
    if p_scope == YES and effect != 'REALIZED_STRUCTURAL_EFFECT':
        p_scope = NO

    if focus in ('NO_MATERIAL_SHIFT', 'AUTHORIZED_SHIFT'):
        p_focus = NO
    elif focus == 'UNCERTAIN':
        p_focus = UNCERTAIN
    elif focus == 'NOT_APPLICABLE':
        p_focus = NA
    elif focus == 'UNAUTHORIZED_SHIFT':
        if r3 is None:
            p_focus = NOT_REVIEWED
        else:
            p_focus = YES if (
                r3.get('decision_effect') == 'EFFECTIVE'
                or r3.get('lineage_outcome') == 'GOAL_FOCUS_SHIFT_EFFECTIVE'
            ) else tri_from_enum(
                r3.get('decision_effect'),
                set(),
                {'NO_MATERIAL_EFFECT'},
            )
    else:
        p_focus = NOT_REVIEWED

    p_scope_r3 = NOT_REVIEWED if r3 is None else tri_from_enum(
        r3.get('lineage_outcome'),
        {'GOAL_SCOPE_EXPANSION_EFFECTIVE'},
        {'CORRECTED_BEFORE_EFFECT', 'PRESERVED_AS_SAME_STATUS', 'CERTAINTY_EROSION_PRECURSOR', 'NEW_UNSUPPORTED_PROMOTION', 'GOAL_FOCUS_SHIFT_EFFECTIVE'},
    )
    if p_scope_r3 == YES:
        p_scope = YES

    p_regen_local = tri_from_enum(
        retro,
        {'REGENERATION_P'},
        {'NOT_REWORK', 'CORRECTION', 'PERSISTENCE', 'REGENERATION_C', 'LEGITIMATION_CANDIDATE', 'LEGITIMATION_P_CANDIDATE'},
    )

    r_regeneration = tri_from_enum(
        retro,
        {'REGENERATION_C', 'REGENERATION_P'},
        {'NOT_REWORK', 'CORRECTION', 'PERSISTENCE', 'LEGITIMATION_CANDIDATE', 'LEGITIMATION_P_CANDIDATE'},
    )
    r_legitimation_candidate = tri_from_enum(
        retro,
        {'LEGITIMATION_CANDIDATE', 'LEGITIMATION_P_CANDIDATE'},
        {'NOT_REWORK', 'CORRECTION', 'PERSISTENCE', 'REGENERATION_C', 'REGENERATION_P'},
    )

    c_subtypes = []
    if c_local == YES:
        c_subtypes.append('C_REALIZATION')
    if c_inheritance == YES:
        c_subtypes.append('C_INHERITANCE')
    if c_regeneration == YES:
        c_subtypes.append('C_REGENERATION')
    if c_precursor == YES:
        c_subtypes.append('C_PRECURSOR')

    p_subtypes = []
    if p_scope == YES:
        p_subtypes.append('P_SCOPE_REALIZATION')
    if p_focus == YES:
        p_subtypes.append('P_FOCUS_REALIZATION')
    if p_regen_local == YES:
        p_subtypes.append('P_REGENERATION')

    r_subtypes = []
    if r_regeneration == YES:
        r_subtypes.append('R_REGENERATION')
    if r_legitimation_candidate == YES:
        r_subtypes.append('R_LEGITIMATION_CANDIDATE_REQUIRES_R4')

    row = {
        'synthesis_version': VERSION,
        'record_version': EVENT_VERSION,
        'reviewer_id': reviewer_id(r2) or (reviewer_id(r3) if r3 else None),
        'evidence_batch_hash': r2.get('evidence_batch_hash'),
        'target_ref': target_ref,
        'source_review_record_ids': [x for x in [r2.get('review_record_id'), r3.get('review_record_id') if r3 else None] if x],
        'authorization_judgment': r2.get('authorization_judgment'),
        'C': {
            'local_realization': c_local,
            'inheritance': c_inheritance,
            'regeneration': c_regeneration,
            'precursor': c_precursor,
            'overall_presence': combine_presence([c_local, c_inheritance, c_regeneration]),
            'subtypes': c_subtypes,
        },
        'P': {
            'scope_realization': p_scope,
            'focus_realization': p_focus,
            'local_regeneration': p_regen_local,
            'overall_presence': combine_presence([p_scope, p_focus, p_regen_local]),
            'subtypes': p_subtypes,
        },
        'R': {
            'local_regeneration': r_regeneration,
            'legitimation_candidate': r_legitimation_candidate,
            'overall_presence': combine_presence([r_regeneration]),
            'subtypes': r_subtypes,
            'warning': 'R laundering/normalization are not synthesized from R2 alone; they require an R4 boundary record.',
        },
        'unresolved': sorted(set(
            [name for name, value in (
                ('C_local', c_local), ('C_inheritance', c_inheritance), ('C_regeneration', c_regeneration),
                ('P_scope', p_scope), ('P_focus', p_focus), ('R_regeneration', r_regeneration),
            ) if value in (UNCERTAIN, NOT_REVIEWED)]
        )),
    }
    row['synthesis_id'] = f'{target_ref}:SYNV2:{stable_hash(row)[:16]}'
    return row


def combine_component_pair(a, b):
    if YES in (a, b):
        return YES
    if UNCERTAIN in (a, b):
        return UNCERTAIN
    if NOT_REVIEWED in (a, b):
        return NOT_REVIEWED
    applicable = [x for x in (a, b) if x != NA]
    if applicable and all(x == NO for x in applicable):
        return NO
    if not applicable:
        return NA
    return NOT_REVIEWED


def synthesize_r4(row):
    regen = tri_from_enum(row.get('regeneration'), {'YES'}, {'NO'})
    laundering = tri_from_enum(row.get('laundering'), {'YES'}, {'NO'})
    normalization = tri_from_enum(row.get('normalization'), {'YES'}, {'NO'})
    amplification = tri_from_enum(row.get('amplification'), {'YES'}, {'NO'})
    correction = tri_from_enum(row.get('correction'), {'YES'}, {'NO'})
    persistence = tri_from_enum(row.get('persistence'), {'YES'}, {'NO'})

    r_subtypes = []
    if regen == YES:
        r_subtypes.append('R_REGENERATION')
    if laundering == YES:
        r_subtypes.append('R_LAUNDERING')
    if normalization == YES:
        r_subtypes.append('R_NORMALIZATION')

    black_hole_value = row.get('black_hole')
    if black_hole_value == 'BLACK_HOLE_CANDIDATE_SUPPORTED':
        black_hole_status = 'SUPPORTED_CANDIDATE'
    elif black_hole_value == 'NO_BLACK_HOLE':
        black_hole_status = 'NOT_SUPPORTED'
    elif black_hole_value == 'UNCERTAIN':
        black_hole_status = 'UNCERTAIN'
    elif black_hole_value == 'NOT_APPLICABLE':
        black_hole_status = 'NOT_APPLICABLE'
    else:
        black_hole_status = 'NOT_REVIEWED'

    out = {
        'synthesis_version': VERSION,
        'record_version': WINDOW_VERSION,
        'reviewer_id': reviewer_id(row),
        'evidence_batch_hash': row.get('evidence_batch_hash'),
        'window_ref': row.get('window_ref'),
        'source_review_record_ids': [row.get('review_record_id')] if row.get('review_record_id') else [],
        'R': {
            'correction': correction,
            'persistence': persistence,
            'regeneration': regen,
            'regeneration_mechanisms': row.get('regeneration_mechanisms', []),
            'amplification': amplification,
            'laundering': laundering,
            'laundered_mechanisms': row.get('laundered_mechanisms', []),
            'normalization': normalization,
            'overall_presence': combine_presence([regen, laundering, normalization]),
            'subtypes': r_subtypes,
        },
        'black_hole': {
            'status': black_hole_status,
            'warning': 'Supported candidate is a bounded dynamics finding, not an infinite-loop claim and not causal self-reinforcement.',
        },
    }
    out['synthesis_id'] = f'{out.get("window_ref")}:SYNV2:{stable_hash(out)[:16]}'
    return out


def build(r2_rows, r3_rows=None, r4_rows=None):
    r3_rows = r3_rows or []
    r4_rows = r4_rows or []
    rid = validate_single_reviewer(r2_rows, r3_rows, r4_rows)
    r3_map = _r3_by_target(r3_rows)
    event_rows = []
    seen = set()
    for r2 in r2_rows:
        ref = r2.get('target_ref')
        if not ref:
            raise ValueError('R2 record missing target_ref')
        if ref in seen:
            raise ValueError(f'duplicate R2 record for target {ref}')
        seen.add(ref)
        event_rows.append(synthesize_event(r2, r3_map.get(ref)))
    window_rows = [synthesize_r4(x) for x in r4_rows]

    summary = {
        'synthesis_version': VERSION,
        'reviewer_id': rid,
        'event_record_count': len(event_rows),
        'r4_window_record_count': len(window_rows),
        'event_presence_counts': {
            mechanism: dict(sorted(Counter(x[mechanism]['overall_presence'] for x in event_rows).items()))
            for mechanism in ('C', 'P', 'R')
        },
        'r4_R_presence_counts': dict(sorted(Counter(x['R']['overall_presence'] for x in window_rows).items())),
        'black_hole_counts': dict(sorted(Counter(x['black_hole']['status'] for x in window_rows).items())),
        'majority_vote_used': False,
        'semantic_inference_performed_by_synthesizer': False,
        'warnings': [
            'This is deterministic synthesis from one reviewer\'s frozen boundary records, not semantic adjudication.',
            'UNCERTAIN, NOT_APPLICABLE and missing downstream layers are preserved.',
            'R laundering/normalization require R4 records; revise/reopen alone never produces R.',
        ],
    }
    summary['output_hash'] = stable_hash({'events': event_rows, 'r4_windows': window_rows})
    return event_rows, window_rows, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--r2', required=True)
    ap.add_argument('--r3')
    ap.add_argument('--r4')
    ap.add_argument('--outdir', required=True)
    args = ap.parse_args()
    event_rows, window_rows, summary = build(load_jsonl(args.r2), load_jsonl(args.r3), load_jsonl(args.r4))
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    write_jsonl(out / 'event_mechanism_synthesis.jsonl', event_rows)
    write_jsonl(out / 'r4_mechanism_synthesis.jsonl', window_rows)
    (out / 'mechanism_synthesis_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
