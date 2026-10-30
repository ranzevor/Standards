import sys,pathlib,unittest,tempfile,copy,io,zipfile,stat,concurrent.futures,threading,json,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from checks.ai_agent_model import *
from checks.ai_evidence_gate import Evidence,decide,raw_success_fraction,zero_failure_upper

class BudgetTests(unittest.TestCase):
    def test_exact_limit(self):
        b=Budget(10);b.reserve('one',10);self.assertEqual(b.reserved,10)
    def test_over_limit(self):
        b=Budget(10)
        with self.assertRaises(PermissionError):b.reserve('one',11)
    def test_bool_not_money(self):
        with self.assertRaises(ValueError):Budget(True)
    def test_negative_not_money(self):
        with self.assertRaises(ValueError):Budget(-1)
    def test_unknown_not_released(self):
        b=Budget(10);b.reserve('one',10);b.unknown('one');self.assertEqual(b.reserved,10)
        with self.assertRaises(PermissionError):b.reserve('two',1)
    def test_release_requires_authority(self):
        b=Budget(10);b.reserve('one',10)
        with self.assertRaises(PermissionError):b.release('one','timeout')
    def test_authoritative_not_started_release(self):
        b=Budget(10);b.reserve('one',10);self.assertTrue(b.release('one','authoritative-not-started'));self.assertFalse(b.release('one','authoritative-not-started'));self.assertEqual(b.reserved,0)
    def test_settlement_idempotent(self):
        b=Budget(10);b.reserve('one',10);self.assertTrue(b.settle('one',7,'r1'));self.assertFalse(b.settle('one',7,'r1'));self.assertEqual((b.used,b.reserved),(7,0))
    def test_conflicting_settlement_rejected(self):
        b=Budget(10);b.reserve('one',10);b.settle('one',7,'r1')
        with self.assertRaises(ValueError):b.settle('one',8,'r2')
    def test_reservation_id_cannot_change_bound(self):
        b=Budget(10);b.reserve('one',5)
        with self.assertRaises(ValueError):b.reserve('one',4)
    def test_snapshot_keeps_root_usage_and_unknown(self):
        b=Budget(10);b.reserve('one',5);b.settle('one',3,'r');b.reserve('two',7);b.unknown('two');r=Budget.restore(b.snapshot());self.assertEqual((r.used,r.reserved,r.limit),(3,7,10))
        with self.assertRaises(PermissionError):r.reserve('new-run',1)
    def test_target_overrun_is_reported_not_hidden(self):
        b=Budget(10);b.reserve('one',5);b.settle('one',6,'breach');self.assertEqual(b.used,6);self.assertEqual(len(b.breaches),1)
    def test_concurrent_last_budget(self):
        b=Budget(5);barrier=threading.Barrier(2)
        def attempt(key):
            barrier.wait()
            try:b.reserve(key,5);return True
            except PermissionError:return False
        with concurrent.futures.ThreadPoolExecutor(2)as pool:r=list(pool.map(attempt,['a','b']))
        self.assertEqual(sum(r),1);self.assertEqual(b.reserved,5)
    def test_settled_cost_cannot_be_erased(self):
        b=Budget(5);b.reserve('one',5);b.settle('one',3,'r')
        with self.assertRaises(ValueError):b.release('one','authoritative-not-started')

