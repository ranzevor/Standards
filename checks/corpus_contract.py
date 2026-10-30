"""Markdown structure and exact-body binding. Parsed headings are not obligation totals."""
import sys
if sys.flags.optimize:
    raise RuntimeError('Validation requires assertions enabled; do not use -O or -OO')
import re
from html.parser import HTMLParser
from checks.validation_common import require, digest, normalized, substantive

HEADING = re.compile(r'^(#{1,6})[ \t]+(.+?)(?:[ \t]+#+)?[ \t]*$')
CLAUSE = re.compile(r'^(§\d{1,3}|[A-Z][A-Z0-9]*(?:-[A-Z][A-Z0-9]*)?-?\d{1,4})(?=[\s：:、])(?:[\s：:、]+)(.+)$')
FIELD = re.compile(r'\*\*([^*\n]+?)[：:]\*\*[ \t]*')
REFERENCE_DEF = re.compile(r'^\s{0,3}\[([^\]]+)\]:\s*(\S+)(?:\s+.+)?$')
LINK = re.compile(r'!?\[([^\]\n]*)\]\(([^\n)]*)\)|!?\[([^\]\n]+)\]\[([^\]\n]*)\]')
ACCEPTANCE = ('验收', '完成标准', '完成条件', '可核验准则', '核验准则', '可核证据', '检查与证据', '证据与完成条件', '输出与验收')

def _unescaped_pipes(line):
    without_code=re.sub(r'`[^`]*`','',line)
    return len(re.findall(r'(?<!\\)\|',without_code))

def _comment_visibility(text):
    """Mask comment bytes, not their line positions; fenced/code examples stay literal."""
    if '<!--' not in text:return text
    output=[];comment=False;fence=None
    for number,line in enumerate(text.splitlines(keepends=True),1):
        if not comment and fence is not None:
            output.append(line)
            if re.match(r'^\s{0,3}'+re.escape(fence[0])+r'{'+str(fence[1])+r',}\s*$',line.rstrip('\r\n')):fence=None
            continue
        opening=re.match(r'^\s{0,3}(`{3,}|~{3,})',line) if not comment else None
        if opening:
            fence=(opening[1][0],len(opening[1]));output.append(line);continue
        visible=list(line);i=0
        while i<len(line):
            if comment:
                require(not line.startswith('<!--',i),'nested or ambiguous comment',number)
                if line.startswith('-->',i):
                    visible[i:i+3]=[' ']*3;i+=3;comment=False;continue
                if line[i] not in '\r\n':visible[i]=' '
                i+=1;continue
            if line[i]=='`':
                run=re.match(r'`+',line[i:])[0];close=line.find(run,i+len(run))
                if close>=0:i=close+len(run);continue
            if line.startswith('<!--',i):
                visible[i:i+4]=[' ']*4;i+=4;comment=True;continue
            i+=1
        output.append(''.join(visible))
    require(not comment,'unclosed multiline comment')
    return ''.join(output)


def _cells(line):
    # Pipes inside inline code and escaped pipes are not table delimiters.
    text = re.sub(r'`[^`]*`', lambda m: m[0].replace('|', '\x00'), line.strip())
    text = text.replace('\\|', '\x00')
    require(text.startswith('|') and text.endswith('|'), 'malformed or orphan table row', line)
    return [cell.replace('\x00', '|').strip() for cell in text[1:-1].split('|')]


