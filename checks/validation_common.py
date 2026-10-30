"""Shared deterministic validation primitives."""
import sys
if sys.flags.optimize:
    raise RuntimeError('Validation requires assertions enabled; do not use -O or -OO')
from pathlib import Path, PurePosixPath
import hashlib, json, re, unicodedata, math

class ValidationError(AssertionError):
    pass

def require(condition, message, *context):
    if not condition:
        raise ValidationError((message, *context) if context else message)

def digest(value):
    return hashlib.sha256(value.encode('utf-8') if isinstance(value, str) else value).hexdigest()

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)

def finite_json_float(text):
    value=float(text)
    require(math.isfinite(value),'JSON floating number exceeds this finite implementation range',text)
    mantissa=re.split('[eE]',text)[0]
    require(value!=0.0 or not re.search('[1-9]',mantissa),'JSON floating number underflows this finite implementation range',text)
    return value

def read_json(path):
    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value, 'duplicate JSON key', str(path), key)
            value[key] = item
        return value
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=pairs, parse_float=finite_json_float,
                          parse_constant=lambda v: (_ for _ in ()).throw(ValidationError('nonfinite JSON: '+v)))
    except (ValueError, OSError) as exc:
        raise ValidationError(('unreadable JSON', str(path), str(exc))) from exc

def read_text_exact(path):
    return Path(path).read_bytes().decode('utf-8')

def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='\n')

def safe_path(root, value, *, base=None, allow_parent=False, kind='file'):
    root = Path(root).resolve()
    require(type(value) is str and value.strip() == value and value, 'relative path string required', value)
    require('\\' not in value and '\x00' not in value and not re.match(r'^[A-Za-z]:', value), 'nonportable path', value)
    rel = PurePosixPath(value)
    require(not rel.is_absolute(), 'absolute path prohibited', value)
    require(allow_parent or '..' not in rel.parts, 'parent traversal prohibited', value)
    candidate = (Path(base) if base is not None else root) / value
    resolved = candidate.resolve()
    require(resolved.is_relative_to(root), 'path escapes repository (including symlink)', value)
    if kind == 'file':
        require(resolved.is_file(), 'missing file', value)
    elif kind == 'directory':
        require(resolved.is_dir(), 'missing directory', value)
    elif kind == 'any':
        require(resolved.exists(), 'missing target', value)
    return resolved

ROOT_LITERAL_PREFIXES={'standards','registry','checks','tests','examples','sources','governance','assets','docs','.github'}
def resolve_local_reference(root,source,value,*,reference_kind='inline'):
    """Markdown URLs stay relative; documented repository code paths are explicit."""
    root=Path(root).resolve();source=Path(source).resolve()
    require(source.is_relative_to(root),'reference source escapes repository')
    require(type(value) is str,'reference path string required')
    path=value or source.name;base=source.parent
    if reference_kind=='literal-path' and value and not value.startswith(('./','../')) and PurePosixPath(value).parts[0] in ROOT_LITERAL_PREFIXES:
        base=root
        # A colliding local interpretation is not silently guessed. Authors may
        # use ./ for the local object; ordinary Markdown links are always local.
        local=(source.parent/value).resolve();rooted=(root/value).resolve()
        require(not (local.exists() and rooted.exists() and local!=rooted),'ambiguous literal repository/local path; use explicit relative spelling',value)
    return safe_path(root,path,base=base,allow_parent=True,kind='any')

def normalized(value):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', value)).strip()

def unique(rows, key, label):
    values = [row[key] for row in rows]
    require(len(values) == len(set(values)), 'duplicate '+label, values)
    return {row[key]: row for row in rows}

BAD = {'', 'todo', 'tbd', 'undefined', 'none', 'null', 'n/a', '待补充', '待定', '—'}
def substantive(value):
    return type(value) is str and normalized(value).casefold() not in BAD
