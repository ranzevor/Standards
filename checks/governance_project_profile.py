"""Finite project-profile predicates; manual clause judgments are separately recorded."""
import sys
if sys.flags.optimize:raise RuntimeError('Project-profile validation requires normal Python mode; do not use -O or -OO')
from pathlib import Path
from copy import deepcopy
from checks import governance_models as g
from checks.validation_common import read_json
from checks.governance_field_conditions import validate_mapping_condition

SCENARIO_PREDICATES={
 'normal':['csv-column-output'], 'bad-row':['csv-malformed-refusal'],
 'wrong-input-identity':['csv-input-identity'], 'wrong-output-identity':['csv-output-identity'],
 'existing-output':['csv-no-overwrite'], 'quoted-neighbor':['csv-quoted-neighbor'],
 'missing-check':['aggregate-missing'], 'failed-check':['aggregate-fail'], 'unknown-check':['aggregate-unknown'],
 'stale-revision':['stale-scope-revision'], 'wrong-adoption-scope':['adoption-scope'],
 'unresolved-dependency':['required-work-dependency'], 'active-material':['active-material-reference'],
 'recovery':['event-outcome-recovery'], 'maintenance-boundary':['maintenance-commitment'],
 'work-state-boundary':['work-state-closure'], 'configuration-boundary':['configuration-precedence-types'],
 'reference-boundary':['exact-reference-identity'], 'traceability-boundary':['traceability-closure'],
 'four-axis-boundary':['four-axis-separation'], 'milestone-boundary':['milestone-verified-closure'],
 'dependency-lock-boundary':['dependency-content-lock'], 'release-boundary':['release-blockers'],
 'capacity-boundary':['capacity-boundary'], 'standard-closure-boundary':['required-standard-closure'],
}
CLAUSE_PREDICATES={
 ('STD-PG-001','PGF-01'):{'exact-reference-identity'},
 ('STD-PG-001','PGF-04'):{'four-axis-separation'},
 ('STD-PG-002','PGI-01'):{'csv-column-output'},('STD-PG-002','PGI-04'):{'stale-scope-revision'},
 ('STD-PG-003','PGT-03'):{'traceability-closure'},
 ('STD-PG-003','PGT-04'):{'csv-malformed-refusal','event-outcome-recovery'},
 ('STD-PG-003','PGT-05'):{'required-work-dependency','milestone-verified-closure'},
 ('STD-PG-009','PGC-02'):{'exact-reference-identity','release-blockers'},
 ('STD-PG-010','PGK-02'):{'work-state-closure'},
 ('STD-PG-010','PGK-03'):{'required-work-dependency','milestone-verified-closure'},
 ('STD-PG-011','PGQ-01'):{'csv-column-output'},
 ('STD-PG-011','PGQ-02'):{'csv-malformed-refusal','csv-quoted-neighbor'},
 ('STD-PG-011','PGQ-04'):{'aggregate-missing','aggregate-fail','aggregate-unknown','event-outcome-recovery'},
 ('STD-PG-012','PGS-01'):{'dependency-content-lock'},
 ('STD-PG-012','PGS-03'):{'configuration-precedence-types'},
 ('STD-PG-015','PGV-02'):{'release-blockers'},
 ('STD-PG-017','PGM-01'):{'maintenance-commitment'},
 ('STD-PG-019','PGX-03'):{'active-material-reference','capacity-boundary'},
 ('STD-PG-019','PGX-04'):{'active-material-reference'},
 ('STD-PG-020','PGN-01'):{'exact-reference-identity'},
 ('STD-PG-020','PGN-02'):{'adoption-scope','required-standard-closure'},
 ('STD-L1-001','GG-05'):{'four-axis-separation'},
 ('STD-L6-001','ADP-01'):{'exact-reference-identity','adoption-scope'},
 ('STD-L6-001','ADP-02'):{'required-standard-closure'},
 ('STD-L6-001','ADP-05'):{'aggregate-missing','aggregate-fail','aggregate-unknown','event-outcome-recovery'},
}

