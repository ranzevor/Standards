"""Finite reference contracts. Locks model one process, not distributed storage/security."""
from __future__ import annotations
import sys
if sys.flags.optimize:
    raise RuntimeError('Validation requires assertions enabled; do not use -O or -OO')
from dataclasses import dataclass, field, asdict
from pathlib import Path, PurePosixPath
import copy, hashlib, hmac, json, math, os, re, threading, zipfile, stat

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
def digest(value): return hashlib.sha256(canonical(value).encode()).hexdigest()
def integer(value, minimum=0):
    if type(value) is not int or value<minimum: raise ValueError('integer range')
    return value

@dataclass
class Reservation:
    ceiling:int
    status:str='reserved'
    actual:int|None=None
    receipt:str|None=None

class Budget:
    def __init__(self,limit):
        self.limit=integer(limit);self.used=0;self.entries={};self.lock=threading.RLock();self.breaches=[]
    @property
    def reserved(self):return sum(x.ceiling for x in self.entries.values() if x.status in ('reserved','unknown'))
    def reserve(self,key,ceiling):
        integer(ceiling)
        if type(key)is not str or not key:raise ValueError('reservation identity')
        with self.lock:
            old=self.entries.get(key)
            if old:
                if old.ceiling!=ceiling:raise ValueError('same reservation different ceiling')
                return old.status
            if self.used+self.reserved+ceiling>self.limit:raise PermissionError('budget exhausted')
            self.entries[key]=Reservation(ceiling);return 'reserved'
    def unknown(self,key):
        with self.lock:
            e=self.entries[key]
            if e.status=='reserved':e.status='unknown'
    def settle(self,key,actual,receipt):
        integer(actual)
        if type(receipt)is not str or not receipt:raise ValueError('receipt identity')
        with self.lock:
            e=self.entries[key]
            if e.status=='released':raise ValueError('released reservation cannot acquire new charge silently')
            if e.status=='settled':
                if(e.actual,e.receipt)!=(actual,receipt):raise ValueError('conflicting settlement')
                return False
            if actual>e.ceiling:
                self.breaches.append({'key':key,'ceiling':e.ceiling,'actual':actual,'receipt':receipt})
            e.actual=actual;e.receipt=receipt;e.status='settled';self.used+=actual;return True
    def release(self,key,proof):
        if proof!='authoritative-not-started':raise PermissionError('unknown is not zero')
        with self.lock:
            e=self.entries[key]
            if e.status=='settled':raise ValueError('cannot erase observed cost')
            if e.status=='released':return False
            e.status='released';return True
    def snapshot(self):
        with self.lock:return {'limit':self.limit,'used':self.used,'entries':{k:asdict(v)for k,v in self.entries.items()},'breaches':copy.deepcopy(self.breaches)}
    @classmethod
    def restore(cls,s):
        if type(s)is not dict or set(s)!={'limit','used','entries','breaches'}:raise ValueError('budget snapshot fields')
        b=cls(s['limit']);b.used=integer(s['used'])
        if type(s['entries'])is not dict or type(s['breaches'])is not list:raise ValueError('budget snapshot collections')
        total=0;expected_breaches={}
        for key,value in s['entries'].items():
            if type(key)is not str or not key or type(value)is not dict or set(value)!={'ceiling','status','actual','receipt'}:raise ValueError('reservation snapshot fields')
            integer(value['ceiling'])
            if value['status']not in('reserved','unknown','settled','released'):raise ValueError('reservation snapshot state')
            if value['status']=='settled':
                integer(value['actual'])
                if type(value['receipt'])is not str or not value['receipt']:raise ValueError('settlement snapshot receipt')
                total+=value['actual']
                if value['actual']>value['ceiling']:expected_breaches[key]=(value['ceiling'],value['actual'],value['receipt'])
            elif value['actual']is not None or value['receipt']is not None:raise ValueError('unsettled reservation has final charge')
            b.entries[key]=Reservation(**copy.deepcopy(value))
        if total!=b.used:raise ValueError('budget used must equal retained final settlements')
        actual_breaches={}
        for breach in s['breaches']:
            if type(breach)is not dict or set(breach)!={'key','ceiling','actual','receipt'}:raise ValueError('budget breach snapshot fields')
            if type(breach['key'])is not str or breach['key']in actual_breaches:raise ValueError('duplicate budget breach')
            integer(breach['ceiling']);integer(breach['actual'])
            if type(breach['receipt'])is not str:raise ValueError('budget breach receipt type')
            actual_breaches[breach['key']]=(breach['ceiling'],breach['actual'],breach['receipt'])
        if actual_breaches!=expected_breaches:raise ValueError('budget breach facts differ from settlements')
        b.breaches=copy.deepcopy(s['breaches']);return b
    @classmethod
    def reconcile(cls,checkpoint,current):
        """Require current authority to retain every checkpoint budget fact."""
        old=cls.restore(checkpoint);now=cls.restore(current)
        for key,prior in old.entries.items():
            latest=now.entries.get(key)
            if latest is None or latest.ceiling!=prior.ceiling:raise ValueError('current budget lost or rebound an operation')
            if prior.status=='settled' and(latest.status,latest.actual,latest.receipt)!=('settled',prior.actual,prior.receipt):raise ValueError('current budget regressed or contradicted final spend')
            if prior.status=='released' and latest.status!='released':raise ValueError('current budget reopened a released operation')
            if prior.status=='unknown' and latest.status=='reserved':raise ValueError('current budget forgot operation uncertainty')
        return now

