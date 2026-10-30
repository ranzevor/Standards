"""Bind cloud consumer/provider interfaces to the current normative corpus."""
from pathlib import Path
import argparse
import json
import sys
if sys.flags.optimize: raise RuntimeError('Cloud interface validation requires normal Python mode')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from checks.validation_common import read_json, require, safe_path, digest, substantive
from checks.corpus_contract import extract_document, headings, markdown_blocks


def validate(root=ROOT):
    root = Path(root).resolve()
    entries = {entry['path']: entry for entry in read_json(root/'registry/standards.json')}
    rows = read_json(root/'registry/cloud-interfaces.json')
    require(type(rows) is list and rows, 'cloud interface collection required')
    seen = set(); documents = {}
    for row in rows:
        required = {'consumer', 'provider', 'consumer_sha256', 'provider_sha256',
                    'consumer_clauses', 'provider_locators', 'provider_version',
                    'interface', 'kind', 'exchange'}
        require(type(row) is dict and required <= set(row), 'cloud interface fields')
        require(row['kind'] == 'conditional-technical-dependency' and substantive(row['interface']),
                'cloud interface identity and kind')
        for field in ('activation', 'required_guarantee'):
            if field in row:
                require(substantive(row[field]), 'empty cloud interface condition', field)
        for side in ('consumer', 'provider'):
            path = row[side]
            require(path in entries, 'unknown cloud interface endpoint', path)
            entry = entries[path]
            require(row[side+'_sha256'] == entry['sha256'], 'cloud interface digest drift', path)
            if path not in documents:
                raw = safe_path(root, path).read_bytes()
                require(digest(raw) == entry['sha256'], 'cloud endpoint body drift', path)
                body = raw.decode('utf-8')
                documents[path] = {
                    'clauses': extract_document(entry, body)['clauses'],
                    'headings': {item['title'] for item in headings(markdown_blocks(body))},
                }
        require(row['provider_version'] == entries[row['provider']]['version'], 'cloud provider version drift')
        clauses = {item['clause_id'] for item in documents[row['consumer']]['clauses']}
        require(type(row['consumer_clauses']) is list and row['consumer_clauses'] and len(set(row['consumer_clauses'])) == len(row['consumer_clauses']) and set(row['consumer_clauses']) <= clauses, 'cloud consumer clause mapping')
        locators = documents[row['provider']]['headings']
        require(type(row['provider_locators']) is list and row['provider_locators'] and len(set(row['provider_locators'])) == len(row['provider_locators']) and set(row['provider_locators']) <= locators, 'cloud provider heading mapping')
        require(type(row['exchange']) is list and row['exchange'] and all(substantive(item) for item in row['exchange']), 'cloud interface exchange fields')
        key = (row['consumer'], row['provider'], row['interface'])
        require(key not in seen, 'duplicate cloud interface'); seen.add(key)
    return {'interfaces': len(rows), 'endpoint_documents': len(documents)}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args(); print(json.dumps(validate(args.root), ensure_ascii=False, sort_keys=True))