def verification_axes(record,*,document='draft',technical_review='not-run',implementation='not-run'):
    """Build a finite scenario input; PR review is not a normative review-axis value."""
    return validate_verification_axes({'document':document,'technical_review':technical_review,
            'adoption':record['adoption']['state'],'implementation':implementation})

def validate_verification_axes(value):
    g.need(type(value)is dict and set(value)=={'document','technical_review','adoption','implementation'},'four independent axis keys')
    allowed={'document':{'draft','review','candidate','adopted','deprecated','withdrawn','historical'},
             'technical_review':{'not-run','partial','fail','pass'},
             'adoption':{'not-decided','adopted','rejected','withdrawn'},
             'implementation':{'not-run','partial','fail','pass','unknown','not-applicable'}}
    g.need(all(type(value[k])is str and value[k]in allowed[k]for k in allowed),'four independent axis values')
    return deepcopy(value)

def validate_reference(selection,registry,root):
    sid=selection['document_id'];g.need(sid in registry,'unknown reference identity')
    e=registry[sid];g.need(all(selection[k]==e[k]for k in ('version','path','sha256')),'reference exact identity drift')
    p=(Path(root)/e['path']).resolve();g.need(p.is_relative_to(Path(root).resolve())and p.is_file(),'reference path missing/escaping')
    import hashlib
    g.need(hashlib.sha256(p.read_bytes()).hexdigest()==e['sha256'],'reference actual bytes drift')
    return True

def validate_traceability(record):
    contracts={x['id']:x for x in record['acceptance']};g.need(len(contracts)==len(record['acceptance']),'duplicate trace contract')
    required={r['id']for r in record['requirements']};seen=set()
    for r in record['requirements']:
        ids=g.unique(r['acceptance_ids'],'trace contracts');g.need(ids and ids<=set(contracts),'unresolved trace contract')
        g.need(all(contracts[i]['requirement_id']==r['id']for i in ids),'trace reverse requirement mismatch');seen|=ids
    g.need(seen==set(contracts)and all(c['requirement_id']in required for c in contracts.values()),'orphan trace contract')
    return True

def validate_interface_bindings(record,root):
    selected={(s['document_id'],c['id']):c for s in record['adoption']['selections']for c in s['clauses']}
    edges=[e for e in read_json(Path(root)/'registry/technical-dependencies.json')if e['required']and(e['from_document'],e['from_clause'])in selected]
    key=lambda e:(e['from_document'],e['from_clause'],e['to_document'],e['to_clause'],e['interface'])
    expected={key(e):e for e in edges};bindings=record['adoption']['dependency_bindings']
    actual={key(e):e for e in bindings};g.need(len(actual)==len(bindings)and set(actual)==set(expected),'necessary standard binding set mismatch')
    for k,b in actual.items():
        e=expected[k];g.need(b['condition']==e['condition']and g.text(b['reason']),'necessary standard condition/reason drift')
        consumer=selected[k[:2]]
        if consumer['applicability']=='not-applicable':g.need(b['applicability']=='not-triggered','nonapplicable consumer triggered dependency')
        elif consumer['applicability']=='undetermined':g.need(b['applicability']=='undetermined','undetermined consumer dependency')
        if b['applicability']=='applies':
            g.need(consumer['applicability']=='applicable'and(k[2],k[3])in selected and selected[(k[2],k[3])]['applicability']=='applicable','necessary standard provider absent/not applicable')
    return len(actual)