@dataclass(frozen=True)
class Grant:
    principal:str
    tenant:str
    method:str
    resource:str
    until:int
    revision:int

class Authority:
    def __init__(self):self.grants={};self.revision=0;self.lock=threading.RLock()
    def grant(self,principal,tenant,method,resource,until=100):
        with self.lock:
            self.revision+=1;g=Grant(principal,tenant,method,resource,integer(until),self.revision);self.grants[(principal,tenant,method,resource)]=g;return g
    def revoke(self,principal,tenant,method,resource):
        with self.lock:self.revision+=1;self.grants.pop((principal,tenant,method,resource),None)
    def check(self,g,now):
        with self.lock:
            if g is None or self.grants.get((g.principal,g.tenant,g.method,g.resource))!=g or now>=g.until:raise PermissionError('current authorization required')
            return True

class ApprovalBook:
    def __init__(self):self.rows={};self.lock=threading.RLock()
    def issue(self,ticket,grant,operation,params,until):
        with self.lock:
            if ticket in self.rows:raise ValueError('ticket already exists')
            self.rows[ticket]={'grant':grant,'operation':operation,'digest':digest(params),'until':until,'claimed':None}
    def claim(self,ticket,grant,operation,params,now):
        with self.lock:
            r=self.rows[ticket]
            if r['grant']!=grant or r['operation']!=operation or r['digest']!=digest(params) or now>=r['until']:raise PermissionError('approval binding')
            if r['claimed'] is None:r['claimed']=operation;return 'claimed'
            if r['claimed']==operation:return 'same-operation-recovery'
            raise PermissionError('consumed')

class Target:
    """Synthetic authority: atomically checks auth, fence, object version, then deduplicates."""
    def __init__(self,authority,tenant="t1",resource="order1",method="write"):
        self.tenant=tenant;self.resource=resource;self.method=method;self.authority=authority;self.epoch=1;self.version=1;self.operations={};self.effects=0;self.lock=threading.RLock()
    def accept(self,grant,operation,params,epoch,expected_version,now=0):
        # Shared authority lock makes this model's authorization/accept transition atomic.
        with self.authority.lock,self.lock:
            self.authority.check(grant,now)
            if (grant.tenant,grant.resource,grant.method)!=(self.tenant,self.resource,self.method):raise PermissionError("target object/method binding")
            if epoch!=self.epoch:raise PermissionError('stale target fence')
            old=self.operations.get(operation)
            if old:
                if old['digest']!=digest(params):raise ValueError('same intent different params')
                return copy.deepcopy(old)
            if expected_version!=self.version:raise ValueError('object version conflict')
            self.effects+=1;self.version+=1
            receipt={'operation':operation,'digest':digest(params),'tenant':grant.tenant,'resource':grant.resource,'effect_count':self.effects,'version':self.version}
            self.operations[operation]=receipt;return copy.deepcopy(receipt)
    def query(self,operation,final=False):
        with self.lock:
            if operation in self.operations:return {'status':'confirmed','receipt':copy.deepcopy(self.operations[operation])}
            return {'status':'not-started'if final else'unknown','receipt':None}

