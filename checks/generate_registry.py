"""Regenerate/check document, clause and local citation indexes."""
import sys
if sys.flags.optimize:
    raise RuntimeError('Validation requires assertions enabled; do not use -O/-OO')
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import argparse,json
from checks.repository_registry import build_catalogues
from checks.validation_common import read_json,require

def generate(root,check=False):
    root=Path(root).resolve()
    indexes=build_catalogues(root)
    for filename,value in indexes.items():
        p=root/'registry'/filename
        if check:require(read_json(p)==value,'stale document/reader index',filename)
        else:p.write_text(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf8',newline='\n')
    return {'documents':len(indexes['document-profiles.json']),
            'labelled_clauses':len(indexes['requirements.json']),'references':len(indexes['references.json']),
            'check':check}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--check',action='store_true')
    a=p.parse_args();print(json.dumps(generate(a.root,a.check),ensure_ascii=False,sort_keys=True))
