#!/usr/bin/env python3
"""Provider-independent serialized volume profile for Reviewer-v2 packets.

This intentionally reports UTF-8 bytes and Unicode character counts, not tokens and
not money. Provider tokenization/caching is a separate launch-time measurement.
"""
import argparse
import json
import math
from pathlib import Path

VERSION = 'R234-REVIEWER-V2-PACKET-VOLUME-v0.1'


def load_lines(path):
    return [line for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]


def percentile(sorted_values, q):
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return sorted_values[0]
    pos = (len(sorted_values) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    if lo == hi:
        return sorted_values[lo]
    frac = pos - lo
    return sorted_values[lo] * (1 - frac) + sorted_values[hi] * frac


def stats(values):
    ordered = sorted(values)
    return {
        'count': len(values),
        'sum': sum(values),
        'min': min(values) if values else None,
        'mean': (sum(values) / len(values)) if values else None,
        'median': percentile(ordered, 0.5),
        'p90': percentile(ordered, 0.9),
        'p95': percentile(ordered, 0.95),
        'max': max(values) if values else None,
    }


def profile_file(path, prompt_path=None):
    lines = load_lines(path)
    packet_chars = [len(line) for line in lines]
    packet_bytes = [len(line.encode('utf-8')) for line in lines]
    prompt_chars = 0
    prompt_bytes = 0
    if prompt_path:
        prompt = Path(prompt_path).read_text(encoding='utf-8')
        prompt_chars = len(prompt)
        prompt_bytes = len(prompt.encode('utf-8'))
    request_chars = [x + prompt_chars for x in packet_chars]
    request_bytes = [x + prompt_bytes for x in packet_bytes]
    return {
        'packet': {
            'characters': stats(packet_chars),
            'utf8_bytes': stats(packet_bytes),
        },
        'system_prompt': {
            'characters_per_request': prompt_chars,
            'utf8_bytes_per_request': prompt_bytes,
        },
        'request_without_provider_wrapper': {
            'characters': stats(request_chars),
            'utf8_bytes': stats(request_bytes),
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--r2', required=True)
    ap.add_argument('--r3', required=True)
    ap.add_argument('--r4', required=True)
    ap.add_argument('--r2-prompt', required=True)
    ap.add_argument('--r3-prompt', required=True)
    ap.add_argument('--r4-prompt', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    layers = {
        'R2': profile_file(args.r2, args.r2_prompt),
        'R3': profile_file(args.r3, args.r3_prompt),
        'R4': profile_file(args.r4, args.r4_prompt),
    }
    total_units = sum(x['packet']['characters']['count'] for x in layers.values())
    total_packet_chars = sum(x['packet']['characters']['sum'] for x in layers.values())
    total_packet_bytes = sum(x['packet']['utf8_bytes']['sum'] for x in layers.values())
    total_prompt_chars = sum(
        x['packet']['characters']['count'] * x['system_prompt']['characters_per_request']
        for x in layers.values()
    )
    total_prompt_bytes = sum(
        x['packet']['characters']['count'] * x['system_prompt']['utf8_bytes_per_request']
        for x in layers.values()
    )
    result = {
        'version': VERSION,
        'unit_count': total_units,
        'layers': layers,
        'full_population_serialized_request_volume_without_provider_wrapper': {
            'packet_characters': total_packet_chars,
            'system_prompt_characters': total_prompt_chars,
            'combined_characters': total_packet_chars + total_prompt_chars,
            'packet_utf8_bytes': total_packet_bytes,
            'system_prompt_utf8_bytes': total_prompt_bytes,
            'combined_utf8_bytes': total_packet_bytes + total_prompt_bytes,
        },
        'provider_calls': 0,
        'token_estimate_present': False,
        'monetary_estimate_present': False,
        'warnings': [
            'Character/byte volume is not provider token count.',
            'Provider wrappers, tokenizer behavior, prompt caching, output tokens, retries, and bounded expansions are excluded.',
            'Use this profile only to compare packet sizes and prepare a later provider-specific launch budget.'
        ],
    }
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
