import hashlib
import hmac
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'examples'))
from runtime_protocol.contracts import (LengthFramer,frame,SSEFixture,local_candidates,
    explicit_datetime,generated_daily,calendar_set,verify_webhook,DurableFixture,
    fingerprint,atomic_publish,replay)

class WireTests(unittest.TestCase):
    def test_every_short_partition(self):
        data=frame(b'\xe4\xb8\xad')+frame(b'')+frame(b'a')
        # Every choice of split points, not just every single split.
        for mask in range(1<<(len(data)-1)):
            parser=LengthFramer(4);out=[];last=0
            for i in range(1,len(data)):
                if mask&(1<<(i-1)):out+=parser.feed(data[last:i]);last=i
            out+=parser.feed(data[last:]);parser.finish()
            self.assertEqual([b'\xe4\xb8\xad',b'',b'a'],out)
    def test_incomplete_and_bad_length(self):
        for data in [b'\0',frame(b'abc')[:-1]]:
            p=LengthFramer();p.feed(data)
            with self.assertRaises(ValueError):p.finish()
        p=LengthFramer(4)
        with self.assertRaises(ValueError):p.feed((2**32-1).to_bytes(4,'big'))
        with self.assertRaises(ValueError):p.feed(frame(b'a'))
    def test_maximum_legal_and_concatenated_budget(self):
        p=LengthFramer(3);self.assertEqual([b'abc']*100,p.feed(frame(b'abc')*100));p.finish()
    def test_sse_boundaries_empty_id_and_unterminated_tail(self):
        raw='id: 9\r\ndata: 中\r\n\r\nid:\ndata: next\n\ndata: lost'.encode()
        p=SSEFixture()
        for b in raw:p.feed(bytes([b]))
        p.finish();self.assertEqual([('9','中'),('','next')],p.events)
    def test_sse_budget_and_legal_zero_length_frame(self):
        p=SSEFixture(12)
        with self.assertRaises(ValueError):p.feed(b'data: '+b'x'*20)
        p=LengthFramer(0);self.assertEqual([b''],p.feed(frame(b'')));p.finish()
        with self.assertRaises(ValueError):LengthFramer(-1)

class CalendarTests(unittest.TestCase):
    def test_fold_and_explicit_gap(self):
        fold=datetime(2024,11,3,1,30);gap=datetime(2024,3,10,2,30)
        self.assertEqual([datetime(2024,11,3,5,30,tzinfo=timezone.utc),datetime(2024,11,3,6,30,tzinfo=timezone.utc)],local_candidates(fold,'America/New_York'))
        self.assertEqual(datetime(2024,11,3,5,30,tzinfo=timezone.utc),explicit_datetime(fold,'America/New_York'))
        self.assertEqual([],local_candidates(gap,'America/New_York'))
        self.assertEqual(datetime(2024,3,10,7,30,tzinfo=timezone.utc),explicit_datetime(gap,'America/New_York'))
    def test_generated_gap_ignored_not_counted(self):
        actual=generated_daily(datetime(2024,3,9,2,30),'America/New_York',3)
        expected=[datetime(2024,3,9,7,30,tzinfo=timezone.utc),datetime(2024,3,11,6,30,tzinfo=timezone.utc),datetime(2024,3,12,6,30,tzinfo=timezone.utc)]
        self.assertEqual(expected,actual)
        self.assertNotIn(explicit_datetime(datetime(2024,3,10,2,30),'America/New_York'),actual)
    def test_union_exclusion_and_utc_neighbor(self):
        vals=generated_daily(datetime(2024,2,28,12),'UTC',3)
        self.assertEqual([28,29,1],[d.day for d in vals])
        self.assertEqual([vals[0],vals[2]],calendar_set(vals,[vals[0]],[vals[1]]))
    def test_fixture_rejects_invalid_profile(self):
        with self.assertRaises(ValueError):generated_daily(datetime(2024,3,10,2,30),'America/New_York',3)
        with self.assertRaises(ValueError):generated_daily(datetime(2024,1,1),'UTC',101)

class EffectTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'db.sqlite';self.f=DurableFixture(self.path)
    def tearDown(self):self.f.close();self.tmp.cleanup()
    def test_older_unknown_survives_new_not_applied(self):
        self.f.begin_attempt('t:x',{'n':1},'a1');self.f.attempt_result('t:x','a1','unknown')
        self.f.begin_attempt('t:x',{'n':1},'a2');self.f.attempt_result('t:x','a2','not_applied')
        self.assertEqual('unknown',self.f.state('t:x'))
        with self.assertRaises(ValueError):self.f.resolve_local_operation('t:x',['a2'],True,False)
        with self.assertRaises(ValueError):self.f.resolve_local_operation('t:x',['a1','a2'],False,False)
        self.f.resolve_local_operation('t:x',['a1','a2'],True,True)
        self.assertEqual('succeeded',self.f.state('t:x'))
    def test_late_failure_does_not_regress_success(self):
        self.f.begin_attempt('x',{},'old');self.f.resolve_local_operation('x',['old'],True,True)
        self.f.attempt_result('x','old','not_applied');self.assertEqual('succeeded',self.f.state('x'))
    def test_payload_and_tenant_scope(self):
        self.f.begin_attempt('tenant1:x',{'v':1},'a')
        with self.assertRaises(ValueError):self.f.begin_attempt('tenant1:x',{'v':2},'b')
        self.f.begin_attempt('tenant2:x',{'v':1},'a')
        self.assertNotEqual(fingerprint({'v':None}),fingerprint({}))
    def test_target_fence_installed_before_new_business_write(self):
        self.f.install_fence('actor',1);self.f.register_target_contract('x',{},10,12)
        self.f.install_fence('actor',2)
        with self.assertRaises(ValueError):self.f.apply_target('x',{},'actor',1,2)
        self.assertEqual(0,self.f.db.execute('select count(*) from effects').fetchone()[0])
        self.f.apply_target('x',{},'actor',2,2)
    def test_target_deadline_prevents_expired_key_late_effect(self):
        self.f.install_fence('actor',1);self.f.register_target_contract('x',{'n':1},10,12)
        a=self.f.apply_target('x',{'n':1},'actor',1,8)
        self.assertEqual(a,self.f.apply_target('x',{'n':1},'actor',1,9))
        with self.assertRaises(ValueError):self.f.apply_target('x',{'n':1},'actor',1,13)
        self.assertEqual(1,self.f.db.execute('select count(*) from effects').fetchone()[0])
    def test_late_window_negative_control_and_legal_retry(self):
        sent_at,expires,arrives=9,10,11
        unsafe_client_allows_retry=sent_at<=expires
        unsafe_effects=1+int(unsafe_client_allows_retry and arrives>expires)
        self.assertEqual(2,unsafe_effects)
        self.f.install_fence('actor',1);self.f.register_target_contract('x',{},10,10)
        first=self.f.apply_target('x',{},'actor',1,9)
        self.assertEqual(first,self.f.apply_target('x',{},'actor',1,10))
        with self.assertRaises(ValueError):self.f.apply_target('x',{},'actor',1,11)
    def test_two_real_processes_target_same_intent(self):
        self.f.install_fence('actor',1);self.f.register_target_contract('x',{},10,12)
        code="import sys;from runtime_protocol.contracts import DurableFixture;f=DurableFixture(sys.argv[1]);print(f.apply_target('x',{},'actor',1,2));f.close()"
        env=dict(os.environ,PYTHONPATH=str(ROOT/'examples'))
        processes=[subprocess.Popen([sys.executable,'-c',code,str(self.path)],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE) for _ in range(2)]
        results=[p.communicate(timeout=5) for p in processes]
        self.assertTrue(all(p.returncode==0 for p in processes),results)
        self.assertEqual(results[0][0],results[1][0])
        self.assertEqual(1,self.f.db.execute('select count(*) from effects').fetchone()[0])
    def test_independent_current_targets_and_wrong_payload(self):
        for t in ['entity1','entity2']:
            self.f.install_fence(t,1);self.f.register_target_contract(t,{},10,11,target=t)
            self.f.apply_target(t,{},t,1,1)
        self.assertEqual(2,self.f.db.execute('select count(*) from effects').fetchone()[0])
        with self.assertRaises(ValueError):self.f.apply_target('entity1',{'extra':1},'entity1',1,2)
        with self.assertRaises(ValueError):self.f.apply_target('entity1',{},'entity2',1,2)
    def test_process_exit_after_sqlite_commit(self):
        self.f.close()
        code="import os,sys;from runtime_protocol.contracts import DurableFixture;f=DurableFixture(sys.argv[1]);f.begin_attempt('x',{},'a');os._exit(17)"
        env=dict(os.environ,PYTHONPATH=str(ROOT/'examples'))
        result=subprocess.run([sys.executable,'-c',code,str(self.path)],env=env,capture_output=True,timeout=5)
        self.assertEqual(17,result.returncode)
        self.f=DurableFixture(self.path);self.assertEqual('dispatching',self.f.state('x'))
    def test_fingerprint_rejects_non_json_and_cycles(self):
        cycle=[];cycle.append(cycle)
        for value in [float('nan'),(1,2),{1:'key'},cycle]:
            with self.assertRaises(ValueError):fingerprint(value)
        self.assertEqual(fingerprint({'a':1,'b':2}),fingerprint({'b':2,'a':1}))

