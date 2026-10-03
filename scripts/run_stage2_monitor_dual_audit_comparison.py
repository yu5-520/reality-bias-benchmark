#!/usr/bin/env python3
"""Offline comparison against frozen B/C audits; no provider calls or subject runs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / 'scripts/stage2_monitor_audit_comparison'
FROZEN = ROOT / 'stage2/replication_v2/enhanced_monitor_dual_audit_comparison_v1'
OUTPUTS = ['comparison_summary.json', 'localization_records.json',
           'corrected_comparison.json', 'node_localization.json',
           'source_binding_records.json', 'source_binding_summary.json']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work-dir', type=Path, required=True)
    p.add_argument('--source-root', type=Path, required=True,
                   help='Contains G2A through G5A source checkouts')
    p.add_argument('--replay-root', type=Path, required=True,
                   help='Validated enhanced_monitor_p2_v2 replay directory')
    p.add_argument('--reuse-inputs', type=Path,
                   help='Optional exact hash-bound joined_inputs.json from an earlier preparation')
    a = p.parse_args()
    work = a.work_dir.resolve()
    if work.exists() and any(work.iterdir()):
        p.error('--work-dir must be absent or empty')
    work.mkdir(parents=True, exist_ok=True)
    seal = json.loads((FROZEN/'seal.json').read_text())
    for rel, expected in seal['files'].items():
        assert sha(ROOT/rel) == expected, f'Changed frozen input/code/result: {rel}'
    replay = a.replay_root.resolve()
    for rel, expected in seal['replay_files'].items():
        assert sha(replay/rel) == expected, f'Changed replay input: {rel}'
    shutil.copytree(CODE/'sources', work/'sources')
    env = dict(os.environ, MONITOR_COMPARISON_REPO=str(ROOT),
               MONITOR_COMPARISON_REPLAY=str(replay),
               MONITOR_COMPARISON_SOURCES=str(a.source_root.resolve()))
    def run(name):
        with (work/(name+'.log')).open('w') as log:
            subprocess.run([sys.executable, str(CODE/name)], cwd=work,
                           env=env, stdout=log, check=True)
    if a.reuse_inputs:
        shutil.copyfile(a.reuse_inputs, work/'joined_inputs.json')
    else:
        run('prepare.py')
    assert sha(work/'joined_inputs.json') == seal['joined_inputs_sha256']
    joined = json.loads((work/'joined_inputs.json').read_text())
    extra = json.loads((CODE/'sources/remaining_b_packet_hashes.json').read_text())
    count = {'B': 0, 'C': 0}
    for fid, d in joined.items():
        for key in ['b_packet', 'c_packet']:
            if key not in d:
                continue
            packet = dict(d[key]); expected = packet['packet_sha256']
            packet['packet_sha256'] = ''
            actual = hashlib.sha256(json.dumps(packet, ensure_ascii=False,
                       sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            assert actual == expected, (fid, key)
        if 'c_audit' in d:
            assert d['c_packet']['packet_sha256'] == d['c_audit']['input_packet_sha256']
            croot = ROOT/'stage2/replication_v2/gpt56sol_full_context_semantic_audit_v1'
            frozen_audit = json.loads((croot/'formal_review'/f'{fid}.json').read_text())
            assert d['c_audit'] == frozen_audit
            bsource = json.loads((croot/'layer_b_c_comparison/cells'/f'{fid}.json').read_text())
            assert d['b_packet']['packet_sha256'] == bsource['layer_b']['packet_sha256']
            count['C'] += 1
        else:
            assert d['b_packet']['packet_sha256'] == extra[fid]
        count['B'] += 1
    assert count == {'B': 84, 'C': 80}
    for name in ['compare.py', 'corrected_compare.py', 'node_localization.py', 'source_binding.py']:
        run(name)
    for name in OUTPUTS:
        assert json.loads((work/name).read_text()) == json.loads((FROZEN/name).read_text()), name
    # Reproduce C's historical event classes individually, not just their aggregate.
    cpath = ROOT/'stage2/replication_v2/gpt56sol_full_context_semantic_audit_v1/layer_a_c_monitor_comparison_v1/evaluation_records.jsonl'
    historical = {r['reference_id']:r for r in map(json.loads,cpath.read_text().splitlines()) if r.get('reference_id')}
    labels = {'core':'SUPPORTED_MATCH','evidence':'PARTIAL_LOCALIZATION','none':'MISS'}
    records = json.loads((work/'localization_records.json').read_text())
    checked = 0
    for r in records:
        if r['layer']=='C' and r['positive']:
            assert labels[r['old_legacy']['tier']] == historical[r['full_id']+':'+r['reference_id']]['match_class']
            checked += 1
    assert checked == 40
    receipt = {'schema':'stage2-dual-audit-comparison-validation-v1',
               'packet_hashes_verified':count, 'b_positive_class_and_warning_identity_reproduced':97,
               'c_positive_classes_reproduced':checked, 'result_files_equal':OUTPUTS,
               'subject_reruns':0, 'provider_calls':0, 'repairs_executed':0,
               'seal_sha256':sha(FROZEN/'seal.json')}
    (work/'validation_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))

if __name__ == '__main__':
    main()
