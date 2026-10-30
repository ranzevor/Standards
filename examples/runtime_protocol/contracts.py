"""Finite stdlib examples: not a product protocol, scheduler, or game engine."""
from __future__ import annotations
import codecs
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import math
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
from zoneinfo import ZoneInfo

if sys.flags.optimize:
    raise RuntimeError('optimized mode is not a supported evidence entry point')


def fingerprint(value):
    active=set()
    def check(v):
        if v is None or type(v) in (str, bool, int):
            return
        if type(v) is float:
            if not math.isfinite(v): raise ValueError('non-finite value')
            return
        if type(v) not in (list, dict): raise ValueError('not a JSON value')
        if id(v) in active: raise ValueError('cyclic input')
        active.add(id(v))
        if type(v) is dict:
            if any(type(k) is not str for k in v): raise ValueError('non-string key')
            values=v.values()
        else: values=v
        for item in values: check(item)
        active.remove(id(v))
    check(value)
    data=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    return hashlib.sha256(data).hexdigest()


class LengthFramer:
    """Toy unsigned big-endian 4-byte framing, bounded complete-message parser."""
    def __init__(self,max_payload=1024):
        if type(max_payload) is not int or max_payload<0:raise ValueError('invalid framing budget')
        self.max_payload=max_payload;self.buf=bytearray();self.need=None;self.failed=False
    def feed(self,data):
        if self.failed: raise ValueError('parser failed')
        out=[]
        # Consume bounded pieces so an arbitrarily large input chunk is not retained.
        view=memoryview(data);pos=0
        while pos<len(view):
            wanted=4 if self.need is None else self.need
            take=min(wanted-len(self.buf),len(view)-pos)
            self.buf.extend(view[pos:pos+take]);pos+=take
            if len(self.buf)<wanted: continue
            if self.need is None:
                n=int.from_bytes(self.buf,'big');self.buf.clear()
                if n>self.max_payload:
                    self.failed=True;raise ValueError('length exceeds budget')
                self.need=n
                if n==0:
                    out.append(b'');self.need=None
            else:
                out.append(bytes(self.buf));self.buf.clear();self.need=None
        return out
    def finish(self):
        if self.failed or self.buf or self.need is not None: raise ValueError('truncated frame')


def frame(data): return len(data).to_bytes(4,'big')+data


class SSEFixture:
    """Selected SSE fields; no HTTP, reconnect service, or persistence implied."""
    def __init__(self,max_event_bytes=4096):
        self.decoder=codecs.getincrementaldecoder('utf-8')('strict')
        self.line='';self.skip_lf=False;self.data=[];self.event_id='';self.events=[]
        self.max_event_bytes=max_event_bytes;self.pending_bytes=0
    def _line(self,line):
        if not line:
            if self.data:
                self.events.append((self.event_id,'\n'.join(self.data)))
                self.data=[]
            self.pending_bytes=0
            return
        if line.startswith(':'): return
        field,sep,value=line.partition(':')
        if value.startswith(' '):value=value[1:]
        if field=='data':self.data.append(value)
        elif field=='id' and '\0' not in value:self.event_id=value
    def feed(self,data):
        for ch in self.decoder.decode(data):
            self.pending_bytes+=len(ch.encode('utf-8'))
            if self.pending_bytes>self.max_event_bytes:raise ValueError('SSE fixture event budget')
            if self.skip_lf:
                self.skip_lf=False
                if ch=='\n':continue
            if ch in ('\r','\n'):
                self._line(self.line);self.line='';self.skip_lf=ch=='\r'
            else:self.line+=ch
    def finish(self):
        self.decoder.decode(b'',final=True)
        # EOF is not a blank line and never dispatches the pending event.
        self.line='';self.data=[]


def local_candidates(naive,zone):
    """Valid UTC instants only; round trip detects gaps, fold duplicates dedupe."""
    if naive.tzinfo is not None:raise ValueError('local input must be naive')
    tz=ZoneInfo(zone);out=set()
    for fold in (0,1):
        aware=naive.replace(tzinfo=tz,fold=fold)
        utc=aware.astimezone(timezone.utc)
        if utc.astimezone(tz).replace(tzinfo=None)==naive:out.add(utc)
    return sorted(out)


def explicit_datetime(naive,zone):
    """Selected RFC5545 DATE-TIME rule; not a general iCalendar parser."""
    valid=local_candidates(naive,zone)
    if valid:return valid[0]
    # ZoneInfo fold=0 uses the pre-transition offset in the tested gap profile.
    return naive.replace(tzinfo=ZoneInfo(zone),fold=0).astimezone(timezone.utc)


def generated_daily(start,zone,count):
    """Finite daily same-local-time recurrence, valid DTSTART required."""
    if type(count) is not int or not 0<count<=100:raise ValueError('count outside fixture budget')
    if not local_candidates(start,zone):raise ValueError('fixture requires valid DTSTART')
    out=[];day=start
    for _ in range(400):
        valid=local_candidates(day,zone)
        if valid:out.append(valid[0])
        if len(out)==count:return out
        day+=timedelta(days=1)
    raise ValueError('generation budget exhausted')


