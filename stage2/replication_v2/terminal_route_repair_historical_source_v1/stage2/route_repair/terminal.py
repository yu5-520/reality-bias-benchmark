"""Frozen terminal evidence access and independently bounded repair decisions.

The observation graph is an index, never mutation authority. Audit labels are
not inputs. A new repair phase supersedes a process account without changing it.
"""
from __future__ import annotations
import copy
import hashlib
import json
import tarfile
from pathlib import Path, PurePosixPath
from collections import defaultdict
from stage2.r7_checkpoint_v1.common import digest, stable_json_bytes, file_tree_manifest


def exact_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_pointer(value, pointer):
    if not pointer:
        return value
    if not pointer.startswith('/'):
        raise ValueError('invalid JSON pointer')
    for part in pointer[1:].split('/'):
        part = part.replace('~1', '/').replace('~0', '~')
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


class FrozenGraphAccess:
    """Same raw evidence access in both arms; graph navigation only in GRAPH."""
    def __init__(self, graph, archive, *, arm, expected_archive_hash, max_queries=12,
                 response_chars=24000, total_chars=120000):
        if arm not in {'LOCAL', 'GRAPH'}:
            raise ValueError('unknown comparison arm')
        if exact_hash(archive) != expected_archive_hash:
            raise ValueError('source archive hash mismatch')
        payload = {k:v for k,v in graph.items() if k != 'graph_hash'}
        if digest(payload) != graph['graph_hash']:
            raise ValueError('graph hash mismatch')
        self.archive_hash = expected_archive_hash
        self.graph = graph; self.arm = arm; self.max_queries = max_queries
        self.response_chars = response_chars; self.total_chars = total_chars
        self.returned_chars = 0; self.query_attempts = 0; self.log = []; self.read_observation_ids = set()
        self.read_members = set(); self.archive = tarfile.open(archive, 'r:gz')
        self.members = {m.name.removeprefix('./'):m for m in self.archive if m.isfile()}
        self.nodes = {n['ref']:n for n in graph['nodes']}
        self.observations = {o['observation_id']:o for o in graph['observations']}
        self.by_object = defaultdict(list)
        for o in graph['observations']:
            for ref in o['object_refs']:
                self.by_object[ref].append(o)
        self.by_node_edges = defaultdict(list)
        for e in graph['edges']:
            self.by_node_edges[e['source_ref']].append(e)
            if e['destination_ref'] != e['source_ref']:
                self.by_node_edges[e['destination_ref']].append(e)

    def close(self):
        self.archive.close()

    def member(self, name):
        if name not in self.members:
            raise ValueError('source member absent')
        return self.archive.extractfile(self.members[name]).read()

    def _source(self, locator):
        if locator.get('archive_sha256') != self.archive_hash:
            raise ValueError('observation belongs to another archive')
        raw = self.member(locator['member'])
        if hashlib.sha256(raw).hexdigest() != locator['member_sha256']:
            raise ValueError('member checksum mismatch')
        text = raw.decode('utf-8')
        if locator.get('line') is not None:
            text = text.splitlines()[int(locator['line'])-1]
        pointer = locator.get('json_pointer') or ''
        if pointer:
            text = json.dumps(json_pointer(json.loads(text), pointer), ensure_ascii=False)
        return text

    def query(self, request):
        if self.query_attempts >= self.max_queries:
            raise ValueError('query budget exhausted')
        self.query_attempts += 1
        try:
            return self._query(request)
        except Exception as exc:
            self.log.append({'request':copy.deepcopy(request),'error_type':type(exc).__name__,'error':str(exc)})
            raise

    def _query(self, request):
        q = copy.deepcopy(dict(request)); op = q.get('op')
        offset = q.get('offset', 0); limit = q.get('limit', 20)
        if not isinstance(offset,int) or offset<0 or not isinstance(limit,int) or not 1<=limit<=50:
            raise ValueError('invalid page')
        read_ids = set(); read_members = set()
        if op == 'list_members':
            names = sorted(self.members)
            data = {'items':names[offset:offset+limit], 'total':len(names), 'next_offset':offset+limit if offset+limit<len(names) else None}
        elif op == 'read_member':
            name=q.get('member'); raw=self.member(name)
            content=raw.decode('utf-8'); start=q.get('start',0); length=q.get('length',8000)
            if not isinstance(start,int) or start<0 or not isinstance(length,int) or not 1<=length<=16000:
                raise ValueError('invalid text slice')
            data={'member':name,'member_sha256':hashlib.sha256(raw).hexdigest(),
                  'text':content[start:start+length],'start':start,'total_chars':len(content),
                  'next_start':start+length if start+length<len(content) else None}
            read_members.add(name)
        elif op == 'list_nodes' and self.arm=='GRAPH':
            refs=sorted(self.nodes); prefix=q.get('prefix','')
            refs=[r for r in refs if r.startswith(prefix)]
            data={'items':refs[offset:offset+limit],'total':len(refs),'next_offset':offset+limit if offset+limit<len(refs) else None}
        elif op == 'node' and self.arm=='GRAPH':
            ref=q.get('ref'); n=self.nodes[ref]
            summary={k:(v[offset:offset+limit] if isinstance(v,list) else v) for k,v in n.items()}
            counts={k:len(v) for k,v in n.items() if isinstance(v,list)}
            total=max([len(self.by_node_edges[ref])]+list(counts.values()))
            data={'node':summary,'node_list_counts':counts,'edges':self.by_node_edges[ref][offset:offset+limit],
                  'total_edges':len(self.by_node_edges[ref]),'next_offset':offset+limit if offset+limit<total else None}
        elif op == 'object_history' and self.arm=='GRAPH':
            rows=self.by_object[q['ref']]; selected=rows[offset:offset+limit]
            data={'items':selected,'total':len(rows),'next_offset':offset+limit if offset+limit<len(rows) else None,
                  'ordering':'capture order only; compare clock_id before interpreting sequences'}
            read_ids.update(o['observation_id'] for o in selected)
        elif op == 'observation' and self.arm=='GRAPH':
            o=self.observations[q['observation_id']]; text=self._source(o['source_locator'])
            start=q.get('start',0)
            if not isinstance(start,int) or start<0:raise ValueError('invalid text slice')
            data={'observation':o,'source_text':text[start:start+12000],
                  'total_chars':len(text),'next_start':start+12000 if start+12000<len(text) else None}
            read_ids.add(o['observation_id']);read_members.add(o['source_locator']['member'])
        else:
            raise ValueError('operation not available in this arm')
        encoded=stable_json_bytes(data).decode()
        if len(encoded)>self.response_chars or self.returned_chars+len(encoded)>self.total_chars:
            raise ValueError('response budget exceeded; request a smaller page')
        self.returned_chars+=len(encoded);self.read_observation_ids.update(read_ids)
        self.read_members.update(read_members)
        row={'request':q,'response':data,'response_hash':digest(data),'returned_chars':len(encoded)}
        self.log.append(row)
        return data

    def validate_citations(self, citations):
        if not citations:
            raise ValueError('evidence citations required')
        for c in citations:
            if c.get('observation_id'):
                if c['observation_id'] not in self.read_observation_ids:
                    raise ValueError('observation citation not inspected')
            elif c.get('member'):
                if c['member'] not in self.read_members:
                    raise ValueError('member citation not inspected')
                if hashlib.sha256(self.member(c['member'])).hexdigest()!=c.get('sha256'):
                    raise ValueError('citation checksum mismatch')
            else:
                raise ValueError('citation must identify inspected evidence')