@dataclass
class Event:
    task:str
    attempt:str
    epoch:int
    plan:int
    status:str
    operation:str|None=None
    receipt:dict|None=None

class Controller:
    def __init__(self,task='root',limit=10):
        self.task=task;self.attempt='a1';self.epoch=1;self.plan=1;self.status='running';self.budget=Budget(limit);self.audit=[];self.results={};self.required=set();self.children={};self.lock=threading.RLock()
    def handoff(self,expected_epoch,new_attempt):
        with self.lock:
            if expected_epoch!=self.epoch or self.status not in ('running','waiting'):raise ValueError('handoff CAS conflict')
            self.epoch+=1;self.attempt=new_attempt;return self.epoch
    def admit(self,e,target=None):
        with self.lock:
            self.audit.append(asdict(e))
            if(e.task,e.attempt,e.epoch,e.plan)!=(self.task,self.attempt,self.epoch,self.plan):return 'historical-only'
            if self.status in ('cancelled','succeeded','failed'):return 'historical-only'
            if e.status=='confirmed':
                if not e.receipt or e.receipt.get('operation')!=e.operation or e.operation not in self.required or target is None:raise ValueError('authority receipt binding')
                authoritative=target.query(e.operation)
                if authoritative['status']!='confirmed' or authoritative['receipt']!=e.receipt:raise ValueError('not target authority result')
                self.results[e.operation]=copy.deepcopy(e.receipt)
            elif e.status=='unknown':self.status='reconciling'
            elif e.status=='running':self.status='running'
            else:raise ValueError('unknown event status')
            return 'accepted'
    def cancel(self):
        with self.lock:
            if self.status=='cancelled':return False
            if self.status in('succeeded','failed'):raise ValueError('terminal guard')
            self.status='cancelled';self.epoch+=1;return True
    def fail(self):
        with self.lock:
            if self.status=='failed':return False
            if self.status in('succeeded','cancelled'):raise ValueError('terminal guard')
            self.status='failed';return True
    def succeed(self):
        with self.lock:
            if self.status in('cancelled','failed'):raise ValueError('terminal guard')
            if self.status not in('running','waiting','reconciling','succeeded'):raise ValueError('controller state')
            if not self.required<=self.results.keys() or any(v in('running','unknown')for v in self.children.values()):raise ValueError('join not satisfied')
            if self.status=='succeeded':return False
            self.status='succeeded';return True
    def snapshot(self):
        with self.lock:return {'task':self.task,'attempt':self.attempt,'epoch':self.epoch,'plan':self.plan,'status':self.status,'budget':self.budget.snapshot(),'audit':copy.deepcopy(self.audit),'results':copy.deepcopy(self.results),'required':sorted(self.required),'children':copy.deepcopy(self.children)}
    @classmethod
    def _checked_snapshot(cls,s):
        fields={'task','attempt','epoch','plan','status','budget','audit','results','required','children'}
        if type(s)is not dict or set(s)!=fields:raise ValueError('controller snapshot fields')
        if any(type(s[k])is not str or not s[k]for k in('task','attempt')):raise ValueError('controller identity')
        integer(s['epoch'],1);integer(s['plan'],1)
        if s['status']not in('running','waiting','reconciling','cancelled','succeeded','failed'):raise ValueError('controller snapshot state')
        if type(s['required'])is not list or any(type(x)is not str or not x for x in s['required'])or len(s['required'])!=len(set(s['required'])):raise ValueError('controller required identities')
        if type(s['results'])is not dict or any(type(k)is not str or not k or type(v)is not dict or v.get('operation')!=k for k,v in s['results'].items()):raise ValueError('controller result identity')
        if type(s['children'])is not dict or any(type(k)is not str or not k or v not in('running','unknown','completed','failed','cancelled')for k,v in s['children'].items()):raise ValueError('controller child state')
        if type(s['audit'])is not list:raise ValueError('controller audit collection')
        canonical(s)
        Budget.restore(s['budget'])
        if s['status']=='succeeded'and(not set(s['required'])<=s['results'].keys()or any(v in('running','unknown')for v in s['children'].values())):raise ValueError('successful controller has incomplete join')
        return copy.deepcopy(s)
    @classmethod
    def restore(cls,s,current):
        """Use a complete current authority image, never an old budget cache.

        The caller supplies that authority; this finite model does not obtain or
        authenticate it. Contradictory or incomplete authority is rejected.
        """
        prior=cls._checked_snapshot(s);latest=cls._checked_snapshot(current)
        if prior['task']!=latest['task']:raise ValueError('controller recovery task identity')
        if prior['epoch']>latest['epoch']or prior['plan']>latest['plan']:raise ValueError('current control authority is older than checkpoint')
        if prior['epoch']==latest['epoch']and prior['attempt']!=latest['attempt']:raise ValueError('same epoch has contradictory attempt identity')
        if prior['status']in('cancelled','succeeded','failed')and prior['status']!=latest['status']:raise ValueError('current control state contradicts a known terminal fact')
        if prior['plan']==latest['plan']and set(prior['required'])!=set(latest['required']):raise ValueError('required plan changed without a new plan revision')
        if canonical(latest['audit'][:len(prior['audit'])])!=canonical(prior['audit']):raise ValueError('current control authority lost prior audit observations')
        for key,receipt in prior['results'].items():
            if key not in latest['results']or canonical(receipt)!=canonical(latest['results'][key]):raise ValueError('current control authority lost or contradicted a result')
        for key,state in prior['children'].items():
            if key not in latest['children']:raise ValueError('current control authority lost a child')
            if state in('completed','failed','cancelled')and latest['children'][key]!=state:raise ValueError('current control authority reopened a terminal child')
        budget=Budget.reconcile(prior['budget'],latest['budget'])
        c=cls(latest['task'],budget.limit);c.attempt=latest['attempt'];c.epoch=latest['epoch'];c.plan=latest['plan'];c.status=latest['status'];c.budget=budget;c.audit=latest['audit'];c.results=latest['results'];c.required=set(latest['required']);c.children=latest['children']
        return c

