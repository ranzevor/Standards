"""Verify Standards release file identities in ZIPs or unpacked directories."""
from __future__ import annotations
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import unicodedata
import zipfile

MANIFEST = 'BUNDLE-MANIFEST.json'
SCHEMA = 'ranzevor-standards-bundle/1'
INITIAL_VERSION = '0.1.0'
DOCUMENT_COUNT = 162
VERSION_PATTERN = r'0\.1\.(?:0|[1-9][0-9]*)'
RELEASE_VERSION_PATTERN = r'(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)'
MAX_FILES = 5000
MAX_BYTES = 600_000_000
MAX_MANIFEST_BYTES = 4_000_000
REGISTRY_FIELDS = {'id','title','path','domain','version','status','language','effective_date','sha256'}
MANIFEST_FIELDS = {'schema','kind','root','version','normative_language','document_count',
                   'adopted_document_count','current_snapshot_sha256','source_tree_sha256',
                   'rights_notice','license_policy','license_grant',
                   'public_distribution_authorized','description','files'}

class VerificationError(ValueError):
    pass

def fail_if(condition: bool, message: str):
    if condition:
        raise VerificationError(message)

def valid_version(value):
    """Individual normative document version under the current adopted corpus."""
    return isinstance(value, str) and re.fullmatch(VERSION_PATTERN, value) is not None


def valid_release_version(value):
    """Distribution version, independent of individual normative documents."""
    return isinstance(value, str) and re.fullmatch(RELEASE_VERSION_PATTERN, value) is not None


def valid_date(value):
    if not isinstance(value, str) or re.fullmatch(r'\d{4}-\d{2}-\d{2}', value) is None:
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def validate_release_config(config, version=None):
    fields = {'schema', 'version', 'previous_version', 'notes_path'}
    fail_if(type(config) is not dict or set(config) != fields or
            config.get('schema') != 'standards-release/1', 'invalid release configuration')
    current, previous = config['version'], config['previous_version']
    fail_if(not valid_release_version(current), 'unsupported release version')
    if current == INITIAL_VERSION:
        fail_if(previous is not None, 'initial release must not declare a previous version')
    else:
        fail_if(not valid_release_version(previous), 'subsequent release requires a previous version')
        major, minor, patch = (int(item) for item in current.split('.'))
        old_major, old_minor, old_patch = (int(item) for item in previous.split('.'))
        next_patch = major == old_major and minor == old_minor and patch == old_patch + 1
        next_minor = major == old_major and minor == old_minor + 1 and patch == 0
        next_major = major == old_major + 1 and minor == 0 and patch == 0
        fail_if(not (next_patch or next_minor or next_major),
                'release must advance by one patch, next minor .0, or next major .0')
    fail_if(version is not None and current != version, 'release configuration version mismatch')
    fail_if(config['notes_path'] != 'releases/v' + current + '.md', 'release notes path mismatch')
    return config


def validate_project_release(project, version=None):
    fail_if(type(project) is not dict or project.get('name')!='Standards' or not valid_release_version(project.get('version')),
            'invalid project release version')
    fail_if(version is not None and project['version'] != version,
            'project and bundle release versions differ')
    return project['version']


def checked_path(name: str):
    fail_if(not isinstance(name,str) or not name or '\\' in name or '\x00' in name,
            'invalid archive path')
    path=PurePosixPath(name)
    fail_if(path.is_absolute() or name!=path.as_posix() or
            any(part in ('','.','..') for part in name.split('/')) or
            any(':' in part for part in path.parts),
            'unsafe or noncanonical archive path: '+name)
    for part in path.parts:
        fail_if(any(ord(char)<32 or char in '<>"|?*' for char in part) or
                part.endswith((' ','.')),
                'nonportable archive component: '+part)
        # Win32 device names remain reserved when followed by an extension.
        # Superscript 1/2/3 also identify COM/LPT devices on Windows.
        stem=part.split('.',1)[0].rstrip(' ').casefold()
        fail_if(stem in {'con','prn','aux','nul','conin$','conout$'} or
                re.fullmatch(r'(?:com|lpt)[1-9¹²³]',stem) is not None,
                'reserved Windows archive component: '+part)
    return path

