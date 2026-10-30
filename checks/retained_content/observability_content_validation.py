"""Candidate structure checks, not runtime/financial compliance verification."""
import sys
if sys.flags.optimize: raise RuntimeError("Validation requires assertions enabled; do not use -O or -OO")
import re
from checks.retained_content.profile_integrity import mechanism_contracts

OBSERVABILITY_ID = 'STD-L4-AI-AGENT-003'
BAD = {'', 'undefined', 'null', 'none', 'n/a', 'todo', 'tbd', '待定', '待补充', '—'}

def assert_observability_complete(entry, body):
    parts = [(p['number'],p['title'],p['mechanism'],p['acceptance']) for p in mechanism_contracts(body)]
    assert len(parts) == entry['mechanism_count'] == 32, 'observability mechanisms'
    assert len(re.findall(r'^### §', body, re.M)) == 32, 'malformed mechanism'
    for i, (number, title, mechanism, acceptance) in enumerate(parts, 1):
        assert number == f'{i:02}', 'mechanism order'
        assert all(x.strip().lower() not in BAD for x in (title, mechanism, acceptance)), 'empty mechanism'
    for h in ('### 最小事实记录', '### 不变量'):
        assert body.count(h+'\n') == 1, 'control section'
    front = body.split('## 二、', 1)[0]
    invariants = re.findall(r'^- I(\d+) ([^\n]+)$', front, re.M)
    assert [n for n, _ in invariants] == [str(i) for i in range(1,7)], 'invariants'
    assert all(s.strip().lower() not in BAD for _, s in invariants), 'empty invariant'
    records = front.split('### 最小事实记录\n')[1].split('### 不变量')[0]
    for field in ('root_task_id', 'run_id', 'attempt_id', 'provider_request_id', 'estimated/unknown', 'reserved/unresolved', 'scope'):
        assert field in records, 'missing control field: '+field
    start='## 四、42 条静态失败输入及预期检查\n'; end='\n## 五、L5/L6 验收与修订入口'
    assert body.count(start)==body.count(end)==1, 'scenario boundaries'
    table=body.split(start)[1].split(end)[0]
    rows=re.findall(r'^\| ([^|\n]+) \| (§[^|\n]+) \| ([^|\n]+) \|$',table,re.M)
    assert len(rows)==entry['static_failure_scenarios']==42, 'scenarios'
    assert len(re.findall(r'^\|',table,re.M))==44, 'malformed table row'
    assert len({f.strip() for f,_,_ in rows})==42, 'duplicate input'
    for i,(failure,refs,result) in enumerate(rows,1):
        assert all(x.strip().lower() not in BAD for x in (failure,result)), 'empty scenario'
        assert re.fullmatch(r'§\d{2}(?:、§\d{2})*',refs), 'reference syntax'
        ids=re.findall(r'§(\d{2})',refs)
        assert len(ids)==len(set(ids)) and all(1<=int(n)<=32 for n in ids), 'reference range'
        assert ids==[f'{i:02}'] if i<=32 else len(ids)>=2, 'reference mapping'
