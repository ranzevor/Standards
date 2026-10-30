"""SQLite/子进程/回环HTTP的有限合成业务，不是生产服务或Broker。"""
from decimal import Decimal, DecimalException
from pathlib import Path
import argparse, hashlib, json, os, sqlite3

def connect(path):
    c=sqlite3.connect(str(path),timeout=10,isolation_level=None)
    c.execute('PRAGMA foreign_keys=ON')
    c.execute('PRAGMA busy_timeout=10000')
    return c

def initialize(path):
    c=connect(path)
    c.execute('PRAGMA journal_mode=WAL')
    c.execute('PRAGMA synchronous=FULL')
    c.executescript('''
      CREATE TABLE IF NOT EXISTS operations(tenant TEXT,intent TEXT,fingerprint TEXT,result TEXT,
        PRIMARY KEY(tenant,intent));
      CREATE TABLE IF NOT EXISTS ledger(tenant TEXT,intent TEXT,cents INTEGER NOT NULL CHECK(cents>0),
        result TEXT NOT NULL,PRIMARY KEY(tenant,intent));
      CREATE TABLE IF NOT EXISTS outbox(tenant TEXT,event_id TEXT,payload TEXT NOT NULL,
        PRIMARY KEY(tenant,event_id));
      CREATE TABLE IF NOT EXISTS inbox(tenant TEXT,consumer TEXT,source TEXT,event_id TEXT,
        PRIMARY KEY(tenant,consumer,source,event_id));
      CREATE TABLE IF NOT EXISTS projection(tenant TEXT,consumer TEXT,total INTEGER NOT NULL,
        PRIMARY KEY(tenant,consumer));
      CREATE TABLE IF NOT EXISTS fences(tenant TEXT,object_id TEXT,epoch INTEGER NOT NULL,value TEXT,
        PRIMARY KEY(tenant,object_id));
    ''')
    c.close()

MAX_AMOUNT_TEXT=1024
MAX_SQLITE_CENTS=(1<<63)-1


def canonical_amount(amount):
    """Exact positive whole cents for this SQLite fixture, not a currency policy.

    Decimal spelling is bounded to 1024 characters and cents to signed int64.
    Native floats use their exact binary value, not rounded str conversion;
    1.0 is legal, while binary 0.1 is not an exact whole-cent amount.
    """
    if type(amount)not in (str,int,Decimal,float):raise ValueError('invalid minor-unit amount: exact numeric type')
    if type(amount)is int and amount.bit_length()>MAX_AMOUNT_TEXT*4:raise ValueError('invalid minor-unit amount: fixture input budget')
    spelling=str(amount)
    if len(spelling)>MAX_AMOUNT_TEXT:raise ValueError('invalid minor-unit amount: fixture input budget')
    try:d=Decimal.from_float(amount)if type(amount)is float else Decimal(spelling)
    except DecimalException as error:raise ValueError('invalid minor-unit amount')from error
    if not d.is_finite():raise ValueError('invalid minor-unit amount')
    sign,digits,exponent=d.as_tuple()
    if sign or not any(digits):raise ValueError('invalid minor-unit amount')
    scale=exponent+2
    if scale<0:
        discard=-scale
        if discard>=len(digits)or any(digits[-discard:]):raise ValueError('invalid minor-unit amount')
        digits=digits[:-discard];scale=0
    if len(digits)+scale>19:raise ValueError('invalid minor-unit amount: SQLite INTEGER range')
    cents=0
    for digit in digits:cents=10*cents+digit
    cents*=10**scale
    if cents>MAX_SQLITE_CENTS:raise ValueError('invalid minor-unit amount: SQLite INTEGER range')
    return cents


