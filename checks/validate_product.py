"""Offline finite-schema checks, exact standard identity and repository links/anchors."""
import sys
if sys.flags.optimize:
    raise RuntimeError('Validation requires assertions enabled; do not use -O or -OO')
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import urllib.parse,re
from checks.validation_common import require,read_json,safe_path,resolve_local_reference,substantive,read_text_exact
from checks.finite_schema import schema_check,KEYWORDS
from checks.generate_index import expected_index
from checks.corpus_contract import references,anchors
from tools.verify_release_bundle import valid_version, validate_release_config
ROOT = Path(__file__).resolve().parents[1]

REQUIRED=['README.md','CONTRIBUTING.md','CODE_OF_CONDUCT.md','SECURITY.md','LICENSE-NOTICE.md','CHANGELOG.md','standards/README.md','governance/RELEASE.md','governance/MAINTENANCE.md','governance/REPOSITORY-NAMING.md','governance/software-repository.json','LICENSE','LICENSES/Apache-2.0.txt','LICENSES/CC-BY-4.0.txt','.github/CODEOWNERS','.github/pull_request_template.md','.github/ISSUE_TEMPLATE/defect.md','.github/ISSUE_TEMPLATE/proposal.md','.github/workflows/quality.yml','checks/definition_interfaces.py','checks/governance_field_conditions.py','checks/software_repository.py','registry/schemas/software-repository-profile.schema.json','templates/project-governance/README.md','templates/repository/README.md']


def validate_project_metadata(project, entries):
    allowed = {'name', 'display_name', 'repository_identifier_style', 'status',
               'audiences', 'scope', 'non_goals', 'constraints', 'formal_adoption',
               'license_status', 'adopted_documents', 'version'}
    require(type(project) is dict and set(project) == allowed,
            'project metadata contains undeclared or missing fields')
    require(project['name'] == 'Standards' and project['repository_identifier_style'] == 'PascalCase'
            and project['status'] == 'adopted' and project['formal_adoption'] is True
            and valid_version(project['version'])
            and project['license_status'] == 'multi-license-CC-BY-4.0-and-Apache-2.0',
            'repository identity and adopted standard set')
    require(project['adopted_documents'] == [item['id'] for item in entries if item['status'] == 'adopted'],
            'adopted document identities differ from canonical registry')
    require(all(project[k] for k in ('audiences', 'scope', 'non_goals', 'constraints')),
            'project reader fields')
    return {'adopted_documents': len(project['adopted_documents']), 'name': project['name']}



def validate_license_policy(root):
    root=Path(root).resolve()
    import hashlib
    expected={'LICENSES/Apache-2.0.txt':'074e6e32c86a4c0ef8b3ed25b721ca23aca83df277cd88106ef7177c354615ff',
              'LICENSES/CC-BY-4.0.txt':'9ba9550ad48438d0836ddab3da480b3b69ffa0aac7b7878b5a0039e7ab429411'}
    for relative,sha256 in expected.items():
        data=safe_path(root,relative).read_bytes()
        require(hashlib.sha256(data).hexdigest()==sha256,'canonical license text identity differs',relative)
    policy=read_text_exact(safe_path(root,'LICENSE'))
    policy_plain=policy.replace('**','')
    require('CC BY 4.0' in policy_plain and 'Apache-2.0' in policy_plain and
            'public redistribution' in policy_plain,
            'root license allocation or redistribution scope missing')
    notice=read_text_exact(safe_path(root,'LICENSE-NOTICE.md'))
    require('Source' in notice and 'Agent Skill' in notice and 'CC BY 4.0' in notice and 'Apache-2.0' in notice,
            'license notice distribution scope differs')
    return {'license_grant':'CC-BY-4.0-and-Apache-2.0','public_distribution_authorized':True}

def validate_adoption(example,entries,clauses):
    known={e['id']:e for e in entries}
    require(type(example) is dict and example.get('example_only') is True and example.get('operation_authorized') is False,'adoption example cannot authorize execution')
    require(substantive(example.get('project')) and substantive(example.get('scope')),'adoption project and scope')
    require(example.get('environment')=='local-synthetic','adoption example environment')
    if example.get('schema_version')=='1':
        selections=[{'id':example['standard_id'],'version':example['standard_version'],'sha256':example['standard_sha256']}]
    else:
        require(example.get('schema_version')=='2','unsupported adoption version')
        selections=example.get('standards');require(type(selections) is list and selections,'exact multi-document adoption selection required')
    ids=[]
    for selected in selections:
        require(selected['id'] in known,'unknown adoption document')
        entry=known[selected['id']];ids.append(entry['id'])
        require(selected['version']==entry['version'] and selected['sha256']==entry['sha256'],'adoption exact identity')
    require(len(ids)==len(set(ids)),'duplicate adoption selection')
    rows=example.get('requirements');require(type(rows) is list and rows,'adoption clause mappings required')
    require(all(type(row) is dict and 'document_id' in row and 'clause_id' in row for row in clauses),
            'canonical document and clause identities required')
    available={(row['document_id'],row['clause_id']) for row in clauses};mapped=[]
    for row in rows:
        doc_id=row.get('document_id',ids[0] if len(ids)==1 else None)
        require(doc_id in ids and (doc_id,row['clause_id']) in available,'adoption clause identity')
        mapped.append((doc_id,row['clause_id']))
        require(row['applicability'] in {'applicable','not-applicable','unknown'},'adoption applicability')
        for field in ('object','check','expected'):require(substantive(row.get(field)),'adoption check field',field)
        require(row.get('status')=='not-run' and row.get('actual') is None,'synthetic adoption cannot claim actual execution')
        if row['applicability']=='not-applicable':require(substantive(row.get('reason')),'not-applicable requires scoped reason')
    require(len(mapped)==len(set(mapped)),'duplicate adoption clause mapping')
    return len(selections)


