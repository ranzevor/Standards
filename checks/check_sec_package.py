"""Structural whole-document/ID/link binding, not semantic or runtime certification."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
if sys.flags.optimize:
    print('optimized interpreter rejected for review entry point',file=sys.stderr)
    raise SystemExit(2)

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
PROFILE={
 'security':('§',32), 'embedded-edge':('M',18),
 'commerce-billing':('M',20), 'open-source':('M',18),
}
TOPIC_COUNTS={'SEC-P':7,'EDG-H':6,'EDG-F':5,'EDG-L':5,'COM-Q':6,'COM-S':5,'COM-L':5,'OSS-B':5,'OSS-R':5,'OSS-M':4}
BASELINE_TITLES={'L4 安全工程与身份系统领域通用基线':('§',32),'L4 嵌入式与边缘计算领域通用基线':('M',18),'L4 商业交易与计费系统领域通用基线':('M',20),'L4 开源项目与公共技术生态领域通用基线':('M',18)}
NEW_FIELDS=['对象与责任','输入/输出/权威','必要机制与不变量','失败、并发、超时与恢复','兼容','验收与产物','正例 / 直接失败 / 合法邻例','来源']
class BindingError(ValueError): pass

def must(value,reason):
    if not value: raise BindingError(reason)

def digest(text):return hashlib.sha256(text.encode()).hexdigest()

def parse_document(text,path='unknown',entry=None,l3_version=None):
    must(isinstance(text,str) and text.strip(),'empty document')
    must('**状态：** adopted' in text,'adopted state required')
    from tools.verify_release_bundle import valid_date,valid_version
    for label,validator in [('版本',valid_version),('生效日期',valid_date)]:
        values=re.findall(r'\*\*'+label+r'[：:]\*\*\s*([^\s*]+)',text.split('\n## ',1)[0])
        must(len(values)==1 and validator(values[0]),'valid adopted '+label+' required')
    if entry is not None:
        from checks.repository_registry import validate_document_metadata
        validate_document_metadata(entry,text)
    l3_versions=re.findall(r'通用工程规范--v([0-9]+(?:\.[0-9]+)+)\.md',text)
    must(all(valid_version(version) and (l3_version is None or version==l3_version) for version in l3_versions),'stale L3 reference')
    matches=list(re.finditer(r'(?m)^### ((?:§\d{2})|(?:M\d{2})|(?:(?:SEC|EDG|COM|OSS)-[A-Z]\d{2})) ([^\n]+)\n',text))
    must(matches,'no clauses')
    ids=[m.group(1) for m in matches];must(len(ids)==len(set(ids)),'duplicate clause id')
    title=text.splitlines()[0].removeprefix('# ').strip()
    if title in BASELINE_TITLES:
        prefix,count=BASELINE_TITLES[title];expected=[f'{prefix}{i:02}' for i in range(1,count+1)]
    else:
        prefix=ids[0][:-2];must(prefix in TOPIC_COUNTS,'unknown topic profile')
        expected=[f'{prefix}{i:02}' for i in range(1,TOPIC_COUNTS[prefix]+1)]
    must(ids==expected,'missing/renamed/reordered/extra clause id')
    # Every level-3 heading must have a recognized stable ID, not silently ignored.
    all_h3=list(re.finditer(r'(?m)^### [^\n]+',text))
    must(len(all_h3)==len(matches),'unparsed level-3 technical heading')
    clauses=[]
    for i,match in enumerate(matches):
        after=text[match.end():]
        next_header=re.search(r'(?m)^#{2,3} ',after)
        end=match.end()+(next_header.start() if next_header else len(after))
        block=text[match.start():end]
        cid=match.group(1)
        if cid.startswith(('§','M')):
            fields=['合同输入/权威/输出','正例','专题承接与实际入口']
            if cid.startswith('§'):fields+=['适用与机制','同场景失败','合法邻例','可核证据','完成条件','来源映射']
            else:fields+=['机制','失败','合法邻例','验收']
            for f in fields:must(re.search(r'\*\*'+re.escape(f)+r'(?:[^*]*)：\*\*',block),f'{cid}: missing {f}')
        else:
            for f in NEW_FIELDS:must(f'**{f}：**' in block,f'{cid}: missing {f}')
            # Catches placeholder/empty fields directly, without a hash short-circuit.
            for f in NEW_FIELDS:
                value=block.split(f'**{f}：**',1)[1].split('\n\n',1)[0].strip()
                must(len(value)>=12 and value not in {'TBD','待补','TODO'},f'{cid}: empty/placeholder {f}')
        start_line=text[:match.start()].count('\n')+1
        end_line=text[:end].count('\n')+1
        clauses.append({'id':cid,'title':match.group(2),'start_line':start_line,'end_line':end_line,'sha256':digest(block),'text':block})
    # Full text is retained as identity; prefix, interstitial and suffix aren't discarded.
    spans=[(c['start_line'],c['end_line']) for c in clauses]
    return {'path':path,'sha256':digest(text),'clauses':clauses,'full_text_sha256':digest(text),'prefix_sha256':digest(text[:matches[0].start()]),'suffix_sha256':digest(text[end:]),'line_count':text.count('\n')+1,'spans':spans}

def inspect(root=ROOT,overlay=None):
    root=Path(root).resolve()
    overlay=Path(overlay).resolve() if overlay is not None else None
    docs=[]
    from checks.repository_registry import validate_entries
    registered=validate_entries(root)
    by_path={row['path']:row for row in registered}
    l3_version=next(row['version'] for row in registered if row['id']=='STD-L3-001')
    paths=sorted(path for domain in PROFILE for path in (root/'standards/L4'/domain).glob('*--v*.md'))
    must(len(paths)==14,'expected four preserved baselines plus ten complete topics')
    for path in paths:
        must(path.resolve().is_relative_to(root),'document path escapes selected repository')
        domain=path.parent.name;must(domain in PROFILE,'unexpected domain')
        relative=path.relative_to(root).as_posix()
        must(relative in by_path,'unregistered selected source')
        parsed=parse_document(path.read_text(),relative,by_path[relative],l3_version);docs.append(parsed)
        if '领域通用基线' in path.name:
            prefix,count=PROFILE[domain]
            must([c['id'] for c in parsed['clauses']]==[f'{prefix}{i:02}' for i in range(1,count+1)],'preserved baseline ids missing/renamed/reordered')
        # Local link identity is checked against package + read-only integration overlay.
        for target in re.findall(r'\]\(([^)]+)\)',path.read_text()):
            if re.match(r'[a-zA-Z][\w+.-]*:',target) or target.startswith('#'):continue
            target=target.split('#',1)[0]
            local=(path.parent/target).resolve()
            must(local.is_relative_to(root),'local link escapes selected repository')
            if local.is_file():continue
            if overlay is not None:
                relative=local.relative_to(root.resolve())
                if (overlay/relative).is_file():continue
            raise BindingError(f'broken local link {path.name} -> {target}')
    return docs

def verify_manifest(root=ROOT):
    manifest=json.loads((root/'manifest.json').read_text())
    listed={r['path']:r for r in manifest['files']}
    actual={str(p.relative_to(root)):p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='manifest.json'}
    must(set(listed)==set(actual),'manifest file set mismatch')
    for path,p in actual.items():must(hashlib.sha256(p.read_bytes()).hexdigest()==listed[path]['sha256'],f'manifest hash mismatch: {path}')
    return len(actual)

def main():
    if sys.flags.optimize:
        print('optimized interpreter rejected for review entry point',file=sys.stderr);return 2
    ap=argparse.ArgumentParser();ap.add_argument('--overlay-root',type=Path);ap.add_argument('--verify-manifest',action='store_true');args=ap.parse_args()
    try:
        docs=inspect(ROOT,args.overlay_root)
        count=verify_manifest() if args.verify_manifest else None
        print(json.dumps({'documents':len(docs),'clauses':sum(len(d['clauses']) for d in docs),'scope':'structural whole-text binding and exact local links only','manifest_files':count,'real_targets':'not-run'},ensure_ascii=False))
        return 0
    except (BindingError,ValueError,KeyError,OSError) as exc:
        print(str(exc),file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
