import importlib.util,json,os,platform,sqlite3,subprocess,sys,tempfile,threading,unittest,urllib.request
from pathlib import Path
from datetime import datetime,timezone
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('wb_local_contracts',ROOT/'examples/web-backend/local_contracts.py')
m=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(m)
RUN=None
EVIDENCE=[]

class LocalContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global RUN
        base=Path(os.environ.get('STANDARDS_WEB_LOCAL_EVIDENCE_DIR',str(Path(tempfile.gettempdir())/'StandardsWebLocalContracts')))
        RUN=base/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
        RUN.mkdir(parents=True,exist_ok=False)
    def setUp(self):
        self.work=Path(tempfile.mkdtemp(prefix=self._testMethodName+'-',dir=RUN))
        self.db=self.work/'state.sqlite'; m.initialize(self.db)
    def command(self,mode='operation',*args):
        return [sys.executable,str(ROOT/'examples/web-backend/local_contracts.py'),mode,str(self.db),*args]
    def child(self,mode='operation',*args):
        p=subprocess.run(self.command(mode,*args),capture_output=True,text=True,timeout=15)
        EVIDENCE.append({'test':self._testMethodName,'command':p.args,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'state':m.state(self.db)})
        return p
    def record(self,**kwargs):
        EVIDENCE.append({'test':self._testMethodName,**kwargs,'state':m.state(self.db)})
    def test_process_crash_before_commit_rolls_back_business_and_outbox(self):
        self.assertEqual(self.child('operation','--crash','before-commit').returncode,71)
        s=m.state(self.db); self.assertEqual([len(s[x]) for x in ['ledger','operations','outbox']],[0,0,0])
        self.assertFalse(m.operation(self.db,'A','order-1','1.00')['replayed'])
        self.record(expected='0/0/0 after actual process exit; retry creates exactly one local effect')
    def test_process_crash_after_commit_authoritative_retry_keeps_original_intent(self):
        self.assertEqual(self.child('operation','--crash','after-commit').returncode,72)
        self.assertTrue(m.operation(self.db,'A','order-1','1.00')['replayed'])
        s=m.state(self.db); self.assertEqual([len(s[x]) for x in ['ledger','operations','outbox']],[1,1,1])
        self.record(expected='1/1/1; replay returns original receipt')
    def test_two_real_processes_contend_for_same_intent(self):
        ps=[subprocess.Popen(self.command('operation','--gate'),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for _ in range(2)]
        outs=[]
        for p in ps: p.stdin.write('\n'); p.stdin.flush()
        for p in ps:
            out,err=p.communicate(timeout=15); self.assertEqual(p.returncode,0,err); outs.append(json.loads(out))
        self.assertEqual(sorted(x['replayed'] for x in outs),[False,True])
        self.assertEqual(len(m.state(self.db)['ledger']),1)
        self.record(expected='one fresh result and one replay; actual SQLite writer contention',outputs=outs)
    def test_same_key_different_payload_conflict_is_not_an_extra_write(self):
        m.operation(self.db,'A','i1','1')
        with self.assertRaisesRegex(ValueError,'fingerprint'): m.operation(self.db,'A','i1','2')
        self.assertEqual(len(m.state(self.db)['ledger']),1); self.record(expected='conflict; one ledger/outbox entry')
    def test_equivalent_decimal_input_is_legal_neighbor(self):
        a=m.operation(self.db,'A','i1','1.00'); b=m.operation(self.db,'A','i1','1.0')
        self.assertEqual(a['result'],b['result']); self.assertTrue(b['replayed'])
        self.record(expected='same minor-unit amount is a legal replay, not a fingerprint conflict')
    def test_same_literal_key_in_different_tenant_is_legal_and_isolated(self):
        a=m.operation(self.db,'A','i1','1'); b=m.operation(self.db,'B','i1','2')
        self.assertNotEqual(a['result'],b['result']); self.assertEqual(len(m.state(self.db)['ledger']),2)
        self.record(expected='two authorized synthetic tenants have separate results; not an authentication test')
    def test_permanent_business_identity_outlives_deleted_dedup_cache(self):
        m.operation(self.db,'A','i1','1')
        c=m.connect(self.db); c.execute('DELETE FROM operations'); c.close()
        self.assertTrue(m.operation(self.db,'A','i1','1')['replayed'])
        self.assertEqual(len(m.state(self.db)['ledger']),1)
        self.record(expected='ephemeral-key removal does not permit a second permanent business effect',scope='ordered key-removal fixture, not real-time TTL scheduling')
    def test_inbox_business_atomic_crash_and_redelivery(self):
        self.assertEqual(self.child('consume','--crash','before-commit').returncode,74)
        self.assertEqual(m.state(self.db)['inbox'],[]); self.assertEqual(m.state(self.db)['projection'],[])
        self.assertFalse(m.consume(self.db,'A','c1','s1','e1',7)['duplicate'])
        self.assertTrue(m.consume(self.db,'A','c1','s1','e1',7)['duplicate'])
        self.assertEqual(m.state(self.db)['projection'],[('A','c1',7)])
        self.record(expected='redelivery applies one increment with atomic receipt and projection')
    def test_same_event_has_independent_legitimate_consumers_and_sources(self):
        m.consume(self.db,'A','c1','s1','e1',7); m.consume(self.db,'A','c2','s1','e1',7); m.consume(self.db,'A','c1','s2','e1',3)
        self.assertEqual(m.state(self.db)['projection'],[('A','c1',10),('A','c2',7)])
        self.record(expected='consumer scope and CloudEvents source distinguish legitimate work')
    def test_atomic_target_fence_rejects_old_writer(self):
        m.install_epoch(self.db,'A','x',1); m.install_epoch(self.db,'A','x',2)
        self.assertEqual(m.fenced_write(self.db,'A','x',1,'old'),0)
        self.assertEqual(m.fenced_write(self.db,'A','x',2,'new'),1)
        self.assertEqual(m.state(self.db)['fences'],[('A','x',2,'new')]); self.record(expected='target SQL rejects stale epoch')
    def test_current_epoch_on_independent_objects_is_legal_neighbor(self):
        for x in ['x','y']: m.install_epoch(self.db,'A',x,1); self.assertEqual(m.fenced_write(self.db,'A',x,1,x),1)
        self.assertEqual(len(m.state(self.db)['fences']),2); self.record(expected='independent current-epoch objects do not need a global lock')
    def test_mutation_split_business_outbox_transactions_exposes_gap(self):
        self.assertEqual(self.child('operation','--broken').returncode,73)
        s=m.state(self.db); self.assertEqual((len(s['ledger']),len(s['outbox'])),(1,0))
        self.record(mutation_failure_observed='business committed with missing outbox after actual process exit',expected_safe_invariant='ledger count equals its pending-event count')
    def test_mutation_inbox_first_commit_loses_work(self):
        self.assertEqual(self.child('consume','--broken').returncode,75)
        self.assertTrue(m.consume(self.db,'A','accounting','orders','e1',1)['duplicate'])
        self.assertEqual(m.state(self.db)['projection'],[])
        self.record(mutation_failure_observed='receipt committed before effect; replay is incorrectly suppressed')
    def test_mutation_missing_target_epoch_allows_old_writer(self):
        m.install_epoch(self.db,'A','x',2); m.fenced_write(self.db,'A','x',2,'new')
        self.assertEqual(m.fenced_write(self.db,'A','x',1,'old',broken=True),1)
        self.assertEqual(m.state(self.db)['fences'],[('A','x',2,'old')])
        self.record(mutation_failure_observed='old writer overwrote newer legitimate state when target guard removed')
    def test_authoritative_absence_before_old_attempt_commit_is_not_rejection(self):
        ready=threading.Event(); release=threading.Event(); errors=[]
        def writer():
            c=m.connect(self.db)
            try:
                c.execute('BEGIN IMMEDIATE'); c.execute("INSERT INTO ledger VALUES('A','old',100,'r-old')")
                ready.set(); self.assertTrue(release.wait(5)); c.commit()
            except BaseException as e: errors.append(repr(e))
            finally: c.close()
        t=threading.Thread(target=writer); t.start(); self.assertTrue(ready.wait(5))
        c=m.connect(self.db); seen=c.execute("SELECT count(*) FROM ledger WHERE intent='old'").fetchone()[0]; c.close()
        self.assertEqual(seen,0); release.set(); t.join(5); self.assertFalse(t.is_alive()); self.assertEqual(errors,[])
        # This deliberately violates the logical-intent requirement, exposing the counterexample.
        m.operation(self.db,'A','new-intent-for-same-user-action','1')
        self.assertEqual(len(m.state(self.db)['ledger']),2)
        self.record(mutation_failure_observed='query saw zero while old write was in flight, then a new intent created a second effect',observed_before_old_commit=seen)
    def test_real_loopback_http_commit_then_drop_response_and_safe_replay(self):
        db=self.db
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*_): pass
            def do_POST(self):
                b=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                r=m.operation(db,b['tenant'],b['intent'],b['amount'])
                if b.get('drop_response'):
                    self.close_connection=True; self.connection.close(); return
                payload=json.dumps(r).encode(); self.send_response(200); self.send_header('Content-Length',str(len(payload))); self.end_headers(); self.wfile.write(payload)
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever); thread.start()
        url='http://127.0.0.1:'+str(server.server_port)
        def post(drop):
            req=urllib.request.Request(url,json.dumps({'tenant':'A','intent':'i-http','amount':'1.00','drop_response':drop}).encode(),{'Content-Type':'application/json'})
            with urllib.request.urlopen(req,timeout=3) as r: return json.load(r)
        try:
            with self.assertRaises(Exception) as raised: post(True)
            result=post(False); self.assertTrue(result['replayed']); self.assertEqual(len(m.state(db)['ledger']),1)
            self.record(expected='actual HTTP response loss followed by same-intent replay has one SQLite effect',client_exception=type(raised.exception).__name__,replay=result)
        finally: server.shutdown(); server.server_close(); thread.join(5)
    def test_sqlite_wal_old_snapshot_cannot_upgrade_after_other_writer(self):
        a=m.connect(self.db); b=m.connect(self.db)
        try:
            a.execute('BEGIN'); a.execute('SELECT * FROM ledger').fetchall()
            b.execute('BEGIN IMMEDIATE'); b.execute("INSERT INTO ledger VALUES('A','i1',100,'r1')"); b.commit()
            with self.assertRaises(sqlite3.OperationalError) as raised: a.execute("INSERT INTO ledger VALUES('A','i2',100,'r2')")
            self.assertEqual(getattr(raised.exception,'sqlite_errorcode',None),sqlite3.SQLITE_BUSY_SNAPSHOT)
            a.rollback(); self.record(expected='actual WAL snapshot upgrade is rejected',sqlite_errorcode=raised.exception.sqlite_errorcode)
        finally: a.close(); b.close()

def tearDownModule():
    if RUN is not None:
        (RUN/'results.json').write_text(json.dumps({'python':sys.version,'sqlite':sqlite3.sqlite_version,'platform':platform.platform(),'scope':'real local processes, SQLite files, threads and loopback HTTP; no browser, AT, Broker, production database or paid service','observations':EVIDENCE},ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__': unittest.main(verbosity=2)
