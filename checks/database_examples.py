"""Small explicit models and SQLite transactions, not a multi-engine implementation."""
import sys
if sys.flags.optimize:
    raise RuntimeError('Database verification requires assertions; -O/-OO are unsupported')
import json
import re
import sqlite3
import math
from collections.abc import Mapping

class ContractError(AssertionError):
    pass

def need(ok, message):
    if not ok:
        raise ContractError(message)

def text(value):
    need(type(value) is str and value.strip() == value and bool(value), 'nonempty exact identity required')
    return value

def integer(value):
    need(type(value) is int and value >= 0, 'nonnegative integer required')
    return value

def durability_boundary(engine, version, config):
    """Classifies declared settings only; it never certifies device or fsync truthfulness."""
    text(version)
    need(type(config) is dict, 'explicit effective configuration required')
    if engine == 'postgresql':
        need(version.split('.')[0] == '18', 'model covers PostgreSQL 18 only')
        need(config.get('fsync') is True, 'fsync=false cannot claim crash durability')
        mode = config.get('synchronous_commit')
        need(mode in {'off','local','remote_write','on','remote_apply'}, 'invalid synchronous_commit')
        names = config.get('synchronous_standby_names')
        need(type(names) is str, 'read-back synchronous_standby_names required')
        remote = bool(names.strip()) and mode not in {'off','local'}
        return {'local_flush': mode != 'off', 'remote_stage': mode if remote else 'none',
                'product_acceptance': 'not-established', 'device_durability': 'not-tested'}
    if engine == 'sqlite':
        need(re.fullmatch(r'3\.\d+(?:\.\d+)?', version) is not None, 'SQLite 3 version required')
        journal=config.get('journal_mode'); mode=config.get('synchronous')
        need(journal in {'WAL','DELETE'}, 'model covers WAL/DELETE only')
        need(mode in {'OFF','NORMAL','FULL','EXTRA'}, 'unknown synchronous level')
        # This is the documented policy distinction, not a simulated power-loss result.
        return {'powerloss_durability_policy': journal=='WAL' and mode in {'FULL','EXTRA'} or journal=='DELETE' and mode=='EXTRA',
                'powerloss_consistency_policy': mode in {'FULL','EXTRA'} or journal=='WAL'and mode=='NORMAL', 'device_durability':'not-tested',
                'product_acceptance':'not-established'}
    if engine == 'mysql-innodb':
        need(version.split('.')[:2]==['8','4'], 'model covers MySQL InnoDB 8.4 only')
        flush=config.get('innodb_flush_log_at_trx_commit'); sync=config.get('sync_binlog')
        need(type(flush) is int and flush in {0,1,2}, 'invalid InnoDB flush policy')
        need(type(sync) is int and sync>=0, 'invalid binlog sync policy')
        need(type(config.get('binary_logging')) is bool, 'read-back binlog state required')
        return {'local_log_flush_policy':flush==1,
                'binlog_flush_policy':not config['binary_logging'] or sync==1,
                'device_durability':'not-tested', 'product_acceptance':'not-established'}
    raise ContractError('unsupported engine, no cross-engine inference')

def event_identity(event):
    need(type(event) is dict, 'event object required')
    values=tuple(text(event.get(k)) for k in ('source','generation','transaction','record','table','tenant','key'))
    # LSN alone is deliberately not the event identity.
    integer(event.get('version')); integer(event.get('epoch'))
    need(event.get('op') in {'upsert','delete'}, 'unsupported operation')
    need('value' in event, 'explicit value required, including null')
    return json.dumps(values, ensure_ascii=False, separators=(',',':'))

def source_payload(event):
    """Immutable source content excludes only the supplied worker-control epoch."""
    def check(value):
        if value is None or type(value)in(str,bool,int):return
        if type(value)is float:
            need(math.isfinite(value),'finite source number required');return
        if type(value)is list:
            for item in value:check(item)
            return
        need(type(value)is dict and all(type(k)is str for k in value),'JSON source keys/types required')
        for item in value.values():check(item)
    source={k:v for k,v in event.items()if k!='epoch'}
    check(source)
    return json.dumps(source,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)

