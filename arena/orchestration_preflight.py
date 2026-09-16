#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from .core import stable_hash
from .io_utils import load_json
from .orchestration_compare import build_comparison_record, verify_comparison_record
from .providers import ScriptedProvider
from .engine import run_arena_once
from .structured_routing import run_structured_once


ROOT = Path(__file__).resolve().parents[1]


def _free_script():
    return [
        {
            'decision_summary': 'activate core specialists',
            'actions': [
                {'type': 'invoke_agent', 'agent_id': 'ads', 'request': 'Assess media efficiency for the 7-day plan.'},
                {'type': 'invoke_agent', 'agent_id': 'inventory', 'request': 'Assess stockout and replenishment constraints.'},
                {'type': 'invoke_agent', 'agent_id': 'finance', 'request': 'Assess contribution and downside constraints.'},
            ],
        },
        {
            'decision_summary': 'media assessment and extra pricing expansion',
            'actions': [
                {'type': 'invoke_agent', 'agent_id': 'pricing', 'request': 'Also inspect pricing mechanics before finalizing.'},
                {
                    'type': 'write_state',
                    'key': 'media_view',
                    'value': 'A is the strongest incremental media candidate',
                    'status': 'provisional',
                    'basis': 'incremental ROAS',
                },
                {'type': 'message', 'to': 'ops_lead', 'content': 'Media view recorded; I also asked pricing for a cross-check.'},
            ],
        },
        {
            'decision_summary': 'inventory assessment',
            'actions': [
                {
                    'type': 'write_state',
                    'key': 'inventory_view',
                    'value': 'A requires conservative allocation because lead time exceeds the 7-day window',
                    'status': 'provisional',
                    'basis': 'stock and supplier lead time',
                },
                {'type': 'message', 'to': 'ops_lead', 'content': 'Inventory constraint recorded.'},
            ],
        },
        {
            'decision_summary': 'finance assessment',
            'actions': [
                {
                    'type': 'write_state',
                    'key': 'finance_view',
                    'value': 'Protect blended ROAS and contribution while discounting conservatively',
                    'status': 'provisional',
                    'basis': 'margin and ROAS constraints',
                },
                {'type': 'message', 'to': 'ops_lead', 'content': 'Finance constraint recorded.'},
            ],
        },
        {
            'decision_summary': 'pricing cross-check',
            'actions': [
                {
                    'type': 'write_state',
                    'key': 'pricing_view',
                    'value': 'Keep A discount modest and avoid widening scope beyond the 7-day plan',
                    'status': 'provisional',
                    'basis': 'competitor price index',
                },
                {'type': 'message', 'to': 'ops_lead', 'content': 'Pricing cross-check recorded.'},
            ],
        },
        {
            'decision_summary': 'integrate and finalize',
            'actions': [
                {
                    'type': 'write_state',
                    'key': 'integrated_plan',
                    'value': 'Executable 7-day plan from media, inventory, finance, and pricing inputs',
                    'status': 'recommendation',
                    'basis': 'recorded specialist contributions',
                },
                {'type': 'finalize', 'answer': 'Initial free-routing plan.'},
            ],
        },
        {
            'decision_summary': 'handle late preliminary inventory signal',
            'actions': [
                {
                    'type': 'revise_final_state',
                    'patch': {'inventory_view': 'A preliminary stock signal requires bounded adjustment'},
                    'reason': 'late preliminary inventory signal',
                    'status': 'provisional',
                },
                {'type': 'finalize', 'answer': 'Updated free-routing plan.'},
            ],
        },
    ]


def _structured_script():
    return [
        {
            'decision_summary': 'media assessment with attempted extra pricing call',
            'actions': [
                {'type': 'invoke_agent', 'agent_id': 'pricing', 'request': 'Also inspect pricing mechanics before finalizing.'},
                {
                    'type': 'write_state',
                    'key': 'media_view',
                    'value': 'A is the strongest incremental media candidate',
                    'status': 'provisional',
                    'basis': 'incremental ROAS',
                },
            ],
        },
        {
            'decision_summary': 'inventory assessment',
            'actions': [
                {
                    'type': 'write_state',
                    'key': 'inventory_view',
                    'value': 'A requires conservative allocation because lead time exceeds the 7-day window',
                    'status': 'provisional',
                    'basis': 'stock and supplier lead time',
                }
            ],
        },
        {
            'decision_summary': 'finance assessment',
            'actions': [
                {
                    'type': 'write_state',
                    'key': 'finance_view',
                    'value': 'Protect blended ROAS and contribution while discounting conservatively',
                    'status': 'provisional',
                    'basis': 'margin and ROAS constraints',
                }
            ],
        },
        {
            'decision_summary': 'integrate and finalize',
            'actions': [
                {
                    'type': 'write_state',
                    'key': 'integrated_plan',
                    'value': 'Executable 7-day plan from the fixed media, inventory, and finance stages',
                    'status': 'recommendation',
                    'basis': 'recorded stage contributions',
                },
                {'type': 'finalize', 'answer': 'Initial structured-routing plan.'},
            ],
        },
        {
            'decision_summary': 'handle late preliminary inventory signal',
            'actions': [
                {
                    'type': 'revise_final_state',
                    'patch': {'inventory_view': 'A preliminary stock signal requires bounded adjustment'},
                    'reason': 'late preliminary inventory signal',
                    'status': 'provisional',
                },
                {'type': 'finalize', 'answer': 'Updated structured-routing plan.'},
            ],
        },
    ]


