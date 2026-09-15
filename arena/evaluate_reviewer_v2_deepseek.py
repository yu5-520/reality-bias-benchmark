#!/usr/bin/env python3
"""Locked DeepSeek transport for Reviewer v2.

A real call requires an immutable AUTHORIZED launch record in addition to the CLI
execute flag. The record binds packet/config/prompt hashes, retry policy and spend
ceiling before any provider request. This is a revised-rubric re-annotation transport,
not automatically a new independent model-family replication.
"""
import argparse
import datetime as dt
import json
import os
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from adapters.deepseek_chat import chat_completion, extract_content
from arena.io_utils import load_json, load_jsonl, write_jsonl, sha256_file
from arena.reviewer_v2_contract import normalize, parse_json, build_ref_index, get_expansion_record, stable_hash

VERSION = 'R234-REVIEWER-V2-DEEPSEEK-ADAPTER-v0.2'
PROMPTS = {
    'R2': 'reviews/reviewer_system_v2/prompts/R2_BOUNDARY_PROMPT_v0.1.md',
    'R3': 'reviews/reviewer_system_v2/prompts/R3_LINEAGE_PROMPT_v0.1.md',
    'R4': 'reviews/reviewer_system_v2/prompts/R4_DYNAMICS_PROMPT_v0.1.md',
}
RECORD_VERSION = {
    'R2': 'R234-REVIEWER-V2-R2-BOUNDARY-RECORD-v0.1',
    'R3': 'R234-REVIEWER-V2-R3-BOUNDARY-RECORD-v0.1',
    'R4': 'R234-REVIEWER-V2-R4-BOUNDARY-RECORD-v0.1',
}


def add_usage(total, usage):
    for k, v in (usage or {}).items():
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            total[k] = total.get(k, 0) + v


def cost_usd(usage, cfg, mode):
    p = (cfg.get('pricing_snapshot_usd_per_million_tokens') or {}).get(mode) or {}
    hit = float(usage.get('prompt_cache_hit_tokens', 0) or 0)
    miss = float(usage.get('prompt_cache_miss_tokens', 0) or 0)
    prompt = float(usage.get('prompt_tokens', 0) or 0)
    out = float(usage.get('completion_tokens', 0) or 0)
    if hit + miss <= 0:
        miss = prompt
    return (hit * p.get('input_cache_hit', 0) + miss * p.get('input_cache_miss', 0) + out * p.get('output', 0)) / 1_000_000


def target_ref(layer, packet):
    if layer in ('R2', 'R3'):
        return (packet.get('target_candidate') or {}).get('event_ref')
    w = packet.get('structural_window') or {}
    return w.get('structural_round_id') or f"{packet.get('run_id')}:R4:{w.get('round_index')}"


def validate_launch_record(record, layer, packets_path, model_config_path, prompt_path,
                           authorization_ref, max_spend_usd, review_retries, price_mode):
    """Validate all immutable launch bindings before credential/provider access."""
    errors = []
    if record.get('status') != 'AUTHORIZED':
        errors.append('launch record status must be AUTHORIZED')
    if record.get('execute_real_api') is not True:
        errors.append('launch record execute_real_api must be true')
    if record.get('authorization_ref') != authorization_ref:
        errors.append('authorization_ref does not match launch record')
    if record.get('scientific_role') != 'REANNOTATION_CALIBRATION_UNDER_REVISED_SEMANTIC_CONTRACT':
        errors.append('unexpected scientific_role')

    layer_record = (record.get('packet_files') or {}).get(layer)
    if not layer_record:
        errors.append(f'launch record missing packet binding for {layer}')
    else:
        actual_packet_hash = sha256_file(packets_path)
        if layer_record.get('sha256') != actual_packet_hash:
            errors.append(f'{layer} packet file SHA256 mismatch')
        expected_count = layer_record.get('unit_count')
        if expected_count is None:
            errors.append(f'{layer} launch record missing unit_count')
        else:
            actual_count = len(load_jsonl(packets_path))
            if actual_count != expected_count:
                errors.append(f'{layer} unit count mismatch: expected {expected_count}, got {actual_count}')

    if record.get('model_config_sha256') != sha256_file(model_config_path):
        errors.append('model config SHA256 mismatch')
    prompt_hash = sha256_file(prompt_path)
    if (record.get('prompt_hashes') or {}).get(layer) != prompt_hash:
        errors.append(f'{layer} prompt SHA256 mismatch')

    runtime = record.get('runtime_policy') or {}
    if runtime.get('malformed_output_retries_max') != review_retries:
        errors.append('review retry ceiling differs from launch record')
    if runtime.get('context_expansion_max_per_packet') != 1:
        errors.append('launch record context expansion ceiling must equal 1')
    if runtime.get('semantic_uncertainty_retry') is not False:
        errors.append('semantic uncertainty retry must be false')
    if runtime.get('subject_rerun_on_reviewer_failure') is not False:
        errors.append('subject rerun on reviewer failure must be false')
    if runtime.get('max_workers') != 1:
        errors.append('first Reviewer-v2 paid launch must use max_workers=1')

    spend = record.get('spend_policy') or {}
    recorded_spend = spend.get('launch_max_spend_usd')
    absolute_ceiling = spend.get('repository_level_absolute_ceiling_usd')
    if type(recorded_spend) not in (int, float) or recorded_spend <= 0:
        errors.append('launch record must freeze positive launch_max_spend_usd')
    elif max_spend_usd != recorded_spend:
        errors.append('CLI max spend does not match launch record')
    if type(absolute_ceiling) not in (int, float) or absolute_ceiling <= 0:
        errors.append('launch record absolute spend ceiling invalid')
    elif type(recorded_spend) in (int, float) and recorded_spend > absolute_ceiling:
        errors.append('launch max spend exceeds repository absolute ceiling')
    if spend.get('price_mode_for_ceiling') != price_mode:
        errors.append('CLI price mode does not match launch record')

    accepted = record.get('accepted_returned_model_values') or []
    if not accepted or not all(isinstance(x, str) and x for x in accepted):
        errors.append('accepted_returned_model_values must be a non-empty string list')
    if errors:
        raise ValueError('; '.join(errors))
    return {
        'packet_sha256': sha256_file(packets_path),
        'prompt_sha256': prompt_hash,
        'model_config_sha256': sha256_file(model_config_path),
        'accepted_returned_model_values': accepted,
        'launch_record_hash': stable_hash(record),
    }


