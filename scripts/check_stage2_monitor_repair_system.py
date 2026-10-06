#!/usr/bin/env python3
"""Reproduce automatic offline coordination; no agent, model or natural rerun."""
import argparse
import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from stage2.r7_checkpoint_v1.common import digest
from stage2.route_repair.branch_fields import save, require, verify_seal
from stage2.route_repair.route_context import CompleteRouteContext
from stage2.route_repair.checkout_route_probe import probe
from stage2.route_repair.offline_system import OfflineRouteRepairSystem


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', required=True, type=Path)
    parser.add_argument('--graph-root', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--compare-frozen', action='store_true')
    args = parser.parse_args()
    if args.out.exists():
        parser.error('fresh output required; use read-only recovery for interrupted branches')
    case = next(c for c in json.loads((ROOT / 'configs/stage2_terminal_route_repair_first_round_v1.json').read_text())['cases']
                if c['full_id'] == 'G3-X4-T2')
    with gzip.open(args.graph_root / 'G3-X4-T2.json.gz') as stream:
        graph = json.load(stream)['graph']
    archive = args.source_root / 'G3A/stage2/replication_v2/G3/natural_A/X4-T2/first_attempt.tar.gz'
    context = CompleteRouteContext(graph, archive, case)
    try:
        prior = ROOT / 'stage2/replication_v2/route_planning_session_integration_v1'
        prior_seal = json.loads((prior / 'seal.json').read_text())
        verify_seal(prior_seal, 'seal_hash')
        for path, expected in prior_seal['artifact_hashes'].items():
            require(digest((prior / path).read_bytes()) == expected, 'PLANNING_ARTIFACT_HASH_DRIFT')
        for path, expected in {**prior_seal['implementation_hashes'], **prior_seal['input_hashes']}.items():
            require(digest((ROOT / path).read_bytes()) == expected, 'PLANNING_DEPENDENCY_HASH_DRIFT:' + path)
        bundle = json.loads((prior / 'planning_bundle.json').read_text())
        policy_root = ROOT / 'stage2/replication_v2/source_based_host_branch_integration_v1'
        application_policy = json.loads((policy_root / 'plan.json').read_text())['policy']
        host_policy = json.loads((policy_root / 'combined_plan.json').read_text())['host_answer_policy']
        task = bundle['proposal']['verification_tasks'][0]
        def verify_route(root):
            result = probe(root)
            passed = (result['controlled_launcher_selection'] == {'UNSET': ['current'], 'on': ['legacy'], 'off': ['current']}
                      and all(r['status'] == 200 and r['body'] == {
                          'status': 'pending_payment', 'amount_cents': 2500, 'method': r['method']}
                          for r in result['http_handler_contracts']['current'])
                      and all(r['status'] == 410 for r in result['http_handler_contracts']['legacy']))
            return {'passed': passed, 'controlled_probe': result,
                    'scope': 'TWO_METHODS_ONE_CART_NOT_BROWSER_OR_REAL_PAYMENT'}
        bindings = {task['verification_id']: {'operation': task['operation'], 'refs': task['refs'],
                    'postcondition': task['postcondition'], 'run': verify_route}}
        system = OfflineRouteRepairSystem(context, bundle, args.out,
            application_policy=application_policy, host_policy=host_policy, verifiers=bindings)
        receipt = system.execute()
        require(receipt['status'] == 'AWAITING_NATIVE_CONTINUATION', 'SYSTEM_INTEGRATION_FAILED')
        require(receipt['native_application_writes'] == 1 and receipt['native_host_answer_supersessions'] == 1,
                'SYSTEM_NATIVE_ACTION_COUNT_DRIFT')
        require(not receipt['repair_success'] and not receipt['branch_promoted'] and receipt['live_provider_calls'] == 0,
                'SYSTEM_FALSE_COMPLETION')
        def current_hash(ref):
            return digest(system.host.current()) if ref == 'state:terminal' else digest(system.executor.checkout.read_file(ref[5:]).encode())
        save(args.out / 'recovery_assessment.json', system.journal.reconcile(current_hash))
        for name in ['full_graph_before.json', 'full_graph_after.json']:
            path = args.out / name
            (args.out / (name + '.gz')).write_bytes(gzip.compress(path.read_bytes(), mtime=0))
        if args.compare_frozen:
            frozen = ROOT / 'stage2/replication_v2/monitor_repair_system_integration_v1'
            sealed = json.loads((frozen / 'seal.json').read_text())
            verify_seal(sealed, 'seal_hash')
            for path, expected in {**sealed['implementation_hashes'], **sealed['input_hashes']}.items():
                require(digest((ROOT / path).read_bytes()) == expected, 'SYSTEM_DEPENDENCY_HASH_DRIFT:' + path)
            for path, expected in sealed['artifact_hashes'].items():
                require(digest((frozen / path).read_bytes()) == expected, 'SYSTEM_FROZEN_HASH_DRIFT:' + path)
                require((args.out / path).read_bytes() == (frozen / path).read_bytes(), 'SYSTEM_REPRODUCTION_DRIFT:' + path)
        print(json.dumps({'status': receipt['status'], 'system_receipt_hash': receipt['system_receipt_hash'],
                          'provider_calls': 0, 'repair_success': False, 'sealed_reproduction': args.compare_frozen}))
    finally:
        context.close()


if __name__ == '__main__':
    main()
