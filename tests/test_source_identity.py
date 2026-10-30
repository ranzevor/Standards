from pathlib import Path
import unittest,tempfile,hashlib
from tests.platform_support import make_symlink
from checks.source_identity import verify_sources,IdentityError

class SourceIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        (self.root/'a.txt').write_text('historical version');(self.root/'b.txt').write_text('other component')
    def record(self,path='a.txt',component='main'):
        return {'component':component,'path':path,'sha256':hashlib.sha256((self.root/path).read_bytes()).hexdigest(),'role':'source'}
    def test_offline_fixed_source_requires_no_remote(self):
        self.assertEqual(verify_sources(self.root,[self.record()])[0]['component'],'main')
    def test_multiple_repositories_or_components_are_legal(self):
        self.assertEqual(len(verify_sources(self.root,[self.record(),self.record('b.txt','dependency')])),2)
    def test_mutated_bytes_rejected(self):
        r=self.record();(self.root/'a.txt').write_text('new version')
        with self.assertRaises(IdentityError):verify_sources(self.root,[r])
    def test_duplicate_component_rejected(self):
        with self.assertRaises(IdentityError):verify_sources(self.root,[self.record(),self.record('b.txt')])
    def test_missing_file_rejected(self):
        r=self.record();r['path']='absent'
        with self.assertRaises(IdentityError):verify_sources(self.root,[r])
    def test_absolute_and_parent_paths_rejected(self):
        for p in [str(self.root/'a.txt'),'../a.txt']:
            r=self.record();r['path']=p
            with self.subTest(path=p),self.assertRaises(IdentityError):verify_sources(self.root,[r])
    def test_symlink_escape_rejected(self):
        with tempfile.TemporaryDirectory() as other:
            outside=Path(other)/'outside';outside.write_text('outside')
            make_symlink(self.root/'link', outside);r=self.record();r['path']='link'
            with self.assertRaises(IdentityError):verify_sources(self.root,[r])
    def test_strict_fields_and_hash(self):
        for key,value in [('component',''),('sha256','x'),('role','remote-current'),('path',True)]:
            r=self.record();r[key]=value
            with self.subTest(key=key),self.assertRaises(IdentityError):verify_sources(self.root,[r])
        r=self.record();r['fresh']=True
        with self.assertRaises(IdentityError):verify_sources(self.root,[r])
    def test_no_implicit_empty_acceptance(self):
        for records in [[],{},None]:
            with self.subTest(records=records),self.assertRaises(IdentityError):verify_sources(self.root,records)
    def test_portable_path_rejects_drive_backslash_nul_and_trimmed_alias(self):
        for path in ('C:/a.txt','C:\\a.txt',' leading.txt','trailing.txt ','a\x00.txt'):
            r=self.record();r['path']=path
            with self.subTest(path=path),self.assertRaises(IdentityError):verify_sources(self.root,[r])
        make_symlink(self.root/'inside-link', self.root/'a.txt')
        self.assertEqual(verify_sources(self.root,[self.record('inside-link')])[0]['component'],'main')
