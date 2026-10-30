"""Finite, in-memory examples of generation and effect boundaries.

No OS permissions, durable locks, network, package signing, devices or real
background schedulers are implemented. Authority objects below are prevalidated
test inputs, not a substitute for authenticating a real authority.
"""
from dataclasses import dataclass, field
import hashlib
import json

def require_runtime():
    if not __debug__:
        raise RuntimeError('optimized Python is unsupported for contract checks')

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

@dataclass(frozen=True)
class Context:
    account: str
    account_epoch: int
    document: str
    document_epoch: int
    scene: str

def can_deliver(original, current, still_authorized=True):
    return original == current and still_authorized

@dataclass
class SaveLedger:
    current: int = 0
    committed: int = 0
    acknowledged: int = 0
    snapshots: dict = field(default_factory=lambda:{0:''})
    pending: dict = field(default_factory=dict)
    committed_operations: set = field(default_factory=set)
    stored: str = ''

    def edit(self, value):
        self.current += 1
        self.snapshots[self.current] = value
        return self.current

    def capture(self, save_id):
        if save_id in self.pending: raise ValueError('duplicate save identity')
        self.pending[save_id]=(self.current,self.snapshots[self.current])
        return self.current

    def commit(self, save_id):
        generation, value=self.pending[save_id]
        if generation < self.committed: raise ValueError('stale write')
        self.committed=generation
        self.stored=value
        self.committed_operations.add(save_id)

    def acknowledge(self, save_id):
        generation,_=self.pending[save_id]
        if save_id not in self.committed_operations: raise ValueError('not committed')
        self.acknowledged=max(self.acknowledged,generation)

    @property
    def dirty(self): return self.current > self.acknowledged

@dataclass
class ActivationLedger:
    events: dict = field(default_factory=dict)
    windows: set = field(default_factory=set)

    def open(self, user, instance, event, document):
        key=(user,instance,event)
        payload=digest({'document':document})
        if key in self.events:
            if self.events[key] != payload: raise ValueError('event identity reused')
            return 'accepted-duplicate'
        self.events[key]=payload
        existed=(user,document) in self.windows
        self.windows.add((user,document))
        return 'focused' if existed else 'opened'

def may_run(binary_formats, data_format, component_protocols, required_protocol):
    return data_format in binary_formats and all(required_protocol in p for p in component_protocols)

@dataclass(frozen=True)
class RetryContract:
    dedup_until: int
    accept_until: int
    server_rejects_late: bool
    bounded_delivery_delay: int | None = None

    def safe_at(self, now):
        if now > self.dedup_until: return False
        # An actual service must enforce the first branch. The second branch
        # assumes a verified bound covering every still-in-flight attempt.
        if self.server_rejects_late:
            return now <= self.accept_until <= self.dedup_until
        return (self.bounded_delivery_delay is not None
                and self.bounded_delivery_delay >= 0
                and now+self.bounded_delivery_delay <= self.dedup_until)

@dataclass(frozen=True)
class Receipt:
    account: str
    operation: str
    parameters: str
    attempt: str
    outcome: str

@dataclass
class Operation:
    account: str
    operation: str
    parameters: str
    pending: set = field(default_factory=set)
    confirmed: bool = False

    def send(self, account, parameters, attempt, now=0, contract=None):
        if account != self.account or parameters != self.parameters:
            raise ValueError('wrong principal or parameters')
        if self.confirmed: return 'already-confirmed'
        if attempt in self.pending: raise ValueError('duplicate attempt identity')
        if self.pending and not self.retry_allowed(account,parameters,now,contract):
            raise ValueError('unknown effect requires verified retry contract')
        self.pending.add(attempt)
        return 'unknown'

    def observe(self, receipt):
        if (receipt.account,receipt.operation,receipt.parameters)!=(self.account,self.operation,self.parameters):
            raise ValueError('receipt identity mismatch')
        if receipt.attempt not in self.pending: raise ValueError('unknown attempt')
        if receipt.outcome not in ('applied','not-applied','unknown'): raise ValueError('invalid outcome')
        if receipt.outcome=='applied': self.confirmed=True
        if receipt.outcome!='unknown': self.pending.remove(receipt.attempt)
        return self.state

    @property
    def state(self):
        if self.confirmed: return 'confirmed'
        return 'unknown' if self.pending else 'not-submitted'

    def retry_allowed(self, account, parameters, now, contract=None):
        if account != self.account or parameters != self.parameters or self.confirmed: return False
        return self.state=='not-submitted' or (contract is not None and contract.safe_at(now))

@dataclass
class BackgroundAttempt:
    job: str
    operation: str
    epoch: int
    owner_epoch: int
    phase: str = 'running'
    completion_count: int = 0

    def may_commit(self, current_account, original_account, effective_permission, target_fence):
        return (self.phase=='running' and self.epoch==self.owner_epoch
                and current_account==original_account and effective_permission and target_fence)

    def expire(self):
        if self.phase=='running': self.phase='expired'

    def complete(self, success):
        if self.completion_count: return False
        self.completion_count=1
        self.phase='completed' if success and self.phase=='running' else 'incomplete'
        return True

def diagnostic_acceptable(binary_id, symbol_id, bytes_count, quota, contains_secret):
    return (binary_id==symbol_id and 0<=bytes_count<=quota and not contains_secret)

require_runtime()
