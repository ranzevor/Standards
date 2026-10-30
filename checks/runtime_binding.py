"""Full-body identity and explicit clause/field binding; not semantic certification."""
from pathlib import Path
import hashlib
import json
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if sys.flags.optimize:
    raise RuntimeError('optimized evidence entry unsupported')

HEADING=re.compile(r'^(#{1,6})\s+(.+?)\s*$',re.M)
CLAUSE=re.compile(r'^(?:§\d{2}|M\d{2}|AUT-\d{2}|(?:G-SIM|G-STATE|G-ASSET|G-DELIVERY|CLI-PROC|SDK-API|CLI-PKG|CLI-EXT|NET-WIRE|NET-FLOW|NET-MEDIA|AUT-TIME|AUT-HOOK|AUT-SYNC|AUT-EFFECT|AUT-RPA)-\d{2})(?:\s|$)')
FIELDS=['触发/前置','必要机制','不变量','并发、超时、未知与恢复','产物与观察点','正例','直接失败','合法邻例','可观察验收','来源与限制']
FIELD=re.compile(r'^- \*\*([^*]+)：\*\*\s*(.*?)(?=^- \*\*|\Z)',re.M|re.S)

def norm(text):return re.sub(r'\s+',' ',text).strip()
def sha(data):return hashlib.sha256(data).hexdigest()

def split_sections(text):
    headings=list(HEADING.finditer(text))
    if not headings or headings[0].start()!=0:raise ValueError('missing document heading')
    sections=[]
    for i,m in enumerate(headings):
        end=headings[i+1].start() if i+1<len(headings) else len(text)
        sections.append({'level':len(m[1]),'heading':m[2],'start':m.start(),'end':end,
                         'line_start':text.count('\n',0,m.start())+1,
                         'line_end':text.count('\n',0,end)+(0 if text[:end].endswith('\n') else 1),
                         'body':text[m.end():end], 'text':text[m.start():end]})
    return sections

def table_check(text):
    columns=None
    for line in text.splitlines():
        if line.startswith('|'):
            if not line.endswith('|'):raise ValueError('orphan table row')
            n=len(re.split(r'(?<!\\)\|',line))-2
            if columns is None:columns=n
            if n!=columns:raise ValueError('malformed table row')
        else:columns=None

def make_profile(path,text):
    sections=split_sections(text);clauses=[]
    for s in sections:
        if CLAUSE.match(s['heading']):
            cid=s['heading'].split()[0]
            fields={m[1]:norm(m[2]) for m in FIELD.finditer(s['body'])}
            clauses.append({'id':cid,'heading':s['heading'],'line_start':s['line_start'],
                            'line_end':s['line_end'],'normalized_text':norm(s['text']),
                            'sha256':sha(s['text'].encode()),'fields':fields})
    return {'path':path,'sha256':sha(text.encode()),
            'sections':[{'level':s['level'],'heading':s['heading'],'line_start':s['line_start'],
                         'line_end':s['line_end'],'normalized_text':norm(s['text']),
                         'sha256':sha(s['text'].encode())} for s in sections],
            'clauses':clauses,'all_nonempty_lines_bound':True}

def validate_document(text,profile):
    sections=split_sections(text);table_check(text)
    actual=[s for s in sections if CLAUSE.match(s['heading'])]
    ids=[s['heading'].split()[0] for s in actual]
    if len(ids)!=len(set(ids)):raise ValueError('duplicate clause')
    if ids!=[c['id'] for c in profile['clauses']]:raise ValueError('clause set or order mismatch')
    for s,expected in zip(actual,profile['clauses']):
        pairs=list(FIELD.finditer(s['body']))
        fields={m[1]:norm(m[2]) for m in pairs}
        if expected['fields']:
            if len(pairs)!=len(fields):raise ValueError('duplicate clause field')
            if list(fields)!=list(expected['fields']):raise ValueError('clause field set/order')
            if any(not v or v in ('TODO','TBD','待补','...') for v in fields.values()):raise ValueError('placeholder clause field')
            if '直接失败' in fields and fields['直接失败']==fields.get('合法邻例'):raise ValueError('failure equals legal neighbor')
            if fields!=expected['fields']:raise ValueError('clause-field binding mismatch')
        elif norm(s['text'])!=expected['normalized_text']:
            raise ValueError('baseline clause binding mismatch')
    if [(s['level'],s['heading']) for s in sections]!=[(s['level'],s['heading']) for s in profile['sections']]:
        raise ValueError('full-body heading profile mismatch')
    for s,expected in zip(sections,profile['sections']):
        if norm(s['text'])!=expected['normalized_text']:raise ValueError('complete section binding mismatch')
    return {'clauses':len(actual),'sections':len(sections),'normalized_binding':'pass','byte_identity':sha(text.encode())==profile['sha256']}

def main():
    from checks.repository_registry import validate_entries
    from checks.corpus_contract import extract_document
    from checks.validation_common import read_json, require
    root = Path(__file__).resolve().parents[1]
    entries = [e for e in validate_entries(root) if e['domain'] in {'automation', 'cli-sdk', 'game', 'network-realtime'}]
    indexed = read_json(root/'registry/requirements.json')
    results = []
    for entry in entries:
        text = (root/entry['path']).read_text()
        table_check(text)
        clauses = extract_document(entry, text)['clauses']
        expected = [c for c in indexed if c['document_id'] == entry['id']]
        require(clauses == expected, 'runtime domain clause binding drift', entry['id'])
        results.append({'document_id': entry['id'], 'clauses': len(clauses)})
    print(json.dumps({'documents': len(results), 'clauses': sum(x['clauses'] for x in results), 'results': results}, ensure_ascii=False, indent=2))

if __name__ == '__main__': main()