def check_path_set(names):
    """Reject aliases and file/directory collisions before accessing bytes."""
    folded=set();paths=[]
    for name in names:
        path=checked_path(name)
        paths.append(path)
        key=unicodedata.normalize('NFC',name).casefold()
        fail_if(key in folded,'path collision: '+name)
        folded.add(key)
    for key in folded:
        parts=key.split('/')
        fail_if(any('/'.join(parts[:n]) in folded for n in range(1,len(parts))),
                'file/directory collision: '+key)
    spellings={}
    for path in paths:
        # A/one and a/two conflict at their directory, even though their full
        # filenames differ. Preserve exact spellings; never silently rename.
        for length in range(1,len(path.parts)+1):
            prefix='/'.join(path.parts[:length])
            normalized=unicodedata.normalize('NFC',prefix).casefold()
            previous=spellings.setdefault(normalized,prefix)
            fail_if(previous!=prefix,'path component collision: '+prefix)

def parse_json(raw: bytes):
    def pairs(value):
        result={}
        for key,item in value:
            fail_if(key in result,'duplicate JSON key')
            result[key]=item
        return result
    try:
        return json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,
                          parse_constant=lambda value: (_ for _ in ()).throw(
                              VerificationError('invalid nonfinite JSON')))
    except (UnicodeError,json.JSONDecodeError) as exc:
        raise VerificationError('invalid JSON/UTF-8') from exc

def canonical(value):
    return (json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode('utf-8')

def is_digest(value):
    return isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) is not None

def validate_document_identity(row, raw):
    """Bind readable title/ID/version to bytes, not merely a matching digest."""
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise VerificationError('invalid normative UTF-8: '+row['id']) from exc
    fail_if(not text.splitlines() or text.splitlines()[0] != '# '+row['title'],
            'normative title differs from registry: '+row['id'])
    header = text.split('\n## ', 1)[0]
    for label, key in [('文档ID', 'id'), ('版本', 'version'),
                       ('状态', 'status'), ('生效日期', 'effective_date')]:
        values = re.findall(r'\*\*'+label+r'[：:]\*\*\s*([^\s*]+)', header)
        fail_if(values != [row[key]], 'normative '+key+' differs from registry: '+row['id'])
    fail_if(PurePosixPath(row['path']).name.split('-', 1)[0] != row['id'].rsplit('-', 1)[1],
            'normative path number differs from document ID: '+row['id'])
    return text

def validate_manifest(manifest):
    fail_if(type(manifest) is not dict or set(manifest)!=MANIFEST_FIELDS or
            manifest.get('schema')!=SCHEMA,'unknown bundle manifest schema or fields')
    kind,root,version=manifest['kind'],manifest['root'],manifest['version']
    fail_if(not valid_release_version(version) or manifest['normative_language']!='zh-Hans',
            'wrong release identity')
    fail_if(kind not in ('source','agent-skill') or
            root!=('Standards-v'+version if kind=='source' else 'ranzevor-standards'),
            'unsupported archive kind/root')
    fail_if(type(manifest['document_count']) is not int or
            type(manifest['adopted_document_count']) is not int or
            manifest['document_count']!=DOCUMENT_COUNT or
            manifest['adopted_document_count']!=DOCUMENT_COUNT,'published document counts mismatch')
    fail_if(not is_digest(manifest['current_snapshot_sha256']) or
            not is_digest(manifest['source_tree_sha256']),'invalid collection digest')
    fail_if(type(manifest['description']) is not str or not manifest['description'].strip(),
            'invalid bundle description')
    prefix='source/' if kind=='source' else 'references/'
    fail_if(manifest['license_grant']!='multi-license: CC-BY-4.0 and Apache-2.0' or
            manifest['license_policy']!=prefix+'LICENSE' or
            manifest['rights_notice']!=prefix+'LICENSE-NOTICE.md' or
            manifest['public_distribution_authorized'] is not True,
            'release license/distribution decision mismatch')
    entries=manifest['files']
    fail_if(type(entries) is not list or not entries or len(entries)>MAX_FILES,'invalid file listing')
    for row in entries:
        fail_if(type(row) is not dict or set(row)!={'path','bytes','sha256'},'invalid file row fields')
        checked_path(row['path'])
        fail_if(row['path']==MANIFEST,'manifest cannot list itself')
        fail_if(type(row['bytes']) is not int or not 0<=row['bytes']<=MAX_BYTES or
                not is_digest(row['sha256']),'invalid file identity')
    check_path_set([row['path'] for row in entries]+[MANIFEST])
    fail_if(sum(row['bytes'] for row in entries)>MAX_BYTES,'bundle over size budget')
    paths={row['path'] for row in entries}
    wrappers={'verify.py'} if kind=='source' else {'SKILL.md','scripts/verify_bundle.py','scripts/lookup.py'}
    fail_if(any(not path.startswith(prefix) and path not in wrappers for path in paths),
            'unknown bundle entry')
    required={prefix+name for name in ('registry/standards.json','registry/requirements.json',
              'LICENSE','LICENSES/Apache-2.0.txt','LICENSES/CC-BY-4.0.txt','LICENSE-NOTICE.md',
              'NOTICE.md','project.json','releases/current.json')}
    fail_if(not (required|wrappers)<=paths,'bundle required files missing')
    source_rows=sorted((row['path'][len(prefix):],row['bytes'],row['sha256'])
                       for row in entries if row['path'].startswith(prefix))
    fail_if(hashlib.sha256(canonical(source_rows)).hexdigest()!=manifest['source_tree_sha256'],
            'source tree SHA-256 mismatch')
    return root,{row['path']:row for row in entries}

