"""Release identity, package integrity and offline lookup regression tests."""
from pathlib import Path
import copy
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from tests.platform_support import make_symlink
from unittest.mock import patch
import zipfile

from tools.build_release_bundle import (
    archive_zip,build,build_report,canonical,manifest,read_source,sha256,verify_normative,
)
from tools.skill_lookup import find
from tools.verify_release_bundle import (
    MANIFEST,VerificationError,checked_path,parse_json,validate_manifest,
    validate_adopted_bytes,verify_directory,verify_zip,
)
ROOT=Path(__file__).resolve().parents[1]

def fixture_source(version="0.1.0"):
    source={}
    documents=[]
    for number in range(1,163):
        path=f'standards/L0/{number:03d}-测试规范--v0.1.0.md'
        raw=(f'# 测试规范 {number}\n\n**文档ID：** STD-L0-{number:03d}　'
             '**版本：** 0.1.0　**状态：** adopted　**生效日期：** 2026-10-27\n\n'
             f'## ARC-{number:03d} 条款\n完整要求。\n').encode()
        source[path]=raw
        documents.append({'id':f'STD-L0-{number:03d}','title':f'测试规范 {number}',
                          'path':path,'domain':'core','version':'0.1.0','status':'adopted',
                          'language':'zh-Hans','effective_date':'2026-10-27','sha256':sha256(raw)})
    source['project.json']=canonical({'name':'Standards','version':version})
    config={'schema':'standards-release/1','version':version,
            'previous_version':None if version=='0.1.0' else
                               '0.1.'+str(int(version.rsplit('.',1)[1])-1),
            'notes_path':'releases/v'+version+'.md'}
    source['releases/current.json']=canonical(config)
    source[config['notes_path']]=b'# Synthetic release notes\n'
    source['registry/standards.json']=canonical(documents)
    first=documents[0];lines=source[first['path']].splitlines(keepends=True)
    source['registry/requirements.json']=canonical([{
        'document_id':first['id'],'clause_id':'ARC-001','path':first['path'],
        'version':'0.1.0','document_sha256':first['sha256'],'line':5,'end_line':6,
        'section_sha256':sha256(b''.join(lines[4:6]))}])
    for name in ('LICENSE','LICENSE-NOTICE.md','NOTICE.md','LICENSES/Apache-2.0.txt',
                 'LICENSES/CC-BY-4.0.txt','tools/verify_release_bundle.py',
                 'tools/skill_lookup.py','skills/ranzevor-standards/SKILL.md.in'):
        source[name]=(ROOT/name).read_bytes()
    import re
    template=source['skills/ranzevor-standards/SKILL.md.in'].decode('utf-8')
    template=re.sub(r'^  version: "[^"]+"$', '  version: "'+version+'"',template,flags=re.M)
    source['skills/ranzevor-standards/SKILL.md.in']=template.encode('utf-8')
    return source

def bundle_parts(source,kind='source'):
    summary=verify_normative(source)
    summary['source_tree_sha256']=sha256(canonical(sorted(
        (key,len(value),sha256(value)) for key,value in source.items())))
    prefix='source/' if kind=='source' else 'references/'
    records={prefix+key:value for key,value in source.items()}
    if kind=='source':records['verify.py']=source['tools/verify_release_bundle.py']
    else:
        records.update({'SKILL.md':source['skills/ranzevor-standards/SKILL.md.in'],
                        'scripts/verify_bundle.py':source['tools/verify_release_bundle.py'],
                        'scripts/lookup.py':source['tools/skill_lookup.py']})
    return records,summary,json.loads(manifest(kind,records,summary))

def write_directory(base,records,metadata):
    directory=Path(base)/metadata['root'];directory.mkdir()
    for name,raw in records.items():
        target=directory/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    (directory/MANIFEST).write_bytes(canonical(metadata))
    return directory

class ReleasePackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src=fixture_source()
        cls.records,cls.summary,cls.man=bundle_parts(cls.src)

    def test_full_adopted_identity_and_build_report(self):
        corpus=verify_normative(self.src)
        self.assertEqual((corpus['documents'],corpus['adopted']),(162,162))
        report=build_report(corpus,'a'*64,{})
        self.assertEqual(set(report),{'status','version','documents','adopted_documents',
                         'current_snapshot_sha256','source_tree_sha256','archives',
                         'public_distribution_authorized','license_grant'})
        self.assertEqual(report['status'],'built-and-file-verified')
        self.assertTrue(report['public_distribution_authorized'])

    def test_normative_body_change_and_missing_file_rejected(self):
        path=next(p for p in self.src if p.startswith('standards/'))
        for missing in (False,True):
            data=dict(self.src)
            if missing:del data[path]
            else:data[path]+=b'\n'
            with self.subTest(missing=missing),self.assertRaises(ValueError):
                verify_normative(data)

    def test_wrong_adopted_metadata_and_duplicate_identity_rejected(self):
        for field,value in [('status','draft'),('version','0.1'),('language','en'),
                            ('effective_date',None),('id','old-id'),('path','../escape.md')]:
            data=dict(self.src);rows=json.loads(data['registry/standards.json'])
            rows[0][field]=value;data['registry/standards.json']=canonical(rows)
            with self.subTest(field=field),self.assertRaises(ValueError):verify_normative(data)
        for mutation in ('duplicate','unknown-field','missing-row'):
            rows=json.loads(self.src['registry/standards.json'])
            if mutation=='duplicate':rows[1]['id']=rows[0]['id']
            elif mutation=='unknown-field':rows[0]['unexpected']=True
            else:rows.pop()
            data={**self.src,'registry/standards.json':canonical(rows)}
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):verify_normative(data)

    def test_unregistered_normative_file_rejected(self):
        data={**self.src,'standards/L0/999-extra--v0.1.0.md':b'extra'}
        with self.assertRaisesRegex(ValueError,'file sets differ'):verify_normative(data)

    def test_direct_verifier_binds_collection_and_document_bytes(self):
        for field,value in [('current_snapshot_sha256','0'*64)]:
            with self.assertRaisesRegex(VerificationError,'collection SHA'):
                validate_adopted_bytes({**self.man,field:value},self.records.__getitem__)
        records=dict(self.records)
        key=next(x for x in records if x.startswith('source/standards/'))
        records[key]+=b'changed'
        with self.assertRaisesRegex(VerificationError,'normative digest'):
            validate_adopted_bytes(self.man,records.__getitem__)

    def test_path_traversal_and_noncanonical_names_rejected(self):
        for path in ('.','../evil.md','/tmp/evil','a/../b','a//b','a\\b','a/./b','C:/escape','a/b:stream'):
            with self.subTest(path=path),self.assertRaises(VerificationError):checked_path(path)
        self.assertEqual(checked_path('standards/L0/001-规范--v0.1.0.md').parts[0],'standards')

    def test_manifest_casefold_and_file_directory_collisions(self):
        for pair in [('Foo','foo'),('Foo','foo/bar.txt')]:
            data=copy.deepcopy(self.man)
            data['files'] += [{'path':x,'bytes':3,'sha256':'a'*64} for x in pair]
            with self.subTest(pair=pair),self.assertRaisesRegex(VerificationError,'collision'):
                validate_manifest(data)

    def test_manifest_rejects_unknown_fields_identity_and_distribution_changes(self):
        for key,value in [('unexpected',1),('document_count',True),('adopted_document_count',161),
                          ('version','0.2.0'),('source_tree_sha256','0'*64),
                          ('license_grant','not-selected'),('public_distribution_authorized',False)]:
            with self.subTest(key=key),self.assertRaises(VerificationError):
                validate_manifest({**self.man,key:value})

    def test_manifest_rejects_missing_required_files_and_unknown_entries(self):
        data=copy.deepcopy(self.man)
        data['files']=[x for x in data['files'] if x['path']!='source/LICENSE']
        with self.assertRaisesRegex(VerificationError,'required files'):validate_manifest(data)
        data=copy.deepcopy(self.man)
        data['files'].append({'path':'outside/data','bytes':0,'sha256':sha256(b'')})
        with self.assertRaisesRegex(VerificationError,'unknown bundle entry'):validate_manifest(data)

    def test_initial_and_later_packages_require_the_release_configuration(self):
        for version in ('0.1.0','0.1.1'):
            for kind in ('source','agent-skill'):
                with self.subTest(version=version,kind=kind):
                    records,summary,metadata=bundle_parts(fixture_source(version),kind)
                    prefix='source/' if kind=='source' else 'references/'
                    metadata['files']=[row for row in metadata['files']
                                       if row['path']!=prefix+'releases/current.json']
                    with self.assertRaisesRegex(VerificationError,'required files'):
                        validate_manifest(metadata)

    def test_initial_release_notes_and_configuration_are_verified(self):
        for mutation in ('missing-config','wrong-version','wrong-notes-path',
                         'unexpected-predecessor','missing-notes','empty-notes'):
            with self.subTest(mutation=mutation):
                source=dict(self.src)
                config=parse_json(source['releases/current.json'])
                if mutation=='missing-config':
                    del source['releases/current.json']
                elif mutation in ('missing-notes','empty-notes'):
                    if mutation=='missing-notes':del source[config['notes_path']]
                    else:source[config['notes_path']]=b' \n\t'
                else:
                    field,value={'wrong-version':('version','0.1.1'),
                                 'wrong-notes-path':('notes_path','../outside.md'),
                                 'unexpected-predecessor':('previous_version','0.1.0')}[mutation]
                    source['releases/current.json']=canonical({**config,field:value})
                with self.assertRaises((VerificationError,KeyError,ValueError)):
                    verify_normative(source)
                records={**self.records,**{'source/'+path:raw for path,raw in source.items()}}
                for missing in set(self.src)-set(source):del records['source/'+missing]
                with self.assertRaises((VerificationError,KeyError,ValueError)):
                    validate_adopted_bytes(self.man,records.__getitem__)

    def test_byte_count_types_and_size_budgets(self):
        for value in (True,-1,600_000_001):
            data=copy.deepcopy(self.man);data['files'][0]['bytes']=value
            with self.subTest(value=value),self.assertRaisesRegex(VerificationError,'file identity'):
                validate_manifest(data)
        total=sum(row['bytes'] for row in self.man['files'])
        with patch('tools.verify_release_bundle.MAX_BYTES',total):
            validate_manifest(self.man)
        with patch('tools.verify_release_bundle.MAX_BYTES',total-1):
            with self.assertRaisesRegex(VerificationError,'size budget'):validate_manifest(self.man)

    def test_archive_budgets_reject_before_payload_read(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'source.zip';archive_zip(path,'source',self.records,self.summary)
            for setting,value,message in [('MAX_BYTES',1,'inflated size'),
                                          ('MAX_FILES',1,'entry count'),
                                          ('MAX_MANIFEST_BYTES',1,'manifest too large')]:
                with self.subTest(setting=setting),patch('tools.verify_release_bundle.'+setting,value):
                    with self.assertRaisesRegex(VerificationError,message):verify_zip(path)

    def test_duplicate_json_nonfinite_invalid_json_rejected(self):
        for raw in (b'{"a":1,"a":2}',b'{"x":NaN}',b'not-json',b'\xff'):
            with self.subTest(raw=raw),self.assertRaises(VerificationError):parse_json(raw)

    def test_zip_and_unpacked_valid_neighbors(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'source.zip'
            report=archive_zip(path,'source',self.records,self.summary)
            self.assertEqual(report['adopted'],162)
            directory=write_directory(temp,self.records,self.man)
            unpacked=verify_directory(directory)
            for result in (report,unpacked):
                self.assertEqual(result['result'],'pass')
                self.assertEqual(result['source_tree_sha256'],self.summary['source_tree_sha256'])
                self.assertEqual(result['manifest_sha256'],sha256(canonical(self.man)))

    def test_manifest_identity_binds_verified_original_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            directory=write_directory(temp,self.records,self.man)
            raw=json.dumps(self.man,ensure_ascii=False,separators=(',',':')).encode('utf-8')
            self.assertNotEqual(raw,canonical(self.man))
            (directory/MANIFEST).write_bytes(raw)
            unpacked=verify_directory(directory)
            path=Path(temp)/'source.zip'
            with zipfile.ZipFile(path,'w') as archive:
                for name,content in {**self.records,MANIFEST:raw}.items():
                    archive.writestr(self.man['root']+'/'+name,content)
            zipped=verify_zip(path)
            for result in (unpacked,zipped):
                self.assertEqual(result['source_tree_sha256'],self.summary['source_tree_sha256'])
                self.assertEqual(result['manifest_sha256'],sha256(raw))

    def test_zip_determinism(self):
        with tempfile.TemporaryDirectory() as temp:
            a=Path(temp)/'a.zip';b=Path(temp)/'b.zip'
            archive_zip(a,'source',self.records,self.summary)
            archive_zip(b,'source',self.records,self.summary)
            self.assertEqual(a.read_bytes(),b.read_bytes())

    def test_rehashed_wrapper_replacement_is_not_source_identity(self):
        for version in ('0.1.0','0.1.1'):
            for kind,wrappers in [('source',['verify.py']),('agent-skill',
                                  ['SKILL.md','scripts/verify_bundle.py','scripts/lookup.py'])]:
                original,summary,metadata=bundle_parts(fixture_source(version),kind)
                validate_adopted_bytes(metadata,original.__getitem__)
                for wrapper in wrappers:
                    with self.subTest(version=version,kind=kind,wrapper=wrapper),tempfile.TemporaryDirectory() as temp:
                        changed=dict(original)
                        changed[wrapper]+=b'\n# unreviewed wrapper change\n'
                        rebound=json.loads(manifest(kind,changed,summary))
                        validate_manifest(rebound)
                        directory=write_directory(temp,changed,rebound)
                        archive=Path(temp)/'changed.zip'
                        with zipfile.ZipFile(archive,'w') as output:
                            for name,raw in {**changed,MANIFEST:canonical(rebound)}.items():
                                output.writestr(rebound['root']+'/'+name,raw)
                        for verify,target in [(verify_directory,directory),(verify_zip,archive)]:
                            with self.assertRaisesRegex(VerificationError,'wrapper differs from packaged source'):
                                verify(target)

    def test_plain_python_lookup_preserves_unpacked_bundle(self):
        for kind in ('source','agent-skill'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as temp:
                records,summary,metadata=bundle_parts(self.src,kind)
                directory=write_directory(temp,records,metadata)
                script='source/tools/skill_lookup.py' if kind=='source' else 'scripts/lookup.py'
                environment=dict(os.environ,PATH='')
                for key in ('PYTHONDONTWRITEBYTECODE','PYTHONPYCACHEPREFIX'):
                    environment.pop(key,None)
                result=subprocess.run([sys.executable,script,'--document-id','STD-L0-001',
                                       '--clause-id','ARC-001'],cwd=directory,env=environment,
                                      capture_output=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stderr.decode())
                self.assertEqual(json.loads(result.stdout)['total'],1)
                self.assertEqual(verify_directory(directory)['result'],'pass')
                self.assertFalse(list(directory.rglob('__pycache__')))

    def test_unpacked_extra_file_and_modified_bytes_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            directory=write_directory(temp,self.records,self.man)
            (directory/'extra').write_text('surprise')
            with self.assertRaisesRegex(VerificationError,'unlisted'):verify_directory(directory)
            (directory/'extra').unlink()
            key=next(x for x in self.records if x.startswith('source/standards/'))
            target=directory/key;target.write_bytes(target.read_bytes()+b'changed')
            with self.assertRaisesRegex(VerificationError,'length mismatch'):verify_directory(directory)
            raw=self.records[key];target.write_bytes(b'!'+raw[1:])
            with self.assertRaisesRegex(VerificationError,'SHA-256 mismatch'):verify_directory(directory)

    def test_archive_missing_and_unlisted_files_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            good=Path(temp)/'source.zip';archive_zip(good,'source',self.records,self.summary)
            with zipfile.ZipFile(good) as original:
                contents=[(info,original.read(info)) for info in original.infolist()]
            for mutation in ('missing','extra','same-size-change'):
                changed=Path(temp)/(mutation+'.zip')
                with zipfile.ZipFile(changed,'w') as archive:
                    for info,raw in contents:
                        if info.filename.endswith('/verify.py'):
                            if mutation=='missing':continue
                            if mutation=='same-size-change':raw=b'!'+raw[1:]
                        archive.writestr(info,raw)
                    if mutation=='extra':archive.writestr('Standards-v0.1.0/unlisted.txt','extra')
                with self.subTest(mutation=mutation),self.assertRaises(VerificationError):verify_zip(changed)

    def test_archive_symlink_special_entry_and_ancestor_collision_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            for name,mode in [('symlink',stat.S_IFLNK),('fifo',stat.S_IFIFO)]:
                path=Path(temp)/(name+'.zip')
                with zipfile.ZipFile(path,'w') as out:
                    item=zipfile.ZipInfo('Standards-v0.1.0/verify.py')
                    item.create_system=3;item.external_attr=(mode|0o777)<<16
                    out.writestr(item,'target')
                with self.subTest(name=name),self.assertRaises(VerificationError):verify_zip(path)
            path=Path(temp)/'ancestor.zip'
            with zipfile.ZipFile(path,'w') as out:
                out.writestr('Standards-v0.1.0/Foo','x')
                out.writestr('Standards-v0.1.0/foo/bar','x')
            with self.assertRaisesRegex(VerificationError,'file/directory'):verify_zip(path)

    def test_source_reader_rejects_symlink_and_casefold_aliases(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'plain').write_text('content')
            make_symlink(root/'link', root/'plain')
            with self.assertRaisesRegex(ValueError,'symlink'):read_source(root)
            (root/'link').unlink();(root/'PLAIN').write_text('other')
            with self.assertRaisesRegex(ValueError,'collision'):read_source(root)

    def test_lookup_adopted_and_clause_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for name,raw in self.src.items():
                target=root/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
            result=find(root,document_id='STD-L0-001')
            self.assertEqual(result['total'],1);self.assertEqual(result['results'][0]['status'],'adopted')
            clause=find(root,clause_id='ARC-001')
            self.assertEqual((clause['results'][0]['line'],clause['results'][0]['end_line']),(5,6))
            rows=json.loads((root/'registry/requirements.json').read_text())
            rows[0]['section_sha256']='0'*64
            (root/'registry/requirements.json').write_bytes(canonical(rows))
            with self.assertRaisesRegex(ValueError,'clause content digest'):find(root,clause_id='ARC-001')

    def test_lookup_rejects_symlinks_and_invalid_limits(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for name,raw in self.src.items():
                target=root/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
            for limit in (0,101,True):
                with self.subTest(limit=limit),self.assertRaises(ValueError):find(root,limit=limit)
            path=root/next(x for x in self.src if x.startswith('standards/'))
            raw=path.read_bytes();path.unlink()
            replacement=root/'replacement';replacement.write_bytes(raw);make_symlink(path, replacement)
            with self.assertRaisesRegex(ValueError,'symlink'):find(root)

    def test_source_and_skill_build_end_to_end(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'repo';root.mkdir()
            for name,raw in self.src.items():
                target=root/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
            output=Path(temp)/'release';report=build(root,output)
            self.assertEqual(report['adopted_documents'],162)
            for path in output.glob('*.zip'):self.assertEqual(verify_zip(path)['result'],'pass')

class RepositoryReleaseTests(unittest.TestCase):
    def test_repository_normative_collection(self):
        corpus=verify_normative(read_source(ROOT))
        self.assertEqual((corpus['documents'],corpus['adopted']),(162,162))

    def test_skill_frontmatter_uses_material_license_policy(self):
        raw=(ROOT/'skills/ranzevor-standards/SKILL.md.in').read_text(encoding='utf-8')
        self.assertTrue(raw.startswith('---\n'));self.assertIn('name: ranzevor-standards\n',raw)
        version=json.loads((ROOT/'project.json').read_text(encoding='utf-8'))['version']
        self.assertIn('version: "'+version+'"',raw);self.assertIn('162 adopted',raw)
        self.assertNotIn('all at version',raw)
        self.assertIn('multi-licensed by material type',raw)
        self.assertNotIn('license: MIT',raw)

if __name__=='__main__':unittest.main()
