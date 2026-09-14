#!/usr/bin/env python3
import datetime as dt
import json
import os
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path


class DeepSeekError(RuntimeError):
    pass


_AUDIT_LOCK = threading.Lock()


def _post_json(url, api_key, payload, timeout=120, max_retries=3, backoff=2):
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    last = None
    for attempt in range(max_retries):
        req = urllib.request.Request(
            url,
            data=body,
            method='POST',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'reality-bias-benchmark/0.3.1'
            }
        )
        started = time.time()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode('utf-8')
            obj = json.loads(raw)
            obj['_transport_latency_ms'] = round((time.time() - started) * 1000, 2)
            return obj
        except urllib.error.HTTPError as e:
            detail = e.read().decode('utf-8', errors='replace')
            last = DeepSeekError(f'HTTP {e.code}: {detail[:1000]}')
            if e.code not in (408, 409, 429, 500, 502, 503, 504):
                raise last
        except Exception as e:
            last = e
        if attempt + 1 < max_retries:
            time.sleep(backoff * (2 ** attempt))
    raise DeepSeekError(f'DeepSeek request failed after {max_retries} attempts: {last}')


def _extract_content(response):
    try:
        return response['choices'][0]['message'].get('content') or ''
    except Exception as e:
        raise DeepSeekError(f'Unexpected response shape: {e}; keys={list(response.keys())}')


def _parse_json_text(text):
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        if '```' in text:
            for piece in text.split('```'):
                piece = piece.strip()
                if piece.startswith('json'):
                    piece = piece[4:].strip()
                try:
                    return json.loads(piece)
                except Exception:
                    pass
        raise


def _aggregate_usage(responses):
    keys = (
        'prompt_tokens', 'completion_tokens', 'total_tokens',
        'prompt_cache_hit_tokens', 'prompt_cache_miss_tokens'
    )
    return {
        key: sum(((r.get('usage') or {}).get(key, 0) or 0) for r in responses)
        for key in keys
    }


def _audit_format_retry(response, *, evaluator, attempt, error):
    record = {
        'timestamp_utc': dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z'),
        'evaluator': bool(evaluator),
        'attempt': attempt,
        'response_id': response.get('id'),
        'model': response.get('model'),
        'usage': response.get('usage') or {},
        'transport_latency_ms': response.get('_transport_latency_ms'),
        'parse_error': repr(error),
        'raw_text': _extract_content(response),
    }
    path = Path('results/json_format_retries.jsonl')
    path.parent.mkdir(parents=True, exist_ok=True)
    with _AUDIT_LOCK:
        with path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')


def chat_completion(config, messages, *, evaluator=False, response_format_json=False):
    api_key = os.environ.get('DEEPSEEK_API_KEY')
    if not api_key:
        raise DeepSeekError('DEEPSEEK_API_KEY is not set')

    section = config['evaluator'] if evaluator else config['subject']
    model = section.get('model_alias', config['model_alias'])
    payload = {
        'model': model,
        'messages': messages,
        'max_tokens': section['max_tokens'],
        'temperature': section['temperature'],
        'thinking': {'type': section['thinking']}
    }
    if response_format_json:
        payload['response_format'] = {'type': 'json_object'}

    url = config['base_url'].rstrip('/') + config['endpoint']
    t = config['transport']

    # Plain-text calls have no format retry layer.
    if not response_format_json:
        return _post_json(
            url, api_key, payload,
            timeout=t['timeout_seconds'],
            max_retries=t['max_retries'],
            backoff=t['retry_backoff_seconds']
        )

    # JSON-mode retries are infrastructure retries only. The exact same model,
    # messages, decoding parameters and response format are used on every try.
    max_format_attempts = int(config.get('json_format_retries', 3))
    responses = []
    last_error = None
    for attempt in range(1, max_format_attempts + 1):
        obj = _post_json(
            url, api_key, payload,
            timeout=t['timeout_seconds'],
            max_retries=t['max_retries'],
            backoff=t['retry_backoff_seconds']
        )
        responses.append(obj)
        try:
            _parse_json_text(_extract_content(obj))
            if len(responses) > 1:
                obj['usage'] = _aggregate_usage(responses)
                obj['_transport_latency_ms'] = sum((x.get('_transport_latency_ms') or 0) for x in responses)
            obj['_json_format_retry_count'] = len(responses) - 1
            return obj
        except Exception as e:
            last_error = e
            _audit_format_retry(obj, evaluator=evaluator, attempt=attempt, error=e)

    raise DeepSeekError(
        f'JSON response remained malformed after {max_format_attempts} identical-request attempts: {last_error}'
    )


def extract_content(response):
    return _extract_content(response)
