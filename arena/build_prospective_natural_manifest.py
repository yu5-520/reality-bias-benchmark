#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path

from .anchor_selection import validate_anchor_rule
from .core import stable_hash
from .io_utils import load_json, sha256_file, write_jsonl

ROOT = Path(__file__).resolve().parents[1]
SCIENTIFIC_STATUS = 'PROSPECTIVE_NATURAL_SUBJECT_CANDIDATE_AWAITING_EXPLICIT_PAID_AUTHORIZATION'


def build_rows(*, contract_path, arena_config_path, model_config_path, code_sha=None):
    contract_file = ROOT / contract_path
    contract = load_json(contract_file)
    if contract.get('schema') != 'RB-PROSPECTIVE-NATURAL-COLLECTION-CONTRACT-v0.1':
        raise ValueError('prospective_contract_schema_invalid')
    if contract.get('paid_subject_execution_authorized') is not False:
        raise ValueError('prospective_prepare_contract_must_not_authorize_paid_execution')
    repeats = contract.get('planned_repeats')
    if type(repeats) is not int or repeats < 1:
        raise ValueError('prospective_planned_repeats_invalid')
    domain_id = contract['domain_id']
    arena_path = ROOT / arena_config_path
    model_path = ROOT / model_config_path
    anchor_rule_path = ROOT / contract['anchor_rule']
    domain_path = ROOT / f'arena/domains/{domain_id}.json'
    arena = load_json(arena_path)
    model = load_json(model_path)
    rule = load_json(anchor_rule_path)
    domain = load_json(domain_path)
    validate_anchor_rule(rule)
    if rule.get('schema') != 'RB-R5R6-ANCHOR-RULE-v0.3':
        raise ValueError('prospective_anchor_rule_must_be_v03')
    if domain_id not in arena.get('default_domains', []):
        raise ValueError('prospective_domain_not_registered')
    code_sha = code_sha or os.environ.get('GITHUB_SHA') or 'LOCAL_OR_UNRECORDED'
    shared = {
        'experiment_family': 'R2R6-PROSPECTIVE-NATURAL-v0.1',
        'batch_id': contract['batch_id'],
        'phase': 'PROSPECTIVE_NATURAL_TRAJECTORY_COLLECTION',
        'domain_id': domain_id,
        'code_commit_sha': code_sha,
        'contract_path': contract_path,
        'contract_hash': sha256_file(contract_file),
        'theory_contract_path': 'theory/theory_contract_v0.5.md',
        'theory_contract_hash': sha256_file(ROOT / 'theory/theory_contract_v0.5.md'),
        'measurement_plan_path': 'docs/system_behavior_measurement_plan_v4.1.md',
        'measurement_plan_hash': sha256_file(ROOT / 'docs/system_behavior_measurement_plan_v4.1.md'),
        'domain_hash': sha256_file(domain_path),
        'task_hash': stable_hash(domain['task']),
        'agent_pool_hash': stable_hash(domain['agents']),
        'arena_config_path': arena_config_path,
        'arena_config_version': arena.get('version'),
        'arena_config_hash': sha256_file(arena_path),
        'model_config_path': model_config_path,
        'model_config_version': model.get('config_version'),
        'model_config_hash': sha256_file(model_path),
        'model_provider': model.get('provider'),
        'model_alias': model.get('model_alias'),
        'anchor_rule_path': contract['anchor_rule'],
        'anchor_rule_version': rule.get('version'),
        'anchor_rule_hash': sha256_file(anchor_rule_path),
        'selection_scope': rule.get('selection_scope'),
        'subject_exposure_to_cpr_labels': False,
        'subject_exposure_to_jump_hypothesis': False,
        'subject_exposure_to_authority_labels': False,
        'automatic_paid_evaluator': False,
        'semantic_review': 'DEFERRED_APPEND_ONLY',
        'snapshot_policy': 'BEFORE_AND_AFTER_EVERY_COMPLETED_ARENA_TURN',
        'no_outcome_aware_rerun': True,
        'scientific_status': SCIENTIFIC_STATUS,
    }
    rows = []
    for trial in range(1, repeats + 1):
        rows.append({
            **shared,
            'trial': trial,
            'logical_seed': trial,
            'run_id': f"prospective-ecommerce-natural-{trial:04d}",
        })
    verify_manifest(rows)
    return rows


def verify_manifest(rows):
    if not rows:
        raise ValueError('prospective_manifest_empty')
    if len({x.get('run_id') for x in rows}) != len(rows):
        raise ValueError('prospective_duplicate_run_id')
    frozen = ('experiment_family', 'batch_id', 'domain_hash', 'task_hash', 'agent_pool_hash', 'contract_hash', 'theory_contract_hash', 'measurement_plan_hash', 'arena_config_hash', 'model_config_hash', 'anchor_rule_hash')
    for key in frozen:
        if len({x.get(key) for x in rows}) != 1:
            raise ValueError('prospective_binding_not_frozen:' + key)
    for row in rows:
        if row.get('selection_scope') != 'STRUCTURAL_ONLY_OUTCOME_BLIND':
            raise ValueError('prospective_selection_scope_invalid')
        if row.get('automatic_paid_evaluator') is not False:
            raise ValueError('prospective_paid_evaluator_must_be_false')
        if row.get('no_outcome_aware_rerun') is not True:
            raise ValueError('prospective_no_rerun_rule_required')
        if row.get('scientific_status') != SCIENTIFIC_STATUS:
            raise ValueError('prospective_scientific_status_invalid')
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--contract', default='configs/prospective_natural_collection_contract_v0.1.json')
    ap.add_argument('--arena-config', default='arena/config/arena_v0.3.json')
    ap.add_argument('--model-config', default='arena/config/model_deepseek_v0.2.json')
    ap.add_argument('--code-sha')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    rows = build_rows(contract_path=args.contract, arena_config_path=args.arena_config, model_config_path=args.model_config, code_sha=args.code_sha)
    write_jsonl(args.out, rows)
    print('PROSPECTIVE_ROWS=' + str(len(rows)))
    print('PAID_API_AUTHORIZED=NO')
    print('SCIENTIFIC_STATUS=' + SCIENTIFIC_STATUS)


if __name__ == '__main__':
    main()
