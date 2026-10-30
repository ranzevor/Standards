"""Requirement-derived finite model cases; not real service/hardware acceptance."""
import copy
from hashlib import sha256
import importlib.util
from pathlib import Path
import sys
import tempfile
import threading
import unittest
BASE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('sec_models',BASE/'examples/security-edge-commerce/models.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)

class MoneyTests(unittest.TestCase):
    def test_decimal_half_even_boundaries(self):
        self.assertEqual(m.Money.decimal('USD',2,'0.005').minor,0)
        self.assertEqual(m.Money.decimal('USD',2,'0.015').minor,2)
        self.assertEqual(m.Money.decimal('USD',2,'-0.015').minor,-2)
    def test_float_rejected(self):
        with self.assertRaises(m.ContractError):m.Money.decimal('USD',2,0.1)
    def test_nonfinite_rejected(self):
        for value in ['NaN','Infinity','-Infinity','1e999999']:
            with self.subTest(value=value),self.assertRaises(m.ContractError):m.Money.decimal('USD',2,value)
    def test_currency_and_exponent_mismatch(self):
        for other in [m.Money('EUR',2,1),m.Money('USD',3,1)]:
            with self.assertRaises(m.ContractError): _=m.Money('USD',2,1)+other
    def test_high_precision_accumulate_before_quantize(self):
        from decimal import Decimal
        accumulated=str(Decimal('0.004')*3)
        self.assertEqual(m.Money.decimal('USD',2,accumulated).minor,1)
    def test_legal_zero_and_three_decimal(self):
        self.assertEqual(m.Money.decimal('JPY',0,'10').minor,10)
        self.assertEqual(m.Money.decimal('BHD',3,'0.001').minor,1)
    def test_allocation_residual_and_order(self):
        weights=[('c',1),('a',1),('b',1)]
        self.assertEqual(m.allocate(1,weights),{'c':0,'a':1,'b':0})
        self.assertEqual(m.allocate(1,weights),m.allocate(1,list(reversed(weights))))
    def test_negative_allocation_symmetry(self):
        self.assertEqual(m.allocate(-1,[('a',1),('b',1)]),{'a':-1,'b':0})
    def test_allocation_exhaustive_conservation(self):
        for total in range(-30,31):
            for a in range(4):
                for b in range(4):
                    if a+b:
                        result=m.allocate(total,[('a',a),('b',b)])
                        self.assertEqual(sum(result.values()),total)
                        self.assertTrue(all(abs(v)<=abs(total) for v in result.values()))
    def test_bad_allocation(self):
        for weights in [[('a',0)],[('a',1),('a',2)],[('a',-1)],[]]:
            with self.assertRaises(m.ContractError):m.allocate(1,weights)

class CommerceTests(unittest.TestCase):
    def test_new_not_applied_does_not_close_old_unknown(self):
        a=m.Attempts();a.observe('old-A','unknown');a.observe('new-B','never-applies')
        self.assertFalse(a.may_create_new())
    def test_all_attempts_terminal_no_effect_allows_retry(self):
        a=m.Attempts();a.observe('A','never-applies');a.observe('B','never-applies')
        self.assertTrue(a.may_create_new())
    def test_pending_and_applied_forbid_new(self):
        for state in ['pending','unknown','applied']:
            a=m.Attempts();a.observe('A',state);self.assertFalse(a.may_create_new())
    def test_late_success_retained_and_terminal_conflict_rejected(self):
        a=m.Attempts();a.observe('A','unknown');a.observe('A','applied')
        with self.assertRaises(m.ContractError):a.observe('A','never-applies')
        self.assertEqual(a.facts['A'],'applied')
    def test_multiple_applied_is_explicit_failure(self):
        a=m.Attempts({'A':'applied','B':'applied'})
        with self.assertRaises(m.ContractError):a.apply_at_most_once()
    def test_refund_unknown_reserves_balance(self):
        b=m.RefundBook(100);b.reserve('A',60);b.observe('A','unknown')
        with self.assertRaises(m.ContractError):b.reserve('B',50)
        self.assertEqual(b.available,40)
    def test_refund_repeated_intent_and_parameter_drift(self):
        b=m.RefundBook(100);b.reserve('A',30);b.reserve('A',30)
        self.assertEqual(b.available,70)
        with self.assertRaises(m.ContractError):b.reserve('A',31)
    def test_refund_terminal_no_effect_releases(self):
        b=m.RefundBook(100);b.reserve('A',70);b.observe('A','never-applies');b.reserve('B',100)
        self.assertEqual(b.available,0)
    def test_legal_multiple_partial_refunds(self):
        b=m.RefundBook(100);b.reserve('A',50);b.observe('A','applied');b.reserve('B',50);b.observe('B','applied')
        self.assertEqual(b.available,0)
    def test_concurrent_refunds_no_overreserve(self):
        b=m.RefundBook(100);barrier=threading.Barrier(3);out=[]
        def reserve(k):
            barrier.wait()
            try:b.reserve(k,60);out.append('ok')
            except m.ContractError:out.append('reject')
        ts=[threading.Thread(target=reserve,args=(k,)) for k in ['A','B']]
        for t in ts:t.start()
        barrier.wait()
        for t in ts:t.join()
        self.assertCountEqual(out,['ok','reject']);self.assertEqual(b.available,40)
    def test_last_stock_concurrent(self):
        b=m.Stock(1);barrier=threading.Barrier(3);out=[]
        def reserve(k):
            barrier.wait()
            try:b.reserve(k);out.append('ok')
            except m.ContractError:out.append('reject')
        ts=[threading.Thread(target=reserve,args=(k,)) for k in ['A','B']]
        for t in ts:t.start()
        barrier.wait()
        for t in ts:t.join()
        self.assertCountEqual(out,['ok','reject'])
    def test_expiry_cannot_release_committed_stock(self):
        b=m.Stock(1);b.reserve('A');b.transition('A','committed')
        with self.assertRaises(m.ContractError):b.transition('A','expired')
        self.assertEqual(b.reservations['A'],'committed')
    def test_repeated_release_and_independent_reservation(self):
        b=m.Stock(1);b.reserve('A');b.transition('A','released');b.transition('A','released');b.reserve('B')
        self.assertEqual(b.reservations['B'],'reserved')
    def test_ledger_source_idempotency_and_drift(self):
        l=m.Ledger({'cash':('USD','asset'),'sales':('USD','revenue')})
        self.assertTrue(l.post('capture-1','USD','capture',[('cash',100),('sales',-100)]))
        self.assertFalse(l.post('capture-1','USD','capture',[('sales',-100),('cash',100)]))
        with self.assertRaises(m.ContractError):l.post('capture-1','USD','capture',[('cash',101),('sales',-101)])
        self.assertEqual(l.balances(),{'cash':100,'sales':-100})
    def test_balanced_wrong_account_mapping_rejected(self):
        l=m.Ledger({'cash':('USD','revenue'),'sales':('USD','asset')})
        with self.assertRaises(m.ContractError):l.post('x','USD','capture',[('cash',100),('sales',-100)])
        self.assertFalse(l.journal)
    def test_cross_currency_and_unbalanced_no_partial_journal(self):
        l=m.Ledger({'cash':('USD','asset'),'sales':('USD','revenue')})
        for currency,lines in [('EUR',[('cash',100),('sales',-100)]),('USD',[('cash',100),('sales',-99)])]:
            with self.assertRaises(m.ContractError):l.post('x',currency,'capture',lines)
            self.assertFalse(l.journal)
    def test_reversal_keeps_original(self):
        l=m.Ledger({'cash':('USD','asset'),'sales':('USD','revenue')})
        l.post('x','USD','capture',[('cash',100),('sales',-100)]);original=l.journal['x']
        l.post('reverse-x','USD','reversal',[('cash',-100),('sales',100)])
        self.assertEqual(l.journal['x'],original);self.assertEqual(l.balances(),{'cash':0,'sales':0})
    def test_usage_duplicate_drift_and_same_value_independent(self):
        u=m.Usage();self.assertTrue(u.add('c','m','A','byte',5,'w'))
        self.assertFalse(u.add('c','m','A','byte',5,'w'))
        with self.assertRaises(m.ContractError):u.add('c','m','A','KB',5,'w')
        self.assertTrue(u.add('c','m','B','byte',5,'w'));self.assertEqual(u.total('c','m','byte','w'),10)
    def test_usage_customer_window_scope(self):
        u=m.Usage();u.add('c','m','A','byte',5,'w');u.add('other','m','A','byte',7,'w')
        self.assertEqual(u.total('c','m','byte','other-window'),0);self.assertEqual(u.total('c','m','byte','w'),5)

class SecurityEdgeTests(unittest.TestCase):
    def manifest(self,image=b'new',seq=2,version='2',**kwargs):
        d=dict(vendor='v',device_class='c',sequence=seq,display_version=version,security_level=2,digest=sha256(image).hexdigest(),size=len(image));d.update(kwargs)
        return m.Manifest(**d)
    def test_issuer_namespace_and_object_grant(self):
        a=m.Principal('idp-a','same','t');b=m.Principal('idp-b','same','t')
        g=m.ResourceGate(1,{(a,'own','read')});g.execute(a,'own','read',1)
        with self.assertRaises(m.ContractError):g.execute(b,'own','read',1)
        with self.assertRaises(m.ContractError):g.execute(a,'other','read',1)
        self.assertEqual(len(g.effects),1)
    def test_target_fence_rejects_old_allows_current_parallel_objects(self):
        a=m.Principal('i','s','t');g=m.ResourceGate(1,{(a,'A','write'),(a,'B','write')});g.install_fence(2)
        with self.assertRaises(m.ContractError):g.execute(a,'A','write',1)
        g.execute(a,'A','write',2);g.execute(a,'B','write',2);self.assertEqual(len(g.effects),2)
    def test_credential_roll_requires_consumer_and_target_rejection(self):
        r=m.CredentialRoll({'a','offline'},{'a':'new'},{'old','new'},{'old-kek'})
        self.assertFalse(r.complete('new','old'));r.versions['offline']='new';self.assertFalse(r.complete('new','old'))
        r.accepted.remove('old');self.assertTrue(r.complete('new','old'));self.assertIn('old-kek',r.historical_decrypt)
    def test_torn_record_every_byte_retains_old(self):
        old=m.record(1,{'x':'old'});new=m.record(2,{'x':'new'})
        for cut in range(len(new)):
            self.assertEqual(m.recover([old,new[:cut]])['payload'],{'x':'old'})
        self.assertEqual(m.recover([old,new])['payload'],{'x':'new'})
    def test_real_file_bytes_reopened_after_simulated_tears(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp)/'slot-a';b=Path(tmp)/'slot-b';a.write_bytes(m.record(1,'old'))
            new=m.record(2,'new')
            for cut in range(len(new)+1):
                b.write_bytes(new[:cut]);r=m.recover([a.read_bytes(),b.read_bytes()])
                self.assertEqual(r['payload'],'new' if cut==len(new) else 'old')
    def test_corruption_and_conflicting_generation(self):
        raw=bytearray(m.record(1,'A'));raw[6]^=1
        self.assertIsNone(m.parse_record(bytes(raw)))
        with self.assertRaises(m.ContractError):m.recover([b'bad',bytes(raw)])
        with self.assertRaises(m.ContractError):m.recover([m.record(1,'A'),m.record(1,'B')])
    def test_valid_manifest_install_and_health(self):
        d=m.FirmwareDevice('v',{'c'},1);man=self.manifest();d.accept(man,b'new');d.boot();d.confirm(man.digest,True)
        self.assertEqual(d.active_digest,man.digest)
    def test_wrong_hardware_hash_size_and_authority(self):
        for kw in [{'vendor':'other'},{'device_class':'wrong'},{'digest':'0'*64},{'size':999},{'authenticated_by_test_authority':False}]:
            with self.subTest(kw=kw):
                d=m.FirmwareDevice('v',{'c'},1)
                with self.assertRaises(m.ContractError):d.accept(self.manifest(**kw),b'new')
                self.assertEqual(d.highest,0);self.assertIsNone(d.active_digest)
    def test_old_sequence_rejected_higher_authorized_display_rollback_allowed(self):
        d=m.FirmwareDevice('v',{'c'},1);d.accept(self.manifest(seq=2),b'new')
        with self.assertRaises(m.ContractError):d.accept(self.manifest(seq=1),b'new')
        self.assertTrue(d.accept(self.manifest(image=b'older',seq=3,version='1'),b'older'))
    def test_equal_same_resume_preserves_attempt_count(self):
        d=m.FirmwareDevice('v',{'c'},1);man=self.manifest();d.accept(man,b'new');d.boot()
        self.assertFalse(d.accept(man,b'new'));self.assertEqual(d.attempts,1)
    def test_equal_sequence_different_content_rejected(self):
        d=m.FirmwareDevice('v',{'c'},1);d.accept(self.manifest(),b'new')
        with self.assertRaises(m.ContractError):d.accept(self.manifest(image=b'other'),b'other')
    def test_security_floor_and_sequence_wrap_rejected(self):
        d=m.FirmwareDevice('v',{'c'},2)
        for man in [self.manifest(security_level=1),self.manifest(seq=2**64)]:
            with self.assertRaises(m.ContractError):d.accept(man,b'new')
    def test_boot_is_not_health_and_attempts_bounded(self):
        d=m.FirmwareDevice('v',{'c'},1);man=self.manifest();d.accept(man,b'new');d.boot()
        self.assertIsNone(d.active_digest)
        with self.assertRaises(m.ContractError):d.confirm(man.digest,False)
        d.boot()
        with self.assertRaises(m.ContractError):d.boot()
    def test_old_candidate_confirmation_rejected(self):
        d=m.FirmwareDevice('v',{'c'},1);old=self.manifest();d.accept(old,b'new');d.boot()
        newer=self.manifest(image=b'newer',seq=3);d.accept(newer,b'newer');d.boot()
        with self.assertRaises(m.ContractError):d.confirm(old.digest,True)
    def test_dma_incomplete_stale_and_free_rejected(self):
        b=m.Buffer();b.start_dma()
        with self.assertRaises(m.ContractError):b.consume()
        with self.assertRaises(m.ContractError):b.free()
        with self.assertRaises(m.ContractError):b.reclaim_and_invalidate()
        b.finish_dma()
        with self.assertRaises(m.ContractError):b.consume()
        b.reclaim_and_invalidate();b.consume();b.free();self.assertEqual(b.owner,'free')
    def test_clock_wrap_with_bound_and_unknown_interval(self):
        self.assertEqual(m.elapsed_u8(250,3,20),9)
        with self.assertRaises(m.ContractError):m.elapsed_u8(0,200,20)
        with self.assertRaises(m.ContractError):m.elapsed_u8(0,1,200)

class EcosystemTests(unittest.TestCase):
    def proof(self,artifact=b'a'):
        return {'signed_by':'trusted','subject':sha256(artifact).hexdigest(),'predicateType':'https://slsa.dev/provenance/v1','builder':'builder','externalParameters':{'source':'canonical'}}
    def policy(self):return {'signers':{'trusted'},'builders':{'builder'},'externalParameters':{'source':'canonical'}}
    def graph(self):return {'spdxVersion':'SPDX-2.3','ids':['SPDXRef-DOCUMENT','SPDXRef-app','SPDXRef-lib'],'relationships':[['SPDXRef-DOCUMENT','DESCRIBES','SPDXRef-app'],['SPDXRef-app','DEPENDS_ON','SPDXRef-lib']]}
    def test_root_license_does_not_override_explicit_different(self):
        self.assertEqual(m.material_scope('icon',{'icon':'CC-BY-4.0'},'MIT'),'CC-BY-4.0')
    def test_missing_or_unknown_material_not_filled_from_root(self):
        for explicit in [{},{'icon':None}]:
            with self.assertRaises(m.ContractError):m.material_scope('icon',explicit,'MIT')
    def test_provenance_subject_and_identity_rejected(self):
        for kw in [{'signed_by':'attacker'},{'subject':'0'*64},{'builder':'other'}]:
            p=self.proof();p.update(kw)
            with self.assertRaises(m.ContractError):m.verify_provenance(b'a',p,self.policy())
    def test_general_unknown_extension_legal_but_external_parameter_unknown_rejected(self):
        p=self.proof();p['futureExtension']={'x':1};self.assertTrue(m.verify_provenance(b'a',p,self.policy()))
        p['externalParameters']['unexpected']='run-evil'
        with self.assertRaises(m.ContractError):m.verify_provenance(b'a',p,self.policy())
    def test_independent_fork_allowed_only_by_explicit_policy(self):
        p=self.proof();p['externalParameters']={'source':'fork'}
        with self.assertRaises(m.ContractError):m.verify_provenance(b'a',p,self.policy())
        policy=self.policy();policy['externalParameters']={'source':'fork'}
        self.assertTrue(m.verify_provenance(b'a',p,policy))
    def test_graph_dangling_and_duplicate_ids_rejected(self):
        g=self.graph();g['relationships'][1][2]='SPDXRef-missing'
        with self.assertRaises(m.ContractError):m.validate_graph(g)
        g=self.graph();g['ids'].append('SPDXRef-app')
        with self.assertRaises(m.ContractError):m.validate_graph(g)
    def test_noassertion_and_none_remain_distinct_legal_values(self):
        g=self.graph();g['relationships'][1][2]='NOASSERTION';self.assertTrue(m.validate_graph(g))
        h=copy.deepcopy(g);h['relationships'][1][2]='NONE';self.assertTrue(m.validate_graph(h))
        self.assertNotEqual(g,h)
    def test_spdx_patch_document_version_stays_major_minor(self):
        self.assertTrue(m.validate_graph(self.graph()))
        g=self.graph();g['spdxVersion']='SPDX-2.3.1'
        with self.assertRaises(m.ContractError):m.validate_graph(g)

if __name__=='__main__':unittest.main()