def validate_registry_bytes(registry,read_file):
    """Bind the adopted registry to its unique normative document bytes."""
    fail_if(type(registry) is not list or len(registry)!=DOCUMENT_COUNT,
            'current document registry count mismatch')
    identifiers,paths,snapshot=set(),set(),[]
    for row in registry:
        fail_if(type(row) is not dict or set(row)!=REGISTRY_FIELDS,'invalid normative registry fields')
        ident,path=row['id'],row['path']
        fail_if(type(ident) is not str or re.fullmatch(
                r'STD-(?:L[0-6](?:-[A-Z0-9]+(?:-[A-Z0-9]+)*)?|PG)-\d{3}',ident) is None or
                ident in identifiers,'duplicate or invalid document ID')
        checked_path(path)
        version=row['version']
        fail_if(not valid_version(version), 'invalid current document version')
        fail_if(not path.startswith('standards/') or re.fullmatch(
                r'\d{3}-.+--v'+re.escape(version)+r'\.md',PurePosixPath(path).name) is None or path in paths,
                'invalid current document path/version')
        fail_if(any(type(row[key]) is not str or not row[key].strip() for key in ('title','domain')) or
                row['status']!='adopted' or
                row['language']!='zh-Hans' or not valid_date(row['effective_date']) or
                not is_digest(row['sha256']),'invalid adopted document metadata: '+ident)
        identifiers.add(ident);paths.add(path)
        try:
            actual=read_file(path)
        except (KeyError,FileNotFoundError) as exc:
            raise VerificationError('missing registered normative source: '+path) from exc
        fail_if(type(actual) is not bytes,'normative reader must return bytes')
        digest=hashlib.sha256(actual).hexdigest()
        fail_if(digest!=row['sha256'],'current normative digest mismatch: '+path)
        validate_document_identity(row, actual)
        snapshot.append((ident,path,len(actual),digest,row['version'],row['status']))
    check_path_set(paths)
    return {'documents':DOCUMENT_COUNT,'adopted':DOCUMENT_COUNT,
            'current_snapshot_sha256':hashlib.sha256(canonical(sorted(snapshot))).hexdigest()},paths

def _decode_physical_line(raw: bytes) -> str:
    """Decode one bytes.splitlines() record without Unicode line-separator splitting."""
    if raw.endswith(b'\r\n'):
        raw = raw[:-2]
    elif raw.endswith((b'\r', b'\n')):
        raw = raw[:-1]
    return raw.decode('utf-8')


def _markdown_headings(lines: list[bytes]) -> dict[int, tuple[int, str]]:
    """Locate headings using the corpus parser's fence and comment semantics."""
    result = {}
    fence = None
    in_comment = False
    for number, raw in enumerate(lines, 1):
        line = _decode_physical_line(raw)
        if fence is not None:
            marker, width = fence
            if re.fullmatch(r'[ \t]{0,3}' + re.escape(marker) + '{' + str(width) + r',}[ \t]*', line):
                fence = None
            continue
        if not in_comment:
            opening = re.match(r'^[ \t]{0,3}(`{3,}|~{3,})', line)
            if opening:
                fence = (opening[1][0], len(opening[1]))
                continue
        visible = list(line)
        offset = 0
        while offset < len(line):
            if in_comment:
                if line.startswith('<!--', offset):
                    raise ValueError('nested Markdown comment in indexed document')
                if line.startswith('-->', offset):
                    visible[offset:offset + 3] = '   '
                    offset += 3
                    in_comment = False
                    continue
                visible[offset] = ' '
                offset += 1
                continue
            if line[offset] == '`':
                ticks = re.match(r'`+', line[offset:])[0]
                closing = line.find(ticks, offset + len(ticks))
                if closing >= 0:
                    offset = closing + len(ticks)
                    continue
            if line.startswith('<!--', offset):
                visible[offset:offset + 4] = '    '
                offset += 4
                in_comment = True
                continue
            offset += 1
        heading = re.fullmatch(r'(#{1,6})[ \t]+(.+?)(?:[ \t]+#+)?[ \t]*', ''.join(visible))
        if heading:
            result[number] = (len(heading[1]), heading[2])
    if fence is not None or in_comment:
        raise ValueError('unclosed Markdown fence or comment in indexed document')
    return result


