#!/usr/bin/env python3
import argparse
import os
from pathlib import Path

from .anchor_selection import validate_anchor_rule
from .core import stable_hash
from .io_utils import load_json, sha256_file, write_jsonl


ROOT = Path(__file__).resolve().parents[1]


def build_rows(
    *,
    repeats,
    domain_id='ecommerce',
    arena_config_path='arena/config/arena_v0.3.json',
    model_config_path='arena/config/model_deepseek_v0.2.json',
    anchor_rule_path='arena/config/r5r6_anchor_rule_v0.2.json',
    code_sha=None,
):
    if type(repeats) is not int or repeats < 1:
        raise ValueError('positive integer repeats required')

    arena_path = ROOT / arena_config_path
    model_path = ROOT / model_config_path
    rule_path = ROOT / anchor_rule_path
    domain_path = ROOT / f'arena/domains/{domain_id}.json'
    arena = load_json(arena_path)
    model = load_json(model_path)
    rule = load_json(rule_path)
    domain = load_json(domain_path)
    validate_anchor_rule(rule)

    if domain_id not in arena.get('default_domains', []):
        raise ValueError('domain_not_registered_in_arena_config')
    if not model.get('provider'):
        raise ValueError('model_provider_required')
    code_sha = code_sha or os.environ.get('GITHUB_SHA') or 'LOCAL_OR_UNRECORDED'

    shared = {
        'experiment_family': 'R5R6-BRANCH-BASELINE-v0.1',
        'phase': 'BASELINE_SNAPSHOT_COLLECTION',
        'domain_id': domain_id,
        'code_commit_sha': code_sha,
        'domain_hash': sha256_file(domain_path),
        'task_hash': stable_hash(domain['task']),
        'agent_pool_hash': stable_hash(domain['agents']),
        'arena_config_path': arena_config_path,
        'arena_config_version': arena['version'],
        'arena_config_hash': sha256_file(arena_path),
        'model_config_path': model_config_path,
        'model_config_version': model.get('config_version'),
        'model_config_hash': sha256_file(model_path),
        'model_provider': model.get('provider'),
        'model_alias': model.get('model_alias'),
        'anchor_rule_path': anchor_rule_path,
        'anchor_rule_version': rule.get('version'),
        'anchor_rule_hash': sha256_file(rule_path),
        'selection_scope': rule.get('selection_scope'),
        'require_pending_queue': bool(rule.get('require_pending_queue')),
        'subject_exposure_to_bias_labels': False,
        'subject_exposure_to_authority_labels': False,
        'automatic_paid_evaluator': False,
        'semantic_review': 'DEFERRED_APPEND_ONLY',
        'snapshot_policy': 'BEFORE_AND_AFTER_EVERY_COMPLETED_ARENA_TURN',
        'scientific_status': 'CANDIDATE_UNTIL_EXPLICIT_REAL_RUN_FREEZE_AND_API_AUTHORIZATION',
    }
    rows = []
    for trial in range(1, repeats + 1):
        rows.append({
            **shared,
            'trial': trial,
            'logical_seed': trial,
            'run_id': f'r5r6-ecommerce-baseline-{trial:04d}',
        })
    return rows


def verify_manifest(rows):
    if not rows:
        raise ValueError('r5r6_baseline_manifest_empty')
    run_ids = [row.get('run_id') for row in rows]
    if len(run_ids) != len(set(run_ids)):
        raise ValueError('duplicate_run_id')
    bindings = (
        'experiment_family', 'phase', 'domain_hash', 'task_hash', 'agent_pool_hash',
        'arena_config_hash', 'model_config_hash', 'anchor_rule_hash', 'model_provider',
    )
    for binding in bindings:
        if len({row.get(binding) for row in rows}) != 1:
            raise ValueError('manifest_binding_not_frozen:' + binding)
    for row in rows:
        if row.get('selection_scope') != 'STRUCTURAL_ONLY':
            raise ValueError('manifest_selection_scope_invalid')
        if row.get('require_pending_queue') is not True:
            raise ValueError('manifest_anchor_must_require_pending_queue')
        if row.get('automatic_paid_evaluator') is not False:
            raise ValueError('automatic_paid_evaluator_must_be_false')
        if row.get('scientific_status') != 'CANDIDATE_UNTIL_EXPLICIT_REAL_RUN_FREEZE_AND_API_AUTHORIZATION':
            raise ValueError('manifest_scientific_status_invalid')
        if type(row.get('trial')) is not int or row['trial'] < 1:
            raise ValueError('manifest_trial_invalid')
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repeats', required=True, type=int)
    ap.add_argument('--domain', default='ecommerce')
    ap.add_argument('--arena-config', default='arena/config/arena_v0.3.json')
    ap.add_argument('--model-config', required=True)
    ap.add_argument('--anchor-rule', default='arena/config/r5r6_anchor_rule_v0.2.json')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    rows = build_rows(
        repeats=args.repeats,
        domain_id=args.domain,
        arena_config_path=args.arena_config,
        model_config_path=args.model_config,
        anchor_rule_path=args.anchor_rule,
    )
    verify_manifest(rows)
    write_jsonl(args.out, rows)
    print(f'prepared {len(rows)} R5/R6 baseline snapshot rows -> {args.out}')
    print('scientific_status=CANDIDATE_UNTIL_EXPLICIT_REAL_RUN_FREEZE_AND_API_AUTHORIZATION')


if __name__ == '__main__':
    main()
