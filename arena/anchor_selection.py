import copy

from .branch_protocol import make_anchor_selection_record, verify_anchor_selection_record
from .core import stable_hash
from .experimental_control import verify_state_snapshot
from .measurement_v2 import build_r2_candidate_index


RULE_SCHEMAS = {
    'RB-R5R6-ANCHOR-RULE-v0.1',
    'RB-R5R6-ANCHOR-RULE-v0.2',
}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_anchor_rule(rule):
    _require(isinstance(rule, dict), 'anchor_rule_must_be_object')
    _require(rule.get('schema') in RULE_SCHEMAS, 'anchor_rule_schema_invalid')
    _require(rule.get('selection_scope') == 'STRUCTURAL_ONLY', 'anchor_rule_scope_invalid')
    _require(rule.get('candidate_type'), 'anchor_rule_candidate_type_required')
    _require(rule.get('action_type'), 'anchor_rule_action_type_required')
    _require(rule.get('anchor_position') == 'AFTER_CANDIDATE_TURN', 'anchor_rule_position_invalid')
    _require(rule.get('tie_break') == 'LOWEST_EVENT_INDEX', 'anchor_rule_tie_break_invalid')
    _require(rule.get('semantic_reviewer_labels_allowed') is False, 'anchor_rule_semantic_contamination')
    _require(rule.get('branch_outcomes_allowed_during_selection') is False, 'anchor_rule_outcome_contamination')
    if rule.get('schema') == 'RB-R5R6-ANCHOR-RULE-v0.2':
        _require(rule.get('require_pending_queue') is True, 'anchor_rule_v02_pending_queue_required')
    return True


def _snapshot_index(snapshots):
    index = {}
    for snapshot in snapshots:
        verify_state_snapshot(snapshot)
        ref = snapshot.get('anchor_ref')
        _require(ref and ref not in index, 'duplicate_or_missing_snapshot_anchor_ref')
        index[ref] = snapshot
    return index


def eligible_anchor_candidates(trace, snapshots, rule, *, evidence_hash=None):
    validate_anchor_rule(rule)
    snap_index = _snapshot_index(snapshots)
    candidates = build_r2_candidate_index(trace, batch_hash=evidence_hash)
    eligible = []
    required_type = rule['candidate_type']
    required_action = rule['action_type']

    for candidate in candidates:
        if candidate.get('action_type') != required_action:
            continue
        if required_type not in (candidate.get('candidate_types') or []):
            continue
        if rule.get('realized_required') and candidate.get('realized_in_baseline') is not True:
            continue
        turn = candidate.get('turn')
        if not isinstance(turn, int):
            continue
        anchor_ref = f'after_turn:{turn}'
        snapshot = snap_index.get(anchor_ref)
        if snapshot is None:
            continue
        if rule.get('require_nonterminal_snapshot') and snapshot.get('terminated'):
            continue
        if rule.get('require_pending_queue') and not snapshot.get('queue'):
            continue
        eligible.append({
            'candidate': copy.deepcopy(candidate),
            'candidate_event_ref': candidate.get('event_ref'),
            'candidate_event_index': candidate.get('event_index'),
            'anchor_ref': anchor_ref,
            'snapshot': copy.deepcopy(snapshot),
            'state_hash': snapshot.get('state_hash'),
        })

    eligible.sort(key=lambda row: (
        row['candidate_event_index'] if isinstance(row.get('candidate_event_index'), int) else 10**12,
        row.get('candidate_event_ref') or '',
    ))
    return eligible


def select_anchor(trace, snapshots, rule, *, evidence_hash=None, selection_id=None):
    """Select one replayable structural anchor without semantic labels or branch outcomes."""
    validate_anchor_rule(rule)
    trace_hash = stable_hash(trace)
    evidence_hash = evidence_hash or stable_hash({
        'trace_hash': trace_hash,
        'snapshot_hashes': [snapshot.get('state_hash') for snapshot in snapshots],
        'rule_hash': stable_hash(rule),
    })
    eligible = eligible_anchor_candidates(trace, snapshots, rule, evidence_hash=evidence_hash)
    if not eligible:
        return {
            'selection_status': 'NO_ELIGIBLE_STRUCTURAL_ANCHOR',
            'trace_hash': trace_hash,
            'evidence_hash': evidence_hash,
            'rule_hash': stable_hash(rule),
            'eligible_count': 0,
            'selection_record': None,
            'selected_candidate': None,
            'selected_snapshot': None,
        }

    selected = eligible[0]
    record = make_anchor_selection_record(
        selection_id=selection_id or f"{trace.get('run_id', 'UNKNOWN')}:R5R6:ANCHOR:{stable_hash({'trace': trace_hash, 'rule': rule})[:16]}",
        source_evidence_batch_hash=evidence_hash,
        source_trace_hash=trace_hash,
        selection_rule=copy.deepcopy(rule),
        candidate_event_refs=[row['candidate_event_ref'] for row in eligible],
        selected_anchor_ref=selected['anchor_ref'],
        selected_state_hash=selected['state_hash'],
        jump_candidate_ref=selected['candidate_event_ref'],
        reviewer_labels_used_for_selection=False,
        branch_outcomes_visible_at_selection=False,
        notes=(
            'Selected by a frozen structural-only rule. Candidate eligibility establishes replayability and, where required, pending continuation work; '
            'it does not establish semantic C/P/R, unauthorized promotion, Jump truth, Authority Penetration, or causal importance.'
        ),
    )
    verify_anchor_selection_record(record)
    return {
        'selection_status': 'ANCHOR_SELECTED',
        'trace_hash': trace_hash,
        'evidence_hash': evidence_hash,
        'rule_hash': stable_hash(rule),
        'eligible_count': len(eligible),
        'eligible_candidate_event_refs': [row['candidate_event_ref'] for row in eligible],
        'selection_record': record,
        'selected_candidate': selected['candidate'],
        'selected_snapshot': selected['snapshot'],
    }
