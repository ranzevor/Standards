import copy,hashlib,unittest
from checks import governance_models as g

A='a'*64;B='b'*64;NOW='2026-10-24T00:00:00Z'


def scope():return {'revision':2,'in_scope':['offline'],'out_of_scope':['cloud'],'history':[]}
def scope_change():
    payload={'in_scope':['offline','reports'],'out_of_scope':['cloud']}
    return dict(payload,intent_id='scope-1',expected_revision=2,decision={'state':'approved','intent_sha256':g.canonical_hash(payload)})
def contract():return {'id':'T-1','input_sha256':A,'environment_sha256':B,'layer':'finite-model','expectation_origin':'requirement','expected_exit':0,'expected_value':{'writes':1,'state':'completed'}}
def event():return dict({k:v for k,v in contract().items()if k in {'id','input_sha256','environment_sha256','layer'}},completion='completed',exit_code=0,actual={'writes':1,'state':'completed'})
def change():return {'base_sha256':A,'candidate_sha256':B,'author':'author','review_units':['R1','R2'],
    'reviews':[{'candidate_sha256':B,'reviewer':'separate-review-instance','units':['R1','R2'],'state':'pass','process_evidence':'bounded actual review receipt'}],
    'findings':[{'id':'F1','blocking':True,'state':'closed','criteria':['part-1','part-2','part-3'],'closed_criteria':['part-1','part-2','part-3']}]}
def grant():return {'subject':'operator','target':'synthetic-resource','environment':'isolated','epoch':3,'state':'active','actions':['read'],
                    'not_before':'2026-10-23T00:00:00Z','expires_at':'2026-10-25T00:00:00Z'}
def operation():return {'subject':'operator','target':'synthetic-resource','environment':'isolated','epoch':3,'action':'read'}
def release():return {'candidate_sha256':B,'source_sha256':B,'checks':[{'id':'T1','state':'pass','candidate_sha256':B}],
    'required_checks':['T1'],'review':{'state':'pass','candidate_sha256':B},'distribution_state':'approved-scope','license_state':'selected-for-scope',
    'artifacts':[{'path':'dist/example','sha256':A,'source_sha256':B}]}
def deployment():return {'applicability':'applicable','expected_target':'synthetic-env','observed_target':'synthetic-env','artifact_sha256':A,
    'phase':'contract','irreversible':True,'backup_verified':True,'restore_contract':'isolated verified restore',
    'backfill_complete':True,'old_writers':0,'old_readers':0,'previous_effect':'confirmed-complete'}
def material(ident='cache',**kw):return dict({'id':ident,'path':'cache/'+ident,'kind':'cache','bytes':4,'sha256':A,'dependencies':[],
    'holds':[],'rebuild_inputs_available':True,'rebuild_command':'synthetic-build --locked'},**kw)


