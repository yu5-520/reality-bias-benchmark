#!/usr/bin/env python3
import argparse, concurrent.futures, json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from arena.engine import run_arena_once
from arena.io_utils import load_json, load_jsonl, write_jsonl, sha256_file
from arena.journal import Journal
from arena.providers import DeepSeekArenaProvider


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--max-workers', type=int, default=4)
    ap.add_argument('--arena-config', default='arena/config/arena_v0.3.json')
    ap.add_argument('--execute-real-api', action='store_true')
    a = ap.parse_args()
    if not a.execute_real_api:
        raise SystemExit('Refusing to call provider. Add --execute-real-api only for the final real-model step.')
    if not os.environ.get('DEEPSEEK_API_KEY'):
        raise SystemExit('DEEPSEEK_API_KEY is not set')
    arena_path = ROOT / a.arena_config
    arena_cfg = load_json(arena_path)
    model_path = ROOT / arena_cfg.get('model_config_path', 'arena/config/model_deepseek_v0.1.json')
    model_cfg = load_json(model_path)
    manifest = load_jsonl(a.manifest)
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() or Path(a.out + '.journals').exists():
        raise ValueError('refusing to overwrite evidence; choose a new output path')
    run_ids = [x['run_id'] for x in manifest]
    if not manifest or len(run_ids) != len(set(run_ids)) or a.max_workers < 1:
        raise ValueError('nonempty unique manifest and positive worker count required')
    provider = DeepSeekArenaProvider(model_cfg)

    def one(entry):
        if entry['domain_id'] not in arena_cfg['default_domains'] or type(entry.get('trial')) is not int or entry['trial'] < 1:
            raise ValueError('unregistered domain or invalid trial')
        if entry.get('arena_config_path') and entry['arena_config_path'] != a.arena_config:
            raise ValueError(f"manifest/config mismatch: {entry['arena_config_path']} != {a.arena_config}")
        domain_path = ROOT / f"arena/domains/{entry['domain_id']}.json"
        for key, path in [('domain_hash', domain_path), ('arena_config_hash', arena_path), ('model_config_hash', model_path)]:
            if entry.get(key) != sha256_file(path):
                raise ValueError(f'manifest actual-file hash mismatch: {key}')
        domain = load_json(domain_path)
        journal_path = Path(a.out + '.journals') / (str(entry['trial']) + '-' + entry['domain_id'] + '.jsonl')
        with Journal(journal_path) as journal:
            journal({'record_type': 'run_started', 'manifest': entry, 'domain': domain, 'config': arena_cfg, 'model_config': model_cfg})
            trace = run_arena_once(domain, arena_cfg, provider, entry['run_id'], entry.get('logical_seed'), recorder=journal)
            journal({'record_type': 'run_finished', 'run_status': trace['run_status'], 'termination_reason': trace['termination_reason']})
        trace['trial'] = entry['trial']
        trace['code_commit_sha'] = entry.get('code_commit_sha')
        trace['domain_hash'] = entry['domain_hash']
        trace['arena_config_path'] = a.arena_config
        trace['arena_config_version'] = arena_cfg['version']
        trace['arena_config_hash'] = entry['arena_config_hash']
        trace['model_config_version'] = entry.get('model_config_version')
        trace['model_config_hash'] = entry['model_config_hash']
        return trace

    rows = []; errors = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.max_workers) as ex:
        futs = {ex.submit(one, e): e for e in manifest}
        for i, fut in enumerate(concurrent.futures.as_completed(futs), 1):
            entry = futs[fut]
            try:
                row = fut.result(); rows.append(row)
                with out.open('a', encoding='utf-8') as f:
                    f.write(json.dumps(row, ensure_ascii=False) + '\n'); f.flush(); os.fsync(f.fileno())
                print(
                    f"[{i}/{len(manifest)}] {row['run_status']} {entry['run_id']} "
                    f"activated={row['activated_agent_count']} executed={row['executed_agent_count']} "
                    f"returned={row['returned_agent_count']} turns={row['turns']}",
                    flush=True,
                )
            except Exception as err:
                errors.append({'entry': entry, 'error': repr(err)})
                print(f"[{i}/{len(manifest)}] ERROR {entry['run_id']}: {err}", file=sys.stderr, flush=True)
    if errors:
        Path(a.out + '.errors.json').write_text(json.dumps(errors, ensure_ascii=False, indent=2), encoding='utf-8')
    # Preserve every completed/partial trace. Batch integrity is decided later; no evaluator is called here.
    if not rows:
        raise SystemExit('no Arena traces were preserved')
    print(f'preserved {len(rows)} arena traces -> {a.out}; review_status=PENDING_REVIEW')
    if errors or any(r['run_status'] == 'RUN_FAILED' for r in rows):
        raise SystemExit('subject failure preserved; review failure must never trigger regeneration')


if __name__ == '__main__':
    main()

