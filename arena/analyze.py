#!/usr/bin/env python3
import argparse, csv, json
from collections import Counter
from pathlib import Path

from .evaluation import validate_evaluation
from .counterfactual import replay_immediate_containment
from .io_utils import load_jsonl
from .topology import topology_metrics


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--traces',required=True)
    ap.add_argument('--evaluations',required=True)
    ap.add_argument('--outdir',required=True)
    a=ap.parse_args()
    traces={x['run_id']:x for x in load_jsonl(a.traces)}
    evals={x['run_id']:x['evaluation'] for x in load_jsonl(a.evaluations)}
    od=Path(a.outdir); od.mkdir(parents=True,exist_ok=True)

    matrix=Counter(); run_rows=[]; cf_rows=[]
    for run_id,trace in traces.items():
        ev=evals[run_id]
        validate_evaluation(trace,ev)
        coded={x['event_index']:x for x in ev.get('coded_events',[])}
        first_bias_idx=None
        bias_presence={'C':0,'P':0,'R':0}
        for event in trace['events']:
            code=coded.get(event['event_index'])
            if not code or code['authorized_under_contract'] or not event.get('realized_in_baseline', False): continue
            labels=code.get('bias_mechanisms') or []
            if labels and first_bias_idx is None:
                first_bias_idx=event['event_index']
            for b in labels:
                bias_presence[b]=1
                auth=event.get('authority_class')
                if auth in ('I','V','T'):
                    matrix[(trace['domain_id'],b,auth)] += 1
        full=topology_metrics(trace)
        pre=topology_metrics(trace,first_bias_idx) if first_bias_idx is not None else full
        run_rows.append({
            'run_id':run_id,'domain_id':trace['domain_id'],
            'C':bias_presence['C'],'P':bias_presence['P'],'R':bias_presence['R'],
            'first_bias_event_index':first_bias_idx if first_bias_idx is not None else '',
            'activated_agent_count':trace['activated_agent_count'],
            **{f'full_{k}':v for k,v in full.items()},
            **{f'prebias_{k}':v for k,v in pre.items()},
        })
        cf_rows.extend(replay_immediate_containment(trace,ev))

    with (od/'run_level.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=run_rows[0].keys()); w.writeheader(); w.writerows(sorted(run_rows,key=lambda x:x['run_id']))
    matrix_rows=[]
    domains=sorted({x['domain_id'] for x in run_rows})
    for domain in domains:
        for b in 'CPR':
            for auth in 'IVT':
                matrix_rows.append({'domain_id':domain,'bias':b,'authority':auth,'event_count':matrix[(domain,b,auth)]})
    with (od/'bias_authority_3x3.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=matrix_rows[0].keys()); w.writeheader(); w.writerows(matrix_rows)
    (od/'counterfactual_replay.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in cf_rows)+'\n',encoding='utf-8')

    lines=['# Free-Agent Arena Summary','', 'Emergence and the 3×3 matrix count realized, unauthorized, mechanism-coded events only. Attempts remain in raw traces and evaluation records.', '']
    for domain in domains:
        subset=[x for x in run_rows if x['domain_id']==domain]
        lines += [f'## {domain}', '', f"Runs: {len(subset)}", '', '|Bias|Run emergence rate|', '|---|---:|']
        for b in 'CPR':
            lines.append(f"|{b}|{sum(x[b] for x in subset)/len(subset):.3f}|")
        lines += ['', '3×3 event counts:', '', '|Bias \\ Authority|I|V|T|','|---|---:|---:|---:|']
        for b in 'CPR':
            lines.append(f"|{b}|{matrix[(domain,b,'I')]}|{matrix[(domain,b,'V')]}|{matrix[(domain,b,'T')]}|")
        lines.append('')
    lines += ['Counterfactual replay is immediate event containment only; blocking an event does not regenerate downstream agent behavior.']
    (od/'SUMMARY.md').write_text('\n'.join(lines),encoding='utf-8')
    print('\n'.join(lines))


if __name__=='__main__': main()