class ScopeAndWorkModels(unittest.TestCase):
    def test_scope_changes_preserve_before_and_support_exact_intent_replay(self):
        current=scope();result=g.apply_scope_change(current,scope_change())
        self.assertEqual(current['revision'],2);self.assertEqual(result['revision'],3)
        self.assertEqual(result['history'][0]['before']['in_scope'],['offline'])
        self.assertEqual(g.apply_scope_change(result,scope_change()),result)

    def test_scope_stale_revision_wrong_decision_and_overlap_fail(self):
        for delta in [{'expected_revision':1},{'decision':{'state':'pending','intent_sha256':A}},{'in_scope':['cloud'],'out_of_scope':['cloud']}]:
            with self.subTest(delta=delta),self.assertRaises(ValueError):g.apply_scope_change(scope(),dict(scope_change(),**delta))

    def test_explicit_approved_non_goal_change_is_legal(self):
        proposal=scope_change();proposal.update(in_scope=['cloud','offline'],out_of_scope=[])
        proposal['decision']['intent_sha256']=g.canonical_hash({'in_scope':['cloud','offline'],'out_of_scope':[]})
        result=g.apply_scope_change(scope(),proposal);self.assertEqual(result['out_of_scope'],[])
        self.assertEqual(result['history'][0]['before']['out_of_scope'],['cloud'])

    def test_same_intent_with_different_content_is_not_a_safe_retry(self):
        result=g.apply_scope_change(scope(),scope_change());proposal=scope_change();proposal['in_scope']=['offline']
        with self.assertRaisesRegex(ValueError,'conflicting'):g.apply_scope_change(result,proposal)

    def test_required_dependency_transitive_closure_missing_cycle_and_reference_neighbor(self):
        rows=[{'id':'a','dependencies':['b'],'references':['a']},{'id':'b','dependencies':['c']},{'id':'c','dependencies':[]}]
        self.assertEqual(g.required_closure(rows,['a']),{'a','b','c'})
        for changed in [rows[:-1],[dict(rows[0],dependencies=['b']),dict(rows[1],dependencies=['a'])]]:
            with self.assertRaises(ValueError):g.required_closure(changed,['a'])

    def test_verified_close_requires_exact_current_acceptance_set(self):
        item={'id':'D1','state':'verification','acceptance_ids':['T1','T2'],'history':[]}
        result=g.transition_work_item(item,'closed',resolution='verified-fix',evidence={'T1':'pass','T2':'pass'})
        self.assertEqual(result['state'],'closed');self.assertEqual(item['state'],'verification')
        for ev in [{'T1':'pass'},{'T1':'pass','T2':'not-run'}]:
            with self.assertRaises(ValueError):g.transition_work_item(item,'closed',resolution='verified-fix',evidence=ev)

    def test_research_delivery_and_nonreproducible_close_have_distinct_meanings(self):
        item={'id':'R1','state':'verification','acceptance_ids':['T1']}
        self.assertEqual(g.transition_work_item(item,'closed',resolution='verified-delivery',evidence={'T1':'pass'})['resolution'],'verified-delivery')
        rows=[{'id':'a','dependencies':[],'state':'closed','resolution':'not-reproducible'}]
        self.assertFalse(g.milestone_ready(rows,['a']))

    def test_milestone_cannot_omit_failed_transitive_dependency(self):
        rows=[{'id':'a','dependencies':['b'],'state':'closed','resolution':'verified-delivery'},{'id':'b','dependencies':[],'state':'verification'}]
        self.assertFalse(g.milestone_ready(rows,['a']));rows[1].update(state='closed',resolution='verified-fix')
        self.assertTrue(g.milestone_ready(rows,['a']))


class EvidenceAndReviewModels(unittest.TestCase):
    def test_observations_match_independent_contract_not_only_exit_zero(self):
        self.assertEqual(g.evaluate_check(contract(),event()),'pass')
        bad=event();bad['actual']['writes']=2;self.assertEqual(g.evaluate_check(contract(),bad),'fail')
        negative=contract();negative.update(expected_exit=2,expected_value={'rejected':True})
        observed=event();observed.update(exit_code=2,actual={'rejected':True})
        self.assertEqual(g.evaluate_check(negative,observed),'pass')

    def test_json_observation_type_boundary_and_legal_key_order(self):
        c=contract();observed=event()
        for expected,actual in [({'count':0},{'count':False}),({'count':1},{'count':True}),({'nested':[0]},{'nested':[0.0]})]:
            c['expected_value']=expected;observed['actual']=actual
            self.assertEqual(g.evaluate_check(c,observed),'fail')
        c['expected_value']={'count':0,'state':'ready'};observed['actual']={'state':'ready','count':0}
        self.assertEqual(g.evaluate_check(c,observed),'pass')

    def test_permission_clock_rejects_normalized_invalid_timezone(self):
        for now in ('2026-10-24T00:00:00+00:60','2026-10-24T00:00:00+24:00'):
            with self.assertRaises(ValueError):g.operation_allowed(grant(),operation(),now)

    def test_unrun_skip_timeout_and_object_drift_do_not_turn_green(self):
        self.assertEqual(g.evaluate_check(contract(),None),'not-run')
        self.assertEqual(g.evaluate_check(contract(),dict(event(),completion='skipped')),'not-run')
        self.assertEqual(g.evaluate_check(contract(),dict(event(),completion='timed-out')),'unknown')
        for key,value in [('input_sha256',B),('environment_sha256',A),('layer','product-runtime')]:
            with self.subTest(key=key),self.assertRaises(ValueError):g.evaluate_check(contract(),dict(event(),**{key:value}))

    def test_self_derived_or_nonfinite_expectation_is_rejected(self):
        for c in [dict(contract(),expectation_origin='copied-from-actual'),dict(contract(),expected_value=float('nan'))]:
            with self.assertRaises(ValueError):g.evaluate_check(c,event())

    def test_required_aggregate_keeps_unknown_missing_and_skips_distinct(self):
        self.assertEqual(g.aggregate_checks([{'id':'T1','state':'pass'}],['T1','T2']),'partial')
        self.assertEqual(g.aggregate_checks([{'id':'T1','state':'pass'},{'id':'T2','state':'unknown'}],['T1','T2']),'unknown')
        self.assertEqual(g.aggregate_checks([{'id':'T1','state':'not-applicable'}],['T1']),'not-applicable')
        with self.assertRaises(ValueError):g.aggregate_checks([{'id':'T1','state':'pass'}]*2,['T1'])

    def test_three_part_finding_cannot_close_with_only_two_parts(self):
        c=change();self.assertTrue(g.validate_change(c)['record_consistency'])
        c['findings'][0]['closed_criteria'].pop()
        with self.assertRaisesRegex(ValueError,'partly closed'):g.validate_change(c)

    def test_review_requires_current_identity_complete_coverage_and_distinct_author(self):
        for delta in [{'candidate_sha256':A},{'units':['R1']},{'reviewer':'author'}]:
            c=change();c['reviews'][0].update(delta)
            with self.subTest(delta=delta),self.assertRaises(ValueError):g.validate_change(c)
        self.assertFalse(g.validate_change(change())['independence_authenticated'])

    def test_merge_requires_actual_current_base_and_final_check_object(self):
        checks=[{'id':'T1','state':'pass','candidate_sha256':B}]
        self.assertTrue(g.merge_ready(change(),A,checks,['T1']))
        with self.assertRaisesRegex(ValueError,'HEAD'):g.merge_ready(change(),B,checks,['T1'])
        with self.assertRaisesRegex(ValueError,'other candidate'):g.merge_ready(change(),A,[dict(checks[0],candidate_sha256=A)],['T1'])


