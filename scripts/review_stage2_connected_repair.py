#!/usr/bin/env python3
"""Replay an independent reviewer's source queries and validate a supplied review.

The host fixes reviewer identity and criteria. This read-only second stage never
calls a provider, reruns the subject, edits the branch or fills missing evidence.
"""
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from stage2.route_repair.branch_fields import require, save
from stage2.route_repair.independent_review import RepairReviewContext, IndependentReviewerBinding
from stage2.route_repair.system_contract import read_capture_member
from scripts.run_stage2_connected_repair import load_context

REVIEWER_ID = 'INDEPENDENT_PROCESS_REVIEWER'


def submit(review, submission):
    """No report-supplied witness is trusted: all witnesses come from replay."""
    require(set(submission) == {'queries', 'report'}, 'EXACT_INDEPENDENT_REVIEW_SUBMISSION_REQUIRED')
    require(type(submission['queries']) is list and len(submission['queries']) <= 256,
            'INDEPENDENT_REVIEW_QUERY_BOUND')
    def inspect(context):
        for query in submission['queries']:
            require(set(query) == {'name', 'arguments'} and query['name'] in {'catalog', 'node', 'read', 'witness'},
                    'READ_ONLY_INDEPENDENT_REVIEW_TOOL_REQUIRED')
            expected = {'catalog': set(), 'node': {'ref'}, 'read': {'observation_id'},
                'witness': {'read_id', 'start', 'end'}}[query['name']]
            require(type(query['arguments']) is dict and set(query['arguments']) == expected,
                    'EXACT_INDEPENDENT_REVIEW_ARGUMENTS_REQUIRED')
            getattr(context, query['name'])(**query['arguments'])
        return submission['report']
    return review.evaluate(IndependentReviewerBinding(REVIEWER_ID, review._criteria_hash, inspect))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['source-root', 'branch', 'submission', 'out']:
        p.add_argument('--' + name, required=True, type=Path)
    args = p.parse_args(); require(not args.out.exists(), 'FRESH_INDEPENDENT_REVIEW_OUTPUT_REQUIRED')
    context = load_context(args.source_root, 'mechanism')
    def read(name): return json.loads((args.branch / name).read_bytes())
    try:
        review = RepairReviewContext(context, read('system_contract.json'), context.graph,
            read('full_graph_after.json'), read('continuation_assessment.json'),
            branch_source_reader=lambda row: read_capture_member(args.branch, row),
            semantic_rules=json.loads((ROOT / 'configs/r8_dynamic_semantic_audit_contract_v0.4.json').read_bytes()),
            lineage_rules=json.loads((ROOT / 'configs/stage2_r6_grade_semantic_audit_rules_v1.json').read_bytes()),
            repair_actor_id=read('provider_bindings.json')['profiles']['planning']['actor_id'])
        receipt = submit(review, json.loads(args.submission.read_bytes()))
        save(args.out / 'review_receipt.json', receipt)
        print(json.dumps({'status': receipt['status'],
            'repair_success_supported_by_bound_reviewer': receipt['repair_success_supported_by_bound_reviewer'],
            'semantic_truth_established_by_validator': False, 'provider_calls': 0}))
    finally: context.close()


if __name__ == '__main__': main()
