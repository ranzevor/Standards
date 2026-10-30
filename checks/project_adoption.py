"""Validate versioned adoption records; record consistency is not real authority."""
from __future__ import annotations
import sys
if sys.flags.optimize:
    raise RuntimeError('Validation requires assertions enabled; do not use -O or -OO')
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from checks.validation_common import read_json
from checks.finite_schema import schema_check
HASH = re.compile(r'[0-9a-f]{64}\Z')
STATES = {'not-run', 'partial', 'fail', 'pass', 'unknown', 'not-applicable'}
LEVELS = {'document-structure', 'semantic-review', 'finite-model', 'isolated-implementation', 'real-business'}

def need(condition, message):
    if not condition:
        raise ValueError(message)

def nonempty(value):
    return type(value) is str and bool(value.strip())

def exact_keys(value, required, optional=()):
    need(type(value) is dict, 'expected object')
    need(set(required) <= set(value), 'missing fields: ' + repr(set(required)-set(value)))
    need(set(value) <= set(required)|set(optional), 'unknown fields: ' + repr(set(value)-set(required)-set(optional)))

def timestamp(value):
    need(nonempty(value), 'timestamp missing')
    try:
        parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
    except (ValueError, TypeError) as e:
        raise ValueError('invalid timestamp') from e
    need(parsed.tzinfo is not None, 'timestamp needs time zone')
    return parsed.astimezone(timezone.utc)

def safe_file(root, relative):
    need(nonempty(relative), 'path missing')
    path=PurePosixPath(relative)
    need(not path.is_absolute() and '..' not in path.parts and '\\' not in relative, 'unsafe relative path')
    resolved=(root/path).resolve()
    need(resolved.is_relative_to(root.resolve()), 'path escapes root')
    need(resolved.is_file(), 'missing file: '+relative)
    return resolved

