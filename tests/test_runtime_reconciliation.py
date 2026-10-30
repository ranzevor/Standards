"""Real SQLite closure/retry, audit identity, rollback and concurrent coverage tests."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'examples'))
from runtime_protocol.contracts import DurableFixture


class RuntimeReconciliation(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'operation.sqlite'
        self.fixture=DurableFixture(self.path)

    def tearDown(self):
        self.fixture.close();self.temp.cleanup()

    def unknown(self,key='op',attempt='a1'):
        self.fixture.begin_attempt(key,{'n':1},attempt)
        self.fixture.attempt_result(key,attempt,'unknown')

    def attempts(self,key='op'):
        return self.fixture.db.execute('SELECT a,state FROM attempts WHERE k=? ORDER BY a',(key,)).fetchall()

    def events(self,key='op'):
        return self.fixture.db.execute('SELECT id,applied,prior_operation_state,prior_attempts_json,covered_attempts_json FROM reconciliation_events WHERE k=? ORDER BY id',(key,)).fetchall()

    def test_terminal_absence_then_legal_retry_and_definitive_failure(self):
        self.unknown();event=self.fixture.resolve_local_operation('op',['a1'],True,False)
        self.assertEqual(self.fixture.state('op'),'failed_known');self.assertEqual(self.attempts(),[('a1','not_applied')])
        self.fixture.begin_attempt('op',{'n':1},'a2');self.assertEqual(self.fixture.state('op'),'dispatching')
        self.fixture.attempt_result('op','a2','not_applied');self.assertEqual(self.fixture.state('op'),'failed_known')
        record=self.events()[0];self.assertEqual(record[0],event);self.assertEqual(record[1],0)
        self.assertEqual(json.loads(record[3]),[['a1','unknown']]);self.assertEqual(json.loads(record[4]),['a1'])

    def test_new_genuinely_unknown_attempt_stays_unknown(self):
        self.unknown();self.fixture.resolve_local_operation('op',['a1'],True,False)
        self.fixture.begin_attempt('op',{'n':1},'a2');self.fixture.attempt_result('op','a2','unknown')
        self.assertEqual(self.fixture.state('op'),'unknown')
        with self.assertRaises(ValueError):self.fixture.resolve_local_operation('op',['a1'],True,False)
        self.assertEqual(self.fixture.state('op'),'unknown');self.assertEqual(len(self.events()),1)

    def test_terminal_absence_then_actual_target_commit_and_known_success(self):
        self.unknown();self.fixture.resolve_local_operation('op',['a1'],True,False)
        self.fixture.begin_attempt('op',{'n':1},'a2')
        self.fixture.install_fence('actor',1);self.fixture.register_target_contract('op',{'n':1},10,12)
        result=self.fixture.apply_target('op',{'n':1},'actor',1,2)
        self.assertIsInstance(result,int)
        self.fixture.resolve_local_operation('op',['a2','a1'],True,True)
        self.assertEqual(self.fixture.state('op'),'succeeded');self.assertEqual(len(self.events()),2)
        self.assertEqual(self.fixture.db.execute('SELECT count(*) FROM effects WHERE k=?',('op',)).fetchone()[0],1)
        self.fixture.attempt_result('op','a2','not_applied');self.assertEqual(self.fixture.state('op'),'succeeded')
        with self.assertRaises(ValueError):self.fixture.resolve_local_operation('op',['a1','a2'],True,False)
        self.assertEqual(self.fixture.state('op'),'succeeded')

    def test_restart_preserves_closed_attempts_and_original_unknown_audit(self):
        self.unknown();self.fixture.resolve_local_operation('op',['a1'],True,False)
        before=self.events();self.fixture.close();self.fixture=DurableFixture(self.path)
        self.assertEqual(self.events(),before);self.assertEqual(json.loads(self.events()[0][3]),[['a1','unknown']])
        self.fixture.begin_attempt('op',{'n':1},'a2');self.assertEqual(self.fixture.state('op'),'dispatching')
        self.fixture.attempt_result('op','a2','not_applied');self.assertEqual(self.fixture.state('op'),'failed_known')

    def test_late_old_unknown_cannot_reopen_closed_attempt(self):
        self.unknown();self.fixture.resolve_local_operation('op',['a1'],True,False)
        self.fixture.begin_attempt('op',{'n':1},'a2')
        with self.assertRaises(ValueError):self.fixture.attempt_result('op','a1','unknown')
        self.assertEqual(self.fixture.state('op'),'dispatching');self.assertEqual(len(self.events()),1)

    def test_failed_reconciliation_rolls_back_event_and_all_state_changes(self):
        self.unknown()
        self.fixture.db.execute("CREATE TEMP TRIGGER reject_reconcile BEFORE UPDATE OF state ON attempts WHEN NEW.state='not_applied' BEGIN SELECT RAISE(ABORT,'synthetic update fault'); END")
        with self.assertRaisesRegex(sqlite3.IntegrityError,'synthetic update fault'):
            self.fixture.resolve_local_operation('op',['a1'],True,False)
        self.assertEqual(self.fixture.state('op'),'unknown');self.assertEqual(self.attempts(),[('a1','unknown')]);self.assertEqual(self.events(),[])
        self.fixture.db.execute('DROP TRIGGER reject_reconcile')
        self.fixture.resolve_local_operation('op',['a1'],True,False)
        self.assertEqual(self.fixture.state('op'),'failed_known');self.assertEqual(len(self.events()),1)

    def test_automatic_sqlite_rollback_preserves_primary_failure(self):
        self.unknown()
        self.fixture.db.execute("CREATE TEMP TRIGGER rollback_reconcile BEFORE UPDATE OF state ON attempts BEGIN SELECT RAISE(ROLLBACK,'synthetic transaction fault'); END")
        with self.assertRaisesRegex(sqlite3.IntegrityError,'synthetic transaction fault'):
            self.fixture.resolve_local_operation('op',['a1'],True,False)
        self.assertFalse(self.fixture.db.in_transaction);self.assertEqual(self.fixture.state('op'),'unknown');self.assertEqual(self.events(),[])

    def test_incomplete_duplicate_or_unclosed_evidence_does_not_change_unknown(self):
        self.unknown();self.fixture.begin_attempt('op',{'n':1},'a2')
        for covered,closed,applied in [(['a1'],True,False),(['a1','a1','a2'],True,False),(['a1','a2'],False,False),(['a1','a2'],'yes',False),(['a1','a2'],True,0)]:
            with self.subTest(covered=covered,closed=closed,applied=applied),self.assertRaises(ValueError):
                self.fixture.resolve_local_operation('op',covered,closed,applied)
        self.assertEqual(self.fixture.state('op'),'unknown');self.assertEqual(self.events(),[])
        with self.assertRaises(ValueError):self.fixture.resolve_local_operation('missing',[],True,False)

    def test_other_operation_unknown_is_not_resolved_by_this_closure(self):
        self.unknown();self.unknown('other','a1');self.fixture.resolve_local_operation('op',{'a1'},True,False)
        self.assertEqual(self.fixture.state('op'),'failed_known');self.assertEqual(self.fixture.state('other'),'unknown')
        self.assertEqual(self.events('other'),[])

    def test_concurrent_new_attempt_cannot_be_silently_covered_by_old_snapshot(self):
        for index in range(4):
            key='race-'+str(index);self.unknown(key);barrier=threading.Barrier(3,timeout=5)
            def act(kind):
                f=DurableFixture(self.path)
                try:
                    barrier.wait()
                    if kind=='begin':f.begin_attempt(key,{'n':1},'a2');return 'begun'
                    try:f.resolve_local_operation(key,['a1'],True,False);return 'resolved'
                    except ValueError:return 'stale-coverage-rejected'
                finally:f.close()
            with ThreadPoolExecutor(max_workers=2) as pool:
                begin=pool.submit(act,'begin');resolve=pool.submit(act,'resolve');barrier.wait()
                self.assertEqual(begin.result(timeout=5),'begun');result=resolve.result(timeout=5)
            if result=='resolved':
                self.assertEqual(self.fixture.state(key),'dispatching');self.assertEqual(len(self.events(key)),1)
            else:
                self.assertEqual(result,'stale-coverage-rejected');self.assertEqual(self.fixture.state(key),'unknown');self.assertEqual(self.events(key),[])

    def test_legacy_operation_label_does_not_fabricate_missing_closure_evidence(self):
        self.unknown();self.fixture.db.execute("UPDATE operations SET state='failed_known' WHERE k='op'")
        self.fixture.close();self.fixture=DurableFixture(self.path)
        self.assertEqual(self.events(),[])
        self.fixture.begin_attempt('op',{'n':1},'a2');self.assertEqual(self.fixture.state('op'),'unknown')
        self.fixture.resolve_local_operation('op',['a1','a2'],True,False)
        self.assertEqual(self.fixture.state('op'),'failed_known');self.assertEqual(len(self.events()),1)


if __name__=='__main__':
    unittest.main()
