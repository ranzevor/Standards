"""Executed local SQLite delivery-progress contract, not an external CDC connector."""
import copy
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest

from checks.database_examples import ContractError, apply_event, event_identity, init_store


class CDCProgress(unittest.TestCase):
    STREAM = 'synthetic-topic-generation-1/partition-0'

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'cdc.sqlite'
        self.db = self.connect()
        init_store(self.db)
        self.db.execute('INSERT INTO lease VALUES(?,?,?)', (self.STREAM, 1, 5))
        self.db.executescript('''
          CREATE TABLE effect_observations(kind TEXT NOT NULL);
          CREATE TRIGGER observe_insert AFTER INSERT ON target BEGIN
            INSERT INTO effect_observations VALUES('insert'); END;
          CREATE TRIGGER observe_update AFTER UPDATE ON target BEGIN
            INSERT INTO effect_observations VALUES('update'); END;
        ''')

    def connect(self):
        db = sqlite3.connect(self.path, isolation_level=None, timeout=2)
        db.execute('PRAGMA foreign_keys=ON')
        self.addCleanup(db.close)
        return db

    def event(self, **updates):
        event = dict(source='synthetic-source', generation='timeline-1', transaction='tx-1',
                     record='record-1', table='orders', tenant='tenant-1', key='42',
                     version=1, epoch=1, op='upsert', value={'status': 'accepted'}, lsn='0/ABC')
        event.update(updates)
        return event

    def apply(self, predecessor=5, next_cursor=17, event=None, fail_at=None, db=None):
        return apply_event(db or self.db, self.event() if event is None else event,
                           self.STREAM, predecessor, next_cursor, fail_at)

    def cursor(self):
        return self.db.execute('SELECT cursor FROM lease WHERE stream=?', (self.STREAM,)).fetchone()[0]

    def state(self):
        return {table: self.db.execute('SELECT * FROM ' + table + ' ORDER BY 1,2').fetchall()
                for table in ('lease', 'inbox', 'target', 'delivery_progress')} | {
                    'effects': self.db.execute('SELECT kind FROM effect_observations ORDER BY rowid').fetchall()}

    def test_same_source_event_at_new_delivery_position_advances_cursor_once(self):
        self.assertEqual(self.apply(), 'applied')
        self.assertEqual(self.apply(17, 18), 'duplicate')
        self.assertEqual(self.cursor(), 18)
        self.assertEqual(self.db.execute('SELECT count(*) FROM inbox').fetchone()[0], 1)
        self.assertEqual(self.db.execute('SELECT kind FROM effect_observations').fetchall(), [('insert',)])
        self.assertEqual(self.db.execute('SELECT predecessor,next_cursor FROM delivery_progress ORDER BY predecessor').fetchall(), [(5, 17), (17, 18)])
        self.assertEqual(self.apply(18, 19, self.event(record='record-2', version=2)), 'applied')
        self.assertEqual(self.cursor(), 19)

    def test_exact_old_ack_replay_is_legal_after_later_progress(self):
        self.apply(); self.apply(17, 23, self.event(record='record-2', version=2))
        before = self.state()
        self.assertEqual(self.apply(), 'duplicate')
        self.assertEqual(self.state(), before)

    def test_lost_initial_ack_reopens_committed_receipt_not_an_unknown_gap(self):
        with self.assertRaisesRegex(RuntimeError, 'lost client'):
            self.apply(fail_at='after-commit')
        reopened = self.connect()
        self.assertEqual(self.apply(db=reopened), 'duplicate')
        self.assertEqual(self.cursor(), 17)
        self.assertEqual(len(self.state()['effects']), 1)

    def test_current_epoch_replay_preserves_source_identity_and_progress(self):
        self.apply()
        self.db.execute('UPDATE lease SET epoch=2 WHERE stream=?', (self.STREAM,))
        current = self.event(epoch=2)
        self.assertEqual(self.apply(event=current), 'duplicate')
        self.assertEqual(self.apply(17, 30, current), 'duplicate')
        self.assertEqual(self.cursor(), 30)
        self.assertEqual(len(self.state()['inbox']), 1)
        self.assertEqual(len(self.state()['effects']), 1)

    def test_stale_epoch_is_fenced_even_for_an_already_known_event(self):
        self.apply(); self.db.execute('UPDATE lease SET epoch=2 WHERE stream=?', (self.STREAM,))
        before = self.state()
        for predecessor, successor in ((5, 17), (17, 18)):
            with self.subTest(predecessor=predecessor), self.assertRaisesRegex(ContractError, 'stale writer'):
                self.apply(predecessor, successor)
            self.assertEqual(self.state(), before)

    def test_same_source_identity_changed_content_is_not_delivery_metadata(self):
        self.apply(); before = self.state()
        for update in ({'value': {'status': 'changed'}}, {'version': 2}, {'lsn': '0/DEF'},
                       {'value': {'status': True}}, {'additional_source_field': 'changed'}):
            with self.subTest(update=update), self.assertRaisesRegex(ContractError, 'different payload'):
                self.apply(17, 18, self.event(**update))
            self.assertEqual(self.state(), before)

    def test_rebound_committed_position_or_range_is_rejected(self):
        self.apply(); before = self.state()
        for successor, event in ((18, self.event()), (17, self.event(record='different-record'))):
            with self.subTest(successor=successor), self.assertRaises(ContractError):
                self.apply(5, successor, event)
            self.assertEqual(self.state(), before)

    def test_gap_and_unrecorded_overlap_are_not_deduced_from_event_deduplication(self):
        self.apply(); before = self.state()
        for predecessor, successor in ((18, 19), (6, 17), (6, 18), (4, 5)):
            with self.subTest(predecessor=predecessor), self.assertRaisesRegex(ContractError, 'cursor chain'):
                self.apply(predecessor, successor)
            self.assertEqual(self.state(), before)

    def test_nonconsecutive_cursor_is_legal_but_nonadvancing_is_not(self):
        self.apply(5, 1000)
        self.assertEqual(self.apply(1000, 100000), 'duplicate')
        before = self.state()
        for successor in (100000, 99999):
            with self.assertRaises(ContractError): self.apply(100000, successor)
            self.assertEqual(self.state(), before)

    def test_duplicate_new_progress_precommit_faults_are_atomic(self):
        self.apply(); before = self.state()
        for stage in ('after-inbox', 'after-target', 'before-commit'):
            with self.subTest(stage=stage), self.assertRaisesRegex(RuntimeError, 'injected'):
                self.apply(17, 18, fail_at=stage)
            self.assertFalse(self.db.in_transaction)
            self.assertEqual(self.state(), before)
        self.assertEqual(self.apply(17, 18), 'duplicate')
        self.assertEqual(self.cursor(), 18)

    def test_duplicate_new_progress_lost_ack_is_reconciled_by_exact_delivery_receipt(self):
        self.apply()
        with self.assertRaisesRegex(RuntimeError, 'lost client'):
            self.apply(17, 18, fail_at='after-commit')
        before = self.state()
        self.assertEqual(self.apply(17, 18, db=self.connect()), 'duplicate')
        self.assertEqual(self.state(), before)
        self.assertEqual(self.cursor(), 18)
        self.assertEqual(len(before['effects']), 1)

    def test_two_connections_same_new_duplicate_delivery_commit_one_progress_receipt(self):
        self.apply(); self.db.execute('PRAGMA journal_mode=WAL')
        barrier = threading.Barrier(2); results = []; errors = []
        def worker():
            db = sqlite3.connect(self.path, isolation_level=None, timeout=2)
            db.execute('PRAGMA foreign_keys=ON')
            try:
                barrier.wait(timeout=2)
                results.append(self.apply(17, 18, db=db))
            except BaseException as error:
                errors.append(repr(error))
            finally:
                db.close()
        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads: thread.start()
        for thread in threads:
            thread.join(5); self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(results, ['duplicate', 'duplicate'])
        self.assertEqual(self.cursor(), 18)
        self.assertEqual(len(self.state()['delivery_progress']), 2)
        self.assertEqual(len(self.state()['effects']), 1)

    def test_new_event_failure_windows_remain_atomic(self):
        before = self.state()
        for stage in ('after-inbox', 'after-target', 'before-commit'):
            with self.subTest(stage=stage), self.assertRaises(RuntimeError): self.apply(fail_at=stage)
            self.assertEqual(self.state(), before)

    def test_nonfinite_or_nonjson_source_content_is_rejected_before_transaction(self):
        before = self.state()
        for value in (float('nan'), float('inf'), {1: 'non-string-key'}, {'bad': object()}):
            with self.subTest(value=repr(value)), self.assertRaises(ContractError):
                self.apply(event=self.event(value=value))
            self.assertFalse(self.db.in_transaction)
            self.assertEqual(self.state(), before)

    def test_caller_transaction_is_neither_committed_nor_rolled_back(self):
        self.db.execute('BEGIN'); self.db.execute("INSERT INTO outbox VALUES('local-intent','{}','pending')")
        with self.assertRaisesRegex(ContractError, 'caller transaction'): self.apply()
        self.assertTrue(self.db.in_transaction)
        self.db.rollback()
        self.assertEqual(self.db.execute('SELECT count(*) FROM outbox').fetchone()[0], 0)

    def test_independent_stream_can_receive_same_source_event_without_a_second_effect(self):
        self.apply(); other = 'synthetic-topic-generation-1/partition-1'
        self.db.execute('INSERT INTO lease VALUES(?,?,?)', (other, 9, 200))
        self.assertEqual(apply_event(self.db, self.event(epoch=9), other, 200, 250), 'duplicate')
        self.assertEqual(self.db.execute('SELECT cursor FROM lease WHERE stream=?', (other,)).fetchone()[0], 250)
        self.assertEqual(len(self.state()['effects']), 1)


if __name__ == '__main__': unittest.main(verbosity=2)
