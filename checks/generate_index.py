"""Generate the only current catalogue from registry/standards.json."""
import sys
if sys.flags.optimize:
    raise RuntimeError('Validation requires assertions enabled; do not use -O or -OO')
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from checks.validation_common import read_json,read_text_exact,require
ROOT = Path(__file__).resolve().parents[1]

def expected_index(entries):
    lines=['# 规范目录','','162 份已采用规范，按稳定标识与准确版本检索。','','| 标识 | 规范 | 版本 | 状态 | 生效日期 |','| --- | --- | --- | --- | --- |']
    lines.extend(f"| {e['id']} | [{e['title']}]({e['path']}) | {e['version']} | {e['status']} | {e['effective_date']} |" for e in entries)
    return '\n'.join(lines)+'\n'

def generate(root=ROOT,check=False):
    root=Path(root);expected=expected_index(read_json(root/'registry/standards.json'));path=root/'INDEX.md'
    if check:require(path.is_file() and read_text_exact(path)==expected,'generated index stale')
    else:path.write_text(expected,encoding='utf-8',newline='\n')
    from checks.domain_navigation import generate as domain_indexes
    return {'index':'current','check':check,**domain_indexes(root,check)}
if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--check',action='store_true');a=p.parse_args()
    print(json.dumps(generate(a.root,a.check),ensure_ascii=False,sort_keys=True))
