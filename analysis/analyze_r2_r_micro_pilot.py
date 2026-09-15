#!/usr/bin/env python3
import argparse,csv,json
from collections import Counter,defaultdict
from pathlib import Path


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input',required=True); ap.add_argument('--outdir',required=True); a=ap.parse_args()
    rows=[json.loads(x) for x in Path(a.input).read_text(encoding='utf-8').splitlines() if x.strip()]
    if not rows: raise SystemExit('No pilot rows')
    groups=defaultdict(list)
    for r in rows: groups[(r['item_id'],r['intended_strength'])].append(r)
    summary=[]
    for (item,strength),vals in sorted(groups.items()):
        n=len(vals)
        ops=Counter(v['planner_plan']['operation'] for v in vals)
        auth=Counter((v['evaluator_primary_authority'] or 'NONE') for v in vals if v['primary_r_event'])
        attempts=sum(v['score']['unauthorized_r_attempt'] for v in vals)
        summary.append({
            'item_id':item,'intended_strength':strength,'n':n,
            'generation_rate':sum(v['score']['bias_generation_r'] for v in vals)/n,
            'unauthorized_r_attempt_rate':attempts/n,
            'realization_rate':sum(v['score']['bias_realization'] for v in vals)/n,
            'state_penetration_rate':sum(v['score']['state_penetration'] for v in vals)/n,
            'valid_operation_rate':sum(v['score']['planner_valid_operation'] for v in vals)/n,
            'authority_agreement_rate':sum(v['authority_class_agreement'] for v in vals)/max(1,attempts),
            'op_no_change':ops['NO_CHANGE'],
            'op_i_write':ops['WRITE_ACTIVE_STATE'],
            'op_v_review':ops['ADD_REVIEW_STAGE'],
            'op_t_reopen':ops['REOPEN_FINALIZED_STATE'],
            'r_primary_i':auth['I'],'r_primary_v':auth['V'],'r_primary_t':auth['T'],
        })
    od=Path(a.outdir); od.mkdir(parents=True,exist_ok=True)
    with (od/'item_summary.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=summary[0].keys()); w.writeheader(); w.writerows(summary)

    all_attempts=sum(r['score']['unauthorized_r_attempt'] for r in rows)
    all_auth=Counter((r['evaluator_primary_authority'] or 'NONE') for r in rows if r['primary_r_event'])
    mech_ops=Counter(r['planner_plan']['operation'] for r in rows)
    md=['# R2 R-Micro v0.1 Structural Feasibility Pilot','',
        '|Item|Strength|n|R generation|Unauthorized R attempt|Realization|State penetration|Valid op|NO_CHANGE|I write|V review|T reopen|R-I|R-V|R-T|',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for x in summary:
        md.append(f"|{x['item_id']}|{x['intended_strength']}|{x['n']}|{x['generation_rate']:.2f}|{x['unauthorized_r_attempt_rate']:.2f}|{x['realization_rate']:.2f}|{x['state_penetration_rate']:.2f}|{x['valid_operation_rate']:.2f}|{x['op_no_change']}|{x['op_i_write']}|{x['op_v_review']}|{x['op_t_reopen']}|{x['r_primary_i']}|{x['r_primary_v']}|{x['r_primary_t']}|")
    md += ['', '## Aggregate diagnostics','',
           f'- Total pilot traces: {len(rows)}',
           f'- Unauthorized R primary events: {all_attempts}',
           f"- R primary Authority distribution: I={all_auth['I']}, V={all_auth['V']}, T={all_auth['T']}",
           f"- Planner operation distribution: {dict(mech_ops)}",
           '',
           'This is a structural feasibility pilot, not confirmatory R2 evidence. The key question is whether the workflow produces auditable operation/state/downstream traces without forcing R to be Temporal by definition.']
    (od/'SUMMARY.md').write_text('\n'.join(md),encoding='utf-8')
    print('\n'.join(md))


if __name__=='__main__': main()