class OperationsAndConfigurationModels(unittest.TestCase):
    def test_read_scope_does_not_authorize_write_other_target_or_old_epoch(self):
        self.assertTrue(g.operation_allowed(grant(),operation(),NOW))
        for key,value in [('action','write'),('target','other'),('environment','production'),('subject','other'),('epoch',2)]:
            with self.subTest(key=key):self.assertFalse(g.operation_allowed(grant(),dict(operation(),**{key:value}),NOW))

    def test_expiry_is_exclusive_and_revoked_grant_cannot_resume(self):
        self.assertFalse(g.operation_allowed(grant(),operation(),'2026-10-25T00:00:00Z'))
        self.assertFalse(g.operation_allowed(dict(grant(),state='revoked'),operation(),NOW))
        with self.assertRaises(ValueError):g.operation_allowed(dict(grant(),epoch=True),operation(),NOW)

    def test_calendar_and_timezone_are_not_lexical_guesses(self):
        self.assertEqual(g.instant('2024-02-29T00:00:00+00:00').day,29)
        for bad in ['2026-02-29T00:00:00Z','2026-10-24','2026-10-24T00:00:00','2026-10-24T00:00:00+99:99']:
            with self.subTest(bad=bad),self.assertRaises(ValueError):g.instant(bad)

    def test_configuration_precedence_types_and_bounds(self):
        schema={'timeout':{'type':'integer','minimum':1,'maximum':60,'required':True},'telemetry':{'type':'boolean'}}
        result=g.effective_config({'timeout':30},{'timeout':20},{'timeout':10},schema)
        self.assertEqual(result,{'values':{'timeout':10},'origins':{'timeout':'command-line'}})
        for value in [True,0,61,'10']:
            with self.subTest(value=value),self.assertRaises(ValueError):g.effective_config({}, {}, {'timeout':value},schema)
        self.assertEqual(g.effective_config({'timeout':30},{},{},schema)['values']['timeout'],30)
        with self.assertRaises(ValueError):g.effective_config({'unknown':1},{},{},schema)

    def test_dependency_lock_and_observed_content_not_just_version_name(self):
        row={'id':'d','kind':'development','purpose':'offline check','source':'official synthetic source','locked_version':'1.2','resolved_version':'1.2','expected_sha256':A,'observed_sha256':A}
        self.assertTrue(g.validate_dependencies_config([row]))
        for delta in [{'observed_sha256':B},{'resolved_version':'1.3'}]:
            with self.assertRaises(ValueError):g.validate_dependencies_config([dict(row,**delta)])
        self.assertTrue(g.validate_dependencies_config([]))

    def test_exception_has_boundaries_compensation_and_real_expiry(self):
        row={'id':'E1','requirement_id':'PGN-04','scope':'synthetic local file','reason':'bounded compatibility window','document_sha256':A,'state':'approved',
             'starts_at':'2026-10-23T00:00:00Z','expires_at':'2026-10-25T00:00:00Z','review_triggered':False,'compensations':[{'state':'pass'}]}
        self.assertTrue(g.exception_valid(row,NOW))
        self.assertFalse(g.exception_valid(row,row['expires_at']))
        self.assertFalse(g.exception_valid(dict(row,review_triggered=True),NOW))
        self.assertFalse(g.exception_valid(dict(row,compensations=[{'state':'not-run'}]),NOW))

    def test_exception_unknown_trigger_is_not_false(self):
        row={'id':'E1','requirement_id':'PGN-04','scope':'synthetic local file','reason':'bounded window','document_sha256':A,'state':'approved','starts_at':'2026-10-23T00:00:00Z','expires_at':'2026-10-25T00:00:00Z','compensations':[{'state':'pass'}]}
        for value in ('',0,None,'false'):
            with self.subTest(value=value),self.assertRaises(ValueError):g.exception_valid(dict(row,review_triggered=value),NOW)
        self.assertTrue(g.exception_valid(dict(row,review_triggered=False),NOW))

    def test_upgrade_preserves_old_selection_and_rejects_stale_or_silent_change(self):
        old={'document_id':'doc','version':'0.1','path':'standards/a.md','sha256':A};new=dict(old,sha256=B)
        record={'revision':2,'selection':old,'history':[]};decision={'state':'approved','target_sha256':B}
        result=g.upgrade_adoption(record,new,decision,2);self.assertEqual(result['history'][0]['selection'],old);self.assertFalse(result['history'][0]['decision_recorded']);self.assertEqual(result['decision'],{'state':'approved','target_sha256':B});self.assertEqual(record['selection'],old)
        with self.assertRaises(ValueError):g.upgrade_adoption(record,new,decision,1)
        with self.assertRaises(ValueError):g.upgrade_adoption(record,new,dict(decision,state='pending'),2)


