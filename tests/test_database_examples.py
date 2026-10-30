import copy
from contextlib import closing
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from checks.database_examples import *

ROOT=Path(__file__).resolve().parents[1]

class FiniteModels(unittest.TestCase):
    def test_pg_settings_exact_enum_and_empty_sync_list(self):
        c={'fsync':True,'synchronous_commit':'on','synchronous_standby_names':''}
        self.assertEqual(durability_boundary('postgresql','18.2',c)['remote_stage'],'none')
        for mode in ('off','local','remote_write','on','remote_apply'):
            c.update(synchronous_commit=mode,synchronous_standby_names='ANY 1 (replica1,replica2)')
            self.assertEqual(durability_boundary('postgresql','18.2',c)['local_flush'],mode!='off')
        for bad in ('remote_flush','on - adopted','ON',None):
            c['synchronous_commit']=bad
            with self.assertRaises(ContractError):durability_boundary('postgresql','18',c)
        c['synchronous_commit']='on';c['fsync']=False
        with self.assertRaises(ContractError):durability_boundary('postgresql','18',c)
    def test_sqlite_journal_scope(self):
        self.assertFalse(durability_boundary('sqlite','3.45.0',{'journal_mode':'DELETE','synchronous':'FULL'})['powerloss_durability_policy'])
        for journal,mode in [('DELETE','EXTRA'),('WAL','FULL'),('WAL','EXTRA')]:
            result=durability_boundary('sqlite','3.45.0',{'journal_mode':journal,'synchronous':mode})
            self.assertTrue(result['powerloss_durability_policy']);self.assertEqual(result['device_durability'],'not-tested')
        for bad in ({'journal_mode':'MEMORY','synchronous':'FULL'},{'journal_mode':'WAL','synchronous':'almost-full'}):
            with self.assertRaises(ContractError):durability_boundary('sqlite','3.45.0',bad)
    def test_mysql_boolean_is_not_numeric_setting(self):
        good={'innodb_flush_log_at_trx_commit':1,'sync_binlog':1,'binary_logging':True}
        self.assertTrue(durability_boundary('mysql-innodb','8.4.3',good)['binlog_flush_policy'])
        good['innodb_flush_log_at_trx_commit']=True
        with self.assertRaises(ContractError):durability_boundary('mysql-innodb','8.4.3',good)
        with self.assertRaises(ContractError):durability_boundary('other','1',{})
    def test_dependency_closure_prevents_old_base_and_key_removal(self):
        assets={k:{'dependencies':deps,'available':True,'legal_hold':False,'retain_until':5} for k,deps in {'base':['key-v1','config'],'inc':['base','wal'],'point':['inc','deletion-ledger'],'key-v1':[],'config':[],'wal':[],'deletion-ledger':[],'orphan':[]}.items()}
        self.assertIn('key-v1',required_closure(assets,['point']))
        self.assertEqual(safe_prune(assets,['point'],['orphan'],5),['orphan'])
        for candidate in ('base','wal','config','key-v1','deletion-ledger','missing'):
            with self.assertRaises(ContractError):safe_prune(assets,['point'],[candidate],9)
        assets['orphan']['legal_hold']=True
        with self.assertRaises(ContractError):safe_prune(assets,['point'],['orphan'],9)
        assets['orphan']['legal_hold']=False;assets['orphan']['retain_until']=10
        with self.assertRaises(ContractError):safe_prune(assets,['point'],['orphan'],9)
        assets['key-v1']['available']=False
        with self.assertRaises(ContractError):required_closure(assets,['point'])
    def test_dependency_unknown_cycle_multi_entity_and_empty_roots(self):
        self.assertEqual(required_closure({},[]),set())
        with self.assertRaises(ContractError):required_closure({'a':{'available':True,'dependencies':['b']}},['a'])
        with self.assertRaises(ContractError):required_closure({'a':{'available':True,'dependencies':['a']}},['a'])
    def test_watermark_idle_resume_is_late_not_lossless(self):
        trace=watermark_trace([('slow',0,1),('fast',1,2),('fast',11,50),('slow',12,3)])
        self.assertEqual(trace['watermarks'],[1,1,50,50]);self.assertEqual(trace['late_side_output'],[('slow',3)])
        self.assertEqual(watermark_trace([('only',0,0)])['late_side_output'],[])
        with self.assertRaises(ContractError):watermark_trace([('s',2,1),('s',1,2)])
    def test_mixed_version_contraction_and_offline_reader(self):
        readers=[{'id':'offline-mobile','version':1,'fenced':False},{'id':'batch','version':2,'fenced':False}]
        with self.assertRaises(ContractError):can_contract(readers,2,True,True)
        readers[0]['fenced']=True;self.assertTrue(can_contract(readers,2,True,True))
        for caught_up,source in [(False,True),(True,False)]:
            with self.assertRaises(ContractError):can_contract(readers,2,caught_up,source)
        self.assertTrue(can_contract([],2,True,True))
    def test_lineage_constant_multi_input_unknown_neighbor(self):
        a={'dataset':'tenant1.orders','version':'v1','field':'price'};b={**a,'field':'count'}
        self.assertEqual(lineage_inputs({'kind':'constant','inputs':[]}),[])
        self.assertEqual(len(lineage_inputs({'kind':'expression','inputs':[a,b]})),2)
        self.assertEqual(lineage_inputs({'kind':'unknown','inputs':[],'complete':False}),[])
        for x in [{'kind':'constant','inputs':[a]},{'kind':'expression','inputs':[]},{'kind':'unknown','inputs':[],'complete':True},{'kind':'expression','inputs':[a,a]}]:
            with self.assertRaises(ContractError):lineage_inputs(x)
    def test_optimized_public_module_actually_refuses(self):
        for flag in ('-O','-OO'):
            p=subprocess.run([sys.executable,flag,'-m','checks.database_examples'],cwd=ROOT,text=True,capture_output=True)
            self.assertNotEqual(p.returncode,0);self.assertIn('-O/-OO',p.stderr)