def validate_links(root):
    root=Path(root).resolve();count=0;anchor_count=0;literal_count=0
    for path in sorted(root.rglob('*.md')):
        if any(x in path.parts for x in ('__pycache__','.git','fixtures')):continue
        safe_path(root,path.relative_to(root).as_posix())
        text=read_text_exact(path)
        for alt in re.findall(r'!\[([^\]]*)\]\([^)]+\)',text):require(alt.strip(),'empty image alternative',str(path))
        for ref in references(text):
            url=urllib.parse.urlsplit(ref['url'])
            if url.scheme or url.netloc:continue
            require(not url.query,'local query cannot be resolved offline',ref['url'])
            raw=urllib.parse.unquote(url.path)
            target=resolve_local_reference(root,path,raw,reference_kind=ref['kind'])
            if target.is_dir():safe_path(root,(target/'README.md').relative_to(root).as_posix())
            if url.fragment:
                require(target.is_file() and urllib.parse.unquote(url.fragment) in anchors(read_text_exact(target)),'missing local anchor',str(path.relative_to(root)),ref['url']);anchor_count+=1
            count+=1;literal_count+=ref['kind']=='literal-path'
    return {'local_links_checked':count,'anchors_checked':anchor_count,'literal_paths_checked':literal_count}


def validate(root=ROOT):
    root=Path(root).resolve()
    from checks.repository_registry import validate_entries
    entries=validate_entries(root)
    for name in REQUIRED:safe_path(root,name)
    require(not (root/'.github/CODEOWNERS.example').exists(),'inactive CODEOWNERS template must not remain beside configured owners')
    owners=(root/'.github/CODEOWNERS').read_text(encoding='utf-8')
    require('* @ranzevor' in owners and '<verified' not in owners,'CODEOWNERS must route to the verified repository owner')
    workflow=(root/'.github/workflows/quality.yml').read_text(encoding='utf-8')
    require('pull_request:' in workflow and 'workflow_dispatch:' in workflow and 'push:' not in workflow,
            'quality workflow trigger boundary differs')
    require("python-version: '3.12'" in workflow, 'quality workflow Python identity differs')
    from checks.software_repository import validate_current_repository
    software_repository=validate_current_repository(root)
    license_policy=validate_license_policy(root)
    schema_check(entries,read_json(root/'registry/schemas/standards.schema.json'))
    for filename in ('document-profiles','requirements','references','technical-dependencies'):
        data=root/'registry'/(filename+'.json');schema=root/'registry/schemas'/(filename+'.schema.json')
        if data.exists() and schema.exists():schema_check(read_json(data),read_json(schema))
    from checks.registry_roles import validate as validate_roles
    from checks.domain_navigation import generate as validate_navigation
    validate_roles(root);validate_navigation(root,True)
    if (root/'templates/ADOPTION.md').is_file():
        from checks.template_interfaces import validate as validate_template
        validate_template(root)
    clauses=read_json(root/'registry/requirements.json')
    example=read_json(root/'examples/adoption.json')
    schema_name='adoption-v2.schema.json' if example.get('schema_version')=='2' else 'adoption.schema.json'
    schema_check(example,read_json(root/'registry/schemas'/schema_name));adopted=validate_adoption(example,entries,clauses)
    require((root/'INDEX.md').read_text(encoding='utf-8')==expected_index(entries),'generated index stale')
    readme=(root/'README.md').read_text(encoding='utf-8')
    for domain in {e['domain'] for e in entries if e['path'].startswith('standards/L4/')}:
        require(f'standards/L4/{domain}/' in readme,'missing domain navigation',domain)
    governance=next((e for e in entries if e['id']=='STD-PG-001'),None)
    if governance:
        require(governance['path'] in readme,'governance reader navigation')
        item=read_json(root/'examples/work-item.json');milestone=read_json(root/'examples/milestone.json')
        require(item['example_only'] is True and item['status']=='open' and milestone['example_only'] is True and milestone['status']=='open','synthetic work records')
        require(item['id'] in milestone['required'] and item['dependencies']==[] and item['owner'] is None,'synthetic work dependency/owner state')
        require(item['object_sha256']==governance['sha256'],'synthetic work item current governance identity')
    project_path=root/'project.json'
    if project_path.exists():
        project=read_json(project_path)
        validate_project_metadata(project, entries)
        config=validate_release_config(read_json(root/'releases/current.json'),project['version'])
        require(safe_path(root,config['notes_path']).read_text(encoding='utf-8').strip(), 'empty release notes')
    return {'documents':len(entries),'schema_examples':1,'adoption_example_documents':adopted,'license_policy':license_policy,
            'software_repository':software_repository,**validate_links(root),
            'schema_support':'finite-documented-keywords',
            'scope':'local product schemas, standard identities, examples, navigation and license allocation'}
if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);a=p.parse_args()
    print(json.dumps(validate(a.root),ensure_ascii=False,sort_keys=True))
