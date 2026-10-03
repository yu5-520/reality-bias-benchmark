#!/usr/bin/env python3
"""Prepare complete route-planning evidence offline; makes no repair/model call."""
import argparse,gzip,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from stage2.route_repair.route_context import CompleteRouteContext
from stage2.route_repair.terminal_runner import save

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root',required=True,type=Path)
    p.add_argument('--graph-root',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path);args=p.parse_args()
    if args.out.exists():p.error('fresh output required')
    args.out.mkdir(parents=True)
    cases=json.loads((ROOT/'configs/stage2_terminal_route_repair_first_round_v1.json').read_text())['cases']
    tasks=json.loads((ROOT/'stage2/tasks.json').read_text())['tasks'];receipts=[]
    for case in cases:
        fid=case['full_id'];g,cell=fid.split('-',1)
        archive=args.source_root/(g+'A')/'stage2/replication_v2'/g/'natural_A'/cell/'first_attempt.tar.gz'
        gp=args.graph_root/(fid+'.json.gz')
        with gzip.open(gp) as f:graph=json.load(f)['graph']
        context=CompleteRouteContext(graph,archive,case)
        try:
            task=next(t for t in tasks if t['id']==fid.rsplit('-',1)[-1])
            catalog=context.catalog(task);dest=args.out/fid;dest.mkdir()
            save(dest/'context_catalog.json',catalog);shutil.copy(gp,dest/'full_graph.json.gz')
            selected=['file:web/index.html','file:web/app.js','file:run.py']
            samples={ref:context.node_context(ref) for ref in selected}
            save(dest/'source_bound_node_examples.json',samples)
            sources=sum(len(x) for x in context.file_versions.values())
            row={'full_id':fid,'status':'PASS_SOURCE_CONTEXT_ONLY','context_hash':catalog['context_hash'],
                'graph_hash':case['graph_hash'],'all_nodes_available':len(catalog['all_node_refs']),
                'terminal_file_sources_verified':len(catalog['current_file_sources']),
                'checkpoint_file_versions_verified':sources,'live_provider_calls':0,'repair_actions':0,
                'route_plan_ready':False,'native_plan_executor_ready':False}
            save(dest/'preparation_receipt.json',row);receipts.append(row);print(json.dumps(row))
        finally:context.close()
    save(args.out/'summary.json',{'schema':'node-route-context-preparation-v1','cases':receipts,
        'live_provider_calls':0,'repair_actions':0,'live_execution_ready':False})

if __name__=='__main__':main()
