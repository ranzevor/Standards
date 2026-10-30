"""Check adopted desktop/mobile metadata, clause contracts, sources and file identities."""
from pathlib import Path
import argparse, hashlib, json, re, sys
from urllib.parse import unquote
if sys.flags.optimize:
    raise RuntimeError('optimized Python is unsupported for contract checks')

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from checks.validation_common import read_json, safe_path

ID_RE = re.compile(r'^### ((?:D\d{2}|I\d{2}|S\d{2}|M\d{2}|DT[3-8]-\d{2}|MB[1-7]-\d{2})) ([^\n]+)\n',re.M)
def require_runtime():
    if not __debug__: raise RuntimeError('optimized Python is unsupported for contract checks')

def parse(text, expected_ids, expected_document_id=None, expected_entry=None):
    require_runtime()
    if len(re.findall(r'^# ',text,re.M))!=1: raise ValueError('one title required')
    header=text.split('\n## ',1)[0]
    from tools.verify_release_bundle import valid_version,valid_date
    for field,key,validator in (('版本','version',valid_version),('状态','status',lambda v:v=='adopted'),('生效日期','effective_date',valid_date)):
        values=re.findall(r'\*\*'+re.escape(field)+r'：\*\*[ \t\u3000]*([^\s*]+)',header)
        if len(values)!=1 or not validator(values[0]) or expected_entry is not None and values[0]!=expected_entry[key]:
            raise ValueError('invalid current metadata: '+field)
    identifiers=re.findall(r'\*\*文档ID：\*\*[ \t\u3000]*([^\s*]+)',header)
    if len(identifiers)!=1 or re.fullmatch(r'STD-L4-(?:DESKTOP|MOBILE)-\d{3}',identifiers[0]) is None:
        raise ValueError('invalid current document ID')
    if expected_document_id is not None and identifiers[0]!=expected_document_id:
        raise ValueError('document ID differs from registry')
    found=list(ID_RE.finditer(text)); ids=[h.group(1) for h in found]
    if ids != expected_ids: raise ValueError('clause sequence changed')
    if len(set(ids)) != len(ids): raise ValueError('duplicate clause')
    if re.search(r'\[(?:S|O)\d{2}\](?!\()',text): raise ValueError('unresolved legacy source labels')
    if re.search(r'\b(?:TODO|TBD|PLACEHOLDER)\b',text): raise ValueError('placeholder')
    for h in found:
        tail=text[h.end():]; nxt=re.search(r'^#{2,3} ',tail,re.M)
        body=tail[:nxt.start()] if nxt else tail
        if len(body.strip())<120: raise ValueError('empty obligation')
        if '**正例：**' not in body: raise ValueError('positive missing')
        if not re.search(r'\[DM\d{2}\]\(\.\./\.\./\.\./sources/desktop-mobile-claims.md#dm\d{2}\)',body): raise ValueError('source mapping missing')
        if h.group(1).startswith(('DT','MB')):
            for key in ('**并发、超时、未知与恢复：**','**产物、真实目标入口与判据：**','**直接失败反例：**','**合法邻例：**'):
                if key not in body: raise ValueError('contract field missing: '+key)
            pos=body.split('**正例：**',1)[1].split('**直接失败反例：**',1)[0].strip()
            neg=body.split('**直接失败反例：**',1)[1].split('**合法邻例：**',1)[0].strip()
            neighbor=body.split('**合法邻例：**',1)[1].split('\n',1)[0].strip()
            if len({pos,neg,neighbor})!=3: raise ValueError('indistinct examples')
        elif '**具体目标入口与完成判据：**' not in body:
            raise ValueError('target entry missing')
    return ids

def check(root=ROOT):
    require_runtime(); root=Path(root).resolve()
    entries=[e for e in read_json(safe_path(root,'registry/standards.json')) if e.get('domain') in {'desktop','mobile'}]
    requirements=read_json(safe_path(root,'registry/requirements.json'))
    clause_ids={e['id']:[r['clause_id'] for r in requirements if r['document_id']==e['id']] for e in entries}
    if not entries or any(not ids for ids in clause_ids.values()): raise ValueError('desktop/mobile current registry coverage missing')
    source=read_json(safe_path(root,'sources/desktop-mobile-source-claims.json'))['claims']
    source_ids={s['id'] for s in source}
    if len(source_ids)!=len(source): raise ValueError('duplicate source identity')
    links=0; clauses=0
    for entry in entries:
        from tools.verify_release_bundle import valid_version,valid_date
        if not valid_version(entry.get('version')) or not valid_date(entry.get('effective_date')) or any(entry.get(field)!=value for field,value in (
                ('status','adopted'),('language','zh-Hans'))):
            raise ValueError('invalid current registry metadata: '+entry['id'])
        p=safe_path(root,entry['path']); data=p.read_bytes(); txt=data.decode('utf-8')
        if hashlib.sha256(data).hexdigest()!=entry['sha256']: raise ValueError('current document digest mismatch: '+entry['path'])
        ids=clause_ids[entry['id']]; parse(txt,ids,entry['id'],entry); clauses+=len(ids)
        for source_id in re.findall(r'\[(DM\d{2})\]',txt):
            if source_id not in source_ids: raise ValueError('unknown source '+source_id)
        for target in re.findall(r'\]\(([^)\s]+)\)',txt):
            if '://' in target: continue
            target,_,anchor=unquote(target).partition('#')
            resolved=(p.parent/target).resolve()
            if not resolved.is_relative_to(root): raise ValueError('local link escapes root')
            if not resolved.exists(): raise ValueError('broken link '+str(target))
            if anchor and resolved.suffix=='.md' and f'id="{anchor}"' not in resolved.read_text(encoding='utf-8'):
                raise ValueError('missing explicit source anchor '+anchor)
            links+=1
    versions=sorted({entry['version'] for entry in entries},key=lambda v:tuple(map(int,v.split('.'))))
    return {'documents':len(entries),'clauses':clauses,'sources':len(source),'local_links':links,
            'gate':'current-structure-and-byte-identity','version':versions[0] if len(versions)==1 else None,
            'versions':versions,'status':'adopted',
            'checks':['document-metadata','clause-sequence','contract-fields',
                      'positive-negative-neighbor','source-mappings','local-links']}

def main(argv=None):
    require_runtime(); ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',type=Path,default=ROOT);args=ap.parse_args(argv)
    print(json.dumps(check(args.root),ensure_ascii=False,indent=2));return 0
if __name__=='__main__': raise SystemExit(main())
