"""Version evolution and rollback mechanism structure checks."""
import sys
if sys.flags.optimize: raise RuntimeError("Validation requires assertions enabled; do not use -O or -OO")
import re
from checks.retained_content.profile_integrity import mechanism_parts

VERSION_ROLLBACK_ID = 'STD-L4-AI-AGENT-013'
MECHANISM_COUNT = 28
SCENARIO_COUNT = 37
BAD = {'', 'undefined', 'null', 'none', 'n/a', 'todo', 'tbd', '待定', '待补充', '—'}
START = '## 四、37 条静态失败场景\n'
END = '\n## 五、最小项目应用记录及分层验证'

def assert_version_rollback_complete(entry, body):
    assert type(entry.get('mechanism_count')) is int and entry['mechanism_count'] == MECHANISM_COUNT, 'version mechanism count'
    assert type(entry.get('static_failure_scenarios')) is int and entry['static_failure_scenarios'] == SCENARIO_COUNT, 'version scenario count'
    assert body.count(START) == body.count(END) == 1, 'version scenario section'
    mechanisms = body.split(START)[0]
    headings = re.findall(r'^### §(\d{2}) [^\n]+$', mechanisms, re.M)
    parts = mechanism_parts(mechanisms)
    assert headings == [f'{i:02}' for i in range(1, MECHANISM_COUNT+1)], 'version headings'
    assert len(parts) == MECHANISM_COUNT, 'version mechanism structure'
    for i, (num, mechanism, acceptance) in enumerate(parts, 1):
        assert num == f'{i:02}', 'version mechanism order'
        assert mechanism.strip().lower() not in BAD, 'version mechanism placeholder'
        assert acceptance.strip().lower() not in BAD, 'version acceptance placeholder'
    section = body.split(START)[1].split(END)[0]
    raw_rows = [line for line in section.splitlines() if line.startswith('|')]
    assert raw_rows[:2] == ['| 失败输入 | 机制关联 | 预期判定 |', '| --- | --- | --- |'], 'version table header'
    assert len(raw_rows) == SCENARIO_COUNT+2, 'version rows'
    seen = set()
    for i, row in enumerate(raw_rows[2:], 1):
        match = re.fullmatch(r'\| ([^|\n]+) \| (§[^|\n]+) \| ([^|\n]+) \|', row)
        assert match, ('version row syntax', i)
        failure, refs, expected = match.groups()
        assert failure.strip().lower() not in BAD and expected.strip().lower() not in BAD, ('version placeholder', i)
        assert failure.strip() not in seen, ('version duplicate failure', i)
        seen.add(failure.strip())
        assert re.fullmatch(r'§\d{2}(?:、§\d{2})*', refs), ('version reference syntax', i)
        values = re.findall(r'§(\d{2})', refs)
        assert len(values) == len(set(values)), ('version duplicate reference', i)
        assert all(1 <= int(v) <= MECHANISM_COUNT for v in values), ('version reference range', i)
        if i <= MECHANISM_COUNT:
            assert values == [f'{i:02}'], ('version direct reference', i)
        else:
            assert len(values) >= 2, ('version compound reference', i)
