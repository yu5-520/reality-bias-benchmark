import copy

from .core import stable_hash


ANCHOR_SELECTION_SCHEMA = 'RB-ANCHOR-SELECTION-v0.1'
RECOVERY_SCHEMA = 'RB-RECOVERY-RECORD-v0.1'


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _hash_record(record):
    material = copy.deepcopy(record)
    material.pop('record_hash', None)
    return stable_hash(material)


def make_anchor_selection_record(
    *,
    selection_id,
    source_evidence_batch_hash,
    source_trace_hash,
    selection_rule,
    candidate_event_refs,
    selected_anchor_ref,
    selected_state_hash,
    jump_candidate_ref=None,
    reviewer_labels_used_for_selection=False,
    branch_outcomes_visible_at_selection=False,
    notes=None,
):
    """Freeze a structural-only branch-anchor decision before branch outcomes exist."""
    _require(selection_id and isinstance(selection_id, str), 'selection_id_required')
    _require(source_evidence_batch_hash and isinstance(source_evidence_batch_hash, str), 'source_evidence_batch_hash_required')
    _require(source_trace_hash and isinstance(source_trace_hash, str), 'source_trace_hash_required')
    _require(isinstance(selection_rule, dict) and selection_rule, 'selection_rule_required')
    _require(isinstance(candidate_event_refs, list) and candidate_event_refs, 'candidate_event_refs_required')
    _require(len(candidate_event_refs) == len(set(candidate_event_refs)), 'candidate_event_refs_must_be_unique')
    _require(selected_anchor_ref and isinstance(selected_anchor_ref, str), 'selected_anchor_ref_required')
    _require(selected_state_hash and isinstance(selected_state_hash, str), 'selected_state_hash_required')
    _require(reviewer_labels_used_for_selection is False, 'reviewer_labels_must_not_drive_anchor_selection')
    _require(branch_outcomes_visible_at_selection is False, 'branch_outcomes_must_not_be_visible_at_selection')

    record = {
        'schema': ANCHOR_SELECTION_SCHEMA,
        'selection_id': selection_id,
        'source_evidence_batch_hash': source_evidence_batch_hash,
        'source_trace_hash': source_trace_hash,
        'selection_rule': copy.deepcopy(selection_rule),
        'selection_rule_hash': stable_hash(selection_rule),
        'candidate_event_refs': list(candidate_event_refs),
        'selected_anchor_ref': selected_anchor_ref,
        'selected_state_hash': selected_state_hash,
        'jump_candidate_ref': jump_candidate_ref,
        'selection_scope': 'STRUCTURAL_ONLY',
        'reviewer_labels_used_for_selection': False,
        'branch_outcomes_visible_at_selection': False,
        'notes': notes,
    }
    record['record_hash'] = _hash_record(record)
    return record


def verify_anchor_selection_record(record):
    _require(isinstance(record, dict), 'anchor_selection_record_must_be_object')
    _require(record.get('schema') == ANCHOR_SELECTION_SCHEMA, 'anchor_selection_schema_invalid')
    _require(record.get('selection_scope') == 'STRUCTURAL_ONLY', 'anchor_selection_scope_invalid')
    _require(record.get('reviewer_labels_used_for_selection') is False, 'anchor_selection_reviewer_contaminated')
    _require(record.get('branch_outcomes_visible_at_selection') is False, 'anchor_selection_outcome_contaminated')
    _require(record.get('selection_rule_hash') == stable_hash(record.get('selection_rule')), 'anchor_selection_rule_hash_mismatch')
    _require(record.get('record_hash') == _hash_record(record), 'anchor_selection_record_hash_mismatch')
    return True


def make_recovery_record(
    *,
    recovery_id,
    parent_trace_hash,
    parent_state_hash,
    recovery_anchor_ref,
    recovery_strategy,
    recovery_status='NOT_EVALUATED',
    parent_branch_id=None,
    jump_ref=None,
    recovery_anchor_distance=None,
    residual_descendant_count=0,
    recurrence_detected=False,
    regeneration_semantic_status='NOT_ADJUDICATED',
    recovery_turns=0,
    recovery_calls=0,
    recovery_tokens=None,
    provenance_reconstruction_status='NOT_EVALUATED',
    notes=None,
):
    _require(recovery_id and isinstance(recovery_id, str), 'recovery_id_required')
    _require(parent_trace_hash and isinstance(parent_trace_hash, str), 'recovery_parent_trace_hash_required')
    _require(parent_state_hash and isinstance(parent_state_hash, str), 'recovery_parent_state_hash_required')
    _require(recovery_anchor_ref and isinstance(recovery_anchor_ref, str), 'recovery_anchor_ref_required')
    _require(recovery_strategy in {
        'FULL_RERUN',
        'CHECKPOINT_RECOVERY',
        'LOCAL_STATE_CORRECTION',
        'VERSIONED_STATE_ADVANCE',
    }, 'recovery_strategy_invalid')
    _require(recovery_status in {'RECOVERED', 'PARTIAL', 'FAILED', 'CENSORED', 'NOT_EVALUATED'}, 'recovery_status_invalid')
    _require(regeneration_semantic_status in {'NOT_ADJUDICATED', 'PRESENT', 'ABSENT', 'NOT_APPLICABLE'}, 'regeneration_semantic_status_invalid')
    _require(provenance_reconstruction_status in {'COMPLETE', 'PARTIAL', 'FAILED', 'NOT_EVALUATED'}, 'provenance_reconstruction_status_invalid')
    _require(int(residual_descendant_count) >= 0, 'residual_descendant_count_invalid')
    _require(int(recovery_turns) >= 0, 'recovery_turns_invalid')
    _require(int(recovery_calls) >= 0, 'recovery_calls_invalid')
    if recovery_anchor_distance is not None:
        _require(int(recovery_anchor_distance) >= 0, 'recovery_anchor_distance_invalid')
    if recovery_tokens is not None:
        _require(float(recovery_tokens) >= 0, 'recovery_tokens_invalid')

    record = {
        'schema': RECOVERY_SCHEMA,
        'recovery_id': recovery_id,
        'parent_branch_id': parent_branch_id,
        'parent_trace_hash': parent_trace_hash,
        'parent_state_hash': parent_state_hash,
        'recovery_anchor_ref': recovery_anchor_ref,
        'jump_ref': jump_ref,
        'recovery_anchor_distance': recovery_anchor_distance,
        'recovery_strategy': recovery_strategy,
        'recovery_status': recovery_status,
        'residual_descendant_count': int(residual_descendant_count),
        'recurrence_detected': bool(recurrence_detected),
        'regeneration_semantic_status': regeneration_semantic_status,
        'recovery_turns': int(recovery_turns),
        'recovery_calls': int(recovery_calls),
        'recovery_tokens': recovery_tokens,
        'provenance_reconstruction_status': provenance_reconstruction_status,
        'provider_internal_state_replayed': False,
        'notes': notes,
    }
    record['record_hash'] = _hash_record(record)
    return record


def verify_recovery_record(record):
    _require(isinstance(record, dict), 'recovery_record_must_be_object')
    _require(record.get('schema') == RECOVERY_SCHEMA, 'recovery_schema_invalid')
    _require(record.get('provider_internal_state_replayed') is False, 'provider_replay_claim_invalid')
    _require(record.get('record_hash') == _hash_record(record), 'recovery_record_hash_mismatch')
    return True
