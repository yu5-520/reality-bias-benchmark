#!/usr/bin/env python3
import argparse
import os
from pathlib import Path

from .core import stable_hash
from .io_utils import load_json, sha256_file, write_jsonl
from .structured_routing import validate_structured_policy


ROOT = Path(__file__).resolve().parents[1]


def build_rows(*, repeats, domain_id='ecommerce', arena_config_path='arena/config/arena_v0.3.json', structured_policy_path='arena/config/structured_ecommerce_v0.1.json', code_sha=None):
    if type(repeats) is not int or repeats < 1:
        raise ValueError('positive integer repeats required')

    arena_path = ROOT / arena_config_path
    policy_path = ROOT / structured_policy_path
    domain_path = ROOT / f'arena/domains/{domain_id}.json'
    arena = load_json(arena_path)
    domain = load_json(domain_path)
    policy = load_json(policy_path)
    validate_structured_policy(domain, policy)

    if domain_id not in arena.get('default_domains', []):
        raise ValueError('domain_not_registered_in_arena_config')

    model_path = ROOT / arena.get('model_config_path', 'arena/config/model_deepseek_v0.1.json')
    model = load_json(model_path)
    code_sha = code_sha or os.environ.get('GITHUB_SHA') or 'LOCAL_OR_UNRECORDED'

    shared = {
        'experiment_family': 'R7-ORCHESTRATION-BOUNDARY-v0.1',
        'domain_id': domain_id,
        'code_commit_sha': code_sha,
        'domain_hash': sha256_file(domain_path),
        'task_hash': stable_hash(domain['task']),
        'agent_pool_hash': stable_hash(domain['agents']),
        'arena_config_path': arena_config_path,
        'arena_config_version': arena['version'],
        'arena_config_hash': sha256_file(arena_path),
        'model_config_path': str(model_path.relative_to(ROOT)),
        'model_config_version': model.get('config_version'),
        'model_config_hash': sha256_file(model_path),
        'structured_policy_path': structured_policy_path,
        'structured_policy_version': policy.get('version'),
        'structured_policy_hash': sha256_file(policy_path),
        'task_goal': domain['task']['goal'],
        'subject_exposure_to_bias_labels': False,
        'subject_exposure_to_authority_labels': False,
        'automatic_paid_evaluator': False,
        'scientific_status': 'CANDIDATE_UNTIL_EXPLICIT_REAL_RUN_FREEZE_AND_API_AUTHORIZATION',
    }

    rows = []
    for trial in range(1, repeats + 1):
        pair_id = f'r7-ecommerce-pair-{trial:04d}'
        logical_seed = trial
        rows.append({
            **shared,
            'pair_id': pair_id,
            'condition_id': 'EMERGENT_FREE_ROUTING',
            'run_id': f'{pair_id}-free',
            'trial': trial,
            'logical_seed': logical_seed,
            'routing_owner': 'AGENT_WITHIN_ARENA_POLICY',
            'structured_policy_active': False,
        })
        rows.append({
            **shared,
            'pair_id': pair_id,
            'condition_id': 'STRUCTURED_SYSTEM_OWNED_ROUTING',
            'run_id': f'{pair_id}-structured',
            'trial': trial,
            'logical_seed': logical_seed,
            'routing_owner': 'EXPERIMENT_SYSTEM',
            'structured_policy_active': True,
        })
    return rows


def verify_pairing(rows):
    if not rows:
        raise ValueError('orchestration_manifest_empty')
    run_ids = [row.get('run_id') for row in rows]
    if len(run_ids) != len(set(run_ids)):
        raise ValueError('duplicate_run_id')

    pairs = {}
    for row in rows:
        pairs.setdefault(row.get('pair_id'), []).append(row)
    for pair_id, pair_rows in pairs.items():
        if not pair_id or len(pair_rows) != 2:
            raise ValueError('pair_must_have_exactly_two_conditions')
        conditions = {row.get('condition_id') for row in pair_rows}
        if conditions != {'EMERGENT_FREE_ROUTING', 'STRUCTURED_SYSTEM_OWNED_ROUTING'}:
            raise ValueError('pair_condition_set_invalid')
        if len({row.get('logical_seed') for row in pair_rows}) != 1:
            raise ValueError('paired_logical_seed_mismatch')
        for binding in ('domain_hash', 'task_hash', 'agent_pool_hash', 'arena_config_hash', 'model_config_hash'):
            if len({row.get(binding) for row in pair_rows}) != 1:
                raise ValueError('paired_binding_mismatch:' + binding)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repeats', type=int, required=True)
    ap.add_argument('--domain', default='ecommerce')
    ap.add_argument('--arena-config', default='arena/config/arena_v0.3.json')
    ap.add_argument('--structured-policy', default='arena/config/structured_ecommerce_v0.1.json')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    rows = build_rows(
        repeats=args.repeats,
        domain_id=args.domain,
        arena_config_path=args.arena_config,
        structured_policy_path=args.structured_policy,
    )
    verify_pairing(rows)
    write_jsonl(args.out, rows)
    print(f'prepared {len(rows)} rows / {len(rows) // 2} paired orchestration trials -> {args.out}')
    print('scientific_status=CANDIDATE_UNTIL_EXPLICIT_REAL_RUN_FREEZE_AND_API_AUTHORIZATION')


if __name__ == '__main__':
    main()
