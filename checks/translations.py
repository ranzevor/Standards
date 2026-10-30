"""Current language availability, exact source/target and clause mapping; not semantic equivalence."""
import sys
if sys.flags.optimize:raise RuntimeError('Translation checks require normal Python mode; do not use -O or -OO')
from pathlib import Path
import argparse,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from checks.validation_common import read_json,safe_path,require
from checks.repository_registry import validate_entries
from checks.project_readme import validate_translations,validate_document_links
ROOT=Path(__file__).resolve().parents[1]


def validate(root=ROOT):
    root=Path(root).resolve();value=read_json(root/'registry/translations.json')
    require(value.get('schema')=='standards-translations/1','translation registry schema')
    entries={e['id']:e for e in validate_entries(root)};rows=value['records'];unavailable=value['unavailable']
    result=validate_translations(root,rows);seen=set();targets=set();links=0
    for row in rows:
        ident=row['document_id'];require(ident in entries and ident not in seen,'unknown/duplicate translated document');seen.add(ident)
        e=entries[ident];require(all(row[a]==e[b]for a,b in [('source_version','version'),('source_path','path'),('source_sha256','sha256')]),'translated source/catalogue identity drift')
        require(row['target_path']not in targets,'two sources claim one translation');targets.add(row['target_path'])
        for side in ('source','target'):
            p=safe_path(root,row[side+'_path']);require(type(row[side+'_bytes'])is int and p.stat().st_size==row[side+'_bytes'],'translation byte size drift')
            links+=validate_document_links(root,row[side+'_path'])[1]['local']
    require(type(unavailable)is list,'unavailable translations array')
    for row in unavailable:
        require(set(row)=={'document_id','source_path','source_sha256','target_language','coverage'},'unavailable translation fields')
        ident=row['document_id'];require(ident in entries and ident not in seen,'duplicate/unknown unavailable document');seen.add(ident)
        require(row['source_path']==entries[ident]['path']and row['source_sha256']==entries[ident]['sha256']and row['target_language']=='en'and row['coverage']=='unavailable','unavailable source identity or coverage drift')
    require(seen==set(entries),'translation availability omitted a normative source')
    actual={p.relative_to(root).as_posix()for p in (root/'translations/en/project-governance').glob('*.md')if p.name!='README.md'}
    require(actual==targets,'undeclared/missing English normative translation')
    return {**result,'source_documents':len(entries),'unavailable':len(unavailable),'local_links_checked':links}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);a=p.parse_args()
    print(json.dumps(validate(a.root),ensure_ascii=False,sort_keys=True))
