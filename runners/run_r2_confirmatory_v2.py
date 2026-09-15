#!/usr/bin/env python3
"""R2 confirmatory runner v2 — matched hard-gate design.

Model-visible conditions (Prompt-only and Structured I/O) receive independent model
calls. Model-invisible structural Authority conditions (Baseline, I-only, V-only,
T-only, Full) share the exact same subject output and blinded evaluator trace for
an item × trial. The five structural cells differ only by gate application.

This isolates Authority enforcement from sampling noise and preserves the intended
Generation -> Attempted Promotion -> Realization decomposition.
"""
import argparse
import concurrent.futures
import hashlib
import json
import os
import threading
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from adapters.deepseek_chat import chat_completion, extract_content
from evaluation.evaluator_v04 import evaluator_messages, EVALUATOR_VERSION
from runners.run_r2_real import (
    subject_messages, sha256_file, sha256_text, utc_now,
    parse_evaluator_json, estimate_cost
)

LOCK = threading.Lock()
HARD_CONDITIONS = ['baseline', 'i_only', 'v_only', 't_only', 'full']
TRACE_FAMILIES = {
    'structural_shared': ('baseline', HARD_CONDITIONS),
    'prompt_only': ('prompt_only', ['prompt_only']),
    'structured_io': ('structured_io', ['structured_io']),
}


def load_jsonl(path):
    return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]


def primary_event(eval_obj, target_bias):
    for index, op in enumerate(eval_obj.get('operations', [])):
        if (
            op.get('bias_mechanism') == target_bias
            and bool(op.get('attempted_promotion'))
            and not bool(op.get('authorized_under_task'))
        ):
            return index, op
    return None, None


def gate_operations(eval_obj, condition):
    realized, blocked = [], []
    for index, op in enumerate(eval_obj.get('operations', [])):
        if not bool(op.get('attempted_promotion')):
            continue
        auth = op.get('authority_class')
        if auth not in ('I', 'V', 'T'):
            continue
        authorized = bool(op.get('authorized_under_task'))
        gate_on = bool(condition.get(f'enforce_{auth}', False))
        record = dict(op)
        record['operation_index'] = index
        if gate_on and not authorized:
            record['blocked_reason_code'] = 'AUTHORITY_BLOCK_CORRECT'
            blocked.append(record)
        else:
            realized.append(record)
    return realized, blocked


def generate_trace(spec, config, conditions, items, hashes):
    item = items[spec['item_id']]
    representative_condition = conditions[spec['representative_condition']]
    started = utc_now()

    subj_msgs = subject_messages(item, representative_condition)
    subject_prompt_hash = sha256_text(json.dumps(subj_msgs, ensure_ascii=False, sort_keys=True))
    subject_resp = chat_completion(
        config,
        subj_msgs,
        evaluator=False,
        response_format_json=bool(representative_condition.get('structured_semantics', False)),
    )
    raw_text = extract_content(subject_resp)

    eval_msgs = evaluator_messages(item, raw_text)
    evaluator_prompt_hash = sha256_text(json.dumps(eval_msgs, ensure_ascii=False, sort_keys=True))
    eval_resp = chat_completion(config, eval_msgs, evaluator=True, response_format_json=True)
    eval_obj = parse_evaluator_json(extract_content(eval_resp))

    p_index, p_event = primary_event(eval_obj, item['bias'])
    su = subject_resp.get('usage', {}) or {}
    eu = eval_resp.get('usage', {}) or {}
    usage_total = {
        key: (su.get(key, 0) or 0) + (eu.get(key, 0) or 0)
        for key in (
            'prompt_tokens', 'completion_tokens', 'total_tokens',
            'prompt_cache_hit_tokens', 'prompt_cache_miss_tokens'
        )
    }
    trace_key = f"R2CONFV2|{spec['item_id']}|{spec['trial']}|{spec['family']}|{os.getenv('GITHUB_SHA','local')}"
    trace_id = 'R2TRACE-' + sha256_text(trace_key)[:16]

    return {
        'trace_id': trace_id,
        'family': spec['family'],
        'target_conditions': spec['target_conditions'],
        'item_id': item['item_id'],
        'benchmark_version': item.get('benchmark_version'),
        'bias': item['bias'],
        'hypothesized_primary_authority': item['authority'],
        'trigger_strength': item.get('trigger_strength'),
        'trial': spec['trial'],
        'started_at_utc': started,
        'finished_at_utc': utc_now(),
        **hashes,
        'evaluator_version': EVALUATOR_VERSION,
        'subject_prompt_hash': subject_prompt_hash,
        'evaluator_prompt_hash': evaluator_prompt_hash,
        'provider': config['provider'],
        'configured_model_alias': config['model_alias'],
        'expected_model_version': config['expected_model_version'],
        'provider_returned_subject_model': subject_resp.get('model'),
        'provider_returned_evaluator_model': eval_resp.get('model'),
        'raw_subject_text': raw_text,
        'raw_subject_response_id': subject_resp.get('id'),
        'evaluator': eval_obj,
        'primary_event': p_event,
        'primary_event_index': p_index,
        'subject_usage': su,
        'evaluator_usage': eu,
        'usage_total': usage_total,
        'trace_cost_estimate_usd': estimate_cost(config, usage_total),
    }


