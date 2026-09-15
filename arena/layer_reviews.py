"""Import independently authored R2/R3/R4 reviews without running a subject/model."""
import argparse
import json
import re
from pathlib import Path
from .io_utils import load_json, load_jsonl, sha256_file


def import_reviews(batch_dir, records_path, outdir):
    batch = Path(batch_dir)
    integrity = load_json(batch / 'integrity.json')
    for name, digest in integrity['files'].items():
        if Path(name).name != name or sha256_file(batch / name) != digest:
            raise ValueError('evidence integrity mismatch')
    metadata = load_json(batch / 'evidence_batch.json')
    if metadata['evidence_batch_hash'] != integrity['evidence_batch_hash']:
        raise ValueError('batch identity mismatch')
    valid_refs = {x['evidence_ref'] for x in load_jsonl(batch / 'review_evidence_index.jsonl')}
    rows = load_jsonl(records_path)
    ids = set()
    for row in rows:
        required = ('review_id', 'layer', 'evidence_batch_hash', 'reviewer', 'rubric_version', 'prompt_version',
                    'created_at', 'evidence_refs', 'finding', 'rationale', 'uncertainties', 'record_kind')
        if any(k not in row for k in required):
            raise ValueError('missing layer review fields')
        ident = row['review_id']
        if not isinstance(ident, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', ident) or ident in ids:
            raise ValueError('invalid/duplicate review id')
        ids.add(ident)
        if row['layer'] not in ('R2', 'R3', 'R4') or row['evidence_batch_hash'] != metadata['evidence_batch_hash']:
            raise ValueError('layer or batch mismatch')
        if not isinstance(row['reviewer'], dict) or not row['reviewer'].get('id') or row['reviewer'].get('type') not in ('human', 'model'):
            raise ValueError('reviewer identity required')
        if row['reviewer']['type'] == 'model' and not all(row['reviewer'].get(k) for k in ('model', 'config_hash')):
            raise ValueError('model review requires model and config_hash')
        if row['record_kind'] not in ('independent', 'recheck', 'adjudication'):
            raise ValueError('invalid review kind')
        if row['record_kind'] == 'independent' and row.get('parent_review_ids'):
            raise ValueError('independent review cannot inherit another review')
        if row['record_kind'] != 'independent' and not row.get('parent_review_ids'):
            raise ValueError('recheck/adjudication must identify parent reviews')
        refs = row['evidence_refs']
        if not isinstance(refs, list) or not refs or any(r not in valid_refs for r in refs):
            raise ValueError('unknown or empty evidence references')
        if row['finding'] not in ('SUPPORTED', 'NOT_SUPPORTED', 'UNCERTAIN') or not row['rationale'] or not isinstance(row['uncertainties'], list):
            raise ValueError('invalid finding/rationale/uncertainties')
    out = Path(outdir) / metadata['evidence_batch_hash']
    if any((out / (r['review_id'] + '.json')).exists() for r in rows):
        raise ValueError('refusing to overwrite a review')
    out.mkdir(parents=True, exist_ok=True)
    for row in rows:
        with (out / (row['review_id'] + '.json')).open('x', encoding='utf-8') as f:
            json.dump(row, f, ensure_ascii=False, indent=2)
    return len(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--batch-dir', required=True)
    ap.add_argument('--records', required=True)
    ap.add_argument('--outdir', required=True)
    a = ap.parse_args()
    print(f'Imported {import_reviews(a.batch_dir, a.records, a.outdir)} layer reviews; subject unchanged.')

if __name__ == '__main__':
    main()
