#!/usr/bin/env python3
"""Run one full Reviewer-v2 DeepSeek re-annotation round across R2/R3/R4.

This runner shares one spend budget across all layers, validates every immutable
launch binding before credential access, checkpoints each completed review record,
and stops on fatal launch/model/spend/expansion violations without rerunning subjects.
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
from arena.io_utils import load_json, load_jsonl, sha256_file
from arena.reviewer_v2_contract import normalize, parse_json, build_ref_index, get_expansion_record, stable_hash
from arena.evaluate_reviewer_v2_deepseek import (
    PROMPTS, RECORD_VERSION, add_usage, cost_usd, target_ref, validate_launch_record,
)

VERSION = 'R234-REVIEWER-V2-DEEPSEEK-ROUND-v0.1'
LAYERS = ('R2', 'R3', 'R4')


class FatalReviewStop(RuntimeError):
    pass


def append_jsonl(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')


def make_record(layer, packet, final, reviewer_id, model_cfg_hash, prompt_hash, response, usage,
                attempt, failures, expansion_ref, authorization_ref, launch_record_hash):
    row = {
        'review_record_version': RECORD_VERSION[layer],
        'review_layer': layer,
        'review_record_id': f'RV2-{uuid.uuid4()}',
        'evidence_batch_hash': packet['evidence_batch_hash'],
        'packet_id': packet['packet_id'],
        'reviewer': {
            'id': reviewer_id,
            'type': 'model',
            'provider': 'deepseek',
            'model': response.get('model'),
            'model_config_hash': model_cfg_hash,
            'prompt_hash': prompt_hash,
            'blind_to_prior_review': True,
            'blind_to_expected_mapping': True,
        },
        'rationale': final['rationale'],
        'confidence': final['confidence'],
        'uncertainties': final['uncertainties'],
        'evidence_refs': final['evidence_refs'],
        'context_expansion_refs': [expansion_ref] if expansion_ref else [],
        'context_expansion_used': bool(expansion_ref),
        'created_at': dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z'),
        'usage': usage,
        'review_attempt_count': attempt,
        'failed_review_attempts': failures,
        'provider_response_id': response.get('id'),
        'adapter_version': VERSION,
        'authorization_ref': authorization_ref,
        'launch_record_hash': launch_record_hash,
        'packet_hash': packet.get('packet_hash'),
    }
    if layer == 'R2':
        row['target_ref'] = target_ref(layer, packet)
        row['target_effect_scope'] = (packet.get('target_candidate') or {}).get('effect_scope')
        for key in ('epistemic_transition', 'goal_relation', 'goal_focus_transition',
                    'local_retrospective_outcome', 'authorization_judgment'):
            row[key] = final[key]
    elif layer == 'R3':
        row['target_ref'] = target_ref(layer, packet)
        for key in ('semantic_adoption', 'decision_effect', 'lineage_outcome', 'penetration_range_refs'):
            row[key] = final[key]
    else:
        row['window_ref'] = target_ref(layer, packet)
        for key in ('correction', 'persistence', 'regeneration', 'regeneration_mechanisms',
                    'amplification', 'laundering', 'laundered_mechanisms', 'normalization', 'black_hole'):
            row[key] = final[key]
    row['review_record_hash'] = stable_hash(row)
    return row


def write_summary(path, launch_record, launch_hash, budget, requested, completed, errors, layer_counts,
                  started_at, status):
    summary = {
        'round_version': VERSION,
        'status': status,
        'authorization_ref': launch_record['authorization_ref'],
        'launch_record_hash': launch_hash,
        'scientific_role': launch_record['scientific_role'],
        'evidence_batch_hash': launch_record['evidence_batch_hash'],
        'requested_unit_count': requested,
        'completed_unit_count': completed,
        'per_layer_completed': dict(layer_counts),
        'error_count': len(errors),
        'errors': errors,
        'aggregate_usage': budget['usage'],
        'estimated_cost_usd': budget['cost'],
        'price_mode': launch_record['spend_policy']['price_mode_for_ceiling'],
        'max_spend_usd': launch_record['spend_policy']['launch_max_spend_usd'],
        'context_expansion_max_per_packet': 1,
        'review_retries': launch_record['runtime_policy']['malformed_output_retries_max'],
        'subject_reruns_triggered': 0,
        'provider_calls': budget['provider_calls'],
        'started_at': started_at,
        'updated_at': dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z'),
    }
    summary['output_hash'] = stable_hash(summary)
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True), encoding='utf-8')
    return summary


def review_one(layer, packet, prompt, cfg, cfg_hash, prompt_hash, ref_index, reviewer_id,
               retries, authorization_ref, budget, max_spend, price_mode, accepted_models,
               launch_record_hash):
    failures = []
    total_usage = {}
    last_error = None
    for attempt in range(1, retries + 2):
        expansion_ref = None
        messages = [
            {'role': 'system', 'content': prompt},
            {'role': 'user', 'content': json.dumps(packet, ensure_ascii=False)},
        ]
        try:
            while True:
                if budget['cost'] >= max_spend:
                    raise FatalReviewStop('hard spend ceiling reached before provider call')
                response = chat_completion(cfg, messages, evaluator=True, response_format_json=True)
                budget['provider_calls'] += 1
                usage = response.get('usage') or {}
                add_usage(total_usage, usage)
                add_usage(budget['usage'], usage)
                budget['cost'] = cost_usd(budget['usage'], cfg, price_mode)
                if budget['cost'] > max_spend:
                    raise FatalReviewStop('hard spend ceiling exceeded; stop further calls')
                returned_model = response.get('model')
                if returned_model not in accepted_models:
                    raise FatalReviewStop(f'unexpected returned model: {returned_model!r}')
                raw = extract_content(response)
                try:
                    parsed = normalize(layer, parse_json(raw))
                except Exception as err:
                    raise ValueError(f'malformed reviewer output: {err}') from err
                if parsed['review_status'] == 'REQUEST_EXPANSION':
                    if expansion_ref is not None:
                        raise FatalReviewStop('second context expansion requested')
                    expansion_ref = parsed['context_expansion_ref']
                    try:
                        expansion = get_expansion_record(packet, ref_index, expansion_ref)
                    except Exception as err:
                        raise FatalReviewStop(f'invalid expansion request: {err}') from err
                    messages.extend([
                        {'role': 'assistant', 'content': raw},
                        {'role': 'user', 'content': json.dumps({'bounded_frozen_expansion': expansion}, ensure_ascii=False)},
                    ])
                    continue
                return make_record(
                    layer, packet, parsed, reviewer_id, cfg_hash, prompt_hash, response, total_usage,
                    attempt, failures, expansion_ref, authorization_ref, launch_record_hash,
                )
        except FatalReviewStop:
            raise
        except Exception as err:
            last_error = err
            failures.append({'attempt': attempt, 'error': repr(err)})
    raise RuntimeError(f'{layer} review failed after {retries + 1} attempts: {last_error!r}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--launch-record', required=True)
    ap.add_argument('--r2', required=True)
    ap.add_argument('--r3', required=True)
    ap.add_argument('--r4', required=True)
    ap.add_argument('--traces', required=True)
    ap.add_argument('--outdir', required=True)
    ap.add_argument('--reviewer-id', default='deepseek-reviewer-v2-reannotation-v1')
    ap.add_argument('--model-config', default='arena/config/model_deepseek_v0.2.json')
    ap.add_argument('--execute-real-api', action='store_true')
    args = ap.parse_args()

    if not args.execute_real_api:
        raise SystemExit('real Reviewer-v2 round locked; --execute-real-api required')

    launch_record = load_json(args.launch_record)
    authorization_ref = launch_record.get('authorization_ref')
    runtime = launch_record.get('runtime_policy') or {}
    spend = launch_record.get('spend_policy') or {}
    max_spend = spend.get('launch_max_spend_usd')
    price_mode = spend.get('price_mode_for_ceiling')
    retries = runtime.get('malformed_output_retries_max')
    if not authorization_ref:
        raise SystemExit('authorized launch record missing authorization_ref')
    if type(max_spend) not in (int, float) or max_spend <= 0:
        raise SystemExit('authorized launch record missing positive launch_max_spend_usd')
    if retries not in (0, 1, 2):
        raise SystemExit('launch record malformed_output_retries_max must be 0..2')

    packet_paths = {'R2': Path(args.r2), 'R3': Path(args.r3), 'R4': Path(args.r4)}
    cfg_path = ROOT / args.model_config
    bindings = {}
    # Validate every layer before credential access.
    for layer in LAYERS:
        try:
            bindings[layer] = validate_launch_record(
                launch_record, layer, packet_paths[layer], cfg_path, ROOT / PROMPTS[layer],
                authorization_ref, max_spend, retries, price_mode,
            )
        except Exception as err:
            raise SystemExit(f'launch record validation failed before provider access for {layer}: {err}')
    launch_hashes = {x['launch_record_hash'] for x in bindings.values()}
    if len(launch_hashes) != 1:
        raise SystemExit('launch record hash mismatch across validated layers')
    launch_hash = next(iter(launch_hashes))

    if not os.environ.get('DEEPSEEK_API_KEY'):
        raise SystemExit('provider credential is not set')

    cfg = load_json(cfg_path)
    ref_index = build_ref_index(load_jsonl(args.traces))
    prompts = {layer: (ROOT / PROMPTS[layer]).read_text(encoding='utf-8') for layer in LAYERS}
    packets = {layer: load_jsonl(packet_paths[layer]) for layer in LAYERS}
    requested = sum(len(v) for v in packets.values())
    expected = sum((launch_record.get('packet_files') or {})[layer]['unit_count'] for layer in LAYERS)
    if requested != expected:
        raise SystemExit(f'round population mismatch after credential gate: expected {expected}, got {requested}')

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    for layer in LAYERS:
        target = out / f'{layer.lower()}_review_records.jsonl'
        if target.exists():
            raise SystemExit(f'refusing to overwrite existing review output: {target}')

    started_at = dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z')
    budget = {'usage': {}, 'cost': 0.0, 'provider_calls': 0}
    errors = []
    layer_counts = {layer: 0 for layer in LAYERS}
    completed = 0
    summary_path = out / 'review_round_summary.json'
    write_summary(summary_path, launch_record, launch_hash, budget, requested, completed, errors,
                  layer_counts, started_at, 'RUNNING')

    try:
        for layer in LAYERS:
            binding = bindings[layer]
            for packet in packets[layer]:
                record = review_one(
                    layer, packet, prompts[layer], cfg, binding['model_config_sha256'],
                    binding['prompt_sha256'], ref_index, args.reviewer_id, retries,
                    authorization_ref, budget, max_spend, price_mode,
                    binding['accepted_returned_model_values'], launch_hash,
                )
                append_jsonl(out / f'{layer.lower()}_review_records.jsonl', record)
                layer_counts[layer] += 1
                completed += 1
                write_summary(summary_path, launch_record, launch_hash, budget, requested, completed,
                              errors, layer_counts, started_at, 'RUNNING')
    except Exception as err:
        errors.append({'layer': layer, 'packet_id': packet.get('packet_id'), 'error': repr(err)})
        summary = write_summary(summary_path, launch_record, launch_hash, budget, requested, completed,
                                errors, layer_counts, started_at, 'STOPPED_WITH_PARTIAL_RESULTS')
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        raise SystemExit('Reviewer-v2 round stopped; partial records preserved')

    summary = write_summary(summary_path, launch_record, launch_hash, budget, requested, completed,
                            errors, layer_counts, started_at, 'COMPLETE')
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