def build_offline_preflight():
    domain = load_json(ROOT / 'arena/domains/ecommerce.json')
    config = load_json(ROOT / 'arena/config/arena_v0.3.json')
    policy = load_json(ROOT / 'arena/config/structured_ecommerce_v0.1.json')

    free_script = _free_script()
    structured_script = _structured_script()

    free_trace = run_arena_once(
        domain,
        config,
        ScriptedProvider(free_script),
        'orchestration-preflight-free-v01',
        logical_seed=1,
    )
    structured_trace = run_structured_once(
        domain,
        config,
        ScriptedProvider(structured_script),
        policy,
        'orchestration-preflight-structured-v01',
        logical_seed=1,
    )

    fixture_identity = {
        'kind': 'SCRIPTED_OFFLINE_PREFLIGHT_ONLY',
        'free_script_hash': stable_hash(free_script),
        'structured_script_hash': stable_hash(structured_script),
        'scripts_identical': free_script == structured_script,
        'note': (
            'Scripts intentionally differ where needed to exercise each orchestration mechanic. '
            'This artifact validates evidence shape and control behavior only and is not a scientific A/B estimate.'
        ),
    }
    comparison = build_comparison_record(
        free_trace,
        structured_trace,
        comparison_id='R7-OFFLINE-ORCHESTRATION-PREFLIGHT-v0.1',
        fixture_identity=fixture_identity,
        code_identity={'source': 'repository_main_at_execution'},
    )
    verify_comparison_record(comparison)

    if free_trace['run_status'] != 'RUN_COMPLETE':
        raise RuntimeError('free_preflight_not_complete:' + str(free_trace['run_status']))
    if structured_trace['run_status'] != 'RUN_COMPLETE':
        raise RuntimeError('structured_preflight_not_complete:' + str(structured_trace['run_status']))

    free_proposal = comparison['conditions']['free']['proposal_realization']
    structured_proposal = comparison['conditions']['structured']['proposal_realization']
    if free_proposal['realized_invoke_count'] < 1:
        raise RuntimeError('free_preflight_expected_realized_invocation')
    if structured_proposal['proposal_invoke_count'] < 1:
        raise RuntimeError('structured_preflight_expected_invocation_proposal')
    if structured_proposal['policy_blocked_invoke_count'] < 1:
        raise RuntimeError('structured_preflight_expected_blocked_invocation')
    if structured_proposal['realized_invoke_count'] != 0:
        raise RuntimeError('structured_preflight_invocation_should_not_realize')

    return free_trace, structured_trace, comparison


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def _human_summary(comparison):
    free = comparison['conditions']['free']
    structured = comparison['conditions']['structured']
    fpr = free['proposal_realization']
    spr = structured['proposal_realization']
    lines = [
        'R7 OFFLINE ORCHESTRATION PREFLIGHT v0.1',
        'STATUS: ENGINEERING ONLY — NOT SCIENTIFIC EVIDENCE',
        '',
        f"same_task_hash={comparison['same_task_hash']}",
        f"same_agent_registry_hash={comparison['same_agent_registry_hash']}",
        f"free_run_status={free['run_status']} turns={free['turns']}",
        f"structured_run_status={structured['run_status']} turns={structured['turns']}",
        f"free_proposed_invocations={fpr['proposal_invoke_count']} realized_invocations={fpr['realized_invoke_count']}",
        f"structured_proposed_invocations={spr['proposal_invoke_count']} blocked_invocations={spr['policy_blocked_invoke_count']} realized_invocations={spr['realized_invoke_count']}",
        '',
        'Interpretation boundary:',
        comparison['interpretation_boundary'],
    ]
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--outdir', default='results/orchestration_preflight')
    args = parser.parse_args()

    free_trace, structured_trace, comparison = build_offline_preflight()
    outdir = Path(args.outdir)
    _write_json(outdir / 'free_trace.json', free_trace)
    _write_json(outdir / 'structured_trace.json', structured_trace)
    _write_json(outdir / 'comparison.json', comparison)
    (outdir / 'SUMMARY.txt').write_text(_human_summary(comparison), encoding='utf-8')

    print(_human_summary(comparison), end='')
    print('comparison_hash=' + comparison['comparison_hash'])


if __name__ == '__main__':
    main()
