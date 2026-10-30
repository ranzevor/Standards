"""Validate the current normative, dependency and governance catalogue roles."""
from pathlib import Path
import sys
if sys.flags.optimize: raise RuntimeError('Registry validation requires normal Python mode')
from checks.validation_common import read_json, require, safe_path
from checks.repository_registry import validate_dependencies


def validate(root):
    root = Path(root).resolve()
    entries = read_json(root/'registry/standards.json'); known = {e['id']: e for e in entries}
    for entry in entries: safe_path(root, entry['path'])
    graph = validate_dependencies(root, entries)
    current = read_json(root/'registry/project-governance-domain.json')
    ids = current['document_ids']
    require(type(ids) is list and len(ids) == len(set(ids)), 'governance unique current document IDs')
    require(all(i in known and known[i]['path'].startswith('standards/project-governance/') for i in ids), 'unknown governance domain document')
    return {'roles': {'normative': 'registry/standards.json', 'necessary_interfaces': 'registry/technical-dependencies.json', 'declared_interfaces': 'registry/interface-requirements.json', 'governance_contracts': 'registry/project-governance-domain.json'}, 'dependency_records': graph['records']}
