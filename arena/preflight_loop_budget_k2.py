#!/usr/bin/env python3
"""Engineering-only K=2 runtime preflight. Never scientific evidence."""
import argparse
import json
from pathlib import Path

from arena.engine import run_arena_once
from arena.evidence import _objective_row
from arena.providers import ScriptedProvider
from arena.structural_feedback import derive_structural_feedback_rounds

ROOT = Path(__file__).resolve().parents[1]


def actions(*xs):
    return {'actions': list(xs)}


def finalize(answer):
    return {'type': 'finalize', 'answer': answer}


def invoke(agent):
    return {'type': 'invoke_agent', 'agent_id': agent, 'request': 'engineering-only structural return check'}


def build_trace():
    domain = json.loads((ROOT / 'arena/domains/ecommerce.json').read_text(encoding='utf-8'))
    config = json.loads((ROOT / 'arena/config/arena_v0.3_k2_candidate.json').read_text(encoding='utf-8'))
    scripted = [
        actions(invoke('inventory'), finalize('initial engineering plan')),
        actions(finalize('post-late engineering plan v1')),
        actions({'type': 'message', 'to': 'ops_lead', 'content': 'engineering return one'}),
        actions(
            {'type': 'revise_final_state', 'patch': {'decision': 'engineering-v2'}, 'reason': 'engineering return one'},
            invoke('inventory'),
        ),
        actions({'type': 'message', 'to': 'ops_lead', 'content': 'engineering return two'}),
        actions(invoke('risk'), finalize('engineering plan v3')),
        actions({'type': 'message', 'to': 'ops_lead', 'content': 'MUST NOT EXECUTE AFTER K2'}),
    ]
    provider = ScriptedProvider(scripted)
    trace = run_arena_once(domain, config, provider, 'engineering-k2-preflight', logical_seed=1)
    return trace, provider.index


def validate(trace, provider_calls):
    assert trace['run_status'] == 'LOOP_BUDGET_COMPLETE'
    assert trace['termination_reason'] == 'structural_feedback_round_limit_reached'
    assert trace['condition_complete'] is True
    assert trace['observation_censored'] is False
    assert trace['turns'] == 6
    assert provider_calls == 6
    assert trace['experimental_stop_policy'] == 'structural_feedback_round_limit'

    loop = trace['loop_budget']
    assert loop['enabled'] is True
    assert loop['semantic_blind'] is True
    assert loop['counter_version'] == 'R4-STRUCTURAL-FEEDBACK-ROUND-v0.2.1'
    assert loop['limit'] == 2
    assert loop['round_count'] == 2
    assert loop['reached'] is True
    assert loop['stop_applied'] is True
    assert loop['reached_at_turn'] == 6
    assert len(loop['round_ids']) == 2

    # Prove this is an experimental-condition stop rather than natural quiescence.
    assert 'risk' in trace['remaining_queue']
    assert 'risk' not in trace['executed_agents']
    assert trace['pending_invocations']

    derived = derive_structural_feedback_rounds(trace)
    assert derived['version'] == 'R4-STRUCTURAL-FEEDBACK-ROUND-v0.2.1'
    assert derived['round_count'] == 2
    for rnd in derived['rounds']:
        assert rnd['bias_labels'] == 'NOT_ADJUDICATED'
        assert rnd['authority_penetration'] == 'NOT_ADJUDICATED'
        assert rnd['semantic_dependency'] == 'NOT_ADJUDICATED'
        assert rnd['self_reinforcement'] == 'NOT_ADJUDICATED'
        assert rnd['anchor_actor'] == rnd['return_actor']
        assert rnd['anchor_actor'] != rnd['exposure_actor']

    obs = _objective_row(trace)['observation']
    assert obs['condition_complete'] is True
    assert obs['loop_budget_bounded'] is True
    assert obs['full_episode_observed'] is False
    assert obs['observation_censored'] is False
    assert obs['loop_budget_limit'] == 2
    assert obs['structural_feedback_rounds_observed'] == 2
    assert obs['negative_finding_scope'] == 'LOOP_BUDGET_CONDITION_ONLY'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out')
    args = ap.parse_args()
    trace, provider_calls = build_trace()
    validate(trace, provider_calls)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(trace, ensure_ascii=False, indent=2), encoding='utf-8')
    print('ENGINEERING_ONLY_NOT_SCIENTIFIC_EVIDENCE')
    print('K2 runtime preflight PASS')
    print(f"turns={trace['turns']} structural_rounds={trace['loop_budget']['round_count']} pending_queue={len(trace['remaining_queue'])}")


if __name__ == '__main__':
    main()