def init_store(connection):
    connection.executescript('''
    PRAGMA foreign_keys=ON;
    CREATE TABLE lease(stream TEXT PRIMARY KEY, epoch INTEGER NOT NULL, cursor INTEGER NOT NULL);
    CREATE TABLE inbox(identity TEXT PRIMARY KEY, payload TEXT NOT NULL);
    CREATE TABLE delivery_progress(stream TEXT NOT NULL, predecessor INTEGER NOT NULL,
      next_cursor INTEGER NOT NULL, event_identity TEXT NOT NULL REFERENCES inbox(identity),
      PRIMARY KEY(stream,predecessor), UNIQUE(stream,next_cursor),
      CHECK(next_cursor>predecessor));
    CREATE TABLE target(source TEXT, generation TEXT, tenant TEXT, table_name TEXT, object_key TEXT,
      version INTEGER NOT NULL, deleted INTEGER NOT NULL, value TEXT,
      PRIMARY KEY(source,generation,tenant,table_name,object_key));
    CREATE TABLE outbox(operation TEXT PRIMARY KEY, payload TEXT NOT NULL, state TEXT NOT NULL CHECK(state IN ('pending','sent')));
    ''')

def apply_event(connection, event, stream, predecessor, next_cursor, fail_at=None):
    """Atomic provided-event + inbox + target + provided broker cursor in one SQLite DB.

    The supplied cursor chain is a contract, not proof that an external broker supplied
    every record. An actual Kafka/Flink connector and log retention are outside this API.
    """
    identity=event_identity(event);text(stream);integer(predecessor);integer(next_cursor)
    need(next_cursor>predecessor,'cursor must advance; offsets need not be consecutive')
    need(fail_at in {None,'after-inbox','after-target','before-commit','after-commit'},'unknown injection')
    payload=source_payload(event)
    need(not connection.in_transaction,'caller transaction must not be silently committed')
    try:
        connection.execute('BEGIN IMMEDIATE')
        row=connection.execute('SELECT epoch,cursor FROM lease WHERE stream=?',(stream,)).fetchone()
        need(row is not None,'unknown stream')
        need(row[0]==event['epoch'],'stale writer fenced at effect time')
        known=connection.execute('SELECT payload FROM inbox WHERE identity=?',(identity,)).fetchone()
        if known:
            need(known[0]==payload,'same event identity, different payload')
        delivery=connection.execute('SELECT next_cursor,event_identity FROM delivery_progress WHERE stream=? AND predecessor=?',(stream,predecessor)).fetchone()
        if delivery is not None:
            need(delivery==(next_cursor,identity)and known is not None,'committed delivery position has different content or range')
            need(row[1]>=next_cursor,'current cursor regressed behind a committed delivery')
            connection.rollback();return 'duplicate'
        need(row[1]==predecessor,'provided cursor chain has a gap or wrong incarnation')
        if not known:connection.execute('INSERT INTO inbox VALUES(?,?)',(identity,payload))
        if fail_at=='after-inbox':raise RuntimeError('injected after inbox')
        if not known:
            key=tuple(event[k] for k in ('source','generation','tenant','table','key'))
            prior=connection.execute('SELECT version,deleted,value FROM target WHERE source=? AND generation=? AND tenant=? AND table_name=? AND object_key=?',key).fetchone()
            value=json.dumps(event['value'],ensure_ascii=False,sort_keys=True,allow_nan=False)
            if prior is not None and prior[0]==event['version']:
                need(prior[1:]==(int(event['op']=='delete'),value),'same object version conflicts')
            if prior is None or event['version']>prior[0]:
                connection.execute('INSERT INTO target VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(source,generation,tenant,table_name,object_key) DO UPDATE SET version=excluded.version,deleted=excluded.deleted,value=excluded.value',key+(event['version'],int(event['op']=='delete'),value))
        if fail_at=='after-target':raise RuntimeError('injected after target')
        connection.execute('INSERT INTO delivery_progress VALUES(?,?,?,?)',(stream,predecessor,next_cursor,identity))
        changed=connection.execute('UPDATE lease SET cursor=? WHERE stream=? AND epoch=? AND cursor=?',(next_cursor,stream,event['epoch'],predecessor))
        need(changed.rowcount==1,'cursor/fence changed before consumption commit')
        if fail_at=='before-commit':raise RuntimeError('injected before commit')
        connection.commit()
    except BaseException:
        connection.rollback();raise
    if fail_at=='after-commit':raise RuntimeError('injected lost client commit acknowledgement')
    return 'duplicate'if known else'applied'