class Checkpoints:
    """Local atomic replace. Exact commit replay returns a historical receipt; load checks current references.

    No cross-node fencing, remote transaction, or power-loss durability guarantee.
    """
    def __init__(self,directory):self.directory=Path(directory);self.directory.mkdir(parents=True,exist_ok=True);self.lock=threading.RLock()
    def commit(self,commit_id,snapshot,refs,expected=None):
        with self.lock:
            if type(commit_id)is not str or not re.fullmatch(r'[A-Za-z0-9_.-]{1,80}',commit_id):raise ValueError('commit id')
            if type(refs)is not dict or any(type(p)is not str or not p or p.strip()!=p or type(h)is not str or not re.fullmatch('[0-9a-f]{64}',h)for p,h in refs.items()):raise ValueError('checkpoint reference identity')
            refs=dict(refs)
            pointer=self.directory/'current.json';prior=json.loads(pointer.read_text()) if pointer.exists() else None
            if prior and prior['commit_id']==commit_id:
                if prior['snapshot_digest']!=digest(snapshot) or prior['refs']!=refs:raise ValueError('commit id reused with conflicting snapshot or references')
                return prior
            if(prior['commit_id']if prior else None)!=expected:raise ValueError('checkpoint CAS conflict')
            for p,h in refs.items():
                q=self._reference(p)
                if not q.is_file() or hashlib.sha256(q.read_bytes()).hexdigest()!=h:raise ValueError('incomplete durable references')
            record={'commit_id':commit_id,'snapshot_digest':digest(snapshot),'snapshot':snapshot,'refs':refs}
            tmp=self.directory/(commit_id+'.tmp')
            with open(tmp,'w',encoding='utf-8')as f:f.write(canonical(record));f.flush();os.fsync(f.fileno())
            os.replace(tmp,pointer);return record
    def _reference(self,p):
        v=PurePosixPath(p)
        if v.is_absolute()or'..'in v.parts or '\\'in p:raise ValueError('reference path')
        q=self.directory/p
        if not q.resolve().is_relative_to(self.directory.resolve()):raise ValueError('reference escapes directory')
        return q
    def load(self):
        r=json.loads((self.directory/'current.json').read_text())
        if r['snapshot_digest']!=digest(r['snapshot']):raise ValueError('snapshot tamper')
        for p,h in r['refs'].items():
            q=self._reference(p)
            if not q.is_file()or hashlib.sha256(q.read_bytes()).hexdigest()!=h:raise ValueError('lost reference')
        return r

