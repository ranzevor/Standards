"""Finite, synthetic contract models; no network, crypto verification or hardware."""
from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_EVEN, InvalidOperation, localcontext
from fractions import Fraction
from hashlib import sha256
import json
import struct
import threading
import zlib

class ContractError(ValueError):
    pass

def require(value, reason):
    if not value:
        raise ContractError(reason)

def integer(value, name='integer'):
    require(type(value) is int, name)
    return value

@dataclass(frozen=True)
class Money:
    currency: str
    exponent: int
    minor: int
    def __post_init__(self):
        require(isinstance(self.currency,str) and len(self.currency)==3 and self.currency.isascii() and self.currency.isupper(), 'currency identity')
        integer(self.exponent); integer(self.minor)
        require(0 <= self.exponent <= 6, 'synthetic exponent range')
        require(abs(self.minor) <= 10**18, 'synthetic amount bound')
    @classmethod
    def decimal(cls,currency,exponent,value,rounding=ROUND_HALF_EVEN):
        require(type(value) is str, 'decimal string required; not binary float')
        integer(exponent)
        require(0 <= exponent <= 6 and len(value)<=100, 'bounded numeric input')
        try:
            with localcontext() as ctx:
                ctx.prec=128
                amount=Decimal(value)
                require(amount.is_finite() and abs(amount) <= Decimal(10)**18, 'finite bounded decimal')
                minor=int((amount*(Decimal(10)**exponent)).quantize(Decimal(1), rounding=rounding))
        except (InvalidOperation,OverflowError,ValueError) as exc:
            raise ContractError('invalid decimal') from exc
        return cls(currency,exponent,minor)
    def __add__(self,other):
        require(isinstance(other,Money) and (self.currency,self.exponent)==(other.currency,other.exponent), 'currency/unit mismatch')
        return Money(self.currency,self.exponent,self.minor+other.minor)