def calendar_set(rrule,rdates,exdates):return sorted((set(rrule)|set(rdates))-set(exdates))


def verify_webhook(body,key,header):
    if type(body) is not bytes or type(header) is not str or not header.isascii() or not header.startswith('sha256='):return False
    expected='sha256='+hmac.new(key,body,hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected,header)



def _rollback_preserving_error(db,primary):
    """Keep the original local failure if SQLite already rolled back or cleanup fails."""
    try:
        if db.in_transaction:db.execute('ROLLBACK')
    except BaseException as cleanup:
        primary.add_note('rollback cleanup failed: '+type(cleanup).__name__+': '+str(cleanup))

class DurableFixture:
    """One real SQLite file, finite transactions; no replicas, OS power loss or auth."""
    def __init__(self,path):
        self.db=sqlite3.connect(path,timeout=2,isolation_level=None)
        self.db.execute('PRAGMA journal_mode=DELETE')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS operations(k TEXT PRIMARY KEY, fp TEXT NOT NULL, state TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS attempts(k TEXT, a TEXT, state TEXT NOT NULL, PRIMARY KEY(k,a));
        CREATE TABLE IF NOT EXISTS reconciliation_events(
            id INTEGER PRIMARY KEY, k TEXT NOT NULL, applied INTEGER NOT NULL CHECK(applied IN (0,1)),
            observed_at_utc TEXT NOT NULL, prior_operation_state TEXT NOT NULL,
            prior_attempts_json TEXT NOT NULL, covered_attempts_json TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS fences(target TEXT PRIMARY KEY, epoch INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS contracts(k TEXT PRIMARY KEY, fp TEXT, accept_until INTEGER, retain_until INTEGER, target TEXT);
        CREATE TABLE IF NOT EXISTS dedupe(k TEXT PRIMARY KEY, fp TEXT, result INTEGER, expiry INTEGER);
        CREATE TABLE IF NOT EXISTS effects(id INTEGER PRIMARY KEY, k TEXT, fp TEXT, target TEXT, epoch INTEGER);
        ''')
    def close(self):self.db.close()
    def begin_attempt(self,k,payload,a):
        fp=fingerprint(payload)
        self.db.execute('BEGIN IMMEDIATE')
        try:
            row=self.db.execute('SELECT fp,state FROM operations WHERE k=?',(k,)).fetchone()
            if row and row[0]!=fp:raise ValueError('same intent, different payload')
            if row and row[1]=='succeeded':raise ValueError('already complete')
            self.db.execute('INSERT OR IGNORE INTO operations VALUES(?,?,?)',(k,fp,'ready'))
            self.db.execute('INSERT INTO attempts VALUES(?,?,?)',(k,a,'in_flight'))
            self._aggregate(k);self.db.execute('COMMIT')
        except BaseException as primary:
            _rollback_preserving_error(self.db,primary)
            raise
    def attempt_result(self,k,a,state):
        if state not in ('unknown','not_applied'):raise ValueError('fixture result kind')
        self.db.execute('BEGIN IMMEDIATE')
        try:
            row=self.db.execute('SELECT state FROM attempts WHERE k=? AND a=?',(k,a)).fetchone()
            if not row:raise ValueError('unknown attempt')
            if row[0]=='not_applied' and state=='unknown':raise ValueError('cannot reopen definitive attempt')
            self.db.execute('UPDATE attempts SET state=? WHERE k=? AND a=?',(state,k,a))
            self._aggregate(k);self.db.execute('COMMIT')
        except BaseException as primary:
            _rollback_preserving_error(self.db,primary)
            raise
    def _aggregate(self,k):
        op=self.db.execute('SELECT state FROM operations WHERE k=?',(k,)).fetchone()
        if op and op[0]=='succeeded':return
        states=[x[0] for x in self.db.execute('SELECT state FROM attempts WHERE k=?',(k,))]
        state='unknown' if 'unknown' in states else ('dispatching' if 'in_flight' in states else 'failed_known')
        self.db.execute('UPDATE operations SET state=? WHERE k=?',(state,k))
    def state(self,k):return self.db.execute('SELECT state FROM operations WHERE k=?',(k,)).fetchone()[0]
    def resolve_local_operation(self,k,covered_attempts,acceptance_closed,applied):
        """Fixture oracle only: atomically persist closure plus prior observations.

        A covered, closed, terminal absence resolves old attempts rather than
        leaving their unknown states to reopen at the next aggregation. The
        accepted reconciliation keeps the prior attempt observations in an
        append-only-through-this-API event; it is not proof of real authority.
        """
        if type(acceptance_closed) is not bool or type(applied) is not bool:
            raise ValueError('fixture oracle flags must be actual booleans')
        if not isinstance(covered_attempts,(list,tuple,set,frozenset)) or not all(type(a) is str for a in covered_attempts):
            raise ValueError('explicit covered attempt collection required')
        if len(covered_attempts)!=len(set(covered_attempts)):
            raise ValueError('duplicate covered attempt')
        self.db.execute('BEGIN IMMEDIATE')
        try:
            operation=self.db.execute('SELECT state FROM operations WHERE k=?',(k,)).fetchone()
            if operation is None:raise ValueError('unknown operation')
            prior_attempts=list(self.db.execute('SELECT a,state FROM attempts WHERE k=? ORDER BY a',(k,)))
            existing={x[0] for x in prior_attempts}
            if set(covered_attempts)!=existing or not acceptance_closed:
                raise ValueError('operation conclusion does not cover outstanding acceptance')
            if operation[0]=='succeeded' and not applied:
                raise ValueError('terminal absence cannot regress known operation success')
            event=self.db.execute('INSERT INTO reconciliation_events(k,applied,observed_at_utc,prior_operation_state,prior_attempts_json,covered_attempts_json) VALUES(?,?,?,?,?,?)',
                (k,int(applied),datetime.now(timezone.utc).isoformat(),operation[0],
                 json.dumps(prior_attempts,ensure_ascii=False,separators=(',',':')),
                 json.dumps(sorted(existing),ensure_ascii=False,separators=(',',':'))))
            if not applied:
                self.db.execute("UPDATE attempts SET state='not_applied' WHERE k=?",(k,))
            self.db.execute('UPDATE operations SET state=? WHERE k=?',('succeeded' if applied else 'failed_known',k))
            self.db.execute('COMMIT')
            return event.lastrowid
        except BaseException as primary:
            _rollback_preserving_error(self.db,primary)
            raise
    def install_fence(self,target,epoch):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            row=self.db.execute('SELECT epoch FROM fences WHERE target=?',(target,)).fetchone()
            if row and epoch<=row[0]:raise ValueError('non-increasing epoch')
            self.db.execute('INSERT INTO fences VALUES(?,?) ON CONFLICT(target) DO UPDATE SET epoch=excluded.epoch',(target,epoch))
            self.db.execute('COMMIT')
        except BaseException as primary:
            _rollback_preserving_error(self.db,primary)
            raise
    def register_target_contract(self,k,payload,accept_until,retain_until,target='actor'):
        if accept_until>retain_until:raise ValueError('dedupe window must cover acceptance')
        self.db.execute('INSERT INTO contracts VALUES(?,?,?,?,?)',(k,fingerprint(payload),accept_until,retain_until,target))
    def apply_target(self,k,payload,target,epoch,now):
        fp=fingerprint(payload);self.db.execute('BEGIN IMMEDIATE')
        try:
            fence=self.db.execute('SELECT epoch FROM fences WHERE target=?',(target,)).fetchone()
            if not fence or fence[0]!=epoch:raise ValueError('target rejects epoch')
            contract=self.db.execute('SELECT fp,accept_until,retain_until,target FROM contracts WHERE k=?',(k,)).fetchone()
            if not contract or fp!=contract[0] or target!=contract[3]:raise ValueError('contract identity mismatch')
            if now>contract[1]:raise ValueError('target acceptance closed')
            self.db.execute('DELETE FROM dedupe WHERE expiry < ?',(now,))
            row=self.db.execute('SELECT fp,result FROM dedupe WHERE k=?',(k,)).fetchone()
            if row:
                if row[0]!=fp:raise ValueError('payload mismatch')
                result=row[1]
            else:
                cur=self.db.execute('INSERT INTO effects(k,fp,target,epoch) VALUES(?,?,?,?)',(k,fp,target,epoch))
                result=cur.lastrowid
                self.db.execute('INSERT INTO dedupe VALUES(?,?,?,?)',(k,fp,result,contract[2]))
            self.db.execute('COMMIT');return result
        except BaseException as primary:
            _rollback_preserving_error(self.db,primary)
            raise


def atomic_publish(directory,name,data,crash_at=None):
    base=Path(directory).resolve()
    if Path(name).name!=name or name in ('','.','..'):raise ValueError('not a file name')
    fd,tmp=tempfile.mkstemp(prefix='.pending-',dir=base)
    with os.fdopen(fd,'wb') as stream:
        stream.write(data);stream.flush();os.fsync(stream.fileno())
    if crash_at=='before_publish':os._exit(21)
    os.replace(tmp,base/name)
    if crash_at=='after_publish':os._exit(22)
    if os.name=='posix':
        dfd=os.open(base,os.O_RDONLY)
        try:os.fsync(dfd)
        finally:os.close(dfd)
    return hashlib.sha256(data).hexdigest()


def replay(identity,initial,inputs):
    if identity.get('initial')!=fingerprint(initial):raise ValueError('initial state mismatch')
    if identity.get('rules')!='integer-add-v1' or identity.get('content')!='fixture-v1':raise ValueError('incompatible replay')
    if type(initial) is not int or any(type(v) is not int for v in inputs):raise ValueError('integer fixture only')
    states=[initial]
    for value in inputs:states.append(states[-1]+value)
    return states