class ReleaseAndRecoveryModels(unittest.TestCase):
    def test_release_uses_current_checks_source_artifacts_and_distribution_scope(self):
        self.assertTrue(g.release_ready(release()))
        for key,value in [('source_sha256',A),('license_state','unselected'),('distribution_state','not-decided')]:
            with self.subTest(key=key),self.assertRaises(ValueError):g.release_ready(dict(release(),**{key:value}))
        row=release();row['checks'][0]['candidate_sha256']=A
        with self.assertRaises(ValueError):g.release_ready(row)

    def test_publication_timeout_does_not_prove_absence_or_success(self):
        intent={'target':'synthetic-local-store','version':'0.1','sha256':A}
        self.assertEqual(g.publication_state(intent,None),'unknown')
        self.assertEqual(g.publication_state(intent,{'target':intent['target'],'version':'0.1','state':'absent'}),'not-published')
        observation={'target':intent['target'],'version':'0.1','state':'present','sha256':A}
        self.assertEqual(g.publication_state(intent,observation),'published')
        with self.assertRaises(ValueError):g.publication_state(intent,dict(observation,sha256=B))

    def test_migration_contraction_waits_for_old_readers_writers_and_backfill(self):
        self.assertEqual(g.deployment_safe(deployment()),'ready-in-model')
        for delta in [{'old_writers':1},{'old_readers':1},{'backfill_complete':False},{'previous_effect':'unknown'},{'backup_verified':False},{'backup_verified':'false'}]:
            with self.subTest(delta=delta),self.assertRaises(ValueError):g.deployment_safe(dict(deployment(),**delta))
        self.assertEqual(g.deployment_safe({'applicability':'not-applicable','reason':'documents only; no runtime target'}),'not-applicable')

    def test_backup_exists_does_not_make_binary_rollback_safe(self):
        row={'old_can_write_current_data':False,'restore_verified':True,'restored_old_data_observed':False}
        self.assertEqual(g.rollback_allowed(row),'restore-data-first')
        self.assertEqual(g.rollback_allowed(dict(row,restored_old_data_observed=True)),'binary-rollback-after-data-restore')
        self.assertEqual(g.rollback_allowed(dict(row,restore_verified=False)),'forward-fix-required')
        self.assertEqual(g.rollback_allowed(dict(row,old_can_write_current_data=True)),'binary-rollback')

    def test_support_commitment_is_not_a_template_owner(self):
        row={'state':'undecided','response_hours':None,'channel_configured':False,'actual_owner':None,'commitment_reference':None,'supported_versions':[]}
        self.assertTrue(g.validate_maintenance(row))
        with self.assertRaises(ValueError):g.validate_maintenance(dict(row,response_hours=24))
        with self.assertRaises(ValueError):g.validate_maintenance(dict(row,state='active'))
        self.assertTrue(g.validate_maintenance(dict(row,state='active',actual_owner='synthetic-owner')))