@dataclass
class Memory:
    tenant:str
    owner:str
    key:str
    version:int
    source:str
    fact_type:str
    content:object
    valid_until:int

class MemoryIndex:
    def __init__(self):self.rows={};self.tombstones={};self.acl={};self.derived={};self.restore_audit=[];self.lock=threading.RLock()
    def allow(self,principal,tenant):self.acl[(principal,tenant)]=True
    def revoke(self,principal,tenant):self.acl[(principal,tenant)]=False
    @staticmethod
    def _check_memory(m):
        if type(m)is not Memory:raise ValueError('memory record type')
        integer(m.version,1);integer(m.valid_until)
        if any(type(v)is not str or not v for v in(m.tenant,m.owner,m.key,m.source)):raise ValueError('memory identity')
        if m.fact_type not in ('verified','user-statement','preference','inference'):raise ValueError('fact type')
        canonical(m.content)
    def put(self,m,expected=None,principal=None):
        with self.lock:
            self._check_memory(m)
            if expected is not None:integer(expected,1)
            if principal!=m.owner or not self.acl.get((principal,m.tenant),False):raise PermissionError("memory write subject")
            k=(m.tenant,m.owner,m.key);old=self.rows.get(k)
            if m.version<=self.tombstones.get(k,0):raise ValueError('deleted generation')
            if (old.version if old else None)!=expected:raise ValueError('memory CAS conflict; current_version='+str(old.version if old else None))
            if old is not None and m.version<=old.version:raise ValueError('memory version must increase; current_version='+str(old.version))
            self.rows[k]=copy.deepcopy(m);self.derived[k]=[m.source];return k
    def delete(self,k,principal=None):
        with self.lock:
            if principal!=k[1] or not self.acl.get((principal,k[0]),False):raise PermissionError("memory delete subject")
            m=self.rows.pop(k,None);self.tombstones[k]=max(self.tombstones.get(k,0),m.version if m else 0)+1;self.derived.pop(k,None)
    def emit(self,principal,tenant,now=0,before_emit=None):
        with self.lock:
            if not self.acl.get((principal,tenant),False):raise PermissionError('read authorization')
            found=copy.deepcopy([m for k,m in self.rows.items()if m.tenant==tenant and m.owner==principal and m.version>self.tombstones.get(k,0)and now<m.valid_until])
        if before_emit:before_emit()
        with self.lock:
            if not self.acl.get((principal,tenant),False):raise PermissionError('revoked before output')
            return [m for m in found if (m.tenant,m.owner,m.key)in self.rows and m.version==self.rows[(m.tenant,m.owner,m.key)].version and m.version>self.tombstones.get((m.tenant,m.owner,m.key),0)]
    def restore_rows(self,rows):
        """Restore unique selected versions atomically; never restore ACLs.

        Stale rows and rows behind a current deletion are isolated, not activated.
        A currently deleted absent key requires an explicit authorized put for
        recreation, even when a backup proposes a higher version number.
        """
        with self.lock:
            if type(rows)not in(list,tuple):raise ValueError('finite memory restore batch required')
            staged=copy.deepcopy(self.rows);derived=copy.deepcopy(self.derived);outcomes=[];seen=set()
            for m in rows:
                self._check_memory(m)
                k=(m.tenant,m.owner,m.key)
                if k in seen:raise ValueError('duplicate memory restore key')
                seen.add(k);old=staged.get(k)
                observation={'key':list(k),'incoming_version':m.version,'incoming_digest':digest(asdict(m))}
                if m.version<=self.tombstones.get(k,0):
                    outcomes.append(dict(observation,status='isolated-deleted-generation'));continue
                if old is None and k in self.tombstones:
                    outcomes.append(dict(observation,status='isolated-current-deletion'));continue
                if old is not None and m.version<old.version:
                    outcomes.append(dict(observation,status='isolated-stale-version'));continue
                if old is not None and m.version==old.version:
                    if canonical(asdict(m))!=canonical(asdict(old)):raise ValueError('same memory version has conflicting content or provenance; current_version='+str(old.version))
                    outcomes.append(dict(observation,status='equivalent-current-version'));continue
                staged[k]=copy.deepcopy(m);derived[k]=[m.source]
                outcomes.append(dict(observation,status='restored-newer-version'if old else'restored-absent-version'))
            self.rows=staged;self.derived=derived;self.restore_audit.extend(copy.deepcopy(outcomes))
            return outcomes