class FileTests(unittest.TestCase):
    def test_real_process_interruption_visibility(self):
        with tempfile.TemporaryDirectory() as directory:
            dest=Path(directory)/'input';dest.write_bytes(b'OLD')
            env=dict(os.environ,PYTHONPATH=str(ROOT/'examples'))
            code="import sys;from runtime_protocol.contracts import atomic_publish;atomic_publish(sys.argv[1],'input',b'NEW',sys.argv[2])"
            for point,exitcode,expected in [('before_publish',21,b'OLD'),('after_publish',22,b'NEW')]:
                r=subprocess.run([sys.executable,'-c',code,directory,point],env=env,capture_output=True,timeout=5)
                self.assertEqual(exitcode,r.returncode);self.assertEqual(expected,dest.read_bytes())
    def test_publish_and_path_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(hashlib.sha256(b'OK').hexdigest(),atomic_publish(directory,'input',b'OK'))
            with self.assertRaises(ValueError):atomic_publish(directory,'../outside',b'BAD')

class WebhookAndReplayTests(unittest.TestCase):
    def test_signature_covers_bytes_not_delivery_header(self):
        body=b'{"id":1}';key=b'synthetic';sig='sha256='+hmac.new(key,body,hashlib.sha256).hexdigest()
        self.assertTrue(verify_webhook(body,key,sig));self.assertFalse(verify_webhook(body+b' ',key,sig))
        for delivery in ['original','attacker-changed']:
            self.assertTrue(verify_webhook(body,key,sig))
            self.assertIsInstance(delivery,str)
    def test_replay_identity_and_float_boundary(self):
        identity={'initial':fingerprint(1),'rules':'integer-add-v1','content':'fixture-v1'}
        self.assertEqual([1,3,6],replay(identity,1,[2,3]))
        with self.assertRaises(ValueError):replay(identity,2,[2,3])
        with self.assertRaises(ValueError):replay(dict(identity,rules='other'),1,[2,3])
        with self.assertRaises(ValueError):replay(identity,1,[0.1])
        self.assertNotEqual((1e16+-1e16)+1,1e16+(-1e16+1))

class ProcessTests(unittest.TestCase):
    def run_fixture(self,*args):
        return subprocess.run([sys.executable,str(ROOT/'examples/runtime_protocol/cli_fixture.py'),*args],input=b'',capture_output=True,timeout=5)
    def test_argv_streams_exit_and_legal_neighbor(self):
        args=['with space','中',';touch marker','--config=evil','']
        r=self.run_fixture('--json','--',*args)
        self.assertEqual(0,r.returncode);self.assertEqual(args,json.loads(r.stdout)['argv']);self.assertEqual(b'diagnostic\n',r.stderr)
        bad=self.run_fixture('--unknown');self.assertEqual(2,bad.returncode);self.assertEqual(b'',bad.stdout)
        help_result=self.run_fixture('--help');self.assertEqual(0,help_result.returncode)
    def test_both_pipes_drained_and_business_failure(self):
        r=self.run_fixture('--large');self.assertEqual(0,r.returncode)
        self.assertEqual(524288,len(r.stdout));self.assertEqual(524288,len(r.stderr))
        r=self.run_fixture('--fail');self.assertEqual(2,r.returncode);self.assertNotEqual(b'',r.stderr)
    def test_optimized_public_entry_rejected(self):
        for mode in ['-O','-OO']:
            r=subprocess.run([sys.executable,mode,str(ROOT/'examples/runtime_protocol/cli_fixture.py'),'--help'],capture_output=True,timeout=5)
            self.assertEqual(2,r.returncode)

if __name__=='__main__':unittest.main()
