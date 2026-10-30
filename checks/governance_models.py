"""Finite governance record/state models. No real authority or operation is authenticated."""
import sys
if sys.flags.optimize:
    raise RuntimeError('Validation requires normal Python mode; optimized validation (-O/-OO) is unsupported')
from copy import deepcopy
from datetime import datetime,timezone
import hashlib,json,math,re
from pathlib import PurePosixPath
from checks.finite_schema import json_equal


def need(value,message):
    if not value:raise ValueError(message)


def text(value):return type(value)is str and bool(value.strip())
def integer(value):return type(value)is int and value>=0
def hash_value(value):return type(value)is str and re.fullmatch('[0-9a-f]{64}',value)is not None


def unique(values,label):
    need(type(values)is list and all(text(x)for x in values)and len(values)==len(set(values)),label+' must be unique nonempty identifiers')
    return set(values)


def instant(value):
    need(type(value)is str and re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?(?:Z|[+-][0-9]{2}:[0-9]{2})',value)is not None,'aware ISO timestamp required')
    if not value.endswith('Z'):need(int(value[-5:-3])<24 and int(value[-2:])<60,'timezone offset lexical range')
    try:v=datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError as e:raise ValueError('invalid calendar timestamp')from e
    need(v.tzinfo is not None,'timezone required')
    return v.astimezone(timezone.utc)


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def required_closure(items,roots):
    need(type(items)is list,'dependency items array required')
    byid={x['id']:x for x in items};need(len(byid)==len(items)and all(text(x)for x in byid),'duplicate/empty dependency identity')
    roots=unique(roots,'dependency roots');seen=set();visiting=set()
    def visit(ident):
        need(ident in byid,'missing required dependency '+ident)
        need(ident not in visiting,'required dependency cycle')
        if ident in seen:return
        visiting.add(ident)
        for dep in sorted(unique(byid[ident]['dependencies'],'dependencies')):visit(dep)
        visiting.remove(ident);seen.add(ident)
    for ident in sorted(roots):visit(ident)
    return seen


def apply_scope_change(current,change):
    need(integer(current['revision'])and integer(change['expected_revision']),'scope revision type')
    before=unique(current['in_scope'],'current scope');excluded=unique(current['out_of_scope'],'scope exclusions')
    target=unique(change['in_scope'],'proposed scope');target_excluded=unique(change['out_of_scope'],'proposed exclusions')
    need(not before&excluded and not target&target_excluded,'scope overlaps explicit exclusions')
    need(text(change['intent_id']),'scope intent identity')
    payload={'in_scope':sorted(target),'out_of_scope':sorted(target_excluded)}
    intent=canonical_hash(payload)
    history=current['history'];need(type(history)is list,'scope history array')
    matches=[x for x in history if x['intent_id']==change['intent_id']]
    if matches:
        need(len(matches)==1 and matches[0]['intent_sha256']==intent,'same scope intent has conflicting content')
        return deepcopy(current)
    need(current['revision']==change['expected_revision'],'stale scope revision')
    decision=change['decision']
    need(decision['state']=='approved'and decision['intent_sha256']==intent,'scope decision missing or bound to other content')
    result=deepcopy(current);result['revision']+=1;result['in_scope']=sorted(target);result['out_of_scope']=sorted(target_excluded)
    result['history'].append({'intent_id':change['intent_id'],'intent_sha256':intent,'revision':result['revision'],
        'before':{'in_scope':sorted(before),'out_of_scope':sorted(excluded)},'after':payload})
    return result


WORK_EDGES={'open':{'triaged'},'triaged':{'in-progress','closed'},'in-progress':{'verification','blocked'},'blocked':{'in-progress'},'verification':{'in-progress','closed'},'closed':{'triaged'}}


def transition_work_item(item,target,*,resolution=None,evidence=None,reason=None):
    need(target in WORK_EDGES.get(item['state'],set()),'invalid work-item transition')
    if target=='closed':
        need(resolution in {'verified-fix','verified-delivery','not-reproducible','rejected','duplicate'},'close resolution required')
        if resolution.startswith('verified-'):
            need(item['state']=='verification'and evidence is not None,'verified close requires verification')
            required=unique(item['acceptance_ids'],'work acceptance conditions')
            need(required and set(evidence)==required and all(x=='pass'for x in evidence.values()),'verified close lacks exact passed conditions')
        else:need(text(reason),'nonverification close reason required')
    result=deepcopy(item);result['state']=target
    result.setdefault('history',[]).append({'from':item['state'],'to':target,'resolution':resolution,'reason':reason})
    result['resolution']=resolution if target=='closed'else None
    return result


def milestone_ready(items,required_ids):
    closed=required_closure(items,required_ids);byid={x['id']:x for x in items}
    return bool(closed)and all(byid[x]['state']=='closed'and byid[x].get('resolution')in {'verified-fix','verified-delivery'}for x in closed)


def finite_json(value):
    if value is None or type(value)in {str,bool,int}:return True
    if type(value)is float:return math.isfinite(value)
    if type(value)is list:return all(finite_json(x)for x in value)
    if type(value)is dict:return all(type(k)is str and finite_json(v)for k,v in value.items())
    return False


def evaluate_check(contract,event):
    need(text(contract['id'])and hash_value(contract['input_sha256'])and hash_value(contract['environment_sha256']),'check identity')
    need(contract['layer']in {'document-check','finite-model','isolated-runtime','product-runtime'},'check layer')
    need(contract['expectation_origin']in {'requirement','protocol','pre-registered-hypothesis'},'independent expectation origin required')
    need(type(contract['expected_exit'])is int and finite_json(contract['expected_value']),'finite expected outcome')
    if event is None:return 'not-run'
    need(all(event[k]==contract[k]for k in ('id','input_sha256','environment_sha256','layer')),'check object/environment/layer drift')
    need(event['completion']in {'completed','timed-out','skipped'},'execution completion state')
    if event['completion']=='skipped':return 'not-run'
    if event['completion']=='timed-out':return 'unknown'
    need(type(event['exit_code'])is int and finite_json(event['actual']),'actual result type')
    return 'pass'if event['exit_code']==contract['expected_exit']and json_equal(event['actual'],contract['expected_value'])else'fail'


def aggregate_checks(results,required_ids):
    needed=unique(required_ids,'required checks')
    need(type(results)is list and all(type(x)is dict and text(x.get('id'))for x in results),'check results')
    byid={x['id']:x for x in results};need(len(byid)==len(results),'duplicate check result')
    need(all(x['state']in {'pass','fail','partial','not-run','unknown','not-applicable'}for x in results),'check result state')
    if not needed:return 'not-applicable'
    states=[byid[x]['state']if x in byid else'not-run'for x in needed]
    if 'fail'in states:return 'fail'
    if 'unknown'in states:return 'unknown'
    if all(x=='pass'for x in states):return 'pass'
    if all(x=='not-applicable'for x in states):return 'not-applicable'
    return 'partial'if any(x in {'pass','partial'}for x in states)else'not-run'


def validate_change(change):
    need(hash_value(change['base_sha256'])and hash_value(change['candidate_sha256']),'change exact identity')
    expected=unique(change['review_units'],'required review units')
    need(expected,'review unit set is empty')
    reviews=change['reviews'];need(type(reviews)is list,'reviews array')
    covered=set()
    for row in reviews:
        need(row['candidate_sha256']==change['candidate_sha256'],'stale review candidate')
        need(text(row['reviewer'])and row['reviewer']!=change['author'],'author cannot self-declare independence')
        units=unique(row['units'],'review coverage');need(units<=expected,'review outside declared unit set')
        need(row['state']=='pass'and text(row['process_evidence']),'review record incomplete or failed')
        covered|=units
    need(covered==expected,'review coverage missing required unit')
    findings=change['findings'];need(type(findings)is list and len({x['id']for x in findings})==len(findings),'finding identity')
    for row in findings:
        need(type(row.get('blocking'))is bool,'finding blocking must be an explicit boolean')
        need(row.get('state')in {'open','partial','closed'},'finding state')
        required=unique(row['criteria'],'finding criteria');closed=unique(row['closed_criteria'],'closed finding criteria')
        need(closed<=required,'unknown finding closure criterion')
        if row['state']=='closed':need(required and closed==required,'partly closed finding or empty closure')
        if row['blocking']:need(row['state']=='closed'and required and closed==required,'open or partly closed blocking finding')
    return {'record_consistency':True,'independence_authenticated':False,'semantic_truth_established':False}


def merge_ready(change,current_base_sha256,checks,required_ids):
    validate_change(change)
    need(change['base_sha256']==current_base_sha256,'target HEAD changed')
    need(all(x['candidate_sha256']==change['candidate_sha256']for x in checks),'check belongs to other candidate')
    need(aggregate_checks(checks,required_ids)=='pass','required integration checks incomplete')
    return True


def operation_allowed(grant,operation,now):
    moment=instant(now)
    need(type(grant['actions'])is list and all(text(x)for x in grant['actions']),'grant actions')
    need(integer(grant['epoch'])and integer(operation['epoch']),'operation epoch')
    need(all(text(value[k])for value in (grant,operation)for k in ('subject','target','environment'))and text(operation['action']),'operation subject/target/environment/action')
    return (moment<instant(grant['expires_at'])and instant(grant['not_before'])<=moment
        and all(grant[k]==operation[k]for k in ('subject','target','environment','epoch'))
        and operation['action']in grant['actions']and grant['state']=='active')


def effective_config(defaults,environment,command_line,schema):
    need(all(type(x)is dict for x in (defaults,environment,command_line,schema)),'configuration objects')
    values={};origins={}
    for origin,part in [('default',defaults),('environment',environment),('command-line',command_line)]:
        need(set(part)<=set(schema),'unknown configuration key')
        for key,value in part.items():
            rule=schema[key];kind={'integer':int,'string':str,'boolean':bool}.get(rule['type'])
            need(kind is not None and type(value)is kind,'configuration type '+key)
            if 'minimum'in rule:need(value>=rule['minimum'],'configuration below minimum')
            if 'maximum'in rule:need(value<=rule['maximum'],'configuration above maximum')
            values[key]=value;origins[key]=origin
    need(all(not rule.get('required',False)or key in values for key,rule in schema.items()),'required configuration absent')
    return {'values':values,'origins':origins}


def validate_dependencies_config(rows):
    need(type(rows)is list and len({x['id']for x in rows})==len(rows),'dependency identities')
    for row in rows:
        need(text(row['id'])and row['kind']in {'runtime','development','optional','service','standard'},'dependency kind')
        need(text(row['purpose'])and text(row['source'])and text(row['locked_version']),'dependency purpose/source/lock')
        if row['kind']!='service':need(hash_value(row['expected_sha256'])and row['observed_sha256']==row['expected_sha256'],'dependency content identity drift')
        need(row['resolved_version']==row['locked_version'],'resolved/locked version drift')
    return True


def exception_valid(record,now):
    need(text(record['id'])and text(record['requirement_id'])and text(record['scope'])and text(record['reason']),'exception identity/scope')
    need(hash_value(record['document_sha256'])and type(record['compensations'])is list and record['compensations'],'bounded exception compensations')
    need(type(record['review_triggered'])is bool,'explicit exception review-trigger state required')
    return (record['state']=='approved'and instant(record['starts_at'])<=instant(now)<instant(record['expires_at'])
        and not record['review_triggered']and all(x['state']=='pass'for x in record['compensations']))


def adoption_object_identity(value):
    need(type(value)is dict and all(text(value.get(k))for k in ('document_id','version','path'))
         and hash_value(value.get('sha256')),'adoption exact object')
    path=PurePosixPath(value['path'])
    need(bool(path.parts)and not path.is_absolute()and path.as_posix()==value['path']
         and all(p not in {'.','..'}for p in path.parts)and '\\'not in value['path']
         and '\x00'not in value['path'],'adoption canonical relative path')
    return {k:value[k]for k in ('document_id','version','path','sha256')}


def upgrade_adoption(current,proposed,decision,expected_revision):
    need(integer(current['revision'])and integer(expected_revision),'adoption revision type')
    need(current['revision']==expected_revision,'stale adoption revision')
    old=adoption_object_identity(current['selection']);new=adoption_object_identity(proposed)
    need(new['document_id']==old['document_id'],'upgrade changes document identity')
    need(type(decision)is dict and decision.get('state')=='approved'
         and decision.get('target_sha256')==new['sha256'],'upgrade decision missing or wrong object')
    prior=current.get('decision')
    if prior is not None:
        need(type(prior)is dict and prior.get('state')in {'approved','not-decided','rejected','withdrawn'},'prior adoption decision state')
        if prior['state']=='approved':need(prior.get('target_sha256')==old['sha256'],'prior decision bound to other object')
    need(type(current.get('history',[]))is list,'adoption history array')
    result=deepcopy(current)
    result.setdefault('history',[]).append({'revision':current['revision'],
        'selection':deepcopy(current['selection']),'decision_recorded':'decision'in current,
        'decision':deepcopy(prior)})
    result['selection']=deepcopy(proposed);result['decision']=deepcopy(decision)
    result['revision']+=1
    return result


def release_ready(record):
    need(hash_value(record['candidate_sha256'])and record['source_sha256']==record['candidate_sha256'],'release source identity')
    need(aggregate_checks(record['checks'],record['required_checks'])=='pass','release checks incomplete')
    need(all(x['candidate_sha256']==record['candidate_sha256']for x in record['checks']),'release uses stale checks')
    review=record['review'];need(review['state']=='pass'and review['candidate_sha256']==record['candidate_sha256'],'release review stale/missing')
    need(record['distribution_state']=='approved-scope'and record['license_state']=='selected-for-scope','release distribution or license unresolved')
    need(type(record['artifacts'])is list and record['artifacts']and len({x['path']for x in record['artifacts']})==len(record['artifacts']),'release artifacts')
    need(all(hash_value(x['sha256'])and x['source_sha256']==record['candidate_sha256']for x in record['artifacts']),'release artifact source drift')
    return True


def publication_state(intent,observation):
    need(hash_value(intent['sha256'])and text(intent['version']),'publication exact intent')
    if observation is None:return 'unknown'
    need(observation['target']==intent['target']and observation['version']==intent['version'],'publication observed wrong target/version')
    if observation['state']=='absent':return 'not-published'
    need(observation['state']=='present','publication observation state')
    need(observation['sha256']==intent['sha256'],'published different bytes')
    return 'published'


def deployment_safe(plan):
    if plan['applicability']=='not-applicable':need(text(plan['reason']),'deployment nonapplicability reason');return 'not-applicable'
    need(plan['applicability']=='applicable','deployment applicability unknown')
    need(all(type(plan[k])is bool for k in ('irreversible','backup_verified','backfill_complete'))and all(integer(plan[k])for k in ('old_writers','old_readers')),'explicit deployment facts')
    need(plan['expected_target']==plan['observed_target']and hash_value(plan['artifact_sha256']),'deployment target/artifact mismatch')
    need(plan['phase']in {'expand','backfill','switch','contract'},'migration phase')
    if plan['irreversible']:need(plan['backup_verified']and text(plan['restore_contract']),'irreversible step lacks verified restoration')
    if plan['phase']=='contract':need(plan['backfill_complete']and plan['old_writers']==0 and plan['old_readers']==0,'premature compatibility contraction')
    need(plan['previous_effect']in {'not-started','confirmed-complete'},'unreconciled prior deployment effect')
    return 'ready-in-model'


def rollback_allowed(record):
    need(all(type(record[k])is bool for k in ('old_can_write_current_data','restore_verified','restored_old_data_observed')),'rollback facts must be explicit booleans')
    if record['old_can_write_current_data']:return 'binary-rollback'
    if record['restore_verified']and record['restored_old_data_observed']:return 'binary-rollback-after-data-restore'
    if record['restore_verified']:return 'restore-data-first'
    return 'forward-fix-required'


def validate_maintenance(record):
    need(record['state']in {'active','limited','unmaintained','retired','undecided'},'maintenance state')
    need(type(record['response_hours'])in {int,type(None)}and (record['response_hours']is None or record['response_hours']>0),'response commitment')
    if record['response_hours']is not None:need(record['channel_configured']and text(record['actual_owner'])and text(record['commitment_reference']),'unbacked response commitment')
    need(type(record['channel_configured'])is bool,'channel configuration fact')
    if record['state']=='active':need(text(record['actual_owner']),'active maintenance lacks actual owner')
    need(type(record['supported_versions'])is list and len(record['supported_versions'])==len(set(record['supported_versions'])),'support versions')
    return True


def capacity_allowed(free_bytes,increment_bytes,reserve_bytes,minimum_free_bytes):
    need(all(integer(x)for x in (free_bytes,increment_bytes,reserve_bytes,minimum_free_bytes)),'capacity needs nonnegative exact integers')
    return free_bytes-increment_bytes-reserve_bytes>=minimum_free_bytes


def reclaim_plan(materials,active_ids,expected_revision,current_revision):
    need(integer(expected_revision)and integer(current_revision)and expected_revision==current_revision,'material reference revision changed')
    byid={x['id']:x for x in materials};need(len(byid)==len(materials),'duplicate material identity')
    active=required_closure(materials,active_ids);allowed=[];refused=[]
    for ident,row in sorted(byid.items()):
        need(text(row['path'])and '\x00'not in row['path'],'unsafe reclaim path')
        p=PurePosixPath(row['path']);need(bool(p.parts)and not p.is_absolute()and p.as_posix()==row['path']and all(x not in {'.','..'}for x in p.parts)and'\\'not in row['path'],'unsafe reclaim path')
        need(integer(row['bytes'])and hash_value(row['sha256']),'material content identity')
        need(type(row['holds'])is list and all(text(x)for x in row['holds'])and type(row['rebuild_inputs_available'])is bool,'material retention/rebuild facts')
        reason=None
        if ident in active:reason='active-reference'
        elif row['holds']:reason='retention-hold'
        elif row['kind']not in {'cache','temporary','dependency','reproducible-build'}:reason='required-source-delivery-or-evidence'
        elif not row['rebuild_inputs_available']or not text(row['rebuild_command']):reason='rebuild-not-established'
        if reason:refused.append({'id':ident,'reason':reason})
        else:allowed.append({'id':ident,'path':row['path'],'bytes':row['bytes'],'sha256':row['sha256']})
    return {'mode':'dry-run','reclaimable':allowed,'retained':refused,'expected_bytes':sum(x['bytes']for x in allowed),'files_deleted':0}


def dedup_plan(records,contents):
    need(type(records)is list and len({r['id']for r in records})==len(records),'dedup record identity')
    groups={};aliases=[]
    for row in records:
        data=contents[row['id']];need(integer(row['bytes'])and text(row['access_boundary'])and text(row['retention_class'])and type(data)is bytes and len(data)==row['bytes']and hashlib.sha256(data).hexdigest()==row['sha256'],'dedup actual content identity mismatch')
        key=(row['sha256'],row['bytes'],row['access_boundary'],row['retention_class'])
        if key in groups:
            need(contents[groups[key]]==data,'hash/size collision is not byte equality')
            aliases.append({'record_id':row['id'],'canonical_blob_record_id':groups[key]})
        else:groups[key]=row['id']
    return {'storage_aliases':aliases,'event_record_ids':[r['id']for r in records],'event_records_removed':0,'files_deleted':0}


def retirement_ready(record):
    need(record['operation']in {'archive','retire','delete'},'retirement operation')
    need(type(record['consumers'])is list and all(x['state']in {'migrated','not-applicable','open','unknown'}for x in record['consumers']),'consumer states')
    need(type(record['has_persistent_user_data'])is bool and type(record['recovery_verified'])is bool and type(record['retention_holds'])is list,'retirement data/recovery/retention facts')
    if any(x['state']in {'open','unknown'}for x in record['consumers']):return False
    if record['has_persistent_user_data']and record['export_state']!='verified':return False
    if record['operation']=='delete'and(record['retention_holds']or not record['recovery_verified']):return False
    return aggregate_checks(record['required_checks'],record['required_check_ids'])=='pass'
