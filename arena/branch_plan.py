#!/usr/bin/env python3
import argparse
import copy
import json
import os
from pathlib import Path

from .branch_protocol import verify_anchor_selection_record
from .core import stable_hash
from .experimental_control import (
    apply_state_intervention,
    make_branch_manifest,
    verify_branch_manifest,
    verify_state_snapshot,
)
from .io_utils import load_json, load_jsonl, write_jsonl


PLAN_SCHEMA = 'RB-R5R6-BRANCH-EXECUTION-PLAN-v0.1'
CONDITIONS = ('CONTROL_CONTINUATION', 'STATUS_DOWNGRADE_INTERVENTION')


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _hash_without(record, key):
    material = copy.deepcopy(record)
    material.pop(key, None)
    return stable_hash(material)


def _selected_trace(selection_package, traces):
    expected_hash = selection_package.get('trace_hash')
    _require(expected_hash, 'selection_package_trace_hash_required')
    matches = [trace for trace in traces if stable_hash(trace) == expected_hash]
    _require(len(matches) == 1, 'selection_package_trace_must_match_exactly_one_baseline_trace')
    return matches[0]


def validate_phase_a_selection(selection_package, baseline_trace):
    _require(isinstance(selection_package, dict), 'selection_package_must_be_object')
    _require(selection_package.get('selection_status') == 'ANCHOR_SELECTED', 'phase_b_requires_anchor_selected')
    record = selection_package.get('selection_record')
    selected_candidate = selection_package.get('selected_candidate')
    parent_snapshot = selection_package.get('selected_snapshot')
    _require(isinstance(record, dict), 'selection_record_required')
    _require(isinstance(selected_candidate, dict), 'selected_candidate_required')
    _require(isinstance(parent_snapshot, dict), 'selected_snapshot_required')
    verify_anchor_selection_record(record)
    verify_state_snapshot(parent_snapshot)

    trace_hash = stable_hash(baseline_trace)
    _require(selection_package.get('trace_hash') == trace_hash, 'baseline_trace_hash_mismatch')
    _require(record.get('source_trace_hash') == trace_hash, 'selection_record_source_trace_hash_mismatch')
    _require(record.get('selected_state_hash') == parent_snapshot.get('state_hash'), 'selected_state_hash_mismatch')
    _require(record.get('selected_anchor_ref') == parent_snapshot.get('anchor_ref'), 'selected_anchor_ref_mismatch')
    _require(record.get('jump_candidate_ref') == selected_candidate.get('event_ref'), 'selected_candidate_ref_mismatch')
    _require(record.get('reviewer_labels_used_for_selection') is False, 'semantic_anchor_selection_forbidden')
    _require(record.get('branch_outcomes_visible_at_selection') is False, 'outcome_aware_anchor_selection_forbidden')
    _require(selected_candidate.get('action_type') == 'write_state', 'phase_b_v01_requires_state_write_candidate')
    _require(
        'HIGH_CERTAINTY_STATE_WRITE_CANDIDATE' in (selected_candidate.get('candidate_types') or []),
        'phase_b_v01_requires_high_certainty_write_candidate',
    )
    _require(selected_candidate.get('realized_in_baseline') is True, 'phase_b_v01_requires_realized_candidate')
    _require(parent_snapshot.get('terminated') is False, 'phase_b_parent_snapshot_must_be_nonterminal')

    facts = selected_candidate.get('structural_facts') or {}
    state_key = facts.get('state_key')
    status_after = facts.get('status_after')
    _require(state_key, 'selected_candidate_state_key_required')
    _require(status_after in ('fact', 'confirmed', 'verified', 'executed'), 'selected_candidate_high_certainty_status_required')
    parent_meta = (parent_snapshot.get('shared_state_metadata') or {}).get(state_key) or {}
    _require(parent_meta.get('status') == status_after, 'parent_snapshot_status_does_not_match_selected_candidate')
    return True


