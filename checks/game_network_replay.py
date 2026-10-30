"""Synthetic single-authority control and integer replay profiles; not a game runtime."""
import sys
if sys.flags.optimize:
    raise RuntimeError('Validation requires assertions enabled; do not use -O or -OO')
import hashlib,json,re,threading
HASH=re.compile(r'[0-9a-f]{64}\Z')
def digest(value):
 def valid(v):
  if v is None or type(v) in (str,bool,int):return
  if type(v) is list:
   for x in v:valid(x)
   return
  if type(v) is dict and all(type(k) is str for k in v):
   for x in v.values():valid(x)
   return
  raise ValueError('profile accepts JSON without floating point or non-string keys')
 valid(value)
 return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def require_hash(value):
 if type(value) is not str or not HASH.fullmatch(value):raise ValueError('SHA256 identity required')
def nonempty(value):
 if type(value) is not str or not value.strip():raise ValueError('nonempty identity required')
class ControlAuthority:
 """In-memory single-controller-per-entity profile, allowing many entities per player."""
 def __init__(self,owners):
  for entity,player in owners.items():nonempty(entity);nonempty(player)
  self.owners=dict(owners);self.epochs={};self.events={};self.effects={};self.lock=threading.RLock()
 def reconnect(self,player):
  nonempty(player)
  with self.lock:
   self.epochs[player]=self.epochs.get(player,-1)+1
   return self.epochs[player]
 def apply(self,player,entity,epoch,event_id,payload):
  nonempty(player);nonempty(entity);nonempty(event_id)
  if type(epoch) is not int or epoch<0:raise ValueError('integer connection generation')
  payload_hash=digest({'entity':entity,'payload':payload})
  with self.lock:
   if self.epochs.get(player)!=epoch or self.owners.get(entity)!=player:raise PermissionError('stale control or wrong entity ownership')
   key=(player,event_id)
   if key in self.events:
    if self.events[key]!=payload_hash:raise ValueError('event identity reused with different payload')
    return False
   self.events[key]=payload_hash;self.effects[entity]=self.effects.get(entity,0)+1
   return True

def validate_manifest(manifest,expected):
 kind=manifest.get('kind')
 if kind=='video':
  require_hash(manifest.get('file_sha256'))
  return 'video-identity-only-not-decoded'
 if kind!='simulation':raise ValueError('unknown recording kind')
 for key in ['rules_sha256','content_sha256','profile']:
  if manifest.get(key)!=expected.get(key) or manifest.get(key) is None:raise ValueError('unsupported replay contract')
 for key in ['rules_sha256','content_sha256','initial_state_sha256','inputs_sha256']:require_hash(manifest.get(key))
 nonempty(manifest.get('profile'))
 if type(expected.get('requires_randomness')) is not bool or type(manifest.get('requires_randomness')) is not bool or manifest['requires_randomness']!=expected.get('requires_randomness'):raise ValueError('randomness contract mismatch')
 if manifest['requires_randomness']:
  rng=manifest.get('randomness',{})
  nonempty(rng.get('algorithm'));nonempty(rng.get('version'));require_hash(rng.get('material_sha256'))
 return 'manifest-consistent-not-runtime-verified'

def toy_replay(manifest,expected,initial,events):
 validate_manifest(manifest,expected)
 if manifest['kind']!='simulation' or manifest['requires_randomness'] or manifest['profile']!='toy-integer-add-v1':raise ValueError('unsupported toy runtime profile')
 if type(events) is not list:raise ValueError('input log must be a list')
 if digest(initial)!=manifest['initial_state_sha256'] or digest(events)!=manifest['inputs_sha256']:raise ValueError('replay material identity mismatch')
 if type(initial) is not dict or any(type(v) is not int for v in initial.values()):raise ValueError('integer positions required')
 state=dict(initial)
 for seq,event in enumerate(events,1):
  if type(event) is not dict or set(event)!={'sequence','entity','delta'} or type(event['sequence']) is not int or event['sequence']!=seq:raise ValueError('recorded input order')
  if event['entity'] not in state or type(event['delta']) is not int:raise ValueError('invalid toy input')
  state[event['entity']]+=event['delta']
 return state
