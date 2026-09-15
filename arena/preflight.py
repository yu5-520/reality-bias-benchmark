#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from arena.engine import run_arena_once
from arena.io_utils import load_json
from arena.providers import ScriptedProvider
from arena.topology import topology_metrics, participation_metrics


EXPECTED_VERSION = 'R2-FREE-AGENT-ARENA-v0.3.2'


def main():
    domain = load_json(ROOT / 'arena/domains/ecommerce.json')
    cfg = load_json(ROOT / 'arena/config/arena_v0.3.json')
    assert cfg['version'] == EXPECTED_VERSION
    assert cfg['termination_policy'] == 'observe_until_quiescent'
    scripted = [
        {
            'decision_summary': 'ask inventory',
            'actions': [
                {'type': 'invoke_agent', 'agent_id': 'inventory', 'request': 'Check stock and replenishment risk.'}
            ],
        },
        {
            'decision_summary': 'share inventory',
            'actions': [
                {
                    'type': 'write_state',
                    'key': 'inventory_view',
                    'value': 'A stock risk elevated',
                    'basis': 'supplier lead time and stock',
                    'status': 'recommendation',
                },
                {'type': 'message', 'to': 'ops_lead', 'content': 'A has the tightest stock coverage.'},
            ],
        },
        {
            'decision_summary': 'finalize first plan',
            'actions': [{'type': 'finalize', 'answer': 'Initial promotion plan.'}],
        },
        {
            'decision_summary': 'respond to late signal',
            'actions': [
                {
                    'type': 'revise_final_state',
                    'patch': {'inventory_view': 'A stock risk critical'},
                    'reason': 'new preliminary inventory signal',
                },
                {'type': 'finalize', 'answer': 'Updated promotion plan.'},
            ],
        },
    ]
    trace = run_arena_once(domain, cfg, ScriptedProvider(scripted), 'offline-preflight-v032', 1)
    types = [e['action_type'] for e in trace['events']]
    assert 'invoke_agent' in types
    assert 'write_state' in types
    assert 'late_event' in types
    assert 'revise_final_state' in types
    assert trace['run_status'] == 'RUN_COMPLETE'
    assert trace['review_status'] == 'PENDING_REVIEW'
    p = participation_metrics(trace)
    assert p['activated_agent_count'] >= 2
    assert p['executed_agent_count'] >= 2
    assert p['messages_read_into_model_input'] >= 2
    assert isinstance(trace['remaining_queue'], list)
    assert trace['trace_schema_version'] == 'R2-ARENA-TRACE-v0.3'
    m = topology_metrics(trace)
    print(f'offline engine preflight PASS {EXPECTED_VERSION}')
    print(
        f"events={len(trace['events'])} activated={p['activated_agent_count']} "
        f"executed={p['executed_agent_count']} turns={trace['turns']} "
        f"execution_edges={m['execution_edge_count']}"
    )


if __name__ == '__main__':
    main()