def _baseline_binding(trace, key, fallback=None):
    value = trace.get(key, fallback)
    _require(value is not None, f'baseline_trace_binding_required:{key}')
    return value


def _verify_single_status_intervention(parent, changed, *, state_key, from_status, to_status):
    """Prove the branch-visible runtime delta is exactly one metadata status field.

    `state_hash` is excluded because it is derived. No anchor/provenance field may
    change here; branch identity belongs in the branch manifest rather than the
    replayed runtime snapshot.
    """
    verify_state_snapshot(parent)
    verify_state_snapshot(changed)
    p = copy.deepcopy(parent)
    c = copy.deepcopy(changed)
    p.pop('state_hash', None)
    c.pop('state_hash', None)
    p_meta = p.pop('shared_state_metadata', None)
    c_meta = c.pop('shared_state_metadata', None)
    _require(p == c, 'intervention_changed_non_metadata_runtime_state')
    _require(isinstance(p_meta, dict) and isinstance(c_meta, dict), 'intervention_metadata_missing')
    _require(set(p_meta) == set(c_meta), 'intervention_changed_metadata_keyset')
    for key in p_meta:
        left = copy.deepcopy(p_meta[key])
        right = copy.deepcopy(c_meta[key])
        if key != state_key:
            _require(left == right, 'intervention_changed_unrelated_metadata:' + str(key))
            continue
        _require(isinstance(left, dict) and isinstance(right, dict), 'intervention_target_metadata_invalid')
        _require(left.get('status') == from_status, 'intervention_source_status_mismatch')
        _require(right.get('status') == to_status, 'intervention_target_status_mismatch')
        left.pop('status', None)
        right.pop('status', None)
        _require(left == right, 'intervention_changed_target_metadata_beyond_status')
    return True