def validate_record(record, entries, clauses=None, root=None):
    """Check a record, optionally resolving current exact documents and clause IDs."""
    exact_keys(record, ['schema_version','id','example_only','operation_authorized','project','decision','standards','requirements','dependencies','implementation'])
    need(record['schema_version']=='1.0' and nonempty(record['id']), 'record identity')
    need(type(record['example_only']) is bool and type(record['operation_authorized']) is bool, 'boolean fields')
    exact_keys(record['project'], ['id','kind'])
    need(nonempty(record['project']['id']) and record['project']['kind'] in {'synthetic','real-project'}, 'project identity')
    if record['example_only']:
        need(record['project']['kind']=='synthetic' and not record['operation_authorized'], 'example is not an authorization')
    decision=record['decision']; exact_keys(decision,['status','actor','authority_reference','at'])
    need(decision['status'] in {'not-decided','adopted','rejected','withdrawn'}, 'decision state')
    if decision['status']=='not-decided':
        need(all(decision[x] is None for x in ['actor','authority_reference','at']), 'undecided cannot invent a decision')
    else:
        need(not record['example_only'], 'example cannot claim real adoption')
        need(nonempty(decision['actor']) and nonempty(decision['authority_reference']), 'decision attribution')
        timestamp(decision['at'])
    catalog={e['id']:e for e in entries}
    need(len(catalog)==len(entries), 'duplicate catalog identity')
    selected={}
    need(type(record['standards']) is list, 'standards list')
    for selection in record['standards']:
        exact_keys(selection,['id','version','sha256','path','selection'])
        sid=selection['id']; need(sid in catalog and sid not in selected, 'unknown or duplicate selected document')
        expected=catalog[sid]
        for field in ['version','sha256','path']:
            need(selection[field]==expected[field], 'selected '+field+' drift')
        need(HASH.fullmatch(selection['sha256']) is not None, 'selected digest')
        need(selection['selection'] in {'technical-reference','trial','adopted'}, 'selection type')
        if selection['selection']=='adopted':
            need(decision['status']=='adopted' and not record['example_only'], 'adoption needs actual attributed decision')
        if root is not None:
            data=safe_file(root,selection['path']).read_bytes()
            need(hashlib.sha256(data).hexdigest()==selection['sha256'], 'selected bytes drift')
        selected[sid]=selection
    known=None
    if clauses is not None:
        known={}
        for c in clauses:
            need(type(c) is dict and nonempty(c.get('document_id')) and nonempty(c.get('clause_id')),
                 'canonical document and clause identities required')
            known.setdefault(c['document_id'],set()).add(c['clause_id'])
    need(type(record['requirements']) is list,'requirements list'); by_key={}
    for item in record['requirements']:
        exact_keys(item,['document_id','clause_id','applicability','reason','checks'])
        sid,cid=item['document_id'],item['clause_id']; key=(sid,cid)
        need(sid in selected and nonempty(cid) and key not in by_key,'unknown or duplicate requirement')
        if known is not None: need(cid in known.get(sid,set()),'unknown clause identity')
        need(item['applicability'] in {'applicable','not-applicable','undetermined'},'applicability state')
        need(nonempty(item['reason']),'applicability reason')
        need(type(item['checks']) is list,'checks list'); ids=set()
        for check in item['checks']:
            exact_keys(check,['id','evidence_level','command','expected','actual','status','evidence'])
            need(nonempty(check['id']) and check['id'] not in ids,'duplicate or empty check id');ids.add(check['id'])
            need(check['evidence_level'] in LEVELS and nonempty(check['command']) and nonempty(check['expected']),'check contract')
            need(check['status'] in STATES,'check status')
            need(type(check['evidence']) is list,'evidence list')
            need(all(nonempty(reference) for reference in check['evidence']),'evidence reference must be a nonempty string')
            if check['status']=='not-run': need(check['actual'] is None and not check['evidence'],'unrun result must not invent evidence')
            elif check['status'] not in {'not-applicable'}:
                need(nonempty(check['actual']) and bool(check['evidence']),'executed result requires actual evidence')
            if record['example_only']:
                need(check['status']=='not-run','adoption example must not impersonate executed project')
            if item['applicability']!='applicable': need(check['status'] in {'not-run','not-applicable'},'nonapplicable requirement cannot claim runtime pass')
        if item['applicability']=='applicable': need(bool(item['checks']),'applicable requires check contract')
        by_key[key]=item
    # Dependencies here are necessary consumption edges, not all Markdown references.
    need(type(record['dependencies']) is list,'dependencies list'); seen=set(); edges={key:set() for key in by_key}
    for dep in record['dependencies']:
        exact_keys(dep,['from','to','interface','kind'])
        need(dep['kind'] in {'required-consumption','technical-reference'},'dependency kind')
        need(nonempty(dep['interface']),'dependency interface')
        def endpoint(value):
            exact_keys(value,['document_id','clause_id'])
            key=(value['document_id'],value['clause_id']); need(key in by_key,'dependency endpoint missing');return key
        a,b=endpoint(dep['from']),endpoint(dep['to']);need(a!=b,'self dependency')
        identity=(a,b,dep['kind']); need(identity not in seen,'duplicate dependency');seen.add(identity)
        if dep['kind']=='required-consumption':
            need(by_key[a]['applicability']!='applicable' or by_key[b]['applicability']=='applicable','required dependency not applicable')
            edges[a].add(b)
    # Reference cycles are legal. Necessary execution/approval cycles are not a closure proof.
    active=set();done=set()
    def visit(key):
        need(key not in active,'necessary dependency cycle')
        if key in done:return
        active.add(key)
        for nxt in edges[key]:visit(nxt)
        active.remove(key);done.add(key)
    for key in edges:visit(key)
    definition_consumptions=0
    if root is not None and any(x['document_id']=='STD-L4-MODEL-RESEARCH-006'and x['applicability']=='applicable'for x in record['requirements']):
        from checks.definition_interfaces import validate_record_consumption
        definition_consumptions=validate_record_consumption(record,root)
    implementation=record['implementation'];exact_keys(implementation,['status','identity','environment','scope'])
    need(implementation['status'] in STATES,'implementation state')
    need(nonempty(implementation['identity']) and nonempty(implementation['environment']) and nonempty(implementation['scope']),'implementation identity/scope')
    if record['example_only']:need(implementation['status']=='not-run','example has no real implementation acceptance')
    if implementation['status']=='pass':
        applicable=[r for r in by_key.values() if r['applicability']=='applicable']
        need(bool(applicable),'implementation pass lacks applicable target scope')
        for requirement in applicable:
            relevant=[c for c in requirement['checks'] if c['evidence_level'] in {'isolated-implementation','real-business'}]
            need(bool(relevant) and all(c['status']=='pass' for c in relevant),'implementation pass lacks actual target checks for a selected requirement')
        need(not any(r['applicability']=='undetermined' for r in by_key.values()),'implementation pass with unresolved applicability')
    return {'record':record['id'],'documents':len(selected),'selected_requirements':len(by_key),'result':'record-consistency-only','authority_established':False}

def validate_examples(root=ROOT):
    root=Path(root).resolve()
    entries=read_json(root/'registry/standards.json')
    clauses=read_json(root/'registry/requirements.json')
    paths=sorted((root/'examples/adoption-contracts').glob('*.json'))
    need(bool(paths),'no multi-domain adoption examples')
    schema=read_json(root/'registry/schemas/project-adoption.schema.json')
    result=[]
    for path in paths:
        record=read_json(path)
        schema_check(record,schema)
        result.append(validate_record(record,entries,clauses,root))
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--record',type=Path,help='check a supplied record against exact documents; does not authenticate authority')
    args=parser.parse_args()
    if args.record:
        entries=read_json(args.root/'registry/standards.json')
        clauses=read_json(args.root/'registry/requirements.json')
        result=validate_record(read_json(args.record),entries,clauses,args.root)
    else:result=validate_examples(args.root)
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
