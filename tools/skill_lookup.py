"""Look up adopted Standards documents and exact clause spans offline."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

if __name__ == '__main__':
    sys.dont_write_bytecode = True

HERE=Path(__file__).resolve().parent
if (HERE/'verify_bundle.py').is_file():
    from verify_bundle import (checked_path,parse_json,validate_registry_bytes,
                           validate_project_release,validate_clause_registry,_decode_physical_line)
else:
    sys.path.insert(0,str(HERE.parent))
    from tools.verify_release_bundle import (checked_path,parse_json,validate_registry_bytes,
                                         validate_project_release,validate_clause_registry,_decode_physical_line)
ROOT=HERE.parent/'references' if (HERE.parent/'references').is_dir() else HERE.parent


class LookupInputError(ValueError):
    """An invalid filter or unregistered exact document identity."""


class LookupSourceMissing(ValueError):
    """A required released file is missing."""


def _casefold_match(text: str, needle: str):
    """Return original character bounds for a Unicode casefolded substring match."""
    folded_parts = []
    starts = []
    ends = []
    for index, char in enumerate(text):
        folded = char.casefold()
        folded_parts.append(folded)
        starts.extend([index] * len(folded))
        ends.extend([index + 1] * len(folded))
    position = ''.join(folded_parts).find(needle)
    if position < 0:
        return None
    return starts[position], ends[position + len(needle) - 1]


def _matched_excerpt(text: str, start: int, end: int, limit: int = 240) -> str:
    """Keep a bounded, match-centred excerpt that always includes the matched text."""
    width = max(limit, end - start)
    if len(text) <= width:
        return text
    left = max(0, min(start - (width - (end - start)) // 2, len(text) - width))
    right = left + width
    return ('…' if left else '') + text[left:right] + ('…' if right < len(text) else '')

def find(root: Path,query=None,document_id=None,clause_id=None,domain=None,limit=20,text_query=None,*,offset=0,text_all=None):
    root=Path(root)
    if root.is_symlink() or not root.is_dir():raise LookupInputError('lookup root is not a plain directory')
    root=root.resolve()
    if type(limit) is not int or not 1<=limit<=100:raise LookupInputError('limit must be 1..100')
    if type(offset) is not int or offset<0:raise LookupInputError('offset must be a nonnegative integer')
    for label,value in (('query',query),('document-id',document_id),('clause-id',clause_id),('domain',domain)):
        if value is not None and (type(value) is not str or not value.strip() or len(value)>256):
            raise LookupInputError(label+' must be 1..256 nonblank characters')
    def read(path):
        parts=checked_path(path).parts
        target=root
        for part in parts:
            target=target/part
            if target.is_symlink():raise ValueError('symlink in lookup path: '+path)
        if not target.is_file():raise LookupSourceMissing('lookup source missing: '+path)
        return target.read_bytes()
    release_version=validate_project_release(parse_json(read('project.json')))
    docs=parse_json(read('registry/standards.json'))
    cache={}
    document_lines={}
    def normative(path):
        cache[path]=read(path)
        return cache[path]
    validate_registry_bytes(docs,normative)
    if document_id is not None and document_id not in {doc['id'] for doc in docs}:
        raise LookupInputError('unknown exact document ID: '+str(document_id)+'; search the document registry with --query before selecting a document ID')
    if text_all is None:
        text_all=()
    if type(text_all) not in (list,tuple):raise LookupInputError('text-all must be a list of literal terms')
    terms=([text_query] if text_query is not None else [])+list(text_all)
    if len(terms)>8:raise LookupInputError('at most eight text-query terms are supported')
    text_needles=[]
    seen_terms=set()
    for term in terms:
        if type(term) is not str or not term.strip() or len(term)>256 or any(chr(c) in term for c in (0,10,13)):
            raise LookupInputError('text-query must be 1..256 nonblank characters')
        folded=term.casefold()
        if folded not in seen_terms:
            text_needles.append((term,folded))
            seen_terms.add(folded)
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
    if clause_id or text_needles:
        clauses=parse_json(read('registry/requirements.json'))
        selected={doc['document_id']:doc for doc in matching}
        # Check every indexed clause for the selected documents before filtering.
        validate_clause_registry(clauses,docs,lambda path:cache[path],set(selected))
        results=[]
        for row in clauses:
            if clause_id and row['clause_id'].casefold()!=clause_id.casefold():continue
            doc=selected.get(row['document_id'])
            if doc is None:continue
            path=row['path']
            if path not in document_lines:
                document_lines[path]=cache[path].splitlines(keepends=True)
            lines=document_lines[path]
            start,end=row['line'],row['end_line']
            normative_start,normative_end=row['normative_start_line'],row['normative_end_line']
            result={**doc,'clause_id':row['clause_id'],'line':start,'end_line':end,
                    'section_sha256':row['section_sha256'],'normative_start_line':normative_start,
                    'normative_end_line':normative_end,'normative_sha256':row['normative_sha256']}
            if text_needles:
                term_matches=[]
                for term,text_needle in text_needles:
                    matched=None
                    for line_offset,raw_line in enumerate(lines[normative_start-1:normative_end]):
                        line_text=_decode_physical_line(raw_line)
                        bounds=_casefold_match(line_text,text_needle)
                        if bounds is not None:
                            matched=(normative_start+line_offset,line_text,bounds)
                            break
                    if matched is None:break
                    line_number,line_text,(match_start,match_end)=matched
                    term_matches.append({'text_query':term,'matched_line':line_number,
                                         'matched_excerpt':_matched_excerpt(line_text,match_start,match_end)})
                if len(term_matches)!=len(text_needles):continue
                result['matched_line']=term_matches[0]['matched_line']
                result['matched_excerpt']=term_matches[0]['matched_excerpt']
                if len(term_matches)>1:result['term_matches']=term_matches
            results.append(result)
        matching=results
    return {'version':release_version,'total':len(matching),'results':matching[offset:offset+limit]}

def error_detail(exc):
    if isinstance(exc,LookupInputError):
        code,action='INVALID_QUERY','Correct the query or exact identifier.'
    elif isinstance(exc,LookupSourceMissing):
        code,action='SOURCE_MISSING','Restore the missing file from the verified release.'
    elif isinstance(exc,OSError):
        code,action='IO_ERROR','Check filesystem access and retry the lookup.'
    else:
        code,action='INTEGRITY_ERROR','Restore the verified release before citing clauses.'
    return {'code':code,'message':str(exc),'next_action':action}


def main(argv=None):
    # JSON redirected to a file or pipe is always UTF-8, including Windows
    # hosts with a legacy console code page. Imported find() has no I/O effects.
    for stream in (sys.stdout,sys.stderr):
        if callable(getattr(stream,'reconfigure',None)):
            stream.reconfigure(encoding='utf-8',newline='\n')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--query',help='Case-insensitive document metadata search (ID, title, path, domain)');parser.add_argument('--document-id',help='Exact registered document ID')
    parser.add_argument('--clause-id',help='Exact clause ID within selected documents; zero matches do not prove inapplicability');parser.add_argument('--domain')
    parser.add_argument('--text-query',action='append',help='Literal text in a verified clause; repeat for AND matching inside one clause (up to 8)')
    parser.add_argument('--limit',type=int,default=20)
    parser.add_argument('--offset',type=int,default=0,help='Skip this many filtered results; retain registry order')
    parser.add_argument('--error-json',action='store_true',help='Write categorized runtime lookup failures as JSON to stderr')
    args=parser.parse_args(argv)
    try:
        if not 1<=args.limit<=100:
            if not args.error_json:parser.error('limit must be 1..100')
            raise LookupInputError('limit must be 1..100')
        if args.offset<0:
            if not args.error_json:parser.error('offset must be a nonnegative integer')
            raise LookupInputError('offset must be a nonnegative integer')
        terms=args.text_query or []
        result=find(args.root,args.query,args.document_id,args.clause_id,args.domain,args.limit,
                    terms[0] if terms else None,offset=args.offset,text_all=terms[1:])
    except (ValueError,OSError,KeyError,TypeError) as exc:
        if args.error_json:
            print(json.dumps(error_detail(exc),ensure_ascii=False),file=sys.stderr)
        else:
            print('lookup failed: '+str(exc),file=sys.stderr)
        return 1
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0

if __name__=='__main__':raise SystemExit(main())
