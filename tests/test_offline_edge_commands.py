"""Finite queued admission and observation cases; no device, durable ledger or real clock."""
from dataclasses import replace
from pathlib import Path
import hashlib,importlib.util,sys,threading,unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('offline_edge_model',ROOT/'examples/security-edge-commerce/models.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)

class Fixture(unittest.TestCase):
    def setUp(self):
        self.p=m.Principal('synthetic-issuer','device-controller','tenant-a')
        self.grants={(self.p,'sensor-a','measure'),(self.p,'sensor-b','measure')}
        self.gate=m.ResourceGate(1,self.grants);self.queue=m.OfflineCommandQueue(self.gate,1,100)
    def command(self,name='intent-a',**kw):
        fields=dict(command_id=name,principal=self.p,resource='sensor-a',action='measure',epoch=1,not_before=2,expires_at=100,payload_digest=hashlib.sha256(b'synthetic-command').hexdigest());fields.update(kw);return m.QueuedCommand(**fields)

class OfflineQueueCases(Fixture):
    def test_normal_then_duplicate_only_returns_historical_receipt(self):
        c=self.command();self.assertEqual(self.queue.execute(c,(10,10))['state'],'executed')
        r=self.queue.execute(c,(200,200));self.assertEqual(r['state'],'executed');self.assertTrue(r['historical_only']);self.assertEqual(len(self.gate.effects),1)
    def test_expired_on_reconnection_does_not_execute(self):
        r=self.queue.execute(self.command(),(100,100),connected=True,synchronized=True)
        self.assertEqual((r['state'],r['reason']),('refused','expired'));self.assertFalse(self.gate.effects)
    def test_expiry_uncertainty_is_not_success(self):
        r=self.queue.execute(self.command(),(99,101));self.assertEqual(r['state'],'held');self.assertFalse(self.gate.effects)
    def test_last_certain_valid_instant_is_legal(self):
        self.assertEqual(self.queue.execute(self.command(),(99,99))['state'],'executed')
    def test_unknown_clock_does_not_renew_original_deadline(self):
        c=self.command();self.assertEqual(self.queue.execute(c,None)['state'],'held')
        self.assertEqual(self.queue.execute(c,(101,101))['reason'],'expired');self.assertFalse(self.gate.effects)
    def test_queued_intent_parameter_drift_is_rejected_before_effect(self):
        c=self.command();self.queue.execute(c,None)
        with self.assertRaisesRegex(m.ContractError,'parameter drift'):self.queue.execute(replace(c,expires_at=200),(10,10))
        self.assertFalse(self.gate.effects)
    def test_independent_low_risk_intents_may_have_equal_parameters(self):
        self.queue.execute(self.command('first'),(10,10));self.queue.execute(self.command('second'),(10,10));self.assertEqual(len(self.gate.effects),2)
    def test_unknown_ack_keeps_old_attempt_unknown_and_does_not_reexecute(self):
        c=self.command();r=self.queue.execute(c,(10,10),acknowledgement_lost=True);self.assertEqual(r['state'],'unknown')
        again=self.queue.execute(c,(11,11));self.assertEqual(again['state'],'unknown');self.assertTrue(again['historical_only']);self.assertEqual(len(self.gate.effects),1)
    def test_wrong_object_tenant_and_action_have_no_effect(self):
        variants=[{'resource':'other'}, {'action':'write'}, {'principal':m.Principal('synthetic-issuer','device-controller','tenant-b')}]
        for n,fields in enumerate(variants):
            with self.subTest(fields=fields):self.assertEqual(self.queue.execute(self.command(str(n),**fields),(10,10))['state'],'refused')
        self.assertFalse(self.gate.effects)
    def test_same_intent_concurrency_has_one_in_process_effect(self):
        c=self.command();barrier=threading.Barrier(9);out=[]
        def run():barrier.wait();out.append(self.queue.execute(c,(10,10)))
        threads=[threading.Thread(target=run)for _ in range(8)]
        for t in threads:t.start()
        barrier.wait()
        for t in threads:t.join(timeout=5);self.assertFalse(t.is_alive())
        self.assertEqual(len(out),8);self.assertEqual(len(self.gate.effects),1);self.assertEqual(sum(not r['historical_only']for r in out),1)
    def test_invalid_time_types_and_order_are_rejected(self):
        for i,value in enumerate([(True,10),(10,False),(11,10),[10,10],(-1,10)]):
            with self.subTest(value=value),self.assertRaises(m.ContractError):self.queue.execute(self.command(str(i)),value)
        self.assertFalse(self.gate.effects)

class OfflineAuthorityCases(Fixture):
    def test_bounded_offline_lease_does_not_claim_unobserved_revocation_is_installed(self):
        # A remote controller could already have advanced; this device has not observed it.
        r=self.queue.execute(self.command(),(10,10));self.assertEqual(r['state'],'executed')
        self.assertEqual((r['installed_epoch'],r['authority_as_of']),(1,1));self.assertIs(r['all_revocations_propagated'],False)
    def test_reconnect_before_control_sync_is_held(self):
        r=self.queue.execute(self.command(),(10,10),connected=True,synchronized=False)
        self.assertEqual(r['reason'],'reconnect-needs-control-sync');self.assertFalse(self.gate.effects)
    def test_observed_fence_rejects_old_and_accepts_current_scoped_command(self):
        self.queue.install_control(2,self.grants,10)
        old=self.queue.execute(self.command('old'),(11,11),connected=True,synchronized=True)
        new=self.queue.execute(self.command('new',epoch=2,resource='sensor-b'),(11,11),connected=True,synchronized=True)
        self.assertEqual((old['reason'],new['state']),('stale-target-epoch','executed'));self.assertEqual(len(self.gate.effects),1)
    def test_unobserved_or_old_control_cannot_renew_lease(self):
        self.queue.install_control(2,self.grants,10)
        r=self.queue.execute(self.command(epoch=2),(11,11));self.assertEqual(r['reason'],'offline-lease-epoch')
        with self.assertRaises(m.ContractError):self.queue.install_control(1,self.grants,11,200)
        self.assertEqual((self.queue.offline_until,self.queue.lease_epoch),(100,1))
    def test_explicit_current_lease_and_current_parallel_objects_are_legal(self):
        self.queue.install_control(2,self.grants,10,200)
        for name in ['sensor-a','sensor-b']:
            self.assertEqual(self.queue.execute(self.command(name,epoch=2,resource=name),(20,20))['state'],'executed')
        self.assertEqual(len(self.gate.effects),2)
    def test_expired_lease_and_uncertain_lease_boundary_do_not_execute(self):
        for name,window,reason in [('expired',(100,100),'offline-lease-expired'),('uncertain',(99,100),'offline-lease-time-uncertain')]:
            with self.subTest(name=name):
                c=self.command(name,expires_at=200);r=self.queue.execute(c,window);self.assertEqual(r['reason'],reason)
        self.assertFalse(self.gate.effects)
    def test_clock_before_observation_is_unknown_not_new_authority(self):
        self.queue.install_control(2,self.grants,10,200)
        r=self.queue.execute(self.command(epoch=2),(5,5));self.assertEqual(r['reason'],'clock-before-control-observation');self.assertFalse(self.gate.effects)
    def test_grant_revocation_requires_new_epoch_and_denies_old_principal(self):
        with self.assertRaises(m.ContractError):self.queue.install_control(1,set(),10)
        self.queue.install_control(2,set(),10,200)
        self.assertEqual(self.queue.execute(self.command(epoch=2),(11,11))['reason'],'object-action-not-granted');self.assertFalse(self.gate.effects)
    def test_historical_receipt_is_not_reauthorized_after_fence(self):
        c=self.command();self.queue.execute(c,(10,10));self.queue.install_control(2,set(),11)
        r=self.queue.execute(c,(12,12),connected=True,synchronized=True)
        self.assertTrue(r['historical_only']);self.assertEqual(r['installed_epoch'],1);self.assertEqual(len(self.gate.effects),1)
    def test_epoch_and_flags_do_not_accept_python_boolean_aliases(self):
        with self.assertRaises(m.ContractError):self.command(epoch=True)
        with self.assertRaises(m.ContractError):m.ResourceGate(True,self.grants)
        with self.assertRaises(m.ContractError):self.gate.execute(self.p,'sensor-a','measure',True)
        with self.assertRaises(m.ContractError):self.queue.execute(self.command(),(10,10),connected=1)
        self.assertFalse(self.gate.effects)

if __name__=='__main__':unittest.main()