class AuthorizationTargetTests(unittest.TestCase):
    def setUp(self):self.a=Authority();self.g=self.a.grant('u','t1','write','order1');self.t=Target(self.a);self.p={'amount':100,'currency':'CNY'}
    def test_authorized_effect(self):self.assertEqual(self.t.accept(self.g,'op',self.p,1,1)['effect_count'],1)
    def test_same_operation_recovery(self):
        first=self.t.accept(self.g,'op',self.p,1,1);second=self.t.accept(self.g,'op',self.p,1,1);self.assertEqual(first,second);self.assertEqual(self.t.effects,1)
    def test_same_operation_changed_amount(self):
        self.t.accept(self.g,'op',self.p,1,1)
        with self.assertRaises(ValueError):self.t.accept(self.g,'op',{'amount':101},1,1)
    def test_revoke_after_prepare(self):
        self.a.revoke('u','t1','write','order1')
        with self.assertRaises(PermissionError):self.t.accept(self.g,'op',self.p,1,1)
        self.assertEqual(self.t.effects,0)
    def test_renewal_does_not_revalidate_old_grant(self):
        self.a.grant('u','t1','write','order1')
        with self.assertRaises(PermissionError):self.t.accept(self.g,'op',self.p,1,1)
    def test_expired_grant(self):
        with self.assertRaises(PermissionError):self.t.accept(self.g,'op',self.p,1,1,now=100)
    def test_wrong_tenant(self):
        g=self.a.grant('u','t2','write','order1')
        with self.assertRaises(PermissionError):self.t.accept(g,'op',self.p,1,1)
    def test_wrong_method(self):
        g=self.a.grant('u','t1','read','order1')
        with self.assertRaises(PermissionError):self.t.accept(g,'op',self.p,1,1)
    def test_wrong_object(self):
        g=self.a.grant('u','t1','write','order2')
        with self.assertRaises(PermissionError):self.t.accept(g,'op',self.p,1,1)
    def test_stale_target_epoch(self):
        self.t.epoch=2
        with self.assertRaises(PermissionError):self.t.accept(self.g,'op',self.p,1,1)
    def test_current_epoch_neighbor(self):
        self.t.epoch=2;self.assertEqual(self.t.accept(self.g,'op',self.p,2,1)['effect_count'],1)
    def test_object_cas(self):
        self.t.accept(self.g,'one',self.p,1,1)
        with self.assertRaises(ValueError):self.t.accept(self.g,'two',self.p,1,1)
    def test_timeout_unknown_is_not_absent(self):self.assertEqual(self.t.query('not-visible')['status'],'unknown')
    def test_final_not_started_neighbor(self):self.assertEqual(self.t.query('not-visible',final=True)['status'],'not-started')
    def test_ack_lost_reconciliation_no_repeat(self):
        self.t.accept(self.g,'op',self.p,1,1);self.assertEqual(self.t.query('op')['status'],'confirmed');self.assertEqual(self.t.effects,1)
    def test_approval_binding(self):
        b=ApprovalBook();b.issue('ticket',self.g,'op',self.p,100);self.assertEqual(b.claim('ticket',self.g,'op',self.p,0),'claimed');self.assertEqual(b.claim('ticket',self.g,'op',self.p,0),'same-operation-recovery')
    def test_approval_changed_parameters(self):
        b=ApprovalBook();b.issue('ticket',self.g,'op',self.p,100)
        with self.assertRaises(PermissionError):b.claim('ticket',self.g,'op',{'amount':100,'currency':'USD'},0)
    def test_approval_new_operation_replay(self):
        b=ApprovalBook();b.issue('ticket',self.g,'op',self.p,100);b.claim('ticket',self.g,'op',self.p,0)
        with self.assertRaises(PermissionError):b.claim('ticket',self.g,'op2',self.p,0)
    def test_concurrent_approval_has_one_first_claim(self):
        b=ApprovalBook();b.issue('ticket',self.g,'op',self.p,100)
        with concurrent.futures.ThreadPoolExecutor(2)as pool:r=list(pool.map(lambda _:b.claim('ticket',self.g,'op',self.p,0),range(2)))
        self.assertEqual(r.count('claimed'),1)