REQUIRED_CONTEXT=('principal','tenant','goal','denials','sources','unknown_operations','accepted_decisions','root_budget','trust')
def verify_compression(before,after):
    for k in REQUIRED_CONTEXT:
        if k not in before or k not in after or canonical(before[k])!=canonical(after[k]):raise ValueError('semantic field lost or changed: '+k)
    return True

class Claims:
    def __init__(self):self.rows={}
    def record(self,key,dependencies,evidence_layer):
        for dep,value in dependencies.items():
            if dep.startswith('claim:') and (dep[6:]not in self.rows or self.rows[dep[6:]]['status']!=value):raise ValueError('invalid claim dependency')
        self.rows[key]={'dependencies':dict(dependencies),'layer':evidence_layer,'status':'fresh'}
    def invalidate(self,dependency,new_version):
        changed=[];queue=[(dependency,new_version)]
        while queue:
            dep,version=queue.pop(0)
            for k,r in self.rows.items():
                if dep in r['dependencies']and r['dependencies'][dep]!=version and r['status']!='stale':
                    r['status']='stale';changed.append(k);queue.append(('claim:'+k,'stale'))
        return changed
    def require(self,key,layer):
        r=self.rows[key]
        if r['status']!='fresh'or r['layer']!=layer:raise ValueError('evidence does not cover decision')
        return True

def mcp_result_type(result,extensions=()):
    rt=result.get('resultType','complete')
    if type(rt)is not str:raise ValueError('resultType must be a string')
    if rt not in {'complete','input_required',*extensions}:raise ValueError('unknown resultType')
    return rt

def rpc_id(value):
    if type(value)not in(str,int):raise ValueError('non-null string or integer id')
    return value

def mrtr_retry(initial,retry,state):
    rpc_id(initial['id']);rpc_id(retry['id'])
    if initial['id']==retry['id']:raise ValueError('MRTR new RPC id required')
    if initial['operation_id']!=retry['operation_id']:raise ValueError('logical intent changed')
    if initial['method']!=retry['method']or initial['arguments']!=retry['arguments']:raise ValueError('request binding changed')
    if state is None:
        if'requestState'in retry:raise ValueError('invented requestState')
    elif retry.get('requestState')!=state:raise ValueError('opaque state must echo exactly')
    return True

class RequestState:
    """HMAC test codec. It does not implement a production OAuth or network protocol."""
    def __init__(self,key):self.key=key;self.used={};self.lock=threading.RLock()
    def issue(self,principal,method,params,until,nonce):
        body=canonical({'principal':principal,'method':method,'digest':digest(params),'until':until,'nonce':nonce});return body+'\n'+hmac.new(self.key,body.encode(),'sha256').hexdigest()
    def consume(self,state,principal,method,params,operation,now=0):
        body,signature=state.rsplit('\n',1)
        if not hmac.compare_digest(signature,hmac.new(self.key,body.encode(),'sha256').hexdigest()):raise PermissionError('tamper')
        s=json.loads(body)
        if(s['principal'],s['method'],s['digest'])!=(principal,method,digest(params))or now>=s['until']:raise PermissionError('requestState binding')
        with self.lock:
            if s['nonce']in self.used:
                if self.used[s['nonce']]!=operation:raise PermissionError('single-use conflict')
                return 'same-operation-recovery'
            self.used[s['nonce']]=operation;return 'consumed'

