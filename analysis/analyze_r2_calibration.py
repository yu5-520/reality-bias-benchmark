#!/usr/bin/env python3
import argparse,csv,json
from collections import defaultdict
from pathlib import Path


def primary_event(r):
    target=r['bias']
    for op in r.get('evaluator',{}).get('operations',[]):
        if op.get('bias_mechanism')==target and op.get('attempted_promotion') and not op.get('authorized_under_task'):
            return op
    return None


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input',required=True)
    ap.add_argument('--outdir',required=True)
    a=ap.parse_args()
    rows=[json.loads(x) for x in Path(a.input).read_text(encoding='utf-8').splitlines() if x.strip()]
    if not rows:
        raise SystemExit('No calibration rows')
    groups=defaultdict(list)
    for r in rows:
        groups[(r['bias'],r['item_id'],r.get('trigger_strength'))].append(r)
    out=[]
    for (bias,item,strength),vals in sorted(groups.items()):
        n=len(vals)
        ev=[primary_event(r) for r in vals]
        out.append({
            'bias':bias,'item_id':item,'trigger_strength':strength,'n':n,
            'generation_rate':sum(bool(r['evaluator']['bias_generation'].get(bias,False)) for r in vals)/n,
            'unauthorized_primary_event_rate':sum(x is not None for x in ev)/n,
            'hypothesized_authority_match_rate':(
                sum(x is not None and x.get('authority_class')==r['primary_authority'] for x,r in zip(ev,vals))
                / max(1,sum(x is not None for x in ev))
            ),
            'task_success_rate':sum(r['score']['task_success'] for r in vals)/n,
            'model_refusal_rate':sum(r['score']['model_refusal'] for r in vals)/n,
        })
    od=Path(a.outdir)
    od.mkdir(parents=True,exist_ok=True)
    with (od/'item_calibration.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=out[0].keys())
        w.writeheader(); w.writerows(out)

    versions=sorted({r.get('benchmark_version','unknown') for r in rows})
    version_label=', '.join(versions)
    md=[
        f'# R2 Baseline Trigger Calibration — {version_label}',
        '',
        '|Bias|Item|Intended strength|n|Generation|Unauthorized primary event|Authority match|Task success|Refusal|',
        '|---|---|---|---:|---:|---:|---:|---:|---:|'
    ]
    for x in out:
        md.append(
            f"|{x['bias']}|{x['item_id']}|{x['trigger_strength']}|{x['n']}|"
            f"{x['generation_rate']:.2f}|{x['unauthorized_primary_event_rate']:.2f}|"
            f"{x['hypothesized_authority_match_rate']:.2f}|{x['task_success_rate']:.2f}|"
            f"{x['model_refusal_rate']:.2f}|"
        )
    md += ['', 'Calibration only. These runs are not used as confirmatory R2 gate evidence.']
    (od/'SUMMARY.md').write_text('\n'.join(md),encoding='utf-8')
    print('\n'.join(md))


if __name__=='__main__':
    main()
