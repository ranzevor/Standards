"""Release version separation and local handoff verification use real fixture bytes."""
from pathlib import Path
import json
import subprocess
import tempfile
import unittest
import copy
import zipfile

from tests.test_release_bundle import fixture_source, bundle_parts
from tools.build_release_bundle import build, canonical, clean_git_identity, sha256, verify_normative
from tools.verify_release_bundle import (
    VerificationError, validate_adopted_bytes, validate_release_config,
    validate_registry_bytes, verify_zip,
)
from tools.verify_release_artifacts import ArtifactError, asset_names, local_assets, verify_artifacts

CONFIG = {'schema': 'standards-release/1', 'version': '0.1.1',
          'previous_version': '0.1.0', 'notes_path': 'releases/v0.1.1.md'}
INITIAL_CONFIG = {'schema': 'standards-release/1', 'version': '0.1.0',
                  'previous_version': None, 'notes_path': 'releases/v0.1.0.md'}


class ReleaseVersionTests(unittest.TestCase):
    def test_initial_release_requires_null_previous_and_cannot_skip_a_patch(self):
        self.assertEqual(validate_release_config(INITIAL_CONFIG, '0.1.0'), INITIAL_CONFIG)
        for previous in ('0.1.0', '0.1.1', '', False, 0):
            with self.subTest(previous=previous), self.assertRaises(VerificationError):
                validate_release_config({**INITIAL_CONFIG, 'previous_version': previous})
        for config in ({**CONFIG, 'previous_version': None},
                       {**INITIAL_CONFIG, 'version': '0.1.1', 'notes_path': 'releases/v0.1.1.md'},
                       {**INITIAL_CONFIG, 'notes_path': 'releases/v0.1.1.md'}):
            with self.subTest(config=config), self.assertRaises(VerificationError):
                validate_release_config(config)
        with self.assertRaisesRegex(VerificationError, 'version mismatch'):
            validate_release_config(INITIAL_CONFIG, '0.1.1')

    def test_patch_sequence_and_note_identity(self):
        self.assertEqual(validate_release_config(CONFIG), CONFIG)
        for key, value in [('version', '0.1.3'), ('version', '0.1.01'),
                           ('previous_version', '0.1.1'), ('notes_path', '../outside.md')]:
            with self.subTest(key=key, value=value), self.assertRaises(VerificationError):
                validate_release_config({**CONFIG, key: value})

    def test_release_can_advance_while_all_normative_documents_stay_at_zero(self):
        source = fixture_source('0.1.1')
        self.assertEqual(verify_normative(source)['version'], '0.1.1')
        self.assertEqual({x['version'] for x in json.loads(source['registry/standards.json'])}, {'0.1.0'})
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'source'
            for name, raw in source.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
            output = Path(temporary) / 'artifacts'
            report = build(root, output)
            self.assertEqual(report['version'], '0.1.1')
            for archive in output.glob('*.zip'):
                self.assertEqual(verify_zip(archive)['version'], '0.1.1')

    def test_individual_normative_patch_must_match_its_filename(self):
        source = fixture_source('0.1.1')
        rows = json.loads(source['registry/standards.json'])
        old = rows[0]['path']
        rows[0]['version'] = '0.1.1'
        rows[0]['effective_date'] = '2026-10-28'
        with self.assertRaisesRegex(VerificationError, 'path/version'):
            validate_registry_bytes(rows, source.__getitem__)
        rows[0]['path'] = old.replace('--v0.1.0.md', '--v0.1.1.md')
        source[rows[0]['path']] = source.pop(old).replace(
            '**版本：** 0.1.0'.encode(), '**版本：** 0.1.1'.encode()).replace(b'2026-10-27', b'2026-10-28')
        rows[0]['sha256'] = sha256(source[rows[0]['path']])
        self.assertEqual(validate_registry_bytes(rows, source.__getitem__)[0]['documents'], 162)

    def test_invalid_normative_date_is_rejected(self):
        source = fixture_source()
        for value in ('2026-02-30', '2026-13-01', '2026-1-2', None):
            rows = json.loads(source['registry/standards.json'])
            rows[0]['effective_date'] = value
            with self.subTest(value=value), self.assertRaises(VerificationError):
                validate_registry_bytes(rows, source.__getitem__)

    def test_package_version_cannot_disagree_with_embedded_project(self):
        records, summary, metadata = bundle_parts(fixture_source())
        records['source/project.json'] = canonical({'name': 'Standards', 'version': '0.1.1'})
        with self.assertRaisesRegex(VerificationError, 'versions differ'):
            validate_adopted_bytes(metadata, records.__getitem__)

    def test_skill_version_cannot_disagree_with_distribution(self):
        records, summary, metadata = bundle_parts(fixture_source('0.1.1'), 'agent-skill')
        records['SKILL.md'] = records['SKILL.md'].replace(b'version: "0.1.1"', b'version: "0.1.0"')
        with self.assertRaisesRegex(VerificationError, 'Skill and release'):
            validate_adopted_bytes(metadata, records.__getitem__)

    def test_rehashed_transfer_cannot_replace_a_source_derived_wrapper(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)/'repo'
            for name,raw in fixture_source('0.1.1').items():
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
            def git(*args):
                return subprocess.check_output(['git','-C',str(root),'-c','user.name=Release Test',
                    '-c','user.email=release-test@example.invalid',*args]).decode().strip()
            git('init','-q');git('add','.');git('commit','-qm','Synthetic wrapper fixture')
            commit=git('rev-parse','HEAD');output=Path(temporary)/'artifacts'
            report=build(root,output,commit)
            originals={p.name:p.read_bytes() for p in output.iterdir()}
            for kind,wrappers in [('source',['verify.py']),('agent-skill',
                                  ['SKILL.md','scripts/verify_bundle.py','scripts/lookup.py'])]:
                name='Standards-v0.1.1-'+kind+'.zip'
                for wrapper in wrappers:
                    with self.subTest(kind=kind,wrapper=wrapper):
                        for file,raw in originals.items():(output/file).write_bytes(raw)
                        with zipfile.ZipFile(output/name) as archive:
                            records={i.filename:archive.read(i) for i in archive.infolist()}
                        bundle_root=report['archives'][name]['root']
                        records[bundle_root+'/'+wrapper]+=b'\n# unreviewed wrapper change\n'
                        manifest_path=bundle_root+'/BUNDLE-MANIFEST.json'
                        metadata=json.loads(records[manifest_path])
                        for row in metadata['files']:
                            if row['path']==wrapper:
                                raw=records[bundle_root+'/'+wrapper]
                                row.update(bytes=len(raw),sha256=sha256(raw))
                        records[manifest_path]=canonical(metadata)
                        with zipfile.ZipFile(output/name,'w') as archive:
                            for path,raw in records.items():archive.writestr(path,raw)
                        rebound=copy.deepcopy(report)
                        rebound['archives'][name].update(sha256=sha256((output/name).read_bytes()),
                            byte_size=(output/name).stat().st_size,
                            manifest_sha256=sha256(records[manifest_path]))
                        (output/'BUILD-REPORT.json').write_bytes(canonical(rebound))
                        (output/'SHA256SUMS.txt').write_bytes(''.join(
                            sha256((output/file).read_bytes())+'  '+file+'\n'
                            for file in (*list(report['archives']), 'BUILD-REPORT.json')).encode())
                        with self.assertRaisesRegex(VerificationError,'wrapper differs from packaged source'):
                            verify_artifacts(root,output,commit)
            for name,raw in originals.items():(output/name).write_bytes(raw)
            self.assertEqual(verify_artifacts(root,output,commit)['status'],'local-artifacts-verified')

    def test_commit_bound_build_and_transfer_verification(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'repo'
            for name, raw in fixture_source('0.1.1').items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
            def git(*args):
                return subprocess.check_output(
                    ['git', '-C', str(root), '-c', 'user.name=Release Test',
                     '-c', 'user.email=release-test@example.invalid', *args]).decode().strip()
            git('init', '-q')
            git('add', '.')
            git('commit', '-qm', 'Synthetic release fixture')
            commit = git('rev-parse', 'HEAD')
            identity = clean_git_identity(root, commit)
            output = Path(temporary) / 'artifacts'
            report = build(root, output, commit)
            self.assertEqual(report['source_commit'], commit)
            assets = local_assets(output, CONFIG['version'], identity, report['source_tree_sha256'])
            self.assertEqual(set(assets), set(asset_names('0.1.1')))
            handoff = verify_artifacts(root, output, commit)
            self.assertEqual(handoff['status'], 'local-artifacts-verified')
            self.assertEqual(handoff['source_commit'], commit)
            self.assertEqual(handoff['assets'], {name: sha256(raw) for name, raw in assets.items()})
            self.assertIn(sha256(assets['BUILD-REPORT.json']).encode() + b'  BUILD-REPORT.json\n',
                          assets['SHA256SUMS.txt'])
            (output / 'SHA256SUMS.txt').write_bytes(b'wrong checksums\n')
            with self.assertRaisesRegex(ArtifactError, 'SHA256SUMS differs'):
                verify_artifacts(root, output, commit)
            (output / 'SHA256SUMS.txt').write_bytes(assets['SHA256SUMS.txt'])
            (output / 'unexpected.txt').write_bytes(b'extra artifact')
            with self.assertRaisesRegex(ArtifactError, 'asset set differs'):
                verify_artifacts(root, output, commit)
            (output / 'unexpected.txt').unlink()
            with self.assertRaisesRegex(ArtifactError, 'commit/tree'):
                local_assets(output, CONFIG['version'], {**identity, 'source_commit': 'f' * 40},
                             report['source_tree_sha256'])
            with self.assertRaisesRegex(ArtifactError, 'checked-out source'):
                local_assets(output, CONFIG['version'], identity, '0' * 64)
            (root / 'unexpected.txt').write_text('untracked change', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'clean commit'):
                build(root, Path(temporary) / 'second-artifacts', commit)
            (root / 'unexpected.txt').unlink()
            (root / '.git/info/exclude').write_text('ignored.txt\n', encoding='utf-8')
            (root / 'ignored.txt').write_text('ignored but packaged', encoding='utf-8')
            self.assertEqual(git('status', '--porcelain'), '')
            with self.assertRaisesRegex(ValueError, 'file set differs'):
                clean_git_identity(root, commit)
            (root / 'ignored.txt').unlink()
            git('update-index', '--assume-unchanged', 'project.json')
            project = root / 'project.json'
            project.write_bytes(project.read_bytes() + b'\n')
            self.assertEqual(git('status', '--porcelain'), '')
            with self.assertRaisesRegex(ValueError, 'source bytes differ'):
                clean_git_identity(root, commit)

    def test_initial_commit_build_also_binds_report_in_checksums(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'repo'
            for name, raw in fixture_source().items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
            def git(*args):
                return subprocess.check_output(
                    ['git', '-C', str(root), '-c', 'user.name=Release Test',
                     '-c', 'user.email=release-test@example.invalid', *args]).decode().strip()
            git('init', '-q')
            git('add', '.')
            git('commit', '-qm', 'Synthetic initial release fixture')
            commit = git('rev-parse', 'HEAD')
            output = Path(temporary) / 'artifacts'
            report = build(root, output, commit)
            self.assertEqual(report['version'], '0.1.0')
            self.assertEqual(verify_artifacts(root, output, commit)['source_commit'], commit)
            checksum_file = output / 'SHA256SUMS.txt'
            checksums = checksum_file.read_bytes()
            report_digest = sha256((output / 'BUILD-REPORT.json').read_bytes()).encode()
            self.assertIn(report_digest + b'  BUILD-REPORT.json\n', checksums)
            checksum_file.write_bytes(b''.join(line for line in checksums.splitlines(keepends=True)
                                               if not line.endswith(b'  BUILD-REPORT.json\n')))
            with self.assertRaisesRegex(ArtifactError, 'SHA256SUMS differs'):
                verify_artifacts(root, output, commit)
            checksum_file.write_bytes(checksums)
            report_path = output / 'BUILD-REPORT.json'
            report_path.write_bytes(report_path.read_bytes() + b'\n')
            with self.assertRaisesRegex(ArtifactError, 'SHA256SUMS differs'):
                verify_artifacts(root, output, commit)


if __name__ == '__main__':
    unittest.main()
