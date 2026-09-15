#!/usr/bin/env python3
"""Minimal Bailian business-space OpenAI-compatible transport.

Credentials/routing are runtime-only. Thinking controls are explicit optional
transport parameters so experiments can freeze the semantic-instrument mode.
"""
import json, os, time, urllib.error, urllib.request
class BailianError(RuntimeError): pass

def _post_json(url,api_key,payload,timeout=120,max_retries=2,backoff=2):
 body=json.dumps(payload,ensure_ascii=False).encode('utf-8');last=None
 for attempt in range(max_retries):
  req=urllib.request.Request(url,data=body,method='POST',headers={'Authorization':f'Bearer {api_key}','Content-Type':'application/json','Accept':'application/json','Connection':'close','User-Agent':'reality-bias-benchmark-bailian/0.2'})
  started=time.time()
  try:
   with urllib.request.urlopen(req,timeout=timeout) as resp:obj=json.loads(resp.read().decode('utf-8'))
   obj['_transport_latency_ms']=round((time.time()-started)*1000,2)
   if isinstance(obj,dict) and obj.get('error') is not None and 'choices' not in obj:raise BailianError('Bailian application error: '+json.dumps(obj['error'],ensure_ascii=False))
   return obj
  except urllib.error.HTTPError as e:
   detail=e.read().decode('utf-8',errors='replace');last=BailianError(f'HTTP {e.code}: {detail[:1500]}')
   if e.code not in (408,409,429,500,502,503,504):raise last
  except BailianError:raise
  except Exception as e:last=e
  if attempt+1<max_retries:time.sleep(backoff*(2**attempt))
 raise BailianError(f'Bailian request failed after {max_retries} attempts: {last}')
def extract_content(response):
 try:return response['choices'][0]['message'].get('content') or ''
 except Exception as e:raise BailianError(f'Unexpected response shape: {e}; keys={list(response.keys())}')
def chat_completion(messages,*,response_format_json=False,max_tokens=4096,temperature=0.0,enable_thinking=None,thinking_budget=None):
 api_key=os.environ.get('BAI');base_url=(os.environ.get('BAILIAN_BASE_URL') or '').rstrip('/');model=os.environ.get('BAILIAN_MODEL')
 if not api_key:raise BailianError('BAI is not set')
 if not base_url:raise BailianError('BAILIAN_BASE_URL is not set')
 if not model:raise BailianError('BAILIAN_MODEL is not set')
 payload={'model':model,'messages':messages,'max_tokens':max_tokens,'temperature':temperature}
 if response_format_json:payload['response_format']={'type':'json_object'}
 if enable_thinking is not None:payload['enable_thinking']=bool(enable_thinking)
 if thinking_budget is not None:payload['thinking_budget']=int(thinking_budget)
 return _post_json(base_url+'/chat/completions',api_key,payload)