def validate_proof_scopes(record,root):
    contracts={c['id']:c for c in record['acceptance']}
    for c in contracts.values():
        g.need(c['scenario']in SCENARIO_PREDICATES,'unimplemented finite profile scenario')
        g.need(g.unique(c['proves'],'finite predicates')==set(SCENARIO_PREDICATES[c['scenario']]),'scenario/predicate binding mismatch')
        g.need(c['layer']==('isolated-runtime'if c['scenario']in {'normal','bad-row','wrong-input-identity','wrong-output-identity','existing-output','quoted-neighbor'}else'finite-model'),'scenario evidence-layer mismatch')
    manual=0
    for s in record['adoption']['selections']:
        for c in s['clauses']:
            scope=g.unique(c['automated_scope'],'clause automated scope');ids=g.unique(c['acceptance_ids'],'clause acceptance')
            allowed=CLAUSE_PREDICATES.get((s['document_id'],c['id']),set())
            predicates={p for i in ids for p in contracts[i]['proves']}
            g.need(scope<=allowed and scope<=predicates,'clause finite predicate not checked or unrelated')
            g.need(all(scope&set(contracts[i]['proves'])for i in ids),'unrelated clause check mapping')
            g.need(not ids or scope,'mapped check lacks explicit finite proof scope')
            validate_mapping_condition(c)
            if c['manual_state']=='not-run':g.need(not c['manual_evidence'],'unrun manual review invents evidence')
            else:g.need(c['manual_evidence']and not record['example_only'],'manual result needs actual nonsynthetic evidence')
            if c['applicability']!='applicable':g.need(not ids and not scope,'nonapplicable clause has automated compliance mapping')
            manual+=c['manual_state']!='pass'
    bindings=validate_interface_bindings(record,root)
    return {'selected_clause_manual_items_pending':manual,'necessary_standard_bindings':bindings,'finite_checks_establish_selected_clause_conformance':False}

def rejected(call):
    try:call()
    except ValueError:return True
    return False

