#!/usr/bin/env python3
"""Offline replay only: no providers, subjects, evaluators or repair execution."""
from __future__ import annotations
import argparse
import gzip
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from stage2.r7_checkpoint_v1.common import digest, stable_json_bytes
from stage2.monitor_enhancement.frozen_archive import NativeArchive
from stage2.monitor_enhancement.evidence_graph import EvidenceGraph
from stage2.monitor_enhancement.replay_analysis import select_candidates, add_unknown_edges, evaluate_corrected_reference
from stage2.monitor_enhancement.route_export import export_observation_map


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n')


def write_gzip(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = gzip.compress(stable_json_bytes(value), mtime=0)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_bytes(raw)
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sources-root', type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists(): raise FileExistsError('use a fresh derived-output directory')
    config_path = ROOT / 'configs/stage2_p2_evidence_graph_replay_v2.json'
    config = json.loads(config_path.read_bytes())
    source = ROOT / config['source_bindings']['path']
    if digest(source.read_bytes()) != config['source_bindings']['sha256']:
        raise ValueError('frozen source bindings changed')
    bindings = json.loads(source.read_bytes())
    expected = {f'G{g}-X{x}-T{t}' for g in range(2,6) for x in range(1,8) for t in range(1,4)}
    if len(bindings) != 84 or {r['full_id'] for r in bindings} != expected:
        raise ValueError('population mismatch')
    args.out.mkdir(parents=True)
    implementation = sorted(set([Path(__file__).relative_to(ROOT), config_path.relative_to(ROOT),
        Path('arena/checkpoint_chronology.py'), Path('stage2/r7_checkpoint_v1/common.py'),
        Path('scripts/validate_stage2_p2_replay_v2.py'), Path('scripts/inspect_stage2_evidence_graph.py')] +
        [p.relative_to(ROOT) for p in (ROOT/'stage2/monitor_enhancement').glob('*.py')]))
    write_json(args.out/'run_binding.json', {'source_base_commit': subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'implementation_sha256': {str(p): digest((ROOT/p).read_bytes()) for p in implementation},
        'contract_sha256': digest(config_path.read_bytes()), 'execution': config['execution']})
    cells, candidates, old_hashes, ref_sets = [], [], set(), {}
    totals = Counter()
    for b in sorted(bindings, key=lambda r:r['full_id']):
        full_id, group, cell = b['full_id'], b['group_id'], b['cell_id']
        base = args.sources_root/(group+'A') if args.sources_root else ROOT
        path = base/f'stage2/replication_v2/{group}/natural_A/{cell}/first_attempt.tar.gz'
        ar = NativeArchive(path, full_id, b['archive_sha256'])
        observations, coverage, sources = ar.build(); resolved = ar.verify_observations()
        builder = EvidenceGraph()
        for obs in observations: builder.add_observation(obs)
        graph = builder.snapshot()
        selected = select_candidates(graph, **config['candidate_rules'])
        add_unknown_edges(builder, graph, selected); graph = builder.snapshot()
        write_gzip(args.out/f'graphs/{full_id}.json.gz', {'full_id':full_id, 'graph':graph, 'source_index': sources})
        if full_id in config['priority_route_maps']:
            write_gzip(args.out/f'route_maps/{full_id}.json.gz', export_observation_map(graph))
        # Legacy candidates are read only after the new graph/candidates are fixed.
        missing_old = 'monitor_candidates.json' not in ar.members
        if missing_old and not coverage.get('failed_attempt_without_terminal_record'):
            raise ValueError('unexplained absent old monitor artifact')
        old = [] if missing_old else ar.json('monitor_candidates.json')
        if not isinstance(old,list): raise ValueError('old candidates must be a list')
        old_hashes.update(r['candidate_hash'] for r in old)
        refs = {n['ref'] for n in graph['nodes'] if n['node_type'] != 'EVENT'}
        ref_sets[full_id] = {'graph':refs, 'old':{r['object_ref'] for r in old}, 'new':{r['object_ref'] for r in selected}}
        row = {**{k:b[k] for k in ('full_id','group_id','cell_id','archive_sha256')},
               'coverage':coverage, 'observation_count':len(observations), 'resolved_observation_count':resolved,
               'graph_hash':graph['graph_hash'], 'graph_node_count':len(graph['nodes']), 'graph_edge_count':len(graph['edges']),
               'candidate_count':len(selected), 'old_candidate_count':len(old), 'old_candidate_artifact_absent':missing_old,
               'attempt_receipt':ar.attempt_receipt}
        cells.append(row); candidates.extend({'full_id':full_id, **r} for r in selected)
        totals.update(coverage); totals.update(observations=len(observations), resolved_observations=resolved,
             nodes=len(graph['nodes']), edges=len(graph['edges']), candidates=len(selected), old_candidate_records=len(old))
        print(full_id, 'native=',coverage['native_records'],'fields=',len(observations),flush=True)
        ar.tf.close()
    if totals['old_candidate_records'] != 996 or len(old_hashes) != 955:
        raise ValueError('frozen legacy candidate identity/count mismatch')
    # Semantic references are loaded only after all graphs have been fixed.
    reference = ROOT / config['corrected_reference']['path']
    if digest(reference.read_bytes()) != config['corrected_reference']['sha256']: raise ValueError('reference changed')
    reviews = json.loads(reference.read_bytes())
    comparison = evaluate_corrected_reference(reviews, ref_sets)
    strata = defaultdict(Counter)
    for r in comparison:
        strata[r['reviewed_status']]['records'] += 1
        for k, matches in r['matches'].items(): strata[r['reviewed_status']][k+'_exact_file_mention'] += bool(matches)
    summary = {'schema':'RB-STAGE2-P2-CORRECTED-REPLAY-v2','trajectories':len(cells),'totals':dict(totals),
               'old_unique_candidate_hashes':len(old_hashes), 'reference_records':len(reviews),
               'reference_strata':dict(strata),'execution':config['execution'],
               'claims':{'detector_superiority_established':False,'live_monitoring_tested':False,
                         'authority_transitions_automatically_identified':False,'route_repair_efficacy_tested':False}}
    write_json(args.out/'summary.json',summary); write_json(args.out/'cell_summary.json',cells)
    for name, rows in [('candidate_objects.jsonl',candidates),('reference_comparison.jsonl',comparison)]:
        (args.out/name).write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rows))
    write_json(args.out/'old_candidate_hashes.json', sorted(old_hashes))
    report = '# Corrected native evidence replay\n\n'
    report += f"84 frozen trajectories; {totals['native_records']:,} native capture records; {totals['observations']:,} field-bound observations. All observation locators and value hashes resolved against their source archives.\n\n"
    report += 'The v1 replay used an incompatible legacy archive adapter. Its graph promotion and old/new localization comparison are withdrawn; frozen historical files remain unchanged.\n\n'
    report += 'Capture records, field observations, snapshot states and inspection candidates are different units. Repeated captures (including post-round memory copies) do not establish new messages, semantic adoption or causal dependency.\n\n'
    report += 'Each clock is local to its producer. The six complete maps are retrospective observation maps with no write authorization. Native-state decoding is limited to declared carriers and host inbox snapshots; it is not a complete model-internal trace.\n\n'
    report += 'The 65 targeted corrected reviews are evaluated separately by status using exact file mentions in corrected rationales only. This proxy is neither event localization nor recall. No detector superiority, live performance or route-repair benefit is established.\n\n'
    report += '```json\n' + json.dumps(summary,indent=2) + '\n```\n'
    (args.out/'P2_Corrected_Replay_Report.md').write_text(report)
    write_json(args.out/'manifest.json',{'schema':'RB-P2-FILE-MANIFEST-v2','files':{
        str(p.relative_to(args.out)):{'bytes':p.stat().st_size,'sha256':digest(p.read_bytes())}
        for p in sorted(args.out.rglob('*')) if p.is_file()}})


if __name__ == '__main__': main()