def header_tools(tools,transport='http'):
    valid=[];rejected={};token=re.compile(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+\Z")
    for tool in tools:
        seen=set();reason=None
        for p in tool.get('parameters',[]):
            h=p.get('x-mcp-header')
            if h is None or transport!='http':continue
            if not isinstance(h,str)or not h or not token.fullmatch(h)or h.lower()in seen:reason='header name';break
            seen.add(h.lower())
            if p.get('type')not in('string','integer','boolean')or not p.get('statically_reachable',True):reason='header type/path';break
            if p.get('type')=='integer'and 'value'in p and(type(p['value'])is not int or abs(p['value'])>2**53-1):reason='unsafe integer';break
        if reason:rejected[tool['name']]=reason
        else:valid.append(tool)
    return valid,rejected

def cancellation_signal(protocol,transport):
    if protocol=='2026-07-28':return 'close-request-stream'if transport=='http'else'notifications/cancelled'
    raise ValueError('legacy binding must have separate contract')

@dataclass(frozen=True)
class RemoteKey:
    service:str;interface:str;principal:str;tenant:str;task:str;context:str

def accept_remote(expected,received,current_terminal=False):
    if expected!=received:raise PermissionError('remote task association')
    return 'historical-only'if current_terminal else'accepted'

def part(value):
    content=set(value)&{'text','raw','url','data'}
    if len(content)!=1:raise ValueError('oneof content')
    if 'text'in value and not isinstance(value['text'],str):raise ValueError('text type')
    # JSON serializability includes legitimate scalar/array/null data.
    canonical(value);return next(iter(content))

def release_compatible(old,new,required):
    for component in required:
        if old.get(component)!=new.get(component):return False
    return True

def archive_members(blob,max_total=10000,max_files=20):
    """Finite extraction admission, not a race-proof filesystem sandbox."""
    total=0;names=[]
    with zipfile.ZipFile(blob)as z:
        if len(z.infolist())>max_files:raise ValueError('file count')
        for i in z.infolist():
            p=PurePosixPath(i.filename);mode=i.external_attr>>16
            if p.is_absolute()or'..'in p.parts or '\\'in i.filename or (p.parts and ':'in p.parts[0]):raise ValueError('archive path')
            if stat.S_ISLNK(mode)or stat.S_ISCHR(mode)or stat.S_ISBLK(mode)or stat.S_ISFIFO(mode):raise ValueError('archive special file')
            if i.file_size>max_total-total:raise ValueError('declared expansion limit')
            with z.open(i)as member:
                while True:
                    chunk=member.read(min(65536,max_total-total+1))
                    if not chunk:break
                    total+=len(chunk)
                    if total>max_total:raise ValueError('actual expansion limit')
            names.append(i.filename)
    return names

class Decisions:
    def __init__(self):self.accepted={}
    def accept(self,decision_id,input_version,response,complete=True):
        if not complete:raise ValueError('incomplete model output is not an accepted decision')
        record={'input_version':input_version,'response':copy.deepcopy(response)}
        if decision_id in self.accepted:
            if self.accepted[decision_id]!=record:raise ValueError('accepted decision is immutable; explicit new plan required')
            return False
        self.accepted[decision_id]=record;return True

class StreamAssembler:
    """Adapter-envelope model, not a vendor SSE parser. Complete output remains a proposal."""
    def __init__(self,request,attempt,epoch):
        self.key=(request,attempt,epoch);self.status='open';self.chunks={};self.tool_done=set();self.audit=[];self.local_cancelled=False;self.remote_status='unknown'
    def feed(self,key,kind,item=None,sequence=None,data=None):
        self.audit.append((key,kind,item,sequence,data))
        if key!=self.key:return 'historical-only'
        if self.local_cancelled or self.status in('complete','incomplete','error','refusal','partial'):return 'historical-only'
        if kind in('text.delta','tool_args.delta'):
            integer(sequence);k=(kind,item);chunks=self.chunks.setdefault(k,{})
            if sequence in chunks and chunks[sequence]!=data:raise ValueError('contradictory duplicate delta')
            chunks[sequence]=data;return 'partial'
        if kind=='tool_args.done':self.tool_done.add(item);return 'tool-complete'
        if kind in('complete','incomplete','error','refusal'):self.status=kind;return kind
        if kind=='optional-diagnostic':return 'ignored-optional'
        self.status='error';raise ValueError('unsupported event contract')
    def fin(self):
        if self.status=='open':self.status='partial'
        return self.status
    def cancel(self):self.local_cancelled=True;return 'cancel-requested'
    def text(self,item):return ''.join(v for _,v in sorted(self.chunks.get(('text.delta',item),{}).items()))
    def tool_proposal(self,item):
        if self.local_cancelled or self.status!='complete' or item not in self.tool_done:raise ValueError('not a complete callable proposal')
        parts=self.chunks.get(('tool_args.delta',item),{})
        if sorted(parts)!=list(range(len(parts))):raise ValueError('missing tool argument sequence')
        raw=''.join(v for _,v in sorted(parts.items()));value=json.loads(raw)
        if not isinstance(value,dict):raise ValueError('model function arguments must be an object for this profile')
        return value

def task_result_status(status,result):
    if status!='completed':return 'not-final'
    if result.get('isError',False):return 'tool-failed'
    return 'tool-result-needs-business-validation'

class RemoteTaskTracker:
    STATES={'submitted','working','input-required','auth-required','completed','failed','canceled','rejected'}
    TERMINAL={'completed','failed','canceled','rejected'}
    def __init__(self,key):self.key=key;self.state='submitted';self.connected=True;self.cancel_requested=False;self.artifacts={}
    def update(self,key,state):
        accept_remote(self.key,key)
        if state not in self.STATES:raise ValueError('unknown remote task state')
        if self.state in self.TERMINAL:return 'historical-only'
        self.state=state;return 'accepted'
    def disconnect(self):self.connected=False;return self.state
    def request_cancel(self):self.cancel_requested=True;return self.state
    def artifact(self,key,artifact_id,content,append=False,last=False):
        accept_remote(self.key,key);k=(key,artifact_id)
        if append:
            # A2A does not supply a universal event sequence. Never pretend ambiguous retries are safe concatenation.
            self.artifacts[k]={'status':'needs-authority-query','last_chunk':last};return 'needs-authority-query'
        self.artifacts[k]={'content':copy.deepcopy(content),'status':'complete'if last else'partial','last_chunk':last};return self.artifacts[k]['status']

class RpcOutstanding:
    def __init__(self):self.pending=set()
    def issue(self,value):
        rpc_id(value)
        if value in self.pending:raise ValueError('request id already outstanding')
        self.pending.add(value)
    def respond(self,value):
        rpc_id(value)
        if value not in self.pending:raise ValueError('unmatched response id')
        self.pending.remove(value)


class Inbox:
    """Finite event inbox. Persist/transactional consumption must be supplied by a real adapter."""
    def __init__(self):self.events={};self.consumed=set();self.lock=threading.RLock()
    def put(self,event,interrupt,params,epoch,decision):
        row=(interrupt,digest(params),epoch,decision)
        with self.lock:
            if event in self.events and self.events[event]!=row:raise ValueError('event identity changed')
            self.events[event]=row
    def find(self,interrupt,params,epoch):
        with self.lock:
            return [e for e,r in self.events.items() if e not in self.consumed and r[:3]==(interrupt,digest(params),epoch)]
    def consume(self,event,interrupt,params,epoch):
        with self.lock:
            if event in self.consumed:return 'duplicate'
            row=self.events[event]
            if row[:3]!=(interrupt,digest(params),epoch):raise ValueError('wake binding')
            self.consumed.add(event);return row[3]
