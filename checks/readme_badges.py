"""Validate Shields.io badge URLs and their local source values offline."""
from __future__ import annotations

import re
from urllib.parse import quote

from checks.validation_common import read_json, require, safe_path


def shields_badge_url(label, message, color):
    """Encode the documented Shields static-badge path without query overrides."""
    require(all(type(value) is str and value.strip() == value and value
                for value in (label, message, color)), 'badge text and color required')
    require(re.fullmatch(r'[a-z]+|[A-Fa-f0-9]{6}', color), 'unsupported badge color')
    def encode(value):
        return quote(value.replace('-', '--').replace('_', '__'), safe='')
    return 'https://img.shields.io/badge/' + '-'.join((encode(label), encode(message), color))


def evidence_value(root, evidence, claim):
    require(type(evidence) is dict, 'badge evidence object required')
    mode = evidence.get('mode')
    extra = {'json-field': {'field'}, 'references': {'items'}}.get(mode, set())
    require(set(evidence) == {'path', 'mode'} | extra, 'badge evidence fields differ')
    source = safe_path(root, evidence['path'])
    text = source.read_text(encoding='utf-8')
    if mode == 'json-field':
        value = read_json(source)
        require(type(value) is dict and evidence['field'] in value,
                'badge JSON evidence field missing')
        return value[evidence['field']]
    if mode == 'adopted-documents':
        rows = read_json(source)
        require(type(rows) is list and rows
                and all(type(row) is dict and type(row.get('id')) is str
                        and row['id'] and row.get('status') == 'adopted' for row in rows),
                'badge adopted document state differs')
        require(len({row['id'] for row in rows}) == len(rows),
                'badge document collection contains duplicate identities')
        return str(len(rows)) + ' adopted'
    if mode == 'python-workflow':
        values = re.findall(r"^\s*python-version:\s*['\"]?([0-9]+\.[0-9]+)['\"]?\s*$", text, re.M)
        require(len(values) == 1, 'badge Python baseline is ambiguous')
        return values[0]
    if mode == 'json-schema':
        value = read_json(source)
        require(type(value) is dict and value.get('type') in {'array', 'object'}
                and (type(value.get('items')) is dict or type(value.get('properties')) is dict),
                'badge schema evidence missing')
        return 'JSON Schema'
    if mode == 'references':
        items = evidence['items']
        require(type(items) is list and items and all(type(x) is str and x.strip() for x in items)
                and len(items) == len(set(items)), 'badge reference items required')
        require(all(item in text for item in items), 'badge reference absent from evidence')
        return ' / '.join(items)
    require(mode == 'text', 'unsupported badge evidence mode')
    require(claim in text, 'badge claim absent from textual evidence')
    return claim


def validate_badge(root, records, badge):
    fields = {'id', 'kind', 'object', 'claim', 'url', 'color', 'target', 'evidence'}
    require(type(badge) is dict and set(badge) == fields, 'badge fields differ')
    require(type(badge['id']) is str and re.fullmatch(r'[a-z][a-z0-9-]*', badge['id']),
            'badge stable ID required')
    require(badge['kind'] in {'status', 'version', 'license', 'technology', 'distribution', 'reference'},
            'unsupported badge claim kind')
    require(all(type(badge[key]) is str and badge[key].strip() for key in ('object', 'claim', 'target')),
            'badge object, claim and target required')
    require(badge['url'] == shields_badge_url(badge['object'], badge['claim'], badge['color']),
            'badge URL or visible claim differs from the Shields static format')
    matches = [row for row in records if row['kind'] == 'image' and row['url'] == badge['url']]
    require(len(matches) == 1 and matches[0]['parent_url'] == badge['target'],
            'badge destination mismatch')
    require(matches[0]['label'] == badge['object'] + ': ' + badge['claim']
            and not matches[0].get('decorative'), 'badge alternative differs from its visible claim')
    require(type(badge['evidence']) is dict, 'badge evidence object required')
    if badge['kind'] == 'reference':
        require(badge['object'] == 'References' and badge['evidence'].get('mode') == 'references',
                'reference badge must retain bounded reference meaning')
    else:
        require(badge['evidence'].get('mode') != 'references',
                'reference evidence cannot certify another claim')
    if badge['kind'] == 'status':
        require(badge['object'] == 'Documents' and badge['evidence'].get('mode') == 'adopted-documents',
                'status badge must use the adopted document collection')
    else:
        require(badge['evidence'].get('mode') != 'adopted-documents',
                'document state cannot certify another claim')
    require(evidence_value(root, badge['evidence'], badge['claim']) == badge['claim'],
            'badge claim does not match source value', badge['id'])


def validate_additional_badges(root, records, contract):
    rows = contract.get('additional_badges', [])
    require(type(rows) is list, 'additional badge list required')
    seen_ids = {contract['badge']['id']}; seen_urls = {contract['badge']['url']}
    for badge in rows:
        validate_badge(root, records, badge)
        require(badge['id'] not in seen_ids and badge['url'] not in seen_urls,
                'duplicate additional badge identity')
        require(badge['kind'] != 'status', 'additional badge cannot replace the collection status')
        seen_ids.add(badge['id']); seen_urls.add(badge['url'])
    return len(rows)
