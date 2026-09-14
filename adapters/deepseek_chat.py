#!/usr/bin/env python3
import json, os, time, urllib.request, urllib.error

class DeepSeekError(RuntimeError):
    pass

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
                'User-Agent': 'reality-bias-benchmark/0.3'
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
    return _post_json(
        url, api_key, payload,
        timeout=t['timeout_seconds'],
        max_retries=t['max_retries'],
        backoff=t['retry_backoff_seconds']
    )

def extract_content(response):
    try:
        return response['choices'][0]['message'].get('content') or ''
    except Exception as e:
        raise DeepSeekError(f'Unexpected response shape: {e}; keys={list(response.keys())}')
