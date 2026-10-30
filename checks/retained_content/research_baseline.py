"""Model-research clause and scenario contract validation."""
import sys
if sys.flags.optimize: raise RuntimeError("Validation requires assertions enabled; do not use -O or -OO")
import re

ID = 'STD-L4-MODEL-RESEARCH-006'
BAD = {'', 'undefined', 'null', 'none', 'todo', 'tbd', 'n/a', '待补充', '待定', '—'}
MECHANISM = re.compile(r'^### §(\d{2}) ([^\n]+)\n\*\*机制：\*\* ([^\n]+)\n(?:\n)?\*\*验收：\*\* ([^\n]+)', re.M)
CASE = re.compile(r'^\| F(\d{2}) \| ([^|\n]+) \| (§\d{2}(?:/\d{2})*) \| ([^|\n]+) \|$', re.M)


def assert_lifecycle_header(entry, body):
    from checks.repository_registry import validate_document_metadata
    validate_document_metadata(entry,body)
    from tools.verify_release_bundle import valid_date
    assert entry['status']=='adopted' and valid_date(entry['effective_date'])


def assert_model_research_complete(entry, body):
    assert entry['id'] == ID
    assert body.startswith('# ' + entry['title'] + '\n')
    assert_lifecycle_header(entry, body)
    mechanisms = MECHANISM.findall(body)
    count = entry['mechanism_count']
    assert count > 0 and len(mechanisms) == count, 'mechanism count'
    assert len(re.findall(r'^### §', body, re.M)) == count, 'malformed mechanism'
    for expected, (number, title, mechanism, acceptance) in enumerate(mechanisms, 1):
        assert number == f'{expected:02}', 'mechanism order'
        assert all(s.strip().lower() not in BAD for s in [title, mechanism, acceptance]), 'placeholder'
    start, end = '## 五、静态失败场景矩阵\n', '\n## 六、L5/L6 接入与交付最小集'
    assert body.count(start) == 1 and body.count(end) == 1, 'case section'
    section = body.split(start, 1)[1].split(end, 1)[0]
    cases = CASE.findall(section)
    n = entry['static_failure_scenarios']
    assert len(cases) == n and n >= count, 'case count'
    assert len(re.findall(r'^\|', section, re.M)) == n + 2, 'malformed case'
    assert len({case[1].strip() for case in cases}) == n, 'duplicate failure input'
    for expected, (number, failure, refs, acceptance) in enumerate(cases, 1):
        assert number == f'{expected:02}', 'case order'
        assert failure.strip().lower() not in BAD and acceptance.strip().lower() not in BAD, 'case placeholder'
        ids = [int(x) for x in refs.removeprefix('§').split('/')]
        assert len(set(ids)) == len(ids) and all(1 <= x <= count for x in ids), 'case references'
        assert ids == [expected] if expected <= count else len(ids) >= 2, 'case mapping'
    positives = re.findall(r'^- P(\d{2})：([^\n]+)$', section, re.M)
    assert len(positives) == entry['static_positive_scenarios'] == 5, 'positive case count'
    assert len(re.findall(r'^- P',section,re.M))==5,'unparsed positive case'
    assert len({content.strip() for _,content in positives})==5,'duplicate positive content'
    for expected, (number, contract) in enumerate(positives, 1):
        assert number == f'{expected:02}' and contract.strip().lower() not in BAD, 'positive case order/content'
        assert len(re.findall(r'（§[^）]*）',contract))==1,'positive reference group count'
        evidence=re.sub(r'（§[^）]*）','',contract).strip(' \t；;。.')
        assert evidence.lower() not in BAD,'positive evidence placeholder'
        refs = re.search(r'（§(\d{2}(?:/\d{2})*)）', contract)
        assert refs, 'positive reference syntax'
        values=[int(x) for x in refs[1].split('/')]
        assert len(values)==len(set(values)) and all(1 <= x <= count for x in values), 'positive references'
    for heading in ['## 一、范围、分层与适用判定', '## 二、规范性用语、术语与证据等级', '## 七、审查、版本与生效']:
        assert body.count(heading + '\n') == 1, 'required section'
    assert sum(body.count(heading+'\n') for heading in ('## 三、来源性质与引用边界','## 三、官方资料与有限命题'))==1,'unique bounded source section'
