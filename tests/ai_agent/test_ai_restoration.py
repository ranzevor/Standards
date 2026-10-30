"""Finite recovery regressions; no real Store, provider, billing or distributed claim."""
import copy
from dataclasses import replace
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from checks.ai_agent_model import Authority, Budget, Controller, Event, Memory, MemoryIndex, Target


class MemoryRestorationTests(unittest.TestCase):
    def setUp(self):
        self.index=MemoryIndex();self.index.allow('u','tenant')
        self.old=Memory('tenant','u','preference',1,'source-v1','preference',{'allow_payment':True},100)
        self.key=self.index.put(self.old,principal='u')
        self.corrected=replace(self.old,version=2,source='source-v2',content={'allow_payment':False})

    def correct(self):
        self.index.put(self.corrected,expected=1,principal='u')

    def test_old_restore_cannot_overwrite_current_correction(self):
        self.correct();result=self.index.restore_rows([self.old])
        self.assertEqual(result[0]['status'],'isolated-stale-version')
        self.assertEqual(self.index.emit('u','tenant')[0].content,{'allow_payment':False})
        self.assertEqual(self.index.derived[self.key],['source-v2'])

    def test_same_version_different_content_is_not_equivalent(self):
        with self.assertRaisesRegex(ValueError,'conflicting'):
            self.index.restore_rows([replace(self.old,content={'allow_payment':False})])
        self.assertEqual(self.index.rows[self.key],self.old)

    def test_same_version_different_provenance_is_not_equivalent(self):
        with self.assertRaisesRegex(ValueError,'conflicting'):
            self.index.restore_rows([replace(self.old,source='unrelated-source')])

    def test_same_version_boolean_is_not_interchangeable_with_integer_content(self):
        with self.assertRaisesRegex(ValueError,'conflicting'):
            self.index.restore_rows([replace(self.old,content={'allow_payment':1})])

    def test_put_rejects_older_version_even_with_current_cas(self):
        self.correct()
        with self.assertRaisesRegex(ValueError,'increase'):
            self.index.put(self.old,expected=2,principal='u')

    def test_put_requires_a_new_version_not_same_version_rewriting(self):
        for value in [self.old,replace(self.old,content={'allow_payment':False})]:
            with self.subTest(content=value.content),self.assertRaisesRegex(ValueError,'increase'):
                self.index.put(value,expected=1,principal='u')

    def test_newer_restore_updates_fact_and_derived_provenance(self):
        result=self.index.restore_rows([self.corrected])
        self.assertEqual(result[0]['status'],'restored-newer-version')
        self.assertEqual(self.index.rows[self.key],self.corrected)
        self.assertEqual(self.index.derived[self.key],['source-v2'])

    def test_equivalent_restore_and_repeated_restore_are_legal(self):
        for _ in range(2):
            result=self.index.restore_rows([copy.deepcopy(self.old)])
            self.assertEqual(result[0]['status'],'equivalent-current-version')
            self.assertEqual(self.index.rows[self.key],self.old)

    def test_current_deletion_keeps_old_backup_isolated(self):
        self.index.delete(self.key,principal='u');deleted_generation=self.index.tombstones[self.key]
        result=self.index.restore_rows([self.old])
        self.assertEqual(result[0]['status'],'isolated-deleted-generation')
        self.assertEqual(self.index.emit('u','tenant'),[])
        self.assertEqual(self.index.tombstones[self.key],deleted_generation)

    def test_higher_backup_number_does_not_authorize_recreation_after_current_deletion(self):
        self.index.delete(self.key,principal='u')
        result=self.index.restore_rows([replace(self.corrected,version=3)])
        self.assertEqual(result[0]['status'],'isolated-current-deletion')
        self.assertEqual(self.index.emit('u','tenant'),[])

    def test_current_authorized_recreation_can_accept_a_later_valid_restore(self):
        self.index.delete(self.key,principal='u')
        recreated=replace(self.corrected,version=3)
        self.index.put(recreated,principal='u')
        later=replace(recreated,version=4,source='source-v4')
        self.assertEqual(self.index.restore_rows([later])[0]['status'],'restored-newer-version')
        self.assertEqual(self.index.rows[self.key],later)
        self.assertGreater(later.version,self.index.tombstones[self.key])

    def test_restore_never_restores_revoked_acl(self):
        self.index.revoke('u','tenant');self.index.restore_rows([self.corrected])
        with self.assertRaises(PermissionError):self.index.emit('u','tenant')

    def test_before_emit_stale_restore_does_not_undo_current_correction(self):
        self.correct()
        rows=self.index.emit('u','tenant',before_emit=lambda:self.index.restore_rows([self.old]))
        self.assertEqual([m.version for m in rows],[2])
        self.assertEqual(rows[0].content,{'allow_payment':False})

    def test_correction_then_stale_restore_during_emit_drops_old_read_copy(self):
        def interleave():
            self.correct();self.index.restore_rows([self.old])
        self.assertEqual(self.index.emit('u','tenant',before_emit=interleave),[])
        self.assertEqual(self.index.rows[self.key],self.corrected)

    def test_restore_batch_conflict_is_atomic(self):
        other=replace(self.old,key='other')
        before=copy.deepcopy((self.index.rows,self.index.derived,self.index.restore_audit))
        with self.assertRaises(ValueError):
            self.index.restore_rows([other,replace(self.old,source='conflicting-source')])
        self.assertEqual((self.index.rows,self.index.derived,self.index.restore_audit),before)

    def test_duplicate_key_batch_is_rejected_not_order_dependently_selected(self):
        before=copy.deepcopy(self.index.rows)
        with self.assertRaisesRegex(ValueError,'duplicate'):
            self.index.restore_rows([self.old,self.corrected])
        self.assertEqual(self.index.rows,before)

    def test_restore_version_domain_is_positive_exact_integer(self):
        for version in [True,0,-1,1.0,'2']:
            with self.subTest(version=version),self.assertRaises(ValueError):
                self.index.restore_rows([replace(self.old,version=version)])

    def test_independent_owner_key_and_expiry_boundaries_survive_restore(self):
        self.index.allow('v','tenant')
        other=replace(self.old,owner='v',content={'allow_payment':False})
        self.index.restore_rows([other])
        self.assertEqual(self.index.emit('u','tenant')[0].owner,'u')
        self.assertEqual(self.index.emit('v','tenant')[0].owner,'v')
        self.assertEqual(self.index.emit('v','tenant',now=100),[])


