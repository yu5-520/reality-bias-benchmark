#!/usr/bin/env python3
"""Zero-provider-call preflight for a future Reviewer-v2 paid launch.

This script binds the exact frozen packet population, prompt files, model config,
retry/expansion policy and spend-policy ceiling into one reproducible manifest.
It does not authorize or execute a provider call.
"""
import argparse
import hashlib
import json
from pathlib import Path

VERSION = 'R234-REVIEWER-V2-PAID-LAUNCH-PREFLIGHT-v0.1'
PROMPTS = {
    'R2': 'reviews/reviewer_system_v2/prompts/R2_BOUNDARY_PROMPT_v0.1.md',
    'R3': 'reviews/reviewer_system_v2/prompts/R3_LINEAGE_PROMPT_v0.1.md',
    'R4': 'reviews/reviewer_system_v2/prompts/R4_DYNAMICS_PROMPT_v0.1.md',
}


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def stable_hash(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def load_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def load_jsonl(path):
    return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]


def validate_packet_file(layer, path, expected_count, expected_version, evidence_batch_hash):
    rows = load_jsonl(path)
    errors = []
    if len(rows) != expected_count:
        errors.append(f'{layer}: expected {expected_count} rows, got {len(rows)}')
    ids = [x.get('packet_id') for x in rows]
    if len(set(ids)) != len(ids):
        errors.append(f'{layer}: duplicate packet_id values present')
    for i, row in enumerate(rows):
        if row.get('review_layer') != layer:
            errors.append(f'{layer}[{i}]: review_layer mismatch')
        if row.get('packet_version') != expected_version:
            errors.append(f'{layer}[{i}]: packet_version mismatch: {row.get("packet_version")!r}')
        if row.get('evidence_batch_hash') != evidence_batch_hash:
            errors.append(f'{layer}[{i}]: evidence_batch_hash mismatch')
        if row.get('prior_reviewer_outputs_included') is not False:
            errors.append(f'{layer}[{i}]: prior reviewer outputs are not excluded')
        if row.get('expected_mechanism_mapping_included') is not False:
            errors.append(f'{layer}[{i}]: expected mechanism mapping is not excluded')
        expansion = row.get('context_expansion') or {}
        if expansion.get('max_attempts') != 1:
            errors.append(f'{layer}[{i}]: context expansion max_attempts must equal 1')
        boundary = row.get('boundary_fields') or {}
        if not boundary or any(v != 'NOT_ADJUDICATED' for v in boundary.values()):
            errors.append(f'{layer}[{i}]: boundary fields must remain NOT_ADJUDICATED')
    return rows, errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--candidate', required=True)
    ap.add_argument('--r2', required=True)
    ap.add_argument('--r3', required=True)
    ap.add_argument('--r4', required=True)
    ap.add_argument('--base-compact-summary', required=True)
    ap.add_argument('--r3-summary', required=True)
    ap.add_argument('--repo-root', default='.')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    root = Path(args.repo_root)
    candidate_path = Path(args.candidate)
    candidate = load_json(candidate_path)
    errors = []

    if candidate.get('status') != 'NOT_AUTHORIZED':
        errors.append('candidate status must remain NOT_AUTHORIZED during offline preflight')
    if candidate.get('execute_real_api') is not False:
        errors.append('candidate execute_real_api must remain false during offline preflight')
    auth = candidate.get('authorization') or {}
    if auth.get('authorized_by_user') is not False or auth.get('authorization_ref') is not None:
        errors.append('offline candidate must not contain paid authorization')
    if candidate.get('k2_authorized') is not False:
        errors.append('K2 must remain unauthorized')

    evidence_hash = candidate['evidence_batch_hash']
    pop = candidate['population']
    packet_sources = candidate['packet_sources']
    packet_paths = {'R2': Path(args.r2), 'R3': Path(args.r3), 'R4': Path(args.r4)}
    expected_counts = {'R2': pop['r2_units'], 'R3': pop['r3_units'], 'R4': pop['r4_units']}
    expected_versions = {
        'R2': packet_sources['r2']['packet_version'],
        'R3': packet_sources['r3']['packet_version'],
        'R4': packet_sources['r4']['packet_version'],
    }

    rows_by_layer = {}
    for layer in ('R2', 'R3', 'R4'):
        rows, layer_errors = validate_packet_file(
            layer, packet_paths[layer], expected_counts[layer], expected_versions[layer], evidence_hash
        )
        rows_by_layer[layer] = rows
        errors.extend(layer_errors)
    total = sum(len(v) for v in rows_by_layer.values())
    if total != pop['total_units']:
        errors.append(f'total population mismatch: expected {pop["total_units"]}, got {total}')

    base_summary = load_json(args.base_compact_summary)
    expected_base_hash = packet_sources['r2']['source_compact_output_hash']
    if packet_sources['r4']['source_compact_output_hash'] != expected_base_hash:
        errors.append('R2/R4 candidate source compact hashes disagree')
    if base_summary.get('output_hash') != expected_base_hash:
        errors.append('base compact artifact output_hash mismatch')
    if base_summary.get('evidence_batch_hash') != evidence_hash:
        errors.append('base compact artifact evidence batch mismatch')

    r3_summary = load_json(args.r3_summary)
    if r3_summary.get('output_hash') != packet_sources['r3']['packet_set_hash']:
        errors.append('R3 v0.2 packet-set hash mismatch')
    if r3_summary.get('packet_count') != pop['r3_units']:
        errors.append('R3 v0.2 packet count mismatch')
    if r3_summary.get('semantic_selection_used') is not False:
        errors.append('R3 compaction must not use semantic selection')

    prompt_hashes = {}
    prompt_bytes = {}
    for layer, rel in PROMPTS.items():
        p = root / rel
        digest = sha256_file(p)
        prompt_hashes[layer] = digest
        prompt_bytes[layer] = p.stat().st_size
        if digest != candidate['prompt_hashes'][layer]:
            errors.append(f'{layer} prompt hash mismatch')

    model = candidate['model']
    model_path = root / model['config_path']
    model_cfg = load_json(model_path)
    model_hash = sha256_file(model_path)
    if model_cfg.get('config_version') != model['config_version']:
        errors.append('model config_version mismatch')
    if model_cfg.get('model_alias') != model['model_alias']:
        errors.append('model_alias mismatch')
    if model_cfg.get('expected_model_version') != model['expected_provider_model_version']:
        errors.append('expected provider model version mismatch')
    evaluator = model_cfg.get('evaluator') or {}
    if evaluator.get('temperature') != model['evaluator_temperature']:
        errors.append('evaluator temperature mismatch')
    if evaluator.get('thinking') != model['evaluator_thinking']:
        errors.append('evaluator thinking mismatch')
    if evaluator.get('max_tokens') != model['evaluator_max_tokens']:
        errors.append('evaluator max_tokens mismatch')

    spend = candidate['spend_policy']
    pricing = model_cfg.get('pricing_snapshot_usd_per_million_tokens') or {}
    if pricing.get('source_date') != spend['price_snapshot_source_date']:
        errors.append('pricing source date mismatch')
    if spend.get('launch_max_spend_usd') is not None:
        errors.append('disabled candidate must leave launch_max_spend_usd unset')
    ceiling = spend.get('repository_level_absolute_ceiling_usd')
    if type(ceiling) not in (int, float) or ceiling <= 0:
        errors.append('repository absolute spend ceiling must be positive')

    runtime = candidate['runtime_policy']
    if runtime.get('max_workers') != 1:
        errors.append('candidate max_workers must remain 1 for the first v2 paid pass')
    if runtime.get('malformed_output_retries_max') not in (0, 1, 2):
        errors.append('malformed output retry ceiling must be 0..2')
    if runtime.get('context_expansion_max_per_packet') != 1:
        errors.append('context expansion ceiling must be exactly 1')
    if runtime.get('semantic_uncertainty_retry') is not False:
        errors.append('semantic uncertainty must not trigger retry')
    if runtime.get('subject_rerun_on_reviewer_failure') is not False:
        errors.append('reviewer failure must never trigger subject rerun')

    packet_file_hashes = {layer: sha256_file(path) for layer, path in packet_paths.items()}
    packet_file_bytes = {layer: path.stat().st_size for layer, path in packet_paths.items()}
    prompt_population_bytes = sum(prompt_bytes[layer] * len(rows_by_layer[layer]) for layer in ('R2', 'R3', 'R4'))
    packet_population_bytes = sum(packet_file_bytes.values())
    max_calls_per_unit = (runtime['malformed_output_retries_max'] + 1) * (runtime['context_expansion_max_per_packet'] + 1)
    pathological_call_ceiling = total * max_calls_per_unit
    pathological_output_token_ceiling = pathological_call_ceiling * model['evaluator_max_tokens']

    manifest = {
        'preflight_version': VERSION,
        'status': 'PASS' if not errors else 'FAIL',
        'provider_calls': 0,
        'paid_api_authorized': False,
        'candidate_path': str(candidate_path),
        'candidate_sha256': sha256_file(candidate_path),
        'candidate_semantic_hash': stable_hash(candidate),
        'scientific_role': candidate['scientific_role'],
        'evidence_batch_hash': evidence_hash,
        'population': {
            'R2': len(rows_by_layer['R2']),
            'R3': len(rows_by_layer['R3']),
            'R4': len(rows_by_layer['R4']),
            'total': total,
            'selection_rule': pop['selection_rule'],
        },
        'packet_files': {
            layer: {
                'path': str(packet_paths[layer]),
                'sha256': packet_file_hashes[layer],
                'bytes': packet_file_bytes[layer],
                'packet_version': expected_versions[layer],
            }
            for layer in ('R2', 'R3', 'R4')
        },
        'prompt_hashes': prompt_hashes,
        'model_config': {
            'path': str(model_path),
            'sha256': model_hash,
            'config_version': model_cfg.get('config_version'),
            'model_alias': model_cfg.get('model_alias'),
            'expected_model_version': model_cfg.get('expected_model_version'),
            'accepted_returned_model_values': model['accepted_returned_model_values'],
        },
        'runtime_policy': runtime,
        'spend_policy': spend,
        'price_snapshot': pricing,
        'serialized_request_body_without_provider_wrapper': {
            'packet_file_bytes_including_jsonl_newlines': packet_population_bytes,
            'repeated_system_prompt_bytes': prompt_population_bytes,
            'combined_bytes': packet_population_bytes + prompt_population_bytes,
            'note': 'This is byte volume only, not token count or money.'
        },
        'pathological_retry_expansion_envelope': {
            'max_calls_per_unit_if_every_attempt_expands_and_retries': max_calls_per_unit,
            'max_provider_calls_before_spend_stop_if_no_other_stop_condition': pathological_call_ceiling,
            'max_output_tokens_if_every_call_hit_configured_output_cap': pathological_output_token_ceiling,
            'note': 'Safety envelope only; not an expected usage estimate. Spend ceiling may stop much earlier.'
        },
        'stop_conditions': candidate['stop_conditions'],
        'errors': errors,
        'next_gate': 'CREATE_SEPARATE_AUTHORIZED_IMMUTABLE_LAUNCH_RECORD' if not errors else 'FIX_PREFLIGHT_ERRORS',
    }
    manifest['manifest_hash'] = stable_hash(manifest)
    Path(args.out).write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding='utf-8')
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(f'preflight failed with {len(errors)} error(s)')


if __name__ == '__main__':
    main()
