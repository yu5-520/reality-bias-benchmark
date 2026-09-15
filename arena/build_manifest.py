#!/usr/bin/env python3
import argparse
import os
from pathlib import Path
from .io_utils import load_json, write_jsonl, sha256_file
from .core import stable_hash

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--domains', default='all', help='comma-separated domain ids or all')
    ap.add_argument('--repeats', type=int, default=30)
    ap.add_argument('--out', required=True)
    ap.add_argument('--arena-config', default='arena/config/arena_v0.3.json')
    a = ap.parse_args()
    arena_path = ROOT / a.arena_config
    arena = load_json(arena_path)
    model_path = ROOT / arena.get('model_config_path', 'arena/config/model_deepseek_v0.1.json')
    model = load_json(model_path)
    domain_ids = arena['default_domains'] if a.domains == 'all' else [x.strip() for x in a.domains.split(',') if x.strip()]
    code_sha = os.environ.get('GITHUB_SHA') or 'LOCAL_OR_UNRECORDED'
    if a.repeats < 1 or not domain_ids or len(domain_ids) != len(set(domain_ids)) or any(x not in arena['default_domains'] for x in domain_ids):
        raise ValueError('positive repeats and unique registered domain ids required')
    rows = []
    for domain_id in domain_ids:
        path = ROOT / f'arena/domains/{domain_id}.json'
        domain = load_json(path)
        for trial in range(1, a.repeats + 1):
            rows.append({
                'run_id': f"arena-{domain_id}-{trial:04d}",
                'domain_id': domain_id,
                'trial': trial,
                'logical_seed': trial,
                'code_commit_sha': code_sha,
                'domain_hash': sha256_file(path),
                'task_hash': stable_hash(domain['task']),
                'agent_pool_hash': stable_hash(domain['agents']),
                'arena_config_path': a.arena_config,
                'arena_config_version': arena['version'],
                'arena_config_hash': sha256_file(arena_path),
                'model_config_path': str(model_path.relative_to(ROOT)),
                'model_config_version': model.get('config_version'),
                'model_config_hash': sha256_file(model_path),
                'task_goal': domain['task']['goal'],
            })
    write_jsonl(a.out, rows)
    print(f'prepared {len(rows)} arena runs -> {a.out}')


if __name__ == '__main__':
    main()

