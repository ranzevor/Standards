"""Registry-derived navigation for each technical and project-governance domain."""
import sys
if sys.flags.optimize:
    raise RuntimeError('Navigation validation requires assertions enabled; do not use -O or -OO')
from pathlib import Path
import re,urllib.parse
from checks.validation_common import read_json,require,safe_path

BEGIN='<!-- standards-current-domain-index:begin -->'
END='<!-- standards-current-domain-index:end -->'
OLD='| 正文 | 版本 | 文档 | 项目采用 | 实现 |'

def groups(entries):
    result={}
    for e in entries:
        p=Path(e['path'])
        if (len(p.parts)>3 and p.parts[:2]==('standards','L4')) or p.parts[:2]==('standards','project-governance'):
            result.setdefault(p.parent.as_posix(),[]).append(e)
    return result

def table(entries):
    lines=[BEGIN,'| 正文 | 版本 | 状态 | 生效日期 |','| --- | --- | --- | --- |']
    for e in sorted(entries,key=lambda e:e['path']):
        title=e['title'].replace('|','&#124;').replace('[','&#91;').replace(']','&#93;')
        url=urllib.parse.quote(Path(e['path']).name,safe='-._~')
        lines.append('| ['+title+']('+url+') | '+' | '.join(e[k] for k in ('version','status','effective_date'))+' |')
    return '\n'.join(lines+[END])

def expected(text,entries):
    rendered=table(entries)
    require(text.count(BEGIN)==text.count(END) and text.count(BEGIN)<=1,'ambiguous domain index markers')
    if BEGIN in text:
        a=text.index(BEGIN);b=text.index(END)+len(END)
        require(a<b,'reversed domain index markers')
        return text[:a]+rendered+text[b:]
    lines=text.splitlines(keepends=True)
    positions=[i for i,line in enumerate(lines)if line.strip()==OLD]
    require(len(positions)<=1,'ambiguous old current-domain table')
    if positions:
        a=positions[0];b=a+1
        while b<len(lines)and lines[b].startswith('|'):b+=1
        return ''.join(lines[:a])+rendered+'\n'+''.join(lines[b:])
    return text.rstrip()+'\n\n'+rendered+'\n'

def validate_labels(root,path,text,known):
    # A literal version in the label of a link to a current registered object
    # must name that object; independent old/new section counts remain untouched.
    for m in re.finditer(r'\[([^]\n]+)\]\(([^)\s]+)\)',text):
        url=urllib.parse.urlsplit(m[2])
        if url.scheme or url.netloc:continue
        target=(path.parent/urllib.parse.unquote(url.path)).resolve()
        if not target.is_relative_to(root)or target.relative_to(root).as_posix()not in known:continue
        version=known[target.relative_to(root).as_posix()]['version']
        shown=re.search(r'--v(\d+(?:\.\d+)+)(?:\.md)?$',m[1])
        require(shown is None or shown[1]==version,'current navigation label/version mismatch',path.relative_to(root).as_posix(),m[1],version)

def generate(root,check=False):
    root=Path(root).resolve();entries=read_json(root/'registry/standards.json');known={e['path']:e for e in entries};count=0
    for directory,docs in sorted(groups(entries).items()):
        path=safe_path(root,directory+'/README.md');text=path.read_text(encoding='utf-8');want=expected(text,docs)
        if check:require(text==want,'generated domain navigation stale',directory)
        else:path.write_text(want,encoding='utf-8',newline='\n');text=want
        validate_labels(root,path,text,known);count+=1
    return {'domain_indexes':count,'generated_from':'registry/standards.json','mode':'check'if check else'generate'}
