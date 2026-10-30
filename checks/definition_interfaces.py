"""Resolve the named L0 definition block and its explicitly delegated consumers."""
from pathlib import Path
import argparse
import hashlib
from html.parser import HTMLParser
import json
import posixpath
import re
import sys
import urllib.parse

if sys.flags.optimize:
    raise RuntimeError('Definition interfaces require normal Python mode; do not use -O or -OO')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from checks.validation_common import read_json, safe_path, require
from checks.corpus_contract import markdown_blocks, references, slug, anchors, INLINE_CODE

ROOT = Path(__file__).resolve().parents[1]
PROVIDER = 'STD-L0-001'
CONSUMER = 'STD-L4-MODEL-RESEARCH-006'
PROVIDER_CLAUSE = 'ARC-06'
DEFINITION_ANCHOR = 'normative-strength-terms'
CONSUMER_ANCHOR = 'research-normative-strength-consumption'
INTERFACE = 'normative-strength-terms: L0唯一前言定义的准确版本解释'
CONDITION = '该已选择条款适用且需解释其规范性强度与术语时；仅消费词典，不因此采用L0其他技术要求'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _block(text, anchor):
    require(anchor in anchors(text),'definition/consumer anchor missing or ambiguous',anchor)
    matches=[]
    class Locate(HTMLParser):
        def handle_starttag(self,tag,attrs):
            if any(name=='id'and value==anchor for name,value in attrs):self.found+=1
    for block in markdown_blocks(text):
        if block['kind']in {'code','comment'}:continue
        parser=Locate(convert_charrefs=True);parser.found=0
        parser.feed(INLINE_CODE.sub('',block['visible_text']))
        if parser.found:matches.append(block)
    require(len(matches)==1 and matches[0]['kind']=='paragraph','named definition must resolve to one complete paragraph',anchor)
    return matches[0]


def _local_link(text, source, target, fragment):
    for ref in references(text):
        url = urllib.parse.urlsplit(ref['url'])
        if url.scheme or url.netloc:
            continue
        path = posixpath.normpath(posixpath.join(posixpath.dirname(source), urllib.parse.unquote(url.path))) if url.path else source
        if path == target and urllib.parse.unquote(url.fragment) == fragment:
            return True
    return False


def describe(root=ROOT):
    root = Path(root).resolve()
    entries = {e['id']: e for e in read_json(root / 'registry/standards.json')}
    require(PROVIDER in entries, 'definition provider document missing')
    provider = entries[PROVIDER]
    raw = safe_path(root, provider['path']).read_bytes()
    require(sha(raw) == provider['sha256'], 'definition provider source drift')
    text = raw.decode('utf-8')
    clauses = read_json(root / 'registry/requirements.json')
    providers = [c for c in clauses if c['document_id'] == PROVIDER and c['clause_id'] == PROVIDER_CLAUSE]
    require(len(providers) == 1, 'definition provider clause missing or ambiguous')
    clause = providers[0]
    block = _block(text, DEFINITION_ANCHOR)
    require(block['line'] < clause['line'], 'definition must be the separately provided preamble, not a second clause dictionary')
    section = ''.join(text.splitlines(keepends=True)[clause['line'] - 1:clause['end_line']])
    require(_local_link(section, provider['path'], provider['path'], DEFINITION_ANCHOR), 'provider clause does not point to the sole definition block')
    result = {
        'schema': 'standards-definition-reference/1', 'interface_id': INTERFACE,
        'document_id': PROVIDER, 'version': provider['version'], 'path': provider['path'],
        'sha256': provider['sha256'], 'clause_id': PROVIDER_CLAUSE,
        'definition_anchor': DEFINITION_ANCHOR, 'definition_sha256': block['sha256'],
    }
    consumers = []
    if CONSUMER in entries:
        consumer = entries[CONSUMER]
        data = safe_path(root, consumer['path']).read_bytes()
        require(sha(data) == consumer['sha256'], 'definition consumer source drift')
        body = data.decode('utf-8')
        selected = _block(body, CONSUMER_ANCHOR)
        provider_anchor = slug(clause['heading'])
        require(_local_link(selected['text'], consumer['path'], provider['path'], provider_anchor), 'consumer provider-clause reference missing')
        require(_local_link(selected['text'], consumer['path'], provider['path'], DEFINITION_ANCHOR), 'consumer sole-definition reference missing')
        ids = [c['clause_id'] for c in clauses if c['document_id'] == CONSUMER]
        require(ids and len(ids) == len(set(ids)), 'definition consumer clauses missing/duplicate')
        consumers.append({'document_id': CONSUMER, 'version': consumer['version'], 'path': consumer['path'],
                          'sha256': consumer['sha256'], 'clause_ids': ids, 'anchor': CONSUMER_ANCHOR,
                          'block_sha256': selected['sha256'], 'condition': CONDITION})
    return {'reference': result, 'definition_location': {'line': block['line'], 'end_line': block['end_line']},
            'provider_clause_anchor': slug(clause['heading']), 'consumers': consumers}


