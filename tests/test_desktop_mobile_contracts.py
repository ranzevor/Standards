import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec)
    sys.modules[name]=mod; spec.loader.exec_module(mod); return mod
c=module('desktop_mobile_finite',ROOT/'examples/desktop-mobile/contracts.py')
gate=module('desktop_mobile_gate',ROOT/'tools/check_desktop_mobile.py')

class GenerationContracts(unittest.TestCase):
    def test_current_context_delivers(self):
        a=c.Context('A',1,'doc',1,'scene'); self.assertTrue(c.can_deliver(a,a))
    def test_account_epoch_change_rejects(self):
        a=c.Context('A',1,'doc',1,'scene'); b=c.Context('A',2,'doc',1,'scene'); self.assertFalse(c.can_deliver(a,b))
    def test_new_document_same_origin_rejects(self):
        a=c.Context('A',1,'doc',1,'scene'); b=c.Context('A',1,'doc',2,'scene'); self.assertFalse(c.can_deliver(a,b))
    def test_scene_change_rejects(self):
        a=c.Context('A',1,'doc',1,'s1'); b=c.Context('A',1,'doc',1,'s2'); self.assertFalse(c.can_deliver(a,b))
    def test_revocation_rejects_same_context(self):
        a=c.Context('A',1,'doc',1,'scene'); self.assertFalse(c.can_deliver(a,a,False))
    def test_save_old_ack_preserves_new_dirty(self):
        s=c.SaveLedger(); s.edit('one'); s.capture('s1'); s.edit('two'); s.commit('s1'); s.acknowledge('s1')
        self.assertTrue(s.dirty); self.assertEqual(s.stored,'one')
    def test_late_ack_does_not_regress_clean(self):
        s=c.SaveLedger(); s.edit('one'); s.capture('s1'); s.commit('s1'); s.edit('two'); s.capture('s2'); s.commit('s2'); s.acknowledge('s2'); s.acknowledge('s1')
        self.assertFalse(s.dirty); self.assertEqual(s.stored,'two'); self.assertEqual(s.acknowledged,2)
    def test_old_write_cannot_overwrite_new(self):
        s=c.SaveLedger(); s.edit('one'); s.capture('s1'); s.edit('two'); s.capture('s2'); s.commit('s2')
        with self.assertRaises(ValueError): s.commit('s1')
    def test_uncommitted_ack_rejected(self):
        s=c.SaveLedger(); s.edit('one'); s.capture('s1')
        with self.assertRaises(ValueError): s.acknowledge('s1')
    def test_uncommitted_old_save_not_proven_by_new_commit(self):
        s=c.SaveLedger(); s.edit('one'); s.capture('s1'); s.edit('two'); s.capture('s2'); s.commit('s2')
        with self.assertRaises(ValueError): s.acknowledge('s1')

class ActivationAndCompatibility(unittest.TestCase):
    def test_duplicate_activation_and_new_intent(self):
        l=c.ActivationLedger(); self.assertEqual(l.open('u','i','e1','中文 空格'),'opened')
        self.assertEqual(l.open('u','i','e1','中文 空格'),'accepted-duplicate')
        self.assertEqual(l.open('u','i','e2','中文 空格'),'focused')
    def test_identity_same_event_different_payload_rejected(self):
        l=c.ActivationLedger(); l.open('u','i','e1','a')
        with self.assertRaises(ValueError): l.open('u','i','e1','b')
    def test_separate_users_are_independent(self):
        l=c.ActivationLedger(); l.open('u1','i','e','a'); self.assertEqual(l.open('u2','i','e','a'),'opened')
    def test_compatible_binary_and_components(self): self.assertTrue(c.may_run({1,2},2,[{1,2},{2}],2))
    def test_binary_rollback_not_data_rollback(self): self.assertFalse(c.may_run({1},2,[{1,2}],1))
    def test_old_helper_protocol_rejected(self): self.assertFalse(c.may_run({2},2,[{1},{2}],2))

