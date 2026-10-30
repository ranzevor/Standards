"""Check explicit document identities in links; not general semantic entailment."""
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

from checks.corpus_contract import references, markdown_blocks, headings, slug, LINK, INLINE_CODE, _inline_markup
from checks.validation_common import require

DOCUMENT_ID = re.compile(r'STD-(?:L[0-6](?:-[A-Z0-9]+)*|PG)-[0-9]{3}(?![A-Z0-9-])')
OLD_AI_ORDINAL = re.compile(
    r'第\s*(?:0[1-9]|1[0-5])(?!\d)\s*(?:专题|模型(?:接入|接口|调用)|'
    r'指令(?:信任|体系|污染)|不可信指令|上下文|知识检索|检索|持久记忆|'
    r'Tool|MCP|授权|沙箱|执行隔离|控制循环|跨Agent协议|跨域消息|长任务|'
    r'检查点|(?:AI\s*)?评测|版本演进|联合版本)')

# These are the five displayed topic names in the defective v0.1.0 AI-005
# links. Keep this a finite, reviewed identity mapping, not a prose classifier.
LEGACY_AI_LINK_LABELS = {
    '指令信任': 'STD-L4-AI-AGENT-011',
    '上下文': 'STD-L4-AI-AGENT-007',
    'Tool/MCP': 'STD-L4-AI-AGENT-009',
    '授权及副作用': 'STD-L4-AI-AGENT-004',
    '执行隔离': 'STD-L4-AI-AGENT-008',
}
NUMBERED_LABEL = re.compile(r'^(?:第[ \t]*)?(\d{1,3})(?:[ \t]+|[·、:：])(.+)$')


def reference_view(text):
    """Recover rendered code labels only inside links found outside code spans."""
    visible_lines={};raw_lines={};link_matches={}
    for block in markdown_blocks(text):
        if block['kind'] in {'code','comment'}:continue
        raw_block=block['visible_text'];markup=_inline_markup(raw_block)
        for offset,(raw,visible) in enumerate(zip(raw_block.splitlines(keepends=True),markup.splitlines(keepends=True))):
            number=block['line']+offset;raw_lines[number]=raw
            visible_lines[number]=visible
            link_matches[number]=iter(LINK.finditer(visible_lines[number]))
    refs=references(text,visible_only=True,display_labels=True)
    definitions={ref['label'] for ref in refs if ref['kind']=='definition'}
    for ref in refs:
        if ref['kind'] in {'inline','reference'}:
            while True:
                match=next(link_matches[ref['line']])
                # Match the parser's adjacent source-citation shorthand: an
                # undeclared [S1][S2] group is not a named Markdown link.
                if (match[1] is None and re.fullmatch(r'[A-Z]\d+',match[3])
                        and re.fullmatch(r'[A-Z]\d+',match[4])
                        and match[4].casefold() not in definitions):continue
                break
            group=1 if ref['kind']=='inline' else 3
            raw=raw_lines[ref['line']][match.start(group):match.end(group)]
            ref['label']=INLINE_CODE.sub(lambda code:code[2],raw)
            ref['span']=match.span()
        elif ref['kind']=='definition':
            # Reference definitions are syntax, not displayed prose.
            visible_lines[ref['line']]='\n'
    return refs,visible_lines


def clause_number_at_fragment(target, fragment):
    """Resolve a real numbered clause, using the repository's heading anchors."""
    if not fragment or not target.is_file():return None
    fragment=unquote(fragment);counts={}
    for heading in headings(markdown_blocks(target.read_text('utf-8'))):
        base=slug(heading['title']);count=counts.get(base,0);counts[base]=count+1
        anchor=base+('-'+str(count) if count else '')
        if anchor == fragment:
            clause=heading['match']
            return int(clause[1][1:]) if clause and clause[1].startswith('§') else None
    return None


def validate_numbered_label(label, target, fragment, target_entry, titles, entry, line):
    """Only registered titles and reviewed legacy labels assert document numbers."""
    ordinal=NUMBERED_LABEL.fullmatch(label)
    if ordinal is None:return False
    number=int(ordinal[1]);name=ordinal[2].strip()
    if name in titles:
        require(name == target_entry['title'],
                'reference title differs from registered target',entry['id'],line)
    elif number == clause_number_at_fragment(target,fragment):
        # The resolved §NN target gives the number a clause meaning. A fragment
        # that merely looks numbered, but has no such heading, grants no bypass.
        return True
    elif target_entry['domain']=='ai-agent' and name in LEGACY_AI_LINK_LABELS:
        require(LEGACY_AI_LINK_LABELS[name] == target_entry['id'],
                'legacy reference label names another document',entry['id'],line)
    else:
        # Counts, page labels and other prose are not document identity claims.
        return False
    require(number == int(target_entry['id'].rsplit('-',1)[1]),
            'reference ordinal names another document',entry['id'],line)
    return True

def validate_text(root, entry, text, entries):
    """Check explicit identities, including fragment links to the current document."""
    root=Path(root).resolve()
    by_path={row['path']:row for row in entries}
    titles={row['title'] for row in entries}
    source=root/entry['path']; checked=0
    refs,visible_lines=reference_view(text)
    for ref in refs:
        if ref['kind']=='definition':continue
        label=ref['label']; identifiers=DOCUMENT_ID.findall(label)
        uri=urlsplit(ref['url'])
        if uri.scheme or uri.netloc:continue
        target=(source.parent/unquote(uri.path)).resolve() if uri.path else source
        if not target.is_relative_to(root):continue
        target_entry=by_path.get(target.relative_to(root).as_posix())
        if target_entry is None:
            require(not identifiers,'reference ID has no registered normative target',entry['id'],ref['line'])
            continue
        if identifiers:
            require(identifiers == [target_entry['id']], 'reference ID names another document', entry['id'],ref['line'])
            # Canonical labels deliberately expose the whole registered title.
            # Other ordinary descriptive links retain their existing behavior.
            canonical=target_entry['id']+' · '+target_entry['title']
            require(label == canonical or label == target_entry['id'],
                    'reference title differs from registered target',entry['id'],ref['line'])
        numbered=validate_numbered_label(label,target,uri.fragment,target_entry,titles,entry,ref['line'])
        if (identifiers or numbered) and 'span' in ref:
            # An identity already checked against its target is not a bare old
            # topic ordinal. Preserve offsets for other links on the same line.
            start,end=ref['span'];visible=visible_lines[ref['line']]
            visible_lines[ref['line']]=visible[:start]+' '*(end-start)+visible[end:]
        checked+=1
    if entry['domain']=='ai-agent':
        visible=''.join(visible_lines[number] for number in sorted(visible_lines))
        require(OLD_AI_ORDINAL.search(visible) is None,
                'ambiguous old AI topic ordinal; use the stable document ID',entry['id'])
    return checked

def validate(root, entries=None):
    from checks.repository_registry import validate_entries
    root=Path(root).resolve()
    entries=validate_entries(root) if entries is None else entries
    count=sum(validate_text(root,row,(root/row['path']).read_text('utf-8'),entries) for row in entries)
    return {'documents':len(entries),'normative_links':count,
            'scope':'explicit link ID/title identity, known numbered document labels, and named old AI topic ordinals; not arbitrary prose entailment'}
