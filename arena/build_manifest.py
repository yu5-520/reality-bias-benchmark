#!/usr/bin/env python3
import argparse
from pathlib import Path
from .io_utils import load_json, write_jsonl, sha256_file

ROOT=Path(__file__).resolve().parents[1]


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--domains',default='all',help='comma-separated domain ids or all')
    ap.add_argument('--repeats',type=int,default=30)
    ap.add_argument('--out',required=True)
    a=ap.parse_args()
    arena=load_json(ROOT/'arena/config/arena_v0.1.json')
    domain_ids=arena['default_domains'] if a.domains=='all' else [x.strip() for x in a.domains.split(',') if x.strip()]
    rows=[]
    for domain_id in domain_ids:
        path=ROOT/f'arena/domains/{domain_id}.json'
        domain=load_json(path)
        for trial in range(1,a.repeats+1):
            rows.append({
                'run_id':f"arena-{domain_id}-{trial:04d}",
                'domain_id':domain_id,
                'trial':trial,
                'logical_seed':trial,
                'domain_hash':sha256_file(path),
                'arena_config_hash':sha256_file(ROOT/'arena/config/arena_v0.1.json'),
                'model_config_hash':sha256_file(ROOT/'arena/config/model_deepseek_v0.1.json'),
                'task_goal':domain['task']['goal'],
            })
    write_jsonl(a.out,rows)
    print(f'prepared {len(rows)} arena runs -> {a.out}')


if __name__=='__main__': main()
