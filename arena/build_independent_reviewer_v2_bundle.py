#!/usr/bin/env python3
"""Build a result-blind Reviewer-v2 replication bundle.

The bundle contains only frozen packets, frozen prompts, and exact frozen subject
records addressable through packet context-expansion allowlists. It deliberately
excludes all historical/current reviewer outputs and paper/result summaries.
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

from .reviewer_v2_contract import build_ref_index, stable_hash

VERSION = 'R234-INDEPENDENT-REVIEWER-V2-BLIND-BUNDLE-v0.1'
EXPECTED = {
    'R2': {
        'packet_sha256': 'c23522f9916530b4a342c2fd4b2cc028bb8613d0b8626cdc0d76ed9bc1ded63f',
        'packet_count': 70,
        'packet_version': 'R234-REVIEWER-V2-R2-COMPACT-PACKET-v0.1',
        'prompt_sha256': '88cc842ea12030530abd43563b8d6c9d6fb82ef25f997bcd9f55831c4794a924',
    },
    'R3': {
        'packet_sha256': '7cbe61987172f6dd2fa6f547766c145ddf8782d5fc7ec1bf3762b06fb0db0151',
        'packet_count': 70,
        'packet_version': 'R234-REVIEWER-V2-R3-COMPACT-PACKET-v0.2',
        'prompt_sha256': 'e3b2aaafb0ac344b9d92ce3b0c8e0b0dd1fe2693a78b773c5bb3afd8e432373d',
    },
    'R4': {
        'packet_sha256': 'fe0a7d24a2d8fa4f102da9883529bebbcef9be0397057f3b8a23230754ee393a',
        'packet_count': 4,
        'packet_version': 'R234-REVIEWER-V2-R4-COMPACT-PACKET-v0.1',
        'prompt_sha256': '626ace9b857e352380801eb4d125d387af97953ee184b692aa9981b0b2ed12af',
    },
}

# These are result/provenance cues that must never enter the reviewer workspace.
FORBIDDEN_CUES = [
    'Reviewer A',
    'Reviewer B',
    'deepseek-blind-reviewer-b-v1',
    'deepseek-reviewer-v2-reannotation',
    '34993941914',
    '10407112876',
    'CN-R-034',
    'CN-R-035',
    'CN-R-042',
    'CN-R-043',
    'R234-REVIEWER-V1-V2-MEASUREMENT-TRANSITION',
    'Jaccard',
    'C→I',
    'P→V',
    'R→T',
    'zero-positive',
    'zero positive',
    'first full Reviewer-v2 pass',
]


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load_jsonl(path):
    return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]


def write_jsonl(path, rows):
    Path(path).write_text(''.join(json.dumps(x, ensure_ascii=False, sort_keys=True) + '\n' for x in rows), encoding='utf-8')


def validate_packets(layer, path):
    spec = EXPECTED[layer]
    digest = sha256_file(path)
    if digest != spec['packet_sha256']:
        raise ValueError(f'{layer} packet SHA256 mismatch: {digest}')
    rows = load_jsonl(path)
    if len(rows) != spec['packet_count']:
        raise ValueError(f'{layer} packet count mismatch: {len(rows)}')
    for i, row in enumerate(rows):
        if row.get('review_layer') != layer:
            raise ValueError(f'{layer}[{i}] review_layer mismatch')
        if row.get('packet_version') != spec['packet_version']:
            raise ValueError(f'{layer}[{i}] packet_version mismatch')
        if row.get('prior_reviewer_outputs_included') is not False:
            raise ValueError(f'{layer}[{i}] prior reviewer output leak')
        if row.get('expected_mechanism_mapping_included') is not False:
            raise ValueError(f'{layer}[{i}] expected-mechanism leak')
        boundary = row.get('boundary_fields') or {}
        if not boundary or any(v != 'NOT_ADJUDICATED' for v in boundary.values()):
            raise ValueError(f'{layer}[{i}] semantic field already adjudicated')
        if (row.get('context_expansion') or {}).get('max_attempts') != 1:
            raise ValueError(f'{layer}[{i}] expansion ceiling mismatch')
    return rows


def scan_text(name, text):
    lower = text.lower()
    hits = [cue for cue in FORBIDDEN_CUES if cue.lower() in lower]
    if hits:
        raise ValueError(f'blind-bundle leakage in {name}: {hits}')


def build(packet_paths, prompt_paths, traces_path, outdir, evidence_batch_hash):
    out = Path(outdir)
    if out.exists() and any(out.iterdir()):
        raise ValueError(f'output directory must be empty: {out}')
    (out / 'packets').mkdir(parents=True, exist_ok=True)
    (out / 'prompts').mkdir(parents=True, exist_ok=True)

    packets = {}
    allowed_refs = set()
    files = {}
    for layer in ('R2', 'R3', 'R4'):
        rows = validate_packets(layer, packet_paths[layer])
        packets[layer] = rows
        for row in rows:
            if row.get('evidence_batch_hash') != evidence_batch_hash:
                raise ValueError(f'{layer} evidence batch mismatch')
            allowed_refs.update((row.get('context_expansion') or {}).get('allowed_refs') or [])
        dst = out / 'packets' / f'{layer.lower()}_packets.jsonl'
        shutil.copyfile(packet_paths[layer], dst)
        files[f'packets/{dst.name}'] = sha256_file(dst)

        prompt_digest = sha256_file(prompt_paths[layer])
        if prompt_digest != EXPECTED[layer]['prompt_sha256']:
            raise ValueError(f'{layer} prompt SHA256 mismatch: {prompt_digest}')
        prompt_dst = out / 'prompts' / f'{layer.lower()}_prompt.md'
        shutil.copyfile(prompt_paths[layer], prompt_dst)
        files[f'prompts/{prompt_dst.name}'] = sha256_file(prompt_dst)

    traces = load_jsonl(traces_path)
    ref_index = build_ref_index(traces)
    missing = sorted(ref for ref in allowed_refs if ref not in ref_index)
    if missing:
        raise ValueError(f'{len(missing)} allowed expansion refs missing from frozen traces: {missing[:5]}')

    expansion_rows = []
    for ref in sorted(allowed_refs):
        source = ref_index[ref]
        expansion_rows.append({
            'ref': ref,
            'record_type': source['record_type'],
            'record': source['record'],
            'record_hash': stable_hash(source),
        })
    expansion_path = out / 'expansion_records.jsonl'
    write_jsonl(expansion_path, expansion_rows)
    files['expansion_records.jsonl'] = sha256_file(expansion_path)

    # Leakage check is intentionally run on the exact material delivered to a reviewer.
    for rel in sorted(files):
        p = out / rel
        scan_text(rel, p.read_text(encoding='utf-8'))

    manifest = {
        'bundle_version': VERSION,
        'scientific_role': 'INDEPENDENT_REVIEWER_V2_REPLICATION',
        'evidence_batch_hash': evidence_batch_hash,
        'population': {'R2': len(packets['R2']), 'R3': len(packets['R3']), 'R4': len(packets['R4']), 'total': sum(len(x) for x in packets.values())},
        'packet_versions': {layer: EXPECTED[layer]['packet_version'] for layer in EXPECTED},
        'files': files,
        'allowed_expansion_ref_count': len(allowed_refs),
        'expansion_record_count': len(expansion_rows),
        'prior_reviewer_outputs_included': False,
        'prior_v2_result_included': False,
        'historical_agreement_result_included': False,
        'expected_mechanism_mapping_included': False,
        'manuscript_conclusion_included': False,
        'provider_model_selected': False,
        'provider_calls': 0,
        'forbidden_cue_scan': {'status': 'PASS', 'cue_count': len(FORBIDDEN_CUES)},
        'warning': 'This blind bundle contains evidence only. A model family different from DeepSeek must be frozen before it can qualify as independent Reviewer-v2 replication.',
    }
    manifest['bundle_hash'] = stable_hash({'files': files, 'expansion_record_hashes': [x['record_hash'] for x in expansion_rows], 'population': manifest['population']})
    manifest_path = out / 'bundle_manifest.json'
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding='utf-8')
    return manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--r2', required=True)
    ap.add_argument('--r3', required=True)
    ap.add_argument('--r4', required=True)
    ap.add_argument('--r2-prompt', required=True)
    ap.add_argument('--r3-prompt', required=True)
    ap.add_argument('--r4-prompt', required=True)
    ap.add_argument('--traces', required=True)
    ap.add_argument('--evidence-batch-hash', required=True)
    ap.add_argument('--outdir', required=True)
    args = ap.parse_args()
    manifest = build(
        {'R2': args.r2, 'R3': args.r3, 'R4': args.r4},
        {'R2': args.r2_prompt, 'R3': args.r3_prompt, 'R4': args.r4_prompt},
        args.traces, args.outdir, args.evidence_batch_hash,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
