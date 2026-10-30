"""Theory, distributed training and material-risk contracts; not research execution."""
import sys
if sys.flags.optimize: raise RuntimeError("Validation requires assertions enabled; do not use -O or -OO")
import re
from checks.retained_content.research_baseline import BAD, MECHANISM, assert_lifecycle_header
from checks.retained_content.research_data_experiments import references
from checks.retained_content.research_optimization_adaptation import numeric_references

DISTRIBUTED_ID = 'STD-L4-MODEL-RESEARCH-004'
THEORY_ID = 'STD-L4-MODEL-RESEARCH-001'
SECURITY_ID = 'STD-L4-MODEL-RESEARCH-007'
ARTIFACT_ID = 'STD-L4-MODEL-RESEARCH-008'
SPECS = {
    DISTRIBUTED_ID: (24, 24, 3, 0, '## 五、失败—合法邻例矩阵\n', '\n## 六、最小证据接口与实现计划'),
    THEORY_ID: (24, 24, 6, 9, '## 六、直接与复合失败矩阵\n', '\n## 七、L5／L6 接入与最小审查材料'),
    SECURITY_ID: (24, 25, 7, 8, '## 四、失败反例、合法邻近情形与复合风险\n', '\n## 五、实施接口与证据最小集'),
    ARTIFACT_ID: (22, 24, 6, 10, '## 六、一般公开工程情境的验收矩阵\n', '\n## 七、最小实施与独立审查'),
}


def bounded_references(raw, count):
    values = references(raw.strip().replace('/', '、'))
    assert all(n <= count for n in values), 'topic reference bounds'
    return values


def section_between(body, start, end):
    assert body.count(start) == body.count(end) == 1, 'section identity'
    return body.split(start, 1)[1].split(end, 1)[0]


def assert_third_topic_complete(entry, body):
    identity = entry['id']
    assert identity in SPECS, 'research identity'
    count, direct_count, composite_count, positive_count, start, end = SPECS[identity]
    assert body.startswith('# ' + entry['title'] + '\n'), 'title identity'
    assert_lifecycle_header(entry, body)
    mechanisms = MECHANISM.findall(body)
    assert entry['mechanism_count'] == len(mechanisms) == count, 'mechanism count'
    assert len(re.findall(r'^### §', body, re.M)) == count, 'malformed mechanism'
    for i, (number, title, mechanism, acceptance) in enumerate(mechanisms, 1):
        assert number == f'{i:02}', 'mechanism order'
        assert all(x.strip().lower() not in BAD for x in [title, mechanism, acceptance]), 'mechanism placeholder'
    assert entry['static_direct_scenarios'] == direct_count, 'direct count metadata'
    assert entry['static_composite_scenarios'] == composite_count, 'composite count metadata'
    assert entry['static_positive_scenarios'] == positive_count, 'positive count metadata'
    assert entry['static_failure_scenarios'] == direct_count + composite_count, 'failure count metadata'
    section = section_between(body, start, end)
    if identity == DISTRIBUTED_ID:
        rows = re.findall(r'^\| B(\d{2}) \| ([^|\n]+) \| ([^|\n]+) \| ([^|\n]+) \| ([^|\n]+) \|$', section, re.M)
        assert len(rows) == direct_count and len(re.findall(r'^\|', section, re.M)) == direct_count + 2, 'distributed table shape'
        assert len({r[1].strip() for r in rows}) == direct_count, 'duplicate distributed input'
        for i, (number, failure, outcome, neighbor, refs) in enumerate(rows, 1):
            assert number == f'{i:02}', 'distributed case order'
            assert all(x.strip().lower() not in BAD for x in [failure, outcome, neighbor]), 'distributed placeholder'
            numeric_references(refs, ',', count)
        assert entry['static_legal_neighbor_scenarios'] == direct_count, 'paired neighbor count'
        # This matrix is illustrative; it does not claim an explicit B-row for every mechanism.
        compounds = re.findall(r'^复合场景 C(\d{2})：([^\n]+)$', section, re.M)
        assert len(compounds) == composite_count and len(re.findall(r'^复合场景 C', section, re.M)) == composite_count, 'composite shape'
        assert len({content.strip() for _, content in compounds}) == composite_count, 'duplicate composite content'
        for i, (number, content) in enumerate(compounds, 1):
            assert number == f'{i:02}' and content.strip().lower() not in BAD, 'composite order/content'
        return
    rows = re.findall(r'^\| ([TFCP])(\d{2}) \| ([^|\n]+) \| ([^|\n]+) \| ([^|\n]+) \|$', section, re.M)
    total = direct_count + composite_count + (0 if identity == THEORY_ID else positive_count)
    assert len(rows) == total and len(re.findall(r'^\|', section, re.M)) == total + 2, 'matrix shape'
    assert len({row[2].strip() for row in rows}) == total, 'duplicate matrix input'
    allowed = {'T': direct_count + composite_count} if identity == THEORY_ID else {'F': direct_count, 'C': composite_count, 'P': positive_count}
    assert {row[0] for row in rows} == set(allowed), 'case group identity'
    for prefix, expected_count in allowed.items():
        group = [row for row in rows if row[0] == prefix]
        assert len(group) == expected_count, 'case group count'
        for i, (_, number, failure, raw_refs, outcome) in enumerate(group, 1):
            assert number == f'{i:02}', 'case group order'
            assert all(x.strip().lower() not in BAD for x in [failure, outcome]), 'case placeholder'
            refs = bounded_references(raw_refs, count)
            if prefix in {'F', 'T'} and i <= count:
                assert i in refs, 'direct case mapping'
            if prefix == 'C' or prefix == 'T' and i > count:
                assert len(refs) >= 2, 'compound case mapping'
    if identity == THEORY_ID:
        positives = section_between(body, '## 五、可核验玩具推演与合法邻例\n', '\n## 六、直接与复合失败矩阵')
        rows = re.findall(r'^- \*\*P(\d{2}) ([^：\n]+)：\*\* ([^\n]+)$', positives, re.M)
        assert len(rows) == positive_count and len(re.findall(r'^- \*\*P', positives, re.M)) == positive_count, 'theory positive shape'
        assert len({row[2].strip() for row in rows}) == positive_count, 'duplicate positive content'
        for i, (number, title, content) in enumerate(rows, 1):
            assert number == f'{i:02}', 'positive order'
            assert title.strip().lower() not in BAD and content.strip().lower() not in BAD, 'positive placeholder'
            refs = re.findall(r'（(§[^（）]+)）', content)
            assert len(refs) == 1, 'positive reference contract'
            evidence = re.sub(r'（§[^（）]+）', '', content).strip(' \t；;。.')
            assert evidence.lower() not in BAD, 'positive evidence placeholder'
            bounded_references(refs[0], count)