def markdown_blocks(text):
    require(type(text) is str and text.strip(), 'nonempty Markdown body required')
    lines = text.splitlines(keepends=True)
    visible_lines=_comment_visibility(text).splitlines(keepends=True)
    blocks = []; i = 0
    def emit(kind, start, end):
        body = ''.join(lines[start:end])
        blocks.append({'kind': kind, 'line': start+1, 'end_line': end,
                       'sha256': digest(body), 'text': body,'visible_text':''.join(visible_lines[start:end])})
    while i < len(lines):
        start = i; line = lines[i].rstrip('\r\n');visible=visible_lines[i].rstrip('\r\n')
        if not line.strip():
            while i < len(lines) and not lines[i].strip(): i += 1
            emit('whitespace', start, i); continue
        if re.match(r'^\s*<!--', line):
            while i < len(lines) and '-->' not in lines[i]: i += 1
            require(i < len(lines), 'unclosed multiline comment', start+1)
            i += 1
            require(''.join(lines[start:i]).count('<!--') == 1 and ''.join(lines[start:i]).count('-->') == 1,
                    'nested or ambiguous comment', start+1)
            emit('paragraph' if ''.join(visible_lines[start:i]).strip() else 'comment', start, i); continue
        fence = re.match(r'^\s{0,3}(`{3,}|~{3,})', line)
        if fence:
            i += 1
            close = re.compile(r'^\s{0,3}'+re.escape(fence[1][0])+r'{'+str(len(fence[1]))+r',}\s*$')
            while i < len(lines) and not close.match(lines[i].rstrip('\r\n')): i += 1
            require(i < len(lines), 'unclosed code fence', start+1)
            i += 1; emit('code', start, i); continue
        if HEADING.match(visible):
            emit('heading', i, i+1); i += 1; continue
        if visible.lstrip().startswith('|'):
            while i < len(lines) and visible_lines[i].strip() and visible_lines[i].lstrip().startswith('|'): i += 1
            raw = [x.rstrip('\r\n') for x in visible_lines[start:i]]
            previous = next((b for b in reversed(blocks) if b['kind'] != 'whitespace'),None)
            require(len(raw) >= 2 or previous and previous['kind'] in {'table','table-continuation'}, 'orphan table row', start+1)
            rows = [_cells(x) for x in raw]
            require(all(len(r) == len(rows[0]) for r in rows), 'table column count differs', start+1)
            separator = len(rows)>1 and all(re.fullmatch(r':?-{3,}:?', c) for c in rows[1])
            previous = next((b for b in reversed(blocks) if b['kind'] != 'whitespace'),None)
            continuation = previous and previous['kind'] in {'table','table-continuation'} and len(_cells(previous['visible_text'].splitlines()[0])) == len(rows[0])
            require(separator or continuation, 'table separator missing', start+1)
            emit('table' if separator else 'table-continuation', start, i); continue
        if REFERENCE_DEF.match(visible):
            emit('reference-definition', i, i+1); i += 1; continue
        if _unescaped_pipes(visible) >= 2:
            require(False, 'malformed or orphan table row', start+1, line)
        i += 1
        while i < len(lines):
            following = lines[i].rstrip('\r\n')
            visible_following=visible_lines[i].rstrip('\r\n')
            if not following.strip() or HEADING.match(visible_following) or visible_following.lstrip().startswith(('|', '```', '~~~')) or following.lstrip().startswith('<!--') or REFERENCE_DEF.match(visible_following): break
            require(_unescaped_pipes(visible_following) < 2, 'malformed or orphan table row', i+1)
            i += 1
        emit('paragraph', start, i)
    require(''.join(b['text'] for b in blocks) == text, 'body partition gap')
    require([n for b in blocks for n in range(b['line'], b['end_line']+1)] == list(range(1, len(lines)+1)), 'body partition overlap')
    return blocks


def headings(blocks):
    result = []
    for block in blocks:
        if block['kind'] == 'heading':
            match = HEADING.match(block['visible_text'].rstrip('\r\n'))
            result.append({'level':len(match[1]), 'title':match[2], 'line':block['line'], 'match':CLAUSE.match(match[2])})
    return result


def slug(value):
    value = re.sub(r'\[([^]]+)\]\([^)]+\)', r'\1', value)
    value = re.sub(r'<[^>]+>', '', value).replace('`','').replace('*','').replace('_','')
    value = re.sub(r'[^\w\-\u4e00-\u9fff ]', '', value.lower()).replace(' ', '-')
    return value


def anchors(text):
    counts = {}; result = set();blocks=markdown_blocks(text)
    for h in headings(blocks):
        base = slug(h['title']); count = counts.get(base, 0); counts[base] = count+1
        result.add(base + ('-'+str(count) if count else ''))
    visible=''.join(b['visible_text'] for b in blocks if b['kind'] not in {'code','comment'})
    visible=re.sub(r'(`+).*?\1','',visible,flags=re.S)
    class ExplicitIds(HTMLParser):
        def handle_starttag(self,tag,attrs):
            identifiers=[value for name,value in attrs if name=='id']
            require(len(identifiers)<=1,'duplicate explicit id attribute')
            for anchor in identifiers:
                require(anchor and anchor not in result, 'empty/duplicate explicit anchor', anchor);result.add(anchor)
    ExplicitIds(convert_charrefs=True).feed(visible)
    return result


