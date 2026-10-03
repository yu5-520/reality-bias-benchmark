#!/usr/bin/env python3
"""Zero-model field executor integration on a copy of a frozen MCP application.

These deliberately marked fixture changes are not a diagnosed repair and do not
measure efficacy. No historical trajectory, protocol or product code is changed.
"""
import argparse
import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from stage2.r7_checkpoint_v1.common import digest
from stage2.route_repair.route_context import CompleteRouteContext
from stage2.route_repair.branch_fields import (
    NativeFieldBranchExecutor, build_branch_policy, compile_branch_plan, save,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', required=True, type=Path)
    parser.add_argument('--graph-root', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        parser.error('fresh output required')
    cases = json.loads((ROOT/'configs/stage2_terminal_route_repair_first_round_v1.json').read_text())['cases']
    case = next(c for c in cases if c['full_id'] == 'G3-X4-T2')
    archive = args.source_root/'G3A/stage2/replication_v2/G3/natural_A/X4-T2/first_attempt.tar.gz'
    with gzip.open(args.graph_root/'G3-X4-T2.json.gz') as stream:
        graph = json.load(stream)['graph']
    context = CompleteRouteContext(graph, archive, case)
    try:
        refs = ['file:versions/after.json', 'file:web/app.js']
        version = json.loads(context.read_file(refs[0])['content'])
        # A mechanical test operation, explicitly outside semantic evaluation.
        key = next(k for k in sorted(version) if type(version[k]) is str)
        pointer = '/' + key.replace('~', '~0').replace('/', '~1')
        app = context.read_file(refs[1])['content']
        marker = 'Processing payment...'
        start = app.index(marker)
        end = start + len(marker)
        task = next(t for t in json.loads((ROOT/'stage2/tasks.json').read_text())['tasks'] if t['id'] == 'T2')
        policy = build_branch_policy(context, original_task=task,
            branch_id='G3-X4-T2-OFFLINE-FIELD-FIXTURE', semantic_id='MECHANICAL_FIXTURE_NOT_DIAGNOSIS',
            route_refs=refs, grants=[
                {'target_ref':refs[0], 'kind':'JSON_LEAF_REPLACE', 'pointer':pointer},
                {'target_ref':refs[1], 'kind':'TEXT_SPAN_REPLACE', 'start':start, 'end':end}],
            evidence=[context.read_file(ref)['source_locator'] for ref in refs])
        actions = [
            {'action_id':'fixture_json', 'target_ref':refs[0], 'kind':'JSON_LEAF_REPLACE',
             'pointer':pointer, 'before_value_hash':digest(version[key]),
             'value':version[key]+'-OFFLINE-FIXTURE', 'depends_on':[],
             'reason':'Mechanical leaf-write check only; not a finding or semantic repair.'},
            {'action_id':'fixture_text', 'target_ref':refs[1], 'kind':'TEXT_SPAN_REPLACE',
             'start':start, 'end':end, 'before_value_hash':digest(marker.encode()),
             'value':'Processing payment... [OFFLINE FIXTURE]', 'depends_on':['fixture_json'],
             'reason':'Mechanical ordered span-write check only; not a dependency inference.'}]
        plan = compile_branch_plan(context, policy, actions,
            preserve_refs=[ref for ref in context.file_versions if ref not in refs])
        executor = NativeFieldBranchExecutor(context, plan, args.out, trusted_policy=policy)
        result = executor.execute()
        if (result['status'] != 'PASS_OFFLINE_NATIVE_EXECUTION'
                or result['native_write_attempts'] != 2
                or not result['unrelated_application_preserved']
                or not result['historical_archive_preserved']):
            raise RuntimeError('field branch integration failed')
        receipt = {
            'schema':'stage2-field-branch-native-integration-v1',
            'classification':'OFFLINE_MECHANICAL_INTEGRATION_NOT_SEMANTIC_REPAIR',
            'full_id':case['full_id'], 'archive_sha256':case['archive_sha256'],
            'parent_checkpoint_hash':case['terminal_checkpoint_hash'],
            'policy_hash':policy['policy_hash'], 'plan_hash':plan['plan_hash'],
            'status':result['status'], 'native_write_attempts':result['native_write_attempts'],
            'unrelated_application_preserved':True, 'historical_archive_preserved':True,
            'graph_comparison':result['graph_comparison'], 'live_provider_calls':0,
            'semantic_repair_effect':'NOT_EVALUATED', 'native_agent_continuation_executed':False,
            'branch_promoted':False, 'private_product_code_imported':False,
        }
        save(args.out/'integration_receipt.json', receipt)
        print(json.dumps(receipt, ensure_ascii=False))
    finally:
        context.close()


if __name__ == '__main__':
    main()