class ControllerTests(unittest.TestCase):
    def setUp(self):self.c=Controller();self.c.required={'op'};self.a=Authority();self.g=self.a.grant('u','t1','write','order1');self.t=Target(self.a);self.r=self.t.accept(self.g,'op',{'x':1},1,1)
    def event(self,**kwargs):return Event(**dict(task='root',attempt='a1',epoch=1,plan=1,status='confirmed',operation='op',receipt=self.r,**kwargs))
    def test_current_result_accepted(self):self.assertEqual(self.c.admit(self.event(),self.t),'accepted')
    def test_fake_model_receipt_rejected(self):
        e=self.event();e.receipt={'operation':'op','effect_count':99}
        with self.assertRaises(ValueError):self.c.admit(e,self.t)
    def test_no_target_authority_rejected(self):
        with self.assertRaises(ValueError):self.c.admit(self.event())
    def test_old_attempt_current_epoch_rejected(self):
        self.c.attempt='a2';self.assertEqual(self.c.admit(self.event(),self.t),'historical-only');self.assertEqual(self.c.results,{})
    def test_old_epoch_rejected(self):
        self.c.epoch=2;self.assertEqual(self.c.admit(self.event(),self.t),'historical-only')
    def test_old_plan_rejected(self):
        self.c.plan=2;self.assertEqual(self.c.admit(self.event(),self.t),'historical-only')
    def test_wrong_task_rejected(self):
        e=self.event();e.task='other';self.assertEqual(self.c.admit(e,self.t),'historical-only')
    def test_cancel_does_not_undo_target(self):
        self.c.cancel();self.assertEqual(self.t.effects,1);self.assertEqual(self.c.admit(self.event(),self.t),'historical-only');self.assertEqual(self.c.status,'cancelled')
    def test_join_requires_receipt(self):
        with self.assertRaises(ValueError):self.c.succeed()
    def test_join_tracks_unknown_child(self):
        self.c.admit(self.event(),self.t);self.c.children={'b':'unknown'}
        with self.assertRaises(ValueError):self.c.succeed()
    def test_join_legal_done_children(self):
        self.c.admit(self.event(),self.t);self.c.children={'b':'completed'};self.c.succeed();self.assertEqual(self.c.status,'succeeded')
    def test_cancelled_snapshot_cannot_revive(self):
        old=self.c.snapshot();self.c.cancel();r=Controller.restore(old,self.c.snapshot());self.assertEqual(r.status,'cancelled');self.assertEqual(r.epoch,2)
    def test_handoff_only_one_epoch(self):
        self.assertEqual(self.c.handoff(1,'a2'),2)
        with self.assertRaises(ValueError):self.c.handoff(1,'a3')
    def test_old_event_audit_fact_preserved(self):
        self.c.handoff(1,'a2');self.c.admit(self.event(),self.t);self.assertEqual(len(self.c.audit),1);self.assertEqual(self.c.results,{})

class CheckpointTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.s=Checkpoints(self.tmp.name)
    def test_commit_and_restart(self):
        self.s.commit('c1',{'decision':'accepted'},{});self.assertEqual(Checkpoints(self.tmp.name).load()['snapshot']['decision'],'accepted')
    def test_same_commit_ack_lost(self):
        a=self.s.commit('c1',{'x':1},{});b=self.s.commit('c1',{'x':1},{});self.assertEqual(a,b)
    def test_same_commit_different_snapshot(self):
        self.s.commit('c1',{'x':1},{})
        with self.assertRaises(ValueError):self.s.commit('c1',{'x':2},{})
    def test_pointer_cas(self):
        self.s.commit('c1',{},{});self.s.commit('c2',{'x':1},{},expected='c1')
        with self.assertRaises(ValueError):self.s.commit('c3',{}, {},expected='c1')
    def test_missing_reference(self):
        with self.assertRaises(ValueError):self.s.commit('c1',{}, {'missing':'abc'})
    def test_durable_reference_neighbor(self):
        q=pathlib.Path(self.tmp.name)/'blob';q.write_bytes(b'accepted');h=hashlib.sha256(q.read_bytes()).hexdigest();self.s.commit('c1',{}, {'blob':h});self.assertEqual(self.s.load()['refs']['blob'],h)
    def test_reference_lost_after_commit(self):
        q=pathlib.Path(self.tmp.name)/'blob';q.write_bytes(b'accepted');h=hashlib.sha256(q.read_bytes()).hexdigest();self.s.commit('c1',{}, {'blob':h});q.unlink()
        with self.assertRaises(ValueError):self.s.load()
    def test_snapshot_tamper(self):
        self.s.commit('c1',{'approve':False},{});p=pathlib.Path(self.tmp.name)/'current.json';r=json.loads(p.read_text());r['snapshot']['approve']=True;p.write_text(json.dumps(r))
        with self.assertRaises(ValueError):self.s.load()
    def test_reference_traversal(self):
        with self.assertRaises(ValueError):self.s.commit('c1',{}, {'../elsewhere':'a'})
    def test_commit_id_path(self):
        with self.assertRaises(ValueError):self.s.commit('../c1',{}, {})

