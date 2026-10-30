"""Build deterministic offline source and Agent Skill release artifacts."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import zipfile

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parent
sys.path.insert(0,str(PROJECT))
from tools.verify_release_bundle import (
    SCHEMA,MAX_BYTES,MAX_FILES,canonical,checked_path,check_path_set,
    parse_json,validate_registry_bytes,verify_zip,validate_project_release,validate_release_config,
)

ZIP_DATE=(2026,10,27,0,0,0)
def root_name(kind,version):
    return 'Standards-v'+version if kind=='source' else 'ranzevor-standards'

def archive_names(version):
    return ('Standards-v'+version+'-source.zip','Standards-v'+version+'-agent-skill.zip')
IGNORE={'.git','.venv','__pycache__','.pytest_cache'}

def sha256(value: bytes):
    return hashlib.sha256(value).hexdigest()

def read_source(root: Path):
    root=Path(root)
    if not root.is_dir() or root.is_symlink():
        raise ValueError('source is not a regular directory')
    result={};total=0
    for item in sorted(root.rglob('*')):
        if any(part in IGNORE for part in item.relative_to(root).parts):continue
        rel=item.relative_to(root).as_posix();checked_path(rel)
        if item.is_symlink() or not (item.is_file() or item.is_dir()):
            raise ValueError('source contains symlink or special entry: '+rel)
        if item.is_dir():continue
        total+=item.stat().st_size
        if len(result)>=MAX_FILES or total>MAX_BYTES:
            raise ValueError('unexpected source file or size count')
        result[rel]=item.read_bytes()
    check_path_set(result)
    return result

def verify_normative(source):
    summary,paths=validate_registry_bytes(parse_json(source['registry/standards.json']),source.__getitem__)
    actual={path for path in source if path.startswith('standards/') and path.endswith('.md')
            and Path(path).name!='README.md'}
    if actual!=paths:
        raise ValueError('registered and packaged normative file sets differ')
    version=validate_project_release(parse_json(source['project.json']))
    config=validate_release_config(parse_json(source['releases/current.json']),version)
    if not source[config['notes_path']].strip():raise ValueError('release notes are empty')
    return {**summary,'version':version}

def manifest(kind,records,source_summary):
    prefix='source/' if kind=='source' else 'references/'
    return canonical({
        'schema':SCHEMA,'kind':kind,'root':root_name(kind,source_summary['version']),'version':source_summary['version'],
        'normative_language':'zh-Hans','document_count':source_summary['documents'],
        'adopted_document_count':source_summary['adopted'],
        'current_snapshot_sha256':source_summary['current_snapshot_sha256'],
        'source_tree_sha256':source_summary['source_tree_sha256'],
        'rights_notice':prefix+'LICENSE-NOTICE.md','license_policy':prefix+'LICENSE',
        'license_grant':'multi-license: CC-BY-4.0 and Apache-2.0',
        'public_distribution_authorized':True,
        'description':'Offline engineering standards, clause lookup and file integrity manifest.',
        'files':[{'path':path,'bytes':len(raw),'sha256':sha256(raw)}
                 for path,raw in sorted(records.items())],
    })

def build_report(corpus,source_tree_sha256,archives,source_identity=None):
    report={'status':'built-and-file-verified','version':corpus['version'],
            'documents':corpus['documents'],'adopted_documents':corpus['adopted'],
            'current_snapshot_sha256':corpus['current_snapshot_sha256'],
            'source_tree_sha256':source_tree_sha256,'archives':archives,
            'public_distribution_authorized':True,
            'license_grant':'multi-license: CC-BY-4.0 and Apache-2.0'}
    if source_identity is not None:report.update(source_identity)
    return report

def archive_zip(destination: Path,kind: str,contents: dict[str,bytes],source_summary):
    root=root_name(kind,source_summary['version']);items=dict(contents)
    items['BUNDLE-MANIFEST.json']=manifest(kind,contents,source_summary)
    with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,
                         allowZip64=True,strict_timestamps=True) as output:
        for relative,content in sorted(items.items()):
            info=zipfile.ZipInfo(root+'/'+relative,ZIP_DATE)
            info.create_system=3;info.external_attr=(stat.S_IFREG|0o644)<<16
            info.compress_type=zipfile.ZIP_DEFLATED;info.flag_bits=0x800
            output.writestr(info,content,compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)
    return verify_zip(destination)

def clean_git_identity(root: Path, expected_commit: str, source=None):
    from tools.verify_release_bundle import fail_if
    import re
    root=Path(root).resolve()
    fail_if(re.fullmatch('[0-9a-f]{40}', expected_commit or '') is None, 'invalid source commit')
    environment=dict(os.environ)
    for name in ('GIT_DIR','GIT_WORK_TREE','GIT_COMMON_DIR','GIT_INDEX_FILE',
                 'GIT_OBJECT_DIRECTORY','GIT_ALTERNATE_OBJECT_DIRECTORIES','GIT_PREFIX'):
        environment.pop(name,None)
    environment.update(GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',GIT_NO_REPLACE_OBJECTS='1')
    def git(*args,raw=False):
        result=subprocess.run(['git','-C',str(root),'-c','core.fsmonitor=false',
                               '-c','core.untrackedCache=false',*args],env=environment,
                              capture_output=True,check=True,timeout=30)
        return result.stdout if raw else result.stdout.decode('utf-8').strip()
    fail_if(Path(git('rev-parse','--show-toplevel')).resolve()!=root, 'wrong source Git root')
    fail_if(git('rev-parse','--show-object-format')!='sha1', 'unsupported release Git object format')
    fail_if(git('rev-parse','HEAD')!=expected_commit, 'source commit differs from the release event')
    fail_if(bool(git('status','--porcelain','--untracked-files=all')), 'release source is not a clean commit')
    tracked={}
    for entry in git('ls-tree','-rz',expected_commit,raw=True).split(b'\0'):
        if not entry:continue
        metadata,path=entry.split(b'\t',1)
        mode,kind,digest=metadata.decode('ascii').split()
        relative=path.decode('utf-8');checked_path(relative)
        fail_if(kind!='blob' or mode not in ('100644','100755'), 'unsupported tracked source entry')
        tracked[relative]=digest
    source=read_source(root) if source is None else source
    fail_if(set(source)!=set(tracked), 'packaged source file set differs from the release commit')
    for relative,raw in source.items():
        actual=hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest()
        fail_if(actual!=tracked[relative], 'packaged source bytes differ from the release commit: '+relative)
    fail_if(git('rev-parse','HEAD')!=expected_commit, 'source commit changed during verification')
    return {'source_commit':expected_commit,'source_git_tree':git('rev-parse',expected_commit+'^{tree}')}


def build(root: Path,output: Path,source_commit=None):
    if Path(root).is_symlink() or Path(output).is_symlink():
        raise ValueError('release source and destination must not be symlinks')
    root=Path(root).resolve();output=Path(output).resolve()
    if output==root or output.is_relative_to(root) or root.is_relative_to(output):
        raise ValueError('release destination must be isolated from project source')
    source=read_source(root)
    identity=clean_git_identity(root,source_commit,source) if source_commit else None
    corpus=verify_normative(source)
    source_archive,skill_archive=archive_names(corpus['version'])
    required={'tools/verify_release_bundle.py','tools/skill_lookup.py','skills/ranzevor-standards/SKILL.md.in'}
    if not required<=source.keys():raise ValueError('release/skill tooling not present in source')
    tree_summary=sha256(canonical(sorted((key,len(value),sha256(value)) for key,value in source.items())))
    common={**corpus,'source_tree_sha256':tree_summary}
    source_contents={'source/'+key:raw for key,raw in source.items()}
    source_contents['verify.py']=source['tools/verify_release_bundle.py']
    skill_contents={'references/'+key:raw for key,raw in source.items()}
    skill_contents['SKILL.md']=source['skills/ranzevor-standards/SKILL.md.in']
    skill_contents['scripts/verify_bundle.py']=source['tools/verify_release_bundle.py']
    skill_contents['scripts/lookup.py']=source['tools/skill_lookup.py']
    output.mkdir(parents=True,exist_ok=True)
    reports={}
    with tempfile.TemporaryDirectory(prefix='.standards-build-',dir=output.parent) as staging:
        stage=Path(staging)
        for kind,name,contents in [('source',source_archive,source_contents),
                                   ('agent-skill',skill_archive,skill_contents)]:
            reports[name]=archive_zip(stage/name,kind,contents,common)
        if identity is not None and clean_git_identity(root,source_commit)!=identity:
            raise ValueError('release source changed during build')
        report=build_report(corpus,tree_summary,reports,identity)
        (stage/'BUILD-REPORT.json').write_bytes(canonical(report))
        summed=(source_archive,skill_archive,'BUILD-REPORT.json')
        (stage/'SHA256SUMS.txt').write_text(''.join(
            f"{sha256((stage/name).read_bytes())}  {name}\n" for name in summed),encoding='utf-8',newline='\n')
        for name in (source_archive,skill_archive,'SHA256SUMS.txt','BUILD-REPORT.json'):
            (stage/name).replace(output/name)
    return report

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=PROJECT)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--source-commit',help='Require a clean Git checkout of this exact commit')
    args=parser.parse_args(argv)
    try:report=build(args.root,args.output,args.source_commit)
    except (ValueError,OSError,KeyError,TypeError,zipfile.BadZipFile,subprocess.SubprocessError) as exc:
        print('release build failed: '+str(exc),file=sys.stderr);return 1
    print(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2));return 0

if __name__=='__main__':raise SystemExit(main())
