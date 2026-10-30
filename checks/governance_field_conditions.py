"""Shared finite field conditions and their bilingual generated dictionary row."""
from pathlib import Path
from copy import deepcopy
import argparse
import json
import sys

if sys.flags.optimize:
    raise RuntimeError('Field-condition validation requires normal Python mode; do not use -O or -OO')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

FIELD = 'adoption.selections[].clauses[].acceptance_ids'
RULE_ID = 'clause-proof-field-conditions/1'
ROOT = Path(__file__).resolve().parents[1]
_RULE = {
    'field': FIELD,
    'manual_only': {'minimum_ids': 0, 'maximum_scope': 0},
    'mapped': {'minimum_ids': 1, 'minimum_scope': 1},
    'minimum_manual_criteria': 1,
}


def validate_rule(rule):
    if type(rule) is not dict or set(rule) != {'field', 'manual_only', 'mapped', 'minimum_manual_criteria'} or rule['field'] != FIELD:
        raise ValueError('field rule identity/shape')
    for name, keys in [('manual_only', {'minimum_ids', 'maximum_scope'}), ('mapped', {'minimum_ids', 'minimum_scope'})]:
        item = rule[name]
        if type(item) is not dict or set(item) != keys or any(type(v) is not int or not 0 <= v <= 100 for v in item.values()):
            raise ValueError('field cardinality rule')
    if type(rule['minimum_manual_criteria']) is not int or not 0 <= rule['minimum_manual_criteria'] <= 100:
        raise ValueError('manual criterion cardinality')
    return deepcopy(rule)


def field_rule():
    return validate_rule(_RULE)


def validate_mapping_condition(clause, rule=None):
    """Cardinality/text conditions only; the profile separately checks actual scope and evidence."""
    r = field_rule() if rule is None else validate_rule(rule)
    ids, scope, criteria = (clause[k] for k in ('acceptance_ids', 'automated_scope', 'manual_criteria'))
    if not all(type(v) is list for v in (ids, scope, criteria)):
        raise ValueError('clause proof fields must be arrays')
    if len(criteria) < r['minimum_manual_criteria'] or not all(type(v) is str and v.strip() for v in criteria):
        raise ValueError('clause manual criteria required')
    if ids:
        branch = r['mapped']
        if len(ids) < branch['minimum_ids'] or len(scope) < branch['minimum_scope']:
            raise ValueError('mapped field condition')
    else:
        branch = r['manual_only']
        if len(ids) < branch['minimum_ids'] or len(scope) > branch['maximum_scope']:
            raise ValueError('manual-only field condition')
    return True


def render_condition(rule=None):
    r = field_rule() if rule is None else validate_rule(rule)
    a, b, n = r['manual_only'], r['mapped'], r['minimum_manual_criteria']
    criterion_word = 'criterion' if n == 1 else 'criteria'
    return (
        f"必填数组；IDs为空时：IDs长度≥{a['minimum_ids']}、scope长度≤{a['maximum_scope']}；"
        f"IDs非空时：IDs长度≥{b['minimum_ids']}、scope长度≥{b['minimum_scope']}；人工准则≥{n}且逐项非空 / "
        f"Required array; when IDs are empty: IDs length≥{a['minimum_ids']}, scope length≤{a['maximum_scope']}; "
        f"when IDs are nonempty: IDs length≥{b['minimum_ids']}, scope length≥{b['minimum_scope']}; "
        f"at least {n} nonblank manual {criterion_word}"
    )


def render_row(rule=None):
    meaning = (
        '有限自动合同ID；IDs=acceptance_ids、scope=automated_scope，实际条款/合同关联及人工状态由同一profile核验 / '
        'Finite automated contract IDs; IDs=acceptance_ids and scope=automated_scope; '
        'the same profile checks actual clause/contract relations and manual state'
    )
    return f'| `{FIELD}` | {meaning} | {render_condition(rule)} | F1 |'


def _cells(line):
    return [' '.join(c.split()) for c in line.strip().strip('|').split('|')]


def validate_dictionary(text, rule=None):
    rows = [line for line in text.splitlines() if _cells(line)[0] == '`' + FIELD + '`']
    if len(rows) != 1:
        raise ValueError('one generated proof-field row required')
    if _cells(rows[0]) != _cells(render_row(rule)):
        raise ValueError('proof-field condition projection drift')
    return True


def validate(root=ROOT):
    path = Path(root) / 'templates/project-governance/README.md'
    validate_dictionary(path.read_text(encoding='utf-8'))
    return {'rule_id': RULE_ID, 'field': FIELD, 'rule': field_rule(),
            'dictionary_projection': 'matched',
            'scope': 'Structured cardinality/text conditions and one generated bilingual field row; '
                     'not natural-language sufficiency, actual review evidence or whole-clause conformance.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(validate(args.root), ensure_ascii=False, sort_keys=True))
