"""Executable abstract contract, not a production connector or proof of delivery."""
import sys
if sys.flags.optimize:
    raise RuntimeError('Validation requires assertions enabled; do not use -O or -OO')
from dataclasses import dataclass,field
from enum import Enum
import hashlib,json,math,re
def validate_json(value):
 if value is None or type(value) in (str,bool,int):return
 if type(value) is float:
  if not math.isfinite(value):raise ValueError("non-finite JSON number")
  return
 if type(value) is list:
  for item in value:validate_json(item)
  return
 if type(value) is dict and all(type(key) is str for key in value):
  for item in value.values():validate_json(item)
  return
 raise ValueError("fingerprint input must use JSON values and string object keys")
def epoch_number(value):
 if type(value) is not int or value<0:raise ValueError("epoch must be nonnegative integer")
def finite_clock(value):
 if type(value) not in (int,float) or not math.isfinite(value):raise ValueError("finite clock value required")
class State(str,Enum):
 READY='ready'; DISPATCHING='dispatching'; SUCCEEDED='succeeded'; FAILED='failed_known'; UNKNOWN='unknown'
def fingerprint(value):
 validate_json(value)
 return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
@dataclass(frozen=True)
class Identity:
 tenant:str; target:str; definition:str; intent:str; operation:str
 def __post_init__(self):
  if any(type(value) is not str or not value.strip() for value in (self.tenant,self.target,self.definition,self.intent,self.operation)):raise ValueError("complete string identity required")
@dataclass
class Operation:
 identity:Identity
 digest:str
 state:State=State.READY
 epoch:int=0
 cancel_requested:bool=False
 attempts:int=0
 unresolved_attempts:set=field(default_factory=set)
 last_authority_revision:int=-1
 def __post_init__(self):
  if type(self.identity) is not Identity or type(self.digest) is not str or not re.fullmatch(r"[0-9a-f]{64}",self.digest):raise ValueError("operation identity and SHA256 required")
  epoch_number(self.epoch)
 def dispatch(self,identity,digest,epoch,authorized):
  epoch_number(epoch)
  if identity!=self.identity or digest!=self.digest:raise ValueError('identity or parameter mismatch')
  if epoch!=self.epoch or self.cancel_requested or authorized is not True:raise PermissionError('dispatch prohibited')
  if self.state not in (State.READY,State.FAILED):raise ValueError('reconciliation required')
  self.state=State.DISPATCHING;self.attempts+=1;self.unresolved_attempts.add(self.attempts)
 def resolve(self,result,identity,digest,attempt):
  if type(attempt) is not int or attempt<1:raise ValueError("positive integer attempt identity required")
  if identity!=self.identity or digest!=self.digest or attempt!=self.attempts:raise ValueError('unbound or stale receipt')
  if self.state not in (State.DISPATCHING,State.UNKNOWN):raise ValueError('not in flight')
  if result not in ('committed','not_applied','uncertain'):raise ValueError('invalid result')
  if result=='committed':
   self.unresolved_attempts.clear();self.state=State.SUCCEEDED
  elif result=='not_applied':
   self.unresolved_attempts.discard(attempt)
   self.state=State.UNKNOWN if self.unresolved_attempts else State.FAILED
  else:self.state=State.UNKNOWN
 def cancel(self):
  self.cancel_requested=True;self.epoch+=1
 def resume(self,authorized):
  if authorized is not True:raise PermissionError('authorization required')
  self.cancel_requested=False;self.epoch+=1
 def retry_unknown(self,now,dedupe_until,target_guarantees,authorized,*,epoch,target_enforces_expiry=False):
  epoch_number(epoch)
  if epoch!=self.epoch:raise PermissionError("stale retry epoch")
  finite_clock(now);finite_clock(dedupe_until)
  if self.state!=State.UNKNOWN:raise ValueError('not unknown')
  if authorized is not True or self.cancel_requested:raise PermissionError('dispatch prohibited')
  if target_guarantees is not True or target_enforces_expiry is not True or now>=dedupe_until:raise ValueError('target reconciliation required')
  self.state=State.DISPATCHING;self.attempts+=1;self.unresolved_attempts.add(self.attempts)
 def reconcile_operation(self,identity,digest,*,through_attempt,result,inflight_excluded,authority_revision):
  if identity!=self.identity or digest!=self.digest:raise ValueError('operation query identity mismatch')
  if type(through_attempt) is not int or through_attempt!=self.attempts:raise ValueError('query does not cover current attempt watermark')
  if type(authority_revision) is not int or authority_revision<=self.last_authority_revision:raise ValueError('stale authority revision')
  if self.state not in (State.DISPATCHING,State.UNKNOWN):raise ValueError('no unresolved operation')
  if inflight_excluded is not True:raise ValueError('inflight acceptance window still open')
  if result not in ('committed','not_applied'):raise ValueError('non-authoritative query result')
  self.last_authority_revision=authority_revision;self.unresolved_attempts.clear()
  self.state=State.SUCCEEDED if result=='committed' else State.FAILED
class FencedTarget:
 def __init__(self):self.epoch=-1;self.value=None
 def install_fence(self,epoch):
  epoch_number(epoch)
  if epoch<=self.epoch:raise PermissionError('non-increasing fence')
  self.epoch=epoch
 def write(self,epoch,value):
  epoch_number(epoch)
  if epoch!=self.epoch:raise PermissionError('uninstalled or stale fence')
  self.value=value
