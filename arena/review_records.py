import math

REVIEW_RECORD_VERSION = 'R2-REVIEW-RECORD-v0.1'
ALLOWED_BIAS = {'C', 'P', 'R'}
ALLOWED_AUTH = {'AUTHORIZED', 'UNAUTHORIZED', 'UNCERTAIN', 'NOT_APPLICABLE'}
ALLOWED_KIND = {'independent', 'recheck', 'adjudication'}


def validate_review_record(row):
    required = [
        'review_record_version', 'review_record_id', 'record_kind',
        'evidence_batch_hash', 'packet_id', 'event_id', 'reviewer',
        'rubric_version', 'prompt_version', 'bias_labels',
        'authorization_judgment', 'rationale', 'confidence',
        'uncertainties', 'created_at', 'review_version'
    ]
    for key in required:
        if key not in row:
            raise ValueError(f'missing review field: {key}')
    if row['review_record_version'] != REVIEW_RECORD_VERSION:
        raise ValueError('unsupported review_record_version')
    if row['record_kind'] not in ALLOWED_KIND:
        raise ValueError('invalid record_kind')
    if not isinstance(row['reviewer'], dict) or not row['reviewer'].get('id'):
        raise ValueError('reviewer.id required')
    labels = row['bias_labels']
    if not isinstance(labels, list) or len(labels) != len(set(labels)) or any(x not in ALLOWED_BIAS for x in labels):
        raise ValueError('bias_labels must be unique C/P/R values')
    if row['authorization_judgment'] not in ALLOWED_AUTH:
        raise ValueError('invalid authorization_judgment')
    if not isinstance(row['rationale'], str) or not row['rationale'].strip():
        raise ValueError('rationale required')
    c = row['confidence']
    if type(c) not in (int, float) or not math.isfinite(c) or not 0 <= c <= 1:
        raise ValueError('confidence must be finite 0..1')
    if not isinstance(row['uncertainties'], list):
        raise ValueError('uncertainties must be a list')
    parents = row.get('parent_review_ids', [])
    if not isinstance(parents, list):
        raise ValueError('parent_review_ids must be a list')
    return True