CLAUSE_HEADING = re.compile(
    r'^(§\d{1,3}|[A-Z][A-Z0-9]*(?:-[A-Z][A-Z0-9]*)?-?\d{1,4})'
    r'(?=[\s：:、])(?:[\s：:、]+)(.+)$'
)


def _parsed_clause_spans(headings: dict[int, tuple[int, str]], line_count: int):
    """Mirror the corpus parser's clause selection and heading boundaries."""
    all_headings = [(number, level, title, CLAUSE_HEADING.match(title))
                    for number, (level, title) in headings.items()]
    labelled = [item for item in all_headings if item[1] > 1 and item[3] is not None]
    selected = labelled or [item for item in all_headings if item[1] == 2]
    if not selected:
        raise ValueError('indexed document has no parseable clauses')
    spans = {}
    titles = set()
    for number, level, heading, match in selected:
        title = match[2] if match else heading
        normalized_heading = re.sub(r'\s+', ' ', unicodedata.normalize('NFC', heading)).strip()
        identity = match[1] if match else 'H-' + hashlib.sha256(
            normalized_heading.encode('utf-8')).hexdigest()[:12]
        if identity in spans:
            raise ValueError('duplicate parsed clause identity')
        end = next((candidate[0] for candidate in all_headings
                    if candidate[0] > number and candidate[1] <= level), line_count + 1) - 1
        parent = None
        normative_start = number
        if '核验合同' in title:
            parent = next((candidate for candidate in reversed(all_headings)
                           if candidate[0] < number and candidate[1] < level), None)
            if match:
                if parent is None or parent[1] <= 1:
                    raise ValueError('normative chapter heading missing')
                if sum(parent[0] < candidate[0] <= end for candidate in selected) != 1:
                    raise ValueError('ambiguous chapter-to-contract mapping')
                normative_start = parent[0]
        qualified_title = (parent[2] if parent else '') + '::' + title if '核验合同' in title else title
        normalized_title = re.sub(r'\s+', ' ', unicodedata.normalize('NFC', qualified_title)).strip()
        if normalized_title in titles:
            raise ValueError('duplicate parsed clause title')
        titles.add(normalized_title)
        spans[identity] = {'line': number, 'end_line': end,
                           'normative_start_line': normative_start,
                           'heading': heading, 'title': title}
    return spans