def build_branch_plan(
    selection_package,
    baseline_trace,
    *,
    replicates,
    target_status='provisional',
    branch_code_sha=None,
):
    if type(replicates) is not int or replicates < 1:
        raise ValueError('positive integer replicates required')
    validate_phase_a_selection(selection_package, baseline_trace)
    _require(target_status == 'provisional', 'phase_b_v01_target_status_must_be_provisional')
    branch_code_sha = branch_code_sha or os.environ.get('GITHUB_SHA') or 'LOCAL_OR_UNRECORDED'

    record = selection_package['selection_record']
    candidate = selection_package['selected_candidate']
    parent_snapshot = copy.deepcopy(selection_package['selected_snapshot'])
    facts = candidate.get('structural_facts') or {}
    state_key = facts['state_key']
    original_status = facts['status_after']
    intervention_spec = {
        'type': 'set_shared_state_status',
        'key': state_key,
        'from_status': original_status,
        'status': target_status,
        'intervention_family': 'EPISTEMIC_STATUS_DOWNGRADE_TO_PROVISIONAL',
        'scope': 'ONE_BRANCH_VISIBLE_STATE_STATUS_FIELD_ONLY',
    }
    intervention_start = apply_state_intervention(parent_snapshot, intervention_spec)
    _require(parent_snapshot['state_hash'] != intervention_start['state_hash'], 'intervention_must_change_branch_start_state')
    _verify_single_status_intervention(
        parent_snapshot,
        intervention_start,
        state_key=state_key,
        from_status=original_status,
        to_status=target_status,
    )

    source_trace_hash = stable_hash(baseline_trace)
    common_identity = {
        'baseline_run_id': baseline_trace.get('run_id'),
        'source_trace_hash': source_trace_hash,
        'source_evidence_hash': selection_package.get('evidence_hash'),
        'selection_record_hash': record.get('record_hash'),
        'selected_candidate_id': candidate.get('candidate_id'),
        'selected_candidate_event_ref': candidate.get('event_ref'),
        'parent_state_hash': parent_snapshot['state_hash'],
        'parent_anchor_ref': parent_snapshot.get('anchor_ref'),
        'state_key': state_key,
        'original_status': original_status,
        'target_status': target_status,
    }
    model_identity = {
        'provider': _baseline_binding(baseline_trace, 'provider', None),
        'model_config_path': _baseline_binding(baseline_trace, 'model_config_path', None),
        'model_config_version': baseline_trace.get('model_config_version'),
        'model_config_hash': _baseline_binding(baseline_trace, 'model_config_hash', None),
    }
    config_identity = {
        'arena_config_path': _baseline_binding(baseline_trace, 'arena_config_path', None),
        'arena_config_version': baseline_trace.get('arena_config_version'),
        'arena_config_hash': _baseline_binding(baseline_trace, 'arena_config_hash', None),
        'domain_id': _baseline_binding(baseline_trace, 'domain_id', None),
        'domain_hash': _baseline_binding(baseline_trace, 'domain_hash', None),
        'task_hash': _baseline_binding(baseline_trace, 'task_hash', None),
        'agent_registry_hash': _baseline_binding(baseline_trace, 'agent_registry_hash', None),
        'anchor_rule_path': baseline_trace.get('anchor_rule_path'),
        'anchor_rule_hash': baseline_trace.get('anchor_rule_hash'),
    }
    code_identity = {
        'source_baseline_commit': baseline_trace.get('code_commit_sha'),
        'branch_execution_commit': branch_code_sha,
    }

    rows = []
    manifests = []
    for replicate in range(1, replicates + 1):
        pair_id = f"{baseline_trace['run_id']}:branch-pair:{replicate:04d}"
        order = CONDITIONS if replicate % 2 else tuple(reversed(CONDITIONS))
        order_pattern = 'CONTROL_FIRST' if replicate % 2 else 'INTERVENTION_FIRST'
        for execution_order, condition in enumerate(order, 1):
            if condition == 'CONTROL_CONTINUATION':
                branch_start = parent_snapshot
                spec = {
                    'type': 'no_intervention_control',
                    'scope': 'UNCHANGED_FROZEN_PARENT_STATE',
                }
            else:
                branch_start = intervention_start
                spec = intervention_spec
            branch_id = f"{pair_id}:{condition.lower()}"
            manifest = make_branch_manifest(
                branch_id=branch_id,
                parent_trace_hash=source_trace_hash,
                parent_snapshot=parent_snapshot,
                branch_start_snapshot=branch_start,
                intervention_spec=spec,
                replicate_index=replicate,
                model_identity=model_identity,
                config_identity=config_identity,
                code_identity=code_identity,
            )
            verify_branch_manifest(manifest, parent_snapshot, branch_start)
            manifests.append(manifest)
            rows.append({
                'run_id': branch_id,
                'pair_id': pair_id,
                'replicate_index': replicate,
                'logical_seed': replicate,
                'execution_order': execution_order,
                'pair_order_pattern': order_pattern,
                'condition_id': condition,
                'branch_id': branch_id,
                'branch_hash': manifest['branch_hash'],
                'parent_trace_hash': source_trace_hash,
                'parent_state_hash': parent_snapshot['state_hash'],
                'branch_start_state_hash': branch_start['state_hash'],
                'intervention_hash': manifest['intervention_hash'],
                'domain_id': baseline_trace['domain_id'],
                'domain_hash': baseline_trace['domain_hash'],
                'task_hash': baseline_trace['task_hash'],
                'agent_pool_hash': baseline_trace['agent_registry_hash'],
                'arena_config_path': baseline_trace['arena_config_path'],
                'arena_config_version': baseline_trace.get('arena_config_version'),
                'arena_config_hash': baseline_trace['arena_config_hash'],
                'model_config_path': baseline_trace['model_config_path'],
                'model_config_version': baseline_trace.get('model_config_version'),
                'model_config_hash': baseline_trace['model_config_hash'],
                'model_provider': baseline_trace['provider'],
                'anchor_rule_path': baseline_trace.get('anchor_rule_path'),
                'anchor_rule_hash': baseline_trace.get('anchor_rule_hash'),
                'source_selection_record_hash': record['record_hash'],
                'source_baseline_code_commit_sha': baseline_trace.get('code_commit_sha'),
                'branch_execution_code_commit_sha': branch_code_sha,
                'scientific_status': 'CANDIDATE_UNTIL_EXPLICIT_REAL_RUN_FREEZE_AND_API_AUTHORIZATION',
                'automatic_paid_evaluator': False,
                'semantic_review': 'DEFERRED_APPEND_ONLY',
            })

    plan = {
        'schema': PLAN_SCHEMA,
        'version': 'R5R6-BRANCH-PLAN-v0.1',
        'phase': 'BRANCH_CONTINUATION_CANDIDATE',
        'scientific_status': 'CANDIDATE_UNTIL_EXPLICIT_REAL_RUN_FREEZE_AND_API_AUTHORIZATION',
        'common_identity': common_identity,
        'model_identity': model_identity,
        'config_identity': config_identity,
        'code_identity': code_identity,
        'replicates': replicates,
        'condition_ids': list(CONDITIONS),
        'execution_order_policy': 'ODD_CONTROL_FIRST_EVEN_INTERVENTION_FIRST',
        'intervention_spec': copy.deepcopy(intervention_spec),
        'parent_snapshot_hash': parent_snapshot['state_hash'],
        'intervention_start_snapshot_hash': intervention_start['state_hash'],
        'branch_row_count': len(rows),
        'branch_manifest_hashes': [manifest['branch_hash'] for manifest in manifests],
        'automatic_paid_evaluator': False,
        'semantic_review': 'DEFERRED_APPEND_ONLY',
        'authorization_status': 'NOT_AUTHORIZED',
        'warning': (
            'Prepared from frozen Phase-A evidence. This plan does not authorize provider calls and does not establish that the selected structural candidate is semantic C/Jump/penetration.'
        ),
    }
    plan['plan_hash'] = _hash_without(plan, 'plan_hash')
    return {
        'plan': plan,
        'parent_snapshot': parent_snapshot,
        'intervention_start_snapshot': intervention_start,
        'branch_rows': rows,
        'branch_manifests': manifests,
    }


