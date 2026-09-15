#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from arena.core import validate_domain
from arena.io_utils import load_json
from arena.prompts import build_agent_messages


CURRENT_CONFIG = ROOT / 'arena/config/arena_v0.3.json'
EXPECTED_VERSION = 'R2-FREE-AGENT-ARENA-v0.3.2'


def main():
    config = load_json(CURRENT_CONFIG)
    assert config['version'] == EXPECTED_VERSION
    assert config['design'] == 'fixed_environment_free_routing'
    assert config['default_review_policy'] == 'no_automatic_paid_evaluator'
    assert config['termination_policy'] == 'observe_until_quiescent'
    assert config['trace_schema_version'] == 'R2-ARENA-TRACE-v0.3'
    assert config['evidence_policy'] == 'immutable_raw_evidence_deferred_adjudication'

    forbidden_terms = (
        'Reality Bias',
        'Completion Bias',
        'Perfection Bias',
        'Retrospective Bias',
        'Information Authority',
        'Invocation Authority',
        'Temporal Authority',
        'Escape Propensity',
        'Authority Penetration',
    )

    for domain_id in config['default_domains']:
        path = ROOT / f'arena/domains/{domain_id}.json'
        domain = load_json(path)
        validate_domain(domain)
        entry = next(a for a in domain['agents'] if a['id'] == domain['entry_agent'])
        msgs = build_agent_messages(domain, entry, {
            'shared_state': domain['task']['initial_shared_state'],
            'shared_state_metadata': {},
            'final_state': None,
            'inbox': [],
            'active_agents': [domain['entry_agent']],
            'remaining_turn_budget': config['max_turns'],
        })
        text = str(msgs)
        for forbidden in forbidden_terms:
            if forbidden in text:
                raise AssertionError(f'{domain_id} agent prompt leaked research label: {forbidden}')
        print(f"OK {domain_id}: agents={len(domain['agents'])}")

    print(f'environment validation PASS {EXPECTED_VERSION}')


if __name__ == '__main__':
    main()
