#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .branch_plan_one_shot import build_one_shot_branch_plan, verify_one_shot_branch_plan, _selected_trace
from .core import stable_hash
from .io_utils import load_json, load_jsonl, write_jsonl

FORWARD_STATUS = 'PREPARED_FROM_POST_FREEZE_PROSPECTIVE_NATURAL_JUMP_PENDING_SEMANTIC_ADJUDICATION_AND_PAID_AUTHORIZATION'


def _rehash_plan(plan):
    material = dict(plan)
    material.pop('plan_hash', None)
    plan['plan_hash'] = stable_hash(material)


def build(selection, baseline, *, replicates, branch_code_sha):
    if baseline.get('prospective_evidence') is not True:
        raise ValueError('prospective_one_shot_requires_post_freeze_prospective_trace')
    bundle = build_one_shot_branch_plan(
        selection,
        baseline,
        replicates=replicates,
        branch_code_sha=branch_code_sha,
    )
    plan = bundle['plan']
    plan['scientific_status'] = FORWARD_STATUS
    plan['source_evidence_role'] = 'POST_FREEZE_PROSPECTIVE_NATURAL_TRAJECTORY'
    plan['prospective_confirmation_status'] = 'SOURCE_IS_POST_FREEZE_PROSPECTIVE; CPR_SEMANTIC_STATUS_NOT_ADJUDICATED'
    plan['semantic_cpr_status'] = 'NOT_ADJUDICATED'
    plan['paid_one_shot_authorization_status'] = 'NOT_AUTHORIZED'
    plan['causal_claim_status'] = 'NOT_TESTED_PREPARED_ONLY'
    plan['raw_source_evidence_mutated'] = False
    for row in bundle['branch_rows']:
        row['scientific_status'] = FORWARD_STATUS
        row['source_evidence_role'] = 'POST_FREEZE_PROSPECTIVE_NATURAL_TRAJECTORY'
        row['semantic_cpr_status'] = 'NOT_ADJUDICATED'
    _rehash_plan(plan)
    verify_one_shot_branch_plan(bundle)
    return bundle


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--selection-package', required=True)
    ap.add_argument('--baseline-traces', required=True)
    ap.add_argument('--replicates', type=int, default=2)
    ap.add_argument('--branch-code-sha', required=True)
    ap.add_argument('--outdir', required=True)
    args = ap.parse_args()
    selection = load_json(args.selection_package)
    traces = load_jsonl(args.baseline_traces)
    baseline = _selected_trace(selection, traces)
    bundle = build(selection, baseline, replicates=args.replicates, branch_code_sha=args.branch_code_sha)
    out = Path(args.outdir)
    if out.exists():
        raise ValueError('refusing_to_overwrite_prospective_one_shot_plan')
    out.mkdir(parents=True)
    (out / 'branch_plan.json').write_text(json.dumps(bundle['plan'], ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out / 'parent_snapshot.json').write_text(json.dumps(bundle['parent_snapshot'], ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out / 'one_shot_intervention_envelope.json').write_text(json.dumps(bundle['one_shot_envelope'], ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    write_jsonl(out / 'branch_execution_manifest.jsonl', bundle['branch_rows'])
    write_jsonl(out / 'branch_manifests.jsonl', bundle['branch_manifests'])
    print('PROSPECTIVE_ONE_SHOT_PLAN=PREPARED_OFFLINE')
    print('PLAN_HASH=' + bundle['plan']['plan_hash'])
    print('SOURCE_RUN=' + str(baseline.get('run_id')))
    print('SEMANTIC_CPR_STATUS=NOT_ADJUDICATED')
    print('PAID_ONE_SHOT_AUTHORIZED=NO')


if __name__ == '__main__':
    main()
