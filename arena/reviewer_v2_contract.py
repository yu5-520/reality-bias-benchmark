#!/usr/bin/env python3
"""Offline Reviewer-v2 output/expansion contract.

No provider calls occur here. The module validates model/human boundary outputs,
keeps UNCERTAIN explicit, and enforces one allowed-ref expansion request.
"""
import hashlib
import json

VERSION = 'R234-REVIEWER-V2-CONTRACT-v0.1'

R2_ENUMS = {
    'epistemic_transition': {'NO_PROMOTION', 'SUPPORTED_PROMOTION', 'UNSUPPORTED_PROMOTION', 'INHERITED_HIGHER_CERTAINTY', 'UNCERTAIN', 'NOT_APPLICABLE'},
    'goal_relation': {'ORIGINAL_GOAL', 'NECESSARY_DECOMPOSITION', 'AUTHORIZED_EXPANSION', 'UNAUTHORIZED_EXPANSION', 'UNCERTAIN', 'NOT_APPLICABLE'},
    'goal_focus_transition': {'NO_MATERIAL_SHIFT', 'AUTHORIZED_SHIFT', 'UNAUTHORIZED_SHIFT', 'UNCERTAIN', 'NOT_APPLICABLE'},
    'local_retrospective_outcome': {'NOT_REWORK', 'CORRECTION', 'PERSISTENCE', 'REGENERATION_C', 'REGENERATION_P', 'LEGITIMATION_CANDIDATE', 'LEGITIMATION_P_CANDIDATE', 'UNCERTAIN', 'NOT_APPLICABLE'},
    'authorization_judgment': {'AUTHORIZED', 'UNAUTHORIZED', 'UNCERTAIN', 'NOT_APPLICABLE'},
}
R3_ENUMS = {
    'semantic_adoption': {'ADOPTED', 'REJECTED', 'NOT_USED', 'UNCERTAIN', 'NOT_APPLICABLE'},
    'decision_effect': {'EFFECTIVE', 'NO_MATERIAL_EFFECT', 'UNCERTAIN', 'NOT_APPLICABLE'},
    'lineage_outcome': {'CORRECTED_BEFORE_EFFECT', 'PRESERVED_AS_SAME_STATUS', 'CERTAINTY_EROSION_PRECURSOR', 'NEW_UNSUPPORTED_PROMOTION', 'GOAL_SCOPE_EXPANSION_EFFECTIVE', 'GOAL_FOCUS_SHIFT_EFFECTIVE', 'UNCERTAIN', 'NOT_APPLICABLE'},
}
R4_TRI = {'YES', 'NO', 'UNCERTAIN', 'NOT_APPLICABLE'}
R4_ENUMS = {
    'correction': R4_TRI,
    'persistence': R4_TRI,
    'regeneration': R4_TRI,
    'amplification': R4_TRI,
    'laundering': R4_TRI,
    'normalization': R4_TRI,
    'black_hole': {'NO_BLACK_HOLE', 'BLACK_HOLE_CANDIDATE_SUPPORTED', 'UNCERTAIN', 'NOT_APPLICABLE'},
}


