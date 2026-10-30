"""Identity adapter for retained content parsers; canonical registration stays singular."""
import sys
if sys.flags.optimize:raise RuntimeError('Validation requires assertions enabled; do not use -O or -OO')
from pathlib import Path
import os
from checks.validation_common import require,read_json
from checks.validate_system import ROOT

def mechanism_contracts(body):
    """Read visible per-clause fields, not a heading-to-field adjacency shortcut."""
    import re
    from checks.corpus_contract import markdown_blocks,headings,fields_of
    hs=headings(markdown_blocks(body));lines=body.splitlines(keepends=True);result=[]
    for h in hs:
        match=re.fullmatch(r'§(\d{2}) (.+)',h['title']) if h['level']==3 else None
        if match is None:continue
        following=next((n for n in hs if n['line']>h['line'] and n['level']<=h['level']),None)
        end=following['line']-1 if following else len(lines)
        fields=fields_of(''.join(lines[h['line']-1:end]))
        require({'机制','验收'}<=fields.keys(),'retained mechanism/acceptance fields missing',match[1])
        result.append({'number':match[1],'title':match[2],
                       'mechanism':fields['机制'],'acceptance':fields['验收']})
    return result

def mechanism_parts(body):
    return [(p['number'],p['mechanism'],p['acceptance']) for p in mechanism_contracts(body)]

def validate_body_identity(entry, body):
    from checks.repository_registry import validate_document_metadata
    validate_document_metadata(entry, body)
    from tools.verify_release_bundle import valid_version
    require(entry['status'] == 'adopted' and valid_version(entry['version']), 'current content contract identity')


def validate_profiles(expected_ids, root=ROOT):
    from checks.retained_content.contract_metrics import CONTRACT_METRICS
    known = {e['id']: e for e in read_json(Path(root)/'registry/standards.json')}
    require(set(expected_ids) <= known.keys() and set(expected_ids) <= CONTRACT_METRICS.keys(), 'content profile coverage')
    return [dict(known[ident], **CONTRACT_METRICS[ident]) for ident in sorted(expected_ids)]