def allocate(total:int, weights:list[tuple[str,int]]) -> dict[str,int]:
    integer(total)
    require(weights and all(isinstance(k,str) and k and type(w) is int and w>=0 for k,w in weights),'allocation input')
    require(len({k for k,_ in weights})==len(weights),'duplicate line id')
    denominator=sum(w for _,w in weights)
    require(denominator>0,'zero weight sum')
    magnitude=abs(total)
    quotients={k:(magnitude*w)//denominator for k,w in weights}
    remainders={k:(magnitude*w)%denominator for k,w in weights}
    residual=magnitude-sum(quotients.values())
    for k in sorted(quotients, key=lambda k:(-remainders[k],k))[:residual]:
        quotients[k]+=1
    sign=-1 if total<0 else 1
    return {k:sign*v for k,v in quotients.items()}

@dataclass
class Attempts:
    """Authority observations are assumptions; not-found is NOT terminal proof."""
    facts:dict[str,str]=field(default_factory=dict)
    def observe(self,attempt,status):
        require(status in {'unknown','pending','applied','never-applies'},'attempt fact')
        old=self.facts.get(attempt)
        require(old not in {'applied','never-applies'} or old==status,'conflicting terminal authority evidence')
        self.facts[attempt]=status
    def may_create_new(self):
        return bool(self.facts) and all(v=='never-applies' for v in self.facts.values())
    def apply_at_most_once(self):
        require(sum(v=='applied' for v in self.facts.values())<=1,'multiple effects; evidence conflict')

@dataclass
class RefundBook:
    captured:int
    states:dict[str,tuple[int,str]]=field(default_factory=dict)
    lock:threading.Lock=field(default_factory=threading.Lock,repr=False)
    def __post_init__(self):
        integer(self.captured); require(self.captured>=0,'capture')
    @property
    def available(self):
        return self.captured-sum(v for v,s in self.states.values() if s in {'reserved','unknown','applied'})
    def reserve(self,intent,amount):
        integer(amount)
        with self.lock:
            require(amount>0,'positive refund')
            if intent in self.states:
                require(self.states[intent][0]==amount,'refund parameter drift')
                return self.states[intent]
            require(amount<=self.available,'refund over balance including unresolved reservations')
            self.states[intent]=(amount,'reserved')
            return self.states[intent]
    def observe(self,intent,status):
        require(status in {'unknown','applied','never-applies'},'refund status')
        with self.lock:
            require(intent in self.states,'unknown refund intent')
            amount,old=self.states[intent]
            require(old not in {'applied','never-applies'} or old==status,'conflicting terminal refund')
            self.states[intent]=(amount,status)

@dataclass
class Stock:
    capacity:int
    reservations:dict[str,str]=field(default_factory=dict)
    lock:threading.Lock=field(default_factory=threading.Lock,repr=False)
    def reserve(self,key):
        with self.lock:
            if key in self.reservations:
                require(self.reservations[key] in {'reserved','committed'},'terminal reservation identity cannot be reused')
                return self.reservations[key]
            require(sum(v in {'reserved','committed'} for v in self.reservations.values())<self.capacity,'no stock')
            self.reservations[key]='reserved'
            return 'reserved'
    def transition(self,key,target):
        with self.lock:
            require(key in self.reservations,'unknown reservation')
            old=self.reservations[key]
            if old==target: return
            require(old=='reserved' and target in {'committed','released','expired'},'reservation transition')
            self.reservations[key]=target

@dataclass
class Ledger:
    accounts:dict[str,tuple[str,str]]
    journal:dict[str,tuple]=field(default_factory=dict)
    def post(self,source,currency,kind,lines):
        require(isinstance(source,str) and source and lines,'journal identity')
        checked=[]
        for account,delta in lines:
            integer(delta)
            require(account in self.accounts and self.accounts[account]==(currency,kind_for_account(kind,account)),'account currency/type mapping')
            checked.append((account,delta))
        require(sum(delta for _,delta in checked)==0,'unbalanced journal')
        canonical=(currency,kind,tuple(sorted(checked)))
        if source in self.journal:
            require(self.journal[source]==canonical,'same source different content')
            return False
        self.journal[source]=canonical
        return True
    def balances(self):
        balances={k:0 for k in self.accounts}
        for _,_,lines in self.journal.values():
            for account,delta in lines: balances[account]+=delta
        return balances

def kind_for_account(kind,account):
    # A deliberately small business mapping, not general accounting policy.
    policy={'capture':{'cash':'asset','sales':'revenue'},'reversal':{'cash':'asset','sales':'revenue'}}
    require(kind in policy and account in policy[kind],'unsupported synthetic accounting mapping')
    return policy[kind][account]

@dataclass
class Usage:
    seen:dict[tuple[str,str,str],tuple]=field(default_factory=dict)
    def add(self,customer,meter,event_id,unit,quantity,window):
        integer(quantity)
        require(isinstance(unit,str) and unit and quantity>=0,'usage unit/quantity')
        key=(customer,meter,event_id); value=(unit,quantity,window)
        if key in self.seen:
            require(self.seen[key]==value,'usage id parameter drift')
            return False
        self.seen[key]=value
        return True
    def total(self,customer,meter,unit,window):
        return sum(q for (c,m,_),(u,q,w) in self.seen.items() if (c,m,u,w)==(customer,meter,unit,window))

@dataclass(frozen=True)
class Principal:
    issuer:str
    sub:str
    tenant:str

@dataclass
class ResourceGate:
    epoch:int
    grants:set[tuple[Principal,str,str]]
    effects:list[tuple]=field(default_factory=list)
    def __post_init__(self):
        integer(self.epoch,'target epoch');require(self.epoch>=0,'target epoch')
    def execute(self,principal,resource,action,epoch):
        integer(epoch,'target epoch')
        require(epoch==self.epoch,'stale target epoch')
        require((principal,resource,action) in self.grants,'object/action grant')
        self.effects.append((principal,resource,action,epoch))
    def install_fence(self,new_epoch):
        require(type(new_epoch) is int and new_epoch>self.epoch,'monotonic target fence')
        self.epoch=new_epoch

@dataclass
class CredentialRoll:
    consumers:set[str]
    versions:dict[str,str]
    accepted:set[str]
    historical_decrypt:set[str]=field(default_factory=set)
    def complete(self,new,old):
        return bool(self.consumers) and all(self.versions.get(k)==new for k in self.consumers) and new in self.accepted and old not in self.accepted

# Synthetic storage format: [length:u32][payload JSON][crc:u32][commit:b'OK'].
# CRC detects tears in this finite model; NOT cryptographic authenticity.
def record(sequence,payload,committed=True):
    integer(sequence); require(sequence>=0,'record sequence')
    data=json.dumps({'sequence':sequence,'payload':payload},sort_keys=True,separators=(',',':')).encode()
    return struct.pack('>I',len(data))+data+struct.pack('>I',zlib.crc32(data))+(b'OK' if committed else b'')

def parse_record(raw):
    try:
        require(len(raw)>=10,'short record')
        length=struct.unpack('>I',raw[:4])[0]
        require(length<=4096 and len(raw)==length+10,'record length')
        data=raw[4:4+length]
        require(raw[-2:]==b'OK' and zlib.crc32(data)==struct.unpack('>I',raw[4+length:8+length])[0],'record integrity/commit')
        result=json.loads(data)
        integer(result['sequence']);require(result['sequence']>=0,'sequence')
        return result
    except (ContractError,KeyError,ValueError,TypeError,struct.error,UnicodeDecodeError):
        return None

def recover(slots):
    valid=[r for raw in slots if (r:=parse_record(raw)) is not None]
    require(valid,'no valid durable record')
    top=max(r['sequence'] for r in valid)
    winners=[r for r in valid if r['sequence']==top]
    require(all(r==winners[0] for r in winners),'same generation conflicting durable records')
    return winners[0]

@dataclass(frozen=True)
class Manifest:
    vendor:str
    device_class:str
    sequence:int
    display_version:str
    security_level:int
    digest:str
    size:int
    authenticated_by_test_authority:bool=True

@dataclass
class FirmwareDevice:
    vendor:str
    classes:set[str]
    floor:int
    highest:int=0
    accepted_digest:str|None=None
    candidate:Manifest|None=None
    image:bytes|None=None
    stage:str='idle'
    attempts:int=0
    active_digest:str|None=None
    def accept(self,m:Manifest,image:bytes):
        require(m.authenticated_by_test_authority is True,'synthetic authority rejected')
        require(m.vendor==self.vendor and m.device_class in self.classes,'hardware binding')
        integer(m.sequence); integer(m.security_level); integer(m.size)
        require(0<=m.sequence<2**64 and m.sequence>=self.highest,'manifest monotonic sequence')
        require(m.security_level>=self.floor,'security floor')
        require(m.size==len(image) and sha256(image).hexdigest()==m.digest,'image consumption binding')
        identity=sha256(json.dumps(m.__dict__,sort_keys=True).encode()).hexdigest()
        if m.sequence==self.highest:
            require(self.accepted_digest==identity,'same sequence different manifest')
            # Retry resumes existing state; never resets attempts or health.
            return False
        self.highest=m.sequence;self.accepted_digest=identity
        self.candidate=m;self.image=bytes(image);self.stage='verified';self.attempts=0
        return True
    def boot(self):
        require(self.candidate is not None and self.stage in {'verified','booted'},'no bootable candidate')
        require(self.attempts<2,'bounded candidate boots')
        self.attempts+=1;self.stage='booted'
    def confirm(self,digest,core_healthy):
        require(self.candidate is not None and self.stage=='booted','candidate not booted')
        require(digest==self.candidate.digest and core_healthy is True,'candidate identity/health')
        self.active_digest=digest;self.stage='active'

@dataclass
class Buffer:
    owner:str='cpu'
    complete:bool=False
    cache_current:bool=False
    def start_dma(self):
        require(self.owner=='cpu','buffer ownership')
        self.owner='dma';self.complete=False;self.cache_current=False
    def finish_dma(self):
        require(self.owner=='dma','DMA ownership')
        self.complete=True
    def reclaim_and_invalidate(self):
        require(self.owner=='dma' and self.complete,'DMA not complete')
        self.owner='cpu';self.cache_current=True
    def consume(self):
        require(self.owner=='cpu' and self.complete and self.cache_current,'incomplete or stale buffer')
    def free(self):
        require(self.owner=='cpu','DMA still owns buffer')
        self.owner='free'

def elapsed_u8(start,end,maximum_interval):
    require(type(start) is int and type(end) is int and 0<=start<256 and 0<=end<256,'u8 clock')
    require(type(maximum_interval) is int and 0<=maximum_interval<128,'bounded unambiguous comparison interval')
    delta=(end-start)%256
    require(delta<=maximum_interval,'unknown elapsed outside model interval')
    return delta

def material_scope(path,explicit,root_license):
    # Only exact synthetic identities; no legal inference or universal glob parser.
    require(path in explicit,'missing per-material disposition; root not inferred')
    value=explicit[path]
    require(value is not None,'unknown material license')
    return value

def verify_provenance(artifact,proof,policy):
    # signed_by is assumed authority evidence, not a signature algorithm.
    require(proof.get('signed_by') in policy['signers'],'untrusted signer')
    require(proof.get('subject')==sha256(artifact).hexdigest(),'artifact subject mismatch')
    require(proof.get('predicateType')=='https://slsa.dev/provenance/v1','predicate major')
    require(proof.get('builder') in policy['builders'],'builder')
    params=proof.get('externalParameters')
    require(isinstance(params,dict) and params==policy['externalParameters'],'unexpected external parameters')
    # Unknown ordinary extension fields intentionally ignored.
    return True

def validate_graph(document):
    require(document.get('spdxVersion')=='SPDX-2.3','synthetic selected SPDX syntax version')
    ids=document.get('ids',[])
    require(ids and len(ids)==len(set(ids)),'element ids')
    require('SPDXRef-DOCUMENT' in ids,'document id')
    for left,relationship,right in document.get('relationships',[]):
        require(left in ids and relationship in {'DESCRIBES','CONTAINS','DEPENDS_ON'},'relationship source/type')
        require(right in ids or right in {'NOASSERTION','NONE'},'dangling relationship')
    return True

@dataclass(frozen=True)
class QueuedCommand:
    command_id:str
    principal:Principal
    resource:str
    action:str
    epoch:int
    not_before:int
    expires_at:int
    payload_digest:str
    def __post_init__(self):
        require(all(type(v)is str and v and v.strip()==v for v in (self.command_id,self.resource,self.action)),'command names')
        require(type(self.principal)is Principal and all(type(v)is str and v for v in (self.principal.issuer,self.principal.sub,self.principal.tenant)),'command principal')
        for v in (self.epoch,self.not_before,self.expires_at):integer(v,'command epoch/time')
        require(self.epoch>=0 and 0<=self.not_before<self.expires_at,'command validity interval')
        require(type(self.payload_digest)is str and len(self.payload_digest)==64 and all(c in '0123456789abcdef'for c in self.payload_digest),'command payload digest')


class OfflineCommandQueue:
    """Sequential/in-process lease and replay model with trusted control/time observations.

    The queue exclusively manages its ResourceGate. Receipts/intents are RAM state;
    they do not establish durable physical at-most-once execution or authenticate
    a lease, clock, grant or control message. A replay receipt is historical.
    """
    def __init__(self,gate,authority_as_of,offline_until=None):
        require(type(gate)is ResourceGate,'finite resource gate')
        integer(authority_as_of,'control observation time');require(authority_as_of>=0,'control observation time')
        if offline_until is not None:
            integer(offline_until,'offline lease deadline');require(offline_until>authority_as_of,'offline lease deadline')
        self.gate=gate;self.authority_as_of=authority_as_of;self.offline_until=offline_until
        self.lease_epoch=gate.epoch;self.intents={};self.results={};self.lock=threading.RLock()
    def install_control(self,epoch,grants,observed_at,offline_until=None):
        with self.lock:
            integer(epoch,'control epoch');integer(observed_at,'control observation time')
            require(epoch>=self.gate.epoch and observed_at>=self.authority_as_of,'old control observation')
            require(type(grants)is set and all(type(x)is tuple and len(x)==3 and type(x[0])is Principal and all(type(v)is str and v for v in x[1:])for x in grants),'control grant shape')
            require(epoch!=self.gate.epoch or grants==self.gate.grants,'grant change needs new control epoch')
            if offline_until is not None:
                integer(offline_until,'offline lease deadline');require(offline_until>observed_at,'offline lease deadline')
            if epoch>self.gate.epoch:self.gate.install_fence(epoch)
            self.gate.grants=set(grants);self.authority_as_of=observed_at
            if offline_until is not None:self.offline_until=offline_until;self.lease_epoch=epoch
    def execute(self,command,time_window,*,connected=False,synchronized=False,acknowledgement_lost=False):
        from copy import deepcopy
        with self.lock:
            require(type(command)is QueuedCommand,'queued command shape')
            require(all(type(v)is bool for v in (connected,synchronized,acknowledgement_lost)),'execution observation flags')
            if command.command_id in self.intents:require(self.intents[command.command_id]==command,'same intent parameter drift')
            else:self.intents[command.command_id]=command
            if command.command_id in self.results:
                return dict(deepcopy(self.results[command.command_id]),historical_only=True)
            observed={'authority_as_of':self.authority_as_of,'installed_epoch':self.gate.epoch,
                      'all_revocations_propagated':False,'historical_only':False}
            def result(state,reason):return dict(observed,state=state,reason=reason)
            if time_window is None:return result('held','time-unknown')
            require(type(time_window)is tuple and len(time_window)==2,'trusted time interval')
            low,high=time_window;integer(low,'time bound');integer(high,'time bound');require(0<=low<=high,'time interval order')
            if self.authority_as_of>high:return result('held','clock-before-control-observation')
            if low>=command.expires_at:return result('refused','expired')
            if high<command.not_before:return result('held','not-before')
            if low<command.not_before or high>=command.expires_at:return result('held','time-validity-uncertain')
            if connected and not synchronized:return result('held','reconnect-needs-control-sync')
            if not connected:
                if self.offline_until is None:return result('held','no-offline-lease')
                if self.lease_epoch!=command.epoch:return result('refused','offline-lease-epoch')
                if low>=self.offline_until:return result('refused','offline-lease-expired')
                if high>=self.offline_until:return result('held','offline-lease-time-uncertain')
            if command.epoch!=self.gate.epoch:return result('refused','stale-target-epoch')
            if(command.principal,command.resource,command.action)not in self.gate.grants:return result('refused','object-action-not-granted')
            self.gate.execute(command.principal,command.resource,command.action,command.epoch)
            receipt=result('unknown'if acknowledgement_lost else'executed','acknowledgement-lost'if acknowledgement_lost else'finite-effect-observed')
            receipt['effect_count_at_observation']=len(self.gate.effects);self.results[command.command_id]=deepcopy(receipt)
            return deepcopy(receipt)