def resolve_definition(reference, root=ROOT):
    expected = describe(root)['reference']
    require(type(reference) is dict and set(reference) == set(expected), 'definition reference shape')
    for key in ('schema', 'interface_id', 'document_id', 'version', 'path', 'clause_id', 'definition_anchor'):
        require(type(reference[key]) is str and reference[key] == expected[key], 'definition provider endpoint mismatch', key)
    for key in ('sha256', 'definition_sha256'):
        require(reference[key] == expected[key], 'definition identity drift', key)
    return dict(expected)


def expected_edges(root=ROOT):
    d = describe(root)
    provider = d['reference']
    catalog = {e['id']:e for e in read_json(Path(root)/'registry/standards.json')}
    rows = []
    for consumer in d['consumers']:
        for ident in consumer['clause_ids']:
            rows.append({
                'from_document': consumer['document_id'], 'from_clause': ident,
                'from_path': consumer['path'], 'from_sha256': consumer['sha256'],
                'to_document': provider['document_id'], 'to_clause': provider['clause_id'],
                'to_path': provider['path'], 'to_version': provider['version'], 'to_sha256': provider['sha256'],
                'to_anchor': d['provider_clause_anchor'], 'interface': INTERFACE,
                'condition': CONDITION, 'state': 'adopted-technical-reference', 'required': True, 'family': 'normative-definition-consumption',
                'semantic_basis': 'Explicit whole-document terminology delegation at the named consumer paragraph; each selected clause consumes the same uniquely anchored definition, not an arbitrary Markdown link.',
                'verification_owner': '提供方维护唯一前言定义和准确接口；采用者锁定版本/摘要并按实际选择判断适用；引用不产生采用决定或操作权限',
            })
    return rows


def validate_record_consumption(record, root=ROOT):
    """The pure, applicable terminology condition; not arbitrary environment-dependent edges."""
    chosen={(x['document_id'],x['clause_id']):x for x in record['requirements']}
    consumers=[k for k,x in chosen.items()if k[0]==CONSUMER and x['applicability']=='applicable']
    if not consumers:return 0
    provider=(PROVIDER,PROVIDER_CLAUSE)
    require(provider in chosen and chosen[provider]['applicability']=='applicable','definition required provider missing or not applicable')
    edges={((d['from']['document_id'],d['from']['clause_id']),(d['to']['document_id'],d['to']['clause_id']),d['interface'],d['kind'])for d in record['dependencies']}
    for consumer in consumers:
        require((consumer,provider,INTERFACE,'required-consumption')in edges,'definition required consumption missing or wrong provider')
    resolve_definition(describe(root)['reference'],root)
    return len(consumers)


def validate(root=ROOT):
    root = Path(root).resolve()
    entries = read_json(root / 'registry/standards.json')
    if not any(e['id'] == CONSUMER for e in entries):
        return {'interfaces': 0, 'scope': 'This collection does not declare the research terminology consumer'}
    expected = expected_edges(root)
    actual = [e for e in read_json(root / 'registry/technical-dependencies.json') if e['interface'] == INTERFACE]
    key = lambda e: (e['from_document'], e['from_clause'], e['to_document'], e['to_clause'], e['interface'])
    require(len(actual) == len({key(e) for e in actual}), 'duplicate definition consumption')
    require({key(e) for e in actual} == {key(e) for e in expected}, 'definition dependency set missing or wrong provider')
    expected_by_key = {key(e): e for e in expected}
    for e in actual:
        require(all(e.get(k) == v for k, v in expected_by_key[key(e)].items()), 'definition dependency contract drift')
    description = describe(root)
    resolve_definition(description['reference'], root)
    return {'interfaces': 1, 'necessary_clause_consumers': len(actual),
            'reference': description['reference'], 'definition_location': description['definition_location'],
            'scope': 'Named source/block identity, exact required provider and registered consumer closure; '
                     'not natural-language semantic review, adoption or business authorization.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=ROOT)
    a = p.parse_args()
    print(json.dumps(validate(a.root), ensure_ascii=False, sort_keys=True))
