"""Validate optional behavior cases and bind their selected normative identities.

This validates the finite case format, not a model's behavior or conformance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import sys

from checks.corpus_contract import extract_document

SCHEMA = 'standards-behavior-cases/1'
CHECK_KINDS = {'exists', 'absent', 'text_contains', 'text_excludes', 'text_equals', 'json_equals'}
ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate JSON key: ' + key)
            result[key] = value
        return result
    def finite_float(text):
        value = float(text)
        require(math.isfinite(value), 'nonfinite JSON number')
        require(value != 0.0 or not re.search('[1-9]', re.split('[eE]', text)[0]),
                'JSON number underflows finite implementation')
        return value
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=pairs, parse_float=finite_float,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def relative_path(value):
    require(type(value) is str and value and value == value.strip(), 'relative path required')
    path = PurePosixPath(value)
    require(not path.is_absolute() and '..' not in path.parts and '.' != value and
            '\\' not in value and '\x00' not in value and not re.match(r'^[A-Za-z]:', value),
            'unsafe relative path: ' + value)
    require(path.as_posix() == value and all(part not in {'', '.', '..'} for part in value.split('/')),
            'noncanonical relative path: ' + value)
    return value


def nonempty(value, label):
    require(type(value) is str and bool(value.strip()), label + ' must be nonempty text')


def validate_suite(suite):
    require(type(suite) is dict and set(suite) == {
        'schema', 'suite_id', 'introduced_in', 'origin', 'purpose', 'normative_refs', 'cases'},
        'suite fields')
    require(suite['schema'] == SCHEMA, 'unsupported case schema')
    require(re.fullmatch(r'[a-z][a-z0-9-]+', suite['suite_id']) is not None, 'suite ID')
    require(re.fullmatch(r'0\.1\.[0-9]+', suite['introduced_in']) is not None, 'introduced version')
    require(suite['origin'] == 'safe-synthetic-scenarios', 'case origin must identify synthetic scenarios')
    nonempty(suite['purpose'], 'purpose')
    require(type(suite['normative_refs']) is list and suite['normative_refs'], 'normative references')
    reference_ids = set()
    for ref in suite['normative_refs']:
        require(type(ref) is dict and set(ref) == {'document_id', 'clause_ids'}, 'reference fields')
        nonempty(ref['document_id'], 'document ID')
        require(ref['document_id'] not in reference_ids, 'duplicate reference document')
        reference_ids.add(ref['document_id'])
        require(type(ref['clause_ids']) is list and ref['clause_ids'] and
                len(ref['clause_ids']) == len(set(ref['clause_ids'])), 'clause IDs')
        for clause in ref['clause_ids']:
            nonempty(clause, 'clause ID')
    require(type(suite['cases']) is list and suite['cases'], 'nonempty cases')
    identifiers = set()
    for case in suite['cases']:
        require(type(case) is dict and set(case) == {
            'id', 'title', 'task_family', 'prompt', 'setup', 'authorization', 'completion',
            'checks', 'rubric', 'examples'}, 'case fields')
        require(type(case['id']) is str and re.fullmatch(r'[A-Z]+-[0-9]{3}', case['id']), 'case ID')
        require(case['id'] not in identifiers, 'duplicate case ID')
        identifiers.add(case['id'])
        for field in ('title', 'task_family', 'prompt', 'completion'):
            nonempty(case[field], field)
        require(type(case['setup']) is list, 'setup files')
        setup_paths = set()
        for item in case['setup']:
            require(type(item) is dict and set(item) == {'path', 'text'}, 'setup fields')
            path = relative_path(item['path'])
            require(path not in setup_paths, 'duplicate setup path')
            setup_paths.add(path)
            require(type(item['text']) is str, 'setup UTF-8 text')
        auth = case['authorization']
        require(type(auth) is dict and set(auth) == {'allowed', 'requires_decision', 'forbidden'},
                'authorization fields')
        for field, items in auth.items():
            require(type(items) is list and all(type(x) is str and x.strip() for x in items),
                    'authorization list: ' + field)
        require(auth['allowed'] and auth['forbidden'], 'authorization scope must be bounded')
        require(type(case['checks']) is list and case['checks'], 'artifact checks')
        check_ids = set()
        for check in case['checks']:
            require(type(check) is dict and set(check) >= {'id', 'kind', 'path'} and
                    not set(check) - {'id', 'kind', 'path', 'expected'}, 'check fields')
            nonempty(check['id'], 'check ID')
            require(check['id'] not in check_ids, 'duplicate check ID')
            check_ids.add(check['id'])
            require(check['kind'] in CHECK_KINDS, 'unsupported artifact check')
            relative_path(check['path'])
            if check['kind'] in {'exists', 'absent'}:
                require('expected' not in check, 'presence check takes no expected value')
            elif check['kind'] == 'json_equals':
                require('expected' in check, 'JSON expected value required')
            else:
                nonempty(check.get('expected'), 'text check expected value')
        require(type(case['rubric']) is list and case['rubric'], 'semantic rubric required')
        rubric_ids = set()
        for row in case['rubric']:
            require(type(row) is dict and set(row) == {'id', 'question', 'failure'}, 'rubric fields')
            for field in row:
                nonempty(row[field], 'rubric ' + field)
            require(row['id'] not in rubric_ids, 'duplicate rubric ID')
            rubric_ids.add(row['id'])
        require(type(case['examples']) is dict and set(case['examples']) == {'positive', 'failure', 'neighbor'},
                'positive, failure and legal neighbor are required')
        for value in case['examples'].values():
            nonempty(value, 'example')
    return len(suite['cases'])


def load_suites(root=ROOT):
    directory = Path(root) / 'examples/ai-agent/behavior/cases'
    paths = sorted(directory.glob('*.json'))
    require(bool(paths), 'no behavior case files')
    suites = []
    ids = set()
    suite_ids = set()
    for path in paths:
        suite = read_json(path)
        validate_suite(suite)
        require(suite['suite_id'] not in suite_ids, 'duplicate suite ID across files')
        suite_ids.add(suite['suite_id'])
        for case in suite['cases']:
            require(case['id'] not in ids, 'duplicate case ID across suites')
            ids.add(case['id'])
        suites.append((path, suite))
    return suites


def bind_normative_references(root, suites):
    root = Path(root).resolve()
    entries = read_json(root / 'registry/standards.json')
    require(type(entries) is list, 'standards registry array')
    docs = {row['id']: row for row in entries}
    require(len(docs) == len(entries), 'duplicate normative document ID')
    requirements = read_json(root / 'registry/requirements.json')
    require(type(requirements) is list, 'requirements registry array')
    clauses = {}
    for row in requirements:
        require(type(row) is dict, 'requirement row object')
        key = (row['document_id'], row['clause_id'])
        require(key not in clauses, 'duplicate normative clause identity')
        clauses[key] = row
    selected = {}
    parsed = {}
    for _, suite in suites:
        for ref in suite['normative_refs']:
            ident = ref['document_id']
            require(ident in docs, 'unknown normative document: ' + ident)
            entry = docs[ident]
            source = root / relative_path(entry['path'])
            require(not source.is_symlink() and source.resolve().is_relative_to(root), 'unsafe normative source')
            raw = source.read_bytes()
            require(digest(raw) == entry['sha256'], 'normative source digest mismatch')
            if ident not in parsed:
                parsed[ident] = {row['clause_id']: row for row in
                                 extract_document(entry, raw.decode('utf-8'))['clauses']}
            for clause in ref['clause_ids']:
                require((ident, clause) in clauses, 'unknown normative clause: ' + ident + '/' + clause)
                require(clause in parsed[ident], 'clause missing from authoritative source: ' + ident + '/' + clause)
                actual, indexed = parsed[ident][clause], clauses[(ident, clause)]
                require(json.dumps(indexed, sort_keys=True, ensure_ascii=False, allow_nan=False) ==
                        json.dumps(actual, sort_keys=True, ensure_ascii=False, allow_nan=False),
                        'normative clause source/index identity mismatch: ' + ident + '/' + clause)
            item = selected.setdefault(ident, {key: entry[key] for key in ('id', 'version', 'path', 'sha256')})
            item.setdefault('clause_ids', [])
            item['clause_ids'] = sorted(set(item['clause_ids']) | set(ref['clause_ids']))
            item['clauses'] = [{key: parsed[ident][clause][key] for key in (
                'clause_id', 'line', 'end_line', 'section_sha256', 'normative_start_line',
                'normative_end_line', 'normative_sha256')} for clause in item['clause_ids']]
    return [selected[key] for key in sorted(selected)]


def validate(root=ROOT):
    suites = load_suites(root)
    bindings = bind_normative_references(root, suites)
    return {'suites': len(suites), 'cases': sum(len(s['cases']) for _, s in suites),
            'normative_documents': len(bindings), 'result': 'case-contracts-verified',
            'scope': 'finite scenario structure and current normative references; model behavior not run'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(validate(args.root), ensure_ascii=False, sort_keys=True))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
