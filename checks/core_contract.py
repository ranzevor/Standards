"""Offline verification of the distributed normative corpus and its reader indexes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

if sys.flags.optimize:
    raise RuntimeError('Validation requires assertions enabled; do not use -O or -OO')

from checks.validation_common import read_json, require
from checks.repository_registry import validate_entries, validate_catalogues, validate_dependencies
from checks.corpus_contract import profile_for
from checks.generate_index import expected_index
from checks.validate_product import validate_links, validate_project_metadata, validate_license_policy

ROOT = Path(__file__).resolve().parents[1]


def validate_clause_index(root: Path, entries=None):
    """Bind every published clause to its real source span, ID and SHA-256."""
    root = Path(root).resolve()
    entries = validate_entries(root) if entries is None else entries
    by_id = {row['id']: row for row in entries}
    indexed = read_json(root / 'registry/requirements.json')
    require(type(indexed) is list and indexed, 'nonempty clause index')
    mapping = {}
    by_doc = {}
    source_lines = {}
    for row in indexed:
        require(type(row) is dict and all(k in row for k in (
            'id','clause_id','document_id','path','version','document_sha256',
            'line','end_line','section_sha256','heading','kind')), 'incomplete clause identity')
        ident = row['document_id']
        require(ident in by_id, 'unregistered clause owner', ident)
        entry = by_id[ident]
        require(row['id'] == ident + '::' + row['clause_id'] and row['kind'] == 'labelled-clause',
                'clause identity or kind changed', row['id'])
        require(row['path'] == entry['path'] and row['document_sha256'] == entry['sha256']
                and row['version'] == entry['version'], 'clause owner/version/hash drift', row['id'])
        require(type(row['line']) is int and type(row['end_line']) is int, 'clause line types')
        if ident not in source_lines:
            source_lines[ident] = (root / entry['path']).read_bytes().decode('utf-8').splitlines(keepends=True)
        lines = source_lines[ident]
        require(1 <= row['line'] <= row['end_line'] <= len(lines), 'invalid clause source span', row['id'])
        require(hashlib.sha256(''.join(lines[row['line']-1:row['end_line']]).encode('utf-8')).hexdigest()
                == row['section_sha256'], 'clause source span changed', row['id'])
        require(re.match(r'^#{2,6}\s+' + re.escape(row['clause_id']) + r'(?:\s|$)',
                         lines[row['line']-1].lstrip()) is not None,
                'clause heading/source span mismatch', row['id'])
        require(row['id'] not in mapping, 'duplicate clause identity', row['id'])
        mapping[row['id']] = row
        by_doc.setdefault(ident, []).append(row['clause_id'])
    require(set(by_doc) == set(by_id), 'clause index has missing document')
    for ident, entry in by_id.items():
        text=''.join(source_lines[ident])
        expected=profile_for(entry,text)['clause_ids']
        require(by_doc[ident] == expected, 'clause enumeration differs from authoritative body', ident)
    return {'documents': len(by_doc), 'labelled_clauses': len(mapping),
            'source_spans_sha256': 'verified'}


def validate(root=ROOT):
    root = Path(root).resolve()
    require(root.is_dir() and not root.is_symlink(), 'regular repository root required')
    inventory = set()
    folded=set()
    for path in sorted(root.rglob('*')):
        rel=path.relative_to(root)
        if any(p in {'.git', '.venv', '__pycache__', '.pytest_cache'} for p in rel.parts):
            continue
        from tools.verify_release_bundle import checked_path
        checked_path(rel.as_posix())
        require(not path.is_symlink() and (path.is_file() or path.is_dir()),
                'symlink or special file in distribution', rel.as_posix())
        require(rel.as_posix().casefold() not in folded, 'portable casefold collision',rel.as_posix())
        folded.add(rel.as_posix().casefold())
        if path.is_file():
            if path.suffix == '.json': read_json(path)
            inventory.add(rel.as_posix())
    require(not any(p == 'reviews' or p.startswith('reviews/') for p in inventory), 'review files cannot be packaged as source')
    entries = validate_entries(root)
    require(len(entries) == 162, 'current document count')
    require((root/'INDEX.md').read_text('utf-8') == expected_index(entries), 'generated index mismatch')
    project=validate_project_metadata(read_json(root/'project.json'),entries)
    license_policy=validate_license_policy(root)
    clauses=validate_clause_index(root,entries)
    validate_catalogues(root)
    dependencies=validate_dependencies(root,entries)
    from checks.semantic_references import validate as validate_references
    semantic_references=validate_references(root,entries)
    from checks.behavior_cases import validate as validate_behavior_cases
    behavior_cases=validate_behavior_cases(root)
    from checks.definition_interfaces import validate as validate_definitions
    definitions=validate_definitions(root)
    from checks.cloud_cross_interfaces import validate as validate_cloud
    cloud=validate_cloud(root)
    links=validate_links(root)
    from checks.project_readme import validate as check_readme
    readme=check_readme(root)
    from checks.generate_source_catalog import generate as check_sources
    sources=check_sources(root,check=True)
    from checks.source_contracts import validate as validate_sources
    source_claims=validate_sources(root)
    from checks.domain_navigation import generate as check_nav
    navigation=check_nav(root,check=True)
    return {'result':'pass','scope':'published corpus, identities, reader indexes, local links, sources and license policy',
            'documents':len(entries),'adopted_documents':sum(e['status']=='adopted' for e in entries),'files':len(inventory), 'clauses':clauses,'project':project,
            'links':links,'semantic_references':semantic_references,'behavior_cases':behavior_cases,'dependencies':dependencies,'definitions':definitions,'cloud_interfaces':cloud,'license_policy':license_policy,'reader_entries':readme,'source_catalog':sources,'source_claims':source_claims,'navigation':navigation}