class MemoryTests(unittest.TestCase):
    def setUp(self):self.s=MemoryIndex();self.s.allow('u','t1');self.m=Memory('t1','u','address',1,'source-v1','preference',{'address':'A'},100);self.k=self.s.put(self.m,principal='u')
    def test_owner_read(self):self.assertEqual(self.s.emit('u','t1')[0].content,{'address':'A'})
    def test_unallowed_tenant(self):
        with self.assertRaises(PermissionError):self.s.emit('u','t2')
    def test_other_owner_same_tenant_not_visible(self):
        self.s.allow('v','t1');self.assertEqual(self.s.emit('v','t1'),[])
    def test_write_requires_owner(self):
        with self.assertRaises(PermissionError):self.s.put(Memory('t1','u','another',1,'s','inference','x',100),principal='v')
    def test_cas_update_conflict(self):
        changed=copy.deepcopy(self.m);changed.version=2
        with self.assertRaises(ValueError):self.s.put(changed,expected=0,principal='u')
    def test_cas_update_neighbor(self):
        changed=copy.deepcopy(self.m);changed.version=2;changed.content={'address':'B'};self.s.put(changed,expected=1,principal='u');self.assertEqual(self.s.emit('u','t1')[0].content,{'address':'B'})
    def test_read_time_expiry(self):self.assertEqual(self.s.emit('u','t1',now=100),[])
    def test_revoke_before_emit(self):
        with self.assertRaises(PermissionError):self.s.emit('u','t1',before_emit=lambda:self.s.revoke('u','t1'))
    def test_delete_during_query(self):self.assertEqual(self.s.emit('u','t1',before_emit=lambda:self.s.delete(self.k,principal='u')),[])
    def test_old_snapshot_cannot_resurrect(self):
        old=copy.deepcopy(self.m);self.s.delete(self.k,principal='u');self.s.restore_rows([old]);self.assertEqual(self.s.emit('u','t1'),[])
    def test_old_writer_cannot_erase_tombstone(self):
        self.s.delete(self.k,principal='u')
        with self.assertRaises(ValueError):self.s.put(self.m,principal='u')
    def test_delete_other_owner_rejected(self):
        self.s.allow('v','t1')
        with self.assertRaises(PermissionError):self.s.delete(self.k,principal='v')
    def test_inference_not_approval_type(self):
        m=copy.deepcopy(self.m);m.key='claim';m.fact_type='user-approved'
        with self.assertRaises(ValueError):self.s.put(m,principal='u')
    def test_update_after_read_drops_stale_copy(self):
        def change():
            m=copy.deepcopy(self.m);m.version=2;m.content={'address':'B'};self.s.put(m,expected=1,principal='u')
        self.assertEqual(self.s.emit('u','t1',before_emit=change),[])

class ContextClaimVersionTests(unittest.TestCase):
    def envelope(self):return {'principal':'u','tenant':'t1','goal':'draft','denials':['do not send'],'sources':['s@1'],'unknown_operations':['op'],'accepted_decisions':['d1'],'root_budget':{'used':3,'reserved':7},'trust':{'s':'untrusted'},'old_debug':'large log'}
    def test_compression_semantic_positive(self):
        a=self.envelope();b=copy.deepcopy(a);b.pop('old_debug');self.assertTrue(verify_compression(a,b))
    def test_compression_loses_deny(self):
        a=self.envelope();b=copy.deepcopy(a);b['denials']=[]
        with self.assertRaises(ValueError):verify_compression(a,b)
    def test_compression_upgrades_source(self):
        a=self.envelope();b=copy.deepcopy(a);b['trust']['s']='system'
        with self.assertRaises(ValueError):verify_compression(a,b)
    def test_compression_unknown_to_done(self):
        a=self.envelope();b=copy.deepcopy(a);b['unknown_operations']=[]
        with self.assertRaises(ValueError):verify_compression(a,b)
    def test_claim_dependency_invalidation(self):
        c=Claims();c.record('answer',{'source':'v1'},'model');self.assertEqual(c.invalidate('source','v2'),['answer'])
        with self.assertRaises(ValueError):c.require('answer','model')
    def test_claim_transitive_invalidation(self):
        c=Claims();c.record('a',{'source':'v1'},'model');c.record('b',{'claim:a':'fresh'},'model');self.assertEqual(set(c.invalidate('source','v2')),{'a','b'})
    def test_unchanged_claim_neighbor(self):
        c=Claims();c.record('a',{'source':'v1'},'model');self.assertEqual(c.invalidate('source','v1'),[]);self.assertTrue(c.require('a','model'))
    def test_model_layer_not_real_business(self):
        c=Claims();c.record('a',{'source':'v1'},'model')
        with self.assertRaises(ValueError):c.require('a','business')
    def test_joint_version_changed_tool(self):self.assertFalse(release_compatible({'model':'A','tool':'draft'},{'model':'A','tool':'send'},['model','tool']))
    def test_absent_component_neighbor(self):self.assertTrue(release_compatible({'model':'A'},{'model':'A','unused':'x'},['model']))

