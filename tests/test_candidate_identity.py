"""Actual Git candidate snapshots, isolation, and drift detection."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from tests.platform_support import make_symlink
from unittest import mock

from checks.candidate_identity import capture_source_identity, verify_source_unchanged


class GitCandidateIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='candidate-identity-test-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / 'repo with spaces'
        self.root.mkdir()
        self.config = mock.patch.dict(os.environ, {
            'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_SYSTEM': os.devnull,
            'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_TERMINAL_PROMPT': '0'})
        self.config.start()
        self.addCleanup(self.config.stop)
        self.git('init', '-b', 'main')
        self.git('config', 'user.name', 'Synthetic Test')
        self.git('config', 'user.email', 'synthetic@example.invalid')
        self.write('.gitignore', 'ignored-*\n__pycache__/\n')
        self.write('tracked.txt', 'base\n')
        self.git('add', '-A')
        self.git('commit', '-m', 'Create synthetic baseline')

    def git(self, *arguments):
        result = subprocess.run(['git', '-C', str(self.root), *arguments],
                                capture_output=True, check=True)
        return result.stdout.decode('utf-8').strip()

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def objects(self):
        base = self.root / '.git/objects'
        return {path.relative_to(base).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in base.rglob('*') if path.is_file()}

    def test_clean_tree_matches_git_without_changing_index_head_or_objects(self):
        index = (self.root / '.git/index').read_bytes()
        head = self.git('rev-parse', 'HEAD')
        objects = self.objects()
        identity = capture_source_identity(self.root)
        self.assertEqual(identity, {'kind': 'git', 'object_format': 'sha1',
                                   'base_commit': head,
                                   'tree': self.git('rev-parse', 'HEAD^{tree}')})
        self.assertEqual((self.root / '.git/index').read_bytes(), index)
        self.assertEqual(self.git('rev-parse', 'HEAD'), head)
        self.assertEqual(self.objects(), objects)

    def test_dirty_staged_unstaged_and_untracked_are_the_current_candidate(self):
        self.write('tracked.txt', 'staged\n')
        self.git('add', 'tracked.txt')
        self.write('tracked.txt', 'current unstaged\n')
        self.write('new file.txt', 'untracked source\n')
        self.write('ignored-cache', 'discardable local cache\n')
        index = (self.root / '.git/index').read_bytes()
        head = self.git('rev-parse', 'HEAD')
        objects = self.objects()
        identity = capture_source_identity(self.root)
        self.assertEqual((self.root / '.git/index').read_bytes(), index)
        self.assertEqual(self.git('rev-parse', 'HEAD'), head)
        self.assertEqual(self.objects(), objects)
        self.git('add', '-A')
        self.assertEqual(identity['tree'], self.git('write-tree'))
        self.assertEqual(identity['base_commit'], head)
        self.assertNotEqual(identity['tree'], self.git('rev-parse', 'HEAD^{tree}'))
        self.assertNotIn('ignored-cache', self.git('ls-files').splitlines())

    def test_staged_ignored_file_is_still_included_with_current_bytes(self):
        self.write('ignored-source', 'staged ignored content\n')
        self.git('add', '-f', 'ignored-source')
        self.write('ignored-source', 'current ignored content\n')
        index = (self.root / '.git/index').read_bytes()
        identity = capture_source_identity(self.root)
        self.assertEqual((self.root / '.git/index').read_bytes(), index)
        self.git('add', '-A')
        self.assertEqual(identity['tree'], self.git('write-tree'))

    def test_staged_untrack_of_ignored_file_is_preserved(self):
        self.write('.gitignore', 'tracked.txt\n')
        self.git('rm', '--cached', 'tracked.txt')
        index = (self.root / '.git/index').read_bytes()
        head = self.git('rev-parse', 'HEAD')
        objects = self.objects()
        identity = capture_source_identity(self.root)
        self.assertEqual((self.root / '.git/index').read_bytes(), index)
        self.assertEqual(self.git('rev-parse', 'HEAD'), head)
        self.assertEqual(self.objects(), objects)
        self.assertTrue((self.root / 'tracked.txt').is_file())
        self.git('add', '-A')
        expected = self.git('write-tree')
        self.assertEqual(identity['tree'], expected)
        self.assertNotIn('tracked.txt', self.git('ls-tree', '--name-only', expected).splitlines())

    def test_unborn_repository_can_validate_before_its_first_commit(self):
        other = Path(self.temporary.name) / 'unborn'
        other.mkdir()
        subprocess.run(['git', '-C', str(other), 'init', '-b', 'main'],
                       capture_output=True, check=True)
        (other / 'first.txt').write_text('first candidate\n')
        identity = capture_source_identity(other)
        self.assertIsNone(identity['base_commit'])
        self.assertFalse((other / '.git/index').exists())
        subprocess.run(['git', '-C', str(other), 'add', '-A'], capture_output=True, check=True)
        expected = subprocess.run(['git', '-C', str(other), 'write-tree'],
                                  capture_output=True, check=True).stdout.decode().strip()
        self.assertEqual(identity['tree'], expected)

    def test_removed_staged_new_file_is_absent_from_candidate(self):
        self.write('new.txt', 'staged then deleted\n')
        self.git('add', 'new.txt')
        (self.root / 'new.txt').unlink()
        index = (self.root / '.git/index').read_bytes()
        identity = capture_source_identity(self.root)
        self.assertEqual((self.root / '.git/index').read_bytes(), index)
        self.assertEqual(identity['tree'], self.git('rev-parse', 'HEAD^{tree}'))

    def test_content_change_is_detected_even_with_restored_size_and_mtime(self):
        before = capture_source_identity(self.root)
        path = self.root / 'tracked.txt'
        stamp = path.stat()
        path.write_bytes(b'edit\n')
        os.utime(path, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
        with self.assertRaisesRegex(ValueError, 'source changed during execution'):
            verify_source_unchanged(self.root, before)

    def test_new_file_and_changed_head_are_detected(self):
        before = capture_source_identity(self.root)
        self.write('added.txt', 'new input\n')
        with self.assertRaisesRegex(ValueError, 'source changed during execution'):
            verify_source_unchanged(self.root, before)
        (self.root / 'added.txt').unlink()
        self.assertEqual(verify_source_unchanged(self.root, before), before)
        self.git('commit', '--allow-empty', '-m', 'Move synthetic baseline')
        with self.assertRaisesRegex(ValueError, 'source changed during execution'):
            verify_source_unchanged(self.root, before)

    def test_subdirectory_cannot_impersonate_repository_root(self):
        child = self.root / 'subdirectory'
        child.mkdir()
        with self.assertRaisesRegex(ValueError, 'not the Git repository root'):
            capture_source_identity(child)

    def test_ambient_index_and_repository_overrides_do_not_redirect_snapshot(self):
        foreign = Path(self.temporary.name) / 'foreign-index'
        foreign.write_bytes(b'untouched unrelated file')
        expected = capture_source_identity(self.root)
        with mock.patch.dict(os.environ, {'GIT_INDEX_FILE': str(foreign),
                                         'GIT_DIR': '/missing-repository'}):
            self.assertEqual(capture_source_identity(self.root), expected)
        self.assertEqual(foreign.read_bytes(), b'untouched unrelated file')

    def test_split_index_does_not_create_or_change_real_shared_indexes(self):
        self.git('config', 'core.splitIndex', 'true')
        self.git('update-index', '--split-index')
        self.write('tracked.txt', 'current worktree bytes\n')
        self.write('new.txt', 'new untracked input\n')
        shared = {path.name: path.read_bytes() for path in (self.root / '.git').glob('sharedindex.*')}
        self.assertTrue(shared)
        index = (self.root / '.git/index').read_bytes()
        head = self.git('rev-parse', 'HEAD')
        objects = self.objects()
        identity = capture_source_identity(self.root)
        self.assertEqual({path.name: path.read_bytes()
                          for path in (self.root / '.git').glob('sharedindex.*')}, shared)
        self.assertEqual((self.root / '.git/index').read_bytes(), index)
        self.assertEqual(self.git('rev-parse', 'HEAD'), head)
        self.assertEqual(self.objects(), objects)
        self.git('add', '-A')
        self.assertEqual(identity['tree'], self.git('write-tree'))


class ReleaseCandidateIdentityTests(unittest.TestCase):
    def make_bundle(self, kind='source'):
        from tests.test_release_bundle import fixture_source, bundle_parts, write_directory
        temporary = tempfile.TemporaryDirectory(prefix='candidate-bundle-test-')
        self.addCleanup(temporary.cleanup)
        records, _, manifest = bundle_parts(fixture_source(), kind)
        root = write_directory(temporary.name, records, manifest)
        return root, root / ('source' if kind == 'source' else 'references')

    def test_verified_source_and_skill_inputs_work_without_git(self):
        for kind in ('source', 'agent-skill'):
            with self.subTest(kind=kind):
                bundle, source = self.make_bundle(kind)
                with mock.patch.dict(os.environ, {'PATH': '', 'GIT_DIR': '/missing-repository',
                                                 'GIT_WORK_TREE': '/unrelated-source'}):
                    identity = capture_source_identity(source)
                    self.assertEqual(verify_source_unchanged(source, identity), identity)
                self.assertEqual(identity['kind'], 'release-bundle')
                self.assertEqual(identity['bundle_kind'], kind)
                self.assertEqual(identity['manifest_sha256'], hashlib.sha256(
                    (bundle / 'BUNDLE-MANIFEST.json').read_bytes()).hexdigest())

    def test_same_size_modified_input_is_rejected(self):
        _, source = self.make_bundle()
        before = capture_source_identity(source)
        path = next((source / 'standards').rglob('*.md'))
        raw = path.read_bytes()
        path.write_bytes(b'!' + raw[1:])
        with mock.patch.dict(os.environ, {'PATH': '', 'GIT_DIR': '/missing-repository'}):
            with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
                verify_source_unchanged(source, before)

    def test_extracted_sources_can_become_git_workspaces_with_uncommitted_changes(self):
        from tools.verify_release_bundle import verify_directory
        for kind in ('source', 'agent-skill'):
            with self.subTest(kind=kind):
                bundle, source = self.make_bundle(kind)
                subprocess.run(['git', '-C', str(source), 'init', '-b', 'main'],
                               capture_output=True, check=True)
                before = capture_source_identity(source)
                self.assertEqual(before['kind'], 'git')
                self.assertIsNone(before['base_commit'])
                self.assertFalse((source / '.git/index').exists())
                (source / 'development.py').write_text('print("new development input")\n')
                after = capture_source_identity(source)
                self.assertNotEqual(after['tree'], before['tree'])
                with self.assertRaisesRegex(ValueError, 'source changed during execution'):
                    verify_source_unchanged(source, before)
                with self.assertRaisesRegex(ValueError, 'unlisted or missing'):
                    verify_directory(bundle)

    def test_worktree_pointer_takes_precedence_over_surrounding_manifest(self):
        bundle, source = self.make_bundle()
        origin = bundle.parent / 'origin'
        source.rename(origin)
        commands = [('init', '-b', 'main'), ('config', 'user.name', 'Synthetic Test'),
                    ('config', 'user.email', 'synthetic@example.invalid'),
                    ('add', '-A'), ('commit', '-m', 'Synthetic source'),
                    ('worktree', 'add', '--detach', str(source), 'HEAD')]
        for command in commands:
            subprocess.run(['git', '-C', str(origin), *command], capture_output=True, check=True)
        self.assertTrue((source / '.git').is_file())
        identity = capture_source_identity(source)
        expected = subprocess.run(['git', '-C', str(source), 'rev-parse', 'HEAD^{tree}'],
                                  capture_output=True, check=True).stdout.decode().strip()
        self.assertEqual(identity['kind'], 'git')
        self.assertEqual(identity['tree'], expected)

    def test_invalid_local_git_marker_does_not_fall_back_to_bundle(self):
        from checks.candidate_identity import CandidateIdentityError
        for kind in ('file', 'directory', 'broken-symlink'):
            with self.subTest(kind=kind):
                _, source = self.make_bundle()
                marker = source / '.git'
                if kind == 'file':
                    marker.write_text('invalid git directory pointer\n')
                elif kind == 'directory':
                    marker.mkdir()
                else:
                    make_symlink(marker, source / 'absent-git-directory', target_is_directory=True)
                with mock.patch('tools.verify_release_bundle.verify_directory',
                                side_effect=AssertionError('unexpected bundle fallback')):
                    with self.assertRaises(CandidateIdentityError):
                        capture_source_identity(source)

    def test_unlisted_file_is_rejected(self):
        _, source = self.make_bundle()
        before = capture_source_identity(source)
        (source / 'extra.py').write_text('print("unexpected input")\n')
        with self.assertRaisesRegex(ValueError, 'unlisted or missing'):
            verify_source_unchanged(source, before)

    def test_manifest_change_after_capture_is_detected(self):
        bundle, source = self.make_bundle()
        before = capture_source_identity(source)
        path = bundle / 'BUNDLE-MANIFEST.json'
        path.write_bytes(path.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'source changed during execution'):
            verify_source_unchanged(source, before)


if __name__ == '__main__':
    unittest.main()
