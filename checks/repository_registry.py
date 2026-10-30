"""Current document identities and generated reader indexes."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import sys

if sys.flags.optimize:
    raise RuntimeError('Standard identity checks require Python without -O/-OO')

from checks.validation_common import require, read_json, digest, safe_path
from checks.corpus_contract import extract_document, markdown_blocks, headings
from tools.verify_release_bundle import valid_version, valid_date

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_DOCUMENTS = 162


def validate_document_metadata(entry, body):
    require(body.splitlines()[0] == '# ' + entry['title'], 'document title mismatch', entry['id'])
    for label, value in [('文档ID', entry['id']), ('版本', entry['version']), ('状态', entry['status']), ('生效日期', entry['effective_date'])]:
        values = re.findall(r'\*\*' + label + r'[：:]\*\*\s*([^\s*]+)', body)
        require(values == [value], 'document metadata mismatch', entry['id'], label)


def validate_entries(root=ROOT, entries=None):
    root = Path(root).resolve()
    entries = read_json(root/'registry/standards.json') if entries is None else entries
    require(type(entries) is list and len(entries) == CANONICAL_DOCUMENTS, 'exact current document count')
    from checks.finite_schema import schema_check
    schema_check(entries, read_json(root/'registry/schemas/standards.schema.json'))
    fields = {'id', 'title', 'path', 'domain', 'version', 'status', 'language', 'effective_date', 'sha256'}
    seen_id = set(); seen_path = set()
    for entry in entries:
        require(type(entry) is dict and set(entry) == fields, 'canonical document identity fields')
        ident = entry['id']; path = entry['path']
        require(type(ident) is str and re.fullmatch(r'STD-(?:L[0-6](?:-[A-Z0-9]+)*|PG)-[0-9]{3}', ident), 'stable document ID', ident)
        require(ident not in seen_id and path not in seen_path, 'duplicate document identity', ident)
        seen_id.add(ident); seen_path.add(path)
        require(valid_version(entry['version']) and entry['status'] == 'adopted'
                and entry['language'] == 'zh-Hans' and valid_date(entry['effective_date']), 'current document metadata', ident)
        require(type(path) is str and re.fullmatch(r'standards/(?:[^/]+/)*[0-9]{3}-[^/]+--v'+re.escape(entry['version'])+r'\.md', path), 'document path and version mismatch', ident)
        require(Path(path).name.split('-', 1)[0] == ident.rsplit('-', 1)[1], 'document path and stable number mismatch', ident)
        require(type(entry['domain']) is str and entry['domain'], 'document domain', ident)
        require(type(entry['sha256']) is str and re.fullmatch('[0-9a-f]{64}', entry['sha256']), 'invalid document SHA-256', ident)
        source = safe_path(root, path); raw = source.read_bytes()
        require(digest(raw) == entry['sha256'], 'current document digest mismatch', ident)
        body = raw.decode('utf-8')
        require([h['title'] for h in headings(markdown_blocks(body)) if h['level'] == 1] == [entry['title']], 'current document title mismatch', ident)
        validate_document_metadata(entry, body)
    actual = {p.relative_to(root).as_posix() for p in (root/'standards').rglob('*--v*.md') if p.is_file()}
    require(actual == seen_path, 'unregistered document files', sorted(actual ^ seen_path))
    return entries


def validate_dependencies(root=ROOT,entries=None):
    """Check exact current dependency edges, including non-adopted endpoints."""
    from checks.finite_schema import schema_check
    root=Path(root).resolve()
    entries=validate_entries(root) if entries is None else entries
    by_id={item['id']:item for item in entries}
    edges=read_json(root/'registry/technical-dependencies.json')
    schema_check(edges,read_json(root/'registry/schemas/technical-dependencies.schema.json'))
    clauses={(item['document_id'],item['clause_id']) for item in read_json(root/'registry/requirements.json')}
    keys=set()
    for edge in edges:
        source=by_id.get(edge['from_document']);target=by_id.get(edge['to_document'])
        require(source is not None and target is not None,'unknown graph document identity')
        require((edge['from_document'],edge['from_clause']) in clauses and
                (edge['to_document'],edge['to_clause']) in clauses,'graph references unknown clause')
        require(edge['from_path']==source['path'] and edge['from_sha256']==source['sha256'] and
                edge['to_path']==target['path'] and edge['to_sha256']==target['sha256'] and
                edge['to_version']==target['version'],'graph endpoint identity drift')
        expected='adopted-technical-reference'
        require(edge['state']==expected,'dependency reference state mismatch')
        key=(edge['from_document'],edge['from_clause'],edge['to_document'],edge['to_clause'],edge['interface'])
        require(key not in keys,'duplicate graph edge identity');keys.add(key)
    return {'records':len(edges),'scope':'current clauses, hashes, statuses and dependency endpoints'}


def validate_catalogues(root=ROOT):
    """Validate generated current catalogs with source-derived exact content."""
    root=Path(root).resolve()
    expected=build_catalogues(root)
    for name,content in expected.items():
        require(read_json(root/'registry'/name)==content,'generated catalogue drift',name)
    return expected


def build_catalogues(root=ROOT,entries=None):
    root=Path(root).resolve()
    entries=validate_entries(root,entries)
    from checks.content_contracts import dispatch, validate_dispatch_registry
    validate_dispatch_registry(root, entries)
    profiles=[];requirements=[];refs=[]
    for e in entries:
        contents=extract_document(e,(root/e['path']).read_text('utf-8'))
        profile=contents['profile']
        # The finite schema requires an executable content validator and the
        # exact field contract for every parsed clause. Both come from the
        # current source instead of a historical review cache.
        profile['content_validator']=dispatch(e, (root/e['path']).read_text('utf-8'), profile, contents['clauses'], root)
        profile['contract_fields']={row['clause_id']:list(row['fields']) for row in contents['clauses']}
        profiles.append(profile)
        requirements.extend(contents['clauses'])
        for ref in contents['references']:
            refs.append({**ref,'document_id':e['id'],'path':e['path']})
    require(len(requirements)==3473,'registered clause count changed')
    return {'document-profiles.json':profiles,'requirements.json':requirements,'references.json':refs}
