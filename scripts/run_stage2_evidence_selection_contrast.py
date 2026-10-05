#!/usr/bin/env python3
"""One-shot planning-only evidence-selection contrast on the frozen G3-X4-T2 prefix.

This runner changes only an appended planning instruction. It never dispatches
a repair, native subject continuation, or paid reviewer. The frozen v3 failure
is the A arm; this script is used once for the B arm.
"""
import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from stage2.native_v7.software_host_v1 import TASKS
from stage2.route_repair.branch_fields import require, save, seal
from stage2.route_repair.connected_provider import (
    DeepSeekHTTPTransport, LoopbackHTTPTransport, ConnectedExchangeSource,
    freeze_connected_bindings,
)
from stage2.route_repair.connected_planning import ConnectedPlanningSession, freeze_connected_envelope
from scripts.run_stage2_connected_repair import load_context

CONFIG = ROOT / 'configs/stage2_evidence_selection_gate_contrast_v1.json'
MECHANISM = ROOT / 'configs/stage2_connected_mechanism_v1.json'


def build(context, transport, out, instruction_suffix):
    bindings = freeze_connected_bindings(context, ROOT, transport)
    mechanism = json.loads(MECHANISM.read_bytes())
    envelope = freeze_connected_envelope(
        context, TASKS['T2'], writable_refs=[],
        message_fields=mechanism.get('message_fields'),
        branch_id='evidence-selection-gate-contrast',
        max_actions=mechanism['max_actions'],
        max_value_bytes=mechanism['max_value_bytes'])
    test_refs = sorted('file:' + p for p in context.parent['files']
                       if p.startswith('tests/') and p.endswith('.py'))
    require(test_refs, 'ORIGINAL_NATIVE_APPLICATION_TESTS_REQUIRED')
    cap = {'verification_id': 'VERIFY_NATIVE_TESTS', 'operation': 'HOST_DEFINED_OFFLINE_CHECK',
           'refs': test_refs, 'postcondition': 'Original native application tests pass.'}
    source = ConnectedExchangeSource(
        bindings['profiles']['planning'], transport, out / 'planning_http', gate=lambda: True)
    planning = ConnectedPlanningSession(
        context, envelope, source, out / 'planning',
        verification_capabilities=[cap], instruction_suffix=instruction_suffix)
    return planning, source, bindings


async def execute_once(context, out, instruction_suffix):
    transport = DeepSeekHTTPTransport()
    os.environ.pop('DEEPSEEK_API_KEY', None)
    planning, source, bindings = build(context, transport, out, instruction_suffix)
    error = None
    try:
        await planning.run()
    except BaseException as exc:
        error = {'error_type': type(exc).__name__, 'message': str(exc)}
    outcome = json.loads((out / 'planning/outcome.json').read_bytes())
    queries = json.loads((out / 'planning/query_log.json').read_bytes())
    witnesses = json.loads((out / 'planning/witnesses.json').read_bytes())
    summary = seal({
        'schema': 'stage2-evidence-selection-gate-contrast-result-v1',
        'classification': 'PLANNING_ONLY_SINGLE_VARIABLE_CONTRAST',
        'planning_state': outcome['state'], 'decision': outcome.get('decision'),
        'failure': outcome.get('failure') or error,
        'provider_calls': outcome['provider_calls'], 'transport_attempts': outcome['transport_attempts'],
        'tool_queries': outcome['tool_queries'],
        'query_operations': [q['operation'] for q in queries],
        'selected_witness_ids': sorted(witnesses),
        'selected_witness_refs': sorted({w['ref'] for w in witnesses.values()}),
        'authorization_created': outcome.get('authorization_hash') is not None,
        'native_actions_executed': 0, 'repair_dispatched': False,
        'subject_provider_calls': 0, 'paid_reviewer_calls': 0,
        'natural_reruns': 0, 'automatic_replay': False,
        'instruction_suffix_hash': planning._binding.get('experimental_instruction_suffix_hash'),
        'binding_hash': planning._binding['binding_hash'],
        'parent_checkpoint_hash': context.parent_checkpoint_hash,
        'graph_hash': context.graph['graph_hash'],
        'planning_profile_hash': bindings['profiles']['planning']['profile_hash'],
    }, 'summary_hash')
    save(out / 'summary.json', summary)
    print(json.dumps(summary))
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--execute', action='store_true')
    args = p.parse_args()
    require(not args.out.exists(), 'FRESH_EVIDENCE_SELECTION_CONTRAST_OUTPUT_REQUIRED')
    config = json.loads(CONFIG.read_bytes())
    suffix = config['instruction_suffix']
    context = load_context(args.source_root, 'mechanism')
    try:
        require(config['baseline']['run_id'] == 37324115903, 'FROZEN_BASELINE_RUN_DRIFT')
        require(config['planning_max_calls'] == 16, 'PLANNING_BUDGET_DRIFT')
        if not args.execute:
            planning, _, bindings = build(context, LoopbackHTTPTransport(18083), args.out, suffix)
            summary = seal({
                'schema': 'stage2-evidence-selection-gate-contrast-preflight-v1',
                'provider_calls': 0, 'execution_armed': False,
                'instruction_suffix_hash': planning._binding['experimental_instruction_suffix_hash'],
                'planning_profile_hash': bindings['profiles']['planning']['profile_hash'],
                'parent_checkpoint_hash': context.parent_checkpoint_hash,
                'graph_hash': context.graph['graph_hash'],
                'repair_dispatched': False, 'subject_provider_calls': 0,
                'paid_reviewer_calls': 0, 'natural_reruns': 0,
            }, 'preflight_hash')
            save(args.out / 'preflight.json', summary)
            print(json.dumps(summary))
            return
        asyncio.run(execute_once(context, args.out, suffix))
    finally:
        context.close()


if __name__ == '__main__':
    main()