INLINE_CODE = re.compile(r'(?<!`)(`+)(?!`)(.*?)\1(?!`)',re.S)

def _inline_markup(text):
    return INLINE_CODE.sub(lambda match:''.join(c if c in '\r\n' else ' ' for c in match[0]),text)

def citation_declarations(text):
    """Exact visible table declarations, including code-formatted identifier cells."""
    result={}
    for block in markdown_blocks(text):
        if block['kind'] not in {'table','table-continuation'}:continue
        for offset,(raw,visible) in enumerate(zip(block['text'].splitlines(keepends=True),block['visible_text'].splitlines(keepends=True))):
            cells=_cells(visible);value=cells[0]
            code=INLINE_CODE.fullmatch(value)
            if code:value=code[2]
            if not re.fullmatch(r'[A-Z]\d+',value):continue
            require(value not in result,'duplicate source declaration',value)
            result[value]={'line':block['line']+offset,'sha256':digest(raw)}
    return result

def references(text,visible_only=False,display_labels=False):
    """Dependency view includes hidden links; citation view masks comments.

    Both retain original line positions. Comment body bytes are always bound
    separately by markdown_blocks; visible citations do not erase raw evidence.
    """
    require(type(visible_only)is bool,'reference view mode must be boolean')
    require(type(display_labels)is bool,'reference label mode must be boolean')
    blocks=markdown_blocks(text);result=[];citations=[];definitions={};lines=[]
    for block in blocks:
        if block['kind']=='code'or visible_only and block['kind']=='comment':continue
        visible_text=block['visible_text'] if visible_only else block['text'];markup=_inline_markup(visible_text)
        lines.extend((block['line']+offset,raw,visible) for offset,(raw,visible) in enumerate(zip(visible_text.splitlines(),markup.splitlines())))
    # Explicit definitions take precedence over the legacy adjacent source-ID
    # shorthand, even when the definition follows its first use.
    for number,raw,line in lines:
        definition=REFERENCE_DEF.match(line)
        if definition:
            key=normalized(definition[1]).casefold()
            require(key not in definitions,'duplicate reference definition',key)
            definitions[key]=definition[2].strip('<>')
    for number,raw,line in lines:
        definition=REFERENCE_DEF.match(line)
        if definition:
            key=normalized(definition[1]).casefold()
            result.append({'line':number,'url':definitions[key],'kind':'definition','label':key})
        actual_link_spans=[]
        for match in LINK.finditer(line):
            if match[1] is not None:
                url=match[2].strip()
                if url.startswith('<') and '>' in url:url=url[1:url.index('>')]
                else:url=re.split(r'\s+["\']',url,1)[0]
                require(url,'empty link target',number)
                result.append({'line':number,'url':url,'kind':'inline','label':match[1]})
            else:
                key=normalized(match[4] or match[3]).casefold()
                if re.fullmatch(r'[A-Z]\d+',match[3]) and re.fullmatch(r'[A-Z]\d+',match[4]) and key not in definitions:continue
                require(key in definitions,'undefined reference group',key)
                result.append({'line':number,'url':definitions[key],'kind':'reference',
                               'label':match[3] if display_labels else key})
            actual_link_spans.append(match.span())
        # Explicit repository code paths remain dependencies, unlike Markdown
        # syntax demonstrated inside code. They retain the original line number.
        for code in INLINE_CODE.finditer(raw):
            path=code[2]
            if re.fullmatch(r'[^`\n]+(?:\.md|\.json)(?:#[^`\s]+)?',path) and ('/' in path or '--v' in path and '.md' in path) and not re.search(r'\s|[{}*<>]',path) and '://' not in path:
                result.append({'line':number,'url':path,'kind':'literal-path','label':path})
        def inside_link(start,end):return any(left<=start and end<=right for left,right in actual_link_spans)
        for group in re.finditer(r'(?:\[[A-Z]\d+\]){2,}',line):
            tokens=[m[1] for m in re.finditer(r'\[([A-Z]\d+)\]',line[group.start():group.end()]) if not inside_link(group.start()+m.start(),group.start()+m.end())]
            require(len(tokens)==len(set(tokens)),'duplicate source citation in group',group[0])
        for token in re.finditer(r'\[([A-Z]\d+)\](?![(:])',line):
            if not inside_link(token.start(),token.end()):citations.append({'line':number,'url':'citation:'+token[1],'kind':'citation','label':token[1]})
    return result+citations


