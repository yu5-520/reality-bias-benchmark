"""Export a complete, explicitly synthetic three-layer evidence batch."""
import argparse
import json
from pathlib import Path
from .engine import run_arena_once
from .providers import ScriptedProvider
from .io_utils import load_json, load_jsonl, write_jsonl
from .evidence import build_batch
from .layer_reviews import import_reviews


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--manifest',required=True); ap.add_argument('--outdir',required=True)
    a=ap.parse_args(); out=Path(a.outdir); out.mkdir(parents=True,exist_ok=True)
    rows=load_jsonl(a.manifest); traces=[]
    for row in rows:
        domain=load_json('arena/domains/'+row['domain_id']+'.json')
        cfg=load_json(row['arena_config_path'])
        t=run_arena_once(domain,cfg,ScriptedProvider([]),row['run_id'])
        t.update({k:row[k] for k in ('domain_hash','arena_config_hash','model_config_hash')})
        t['scientific_use']='SYNTHETIC_ENGINEERING_ONLY'
        traces.append(t)
    path=out/'traces.jsonl'; write_jsonl(path,traces)
    metadata=build_batch(a.manifest,path,None,out/'batch')
    refs=load_jsonl(out/'batch/review_evidence_index.jsonl')
    reviews=[dict(review_id='synthetic-'+layer,layer=layer,evidence_batch_hash=metadata['evidence_batch_hash'],
        reviewer={'id':'engineering-fixture','type':'human'},rubric_version='TEST_ONLY',prompt_version='NOT_APPLICABLE',
        created_at='2026-09-15T00:00:00Z',evidence_refs=[refs[0]['evidence_ref']],finding='UNCERTAIN',
        rationale='Synthetic import validation; not a human or model adjudication.',uncertainties=['engineering fixture'],record_kind='independent')
        for layer in ('R2','R3','R4')]
    rp=out/'synthetic_reviews.jsonl';write_jsonl(rp,reviews)
    assert import_reviews(out/'batch',rp,out/'reviews')==3
    try:
        import_reviews(out/'batch',rp,out/'reviews')
    except ValueError:
        pass
    else:
        raise AssertionError('review overwrite accepted')
    reviews[0]['review_id']='bad-ref'; reviews[0]['evidence_refs']=['missing']
    write_jsonl(rp,reviews[:1])
    try:
        import_reviews(out/'batch',rp,out/'reviews')
    except ValueError:
        pass
    else:
        raise AssertionError('unknown reference accepted')
    print('PASS: synthetic evidence export, three-layer review import, overwrite and reference rejection; no scientific conclusion')

if __name__=='__main__':
    main()