class MCPTests(unittest.TestCase):
    def test_missing_result_type_legacy_complete(self):self.assertEqual(mcp_result_type({'content':[]}), 'complete')
    def test_unknown_result_type_rejected(self):
        with self.assertRaises(ValueError):mcp_result_type({'resultType':'new-kind'})
    def test_declared_extension_neighbor(self):self.assertEqual(mcp_result_type({'resultType':'task'},['task']),'task')
    def test_input_required_not_complete(self):self.assertEqual(mcp_result_type({'resultType':'input_required'}),'input_required')
    def test_rpc_id_valid(self):self.assertEqual(rpc_id(0),0);self.assertEqual(rpc_id('r1'),'r1')
    def test_rpc_id_null_bool_float_invalid(self):
        for v in(None,True,1.5):
            with self.subTest(v=v),self.assertRaises(ValueError):rpc_id(v)
    def initial(self):return {'id':1,'operation_id':'payment1','method':'tools/call','arguments':{'amount':100}}
    def retry(self):r=self.initial();r['id']=2;r['requestState']='opaque';return r
    def test_mrtr_new_rpc_same_intent(self):self.assertTrue(mrtr_retry(self.initial(),self.retry(),'opaque'))
    def test_mrtr_same_rpc_invalid(self):
        r=self.retry();r['id']=1
        with self.assertRaises(ValueError):mrtr_retry(self.initial(),r,'opaque')
    def test_mrtr_new_intent_invalid(self):
        r=self.retry();r['operation_id']='payment2'
        with self.assertRaises(ValueError):mrtr_retry(self.initial(),r,'opaque')
    def test_mrtr_opaque_cannot_be_modified(self):
        r=self.retry();r['requestState']='parsed-and-rebuilt'
        with self.assertRaises(ValueError):mrtr_retry(self.initial(),r,'opaque')
    def test_request_state_tamper_rejected(self):
        s=RequestState(b'test-key');token=s.issue('u','pay',{'amount':100},100,'nonce')
        with self.assertRaises(PermissionError):s.consume(token.replace('100','200'),'u','pay',{'amount':100},'op')
    def test_request_state_binding_and_recovery(self):
        s=RequestState(b'test-key');token=s.issue('u','pay',{'amount':100},100,'nonce');self.assertEqual(s.consume(token,'u','pay',{'amount':100},'op'),'consumed');self.assertEqual(s.consume(token,'u','pay',{'amount':100},'op'),'same-operation-recovery')
        with self.assertRaises(PermissionError):s.consume(token,'u','pay',{'amount':100},'different-op')
    def test_request_state_wrong_principal(self):
        s=RequestState(b'test-key');token=s.issue('u','pay',{},100,'nonce')
        with self.assertRaises(PermissionError):s.consume(token,'v','pay',{},'op')
    def test_request_state_expiry(self):
        s=RequestState(b'test-key');token=s.issue('u','pay',{},100,'nonce')
        with self.assertRaises(PermissionError):s.consume(token,'u','pay',{},'op',100)
    def tools(self):return [{'name':'bad','parameters':[{'type':'string','x-mcp-header':'bad\r\nfield'}]},{'name':'good','parameters':[{'type':'string','x-mcp-header':'Region'}]}]
    def test_illegal_header_only_rejects_bad_tool(self):
        good,bad=header_tools(self.tools());self.assertEqual([x['name']for x in good],['good']);self.assertEqual(set(bad),{'bad'})
    def test_stdio_can_ignore_header_annotation(self):self.assertEqual(len(header_tools(self.tools(),'stdio')[0]),2)
    def test_float_header_type_invalid(self):
        good,bad=header_tools([{'name':'float','parameters':[{'type':'number','x-mcp-header':'Value'}]}]);self.assertEqual(good,[])
    def test_duplicate_header_case_invalid(self):
        good,bad=header_tools([{'name':'dup','parameters':[{'type':'string','x-mcp-header':'X'},{'type':'string','x-mcp-header':'x'}]}]);self.assertEqual(good,[])
    def test_safe_integer_boundary(self):
        good,bad=header_tools([{'name':'i','parameters':[{'type':'integer','x-mcp-header':'N','value':2**53-1}]}]);self.assertEqual(len(good),1)
    def test_unsafe_integer_invalid(self):
        good,bad=header_tools([{'name':'i','parameters':[{'type':'integer','x-mcp-header':'N','value':2**53}]}]);self.assertEqual(good,[])
    def test_cancellation_by_binding(self):self.assertEqual(cancellation_signal('2026-07-28','http'),'close-request-stream');self.assertEqual(cancellation_signal('2026-07-28','stdio'),'notifications/cancelled')