def fields_of(body):
    values = {}
    blocks=markdown_blocks(body)
    for block_number,block in enumerate(blocks):
        if block['kind'] not in {'paragraph','table'}: continue
        text = block['visible_text'];code_spans=[m.span() for m in re.finditer(r'(`+)(.*?)\1',text)]
        matches = [m for m in FIELD.finditer(text) if not any(start<=m.start()<end for start,end in code_spans)]
        for i, match in enumerate(matches):
            label = normalized(match[1]); raw_value=text[match.end():matches[i+1].start() if i+1<len(matches) else len(text)]
            raw_value=re.sub(r'\n[ \t]*(?:[-*]|\d+\.)[ \t]*$','',raw_value)
            if not raw_value.strip() and i==len(matches)-1:
                following=next((b for b in blocks[block_number+1:]if b['kind']!='whitespace'),None)
                if following is not None and following['kind']=='code':
                    content='\n'.join(following['text'].splitlines()[1:-1])
                    require(substantive(content),'placeholder or empty code contract field',label)
                    raw_value=following['text']
            value = normalized(raw_value)
            require(substantive(value), 'placeholder or empty contract field', label)
            require(label not in values, 'duplicate contract field', label)
            values[label] = value
        if re.search(r'^\s*(?:[-*]\s+)?\*\*(?:机制|验收|适用条件|完成标准|完成条件)[：:](?!\*\*)', text, re.M):
            require(False, 'malformed technical field')
    return values


def profile_for(entry, text):
    hs = headings(markdown_blocks(text)); explicit = [h for h in hs if h['level'] > 1 and h['match']]
    selected = explicit or [h for h in hs if h['level'] == 2]
    require(selected, 'document has no parseable section', entry['id'])
    ids = [h['match'][1] if h['match'] else 'H-'+digest(normalized(h['title']))[:12] for h in selected]
    require(len(ids) == len(set(ids)), 'duplicate clause or section identity', entry['id'], ids)
    titles=[]
    for h in selected:
        title=h['match'][2] if h['match'] else h['title']
        if '核验合同' in title:
            parent=next((x for x in reversed(hs) if x['line']<h['line'] and x['level']<h['level']),None)
            title=(parent['title'] if parent else '')+'::'+title
        titles.append(normalized(title))
    require(len(set(titles))==len(selected), 'duplicate renamed heading', entry['id'])
    return {'document_id':entry['id'],'domain':entry['domain'],'path':entry['path'],'version':entry['version'],
            'sha256':entry['sha256'],'heading_profile':'explicit-stable-id' if explicit else 'legacy-h2',
            'clause_ids':ids,'clause_headings':{ident:normalized(h['title']) for ident,h in zip(ids,selected)},
            'id_prefixes':sorted({re.sub(r'\d+$','',x) for x in ids}) if explicit else [],
            'dispatch':'generic-markdown-contract-v1', 'contract_fields':{}}