def make_record(layer, packet, final, reviewer_id, model_cfg_hash, prompt_hash, response, usage,
                attempt, failures, expansion_ref, authorization_ref, launch_record_hash):
    row = {
        'review_record_version': RECORD_VERSION[layer],
        'review_layer': layer,
        'review_record_id': f'RV2-{uuid.uuid4()}',
        'evidence_batch_hash': packet['evidence_batch_hash'],
        'packet_id': packet['packet_id'],
        'reviewer': {
            'id': reviewer_id, 'type': 'model', 'provider': 'deepseek',
            'model': response.get('model'), 'model_config_hash': model_cfg_hash,
            'prompt_hash': prompt_hash, 'blind_to_prior_review': True,
            'blind_to_expected_mapping': True,
        },
        'rationale': final['rationale'], 'confidence': final['confidence'],
        'uncertainties': final['uncertainties'], 'evidence_refs': final['evidence_refs'],
        'context_expansion_refs': [expansion_ref] if expansion_ref else [],
        'context_expansion_used': bool(expansion_ref),
        'created_at': dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z'),
        'usage': usage, 'review_attempt_count': attempt, 'failed_review_attempts': failures,
        'provider_response_id': response.get('id'), 'adapter_version': VERSION,
        'authorization_ref': authorization_ref, 'launch_record_hash': launch_record_hash,
        'packet_hash': packet.get('packet_hash'),
    }
    if layer == 'R2':
        row['target_ref'] = target_ref(layer, packet)
        row['target_effect_scope'] = (packet.get('target_candidate') or {}).get('effect_scope')
        for k in ('epistemic_transition', 'goal_relation', 'goal_focus_transition', 'local_retrospective_outcome', 'authorization_judgment'):
            row[k] = final[k]
    elif layer == 'R3':
        row['target_ref'] = target_ref(layer, packet)
        for k in ('semantic_adoption', 'decision_effect', 'lineage_outcome', 'penetration_range_refs'):
            row[k] = final[k]
    else:
        row['window_ref'] = target_ref(layer, packet)
        for k in ('correction', 'persistence', 'regeneration', 'regeneration_mechanisms', 'amplification', 'laundering', 'laundered_mechanisms', 'normalization', 'black_hole'):
            row[k] = final[k]
    row['review_record_hash'] = stable_hash(row)
    return row


