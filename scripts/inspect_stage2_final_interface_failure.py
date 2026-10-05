#!/usr/bin/env python3
"""Read-only replay of retained planning queries; no provider or native writes."""
import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_stage2_connected_repair import load_context
from stage2.route_repair.planning_session import RoutePlanningSession
from stage2.route_repair.branch_fields import BranchConstraintError, require
from stage2.route_repair.source_navigation import SourceNavigation

EXPECTED_ZIP_SHA = 'd28b12bbbe3b8b56580cf78766674529f50bf47d5449333ee7148c6c6b600292'


def inspect(artifact, source_root):
    raw = artifact.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == EXPECTED_ZIP_SHA, 'ORIGINAL_ARTIFACT_HASH_MISMATCH')
    context = load_context(source_root, 'mechanism')
    try:
        from stage2.native_v7.software_host_v1 import TASKS
        session = RoutePlanningSession(context, TASKS['T2'])
        records = []
        with zipfile.ZipFile(artifact) as archive:
            members = {n: hashlib.sha256(archive.read(n)).hexdigest() for n in archive.namelist() if not n.endswith('/')}
            response_names = sorted(n for n in members if '/planning_http/' in n and n.endswith('/response.bin'))
            require(len(response_names) == 2, 'EXPECTED_TWO_ORIGINAL_RESPONSES')
            for name in response_names:
                body = json.loads(archive.read(name))
                content = body['choices'][0]['message']['content']
                payload = json.loads(content)
                require(payload['kind'] == 'TOOL', 'EXPECTED_RETAINED_TOOL')
                tool, args = payload['name'], payload['arguments']
                row = {'response_member': name, 'response_sha256': members[name], 'original_content': content}
                require(tool in {'catalog', 'node', 'file', 'message', 'observation', 'span', 'witness'}, 'UNSUPPORTED_RETAINED_QUERY')
                try:
                    getattr(session, tool)(**args)
                    row['original_query_result'] = 'ACCEPTED'
                except BranchConstraintError as exc:
                    row['original_query_result'] = str(exc)
                if tool == 'file':
                    ref = args.get('ref'); cp = args.get('checkpoint_hash') or context.parent_checkpoint_hash
                    row['ref_is_known'] = ref in context.file_versions
                    row['checkpoint_is_known'] = cp in context.files_by_checkpoint
                    row['pair_is_known'] = isinstance(ref, str) and ref.startswith('file:') and ref[5:] in context.files_by_checkpoint.get(cp, {})
                    row['checkpoint_is_display_index'] = str(cp).isdigit()
                    row['checkpoint_is_boundary_label'] = cp in {'TASK_START', 'PARENT'}
                    # Resolve only an already-known object; never guess the requested time.
                    if ref in context.file_versions:
                        nav = SourceNavigation(context)
                        row['host_resolved_versions'] = nav.versions(ref)
                        read_session = RoutePlanningSession(context, TASKS['T2'])
                        for version in row['host_resolved_versions']['versions']:
                            nav.read(read_session, version['version_handle'])
                        row['all_listed_handles_read_verified'] = True
                records.append(row)
            outcomes = [n for n in members if n.endswith('/planning/outcome.json')]
            require(len(outcomes) == 1, 'EXACT_ORIGINAL_OUTCOME_REQUIRED')
            outcome = json.loads(archive.read(outcomes[0]))
        require(outcome['failure']['message'] == 'FILE_VERSION_OUTSIDE_VERIFIED_PREFIX', 'ORIGINAL_FAILURE_DRIFT')
        require(any(r['original_query_result'] == outcome['failure']['message'] for r in records), 'FAILURE_NOT_REPRODUCED')
        return {'schema': 'stage2-final-interface-failure-inspection-v1', 'original_run': 37231964981,
            'original_head': 'c1b9b80a31c10e661cafb6bb1ba99b2f47eead24', 'artifact_sha256': EXPECTED_ZIP_SHA,
            'member_hashes': members, 'queries': records, 'original_outcome': outcome,
            'offline_provider_calls': 0, 'native_writes': 0, 'natural_reruns': 0,
            'historical_failure_reclassified': False, 'semantic_efficacy_established': False}
    finally:
        context.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', type=Path, required=True)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = inspect(args.artifact, args.source_root)
    args.out.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