def validate_clause_registry(clauses, documents, read_file, document_ids=None):
    """Verify exact source binding and the entire indexed clause set per document."""
    fail_if(type(clauses) is not list, 'invalid clause registry')
    registry={doc['id']:doc for doc in documents}
    requested=set(registry) if document_ids is None else set(document_ids)
    fail_if(not requested<=registry.keys(), 'unknown indexed document')
    by_document={ident:[] for ident in requested}
    seen=set()
    for row in clauses:
        fail_if(type(row) is not dict, 'invalid clause registry row')
        document_id=row.get('document_id')
        clause_id=row.get('clause_id')
        fail_if(type(document_id) is not str or not document_id or
                type(clause_id) is not str or not clause_id or
                row.get('id')!=document_id+'::'+clause_id,
                'clause registry identity mismatch')
        key=(document_id,clause_id)
        fail_if(key in seen, 'duplicate clause registry identity')
        seen.add(key)
        fail_if(document_id not in registry, 'clause references unknown document')
        if document_id in by_document:
            by_document[document_id].append(row)

    for document_id in sorted(requested):
        document=registry[document_id]
        raw=read_file(document['path'])
        fail_if(type(raw) is not bytes, 'indexed document must be bytes')
        lines=raw.splitlines(keepends=True)
        parsed=_parsed_clause_spans(_markdown_headings(lines),len(lines))
        indexed=set()
        for row in by_document[document_id]:
            fail_if(row.get('path')!=document['path'] or
                    row.get('document')!=document['path'] or
                    row.get('version')!=document['version'] or
                    row.get('document_sha256')!=document['sha256'],
                    'clause document identity mismatch')
            start,end=row.get('line'),row.get('end_line')
            normative_start,normative_end=row.get('normative_start_line'),row.get('normative_end_line')
            fail_if(type(start) is not int or type(end) is not int or
                    not 1<=start<=end<=len(lines), 'invalid clause span')
            fail_if(type(normative_start) is not int or type(normative_end) is not int or
                    not 1<=normative_start<=start<=end<=normative_end<=len(lines),
                    'invalid normative clause span')
            actual=parsed.get(row['clause_id'])
            fail_if(actual is None or actual['heading']!=row.get('heading') or
                    actual['title']!=row.get('title'), 'clause heading identity mismatch')
            fail_if(start!=actual['line'], 'clause heading location mismatch')
            fail_if(end!=actual['end_line'], 'clause span boundary mismatch')
            fail_if(normative_start!=actual['normative_start_line'] or normative_end!=actual['end_line'],
                    'normative span binding mismatch')
            fail_if(hashlib.sha256(b''.join(lines[start-1:end])).hexdigest()!=row.get('section_sha256'),
                    'clause content digest mismatch')
            fail_if(hashlib.sha256(b''.join(lines[normative_start-1:normative_end])).hexdigest()!=row.get('normative_sha256'),
                    'normative clause digest mismatch')
            indexed.add(row['clause_id'])
        fail_if(indexed!=set(parsed), 'clause registry coverage mismatch: '+document_id)
    return clauses


def validate_adopted_bytes(manifest,read_file):
    prefix='source/' if manifest['kind']=='source' else 'references/'
    version=manifest['version']
    validate_project_release(parse_json(read_file(prefix+'project.json')),version)
    config=validate_release_config(parse_json(read_file(prefix+'releases/current.json')),version)
    fail_if(not read_file(prefix+config['notes_path']).strip(), 'release notes are empty')
    if manifest['kind']=='agent-skill':
        skill=read_file('SKILL.md').decode('utf-8')
        fail_if(not skill.startswith('---\n') or '\n---\n' not in skill, 'invalid Skill frontmatter')
        frontmatter=skill.split('\n---\n',1)[0]
        fail_if(re.findall(r'^  version: "([^"\r\n]+)"$',frontmatter,re.M)!=[version],
                'Skill and release versions differ')
    wrappers=({'verify.py':'tools/verify_release_bundle.py'} if manifest['kind']=='source' else {
        'SKILL.md':'skills/ranzevor-standards/SKILL.md.in',
        'scripts/verify_bundle.py':'tools/verify_release_bundle.py',
        'scripts/lookup.py':'tools/skill_lookup.py',
    })
    for wrapper,original in wrappers.items():
        try:
            actual=read_file(wrapper);expected=read_file(prefix+original)
        except (KeyError,FileNotFoundError) as exc:
            raise VerificationError('wrapper source missing: '+original) from exc
        fail_if(type(actual) is not bytes or type(expected) is not bytes or actual!=expected,
                'wrapper differs from packaged source: '+wrapper)
    registry=parse_json(read_file(prefix+'registry/standards.json'))
    summary,paths=validate_registry_bytes(registry,lambda path:read_file(prefix+path))
    validate_clause_registry(parse_json(read_file(prefix+'registry/requirements.json')),
                             registry,lambda path:read_file(prefix+path))
    listed={row['path'][len(prefix):] for row in manifest['files']
            if row['path'].startswith(prefix+'standards/') and row['path'].endswith('.md')
            and PurePosixPath(row['path']).name!='README.md'}
    fail_if(listed!=paths,'registered and packaged normative file sets differ')
    fail_if(summary['current_snapshot_sha256']!=manifest['current_snapshot_sha256'],
            'current document collection SHA-256 mismatch')
    return summary

def digest_of_file(path: Path):
    with path.open('rb') as source:
        return hashlib.file_digest(source,'sha256').hexdigest()

