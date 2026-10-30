"""Validate source claim identities, finite support fields and local clause mappings."""
import argparse
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit

if sys.flags.optimize:
    raise RuntimeError('Validation requires normal Python mode')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from checks.corpus_contract import profile_for
from checks.validation_common import read_json, require, safe_path, substantive

COLLECTIONS = {
    'ai-agent-source-registry.json': 'sources',
    'cloud/interruption-source-claims.json': 'records',
    'cloud/source-claims.json': 'claims',
    'database-sources.json': None,
    'desktop-mobile-source-claims.json': 'claims',
    'model-research-claims.json': 'records',
    'project-governance/core-governance.json': 'sources',
    'project-governance/documentation-rights.json': 'sources',
    'project-governance/git-operations.json': 'sources',
    'runtime-protocol/source-claims.json': None,
    'web-backend/claims.json': 'claims',
}
SUPPORT_FIELDS = ('supported_claim', 'supported_claims', 'supported_proposition',
                  'supported', 'claim_scope', 'limited_proposition', 'claim')


def supported(value):
    return substantive(value) or type(value) is list and bool(value) and all(substantive(x) for x in value)


def validate_claims(rows, packet):
    require(type(rows) is list and rows, 'nonempty source claim collection', packet)
    identities = set()
    for row in rows:
        require(type(row) is dict, 'source claim object', packet)
        identity = row.get('id', row.get('source_id'))
        require(substantive(identity) and identity not in identities, 'duplicate or missing source identity', packet, identity)
        identities.add(identity)
        require(substantive(row.get('url')), 'source URL required', packet, identity)
        uri = urlsplit(row['url'])
        require(uri.scheme in {'http', 'https'} and bool(uri.netloc), 'source HTTP URL required', packet, identity)
        propositions = row.get('propositions')
        proposition_scope = type(propositions) is list and bool(propositions) and all(
            type(item) is dict and substantive(item.get('supported')) for item in propositions)
        require(any(supported(row.get(field)) for field in SUPPORT_FIELDS) or proposition_scope,
                'finite supported proposition required', packet, identity)
    return identities


def validate(root=ROOT):
    root = Path(root).resolve()
    entries = read_json(root/'registry/standards.json')
    by_path = {entry['path']: entry for entry in entries}
    by_id = {entry['id']: entry for entry in entries}
    packets = {}; collections = {}; identities = {}; documents = {}; mappings = 0
    for name, key in COLLECTIONS.items():
        packet = read_json(safe_path(root, 'sources/'+name))
        rows = packet if key is None else packet[key]
        identities[name] = validate_claims(rows, name)
        packets[name] = packet; collections[name] = rows

    def clause(path, identifier):
        nonlocal mappings
        require(path in by_path, 'source mapping document not registered', path)
        if path not in documents:
            documents[path] = set(profile_for(by_path[path], safe_path(root, path).read_text('utf-8'))['clause_ids'])
        require(identifier in documents[path], 'source mapping clause not found', path, identifier)
        mappings += 1

    for name, field in (('desktop-mobile-source-claims.json', 'supports'),
                        ('model-research-claims.json', 'supported_clause_references')):
        for row in collections[name]:
            for reference in row[field]:
                clause(reference['path'], reference['clause'])
    runtime_name = 'runtime-protocol/source-claims.json'
    for row in collections[runtime_name]:
        for reference in row['supported_clauses']:
            require(type(reference) is str and '#' in reference, 'source clause locator required')
            path, identifier = reference.rsplit('#', 1)
            clause(path, identifier)
    aliases = read_json(safe_path(root, 'sources/runtime-protocol/network-aliases.json'))
    require(type(aliases) is dict and aliases, 'runtime source aliases required')
    for alias, targets in aliases.items():
        require(substantive(alias) and type(targets) is list and targets
                and len(set(targets)) == len(targets) and set(targets) <= identities[runtime_name],
                'unknown or duplicate runtime source alias target', alias)

    web_ids = identities['web-backend/claims.json']
    for row in packets['web-backend/claims.json']['document_claim_mapping']:
        require(row['document_id'] in by_id and row['claim_id'] in web_ids,
                'web source document or claim mapping not found')
    mechanisms = read_json(safe_path(root, 'sources/web-backend/mechanism-claims.json'))['mechanisms']
    for row in mechanisms:
        require(row['document'] in by_path and row['document_id'] == by_path[row['document']]['id'],
                'web source document identity drift')
        clause(row['document'], row['mechanism_id'])
        for field in ('claim_ids', 'context_reference_ids'):
            require(type(row[field]) is list and set(row[field]) <= web_ids,
                    'web source claim reference not found', field)
        for item in row['external_support']:
            require(item['id'] in web_ids and substantive(item['only_supports']), 'web external support mapping')
    references = read_json(safe_path(root, 'sources/web-backend/reference-catalog.json'))['references']
    for row in references:
        require(row['document_id'] in by_id and set(row['core_claim_ids']) <= web_ids,
                'web reference document or source identity not found')
    return {'source_collections': len(collections), 'source_claims': sum(map(len, identities.values())),
            'clause_mappings': mappings, 'runtime_aliases': len(aliases),
            'web_mechanisms': len(mechanisms), 'web_references': len(references),
            'scope': 'source identities, HTTP citation syntax, supported proposition fields and current clause mappings'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(validate(args.root), ensure_ascii=False, sort_keys=True))
