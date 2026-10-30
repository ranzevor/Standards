"""Per-document structural dispatch with retained detailed scenario contracts."""
import sys
if sys.flags.optimize:
    raise RuntimeError('Validation requires assertions enabled; do not use -O or -OO')
from pathlib import Path
import re
from checks.validation_common import require,read_json,normalized,substantive
from checks.corpus_contract import markdown_blocks,_cells


def clause_references(text,clause_ids):
    known=set(clause_ids)
    if not any(x.startswith('§') for x in known):return []
    require(type(text) is str and text.strip().startswith('§'),'explicit clause reference required')
    result=[]
    for part in re.split(r'[、/，,]',text.strip()):
        match=re.fullmatch(r'\s*§?(\d+)(?:\s*[—–-]\s*§?(\d+))?\s*',part)
        require(match is not None,'malformed or appended clause reference',text)
        first=match[1];last=match[2]
        require('§'+first in known and (last is None or '§'+last in known),'reference outside exact stable clause IDs',text)
        if last is None:result.append('§'+first)
        else:
            require(int(first)<=int(last),'reversed clause reference range',text)
            expanded=['§'+str(n).zfill(len(first)) for n in range(int(first),int(last)+1)]
            require(set(expanded)<=known,'range crosses unregistered clause identity',text);result.extend(expanded)
    require(len(result)==len(set(result)),'duplicate composite clause reference',text)
    return result


def validate_generic_content(profile,text,clauses):
    for clause in clauses:
        require(substantive(clause['title']),'clause title placeholder',clause['clause_id'])
    # The body binding checks exact content, while table parsing validates every
    # raw row. This layer checks references and contrasting case identities only.
    for block in markdown_blocks(text):
        if block['kind']!='table':continue
        rows=[_cells(line) for line in block['visible_text'].splitlines()];header=rows[0];data=rows[2:]
        if not data:continue
        for row in data:
            for i,value in enumerate(row):
                if value.startswith('§') and any(word in header[i] for word in ('机制','条款','关联','对应')):
                    clause_references(value,profile['clause_ids'])
        case_columns=[i for i,h in enumerate(header) if any(w in h for w in ('失败输入','失败场景','合法邻例'))]
        for i in case_columns:
            values=[normalized(row[i]) for row in data]
            require(all(substantive(v) for v in values),'empty scenario field')
            # A repeated short shared verdict can be legitimate; concrete input
            # columns are unique only when they identify the case itself.
            if '失败输入' in header[i] or '失败场景' in header[i]:require(len(values)==len(set(values)),'duplicate failure input')
    return True


def validate_automation(text,clauses):
    lines=text.splitlines();ids=[c['clause_id'] for c in clauses]
    for clause in clauses:
        if not clause['clause_id'].startswith('AUT-'):continue
        body='\n'.join(lines[clause['line']:clause['end_line']])
        acceptance=re.findall(r'^验收 T(\d+)：(.+)$',body,re.M)
        require(len(acceptance)==1 and 'AUT-'+acceptance[0][0]==clause['clause_id'],'automation acceptance identity',clause['clause_id'])
        require(substantive(acceptance[0][1]),'automation empty acceptance')
    return True


def validate_cli(text,clauses):
    matrix=[]
    for block in markdown_blocks(text):
        if block['kind'] not in {'table','table-continuation'}:continue
        for line in block['visible_text'].splitlines():
            row=_cells(line)
            if re.fullmatch(r'M\d+',row[0]):matrix.append(row)
    require([r[0] for r in matrix]==[c['clause_id'] for c in clauses],'CLI complete ordered matrix identity')
    for row,clause in zip(matrix,clauses):
        require(len(row)==5 and all(substantive(x) for x in row),'CLI matrix fields')
        require(normalized(row[1])!=normalized(row[2]),'CLI failure and legal neighbor identical')
        require('完成标准' in clause['fields'],'CLI completion field')
        require(normalized(row[4]).rstrip('。')==clause['fields']['完成标准'].rstrip('。'),'CLI body/matrix completion conflict')
        n=re.search(r'\d+$',clause['clause_id'])[0]
        for value,prefix in zip(row[1:],('F','N','E','C')):
            require(value.startswith(prefix+n+'：'),'CLI case/evidence/completion identity',clause['clause_id'],prefix)
    return True


def validate_game(text,clauses):
    rows=[]
    for block in markdown_blocks(text):
        if block['kind'] not in {'table','table-continuation'}:continue
        for line in block['visible_text'].splitlines():
            row=_cells(line)
            if re.fullmatch(r'[FN]\d+',row[0]):rows.append(row)
    failures=[r for r in rows if r[0].startswith('F')];neighbors=[r for r in rows if r[0].startswith('N')]
    require(failures and neighbors,'game failure and legal-neighbor matrices required')
    require(len({r[0] for r in rows})==len(rows),'game duplicate case identity')
    for row in failures:
        require(len(row)==6 and all(substantive(c) for c in row) and row[-1]=='失败','game failure matrix state/fields')
        refs=re.findall(r'§\d+',row[1]);require(refs and set(refs)<=set(c['clause_id'] for c in clauses),'game case reference')
    for row in neighbors:require(len(row)==3 and all(substantive(c) for c in row),'game legal-neighbor fields')
    return True


def validate_dispatch_registry(root, entries):
    from checks.retained_content.ai_cloud_contracts import DISPATCH
    from checks.retained_content.research_contracts import EXPECTED_IDS
    from checks.retained_content.contract_metrics import CONTRACT_METRICS
    expected = set(DISPATCH) | set(EXPECTED_IDS)
    require(set(CONTRACT_METRICS) == expected, 'content dispatch coverage')
    require(expected <= {e['id'] for e in entries}, 'content profile targets missing document')


def dispatch(entry, text, profile, clauses, root):
    validate_generic_content(profile, text, clauses)
    if entry['domain'] == 'automation' and all(re.fullmatch(r'AUT-\d{2}', c['clause_id']) for c in clauses): validate_automation(text, clauses)
    if entry['domain'] == 'cli-sdk' and '领域通用基线' in entry['title']: validate_cli(text, clauses)
    if entry['domain'] == 'game' and '领域通用基线' in entry['title']: validate_game(text, clauses)
    from checks.retained_content.ai_cloud_contracts import DISPATCH
    from checks.retained_content.research_contracts import EXPECTED_IDS, validate
    from checks.retained_content.contract_metrics import CONTRACT_METRICS
    if entry['id'] not in CONTRACT_METRICS: return 'generic-markdown-contract-v1'
    configured = dict(entry, **CONTRACT_METRICS[entry['id']])
    if entry['id'] in DISPATCH: DISPATCH[entry['id']](configured, text)
    elif entry['id'] in EXPECTED_IDS: validate(configured, text)
    return 'document-content-contract-v1'
