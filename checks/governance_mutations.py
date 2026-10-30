"""Actual finite-model mutations with executed assertion failures, not import-error kills."""
import sys
if sys.flags.optimize:raise RuntimeError('Mutation verification requires normal Python mode; do not use -O or -OO')
from pathlib import Path
import argparse,ast,datetime,hashlib,json,os,re,shutil,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

VARIANTS=[
 ('json-types',"json_equal(event['actual'],contract['expected_value'])","event['actual']==contract['expected_value']",'test_json_observation_type_boundary_and_legal_key_order'),
 ('scope-cas',"need(current['revision']==change['expected_revision'],'stale scope revision')","need(True,'stale scope revision')",'test_scope_stale_revision_wrong_decision_and_overlap_fail'),
 ('intent-replay',"len(matches)==1 and matches[0]['intent_sha256']==intent","True",'test_same_intent_with_different_content_is_not_a_safe_retry'),
 ('close-all-criteria','set(evidence)==required','set(evidence)<=required','test_verified_close_requires_exact_current_acceptance_set'),
 ('dependency-closure',"for dep in sorted(unique(byid[ident]['dependencies'],'dependencies')):visit(dep)","for dep in []:visit(dep)",'test_required_dependency_transitive_closure_missing_cycle_and_reference_neighbor'),
 ('unknown-check',"if 'unknown'in states:return 'unknown'","if 'unknown'in states:return 'pass'",'test_required_aggregate_keeps_unknown_missing_and_skips_distinct'),
 ('timeout-check',"if event['completion']=='timed-out':return 'unknown'","if event['completion']=='timed-out':return 'pass'",'test_unrun_skip_timeout_and_object_drift_do_not_turn_green'),
 ('independent-author',"row['reviewer']!=change['author']","True",'test_review_requires_current_identity_complete_coverage_and_distinct_author'),
 ('finding-all-parts',"if row['state']=='closed':need(required and closed==required,'partly closed finding or empty closure')\n        if row['blocking']:need(row['state']=='closed'and required and closed==required,'open or partly closed blocking finding')","if row['state']=='closed':need(required and closed<=required,'partly closed finding or empty closure')\n        if row['blocking']:need(row['state']=='closed'and required and closed<=required,'open or partly closed blocking finding')",'test_three_part_finding_cannot_close_with_only_two_parts'),
 ('epoch-boundary',"all(grant[k]==operation[k]for k in ('subject','target','environment','epoch'))","all(grant[k]==operation[k]for k in ('subject','target','environment'))",'test_read_scope_does_not_authorize_write_other_target_or_old_epoch'),
 ('expiry-boundary',"moment<instant(grant['expires_at'])","moment<=instant(grant['expires_at'])",'test_expiry_is_exclusive_and_revoked_grant_cannot_resume'),
 ('config-precedence',"[('default',defaults),('environment',environment),('command-line',command_line)]","[('default',defaults),('command-line',command_line),('environment',environment)]",'test_configuration_precedence_types_and_bounds'),
 ('dependency-digest',"row['observed_sha256']==row['expected_sha256']","True",'test_dependency_lock_and_observed_content_not_just_version_name'),
 ('unknown-publication',"if observation is None:return 'unknown'","if observation is None:return 'not-published'",'test_publication_timeout_does_not_prove_absence_or_success'),
 ('migration-old-writer',"plan['backfill_complete']and plan['old_writers']==0 and plan['old_readers']==0","plan['backfill_complete']and plan['old_readers']==0",'test_migration_contraction_waits_for_old_readers_writers_and_backfill'),
 ('restore-observed',"record['restore_verified']and record['restored_old_data_observed']","record['restore_verified']",'test_backup_exists_does_not_make_binary_rollback_safe'),
 ('space-reserve','free_bytes-increment_bytes-reserve_bytes>=minimum_free_bytes','free_bytes-increment_bytes>=minimum_free_bytes','test_capacity_exact_boundary_and_boolean_are_not_numbers'),
 ('root-reclaim','bool(p.parts)and not p.is_absolute()','not p.is_absolute()','test_reclaim_never_designates_the_directory_root_as_a_cache_entry'),
 ('retention-hold',"elif row['holds']:reason='retention-hold'","elif False:reason='retention-hold'",'test_required_sources_formal_outputs_and_irreplaceable_failures_are_retained'),
 ('dedup-access',"(row['sha256'],row['bytes'],row['access_boundary'],row['retention_class'])","(row['sha256'],row['bytes'],'same-boundary',row['retention_class'])",'test_identical_log_bytes_can_share_storage_not_event_identity'),
 ('retirement-checks',"return aggregate_checks(record['required_checks'],record['required_check_ids'])=='pass'","return True",'test_archive_is_not_delete_and_unresolved_consumers_block_completion'),
]


