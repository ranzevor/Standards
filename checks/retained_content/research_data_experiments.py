"""Research-topic text structure, not real data/experiment acceptance."""
import sys
if sys.flags.optimize: raise RuntimeError("Validation requires assertions enabled; do not use -O or -OO")
import re
from checks.retained_content.research_baseline import BAD, MECHANISM, assert_lifecycle_header

DATASET_ID = 'STD-L4-MODEL-RESEARCH-009'
EXPERIMENT_ID = 'STD-L4-MODEL-RESEARCH-003'
IDS = {DATASET_ID, EXPERIMENT_ID}


def references(text):
    assert re.fullmatch(r'§\d{2}(?:—§?\d{2})?(?:、§?\d{2}(?:—§?\d{2})?)*', text), 'reference syntax'
    values = []
    for part in text.removeprefix('§').split('、'):
        endpoints = part.replace('§', '').split('—')
        assert len(endpoints) <= 2, 'multiple range endpoints'
        if len(endpoints) == 2:
            start, stop = map(int, endpoints)
            assert start <= stop, 'reversed range'
            values.extend(range(start, stop + 1))
        else:
            values.append(int(endpoints[0]))
    assert values and len(values) == len(set(values)) and all(1 <= n <= 24 for n in values), 'reference bounds'
    return values


def assert_topic_complete(entry, body):
    ident = entry['id']
    assert ident in IDS
    assert body.startswith('# ' + entry['title'] + '\n')
    assert_lifecycle_header(entry, body)
    mechanisms = MECHANISM.findall(body)
    assert entry['mechanism_count'] == len(mechanisms) == 24
    assert len(re.findall(r'^### §', body, re.M)) == 24, 'malformed mechanism'
    for expected, (number, title, mechanism, acceptance) in enumerate(mechanisms, 1):
        assert number == f'{expected:02}'
        assert all(s.strip().lower() not in BAD for s in [title, mechanism, acceptance])
    if ident == DATASET_ID:
        start = '## 六、静态失败输入与合法邻近检查\n'
        end = '\n## 七、审查、批准与版本变更'
        expected_ids = [f'T{i:02}' for i in range(1, 25)] + [f'C{i:02}' for i in range(1, 9)]
        assert entry['static_failure_scenarios'] == 32
        assert entry['static_legal_neighbor_scenarios'] == 32
    else:
        start = '## 五、直接与复合反例矩阵\n'
        end = '\n## 六、最小实施契约及 L5/L6 承接'
        expected_ids = [f'E{i:02}' for i in range(1, 31)] + [f'P{i:02}' for i in range(1, 6)]
        assert entry['static_failure_scenarios'] == 30 and entry['static_positive_scenarios'] == 5
    assert body.count(start) == body.count(end) == 1
    section = body.split(start, 1)[1].split(end, 1)[0]
    rows = re.findall(r'^\| ([TCPE]\d{2}) \| ([^|\n]+) \| ([^|\n]+) \| ([^|\n]+) \|$', section, re.M)
    assert [row[0] for row in rows] == expected_ids, 'case IDs/order/completeness'
    headers = 2 if ident == DATASET_ID else 4
    assert len(re.findall(r'^\|', section, re.M)) == len(rows) + headers, 'malformed case row'
    assert len({row[1] for row in rows}) == len(rows), 'duplicate case input'
    for idx, (case_id, failure, third, last) in enumerate(rows):
        assert all(s.strip().lower() not in BAD for s in [failure, third, last])
        if ident == DATASET_ID:
            assert last.count('§') >= 1
            position = last.index('§')
            outcome = last[:position].strip().rstrip('；;：:').strip()
            assert outcome.lower() not in BAD, 'outcome placeholder'
            refs = references(last[position:].strip())
        else:
            refs = references(third)
        if idx < 24:
            assert idx + 1 in refs, 'direct case mapping'
        elif not case_id.startswith('P'):
            assert len(refs) >= 2, 'compound mapping'
