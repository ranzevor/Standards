"""Synthetic unknown-result decision contract, not a connector or authority verifier."""
import sys
if sys.flags.optimize:
    raise RuntimeError('Validation requires assertions enabled; do not use -O or -OO')
import math,re
KEYS=('tenant','target','operation','key','payload_sha256')
def identity(record):
 if any(type(record.get(k)) is not str or not record[k].strip() for k in KEYS):raise ValueError('complete identity required')
 if not re.fullmatch('[0-9a-f]{64}',record['payload_sha256']):raise ValueError('payload identity')
 return tuple(record[k] for k in KEYS)
def unknown_action(current,query,contract,now):
 ident=identity(current)
 if type(now) not in (int,float) or not math.isfinite(now):raise ValueError('finite clock')
 # A record is a synthetic supplied fact; actual receipt authentication is not implemented.
 if query is not None:
  if identity(query)!=ident:raise ValueError('query identity mismatch')
  if query.get('result')=='committed':return 'resolved-committed'
  if query.get('result')=='not-applied-terminal' and query.get('all_attempts_covered') is True and query.get('inflight_excluded') is True:return 'retry-after-terminal-absence'
  if query.get('result') not in {'not-found','unavailable','not-applied-terminal'}:raise ValueError('unknown query result')
 if contract is not None:
  if identity(contract)!=ident:raise ValueError('dedupe scope or payload mismatch')
  until=contract.get('valid_until')
  if type(until) not in (int,float) or not math.isfinite(until):raise ValueError('finite dedupe expiry')
  if contract.get('target_deduplicates') is True and contract.get('rejects_after_valid_until') is True and now<until:return 'retry-same-key'
 return 'remain-unknown'

class SyntheticDedupeEndpoint:
 """One fixed intent; keeps its expiry rejection even after dedupe window ends."""
 def __init__(self,current,valid_until):
  self.ident=identity(current)
  if type(valid_until) not in (int,float) or not math.isfinite(valid_until):raise ValueError('finite expiry')
  self.valid_until=valid_until;self.effects=0
 def accept(self,current,at):
  if identity(current)!=self.ident:raise ValueError('target intent mismatch')
  if type(at) not in (int,float) or not math.isfinite(at):raise ValueError('finite target time')
  if at>=self.valid_until:raise ValueError('expired intent rejected, never a fresh request')
  if self.effects==0:self.effects=1
  return 'committed'