class MaterialAndRetirementModels(unittest.TestCase):
    def test_capacity_exact_boundary_and_boolean_are_not_numbers(self):
        self.assertTrue(g.capacity_allowed(120,10,10,100));self.assertFalse(g.capacity_allowed(119,10,10,100))
        for value in [True,-1,1.0]:
            with self.assertRaises(ValueError):g.capacity_allowed(value,0,0,0)

    def test_reclaim_checks_transitive_active_references_and_never_deletes(self):
        rows=[material('root',kind='source',dependencies=['cache']),material('cache'),material('idle')]
        result=g.reclaim_plan(rows,['root'],4,4)
        self.assertEqual([x['id']for x in result['reclaimable']],['idle'])
        self.assertEqual(result['files_deleted'],0);self.assertEqual(result['expected_bytes'],4)

    def test_required_sources_formal_outputs_and_irreplaceable_failures_are_retained(self):
        for kind in ['source','formal-document','formal-delivery','irreplaceable-evidence']:
            with self.subTest(kind=kind):self.assertFalse(g.reclaim_plan([material(kind,kind=kind)],[],1,1)['reclaimable'])
        self.assertFalse(g.reclaim_plan([material(holds=['investigation'])],[],1,1)['reclaimable'])
        self.assertFalse(g.reclaim_plan([material(rebuild_inputs_available=False)],[],1,1)['reclaimable'])

    def test_reclaim_rejects_stale_scan_path_escape_and_forged_boolean(self):
        for rows,expected,current in [([material()],1,2),([material(path='../evidence')],1,1),([material(rebuild_inputs_available='true')],1,1)]:
            with self.assertRaises(ValueError):g.reclaim_plan(rows,[],expected,current)

    def test_reclaim_never_designates_the_directory_root_as_a_cache_entry(self):
        for path in ('.','','./','cache/..','cache/./item','cache\x00item'):
            with self.subTest(path=path),self.assertRaises(ValueError):g.reclaim_plan([material(path=path)],[],1,1)
        result=g.reclaim_plan([material(path='cache/item')],[],1,1)
        self.assertEqual(result['reclaimable'][0]['path'],'cache/item')
        self.assertEqual(result['files_deleted'],0)

    def test_identical_log_bytes_can_share_storage_not_event_identity(self):
        data=b'same failure';sha=hashlib.sha256(data).hexdigest()
        rows=[{'id':x,'sha256':sha,'bytes':len(data),'access_boundary':'private','retention_class':'hold'}for x in ['run1','run2']]
        result=g.dedup_plan(rows,{'run1':data,'run2':data})
        self.assertEqual(len(result['storage_aliases']),1);self.assertEqual(result['event_record_ids'],['run1','run2']);self.assertEqual(result['event_records_removed'],0)
        rows[1]['access_boundary']='other'
        self.assertFalse(g.dedup_plan(rows,{'run1':data,'run2':data})['storage_aliases'])
        with self.assertRaises(ValueError):g.dedup_plan(rows,{'run1':data,'run2':b'other'})

    def test_archive_is_not_delete_and_unresolved_consumers_block_completion(self):
        row={'operation':'archive','consumers':[],'has_persistent_user_data':False,'export_state':'not-applicable','retention_holds':['audit'],
             'recovery_verified':False,'required_checks':[{'id':'R1','state':'pass'}],'required_check_ids':['R1']}
        self.assertTrue(g.retirement_ready(row));self.assertFalse(g.retirement_ready(dict(row,operation='delete')))
        self.assertFalse(g.retirement_ready(dict(row,consumers=[{'state':'unknown'}])))
        self.assertFalse(g.retirement_ready(dict(row,has_persistent_user_data=True,export_state='not-run')))
        self.assertFalse(g.retirement_ready(dict(row,required_checks=[])))


if __name__=='__main__':unittest.main()