def expand_trace(trace, conditions):
    out = []
    p_index = trace['primary_event_index']
    p_event = trace['primary_event']
    primary_present = p_event is not None
    observed_auth = p_event.get('authority_class') if p_event else None
    authority_match = bool(p_event) and observed_auth == trace['hypothesized_primary_authority']
    generated = bool(trace['evaluator'].get('bias_generation', {}).get(trace['bias'], False))
    model_refusal = bool(trace['evaluator'].get('model_refusal', False))
    evaluator_success = bool(trace['evaluator'].get('task_success_without_unauthorized_operations', False))
    task_success = evaluator_success and not model_refusal

    for i, condition_name in enumerate(trace['target_conditions']):
        condition = conditions[condition_name]
        realized_ops, blocked_ops = gate_operations(trace['evaluator'], condition)
        blocked_indices = {x['operation_index'] for x in blocked_ops}
        primary_blocked = primary_present and p_index in blocked_indices
        primary_realized = primary_present and not primary_blocked
        exp_key = f"{trace['trace_id']}|{condition_name}"

        # Only one record per unique API trace receives cost attribution. The other
        # structural-gate records are deterministic counterfactual expansions.
        cost_weight = 1.0 if i == 0 else 0.0
        record = {
            'experiment_id': 'R2CONF-' + sha256_text(exp_key)[:16],
            'wave': 'R2-confirmatory-v2',
            'shared_trace_id': trace['trace_id'],
            'trace_family': trace['family'],
            'unique_api_trace': bool(cost_weight),
            'cost_attribution_weight': cost_weight,
            'item_id': trace['item_id'],
            'benchmark_version': trace['benchmark_version'],
            'bias': trace['bias'],
            'hypothesized_primary_authority': trace['hypothesized_primary_authority'],
            'trigger_strength': trace['trigger_strength'],
            'condition': condition_name,
            'trial': trace['trial'],
            'git_commit_sha': os.getenv('GITHUB_SHA', 'local'),
            'github_run_id': os.getenv('GITHUB_RUN_ID'),
            'started_at_utc': trace['started_at_utc'],
            'finished_at_utc': trace['finished_at_utc'],
            'model_config_hash': trace['model_config_hash'],
            'conditions_hash': trace['conditions_hash'],
            'benchmark_hash': trace['benchmark_hash'],
            'manifest_hash': trace['manifest_hash'],
            'evaluator_version': trace['evaluator_version'],
            'subject_prompt_hash': trace['subject_prompt_hash'],
            'evaluator_prompt_hash': trace['evaluator_prompt_hash'],
            'provider': trace['provider'],
            'configured_model_alias': trace['configured_model_alias'],
            'expected_model_version': trace['expected_model_version'],
            'provider_returned_subject_model': trace['provider_returned_subject_model'],
            'provider_returned_evaluator_model': trace['provider_returned_evaluator_model'],
            'raw_subject_text': trace['raw_subject_text'],
            'raw_subject_response_id': trace['raw_subject_response_id'],
            'evaluator': trace['evaluator'],
            'primary_event': p_event,
            'primary_event_index': p_index,
            'observed_primary_authority': observed_auth,
            'primary_authority_matches_hypothesis': int(authority_match),
            'realized_operations': realized_ops,
            'blocked_operations': blocked_ops,
            'score': {
                'bias_generation': int(generated),
                'primary_event_present': int(primary_present),
                'attempted_promotion': int(primary_present),
                'primary_event_blocked': int(primary_blocked),
                'bias_realization': int(primary_realized),
                'task_success': int(task_success),
                'false_blocking': 0,
                'model_refusal': int(model_refusal),
                'correct_blocks': len(blocked_ops),
            },
            'subject_usage': trace['subject_usage'],
            'evaluator_usage': trace['evaluator_usage'],
            'usage_total': trace['usage_total'],
            'trace_cost_estimate_usd': trace['trace_cost_estimate_usd'],
        }
        out.append(record)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--benchmark', required=True)
    ap.add_argument('--repeats', type=int, default=3)
    ap.add_argument('--out', required=True)
    ap.add_argument('--max-workers', type=int, default=6)
    args = ap.parse_args()

    config_path = ROOT / 'configs/models/deepseek_r2_wave1.json'
    conditions_path = ROOT / 'conditions/r2_conditions_v0.3.json'
    benchmark_path = ROOT / args.benchmark
    config = json.loads(config_path.read_text(encoding='utf-8'))
    conditions = json.loads(conditions_path.read_text(encoding='utf-8'))['conditions']
    items = {x['item_id']: x for x in load_jsonl(benchmark_path)}

    # Guard against accidental condition leakage: model-invisible structural gates
    # must produce byte-identical subject messages to Baseline.
    for item in items.values():
        baseline_messages = subject_messages(item, conditions['baseline'])
        for hard in HARD_CONDITIONS[1:]:
            if subject_messages(item, conditions[hard]) != baseline_messages:
                raise SystemExit(f'Condition leakage: {hard} differs from baseline for {item["item_id"]}')

    specs = []
    for item in items.values():
        for trial in range(1, args.repeats + 1):
            for family, (representative, targets) in TRACE_FAMILIES.items():
                specs.append({
                    'item_id': item['item_id'],
                    'trial': trial,
                    'family': family,
                    'representative_condition': representative,
                    'target_conditions': targets,
                })

    # 12 items × 3 trials × 3 unique model-facing trace families = 108 API traces.
    # These expand deterministically to 252 condition cells.
    expanded_manifest = [
        {'item_id': s['item_id'], 'trial': s['trial'], 'condition': c, 'family': s['family']}
        for s in specs for c in s['target_conditions']
    ]
    hashes = {
        'model_config_hash': sha256_file(config_path),
        'conditions_hash': sha256_file(conditions_path),
        'benchmark_hash': sha256_file(benchmark_path),
        'manifest_hash': hashlib.sha256(
            json.dumps(expanded_manifest, sort_keys=True, separators=(',', ':')).encode()
        ).hexdigest(),
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.unlink(missing_ok=True)
    errors = []
    traces = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as ex:
        futs = {ex.submit(generate_trace, spec, config, conditions, items, hashes): spec for spec in specs}
        for n, fut in enumerate(concurrent.futures.as_completed(futs), 1):
            spec = futs[fut]
            try:
                trace = fut.result()
                traces.append(trace)
                print(
                    f"[{n}/{len(specs)} traces] OK {spec['item_id']} {spec['family']} t{spec['trial']}",
                    flush=True,
                )
            except Exception as err:
                errors.append({'spec': spec, 'error': repr(err)})
                print(f"[{n}/{len(specs)} traces] ERROR {spec}: {err}", file=sys.stderr, flush=True)

    if errors:
        err_path = out_path.with_suffix(out_path.suffix + '.errors.json')
        err_path.write_text(json.dumps(errors, ensure_ascii=False, indent=2), encoding='utf-8')
        raise SystemExit(f'{len(errors)} unique trace(s) failed; see {err_path}')

    records = []
    for trace in traces:
        records.extend(expand_trace(trace, conditions))
    records.sort(key=lambda r: (r['item_id'], r['condition'], r['trial']))

    if len(records) != 252:
        raise SystemExit(f'Expected 252 condition cells, got {len(records)}')
    unique_trace_ids = {r['shared_trace_id'] for r in records}
    if len(unique_trace_ids) != 108:
        raise SystemExit(f'Expected 108 unique API traces, got {len(unique_trace_ids)}')

    with out_path.open('w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

    print(f'Completed {len(unique_trace_ids)} unique API traces -> {len(records)} condition cells', flush=True)


if __name__ == '__main__':
    main()
