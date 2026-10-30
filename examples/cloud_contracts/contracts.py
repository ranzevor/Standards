"""Finite synthetic contract models. No cloud, CI, kernel or cryptographic verifier."""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import json
import sqlite3
from pathlib import Path

class ContractError(ValueError):pass

def digest(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def canonical(value)->bytes:return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
MAX_MONEY_TEXT=1024
MAX_MONEY_DIGITS=256
MAX_MONEY_EXPONENT=128


def decimal(value)->Decimal:
    """Fixture accepts exact str/int/Decimal: <=256 coefficient digits,
    exponent -128..128 and <=1024 text characters. No float/bool coercion.
    Resource bounds here are not general currency scale requirements.
    """
    if type(value)not in (str,int,Decimal):raise ContractError('money requires exact decimal text/integer/Decimal, not float/bool')
    if type(value)is str and len(value)>MAX_MONEY_TEXT:raise ContractError('money text exceeds fixture bound')
    if type(value)is int and value.bit_length()>MAX_MONEY_TEXT*4:raise ContractError('money integer exceeds fixture bound')
    try:d=Decimal(value)
    except (InvalidOperation,TypeError,ValueError)as error:raise ContractError('invalid money')from error
    if not d.is_finite():raise ContractError('non-finite money')
    sign,digits,exponent=d.as_tuple()
    if len(digits)>MAX_MONEY_DIGITS or not -MAX_MONEY_EXPONENT<=exponent<=MAX_MONEY_EXPONENT:raise ContractError('money coefficient/exponent exceeds fixture bound')
    return d


def _exact_sum(values)->Decimal:
    """Integer-coefficient alignment, independent of Decimal arithmetic context."""
    parts=[v.as_tuple()for v in values]
    if not parts:return Decimal(0)
    exponent=min(p.exponent for p in parts);total=0
    for sign,digits,power in parts:
        coefficient=0
        for digit in digits:coefficient=coefficient*10+digit
        total+=(-coefficient if sign else coefficient)*10**(power-exponent)
    return Decimal((int(total<0),tuple(int(c)for c in str(abs(total))),exponent))

@dataclass(frozen=True)
class Scope:
    account:str
    region:str
    principal:str
    resource:str
    def verify(self,observed:'Scope')->None:
        if self!=observed:raise ContractError('actual immutable scope differs')

@dataclass(frozen=True)
class Plan:
    scope:Scope
    source:str
    inputs_digest:str
    provider_lock_digest:str
    lineage:str
    serial:int
    cloud_revision:str
    payload:bytes
    def identity(self)->str:
        return digest(canonical(dict(scope=self.scope.__dict__,source=self.source,inputs=self.inputs_digest,providers=self.provider_lock_digest,lineage=self.lineage,serial=self.serial,cloud_revision=self.cloud_revision,payload=digest(self.payload))))

def verify_plan(plan:Plan,approved_digest:str,approved_until:int,now:int,current:Plan)->None:
    if now>=approved_until:raise ContractError('approval expired')
    if plan.identity()!=approved_digest:raise ContractError('approved material differs')
    # A project guard, not a claim that Terraform automatically detects every cloud mutation.
    if plan.identity()!=current.identity():raise ContractError('source/state/actual revision changed; re-plan')


def _rollback_preserving_error(db,primary):
    """Keep the original local failure if SQLite already rolled back or cleanup fails."""
    try:
        if db.in_transaction:db.execute('ROLLBACK')
    except BaseException as cleanup:
        primary.add_note('rollback cleanup failed: '+type(cleanup).__name__+': '+str(cleanup))

class OperationLedger:
    """Actual local SQLite ledger; external effects remain external/unknown until reconciled.

    Models CLD-IAC-21/23, OBS-29/30 and COST-15/16. Local transactions are not
    a distributed transaction with any cloud target. Fence is checked by this
    synthetic target itself; a scheduler lease alone cannot provide it.
    """
    def __init__(self,path:str|Path):
        self.db=sqlite3.connect(str(path),timeout=3,isolation_level=None)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS target(id TEXT PRIMARY KEY,epoch INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS operation(id TEXT PRIMARY KEY,fingerprint TEXT NOT NULL,epoch INTEGER NOT NULL,state TEXT NOT NULL,result TEXT);
        CREATE TABLE IF NOT EXISTS synthetic_effect(op TEXT PRIMARY KEY,value TEXT NOT NULL);
        INSERT OR IGNORE INTO target VALUES('target',0);
        ''')
    def close(self):self.db.close()
    def epoch(self)->int:return self.db.execute("SELECT epoch FROM target WHERE id='target'").fetchone()[0]
    def advance(self,expected:int)->int:
        self.db.execute('BEGIN IMMEDIATE')
        try:
            c=self.db.execute("UPDATE target SET epoch=epoch+1 WHERE id='target' AND epoch=?",(expected,))
            if c.rowcount!=1:raise ContractError('fence compare-and-set failed')
            n=self.epoch();self.db.execute('COMMIT');return n
        except BaseException as primary:
            _rollback_preserving_error(self.db,primary)
            raise
    def begin(self,op:str,parameters:dict,epoch:int)->str:
        fp=digest(canonical(parameters));self.db.execute('BEGIN IMMEDIATE')
        try:
            if epoch!=self.epoch():raise ContractError('stale writer at target')
            old=self.db.execute('SELECT fingerprint,state FROM operation WHERE id=?',(op,)).fetchone()
            if old:
                if old[0]!=fp:raise ContractError('operation ID reused with other parameters')
                result=old[1]
            else:
                self.db.execute("INSERT INTO operation VALUES(?,?,?,'unknown',NULL)",(op,fp,epoch));result='unknown'
            self.db.execute('COMMIT');return result
        except BaseException as primary:
            _rollback_preserving_error(self.db,primary)
            raise
    def complete_synthetic(self,op:str,value:str,epoch:int)->None:
        """One SQLite transaction for this synthetic effect only; not cloud exactly-once."""
        self.db.execute('BEGIN IMMEDIATE')
        try:
            if epoch!=self.epoch():raise ContractError('stale writer cannot commit')
            row=self.db.execute('SELECT state,result FROM operation WHERE id=?',(op,)).fetchone()
            if row is None:raise ContractError('missing durable operation')
            if row[0]=='succeeded':
                if row[1]!=value:raise ContractError('conflicting terminal result')
            elif row[0]=='unknown':
                self.db.execute('INSERT INTO synthetic_effect VALUES(?,?)',(op,value))
                self.db.execute("UPDATE operation SET state='succeeded',result=? WHERE id=?",(value,op))
            else:raise ContractError('operation is not completable')
            self.db.execute('COMMIT')
        except BaseException as primary:
            _rollback_preserving_error(self.db,primary)
            raise
    def reconcile(self,op:str,authoritative_state:str,result:str|None=None)->None:
        if authoritative_state not in ('succeeded','failed'):raise ContractError('no authoritative terminal receipt')
        self.db.execute('BEGIN IMMEDIATE')
        try:
            row=self.db.execute('SELECT state,result FROM operation WHERE id=?',(op,)).fetchone()
            if not row:raise ContractError('unknown operation ID')
            if row[0]!='unknown' and row!=(authoritative_state,result):raise ContractError('terminal fact cannot be overwritten')
            self.db.execute('UPDATE operation SET state=?,result=? WHERE id=?',(authoritative_state,result,op));self.db.execute('COMMIT')
        except BaseException as primary:
            _rollback_preserving_error(self.db,primary)
            raise
    def state(self,op:str):
        r=self.db.execute('SELECT state,result FROM operation WHERE id=?',(op,)).fetchone()
        if not r:raise ContractError('unknown operation ID')
        return r

@dataclass(frozen=True)
class VerifiedClaim:
    """Synthetic verifier output; constructing this is NOT signature verification."""
    signature_valid:bool
    signer:str
    builder:str
    subject_digest:str
    platform:str
    predicate_type:str

def accept_artifact(payload:bytes,claim:VerifiedClaim,allowed_pairs:set[tuple[str,str]],platform:str,predicate:str)->str:
    if not claim.signature_valid:raise ContractError('signature verifier rejected')
    if (claim.signer,claim.builder) not in allowed_pairs:raise ContractError('signer-builder pair not allowed')
    if claim.subject_digest!=digest(payload):raise ContractError('actual subject bytes differ')
    if claim.platform!=platform or claim.predicate_type!=predicate:raise ContractError('wrong platform or statement type')
    return claim.subject_digest

def dsse_pae(payload_type:str,payload:bytes)->bytes:
    kind=payload_type.encode('utf-8')
    return b'DSSEv1 '+str(len(kind)).encode()+b' '+kind+b' '+str(len(payload)).encode()+b' '+payload

@dataclass(frozen=True)
class RecoveryNode:
    available:bool
    dependencies:tuple[str,...]=()

def recovery_order(nodes:dict[str,RecoveryNode],goal:str)->list[str]:
    """Nodes explicitly include artifacts, principal permissions and reachability."""
    visiting=set();done=set();order=[]
    def visit(n):
        if n in done:return
        if n in visiting:raise ContractError('bootstrap dependency cycle')
        if n not in nodes or not nodes[n].available:raise ContractError('unavailable recovery dependency: '+n)
        visiting.add(n)
        for d in nodes[n].dependencies:visit(d)
        visiting.remove(n);done.add(n);order.append(n)
    visit(goal);return order

class Budget:
    """Conservative local admission ledger; prices/delays must be supplied, not predicted."""
    def __init__(self,limit,currency,period,fixed='0',reported='0',headroom='0'):
        self.limit=decimal(limit);self.currency=currency;self.period=period
        self.fixed=decimal(fixed);self.reported=decimal(reported);self.headroom=decimal(headroom)
        if min(self.limit,self.fixed,self.reported,self.headroom)<0:raise ContractError('negative bound')
        self.operations={}
    def available(self):return _exact_sum([self.limit,self.fixed.copy_negate(),self.reported.copy_negate(),self.headroom.copy_negate()]+[x['reserved'].copy_negate()for x in self.operations.values()])
    def reserve(self,op:str,amount,currency,period):
        if (currency,period)!=(self.currency,self.period):raise ContractError('incompatible currency/period')
        amount=decimal(amount)
        if amount<0:raise ContractError('negative reservation')
        if op in self.operations:
            if self.operations[op]['bound']!=amount:raise ContractError('operation reservation differs')
            return
        if amount>self.available():raise ContractError('admission budget exhausted')
        self.operations[op]=dict(bound=amount,reserved=amount,state='unknown')
    def cancel_requested(self,op):
        if op not in self.operations:raise ContractError('unknown operation')
        # Deliberately no refund: cancellation request is not non-execution evidence.
    def settle(self,op,actual,authoritative_terminal:bool):
        if not authoritative_terminal:raise ContractError('unknown outcome cannot release reservation')
        if op not in self.operations:raise ContractError('unknown operation')
        actual=decimal(actual);x=self.operations[op]
        if actual<0:raise ContractError('negative actual')
        if x['state']=='settled':
            if x['actual']!=actual:raise ContractError('receipt changed; explicit correction needed')
            return
        # An observed overrun remains recorded; never rewrite it to the reserved bound.
        self.reported=_exact_sum([self.reported,actual]);x.update(state='settled',reserved=Decimal(0),actual=actual)

@dataclass(frozen=True)
class CostRow:
    id:str
    currency:str
    billing_period:str
    billed:str
    effective:str
    resource_id:str|None

def totals(rows:list[CostRow],currency:str,period:str):
    seen=set();billed=Decimal(0);effective=Decimal(0);unallocated=[]
    for r in rows:
        if r.id in seen:raise ContractError('duplicate export row')
        seen.add(r.id)
        if (r.currency,r.billing_period)!=(currency,period):raise ContractError('mixed cost basis')
        billed=_exact_sum([billed,decimal(r.billed)]);effective=_exact_sum([effective,decimal(r.effective)])
        if not r.resource_id:unallocated.append(r.id)
    return dict(billed=billed,effective=effective,unallocated=unallocated)

def retirement_state(resources:dict[str,str],final_invoice:bool,ongoing_commitments:list[str])->str:
    if any(s not in ('deleted','transferred') for s in resources.values()):return 'technical-retirement-incomplete'
    if not final_invoice or ongoing_commitments:return 'technical-retired-settlement-pending'
    return 'settled'

@dataclass(frozen=True)
class ReleaseVector:
    traffic:str
    code:str
    data:str
    external_effects:str
    def aggregate(self)->str:
        s=(self.traffic,self.code,self.data,self.external_effects)
        if any(x not in ('succeeded','failed','unknown','pending') for x in s):raise ContractError('invalid release state')
        if 'failed' in s:return 'failed'
        if 'unknown' in s:return 'unknown'
        if 'pending' in s:return 'pending'
        return 'succeeded'

def otlp_retry(partial_success_present:bool,http_status:int)->bool:
    if partial_success_present:return False
    return http_status in (429,502,503,504)