def operation(path,tenant,intent,amount,crash=None,broken_outbox=False):
    cents=canonical_amount(amount)
    fingerprint=hashlib.sha256(json.dumps({'cents':cents},sort_keys=True).encode()).hexdigest()
    c=connect(path)
    try:
        c.execute('BEGIN IMMEDIATE')
        # The permanent ledger uniqueness outlives an ephemeral dedup cache.
        row=c.execute('SELECT cents,result FROM ledger WHERE tenant=? AND intent=?',(tenant,intent)).fetchone()
        if row:
            if row[0]!=cents: raise ValueError('intent fingerprint conflict')
            c.commit()
            return {'replayed':True,'result':row[1]}
        result='receipt:'+tenant+':'+intent
        c.execute('INSERT INTO operations VALUES(?,?,?,?)',(tenant,intent,fingerprint,result))
        c.execute('INSERT INTO ledger VALUES(?,?,?,?)',(tenant,intent,cents,result))
        if broken_outbox:
            c.commit()
            os._exit(73)
        c.execute('INSERT INTO outbox VALUES(?,?,?)',(tenant,'event:'+intent,json.dumps({'intent':intent,'cents':cents})))
        if crash=='before-commit': os._exit(71)
        c.commit()
        if crash=='after-commit': os._exit(72)
        return {'replayed':False,'result':result}
    finally:
        if c.in_transaction: c.rollback()
        c.close()

def consume(path,tenant,consumer,source,event_id,value,crash=None,broken_inbox=False):
    c=connect(path)
    try:
        c.execute('BEGIN IMMEDIATE')
        inserted=c.execute('INSERT OR IGNORE INTO inbox VALUES(?,?,?,?)',(tenant,consumer,source,event_id)).rowcount
        if not inserted:
            c.commit(); return {'duplicate':True}
        if broken_inbox:
            c.commit(); os._exit(75)
        c.execute('INSERT INTO projection VALUES(?,?,?) ON CONFLICT(tenant,consumer) DO UPDATE SET total=total+excluded.total',(tenant,consumer,value))
        if crash=='before-commit': os._exit(74)
        c.commit()
        return {'duplicate':False}
    finally:
        if c.in_transaction: c.rollback()
        c.close()

def install_epoch(path,tenant,object_id,epoch):
    c=connect(path)
    try:
        c.execute('BEGIN IMMEDIATE')
        row=c.execute('SELECT epoch FROM fences WHERE tenant=? AND object_id=?',(tenant,object_id)).fetchone()
        if row and epoch<=row[0]: raise ValueError('epoch must advance')
        c.execute('INSERT INTO fences VALUES(?,?,?,NULL) ON CONFLICT(tenant,object_id) DO UPDATE SET epoch=excluded.epoch',(tenant,object_id,epoch))
        c.commit()
    finally:
        if c.in_transaction: c.rollback()
        c.close()

def fenced_write(path,tenant,object_id,epoch,value,broken=False):
    c=connect(path)
    try:
        c.execute('BEGIN IMMEDIATE')
        if broken:
            n=c.execute('UPDATE fences SET value=? WHERE tenant=? AND object_id=?',(value,tenant,object_id)).rowcount
        else:
            n=c.execute('UPDATE fences SET value=? WHERE tenant=? AND object_id=? AND epoch=?',(value,tenant,object_id,epoch)).rowcount
        c.commit(); return n
    finally:
        if c.in_transaction: c.rollback()
        c.close()

def state(path):
    c=connect(path)
    try:
        return {t:c.execute('SELECT * FROM '+t+' ORDER BY 1,2').fetchall() for t in ['operations','ledger','outbox','inbox','projection','fences']}
    finally: c.close()

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('mode',choices=['operation','consume'])
    p.add_argument('database'); p.add_argument('--tenant',default='A'); p.add_argument('--intent',default='order-1')
    p.add_argument('--amount',default='1.00'); p.add_argument('--crash'); p.add_argument('--broken',action='store_true'); p.add_argument('--gate',action='store_true')
    p.add_argument('--consumer',default='accounting'); p.add_argument('--source',default='orders'); p.add_argument('--event',default='e1'); p.add_argument('--value',type=int,default=1)
    a=p.parse_args()
    if a.gate: input()
    r=operation(a.database,a.tenant,a.intent,a.amount,a.crash,a.broken) if a.mode=='operation' else consume(a.database,a.tenant,a.consumer,a.source,a.event,a.value,a.crash,a.broken)
    print(json.dumps(r,sort_keys=True),flush=True)