class A2ATests(unittest.TestCase):
    def key(self):return RemoteKey('svc','https://agent.invalid','u','route','task','context')
    def test_expected_remote_key(self):self.assertEqual(accept_remote(self.key(),self.key()),'accepted')
    def test_same_task_other_service_rejected(self):
        a=self.key();b=RemoteKey('evil',a.interface,a.principal,a.tenant,a.task,a.context)
        with self.assertRaises(PermissionError):accept_remote(a,b)
    def test_same_url_other_route_rejected(self):
        a=self.key();b=RemoteKey(a.service,a.interface,a.principal,'other-route',a.task,a.context)
        with self.assertRaises(PermissionError):accept_remote(a,b)
    def test_late_event_terminal_historical(self):self.assertEqual(accept_remote(self.key(),self.key(),True),'historical-only')
    def test_part_arbitrary_json_neighbors(self):
        for v in([],0,False,None,'x',{'x':1}):
            with self.subTest(v=v):self.assertEqual(part({'data':v}),'data')
    def test_part_oneof_reject(self):
        with self.assertRaises(ValueError):part({'text':'ok','url':'http://example.invalid'})
    def test_part_missing_reject(self):
        with self.assertRaises(ValueError):part({'metadata':{}})

class EvaluationTests(unittest.TestCase):
    def test_valid_complete_pass(self):self.assertEqual(decide(Evidence(2,2,judge_valid=True,required_layers_complete=True)),'PASS')
    def test_unknown_not_pass(self):self.assertEqual(decide(Evidence(2,1,unresolved=1,judge_valid=True,required_layers_complete=True)),'INSUFFICIENT')
    def test_real_layer_not_run(self):self.assertEqual(decide(Evidence(2,2,judge_valid=True)),'INSUFFICIENT')
    def test_judge_invalid(self):self.assertEqual(decide(Evidence(2,2,required_layers_complete=True)),'INSUFFICIENT')
    def test_critical_not_averaged(self):self.assertEqual(decide(Evidence(100,100,critical_violations=1,judge_valid=True,required_layers_complete=True)),'FAIL')
    def test_planned_denominator(self):self.assertEqual(raw_success_fraction(Evidence(100,80,10,10,judge_valid=True,required_layers_complete=True)),.8)
    def test_not_run_kept(self):self.assertEqual(decide(Evidence(12,10,not_run=2,judge_valid=True,required_layers_complete=True)),'INSUFFICIENT')
    def test_bool_not_count(self):
        with self.assertRaises(ValueError):decide(Evidence(1,True))
    def test_missing_trials_invalid(self):
        with self.assertRaises(ValueError):decide(Evidence(2,1))
    def test_zero_failures_nonzero_risk(self):self.assertAlmostEqual(zero_failure_upper(100),.02951304960703993)
    def test_empty_evidence_invalid(self):
        with self.assertRaises(ValueError):decide(Evidence(0,0))
    def test_zero_failure_invalid_assumption_count(self):
        for n in(0,True,-1):
            with self.subTest(n=n),self.assertRaises(ValueError):zero_failure_upper(n)

class ArchiveAdmissionTests(unittest.TestCase):
    def archive(self,name,data=b'x',mode=0):
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w')as z:
            info=zipfile.ZipInfo(name);info.external_attr=mode<<16;z.writestr(info,data)
        b.seek(0);return b
    def test_legal_relative_file(self):self.assertEqual(archive_members(self.archive('data/readme.txt')),['data/readme.txt'])
    def test_archive_traversal(self):
        with self.assertRaises(ValueError):archive_members(self.archive('../outside'))
    def test_archive_absolute_path(self):
        with self.assertRaises(ValueError):archive_members(self.archive('/outside'))
    def test_archive_symlink(self):
        with self.assertRaises(ValueError):archive_members(self.archive('link',b'../../outside',stat.S_IFLNK|0o777))
    def test_archive_expansion_limit(self):
        with self.assertRaises(ValueError):archive_members(self.archive('large',b'x'*1000),max_total=999)
    def test_archive_exact_capacity_neighbor(self):self.assertEqual(archive_members(self.archive('large',b'x'*1000),max_total=1000),['large'])


