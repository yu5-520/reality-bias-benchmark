#!/usr/bin/env python3
"""Read the retained first-attempt artifact; never dispatch or retry a model."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artifact-root', required=True, type=Path); args = p.parse_args()
    root = args.artifact_root / 'mechanism-first-attempt'
    paths = ['planning/outcome.json', 'planning/binding.json', 'planning/task_envelope.json',
             'planning_http/0001/request.bin', 'planning_http/0001/response.bin', 'planning_http/0001/receipt.json']
    for name in paths:
        path = root / name
        raw = path.read_bytes()
        obj = json.loads(raw)
        if name.endswith('request.bin'):
            # The complete original request remains in the artifact. Print its
            # hashes plus the actual schema/instructions at the failed boundary.
            request = json.loads(obj['messages'][1]['content'])
            value = {k: request[k] for k in ['instructions', 'output_schema', 'tools']}
        else: value = obj
        print(json.dumps({'retained_source': name, 'sha256': hashlib.sha256(raw).hexdigest(), 'value': value}, ensure_ascii=False))
    outcome = json.loads((root / 'planning/outcome.json').read_bytes())
    assert outcome['provider_calls'] == outcome['actor_calls'] == 1
    assert outcome['tool_queries'] == outcome['native_actions_executed'] == 0
    assert outcome['tools_revoked'] and outcome['state'] == 'FAILED'


if __name__ == '__main__': main()