class OfflineEffects(unittest.TestCase):
    def operation(self): return c.Operation('A','op',c.digest({'amount':5}))
    def test_original_request_can_send(self):
        o=self.operation(); self.assertEqual(o.send('A',o.parameters,'a1'),'unknown')
    def test_account_switch_does_not_rebind_queue(self):
        o=self.operation()
        with self.assertRaises(ValueError): o.send('B',o.parameters,'a1')
    def test_parameters_immutable(self):
        o=self.operation()
        with self.assertRaises(ValueError): o.send('A',c.digest({'amount':6}),'a1')
    def test_unknown_without_contract_cannot_retry(self):
        o=self.operation(); o.send('A',o.parameters,'a1'); self.assertFalse(o.retry_allowed('A',o.parameters,1))
    def test_dispatch_enforces_retry_contract(self):
        o=self.operation(); o.send('A',o.parameters,'old')
        with self.assertRaises(ValueError): o.send('A',o.parameters,'new')
    def test_verified_dedup_and_late_rejection_can_retry(self):
        o=self.operation(); o.send('A',o.parameters,'a1'); self.assertTrue(o.retry_allowed('A',o.parameters,4,c.RetryContract(10,8,True)))
    def test_local_dispatch_before_expiry_not_sufficient(self):
        o=self.operation(); o.send('A',o.parameters,'a1'); self.assertFalse(o.retry_allowed('A',o.parameters,4,c.RetryContract(10,8,False)))
    def test_verified_delivery_bound_is_legal_neighbor(self):
        o=self.operation(); o.send('A',o.parameters,'a1'); self.assertTrue(o.retry_allowed('A',o.parameters,4,c.RetryContract(10,8,False,3)))
    def test_late_acceptance_exceeds_dedup_rejected(self): self.assertFalse(c.RetryContract(10,12,True).safe_at(4))
    def test_expired_dedup_rejected(self): self.assertFalse(c.RetryContract(10,8,True).safe_at(11))
    def test_new_not_applied_does_not_clear_old_unknown(self):
        o=self.operation(); o.send('A',o.parameters,'old'); o.send('A',o.parameters,'new',now=2,contract=c.RetryContract(10,8,True))
        self.assertEqual(o.observe(c.Receipt('A','op',o.parameters,'new','not-applied')),'unknown')
        self.assertEqual(o.pending,{'old'})
    def test_exact_applied_receipt_confirms(self):
        o=self.operation(); o.send('A',o.parameters,'old'); self.assertEqual(o.observe(c.Receipt('A','op',o.parameters,'old','applied')),'confirmed')
        self.assertFalse(o.retry_allowed('A',o.parameters,2))
    def test_wrong_receipt_scope_rejected(self):
        o=self.operation(); o.send('A',o.parameters,'old')
        with self.assertRaises(ValueError): o.observe(c.Receipt('B','op',o.parameters,'old','applied'))
    def test_all_attempts_proven_not_applied_is_legal(self):
        o=self.operation(); o.send('A',o.parameters,'old'); self.assertEqual(o.observe(c.Receipt('A','op',o.parameters,'old','not-applied')),'not-submitted')
        self.assertTrue(o.retry_allowed('A',o.parameters,20))

class BackgroundAndDiagnostics(unittest.TestCase):
    def test_current_authorized_target_fence(self):
        a=c.BackgroundAttempt('job','op',2,2); self.assertTrue(a.may_commit('A','A',True,True))
    def test_stale_epoch_or_no_target_fence(self):
        a=c.BackgroundAttempt('job','op',1,2); self.assertFalse(a.may_commit('A','A',True,True))
        b=c.BackgroundAttempt('job','op',2,2); self.assertFalse(b.may_commit('A','A',True,False))
    def test_expiration_completion_once_not_business_success(self):
        a=c.BackgroundAttempt('job','op',2,2); a.expire(); self.assertTrue(a.complete(True)); self.assertFalse(a.complete(True)); self.assertEqual(a.phase,'incomplete')
    def test_current_job_cannot_use_new_account(self):
        a=c.BackgroundAttempt('job','op',2,2); self.assertFalse(a.may_commit('B','A',True,True))
    def test_diagnostic_exact_symbols_and_minimality(self):
        self.assertTrue(c.diagnostic_acceptable('b1','b1',10,20,False))
        self.assertFalse(c.diagnostic_acceptable('b1','b2',10,20,False))
        self.assertFalse(c.diagnostic_acceptable('b1','b1',30,20,False))
        self.assertFalse(c.diagnostic_acceptable('b1','b1',10,20,True))