def review_one(layer, packet, prompt, cfg, cfg_hash, prompt_hash, ref_index, reviewer_id,
               retries, authorization_ref, budget, max_spend, price_mode, accepted_models,
               launch_record_hash):
    failures, total_usage, last_error = [], {}, None
    for attempt in range(1, retries + 2):
        expansion_ref = None
        messages = [{'role': 'system', 'content': prompt}, {'role': 'user', 'content': json.dumps(packet, ensure_ascii=False)}]
        try:
            while True:
                if budget['cost'] >= max_spend:
                    raise RuntimeError('hard spend ceiling reached')
                response = chat_completion(cfg, messages, evaluator=True, response_format_json=True)
                returned_model = response.get('model')
                if returned_model not in accepted_models:
                    raise RuntimeError(f'unexpected returned model: {returned_model!r}')
                add_usage(total_usage, response.get('usage'))
                add_usage(budget['usage'], response.get('usage'))
                budget['cost'] = cost_usd(budget['usage'], cfg, price_mode)
                if budget['cost'] > max_spend:
                    raise RuntimeError('hard spend ceiling exceeded; stop further calls')
                raw = extract_content(response)
                parsed = normalize(layer, parse_json(raw))
                if parsed['review_status'] == 'REQUEST_EXPANSION':
                    if expansion_ref is not None:
                        raise ValueError('second context expansion requested')
                    expansion_ref = parsed['context_expansion_ref']
                    expansion = get_expansion_record(packet, ref_index, expansion_ref)
                    messages += [
                        {'role': 'assistant', 'content': raw},
                        {'role': 'user', 'content': json.dumps({'bounded_frozen_expansion': expansion}, ensure_ascii=False)},
                    ]
                    continue
                return make_record(layer, packet, parsed, reviewer_id, cfg_hash, prompt_hash, response,
                                   total_usage, attempt, failures, expansion_ref, authorization_ref,
                                   launch_record_hash)
        except Exception as err:
            last_error = err
            failures.append({'attempt': attempt, 'error': repr(err)})
    raise RuntimeError(f'review failed after {retries + 1} attempts: {last_error!r}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--layer', choices=['R2', 'R3', 'R4'], required=True)
    ap.add_argument('--packets', required=True)
    ap.add_argument('--traces', required=True)
    ap.add_argument('--outdir', required=True)
    ap.add_argument('--launch-record', required=True)
    ap.add_argument('--reviewer-id', default='deepseek-reviewer-v2-reannotation')
    ap.add_argument('--model-config', default='arena/config/model_deepseek_v0.2.json')
    ap.add_argument('--review-retries', type=int, default=2)
    ap.add_argument('--price-mode', choices=['off_peak', 'peak'], default='peak')
    ap.add_argument('--max-spend-usd', type=float)
    ap.add_argument('--authorization-ref')
    ap.add_argument('--execute-real-api', action='store_true')
    args = ap.parse_args()

    if not args.execute_real_api:
        raise SystemExit('real API locked; explicit --execute-real-api required')
    if not args.authorization_ref:
        raise SystemExit('--authorization-ref required')
    if args.max_spend_usd is None or args.max_spend_usd <= 0:
        raise SystemExit('--max-spend-usd required and must be > 0')
    if args.review_retries < 0 or args.review_retries > 2:
        raise SystemExit('--review-retries must be 0..2')

    cfg_path = ROOT / args.model_config
    prompt_path = ROOT / PROMPTS[args.layer]
    launch_record = load_json(args.launch_record)
    try:
        launch_binding = validate_launch_record(
            launch_record, args.layer, args.packets, cfg_path, prompt_path,
            args.authorization_ref, args.max_spend_usd, args.review_retries, args.price_mode,
        )
    except Exception as err:
        raise SystemExit(f'launch record validation failed before provider access: {err}')

    # Credential access is deliberately after all immutable launch-record checks.
    if not os.environ.get('DEEPSEEK_API_KEY'):
        raise SystemExit('provider credential is not set')

    cfg = load_json(cfg_path)
    cfg_hash = launch_binding['model_config_sha256']
    prompt, prompt_hash = prompt_path.read_text(encoding='utf-8'), launch_binding['prompt_sha256']
    packets = load_jsonl(args.packets)
    ref_index = build_ref_index(load_jsonl(args.traces))
    budget = {'usage': {}, 'cost': 0.0}
    rows, errors = [], []
    for packet in packets:
        try:
            rows.append(review_one(
                args.layer, packet, prompt, cfg, cfg_hash, prompt_hash, ref_index,
                args.reviewer_id, args.review_retries, args.authorization_ref, budget,
                args.max_spend_usd, args.price_mode,
                launch_binding['accepted_returned_model_values'],
                launch_binding['launch_record_hash'],
            ))
        except Exception as err:
            errors.append({'packet_id': packet.get('packet_id'), 'error': repr(err)})
            break

    out = Path(args.outdir); out.mkdir(parents=True, exist_ok=True)
    write_jsonl(out / f'{args.layer.lower()}_review_records.jsonl', rows)
    (out / 'review_errors.json').write_text(json.dumps(errors, ensure_ascii=False, indent=2), encoding='utf-8')
    summary = {
        'adapter_version': VERSION, 'layer': args.layer, 'authorization_ref': args.authorization_ref,
        'launch_record_hash': launch_binding['launch_record_hash'],
        'requested_unit_count': len(packets), 'completed_unit_count': len(rows), 'error_count': len(errors),
        'aggregate_usage': budget['usage'], 'estimated_cost_usd': budget['cost'],
        'price_mode': args.price_mode, 'max_spend_usd': args.max_spend_usd,
        'review_retries': args.review_retries, 'context_expansion_max_per_packet': 1,
        'subject_reruns_triggered': 0, 'output_hash': stable_hash(rows),
    }
    (out / 'review_run_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    if errors:
        raise SystemExit('review stopped after failure; partial records preserved')


if __name__ == '__main__':
    main()
