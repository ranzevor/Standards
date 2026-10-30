"""Current governance contract bindings. Content sufficiency is reviewed separately."""
import sys
if sys.flags.optimize:
    raise RuntimeError('Validation requires normal Python mode; optimized validation (-O/-OO) is unsupported')
from pathlib import Path
import argparse,ast,hashlib,json,importlib.util
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from checks.validation_common import read_json,safe_path,require,substantive
from checks.repository_registry import validate_entries
from checks.corpus_contract import extract_document
from checks.finite_schema import schema_check

ROOT=Path(__file__).resolve().parents[1]


def symbols(path):
    tree=ast.parse(path.read_text())
    names=set()
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):names.add(node.name)
        elif isinstance(node,ast.ClassDef):
            names.add(node.name)
            names.update(node.name+'.'+child.name for child in node.body if isinstance(child,(ast.FunctionDef,ast.AsyncFunctionDef)))
    return names


def validate_domain(root=ROOT):
    root=Path(root).resolve();entries=validate_entries(root)
    selected={e['id']:e for e in entries if e['domain']=='project-governance'}
    value=read_json(root/'registry/project-governance-domain.json')
    schema_check(value,read_json(root/'registry/schemas/project-governance-domain.schema.json'))
    require(value.get('schema')=='standards-project-governance-domain/1','current governance domain schema')
    # The domain framework carries this matrix's version; individual topics
    # retain their own registered revisions and exact clause identities below.
    require('STD-PG-001' in selected and value.get('version')==selected['STD-PG-001']['version']
            and {e['status'] for e in selected.values()} == {'adopted'}, 'governance current version/adoption')
    ids=value['document_ids'];require(type(ids)is list and len(ids)==len(set(ids))and set(ids)==set(selected),'governance directory omitted/duplicated document')
    actual={}
    for e in selected.values():
        for c in extract_document(e,safe_path(root,e['path']).read_text())['clauses']:
            key=(e['id'],c['clause_id']);require(key not in actual,'duplicate governance clause');actual[key]=c
    rows=value['requirements'];require(type(rows)is list,'governance requirement matrix array')
    seen=set();families=set();cache={}
    for row in rows:
        require(type(row)is dict and set(row)=={'document_id','clause_id','document_sha256','section_sha256','checks','manual_criteria','template','example','technical_sources'},'governance requirement binding fields')
        key=(row['document_id'],row['clause_id']);require(key in actual and key not in seen,'unknown/duplicate governance requirement');seen.add(key)
        clause=actual[key];require(row['document_sha256']==clause['document_sha256']and row['section_sha256']==clause['section_sha256'],'governance exact requirement drift')
        require(type(row['manual_criteria'])is list and row['manual_criteria']and all(substantive(x)for x in row['manual_criteria']),'explicit governance manual criteria required')
        require(type(row['checks'])is list and row['checks'],'actual check mapping required')
        for check in row['checks']:
            require(set(check)=={'kind','path','symbol','command','input','expected','failure','does_not_establish'},'governance check mapping fields')
            require(check['kind']in {'record-binding','finite-model','local-git-runtime','readme-translation-contract','project-record'},'governance check capability kind')
            for field in ('symbol','command','input','expected','failure','does_not_establish'):require(substantive(check[field]),'governance check contract missing '+field)
            path=safe_path(root,check['path']);require(path.suffix=='.py','governance executable Python entry required')
            if check['path']not in cache:cache[check['path']]=symbols(path)
            require(check['symbol']in cache[check['path']],'mapped governance function/class does not exist')
            families.add((check['path'],check['symbol']))
        for field in ('template','example'):safe_path(root,row[field])
        require(type(row['technical_sources'])is list and row['technical_sources'],'governance source/design basis missing')
        source_keys=set()
        for reference in row['technical_sources']:
            if reference['kind']=='governance-design':
                require(set(reference)=={'kind','basis'}and substantive(reference['basis']),'governance design basis fields')
                key=('design',reference['basis'])
            else:
                require(set(reference)=={'kind','packet','source_id'},'finite source reference fields')
                packet=read_json(safe_path(root,reference['packet']))
                sources=packet.get('sources');require(type(sources)is list,'finite source packet lacks sources')
                matches=[source for source in sources if source.get('id',source.get('source_id'))==reference['source_id']]
                require(len(matches)==1,'unknown or ambiguous finite source ID')
                source=matches[0]
                require(substantive(source.get('url',''))and source['url'].startswith('https://'),'finite source URL missing')
                require(substantive(source.get('supported_claim',''))or type(source.get('supported_claims'))is list and source['supported_claims'],'finite source claim scope missing')
                if 'related_clause_ids'in source:
                    require(row['clause_id']in source['related_clause_ids'],'finite source consumer mismatch')
                elif 'consumed_by'in source:
                    consumers=source['consumed_by']
                    require(row['clause_id']in consumers or row['document_id']in consumers or row['document_id']+'::'+row['clause_id']in consumers,'finite source consumer mismatch')
                key=(reference['packet'],reference['source_id'])
            require(key not in source_keys,'duplicate governance source reference');source_keys.add(key)
    require(seen==set(actual),'governance per-clause check/manual mapping omitted')
    return {'documents':len(selected),'clause_units_bound':len(actual),'executable_capability_entries':len(families),
        'mapping_consistency':'pass','scope':'current clause identities, executable check symbols, templates and technical source claims'}


def validate_project(record,root=ROOT):
    """Run the fixed example adapter's schema and cross-field semantic contracts."""
    root=Path(root).resolve();entry=safe_path(root,'examples/project-governance/project_example.py')
    spec=importlib.util.spec_from_file_location('standards_governance_project_example',entry)
    require(spec is not None and spec.loader is not None,'project record adapter unavailable')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    result=module.validate_record(record,root)
    return {**result,'actual_project_implementation_acceptance':'not-run','authority_authenticated':False}


def validate(root=ROOT,project=None):
    result={'domain':validate_domain(root)}
    if project is not None:result['project']=validate_project(read_json(Path(project)),root)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--project',type=Path)
    a=p.parse_args();print(json.dumps(validate(a.root,a.project),ensure_ascii=False,sort_keys=True))