def verify_zip(path: Path):
    with zipfile.ZipFile(path,'r') as archive:
        infos=archive.infolist()
        fail_if(not infos or len(infos)>MAX_FILES+1,'invalid archive entry count')
        names=[info.filename for info in infos]
        check_path_set(names)
        fail_if(sum(info.file_size for info in infos)>MAX_BYTES,'archive inflated size too large')
        for info in infos:
            fail_if(info.is_dir(),'directory entries are not part of canonical bundle')
            mode=stat.S_IFMT(info.external_attr>>16)
            fail_if(mode==stat.S_IFLNK,'symlink entry forbidden')
            fail_if(mode not in (0,stat.S_IFREG),'special archive entry forbidden')
            fail_if(info.flag_bits&1!=0,'encrypted archive entry forbidden')
        by_name={info.filename:info for info in infos}
        roots={name.split('/',1)[0] for name in names}
        fail_if(len(roots)!=1,'archive must have one root')
        root=next(iter(roots));manifest_path=root+'/'+MANIFEST
        fail_if(manifest_path not in by_name,'bundle manifest missing')
        fail_if(by_name[manifest_path].file_size>MAX_MANIFEST_BYTES,'bundle manifest too large')
        manifest_raw=archive.read(manifest_path)
        manifest=parse_json(manifest_raw)
        intended,expected=validate_manifest(manifest)
        fail_if(root!=intended,'wrong root for manifest')
        fail_if(set(names)!={root+'/'+name for name in expected}|{manifest_path},
                'unlisted or missing archive files')
        for relative,row in expected.items():
            info=by_name[root+'/'+relative]
            fail_if(info.file_size!=row['bytes'],'length mismatch: '+relative)
            digest=hashlib.sha256()
            with archive.open(info) as stream:
                while chunk:=stream.read(1024*1024):digest.update(chunk)
            fail_if(digest.hexdigest()!=row['sha256'],'SHA-256 mismatch: '+relative)
        corpus=validate_adopted_bytes(manifest,lambda name:archive.read(root+'/'+name))
        return {**corpus,'result':'pass','kind':manifest['kind'],'version':manifest['version'],
                'source_tree_sha256':manifest['source_tree_sha256'],
                'manifest_sha256':hashlib.sha256(manifest_raw).hexdigest(),
                'files':len(expected),'root':root,'byte_size':path.stat().st_size,
                'sha256':digest_of_file(path)}

def verify_directory(directory: Path):
    fail_if(not directory.is_dir() or directory.is_symlink(),'not a plain bundle directory')
    manifest_path=directory/MANIFEST
    fail_if(not manifest_path.is_file() or manifest_path.is_symlink(),'bundle manifest missing')
    fail_if(manifest_path.stat().st_size>MAX_MANIFEST_BYTES,'bundle manifest too large')
    manifest_raw=manifest_path.read_bytes()
    manifest=parse_json(manifest_raw)
    root,expected=validate_manifest(manifest)
    fail_if(directory.name!=root,'bundle directory has wrong name')
    found={}
    for entry in directory.rglob('*'):
        fail_if(entry.is_symlink(),'symlink forbidden in bundle directory')
        if not entry.is_file():
            fail_if(not entry.is_dir(),'special entry forbidden')
            continue
        found[entry.relative_to(directory).as_posix()]=entry
        fail_if(len(found)>MAX_FILES+1,'too many bundle files')
    check_path_set(found)
    fail_if(set(found)!=set(expected)|{MANIFEST},'unlisted or missing bundle files')
    fail_if(sum(entry.stat().st_size for entry in found.values())>MAX_BYTES,'bundle over size budget')
    for relative,row in expected.items():
        entry=found[relative]
        fail_if(entry.stat().st_size!=row['bytes'],'length mismatch: '+relative)
        fail_if(digest_of_file(entry)!=row['sha256'],'SHA-256 mismatch: '+relative)
    corpus=validate_adopted_bytes(manifest,lambda name:found[name].read_bytes())
    return {**corpus,'result':'pass','kind':manifest['kind'],'version':manifest['version'],
            'source_tree_sha256':manifest['source_tree_sha256'],
            'manifest_sha256':hashlib.sha256(manifest_raw).hexdigest(),
            'files':len(expected),'root':root}

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    script=Path(__file__).resolve()
    default_root=script.parent if (script.parent/MANIFEST).is_file() else script.parent.parent
    parser.add_argument('bundle',nargs='?',type=Path,default=default_root)
    args=parser.parse_args(argv)
    try:
        result=verify_zip(args.bundle) if args.bundle.is_file() else verify_directory(args.bundle)
    except (VerificationError,OSError,zipfile.BadZipFile,ValueError,KeyError,TypeError) as exc:
        print(json.dumps({'result':'fail','error':str(exc)},ensure_ascii=False),file=sys.stderr)
        return 1
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
    return 0

if __name__=='__main__':raise SystemExit(main())