def validate_terminal_decision(decision, *, access, parent, current_files,
                               authorized_files, preserve_files, max_actions=4):
    """Pre-execution validation; unknown graph edges never grant write access."""
    d=copy.deepcopy(dict(decision))
    if parent.get('restore_capability')!='FULL_NATIVE' or not parent.get('checkpoint_hash'):
        raise ValueError('full terminal parent required')
    if d.get('parent_checkpoint_hash')!=parent['checkpoint_hash']:
        raise ValueError('wrong repair parent')
    if d.get('decision') not in {'REPAIR','NO_REPAIR_NEEDED','UNRESOLVED'}:
        raise ValueError('decision class invalid')
    if not isinstance(d.get('reason'),str) or not d['reason'].strip():
        raise ValueError('reason required')
    access.validate_citations(d.get('evidence',[]))
    actions=d.get('actions',[])
    if not isinstance(actions,list) or len(actions)>max_actions:
        raise ValueError('action budget exceeded')
    if d['decision']=='REPAIR' and not actions:raise ValueError('repair requires actions')
    if d['decision']!='REPAIR' and actions:raise ValueError('non-repair decision has actions')
    targets=set()
    for a in actions:
        ref=a.get('target_ref')
        if ref in targets:raise ValueError('duplicate repair target')
        targets.add(ref)
        if not isinstance(a.get('reason'),str) or not a['reason'].strip():raise ValueError('action reason required')
        access.validate_citations(a.get('evidence',[]))
        if a.get('kind')=='file_replace':
            if not isinstance(ref,str) or not ref.startswith('file:'):raise ValueError('file target required')
            name=ref[5:];p=PurePosixPath(name)
            if p.is_absolute() or '..' in p.parts or '\\' in name:raise ValueError('unsafe path')
            if name not in authorized_files or name in preserve_files:raise ValueError('file outside authorized repair scope')
            if a.get('before_hash')!=current_files.get(name):raise ValueError('stale target version')
            if not isinstance(a.get('content'),str) or len(a['content'].encode())>262144:raise ValueError('invalid file content')
        elif a.get('kind')=='process_revision':
            if ref!='state:terminal':raise ValueError('only terminal account supersession supported')
            if a.get('before_hash')!=parent['native_state_sha256']:raise ValueError('stale process state')
            if not isinstance(a.get('instruction'),str) or not a['instruction'].strip():raise ValueError('revision instruction required')
            if len(a['instruction'])>16000:raise ValueError('revision instruction too large')
        else:
            raise ValueError('unsupported native action')
    d['decision_hash']=digest(d)
    return d
