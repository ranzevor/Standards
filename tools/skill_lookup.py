"""Look up adopted Standards documents and exact clause spans offline."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

if __name__ == '__main__':
    sys.dont_write_bytecode = True

HERE=Path(__file__).resolve().parent
if (HERE/'verify_bundle.py').is_file():
    from verify_bundle import checked_path,parse_json,validate_registry_bytes,validate_project_release
else:
    sys.path.insert(0,str(HERE.parent))
    from tools.verify_release_bundle import checked_path,parse_json,validate_registry_bytes,validate_project_release
ROOT=HERE.parent/'references' if (HERE.parent/'references').is_dir() else HERE.parent

def find(root: Path,query=None,document_id=None,clause_id=None,domain=None,limit=20):
    root=Path(root)
    if root.is_symlink() or not root.is_dir():raise ValueError('lookup root is not a plain directory')
    root=root.resolve()
    if type(limit) is not int or not 1<=limit<=100:raise ValueError('limit must be 1..100')
    def read(path):
        parts=checked_path(path).parts
        target=root
        for part in parts:
            target=target/part
            if target.is_symlink():raise ValueError('symlink in lookup path: '+path)
        if not target.is_file():raise ValueError('lookup source missing: '+path)
        return target.read_bytes()
    release_version=validate_project_release(parse_json(read('project.json')))
    docs=parse_json(read('registry/standards.json'))
    cache={}
    def normative(path):
        cache[path]=read(path)
        return cache[path]
    validate_registry_bytes(docs,normative)
    if document_id is not None and document_id not in {doc['id'] for doc in docs}:
        raise ValueError('unknown exact document ID: '+str(document_id))
    needle=query.casefold() if query else None
    prefix='references/' if root.name=='references' else ''
    matching=[]
    for doc in docs:
        ident=doc['id']
        if document_id and ident!=document_id:continue
        if domain and doc['domain'].casefold()!=domain.casefold():continue
        if needle and not any(needle in str(doc[key]).casefold() for key in ('id','title','path','domain')):continue
        matching.append({'document_id':ident,'number':ident.rsplit('-',1)[1],
                         'title':doc['title'],'version':doc['version'],
                         'status':doc['status'],'path':prefix+doc['path'],
                         'sha256':doc['sha256'],'domain':doc['domain']})
    if clause_id:
        clauses=parse_json(read('registry/requirements.json'))
        if type(clauses) is not list:raise ValueError('invalid clause registry')
        selected={doc['document_id']:doc for doc in matching}
        registry={doc['id']:doc for doc in docs}
        results=[]
        for row in clauses:
            if type(row) is not dict:raise ValueError('invalid clause registry row')
            if str(row.get('clause_id','')).casefold()!=clause_id.casefold():continue
            doc=selected.get(row.get('document_id'))
            if doc is None:continue
            original=registry[doc['document_id']]
            if row.get('path')!=original['path'] or row.get('version')!=original['version'] or \
               row.get('document_sha256')!=original['sha256']:
                raise ValueError('clause document identity mismatch')
            start,end=row.get('line'),row.get('end_line')
            lines=cache[original['path']].splitlines(keepends=True)
            if type(start) is not int or type(end) is not int or not 1<=start<=end<=len(lines):
                raise ValueError('invalid clause span')
            digest=hashlib.sha256(b''.join(lines[start-1:end])).hexdigest()
            if digest!=row.get('section_sha256'):raise ValueError('clause content digest mismatch')
            results.append({**doc,'clause_id':row['clause_id'],'line':start,'end_line':end,
                            'section_sha256':digest})
        matching=results
    return {'version':release_version,'total':len(matching),'results':matching[:limit]}

def main(argv=None):
    # JSON redirected to a file or pipe is always UTF-8, including Windows
    # hosts with a legacy console code page. Imported find() has no I/O effects.
    for stream in (sys.stdout,sys.stderr):
        if callable(getattr(stream,'reconfigure',None)):
            stream.reconfigure(encoding='utf-8',newline='\n')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--query');parser.add_argument('--document-id')
    parser.add_argument('--clause-id');parser.add_argument('--domain')
    parser.add_argument('--limit',type=int,default=20)
    args=parser.parse_args(argv)
    if not 1<=args.limit<=100:parser.error('limit must be 1..100')
    try:
        result=find(args.root,args.query,args.document_id,args.clause_id,args.domain,args.limit)
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print('lookup failed: '+str(exc),file=sys.stderr);return 1
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0

if __name__=='__main__':raise SystemExit(main())
