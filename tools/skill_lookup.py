"""Look up adopted Standards documents and exact clause spans offline."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
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


def _decode_physical_line(raw: bytes) -> str:
    """Decode one bytes.splitlines() record without Unicode line-separator splitting."""
    if raw.endswith(b'\r\n'):
        raw = raw[:-2]
    elif raw.endswith((b'\r', b'\n')):
        raw = raw[:-1]
    return raw.decode('utf-8')


def _markdown_headings(lines: list[bytes]) -> dict[int, tuple[int, str]]:
    """Locate headings using the corpus parser's fence and comment semantics."""
    result = {}
    fence = None
    in_comment = False
    for number, raw in enumerate(lines, 1):
        line = _decode_physical_line(raw)
        if fence is not None:
            marker, width = fence
            if re.fullmatch(r'[ \t]{0,3}' + re.escape(marker) + '{' + str(width) + r',}[ \t]*', line):
                fence = None
            continue
        if not in_comment:
            opening = re.match(r'^[ \t]{0,3}(`{3,}|~{3,})', line)
            if opening:
                fence = (opening[1][0], len(opening[1]))
                continue
        visible = list(line)
        offset = 0
        while offset < len(line):
            if in_comment:
                if line.startswith('<!--', offset):
                    raise ValueError('nested Markdown comment in indexed document')
                if line.startswith('-->', offset):
                    visible[offset:offset + 3] = '   '
                    offset += 3
                    in_comment = False
                    continue
                visible[offset] = ' '
                offset += 1
                continue
            if line[offset] == '`':
                ticks = re.match(r'`+', line[offset:])[0]
                closing = line.find(ticks, offset + len(ticks))
                if closing >= 0:
                    offset = closing + len(ticks)
                    continue
            if line.startswith('<!--', offset):
                visible[offset:offset + 4] = '    '
                offset += 4
                in_comment = True
                continue
            offset += 1
        heading = re.fullmatch(r'(#{1,6})[ \t]+(.+?)(?:[ \t]+#+)?[ \t]*', ''.join(visible))
        if heading:
            result[number] = (len(heading[1]), heading[2])
    if fence is not None or in_comment:
        raise ValueError('unclosed Markdown fence or comment in indexed document')
    return result


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