class ControllerRestorationTests(unittest.TestCase):
    def setUp(self):self.controller=Controller('task',10)

    def test_new_spend_then_new_epoch_cannot_reset_budget(self):
        old=self.controller.snapshot();self.controller.budget.reserve('spent',10)
        self.controller.budget.settle('spent',10,'receipt-spent');self.controller.handoff(1,'a2')
        current=self.controller.snapshot();restored=Controller.restore(old,current)
        self.assertEqual(restored.snapshot(),current)
        self.assertEqual(restored.budget.used,10)
        with self.assertRaises(PermissionError):restored.budget.reserve('again',10)

    def test_new_current_unknown_reservation_is_not_dropped(self):
        old=self.controller.snapshot();self.controller.budget.reserve('pending',10)
        self.controller.budget.unknown('pending');restored=Controller.restore(old,self.controller.snapshot())
        self.assertEqual(restored.budget.reserved,10)
        self.assertEqual(restored.budget.entries['pending'].status,'unknown')
        with self.assertRaises(PermissionError):restored.budget.reserve('again',1)

    def test_existing_reserved_can_become_current_unknown_or_final(self):
        self.controller.budget.reserve('op',10);old=self.controller.snapshot()
        self.controller.budget.unknown('op')
        self.assertEqual(Controller.restore(old,self.controller.snapshot()).budget.entries['op'].status,'unknown')
        self.controller.budget.settle('op',4,'receipt')
        restored=Controller.restore(old,self.controller.snapshot())
        self.assertEqual(restored.budget.used,4);self.assertEqual(restored.budget.reserved,0)

    def test_same_epoch_failed_and_succeeded_current_state_cannot_revive(self):
        for terminal in ['failed','succeeded']:
            c=Controller('task',10);old=c.snapshot()
            c.fail()if terminal=='failed'else c.succeed()
            current=c.snapshot();self.assertEqual(current['epoch'],old['epoch'])
            restored=Controller.restore(old,current)
            self.assertEqual(restored.status,terminal);self.assertEqual(restored.snapshot(),current)

    def test_failed_controller_cannot_become_succeeded(self):
        self.controller.fail()
        with self.assertRaisesRegex(ValueError,'terminal'):self.controller.succeed()

    def test_success_is_idempotent_but_other_terminal_transitions_are_not(self):
        self.assertTrue(self.controller.succeed());self.assertFalse(self.controller.succeed())
        for method in [self.controller.cancel,self.controller.fail]:
            with self.assertRaisesRegex(ValueError,'terminal'):method()
        failed=Controller();self.assertTrue(failed.fail());self.assertFalse(failed.fail())
        with self.assertRaises(ValueError):failed.cancel()
        cancelled=Controller();self.assertTrue(cancelled.cancel());epoch=cancelled.epoch
        self.assertFalse(cancelled.cancel());self.assertEqual(cancelled.epoch,epoch)
        with self.assertRaises(ValueError):cancelled.fail()

    def test_wrong_task_current_authority_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'task identity'):
            Controller.restore(self.controller.snapshot(),Controller('different',10).snapshot())

    def test_same_epoch_different_attempt_is_not_a_valid_handoff(self):
        old=self.controller.snapshot();current=copy.deepcopy(old);current['attempt']='a2'
        with self.assertRaisesRegex(ValueError,'attempt'):Controller.restore(old,current)

    def test_new_plan_and_current_required_set_win_over_checkpoint(self):
        old=self.controller.snapshot();self.controller.plan=2;self.controller.required={'new-operation'}
        restored=Controller.restore(old,self.controller.snapshot())
        self.assertEqual(restored.plan,2);self.assertEqual(restored.required,{'new-operation'})
        with self.assertRaises(ValueError):restored.succeed()

    def test_required_set_cannot_change_without_plan_revision(self):
        old=self.controller.snapshot();self.controller.required={'new-operation'}
        with self.assertRaisesRegex(ValueError,'plan changed'):
            Controller.restore(old,self.controller.snapshot())

    def test_current_authority_cannot_erase_previously_final_spend(self):
        self.controller.budget.reserve('op',10);self.controller.budget.settle('op',5,'receipt')
        old=self.controller.snapshot();current=copy.deepcopy(old);current['budget']=Budget(10).snapshot()
        with self.assertRaisesRegex(ValueError,'lost or rebound'):Controller.restore(old,current)

    def test_conflicting_final_settlement_is_not_reconciled_as_a_refund(self):
        self.controller.budget.reserve('op',10);self.controller.budget.settle('op',5,'receipt')
        old=self.controller.snapshot();current=copy.deepcopy(old)
        current['budget']['entries']['op']['actual']=4;current['budget']['used']=4
        with self.assertRaisesRegex(ValueError,'final spend'):Controller.restore(old,current)

    def test_unknown_cannot_regress_to_merely_reserved(self):
        self.controller.budget.reserve('op',10);self.controller.budget.unknown('op')
        old=self.controller.snapshot();current=copy.deepcopy(old)
        current['budget']['entries']['op']['status']='reserved'
        with self.assertRaisesRegex(ValueError,'uncertainty'):Controller.restore(old,current)

    def test_authoritative_zero_effect_release_is_a_legal_neighbor(self):
        self.controller.budget.reserve('op',10);self.controller.budget.unknown('op')
        old=self.controller.snapshot();self.controller.budget.release('op','authoritative-not-started')
        restored=Controller.restore(old,self.controller.snapshot())
        self.assertEqual(restored.budget.reserved,0);restored.budget.reserve('new',10)

    def test_released_reservation_cannot_be_reopened(self):
        self.controller.budget.reserve('op',10);self.controller.budget.release('op','authoritative-not-started')
        old=self.controller.snapshot();current=copy.deepcopy(old)
        current['budget']['entries']['op']['status']='reserved'
        with self.assertRaisesRegex(ValueError,'reopened'):Controller.restore(old,current)

    def test_old_terminal_fact_cannot_be_overruled_by_running_or_another_terminal(self):
        self.controller.fail();old=self.controller.snapshot()
        for state in ['running','succeeded','cancelled']:
            current=copy.deepcopy(old);current['status']=state
            with self.subTest(state=state),self.assertRaisesRegex(ValueError,'terminal fact'):
                Controller.restore(old,current)

    def test_tighter_current_limit_preserves_observed_over_budget_spend(self):
        self.controller.budget.reserve('op',10);self.controller.budget.settle('op',10,'receipt')
        old=self.controller.snapshot();current=copy.deepcopy(old);current['budget']['limit']=5
        restored=Controller.restore(old,current)
        self.assertEqual((restored.budget.limit,restored.budget.used),(5,10))
        with self.assertRaises(PermissionError):restored.budget.reserve('new',1)

    def test_current_authority_must_retain_old_audit_observations(self):
        self.controller.audit.append({'kind':'observed-event','sequence':1})
        old=self.controller.snapshot();current=copy.deepcopy(old);current['audit']=[]
        with self.assertRaisesRegex(ValueError,'audit'):Controller.restore(old,current)

    def test_current_children_and_terminal_child_facts_are_preserved(self):
        self.controller.children={'child':'unknown'};old=self.controller.snapshot()
        restored=Controller.restore(old,self.controller.snapshot())
        self.assertEqual(restored.children,{'child':'unknown'})
        with self.assertRaises(ValueError):restored.succeed()
        current=copy.deepcopy(old);current['children']={}
        with self.assertRaisesRegex(ValueError,'lost a child'):Controller.restore(old,current)
        self.controller.children={'child':'completed'};old=self.controller.snapshot()
        current=copy.deepcopy(old);current['children']['child']='running'
        with self.assertRaisesRegex(ValueError,'terminal child'):Controller.restore(old,current)

    def test_real_finite_target_receipt_cannot_disappear_during_recovery(self):
        authority=Authority();grant=authority.grant('u','t1','write','order1')
        target=Target(authority);receipt=target.accept(grant,'op',{'fixture':True},1,1)
        self.controller.required={'op'}
        self.controller.admit(Event('task','a1',1,1,'confirmed','op',receipt),target)
        old=self.controller.snapshot();current=copy.deepcopy(old);current['results']={}
        with self.assertRaisesRegex(ValueError,'result'):Controller.restore(old,current)
        self.assertEqual(target.effects,1)

    def test_original_state_recovery_and_input_copy_isolation_are_legal(self):
        self.controller.budget.reserve('op',3);s=self.controller.snapshot()
        restored=Controller.restore(s,s);self.assertEqual(restored.snapshot(),s)
        s['budget']['entries']['op']['ceiling']=10;s['audit'].append({'changed':True})
        self.assertEqual(restored.budget.entries['op'].ceiling,3);self.assertEqual(restored.audit,[])

    def test_snapshot_schema_types_sums_and_success_join_are_checked(self):
        base=self.controller.snapshot()
        mutations=[]
        for field,value in [('epoch',True),('epoch',0),('plan','1'),('status','made-up')]:
            m=copy.deepcopy(base);m[field]=value;mutations.append(m)
        m=copy.deepcopy(base);m['budget']['used']=1;mutations.append(m)
        m=copy.deepcopy(base);m['status']='succeeded';m['children']={'child':'unknown'};mutations.append(m)
        m=copy.deepcopy(base);m['budget']['unexpected']=True;mutations.append(m)
        for current in mutations:
            with self.subTest(current=current),self.assertRaises((ValueError,TypeError)):
                Controller.restore(base,current)


if __name__=='__main__':unittest.main()
