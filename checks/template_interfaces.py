"""Finite current adoption-template identities, not an adoption or semantic decision."""
import sys
if sys.flags.optimize:raise RuntimeError('Template validation requires normal Python mode; do not use -O or -OO')
from pathlib import Path
import re,hashlib
from checks.validation_common import require,read_json,safe_path
from checks.corpus_contract import markdown_blocks,_cells

def validate(root):
    root=Path(root).resolve();p=safe_path(root,'templates/ADOPTION.md');rows=[]
    for block in markdown_blocks(p.read_text(encoding='utf-8')):
        if block['kind']=='table':rows.extend(_cells(line)for line in block['visible_text'].splitlines())
    def row(label):
        matches=[r for r in rows if r[0]==label];require(len(matches)==1 and len(matches[0])==3,'unique adoption template identity row',label);return matches[0][2]
    identity=re.findall(r'`([^`]+)`',row('规范集合'));require(len(identity)==5,'explicit adoption template mode and four-part identity')
    mode,did,version,path,digest=identity;require(mode in{'technical-reference','trial'},'synthetic template must not claim adopted')
    entries={e['id']:e for e in read_json(root/'registry/standards.json')};require(did in entries,'adoption template names unknown document')
    e=entries[did];require((version,path,digest)==(e['version'],e['path'],e['sha256']),'adoption template current identity drift')
    require(hashlib.sha256(safe_path(root,path).read_bytes()).hexdigest()==digest,'adoption template actual body drift')
    selected=re.findall(r'`([^`]+)`',row('条款'));require(selected and all(x.startswith(did+'::')for x in selected),'template clause/document mismatch')
    from checks.corpus_contract import extract_document
    known={c['clause_id']for c in extract_document(e,safe_path(root,path).read_text(encoding='utf-8'))['clauses']}
    require(all(x.split('::',1)[1]in known for x in selected),'adoption template unknown clause')
    return {'current_template_document':did,'clauses_checked':len(selected),'actual_adoption_established':False}
