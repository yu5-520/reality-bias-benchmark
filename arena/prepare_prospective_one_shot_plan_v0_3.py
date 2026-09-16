#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from .branch_plan_one_shot import build_one_shot_branch_plan, verify_one_shot_branch_plan, _selected_trace
from .core import stable_hash
from .io_utils import load_json, load_jsonl, write_jsonl

FORWARD_STATUS = 'FORMAL_PROSPECTIVE_ONESHOT_V0_3_PREPARED_FROM_POST_FREEZE_NATURAL_JUMP_PENDING_PAID_AUTHORIZATION'
EXPECTED_MEASUREMENT_VERSION = 'v0.4_THREE_LAYER_PROCESS_TOPOLOGY'
EXPECTED_BINDING_STATUS = 'BOUND_THREE_LAYER_PROCESS_TOPOLOGY_V0.4'


def _rehash_plan(plan):
    material = dict(plan)
    material.pop('plan_hash', None)
    plan['plan_hash'] = stable_hash(material)


def _verify_measurement_binding(binding):
    if not isinstance(binding, dict):
        raise ValueError('v04_source_measurement_binding_required')
    if binding.get('measurement_version') != EXPECTED_MEASUREMENT_VERSION:
        raise ValueError('v04_source_measurement_version_required')
    required = [
        'measurement_workflow_run_id',
        'measurement_artifact_id',
        'measurement_artifact_digest',
        'measurement_hash',
        'measurement_contract_sha256',
        'resolved_root_behavior_event_id',
        'root_edge_multiset_hash',
        'root_ordered_sequence_hash',
        'observed_path_family_hash',
        'descendant_rejump_count',
        'continuation_root_reachable_event_count',
        'continuation_root_reach_depth',
        'root_descendant_cross_actor_relation_count',
        'branch_node_count',
        'merge_node_count',
        'role_reentry_count',
        'observed_path_family_count',
    ]
    missing = [k for k in required if binding.get(k) is None]
    if missing:
        raise ValueError('v04_source_measurement_binding_missing:' + ','.join(missing))
    if binding.get('path_family_overflow') is not False:
        raise ValueError('formal_prepare_requires_nonoverflow_source_path_family_measurement')
    if binding.get('semantic_cpr_status') != 'NOT_ADJUDICATED':
        raise ValueError('source_semantic_cpr_must_remain_not_adjudicated')
    return True


def build(selection, baseline, *, replicates, branch_code_sha, source_measurement_binding):
    if baseline.get('prospective_evidence') is not True:
        raise ValueError('prospective_one_shot_requires_post_freeze_prospective_trace')
    _verify_measurement_binding(source_measurement_binding)
    bundle = build_one_shot_branch_plan(
        selection,
        baseline,
        replicates=replicates,
        branch_code_sha=branch_code_sha,
    )
    plan = bundle['plan']
    plan['formal_prepare_version'] = '0.3'
    plan['scientific_status'] = FORWARD_STATUS
    plan['source_evidence_role'] = 'POST_FREEZE_PROSPECTIVE_NATURAL_TRAJECTORY'
    plan['prospective_confirmation_status'] = 'SOURCE_IS_POST_FREEZE_PROSPECTIVE; CPR_SEMANTIC_STATUS_NOT_ADJUDICATED'
    plan['semantic_cpr_status'] = 'NOT_ADJUDICATED'
    plan['paid_one_shot_authorization_status'] = 'NOT_AUTHORIZED'
    plan['causal_claim_status'] = 'NOT_TESTED_PREPARED_ONLY'
    plan['raw_source_evidence_mutated'] = False
    plan['source_measurement_binding'] = copy.deepcopy(source_measurement_binding)
    plan['source_measurement_binding_status'] = EXPECTED_BINDING_STATUS
    plan['downstream_measurement_version'] = 'RB-PROCESS-REALITY-MECHANISM-MEASUREMENT-v0.4'
    plan['downstream_derivation_module'] = 'arena.derive_one_shot_process_measurements_v0_4'
    plan['analysis_layers'] = ['JUMP_RECURRENCE', 'INHERITED_INERTIA', 'PATH_TOPOLOGY']
    plan['terminal_outcome_is_primary'] = False
    for row in bundle['branch_rows']:
        row['scientific_status'] = FORWARD_STATUS
        row['source_evidence_role'] = 'POST_FREEZE_PROSPECTIVE_NATURAL_TRAJECTORY'
        row['semantic_cpr_status'] = 'NOT_ADJUDICATED'
        row['source_measurement_version'] = EXPECTED_MEASUREMENT_VERSION
        row['downstream_measurement_version'] = 'v0.4'
    _rehash_plan(plan)
    verify_one_shot_branch_plan(bundle)
    return bundle


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--selection-package', required=True)
    ap.add_argument('--baseline-traces', required=True)
    ap.add_argument('--replicates', type=int, default=2)
    ap.add_argument('--branch-code-sha', required=True)
    ap.add_argument('--source-measurement-binding', required=True)
    ap.add_argument('--outdir', required=True)
    args = ap.parse_args()
    selection = load_json(args.selection_package)
    traces = load_jsonl(args.baseline_traces)
    baseline = _selected_trace(selection, traces)
    measurement_binding = load_json(args.source_measurement_binding)
    bundle = build(
        selection,
        baseline,
        replicates=args.replicates,
        branch_code_sha=args.branch_code_sha,
        source_measurement_binding=measurement_binding,
    )
    out = Path(args.outdir)
    if out.exists():
        raise ValueError('refusing_to_overwrite_prospective_one_shot_plan_v03')
    out.mkdir(parents=True)
    (out / 'branch_plan.json').write_text(json.dumps(bundle['plan'], ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out / 'parent_snapshot.json').write_text(json.dumps(bundle['parent_snapshot'], ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out / 'one_shot_intervention_envelope.json').write_text(json.dumps(bundle['one_shot_envelope'], ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    write_jsonl(out / 'branch_execution_manifest.jsonl', bundle['branch_rows'])
    write_jsonl(out / 'branch_manifests.jsonl', bundle['branch_manifests'])
    (out / 'source_measurement_binding.json').write_text(json.dumps(measurement_binding, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('FORMAL_PROSPECTIVE_ONE_SHOT_PLAN_V03=PREPARED_OFFLINE')
    print('PLAN_HASH=' + bundle['plan']['plan_hash'])
    print('SOURCE_RUN=' + str(baseline.get('run_id')))
    print('SOURCE_MEASUREMENT_BINDING=' + bundle['plan']['source_measurement_binding_status'])
    print('DOWNSTREAM_MEASUREMENT=v0.4')
    print('SEMANTIC_CPR_STATUS=NOT_ADJUDICATED')
    print('PAID_ONE_SHOT_AUTHORIZED=NO')


if __name__ == '__main__':
    main()