def required_closure(assets, roots):
    """Finite dependency model: every root's transitive prerequisites must exist."""
    need(type(assets) is dict and type(roots) is list,'asset map and root list required')
    visited=set();active=set()
    def visit(key):
        text(key);need(key in assets,'missing restore prerequisite: '+key)
        need(key not in active,'cyclic restore dependencies: '+key)
        if key in visited:return
        node=assets[key];need(type(node) is dict,'asset record required')
        need(type(node.get('dependencies')) is list,'explicit dependency list required')
        need(type(node.get('available')) is bool and node['available'],'unavailable prerequisite: '+key)
        active.add(key)
        for dep in node['dependencies']:visit(dep)
        active.remove(key);visited.add(key)
    for root in roots:visit(root)
    return visited

def safe_prune(assets, retained_points, candidates, now):
    integer(now);need(type(candidates) is list and len(candidates)==len(set(candidates)),'unique prune candidates required')
    protected=required_closure(assets,retained_points)
    for key in candidates:
        need(key in assets,'unknown deletion candidate')
        need(key not in protected,'candidate needed by retained recovery point: '+key)
        node=assets[key]
        need(node.get('legal_hold') is False,'unknown/active legal hold blocks deletion')
        integer(node.get('retain_until'));need(now>=node['retain_until'],'retention not expired')
    return list(candidates)

def watermark_trace(events, idle_after=10, lateness=3):
    """Finite two-input illustration; not a Flink/Spark/Beam implementation."""
    integer(idle_after);integer(lateness)
    need(idle_after>0,'positive idleness interval required')
    sources={};watermark=None;late=[];history=[];clock=-1
    for source,processing,event_time in events:
        text(source);integer(processing);integer(event_time);need(processing>=clock,'processing clock regressed');clock=processing
        if watermark is not None and event_time<watermark-lateness:late.append((source,event_time))
        prior=sources.get(source)
        sources[source]=(processing,max(event_time,prior[1]) if prior else event_time)
        active=[maximum for last,maximum in sources.values() if processing-last<idle_after]
        candidate=min(active) if active else None
        if candidate is not None:watermark=candidate if watermark is None else max(watermark,candidate)
        history.append(watermark)
    return {'watermarks':history,'late_side_output':late,'scope':'finite-illustration'}

def can_contract(readers, minimum_version, reconciled, retained_source):
    need(type(readers) is list and type(reconciled) is bool and type(retained_source) is bool,'explicit compatibility facts required')
    integer(minimum_version)
    for reader in readers:
        need(type(reader) is dict,'reader record required');text(reader.get('id'))
        integer(reader.get('version'));need(type(reader.get('fenced')) is bool,'reader admission proof required')
        need(reader['version']>=minimum_version or reader['fenced'],'old/offline reader can still return')
    need(reconciled,'backfill count does not prove incremental catch-up')
    need(retained_source,'destructive contraction has no verified restore/forward-fix source')
    return True

def lineage_inputs(record):
    need(type(record) is dict,'lineage record required')
    need(record.get('kind') in {'constant','expression','unknown'},'explicit lineage kind required')
    inputs=record.get('inputs');need(type(inputs) is list,'explicit input set required')
    keys=[]
    for inp in inputs:
        need(type(inp) is dict,'field identity required');keys.append(tuple(text(inp.get(k)) for k in ('dataset','version','field')))
    need(len(keys)==len(set(keys)),'duplicate field dependency')
    if record['kind']=='constant':need(not keys,'constant cannot invent a source column')
    if record['kind']=='expression':need(bool(keys),'known expression needs its actual inputs')
    if record['kind']=='unknown':need(record.get('complete') is False,'unknown cannot be complete')
    return keys

if __name__=='__main__':
    print(json.dumps({'python':sys.version,'sqlite':sqlite3.sqlite_version,'scope':'finite-model-and-isolated-sqlite'},ensure_ascii=False))