class DirectTextMutations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import json
        cls.entry=next(row for row in json.loads((ROOT/'registry/standards.json').read_text()) if row['id']=='STD-L4-MOBILE-006')
        cls.path=ROOT/cls.entry['path']
        cls.text=cls.path.read_text(); cls.ids=[f'MB5-{i:02d}' for i in range(1,8)]
    def test_final_text_parses(self): self.assertEqual(gate.parse(self.text,self.ids),self.ids)
    def rejected(self,text):
        with self.assertRaises(ValueError): gate.parse(text,self.ids)
    def test_delete_clause_without_hash_shortcut(self): self.rejected(self.text.replace('### MB5-03 ','### Removed '))
    def test_duplicate_clause_without_hash_shortcut(self): self.rejected(self.text.replace('### MB5-02 ','### MB5-01 '))
    def test_extra_clause_without_hash_shortcut(self): self.rejected(self.text+'\n### MB5-08 Extra\n'+('x'*150))
    def test_missing_neighbor_without_hash_shortcut(self): self.rejected(self.text.replace('**合法邻例：**','**邻接描述：**',1))
    def test_missing_recovery_without_hash_shortcut(self): self.rejected(self.text.replace('**并发、超时、未知与恢复：**','**其他：**',1))
    def test_source_label_unresolved_without_hash_shortcut(self): self.rejected(self.text+'\n[S99]\n')
    def test_wrong_current_metadata_without_hash_shortcut(self):
        for original,replacement in [('**状态：** adopted','**状态：** draft'),
                                     ('**版本：** '+self.entry['version'],'**版本：** 9.9.9'),
                                     ('**生效日期：** '+self.entry['effective_date'],'**生效日期：** 未设'),
                                     ('STD-L4-MOBILE-006','invalid-id')]:
            with self.subTest(original=original):
                mutated=self.text.replace(original,replacement,1)
                self.assertNotEqual(mutated,self.text)
                self.rejected(mutated)
    def test_duplicate_current_metadata_rejected(self):
        marker='**版本：** '+self.entry['version']
        self.rejected(self.text.replace(marker,marker+' '+marker,1))
    def test_document_identity_must_match_registry(self):
        with self.assertRaisesRegex(ValueError,'differs from registry'):
            gate.parse(self.text,self.ids,'STD-L4-MOBILE-007')
    def test_current_registry_gate(self):
        result=gate.check(ROOT)
        self.assertEqual((result['documents'],result['status']),(17,'adopted'))
        import json
        expected=sorted({row['version'] for row in json.loads((ROOT/'registry/standards.json').read_text()) if row['domain'] in {'desktop','mobile'}})
        self.assertEqual(result['versions'],expected)
        self.assertGreater(result['clauses'],0)
        self.assertEqual(set(result),{'documents','clauses','sources','local_links','gate','version','versions','status','checks'})
    def test_new_revision_requires_exact_registered_metadata(self):
        newer=dict(self.entry,version='0.1.2',effective_date='2026-10-28')
        text=self.text.replace('**版本：** '+self.entry['version'],'**版本：** 0.1.2',1)
        text=text.replace('**生效日期：** '+self.entry['effective_date'],'**生效日期：** 2026-10-28',1)
        self.assertEqual(gate.parse(text,self.ids,self.entry['id'],newer),self.ids)
        with self.assertRaises(ValueError):gate.parse(text,self.ids,self.entry['id'],self.entry)
    def test_legal_whitespace_parses(self): self.assertEqual(gate.parse(self.text.replace('\n\n','\n\n\n'),self.ids),self.ids)
    def test_optimized_public_entry_rejected(self):
        for flag in ('-O','-OO'):
            p=subprocess.run([sys.executable,flag,str(ROOT/'tools/check_desktop_mobile.py'),'--help'],capture_output=True,text=True)
            self.assertNotEqual(p.returncode,0); self.assertIn('optimized Python is unsupported',p.stderr)

if __name__=='__main__': unittest.main()
