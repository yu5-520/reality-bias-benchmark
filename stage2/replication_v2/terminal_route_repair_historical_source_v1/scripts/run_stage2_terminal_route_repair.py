#!/usr/bin/env python3
"""Run the frozen LOCAL/GRAPH terminal comparison; no original subject reruns."""
import argparse,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from stage2.route_repair.terminal_runner import run_arm,save
from stage2.route_repair.terminal import exact_hash

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root',type=Path,required=True)
    p.add_argument('--graph-root',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--execute',action='store_true')
    a=p.parse_args();out=a.out.resolve()
    if out.exists():p.error('use a fresh output directory; attempts cannot be overwritten')
    out.mkdir(parents=True)
    config_path=ROOT/'configs/stage2_terminal_route_repair_first_round_v1.json'
    config=json.load(open(config_path))
    save(out/'run_binding.json',{'config_sha256':exact_hash(config_path),
        'implementation_sha256':{str(f.relative_to(ROOT)):exact_hash(f) for f in
            [Path(__file__),ROOT/'stage2/route_repair/terminal.py',ROOT/'stage2/route_repair/terminal_runner.py']},
        'mode':'ACTIVE' if a.execute else 'ZERO_CALL_PREFLIGHT','subject_reruns':0})
    if a.execute and not os.environ.get('DEEPSEEK_API_KEY'):
        save(out/'summary.json',{'status':'BLOCKED_PROVIDER_CREDENTIALS','provider_calls':0,'subject_reruns':0})
        print('BLOCKED_PROVIDER_CREDENTIALS: DEEPSEEK_API_KEY unavailable');return 2
    source_root=a.source_root.resolve();graph_root=a.graph_root.resolve()
    oldcwd=Path.cwd();oldpath=os.environ.get('PYTHONPATH')
    os.environ['PYTHONPATH']=str(ROOT)+(os.pathsep+oldpath if oldpath else '')
    rows=[]
    try:
        for case in config['cases']:
            g,c=case['full_id'].split('-',1)
            archive=source_root/(g+'A')/'stage2/replication_v2'/g/'natural_A'/c/'first_attempt.tar.gz'
            graph=graph_root/(case['full_id']+'.json.gz')
            for arm in config['arms']:
                dest=out/(case['full_id']+'-'+arm)
                # Keep provider error-format records within this new attempt.
                os.chdir(out)
                rows.append(run_arm(case,archive,graph,dest,arm,config['limits'],execute=a.execute))
                print(case['full_id'],arm,rows[-1]['status'],flush=True)
        summary={'schema':'stage2-terminal-route-repair-comparison-v1',
            'mode':'ACTIVE' if a.execute else 'ZERO_CALL_PREFLIGHT','arms':rows,
            'provider_calls':sum(r['provider_calls'] for r in rows),'subject_reruns':0,
            'semantic_effect':'AWAITING_SEPARATE_AUDIT' if a.execute else 'NOT_TESTED'}
        save(out/'summary.json',summary)
        return int(any(r['status']!='PASS' for r in rows))
    finally:
        os.chdir(oldcwd)
        if oldpath is None:os.environ.pop('PYTHONPATH',None)
        else:os.environ['PYTHONPATH']=oldpath
if __name__=='__main__':raise SystemExit(main())