def stable_hash(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def parse_json(text):
    raw = text.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        if '```' in raw:
            for piece in raw.split('```'):
                piece = piece.strip()
                if piece.startswith('json'):
                    piece = piece[4:].strip()
                try:
                    return json.loads(piece)
                except Exception:
                    pass
        raise


def _enum(obj, key, allowed):
    value = str(obj.get(key, '')).strip().upper()
    if value not in allowed:
        raise ValueError(f'{key} must be one of {sorted(allowed)}, got {value!r}')
    return value


def _common(obj):
    rationale = str(obj.get('rationale', '')).strip()
    if not rationale:
        raise ValueError('rationale required')
    confidence = obj.get('confidence')
    if isinstance(confidence, str):
        confidence = float(confidence)
    if type(confidence) not in (int, float) or not 0 <= confidence <= 1:
        raise ValueError('confidence must be 0..1')
    uncertainties = obj.get('uncertainties', [])
    evidence_refs = obj.get('evidence_refs', [])
    if not isinstance(uncertainties, list) or not isinstance(evidence_refs, list):
        raise ValueError('uncertainties and evidence_refs must be arrays')
    return {
        'rationale': rationale,
        'confidence': float(confidence),
        'uncertainties': [str(x) for x in uncertainties],
        'evidence_refs': list(dict.fromkeys(str(x) for x in evidence_refs)),
    }


def normalize(layer, obj):
    if not isinstance(obj, dict):
        raise ValueError('reviewer output must be an object')
    status = str(obj.get('review_status', '')).strip().upper()
    if status == 'REQUEST_EXPANSION':
        ref = str(obj.get('context_expansion_ref', '')).strip()
        reason = str(obj.get('reason', '')).strip()
        if not ref or not reason:
            raise ValueError('expansion request requires context_expansion_ref and reason')
        return {'review_status': status, 'context_expansion_ref': ref, 'reason': reason}
    if status != 'FINAL':
        raise ValueError('review_status must be FINAL or REQUEST_EXPANSION')

    out = {'review_status': 'FINAL'}
    if layer == 'R2':
        for key, allowed in R2_ENUMS.items():
            out[key] = _enum(obj, key, allowed)
    elif layer == 'R3':
        for key, allowed in R3_ENUMS.items():
            out[key] = _enum(obj, key, allowed)
        refs = obj.get('penetration_range_refs', [])
        if not isinstance(refs, list):
            raise ValueError('penetration_range_refs must be an array')
        out['penetration_range_refs'] = list(dict.fromkeys(str(x) for x in refs))
    elif layer == 'R4':
        for key, allowed in R4_ENUMS.items():
            out[key] = _enum(obj, key, allowed)
        for key, trigger in (('regeneration_mechanisms', 'regeneration'), ('laundered_mechanisms', 'laundering')):
            values = obj.get(key, [])
            if not isinstance(values, list):
                raise ValueError(f'{key} must be an array')
            values = list(dict.fromkeys(str(x).upper() for x in values))
            if any(x not in {'C', 'P'} for x in values):
                raise ValueError(f'{key} may contain C/P only')
            if out[trigger] == 'YES' and not values:
                raise ValueError(f'{key} must be non-empty when {trigger}=YES')
            out[key] = values
    else:
        raise ValueError(f'unsupported layer: {layer}')
    out.update(_common(obj))
    return out


def validate_expansion_request(packet, normalized, already_expanded=False):
    if normalized.get('review_status') != 'REQUEST_EXPANSION':
        return None
    if already_expanded:
        raise ValueError('only one context expansion is permitted')
    allowed = set((packet.get('context_expansion') or {}).get('allowed_refs') or [])
    ref = normalized['context_expansion_ref']
    if ref not in allowed:
        raise ValueError(f'expansion ref is not allowed by packet: {ref}')
    return ref


def build_ref_index(traces):
    out = {}
    for trace in traces:
        run_id = trace['run_id']
        for event in trace.get('events', []):
            idx = event.get('event_index')
            if isinstance(idx, int):
                out[f'{run_id}:EVENT:{idx:04d}'] = {'record_type': 'event', 'record': event}
        for idx, call in enumerate(trace.get('model_calls', [])):
            out[f'{run_id}:CALL:{idx:04d}'] = {'record_type': 'model_call', 'record': call}
    return out


def get_expansion_record(packet, ref_index, ref, already_expanded=False):
    validate_expansion_request(packet, {'review_status': 'REQUEST_EXPANSION', 'context_expansion_ref': ref}, already_expanded)
    if ref not in ref_index:
        raise ValueError(f'allowed expansion ref not found in frozen trace index: {ref}')
    row = ref_index[ref]
    return {'ref': ref, **row, 'record_hash': stable_hash(row)}