def extract_document(entry, text, profile=None):
    actual = profile_for(entry,text)
    if profile is not None:
        for key in ('document_id','domain','path','version','sha256','heading_profile','clause_ids','clause_headings','id_prefixes','dispatch'):
            require(profile.get(key) == actual[key], 'profile identity/dispatch/heading drift', entry['id'], key)
    profile = profile or actual
    blocks = markdown_blocks(text); hs = headings(blocks)
    explicit = [h for h in hs if h['level'] > 1 and h['match']]
    selected = explicit or [h for h in hs if h['level']==2]
    lines = text.splitlines(keepends=True); clauses = []
    for index, h in enumerate(selected):
        local_id = profile['clause_ids'][index]
        # The section ends at the next heading at the same or shallower level,
        # not at the next selected clause. Sources/appendices cannot be swallowed.
        next_heading = next((x for x in hs if x['line'] > h['line'] and x['level'] <= h['level']),None)
        end_line = next_heading['line']-1 if next_heading else len(lines)
        body = ''.join(lines[h['line']-1:end_line]); fields = fields_of(body)
        binding_start=h['line']
        if h['match'] and '核验合同' in h['match'][2]:
            parent=next((x for x in reversed(hs) if x['line']<h['line'] and x['level']<h['level']),None)
            require(parent is not None and parent['level']>1,'contract needs original chapter context',local_id)
            siblings=[x for x in selected if parent['line']<x['line']<=end_line]
            require(len(siblings)==1,'ambiguous chapter-to-contract mapping',local_id)
            binding_start=parent['line']
        normative_body=''.join(lines[binding_start-1:end_line])
        expected_fields = profile.get('contract_fields',{}).get(local_id,[])
        require(set(expected_fields) <= set(fields), 'required contract field omitted',entry['id'],local_id)
        good = [(k,v) for k,v in fields.items() if any(s in k for s in ('正确案例','合法邻例','合法相邻','正例'))]
        bad = [(k,v) for k,v in fields.items() if k=='失败' or any(s in k for s in ('错误案例','失败案例','反例','失败样例','直接失败','同场景失败'))]
        require(not any(gk!=bk and gv==bv for gk,gv in good for bk,bv in bad), 'positive/negative examples identical',entry['id'],local_id)
        identifier = entry['id']+'::'+local_id
        clauses.append({'id':identifier,'clause_id':local_id,'document_id':entry['id'],'document':entry['path'],'path':entry['path'],
                        'version':entry['version'],'document_sha256':entry['sha256'],'title':h['match'][2] if h['match'] else h['title'],
                        'heading':h['title'],'line':h['line'],'end_line':end_line,'section_sha256':digest(body),
                        'normative_start_line':binding_start,'normative_end_line':end_line,'normative_sha256':digest(normative_body),
                        'fields':fields,'acceptance_fields':[v for k,v in fields.items() if k.startswith(ACCEPTANCE)],
                        'kind':'labelled-clause' if explicit else 'narrative-section','check_scope':'identity-and-structure'})
    bindings = []
    for block in blocks:
        owner = next((c['clause_id'] for c in clauses if c['normative_start_line'] <= block['line'] <= c['normative_end_line']), None)
        previous = [h for h in hs if h['line'] <= block['line']]
        role = 'clause' if owner else ('preamble' if not any(h['level']>1 for h in previous) else 'context-or-source-or-ending')
        owner_clause=next((c for c in clauses if c['clause_id']==owner),None)
        owner_kind=owner_clause['kind'] if owner_clause else None
        technical_block=block['kind'] not in {'whitespace','heading'}
        disposition='manual-review-required' if technical_block and owner_kind!='labelled-clause' else ('clause-bound' if technical_block else 'layout-only')
        if owner_kind=='narrative-section':role='narrative-section'
        bindings.append({k:block[k] for k in ('kind','line','end_line','sha256')} | {'clause_id':owner,'role':role,'owner_kind':owner_kind,'review_disposition':disposition})
    require(sum(b['end_line']-b['line']+1 for b in bindings)==len(lines),'incomplete body binding')
    return {'profile':profile,'clauses':clauses,'bindings':{'document_id':entry['id'],'path':entry['path'],'sha256':digest(text),
            'line_count':len(lines),'nonempty_lines':sum(bool(x.strip()) for x in lines),'blocks':bindings},'references':references(text)}


def validate_document_binding(entry,text,profile,expected_clauses,expected_bindings):
    """Direct parser/binding entry point; intentionally no whole-document hash gate."""
    actual=extract_document(entry,text,profile)
    require(actual['clauses']==expected_clauses,'direct clause content/position binding drift',entry['id'])
    require(actual['bindings']==expected_bindings,'direct full-body block binding drift',entry['id'])
    return {'document_id':entry['id'],'clauses':len(actual['clauses']),'scope':'direct-structure-and-full-body-binding'}