def observe(scenario,record,root):
    if scenario=='maintenance-boundary':
        base=dict(record['maintenance'],actual_owner=None,commitment_reference=None)
        good=g.validate_maintenance(base)
        bad=dict(base,response_hours=24)
        neighbor=dict(base,state='limited',supported_versions=['synthetic-0.1'],response_hours=None)
        return {'normal':good,'unbacked_commitment_rejected':rejected(lambda:g.validate_maintenance(bad)),'limited_without_sla':g.validate_maintenance(neighbor)}
    if scenario=='work-state-boundary':
        item={'id':'synthetic','state':'verification','acceptance_ids':['a'],'dependencies':[],'history':[],'resolution':None}
        bad=rejected(lambda:g.transition_work_item(item,'closed',resolution='verified-fix',evidence={'a':'unknown'}))
        closed=g.transition_work_item(item,'closed',resolution='verified-delivery',evidence={'a':'pass'})
        reopened=g.transition_work_item(closed,'triaged')
        triaged=dict(item,state='triaged');nonverified=g.transition_work_item(triaged,'closed',resolution='duplicate',reason='same synthetic intent')
        return {'unknown_rejected':bad,'verified_resolution':closed['resolution'],'history_retained':len(reopened['history'])==2 and item['state']=='verification','nonverified_not_milestone':not g.milestone_ready([nonverified],['synthetic'])}
    if scenario=='configuration-boundary':
        schema={'timeout':{'type':'integer','required':True,'minimum':1,'maximum':30}}
        result=g.effective_config({'timeout':30},{'timeout':20},{'timeout':10},schema)
        return {'value':result['values']['timeout'],'origin':result['origins']['timeout'],'boolean_rejected':rejected(lambda:g.effective_config({'timeout':True},{},{},schema)),'unknown_rejected':rejected(lambda:g.effective_config({'timeout':10,'extra':1},{},{},schema)),'boundary_value':g.effective_config({'timeout':1},{},{},schema)['values']['timeout']}
    if scenario=='reference-boundary':
        registry={e['id']:e for e in read_json(Path(root)/'registry/standards.json')};s=record['adoption']['selections'][0];bad=dict(s,sha256='f'*64)
        return {'normal':validate_reference(s,registry,root),'wrong_hash_rejected':rejected(lambda:validate_reference(bad,registry,root)),'equivalent_copy':validate_reference(deepcopy(s),registry,root)}
    if scenario=='traceability-boundary':
        good=validate_traceability(record);bad=deepcopy(record);bad['acceptance'][0]['requirement_id']='missing'
        neighbor=deepcopy(record);neighbor['requirements'][0]['statement']+=' (same required behavior)'
        return {'normal':good,'wrong_reverse_rejected':rejected(lambda:validate_traceability(bad)),'wording_neighbor':validate_traceability(neighbor)}
    if scenario=='four-axis-boundary':
        axes=verification_axes(record);normal=validate_verification_axes(axes);bad=dict(axes,implementation='draft')
        mixed=validate_verification_axes(dict(axes,technical_review='pass'))
        return {'normal':normal,'bad_axis_rejected':rejected(lambda:validate_verification_axes(bad)),'review_pass_keeps_implementation':mixed['implementation'],'review_pass_keeps_adoption':mixed['adoption']}
    if scenario=='milestone-boundary':
        a={'id':'a','state':'closed','resolution':'verified-delivery','dependencies':['b']};b={'id':'b','state':'verification','resolution':None,'dependencies':[]}
        blocked=not g.milestone_ready([a,b],['a']);b['state']='closed';b['resolution']='verified-delivery'
        normal=g.milestone_ready([a,b],['a']);b['resolution']='duplicate'
        return {'open_dependency_blocks':blocked,'verified_closure':normal,'duplicate_not_verified':not g.milestone_ready([a,b],['a'])}
    if scenario=='dependency-lock-boundary':
        row={'id':'standard','kind':'standard','purpose':'finite identity check','source':'selected local registry','locked_version':'0.1','resolved_version':'0.1','expected_sha256':'a'*64,'observed_sha256':'a'*64}
        return {'normal':g.validate_dependencies_config([row]),'wrong_hash_rejected':rejected(lambda:g.validate_dependencies_config([dict(row,observed_sha256='b'*64)])),'wrong_version_rejected':rejected(lambda:g.validate_dependencies_config([dict(row,resolved_version='0.2')])),'empty_optional_set':g.validate_dependencies_config([])}
    if scenario=='release-boundary':
        h='a'*64;r={'candidate_sha256':h,'source_sha256':h,'checks':[{'id':'a','state':'pass','candidate_sha256':h}],'required_checks':['a'],'review':{'state':'pass','candidate_sha256':h},'distribution_state':'approved-scope','license_state':'selected-for-scope','artifacts':[{'path':'synthetic.txt','sha256':'b'*64,'source_sha256':h}]}
        current=g.release_ready(r);bad=deepcopy(r);bad['checks'][0]['candidate_sha256']='c'*64
        unknown=deepcopy(r);unknown['checks'][0]['state']='unknown'
        license_=deepcopy(r);license_['license_state']='not-decided'
        return {'synthetic_ready':current,'stale_rejected':rejected(lambda:g.release_ready(bad)),'unknown_rejected':rejected(lambda:g.release_ready(unknown)),'unselected_license_rejected':rejected(lambda:g.release_ready(license_))}
    if scenario=='capacity-boundary':
        return {'exact_boundary':g.capacity_allowed(100,20,10,70),'one_byte_short_rejected':not g.capacity_allowed(99,20,10,70),'read_only_small':g.capacity_allowed(100,0,1,70)}
    if scenario=='standard-closure-boundary':
        good=validate_interface_bindings(record,root);bad=deepcopy(record);row=next(e for e in bad['adoption']['dependency_bindings']if e['applicability']=='applies');provider=(row['to_document'],row['to_clause'])
        for s in bad['adoption']['selections']:
            if s['document_id']==provider[0]:s['clauses']=[c for c in s['clauses']if c['id']!=provider[1]]
        return {'normal':good>0,'missing_provider_rejected':rejected(lambda:validate_interface_bindings(bad,root)),'equivalent_copy':validate_interface_bindings(deepcopy(record),root)==good}
    raise ValueError('unknown additional finite scenario')
