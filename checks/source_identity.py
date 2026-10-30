"""Local fixed-source identity checker; not remote freshness, rights or trust validation."""
import sys
if sys.flags.optimize:
    raise RuntimeError('Validation requires assertions enabled; do not use -O or -OO')
from pathlib import Path
import hashlib,re

class IdentityError(ValueError):
    pass

def verify_sources(root, records):
    root=Path(root).resolve()
    if not isinstance(records,list) or not records:
        raise IdentityError('nonempty component list required')
    seen=set(); verified=[]
    for r in records:
        if not isinstance(r,dict) or set(r)!={'component','path','sha256','role'}:
            raise IdentityError('exact record fields required')
        if any(not isinstance(r[k],str) or not r[k].strip() for k in r):
            raise IdentityError('nonempty strings required')
        if r['component'] in seen:
            raise IdentityError('duplicate component identity')
        seen.add(r['component'])
        if r['role'] not in {'source','generated-input','artifact'}:
            raise IdentityError('unknown component role')
        if not re.fullmatch('[0-9a-f]{64}',r['sha256']):
            raise IdentityError('lowercase SHA256 required')
        relative=Path(r['path'])
        if r['path'].strip()!=r['path'] or '\\' in r['path'] or '\x00' in r['path'] or re.match(r'^[A-Za-z]:',r['path']) or relative.is_absolute() or '..' in relative.parts:
            raise IdentityError('path must remain inside selected snapshot')
        path=(root/relative).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise IdentityError('missing file or escaped snapshot')
        # Snapshot must be immutable during validation; this does not establish
        # adversarial race safety or provenance authentication.
        actual=hashlib.sha256(path.read_bytes()).hexdigest()
        if actual!=r['sha256']:
            raise IdentityError('component digest mismatch')
        verified.append({'component':r['component'],'sha256':actual,'role':r['role']})
    return verified