class SQLiteExecution(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.path=Path(self.tmp.name)/'db.sqlite'
    def connect(self):
        c=sqlite3.connect(self.path,isolation_level=None,timeout=0.05);self.addCleanup(c.close);return c
    def event(self,**updates):
        return dict(source='pg-orders',generation='timeline-1',transaction='tx-1',record='row-1',table='orders',tenant='one',key='42',version=1,epoch=1,op='upsert',value={'status':'paid'},lsn='0/ABC',**updates)
    def store(self):
        c=self.connect();init_store(c);c.execute('INSERT INTO lease VALUES(?,?,?)',('topic-incarnation-1/p0',1,5));return c
    def test_effect_cursor_inbox_atomic_at_all_precommit_breaks(self):
        c=self.store()
        for stage in ('after-inbox','after-target','before-commit'):
            with self.assertRaises(RuntimeError):apply_event(c,self.event(),'topic-incarnation-1/p0',5,17,stage)
            self.assertEqual(c.execute('SELECT count(*) FROM inbox').fetchone()[0],0)
            self.assertEqual(c.execute('SELECT count(*) FROM target').fetchone()[0],0)
            self.assertEqual(c.execute('SELECT cursor FROM lease').fetchone()[0],5)
        self.assertEqual(apply_event(c,self.event(),'topic-incarnation-1/p0',5,17),'applied')
        self.assertEqual(c.execute('SELECT cursor FROM lease').fetchone()[0],17)
    def test_unknown_commit_reconciles_duplicate_and_hash_identity_conflict(self):
        c=self.store();e=self.event()
        with self.assertRaises(RuntimeError):apply_event(c,e,'topic-incarnation-1/p0',5,17,'after-commit')
        self.assertEqual(apply_event(c,e,'topic-incarnation-1/p0',5,17),'duplicate')
        self.assertEqual(c.execute('SELECT count(*) FROM target').fetchone()[0],1)
        changed={**e,'value':{'status':'cancelled'}}
        with self.assertRaises(ContractError):apply_event(c,changed,'topic-incarnation-1/p0',5,17)
    def test_same_lsn_two_rows_source_tenant_generation_no_false_dedupe(self):
        c=self.store();cursor=5
        for i,extra in enumerate([{}, {'record':'row-2','key':'43'},{'tenant':'two'}, {'generation':'timeline-2'},{'source':'other-source'}]):
            e={**self.event(),**extra};next_cursor=cursor+7
            self.assertEqual(apply_event(c,e,'topic-incarnation-1/p0',cursor,next_cursor),'applied');cursor=next_cursor
        self.assertEqual(c.execute('SELECT count(*) FROM target').fetchone()[0],5)
    def test_tombstone_older_replay_and_recreation(self):
        c=self.store();base=self.event();cursor=5
        for i,e in enumerate([base,{**base,'record':'delete','version':3,'op':'delete','value':None},{**base,'record':'late-old','version':2},{**base,'record':'new','version':4,'value':{'status':'new'}}]):
            apply_event(c,e,'topic-incarnation-1/p0',cursor,cursor+7);cursor+=7
        self.assertEqual(c.execute('SELECT version,deleted,value FROM target').fetchone(),(4,0,'{"status": "new"}'))
    def test_stale_worker_and_wrong_cursor_closed_unknown_operation(self):
        c=self.store();e=self.event()
        for altered in ({**e,'epoch':0},{**e,'op':'truncate'},{**e,'version':True},{**e,'record':''}):
            with self.assertRaises(ContractError):apply_event(c,altered,'topic-incarnation-1/p0',5,17)
        with self.assertRaises(ContractError):apply_event(c,e,'topic-incarnation-1/p0',6,17)
        self.assertEqual(c.execute('SELECT count(*) FROM target').fetchone()[0],0)
    def test_wal_backup_api_includes_uncheckpointed_commits_main_copy_does_not(self):
        c=self.connect();self.assertEqual(c.execute('PRAGMA journal_mode=WAL').fetchone()[0],'wal')
        c.execute('PRAGMA wal_autocheckpoint=0');c.execute('CREATE TABLE x(k INTEGER PRIMARY KEY,v TEXT)');c.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        c.execute("INSERT INTO x VALUES(1,'committed-in-wal')")
        bare=Path(self.tmp.name)/'bare.sqlite';shutil.copyfile(self.path,bare)
        with closing(sqlite3.connect(bare)) as b:self.assertEqual(b.execute('SELECT count(*) FROM x').fetchone()[0],0)
        good=Path(self.tmp.name)/'backup.sqlite'
        with closing(sqlite3.connect(good)) as b:c.backup(b)
        with closing(sqlite3.connect(good)) as b:
            self.assertEqual(b.execute('SELECT * FROM x').fetchall(),[(1,'committed-in-wal')]);self.assertEqual(b.execute('PRAGMA integrity_check').fetchone()[0],'ok')
    def test_busy_snapshot_requires_whole_transaction_restart(self):
        a=self.connect();a.execute('PRAGMA journal_mode=WAL');a.execute('CREATE TABLE x(k PRIMARY KEY,v)');a.execute('INSERT INTO x VALUES(1,0)');b=self.connect()
        a.execute('BEGIN');self.assertEqual(a.execute('SELECT v FROM x').fetchone()[0],0)
        b.execute('UPDATE x SET v=1');self.assertEqual(a.execute('SELECT v FROM x').fetchone()[0],0)
        with self.assertRaises(sqlite3.OperationalError) as caught:a.execute('UPDATE x SET v=2')
        self.assertEqual(caught.exception.sqlite_errorcode,sqlite3.SQLITE_BUSY_SNAPSHOT)
        a.rollback();a.execute('BEGIN IMMEDIATE');a.execute('UPDATE x SET v=2');a.commit()
        self.assertEqual(b.execute('SELECT v FROM x').fetchone()[0],2)
    def test_single_writer_lock_and_neighbor_after_release(self):
        a=self.connect();a.execute('CREATE TABLE x(k PRIMARY KEY)');b=self.connect();a.execute('BEGIN IMMEDIATE')
        with self.assertRaises(sqlite3.OperationalError) as caught:b.execute('BEGIN IMMEDIATE')
        self.assertEqual(caught.exception.sqlite_errorcode,sqlite3.SQLITE_BUSY)
        a.rollback();b.execute('BEGIN IMMEDIATE');b.execute('INSERT INTO x VALUES(1)');b.commit()
        self.assertEqual(a.execute('SELECT * FROM x').fetchall(),[(1,)])
    def test_effective_pragma_readback_unknown_is_not_a_setting(self):
        c=self.connect();self.assertEqual(c.execute('PRAGMA definitely_unknown_safety=ON').fetchall(),[])
        self.assertEqual(c.execute('PRAGMA definitely_unknown_safety').fetchall(),[])
        c.execute('PRAGMA foreign_keys=ON');self.assertEqual(c.execute('PRAGMA foreign_keys').fetchone()[0],1)
        self.assertIsInstance(c.execute('SELECT sqlite_version()').fetchone()[0],str)
    def test_null_unique_check_and_fk_activation_are_distinct(self):
        c=self.connect();c.execute('CREATE TABLE p(k TEXT PRIMARY KEY, v INTEGER CHECK(v>0), u TEXT UNIQUE)')
        c.execute('INSERT INTO p VALUES(NULL,NULL,NULL)');c.execute('INSERT INTO p VALUES(NULL,NULL,NULL)')
        self.assertEqual(c.execute('SELECT count(*) FROM p').fetchone()[0],2)
        c.execute('CREATE TABLE strict_p(k TEXT NOT NULL UNIQUE,v INTEGER NOT NULL CHECK(v>0))')
        for values in [(None,1),('x',None),('x',0)]:
            with self.assertRaises(sqlite3.IntegrityError):c.execute('INSERT INTO strict_p VALUES(?,?)',values)
        c.execute('CREATE TABLE parent(k INTEGER PRIMARY KEY)');c.execute('CREATE TABLE child(k REFERENCES parent(k))')
        c.execute('PRAGMA foreign_keys=OFF');c.execute('INSERT INTO child VALUES(42)');self.assertEqual(len(c.execute('PRAGMA foreign_key_check').fetchall()),1)
        c.execute('DELETE FROM child');c.execute('PRAGMA foreign_keys=ON')
        with self.assertRaises(sqlite3.IntegrityError):c.execute('INSERT INTO child VALUES(42)')
        c.execute('INSERT INTO child VALUES(NULL)')
    def test_outer_join_not_in_scalar_cardinality_and_count_answers(self):
        c=self.connect();c.executescript('CREATE TABLE l(k);CREATE TABLE r(k,v);INSERT INTO l VALUES(1),(2);INSERT INTO r VALUES(1,NULL),(1,5);')
        self.assertEqual(len(c.execute('SELECT l.k FROM l LEFT JOIN r ON l.k=r.k AND r.v=5').fetchall()),2)
        self.assertEqual(c.execute('SELECT l.k FROM l LEFT JOIN r ON l.k=r.k WHERE r.v=5').fetchall(),[(1,)])
        self.assertEqual(c.execute('SELECT 2 NOT IN (1,NULL), count(v),count(*) FROM r').fetchone(),(None,1,2))
        self.assertIn(c.execute('SELECT (SELECT k FROM l)').fetchone()[0],(1,2))
        rows=c.execute('SELECT k FROM l').fetchall()
        with self.assertRaises(ContractError):need(len(rows)<=1,'business cardinality not unique')
        self.assertEqual(c.execute('SELECT k FROM l ORDER BY k DESC LIMIT 1').fetchone()[0],2)
    def test_stable_keyset_same_snapshot_and_live_moving_key_counterexample(self):
        c=self.connect();c.executescript('CREATE TABLE x(id INTEGER PRIMARY KEY,t INTEGER);INSERT INTO x VALUES(1,1),(2,1),(3,2);')
        first=c.execute('SELECT t,id FROM x ORDER BY t,id LIMIT 2').fetchall();last=first[-1]
        self.assertEqual(first+c.execute('SELECT t,id FROM x WHERE (t,id)>(?,?) ORDER BY t,id',last).fetchall(),[(1,1),(1,2),(2,3)])
        c.execute('UPDATE x SET t=0 WHERE id=3')
        self.assertEqual(c.execute('SELECT t,id FROM x WHERE (t,id)>(?,?) ORDER BY t,id',last).fetchall(),[])
        self.assertEqual(c.execute('SELECT count(*) FROM x').fetchone()[0],3)
    def test_backfill_cas_does_not_overwrite_new_writer(self):
        c=self.connect();c.executescript("CREATE TABLE x(id PRIMARY KEY,version INTEGER,old TEXT,new TEXT);INSERT INTO x VALUES(1,1,'old',NULL);")
        snapshot=c.execute('SELECT version,old FROM x WHERE id=1').fetchone();c.execute("UPDATE x SET version=2,old='latest' WHERE id=1")
        self.assertEqual(c.execute('UPDATE x SET new=? WHERE id=1 AND version=?',(snapshot[1],snapshot[0])).rowcount,0)
        self.assertEqual(c.execute('SELECT old,new FROM x').fetchone(),('latest',None))
        version,value=c.execute('SELECT version,old FROM x WHERE id=1').fetchone()
        self.assertEqual(c.execute('UPDATE x SET new=? WHERE id=1 AND version=?',(value,version)).rowcount,1)
        self.assertEqual(c.execute('SELECT new FROM x').fetchone()[0],'latest')
    def test_transactional_ddl_and_savepoint_outer_rollback(self):
        c=self.connect();c.execute('BEGIN');c.execute('CREATE TABLE new_shape(k)');c.rollback()
        self.assertEqual(c.execute("SELECT name FROM sqlite_master WHERE name='new_shape'").fetchall(),[])
        c.execute('CREATE TABLE x(k)');c.execute('BEGIN');c.execute('SAVEPOINT inner');c.execute('INSERT INTO x VALUES(1)');c.execute('RELEASE inner');c.rollback()
        self.assertEqual(c.execute('SELECT * FROM x').fetchall(),[])
    def test_restore_old_backup_requires_current_deletion_overlay(self):
        c=self.connect();c.executescript("CREATE TABLE data(tenant,id,value,PRIMARY KEY(tenant,id));INSERT INTO data VALUES('a',1,'private'),('b',1,'retain');")
        p=Path(self.tmp.name)/'restore.sqlite'
        with closing(sqlite3.connect(p)) as target:c.backup(target)
        with closing(sqlite3.connect(p)) as restored, restored:
            restored.execute('CREATE TABLE current_deletions(tenant,id,PRIMARY KEY(tenant,id))');restored.execute("INSERT INTO current_deletions VALUES('a',1)")
            restored.execute('DELETE FROM data WHERE EXISTS(SELECT 1 FROM current_deletions d WHERE d.tenant=data.tenant AND d.id=data.id)')
            self.assertEqual(restored.execute('SELECT tenant,id,value FROM data').fetchall(),[('b',1,'retain')])
    def test_parameterized_injection_remains_value(self):
        c=self.connect();c.executescript("CREATE TABLE x(k TEXT);INSERT INTO x VALUES('legit');")
        self.assertEqual(c.execute('SELECT * FROM x WHERE k=?',("' OR 1=1 --",)).fetchall(),[])
        self.assertEqual(c.execute('SELECT * FROM x WHERE k=?',('legit',)).fetchall(),[('legit',)])
    def test_outbox_persistent_intent_and_target_business_identity(self):
        c=self.store();c.execute('BEGIN');c.execute("INSERT INTO outbox VALUES('refund:one:42','{}','pending')");c.commit()
        self.assertEqual(c.execute('SELECT state FROM outbox').fetchone()[0],'pending')
        # Actual separate local SQLite receiver, not an actual payment or transport.
        receiver=sqlite3.connect(':memory:');self.addCleanup(receiver.close);receiver.execute('CREATE TABLE effects(operation TEXT PRIMARY KEY)')
        for attempt in range(2):receiver.execute('INSERT OR IGNORE INTO effects VALUES(?)',('refund:one:42',));receiver.commit()
        c.execute("UPDATE outbox SET state='sent' WHERE operation='refund:one:42'")
        self.assertEqual(receiver.execute('SELECT count(*) FROM effects').fetchone()[0],1)
    def test_real_two_connections_parallel_inbox_unique_effect(self):
        c=self.store();c.execute('PRAGMA journal_mode=WAL');barrier=threading.Barrier(2);results=[];errors=[]
        def worker():
            con=sqlite3.connect(self.path,isolation_level=None,timeout=2)
            try:
                barrier.wait();results.append(apply_event(con,self.event(),'topic-incarnation-1/p0',5,17))
            except BaseException as e:errors.append(repr(e))
            finally:con.close()
        threads=[threading.Thread(target=worker) for _ in range(2)]
        for t in threads:t.start()
        for t in threads:t.join(5);self.assertFalse(t.is_alive())
        self.assertEqual(errors,[]);self.assertCountEqual(results,['applied','duplicate'])
        self.assertEqual(c.execute('SELECT count(*) FROM inbox').fetchone()[0],1)

if __name__=='__main__':unittest.main(verbosity=2)