class StreamAndDecisionTests(unittest.TestCase):
    def setUp(self):self.k=('r1','a1',1);self.s=StreamAssembler(*self.k)
    def test_complete_text(self):
        self.s.feed(self.k,'text.delta','msg',0,'Hello');self.s.feed(self.k,'complete');self.assertEqual(self.s.text('msg'),'Hello');self.assertEqual(self.s.fin(),'complete')
    def test_fin_without_terminal_is_partial(self):
        self.s.feed(self.k,'text.delta','msg',0,'looks done');self.assertEqual(self.s.fin(),'partial')
    def test_partial_json_not_executable_proposal(self):
        self.s.feed(self.k,'tool_args.delta','call',0,'{"amount":100}')
        with self.assertRaises(ValueError):self.s.tool_proposal('call')
    def test_tool_done_without_response_terminal_not_enough(self):
        self.s.feed(self.k,'tool_args.delta','call',0,'{"amount":100}');self.s.feed(self.k,'tool_args.done','call')
        with self.assertRaises(ValueError):self.s.tool_proposal('call')
    def test_complete_tool_is_still_only_proposal(self):
        self.s.feed(self.k,'tool_args.delta','call',0,'{"amount":');self.s.feed(self.k,'tool_args.delta','call',1,'100}');self.s.feed(self.k,'tool_args.done','call');self.s.feed(self.k,'complete');self.assertEqual(self.s.tool_proposal('call'),{'amount':100})
    def test_interleaving_items(self):
        self.s.feed(self.k,'text.delta','A',1,'b');self.s.feed(self.k,'text.delta','B',0,'x');self.s.feed(self.k,'text.delta','A',0,'a');self.assertEqual(self.s.text('A'),'ab');self.assertEqual(self.s.text('B'),'x')
    def test_duplicate_identical_delta(self):
        self.s.feed(self.k,'text.delta','A',0,'a');self.s.feed(self.k,'text.delta','A',0,'a');self.assertEqual(self.s.text('A'),'a')
    def test_duplicate_contradictory_delta(self):
        self.s.feed(self.k,'text.delta','A',0,'a')
        with self.assertRaises(ValueError):self.s.feed(self.k,'text.delta','A',0,'b')
    def test_stream_old_epoch_historical(self):self.assertEqual(self.s.feed(('r1','a1',0),'complete'),'historical-only');self.assertEqual(self.s.status,'open')
    def test_cancel_does_not_prove_remote_stopped(self):
        self.assertEqual(self.s.cancel(),'cancel-requested');self.assertEqual(self.s.remote_status,'unknown');self.assertEqual(self.s.feed(self.k,'complete'),'historical-only')
    def test_incomplete_and_refusal_not_callable(self):
        for terminal in('incomplete','refusal','error'):
            with self.subTest(terminal=terminal):
                s=StreamAssembler(*self.k);s.feed(self.k,terminal)
                with self.assertRaises(ValueError):s.tool_proposal('call')
    def test_unknown_event_not_completion(self):
        with self.assertRaises(ValueError):self.s.feed(self.k,'new-required-event')
        self.assertEqual(self.s.status,'error')
    def test_optional_event_neighbor(self):self.assertEqual(self.s.feed(self.k,'optional-diagnostic'),'ignored-optional')
    def test_decision_not_resampled(self):
        d=Decisions();d.accept('d1','input-v1',{'tool':'A'})
        with self.assertRaises(ValueError):d.accept('d1','input-v1',{'tool':'B'})
    def test_decision_new_revision_neighbor(self):
        d=Decisions();d.accept('d1','input-v1',{'tool':'A'});self.assertTrue(d.accept('d2','input-v2',{'tool':'B'}))
    def test_incomplete_decision_not_accepted(self):
        with self.assertRaises(ValueError):Decisions().accept('d1','v1',{'tool':'A'},complete=False)
    def test_task_completed_tool_error_not_business_success(self):self.assertEqual(task_result_status('completed',{'isError':True}),'tool-failed')
    def test_task_completed_legal_neighbor(self):self.assertEqual(task_result_status('completed',{'isError':False}),'tool-result-needs-business-validation')

