"""Optimization and adaptation contracts; not mathematical or runtime evidence."""
import sys
if sys.flags.optimize: raise RuntimeError("Validation requires assertions enabled; do not use -O or -OO")
import re
from checks.retained_content.research_baseline import BAD, MECHANISM, assert_lifecycle_header

OPTIMIZATION_ID = 'STD-L4-MODEL-RESEARCH-002'
ADAPTATION_ID = 'STD-L4-MODEL-RESEARCH-005'


def numeric_references(raw, separator, count):
    assert re.fullmatch(r'\d{2}(?:' + re.escape(separator) + r'\d{2})*', raw.strip()), 'numeric reference syntax'
    refs = [int(x) for x in raw.strip().split(separator)]
    assert len(set(refs)) == len(refs) and all(1 <= x <= count for x in refs), 'numeric reference bounds/duplicates'
    return refs


def assert_second_topic_complete(entry, body):
    identity = entry['id']
    assert identity in {OPTIMIZATION_ID, ADAPTATION_ID}, 'optimization/adaptation identity'
    assert body.startswith('# ' + entry['title'] + '\n'), 'title identity'
    normalized = body
    assert_lifecycle_header(entry, normalized)
    mechanisms = MECHANISM.findall(body)
    assert entry['mechanism_count'] == len(mechanisms) == 24, 'mechanism count'
    assert len(re.findall(r'^### §', body, re.M)) == 24, 'malformed mechanism'
    for i, (number, title, mechanism, acceptance) in enumerate(mechanisms, 1):
        assert number == f'{i:02}', 'mechanism order'
        assert all(s.strip().lower() not in BAD for s in [title, mechanism, acceptance]), 'mechanism placeholder'
    if identity == OPTIMIZATION_ID:
        start, end = '## 五、边界与复合失效验收矩阵\n', '\n## 六、L5/L6 落地与证据接口'
        pattern = r'^\| B(\d{2}) \| ([^|\n]+) \| ([^|\n]+) \| ([^|\n]+) \| ([^|\n]+) \|$'
        separator = ','
    else:
        start, end = '## 五、失败、复合失效与合法邻近边界\n', '\n## 六、L5/L6 实施与交付'
        pattern = r'^\|F(\d{2})\|([^|\n]+)\|([^|\n]+)\|([^|\n]+)\|$'
        separator = '/'
    assert body.count(start) == body.count(end) == 1, 'case section identity'
    section = body.split(start, 1)[1].split(end, 1)[0]
    rows = re.findall(pattern, section, re.M)
    assert len(rows) == 28 and len(re.findall(r'^\|', section, re.M)) == 30, 'case count/shape'
    assert len({row[1].strip() for row in rows}) == 28, 'duplicate case input'
    covered = set()
    for i, row in enumerate(rows, 1):
        assert row[0] == f'{i:02}', 'case order'
        assert all(cell.strip().lower() not in BAD for cell in row[1:-1]), 'case placeholder'
        refs = numeric_references(row[-1], separator, 24)
        covered.update(refs)
        if identity == ADAPTATION_ID:
            assert i in refs if i <= 24 else len(refs) >= 2, 'adaptation case mapping'
    assert covered == set(range(1, 25)), 'mechanism case coverage'
    assert entry['static_boundary_scenarios'] == 28, 'boundary count'
    if identity == OPTIMIZATION_ID:
        assert entry['static_legal_neighbor_scenarios'] == 28, 'neighbor count'
        compounds = re.findall(r'^复合场景 C(\d{2})：([^\n]+)$', section, re.M)
        assert len(compounds) == entry['static_composite_scenarios'] == 3, 'composite count'
        assert len(re.findall(r'^复合场景 C', section, re.M)) == 3, 'malformed composite'
        assert len({content.strip() for _, content in compounds}) == 3, 'duplicate composite content'
        for i, (number, content) in enumerate(compounds, 1):
            assert number == f'{i:02}' and content.strip().lower() not in BAD, 'composite identity/content'
        assert entry['static_boundary_scenarios'] == 28 and entry['static_failure_scenarios'] == 31, 'optimization case metadata'
    else:
        assert entry['static_failure_scenarios'] == 28, 'adaptation case metadata'