def verify_branch_plan(bundle):
    _require(isinstance(bundle, dict), 'branch_plan_bundle_must_be_object')
    plan = bundle.get('plan') or {}
    parent = bundle.get('parent_snapshot')
    intervention = bundle.get('intervention_start_snapshot')
    rows = bundle.get('branch_rows') or []
    manifests = bundle.get('branch_manifests') or []
    _require(plan.get('schema') == PLAN_SCHEMA, 'branch_plan_schema_invalid')
    _require(plan.get('authorization_status') == 'NOT_AUTHORIZED', 'branch_plan_must_not_self_authorize')
    _require(plan.get('automatic_paid_evaluator') is False, 'branch_plan_paid_evaluator_must_be_false')
    _require(plan.get('plan_hash') == _hash_without(plan, 'plan_hash'), 'branch_plan_hash_mismatch')
    verify_state_snapshot(parent)
    verify_state_snapshot(intervention)
    _require(plan.get('parent_snapshot_hash') == parent.get('state_hash'), 'branch_plan_parent_snapshot_hash_mismatch')
    _require(plan.get('intervention_start_snapshot_hash') == intervention.get('state_hash'), 'branch_plan_intervention_snapshot_hash_mismatch')
    _require(parent.get('state_hash') != intervention.get('state_hash'), 'branch_plan_intervention_state_must_differ')
    spec = plan.get('intervention_spec') or {}
    _verify_single_status_intervention(
        parent,
        intervention,
        state_key=spec.get('key'),
        from_status=spec.get('from_status'),
        to_status=spec.get('status'),
    )
    _require(len(rows) == len(manifests) == plan.get('branch_row_count'), 'branch_plan_row_count_mismatch')
    _require(len(rows) == int(plan.get('replicates')) * 2, 'branch_plan_expected_two_conditions_per_replicate')

    by_hash = {manifest['branch_hash']: manifest for manifest in manifests}
    pairs = {}
    for row in rows:
        manifest = by_hash.get(row.get('branch_hash'))
        _require(manifest is not None, 'branch_plan_manifest_missing_for_row')
        start = parent if row['condition_id'] == 'CONTROL_CONTINUATION' else intervention
        verify_branch_manifest(manifest, parent, start)
        _require(row['parent_state_hash'] == parent['state_hash'], 'branch_plan_row_parent_hash_mismatch')
        _require(row['branch_start_state_hash'] == start['state_hash'], 'branch_plan_row_start_hash_mismatch')
        _require(row.get('logical_seed') == row.get('replicate_index'), 'branch_plan_pair_logical_seed_mismatch')
        _require(
            row.get('branch_execution_code_commit_sha') == (plan.get('code_identity') or {}).get('branch_execution_commit'),
            'branch_plan_execution_code_binding_mismatch',
        )
        pairs.setdefault(row['pair_id'], []).append(row)
    for pair_id, pair_rows in pairs.items():
        _require(len(pair_rows) == 2, 'branch_plan_pair_must_have_two_rows')
        _require({row['condition_id'] for row in pair_rows} == set(CONDITIONS), 'branch_plan_pair_conditions_invalid')
        _require(len({row['parent_state_hash'] for row in pair_rows}) == 1, 'branch_plan_pair_parent_hash_mismatch')
        _require(len({row['logical_seed'] for row in pair_rows}) == 1, 'branch_plan_pair_seed_mismatch')
        _require(sorted(row['execution_order'] for row in pair_rows) == [1, 2], 'branch_plan_pair_execution_order_invalid')
    return True