def find(root: Path,query=None,document_id=None,clause_id=None,domain=None,limit=20,text_query=None):
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
    document_lines={}
    document_headings={}
    def normative(path):
        cache[path]=read(path)
        return cache[path]
    validate_registry_bytes(docs,normative)
    if document_id is not None and document_id not in {doc['id'] for doc in docs}:
        raise ValueError('unknown exact document ID: '+str(document_id))
    if text_query is not None:
        if type(text_query) is not str or not text_query.strip() or len(text_query)>256 or any(chr(c) in text_query for c in (0, 10, 13)):
            raise ValueError('text-query must be 1..256 nonblank characters')
        text_needle=text_query.casefold()
    else:
        text_needle=None
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
    if clause_id or text_needle is not None:
        clauses=parse_json(read('registry/requirements.json'))
        if type(clauses) is not list:raise ValueError('invalid clause registry')
        selected={doc['document_id']:doc for doc in matching}
        registry={doc['id']:doc for doc in docs}
        seen_clause_ids=set()
        results=[]
        for row in clauses:
            if type(row) is not dict:raise ValueError('invalid clause registry row')
            row_document_id=row.get('document_id')
            row_clause_id=row.get('clause_id')
            if (
                type(row_document_id) is not str or not row_document_id or
                type(row_clause_id) is not str or not row_clause_id or
                row.get('id') != row_document_id + '::' + row_clause_id
            ):
                raise ValueError('clause registry identity mismatch')
            identity=(row_document_id,row_clause_id)
            if identity in seen_clause_ids:
                raise ValueError('duplicate clause registry identity')
            seen_clause_ids.add(identity)
            if clause_id and row_clause_id.casefold()!=clause_id.casefold():continue
            doc=selected.get(row_document_id)
            if doc is None:continue
            original=registry[row_document_id]
            if (
                row.get('path') != original['path'] or
                row.get('document') != original['path'] or
                row.get('version') != original['version'] or
                row.get('document_sha256') != original['sha256']
            ):
                raise ValueError('clause document identity mismatch')
            start,end=row.get('line'),row.get('end_line')
            normative_start,normative_end=row.get('normative_start_line'),row.get('normative_end_line')
            path=original['path']
            if path not in document_lines:
                document_lines[path]=cache[path].splitlines(keepends=True)
                document_headings[path]=_markdown_headings(document_lines[path])
            lines=document_lines[path]
            if type(start) is not int or type(end) is not int or not 1<=start<=end<=len(lines):
                raise ValueError('invalid clause span')
            if (type(normative_start) is not int or type(normative_end) is not int or
                    not 1<=normative_start<=start<=end<=normative_end<=len(lines)):
                raise ValueError('invalid normative clause span')
            parsed_heading=document_headings[path].get(start)
            if parsed_heading is None or parsed_heading[1]!=row.get('heading'):
                raise ValueError('clause heading location mismatch')
            heading_level,heading=parsed_heading
            heading_parts=heading.split(maxsplit=1)
            if (
                not heading_parts or heading_parts[0] != row_clause_id or
                len(heading_parts) < 2 or heading_parts[1] != row.get('title')
            ):
                raise ValueError('clause heading identity mismatch')
            expected_normative_start=start
            if '核验合同' in heading_parts[1]:
                parent=next(((number,level) for number,(level,_) in
                             reversed(list(document_headings[path].items()))
                             if number<start and level<heading_level),None)
                if parent is None or parent[1]<=1:
                    raise ValueError('normative chapter heading missing')
                expected_normative_start=parent[0]
            if normative_start!=expected_normative_start or normative_end!=end:
                raise ValueError('normative span binding mismatch')
            for number,(_,nested_heading) in document_headings[path].items():
                if start<number<=end and nested_heading.split(maxsplit=1)[0]==row_clause_id:
                    raise ValueError('duplicate clause heading in indexed span')
            section=b''.join(lines[start-1:end])
            digest=hashlib.sha256(section).hexdigest()
            if digest!=row.get('section_sha256'):
                raise ValueError('clause content digest mismatch')
            normative=b''.join(lines[normative_start-1:normative_end])
            normative_digest=hashlib.sha256(normative).hexdigest()
            if normative_digest!=row.get('normative_sha256'):
                raise ValueError('normative clause digest mismatch')
            result={**doc,'clause_id':row_clause_id,'line':start,'end_line':end,
                    'section_sha256':digest,'normative_start_line':normative_start,
                    'normative_end_line':normative_end,'normative_sha256':normative_digest}
            if text_needle is not None:
                matched=None
                for offset,raw_line in enumerate(lines[normative_start-1:normative_end]):
                    line_text=_decode_physical_line(raw_line)
                    bounds=_casefold_match(line_text,text_needle)
                    if bounds is not None:
                        matched=(normative_start+offset,line_text,bounds)
                        break
                if matched is None:continue
                line_number,line_text,(match_start,match_end)=matched
                result['matched_line']=line_number
                result['matched_excerpt']=_matched_excerpt(line_text,match_start,match_end)
            results.append(result)
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
    parser.add_argument('--text-query',help='Exact text contained in a verified clause (not semantic search)')
    parser.add_argument('--limit',type=int,default=20)
    args=parser.parse_args(argv)
    if not 1<=args.limit<=100:parser.error('limit must be 1..100')
    try:
        result=find(args.root,args.query,args.document_id,args.clause_id,args.domain,args.limit,args.text_query)
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print('lookup failed: '+str(exc),file=sys.stderr);return 1
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0

if __name__=='__main__':raise SystemExit(main())