class RemoteLifecycleTests(unittest.TestCase):
    def setUp(self):self.k=RemoteKey('svc','https://agent.invalid','u','route','task','ctx');self.t=RemoteTaskTracker(self.k)
    def test_a2a_disconnect_not_task_cancellation(self):self.t.update(self.k,'working');self.assertEqual(self.t.disconnect(),'working')
    def test_a2a_cancel_requested_not_cancel_confirmed(self):self.t.update(self.k,'working');self.assertEqual(self.t.request_cancel(),'working');self.assertTrue(self.t.cancel_requested)
    def test_a2a_auth_required_not_approval(self):self.t.update(self.k,'auth-required');self.assertEqual(self.t.state,'auth-required')
    def test_a2a_unknown_not_complete(self):
        with self.assertRaises(ValueError):self.t.update(self.k,'new-state')
    def test_artifact_last_chunk_not_task_terminal(self):self.assertEqual(self.t.artifact(self.k,'a',{'text':'report'},last=True),'complete');self.assertEqual(self.t.state,'submitted')
    def test_ambiguous_append_requires_query(self):self.assertEqual(self.t.artifact(self.k,'a','piece',append=True,last=True),'needs-authority-query')
    def test_full_artifact_read_neighbor(self):self.t.artifact(self.k,'a','piece',append=True);self.assertEqual(self.t.artifact(self.k,'a','complete original',last=True),'complete')
    def test_terminal_not_revived_by_working(self):self.t.update(self.k,'completed');self.assertEqual(self.t.update(self.k,'working'),'historical-only');self.assertEqual(self.t.state,'completed')


class RpcOutstandingTests(unittest.TestCase):
    def test_duplicate_pending_id_rejected(self):
        p=RpcOutstanding();p.issue('r1')
        with self.assertRaises(ValueError):p.issue('r1')
    def test_completed_id_may_be_reused_neighbor(self):
        p=RpcOutstanding();p.issue(1);p.respond(1);p.issue(1);self.assertEqual(p.pending,{1})
    def test_unmatched_response_cannot_clear_other(self):
        p=RpcOutstanding();p.issue('r1')
        with self.assertRaises(ValueError):p.respond('r2')
        self.assertEqual(p.pending,{'r1'})
    def test_resulttype_wrong_type_rejected(self):
        for value in([],True,None,1):
            with self.subTest(value=value),self.assertRaises(ValueError):mcp_result_type({'resultType':value})



class AdditionalRecoveryTests(unittest.TestCase):
    def test_event_before_wait_is_not_lost(self):
        i=Inbox();i.put('e1','interrupt1',{'amount':100},2,'approve');self.assertEqual(i.find('interrupt1',{'amount':100},2),['e1']);self.assertEqual(i.consume('e1','interrupt1',{'amount':100},2),'approve');self.assertEqual(i.consume('e1','interrupt1',{'amount':100},2),'duplicate')
    def test_wake_changed_parameters_rejected(self):
        i=Inbox();i.put('e1','interrupt1',{'amount':100},2,'approve')
        with self.assertRaises(ValueError):i.consume('e1','interrupt1',{'amount':200},2)
    def test_old_epoch_wake_does_not_wake_new_attempt(self):
        i=Inbox();i.put('e1','interrupt1',{},1,'approve');self.assertEqual(i.find('interrupt1',{},2),[])
    def test_cancel_preserves_unknown_budget(self):
        c=Controller();c.budget.reserve('op',10);c.budget.unknown('op');c.cancel();self.assertEqual(c.budget.reserved,10);r=Controller.restore(c.snapshot(),c.snapshot());self.assertEqual(r.budget.reserved,10)
    def test_stream_sequence_gap_not_callable(self):
        s=StreamAssembler('r','a',1);k=('r','a',1);s.feed(k,'tool_args.delta','c',1,'{"amount":100}');s.feed(k,'tool_args.done','c');s.feed(k,'complete')
        with self.assertRaises(ValueError):s.tool_proposal('c')
    def test_fin_cannot_later_promote_same_stream(self):
        s=StreamAssembler('r','a',1);self.assertEqual(s.fin(),'partial');self.assertEqual(s.feed(('r','a',1),'complete'),'historical-only');self.assertEqual(s.status,'partial')

if __name__=='__main__':unittest.main()
