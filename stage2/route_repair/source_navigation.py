"""Exact prefix navigation for the external repair actor.

Handles bind observed versions, not semantic truth or write authority. Native
frameworks and the internal source-query replay format remain unchanged.
"""
import copy
from stage2.r7_checkpoint_v1.common import digest
from stage2.route_repair.branch_fields import require


def version_handle(context, ref, row):
    return 'version:' + digest({
        'archive_sha256': context.case['archive_sha256'],
        'parent_checkpoint_hash': context.parent_checkpoint_hash,
        'graph_hash': context.graph['graph_hash'], 'ref': ref,
        'checkpoint_hash': row['checkpoint_hash'],
        'content_sha256': row['content_sha256']})


class SourceNavigation:
    def __init__(self, context):
        self.context = context
        self._versions = {}
        for ref, rows in context.file_versions.items():
            for row in rows:
                handle = version_handle(context, ref, row)
                value = {**copy.deepcopy(row), 'ref': ref, 'version_handle': handle}
                require(handle not in self._versions, 'DUPLICATE_VERSION_HANDLE')
                self._versions[handle] = value

    def versions(self, ref, at='ALL'):
        require(isinstance(ref, str) and ref in self.context.file_versions,
                'NODE_OUTSIDE_VERIFIED_PREFIX')
        require(at in {'ALL', 'TASK_START', 'PARENT'}, 'VERSION_SELECTOR_INVALID')
        rows = [row for row in self._versions.values() if row['ref'] == ref]
        if at == 'TASK_START':
            rows = [row for row in rows if row['boundary'] == 'TASK_START']
        elif at == 'PARENT':
            rows = [row for row in rows if row['checkpoint_hash'] == self.context.parent_checkpoint_hash]
        # Never substitute the earliest available file for an absent initial file.
        return {'status': 'AVAILABLE' if rows else 'VERSION_ABSENT', 'ref': ref, 'at': at,
                'versions': [{k: row[k] for k in ['version_handle', 'checkpoint_hash',
                    'content_sha256', 'native_sequence', 'boundary']} for row in rows],
                'source_content_read': False, 'write_authority_granted': False}

    def read(self, session, handle):
        require(isinstance(handle, str) and handle in self._versions,
                'VERSION_HANDLE_OUTSIDE_VERIFIED_PREFIX')
        bound = self._versions[handle]
        # Check the frozen member bytes before admitting a source read.
        row = self.context.read_file(bound['ref'], bound['checkpoint_hash'])
        require(row['checkpoint_hash'] == bound['checkpoint_hash']
                and digest(row['content'].encode()) == bound['content_sha256'],
                'VERSION_CONTENT_HASH_MISMATCH')
        return session._read('read_file', {'ref': bound['ref'], 'checkpoint_hash': bound['checkpoint_hash']},
                             bound['ref'], row['content'], row['source_locator'])


# Only errors that expose no new source or authority may remain in this session.
# Unknown failures, invalid finals, corrupt sources and prefix violations close it.
RECOVERABLE_QUERY_ERRORS = frozenset({
    'EXACT_PLANNING_TOOL_ARGUMENTS_REQUIRED', 'VERSION_SELECTOR_INVALID',
    'EXACT_SOURCE_QUOTE_REQUIRED', 'SOURCE_QUOTE_NOT_PRESENT',
    'SOURCE_QUOTE_AMBIGUOUS_USE_OFFSETS', 'EXACT_WITNESS_SPAN_REQUIRED',
    'WITNESS_SOURCE_NOT_INSPECTED',
})


def classify_query_error(code):
    if code in RECOVERABLE_QUERY_ERRORS:
        return 'QUERY_CORRECTION', True
    if 'HASH' in code or 'DRIFT' in code:
        return 'SOURCE_INTEGRITY', False
    if 'OUTSIDE' in code or 'FORBIDDEN' in code or 'REVOKED' in code:
        return 'ACCESS_BOUNDARY', False
    return 'UNCLASSIFIED_FAILURE', False
