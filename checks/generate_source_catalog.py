"""Deterministic index of local source objects and normative citations."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
from urllib.parse import unquote,urlsplit

if sys.flags.optimize:
    raise RuntimeError('Validation requires assertions enabled; optimized validation (-O/-OO) is unsupported')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from checks.corpus_contract import references
from checks.validate_product import validate_license_policy
from checks.validation_common import read_json,read_text_exact,require,safe_path

OUTPUT='registry/source-catalog.json'
IGNORED={'__pycache__','.pytest_cache','.venv','.git'}
SOURCE_LICENSE='CC-BY-4.0-project-authored-metadata; third-party-material-excluded'
SOURCE_RIGHTS=('project-authored source metadata/limited paraphrase is CC-BY-4.0; underlying third-party '
               'works, trademarks and quoted material remain excluded and subject to their own terms')

def sha(raw):return hashlib.sha256(raw).hexdigest()

def kind(path):
    if path.suffix == '.json': return 'source-claims-and-interfaces'
    return 'source-reference-document'

def build(root):
    root=Path(root).resolve();source_root=root/'sources'
    validate_license_policy(root)
    require(source_root.is_dir()and not source_root.is_symlink(),'regular source directory required')
    objects=[]
    for path in sorted(source_root.rglob('*'),key=lambda p:p.relative_to(root).as_posix()):
        relative=path.relative_to(root)
        if any(x in IGNORED for x in relative.parts):continue
        require(not path.is_symlink(),'source catalog symlink not permitted')
        if not path.is_file():continue
        safe_path(root,relative.as_posix());raw=path.read_bytes()
        if path.suffix=='.json':read_json(path)
        objects.append({'path':relative.as_posix(),'sha256':sha(raw),'bytes':len(raw),'kind':kind(relative),
            'license_status':SOURCE_LICENSE,
            'public_redistribution_authorized':True,
            'rights_scope':SOURCE_RIGHTS})
    docs=[]
    for entry in read_json(safe_path(root,'registry/standards.json')):
        path=safe_path(root,entry['path']);raw=path.read_bytes();require(sha(raw)==entry['sha256'],'source interface document digest drift')
        links=[]
        for reference in references(raw.decode(),visible_only=True):
            target=reference['url'];uri=urlsplit(target)
            if uri.scheme in {'https','http'}:
                links.append({'label':reference['label'],'url':target,'relationship':'external-citation'})
            elif not uri.scheme and not uri.netloc and uri.path:
                candidate=(path.parent/unquote(uri.path)).resolve()
                require(candidate.is_relative_to(root),'source interface path escapes repository')
                if candidate.is_relative_to(source_root):
                    source=safe_path(root,candidate.relative_to(root).as_posix())
                    links.append({'label':reference['label'],'path':source.relative_to(root).as_posix(),'sha256':sha(source.read_bytes()),'relationship':'local-source-interface'})
        docs.append({'document_id':entry['id'],'path':entry['path'],'sha256':entry['sha256'],
            'source_interfaces':links})
    return {'schema_version':'1.0','scope':'current source documents and their normative citation interfaces',
        'generator_scope':{'ignored_local_cache_parts':sorted(IGNORED),'syntax':'visible Markdown citations; fenced code and comments excluded'},
        'source_objects':objects,'documents':docs}

def serialized(value):return json.dumps(value,ensure_ascii=False,indent=2)+'\n'

def generate(root,check=False):
    root=Path(root).resolve();expected=serialized(build(root));path=root/OUTPUT
    if check:require(path.is_file()and read_text_exact(path)==expected,'source catalog is stale; explicit regeneration and review required')
    else:path.write_text(expected,encoding='utf-8',newline='\n')
    value=json.loads(expected)
    return {'source_objects':len(value['source_objects']),'documents':len(value['documents']),'check':check,
        'scope':'local source object hashes, source licenses and visible normative citations'}

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);parser.add_argument('--check',action='store_true');args=parser.parse_args(argv)
    print(json.dumps(generate(args.root,args.check),ensure_ascii=False,sort_keys=True))

if __name__=='__main__':main()