def prepare_from_files(*, selection_package_path, baseline_traces_path, replicates, outdir, branch_code_sha=None):
    selection = load_json(selection_package_path)
    traces = load_jsonl(baseline_traces_path)
    baseline = _selected_trace(selection, traces)
    bundle = build_branch_plan(
        selection,
        baseline,
        replicates=replicates,
        branch_code_sha=branch_code_sha,
    )
    verify_branch_plan(bundle)

    out = Path(outdir)
    if out.exists():
        raise ValueError('refusing_to_overwrite_branch_plan_outdir')
    out.mkdir(parents=True, exist_ok=False)
    (out / 'branch_plan.json').write_text(json.dumps(bundle['plan'], ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    (out / 'parent_snapshot.json').write_text(json.dumps(bundle['parent_snapshot'], ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    (out / 'intervention_start_snapshot.json').write_text(json.dumps(bundle['intervention_start_snapshot'], ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    write_jsonl(out / 'branch_execution_manifest.jsonl', bundle['branch_rows'])
    write_jsonl(out / 'branch_manifests.jsonl', bundle['branch_manifests'])
    return bundle


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--selection-package', required=True)
    ap.add_argument('--baseline-traces', required=True)
    ap.add_argument('--replicates', required=True, type=int)
    ap.add_argument('--branch-code-sha')
    ap.add_argument('--outdir', required=True)
    args = ap.parse_args()
    bundle = prepare_from_files(
        selection_package_path=args.selection_package,
        baseline_traces_path=args.baseline_traces,
        replicates=args.replicates,
        outdir=args.outdir,
        branch_code_sha=args.branch_code_sha,
    )
    print(f"prepared {bundle['plan']['branch_row_count']} branch rows from frozen parent {bundle['plan']['parent_snapshot_hash']}")
    print('authorization_status=NOT_AUTHORIZED')


if __name__ == '__main__':
    main()