def classify(exit_code,output,legal=False):
    counts=re.findall(r'^Ran (\d+) tests? in ',output,re.M)
    if not counts or int(counts[-1])<1 or re.search(r'\b(?:ImportError|ModuleNotFoundError|SyntaxError)\b',output):return 'invalid-run'
    if re.search(r'^ERROR:',output,re.M)or re.search(r'\bskipped=[1-9]',output):return 'invalid-run'
    if legal:return 'accepted'if exit_code==0 and re.search(r'^OK\s*$',output,re.M)else'invalid-run'
    return 'killed-by-assertion'if exit_code!=0 and re.search(r'^FAIL:',output,re.M)and re.search(r'^FAILED \(failures=[1-9]',output,re.M)else'survived-or-invalid'


def run(root=ROOT,evidence_parent=None,min_free_bytes=0):
    root=Path(root).resolve();parent=Path(evidence_parent).resolve()if evidence_parent else Path(tempfile.gettempdir())
    if not parent.is_dir()or parent.is_relative_to(root):raise ValueError('existing evidence parent outside source is required')
    if type(min_free_bytes)is not int or min_free_bytes<0:raise ValueError('nonnegative exact minimum free bytes required')
    if shutil.disk_usage(parent).free-16*1024**2<min_free_bytes:raise ValueError('insufficient free-space reserve before mutation fixtures')
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ');evidence=parent/('governance-mutations-'+stamp);evidence.mkdir()
    source=(root/'checks/governance_models.py').read_text();hash_of=lambda raw:hashlib.sha256(raw).hexdigest();rows=[]
    with tempfile.TemporaryDirectory(prefix='StandardsGovernanceMutation-')as temporary:
        fixture=Path(temporary);(fixture/'checks').mkdir();(fixture/'tests').mkdir();(fixture/'checks/__init__.py').write_text('');(fixture/'tests/__init__.py').write_text('')
        for name in ('finite_schema.py','validation_common.py'):shutil.copyfile(root/'checks'/name,fixture/'checks'/name)
        shutil.copyfile(root/'tests/test_governance_models.py',fixture/'tests/test_governance_models.py')
        variants=[('baseline',source,None,True)]
        for ident,before,after,target in VARIANTS:
            if source.count(before)!=1:raise ValueError('mutation must match one actual semantic guard: '+ident)
            variants.append((ident,source.replace(before,after,1),target,False))
        variants.append(('legal-comment',source+'\n# Equivalent formatting and presentation comment.\n',None,True))
        for ident,mutant,target,legal in variants:
            ast.parse(mutant);(fixture/'checks/governance_models.py').write_text(mutant)
            argv=[sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_governance_models.py','-v']
            if target:argv+=['-k',target]
            started=datetime.datetime.now(datetime.timezone.utc).isoformat()
            completed=subprocess.run(argv,cwd=fixture,env={**os.environ,'PYTHONPATH':str(fixture),'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=30)
            output=completed.stdout+'\n'+completed.stderr;directory=evidence/ident;directory.mkdir();raw=output.encode();(directory/'output.log').write_bytes(raw)
            if ident!='baseline':(directory/'governance_models.py').write_text(mutant)
            result=classify(completed.returncode,output,legal);expected='accepted'if legal else'killed-by-assertion'
            rows.append({'id':ident,'command':argv,'started_at':started,'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha256':hash_of(source.encode()),'mutant_sha256':hash_of(mutant.encode()),'target_test':target,'legal_neighbor':legal,'expected':expected,'actual':result,'exit_code':completed.returncode,'tests_executed':int(re.findall(r'^Ran (\d+) tests? in ',output,re.M)[-1])if re.findall(r'^Ran (\d+) tests? in ',output,re.M)else 0,'raw_output':str(directory/'output.log'),'raw_sha256':hash_of(raw)})
            with (evidence/'results.json').open('w')as f:json.dump(rows,f,ensure_ascii=False,indent=2);f.write('\n')
            if result!=expected:raise ValueError('mutation outcome was not a valid semantic observation: '+ident+'; evidence='+str(evidence))
    return {'semantic_mutants_killed':len(VARIANTS),'baseline_methods':rows[0]['tests_executed'],'legal_code_neighbors_accepted':1,'evidence':str(evidence),'real_system_acceptance':'not-run','scope':'finite governance-model guards only; no source repository or external resource changed'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--evidence-parent',type=Path);p.add_argument('--min-free-bytes',type=int,default=0);a=p.parse_args()
    print(json.dumps(run(a.root,a.evidence_parent,a.min_free_bytes),ensure_ascii=False,sort_keys=True))
