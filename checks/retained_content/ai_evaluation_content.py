"""Checks only document structure and mapping, never semantic/model performance."""
import sys
if sys.flags.optimize: raise RuntimeError("Validation requires assertions enabled; do not use -O or -OO")
import re
from checks.retained_content.profile_integrity import mechanism_parts

ID = 'STD-L4-AI-AGENT-002'


def assert_evaluation_complete(entry, body):
    parts = mechanism_parts(body)
    assert len(parts) == entry['mechanism_count'] == 30, 'evaluation mechanism count'
    assert [p[0] for p in parts] == [f'{i:02}' for i in range(1, 31)], 'evaluation order'
    bad = {'', 'undefined', 'null', 'none', 'n/a', 'todo', 'tbd', '待定', '待补充', '无', '—'}
    assert all(v.strip().lower() not in bad for _, m, a in parts for v in (m, a)), 'evaluation empty content'
    start = '## 四、静态失败输入与预期判定\n'
    end = '\n## 五、指标、门禁与最小实施实例'
    assert body.count(start) == body.count(end) == 1, 'evaluation section'
    section = body.split(start)[1].split(end)[0]
    lines = [line for line in section.splitlines() if line.startswith('|')]
    assert len(lines) == 40, 'evaluation malformed rows'
    rows = re.findall(r'^\| ([^|\n]+) \| (§[^|\n]+) \| ([^|\n]+) \|$', section, re.M)
    assert len(rows) == entry['static_failure_scenarios'] == 38, 'evaluation scenarios'
    assert len({r[0] for r in rows}) == len(rows), 'evaluation duplicates'
    for i, (failure, refs, expected) in enumerate(rows, 1):
        assert failure.strip().lower() not in bad and expected.strip().lower() not in bad
        assert re.fullmatch(r'§\d{2}(?:、§\d{2})*', refs), 'evaluation reference syntax'
        ids = re.findall(r'§(\d{2})', refs)
        assert len(ids) == len(set(ids)) and all(1 <= int(n) <= 30 for n in ids)
        if i <= 30:
            assert ids == [f'{i:02}'], 'evaluation direct mapping'
        else:
            assert len(ids) >= 2, 'evaluation compound mapping'
