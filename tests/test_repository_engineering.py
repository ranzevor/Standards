"""Exercise independent expectations, legal evolution and physical path boundaries."""
import copy
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from examples.repository_engineering.contracts import (
    ContractError, expected_package, file_identity, include_targets, inventory,
    read_config, resolve_member, switch_owned_files, verify_package,
)


SOURCE = {
    'src/demo_reader/__init__.py': b'def answer(): return 42\n',
    'src/demo_reader/py.typed': b'',
    'LICENSE': b'Synthetic project license fixture.\n',
}


class IndependentPackageTests(unittest.TestCase):
    def setUp(self):
        self.expected = expected_package(SOURCE, '0.1.1')

    def verify(self, files, source_digest=None):
        return verify_package(files, inventory(files), self.expected, SOURCE,
                              source_digest or file_identity(SOURCE))

    def test_missing_type_marker_is_rejected_even_after_self_manifest_is_rehashed(self):
        files = dict(self.expected)
        del files['demo_reader/py.typed']
        with self.assertRaisesRegex(ContractError, 'package contract differs'):
            self.verify(files)

    def test_mixed_bytes_and_extra_files_are_rejected_despite_consistent_self_inventory(self):
        for name, raw in (('demo_reader/__init__.py', b'def answer(): return 0\n'),
                          ('undeclared.txt', b'extra')):
            with self.subTest(name=name):
                files = {**self.expected, name: raw}
                with self.assertRaisesRegex(ContractError, 'package contract differs'):
                    self.verify(files)

    def test_conflicting_source_manifest_identity_is_rejected_at_that_boundary(self):
        with self.assertRaisesRegex(ContractError, 'source manifest identity differs'):
            self.verify(self.expected, '0' * 64)

    def test_member_and_manifest_order_do_not_change_a_valid_package(self):
        files = dict(reversed(list(self.expected.items())))
        declared = dict(reversed(list(inventory(files).items())))
        self.assertEqual(verify_package(files, declared, self.expected, SOURCE,
                                        file_identity(SOURCE)), file_identity(self.expected))
        self.assertIn('demo_reader/py.typed', files)

    def test_legal_new_version_is_checked_against_its_own_expected_metadata(self):
        changed = expected_package(SOURCE, '0.1.2')
        self.assertNotEqual(file_identity(changed), file_identity(self.expected))
        self.assertEqual(verify_package(changed, inventory(changed), changed, SOURCE,
                                        file_identity(SOURCE)), file_identity(changed))

    def test_inventory_rejects_unsafe_paths_and_portable_collisions(self):
        for files in ({'../escape': b'x'}, {'a': b'x', 'a/b': b'y'},
                      {'Data': b'x', 'data': b'y'}):
            with self.subTest(files=files), self.assertRaises(ContractError):
                inventory(files)


class LegalChangeAndReadTests(unittest.TestCase):
    def test_independent_requirement_includes_allow_reordering_and_comments(self):
        required = {'core.txt', 'cli.txt', 'tests.txt'}
        before = '-r core.txt\n-r cli.txt\n-r tests.txt\n'
        after = '# independent groups\n-r tests.txt\n-r core.txt # core\n-r cli.txt\n'
        self.assertEqual(include_targets(before, required), include_targets(after, required))
        for invalid in (before + '-r core.txt\n', before.replace('cli.txt', 'other.txt'),
                        before.replace('-r cli.txt', '--index-url https://example.invalid')):
            with self.subTest(invalid=invalid), self.assertRaises(ContractError):
                include_targets(invalid, required)

    def test_config_validation_and_digest_use_one_read_even_if_path_changes_afterward(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'config.json'
            original = b'{"workers": 2}'
            path.write_bytes(original)
            actual_read = Path.read_bytes

            def replace_after_read(target):
                raw = actual_read(target)
                target.write_bytes(b'{"workers": false}')
                return raw

            with patch.object(Path, 'read_bytes', replace_after_read):
                config, digest = read_config(path)
            self.assertEqual(config, {'workers': 2})
            self.assertEqual(digest, hashlib.sha256(original).hexdigest())
            with self.assertRaisesRegex(ContractError, 'workers must be an integer'):
                read_config(path)

    def test_equivalent_json_layouts_are_valid_but_keep_distinct_byte_identities(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'config.json'
            values = []
            for raw in (b'{"workers":2}', b'{ "workers": 2 }\n'):
                path.write_bytes(raw)
                values.append(read_config(path))
            self.assertEqual(values[0][0], values[1][0])
            self.assertNotEqual(values[0][1], values[1][1])

    def test_regular_unicode_member_is_within_the_physical_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            member = root / '资料 空格.txt'
            member.write_bytes(b'valid')
            self.assertEqual(resolve_member(root, member.name), member.resolve())

    @unittest.skipUnless(os.name == 'nt', 'Windows junction scenario')
    def test_windows_junction_cannot_escape_to_a_sibling_with_a_shared_path_prefix(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'owned'
            outside = Path(temporary) / 'owned-other'
            root.mkdir()
            outside.mkdir()
            (outside / 'secret.txt').write_bytes(b'outside')
            junction = root / 'linked'
            result = subprocess.run(['cmd', '/d', '/c', 'mklink', '/J', str(junction), str(outside)],
                                    capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, (result.stdout, result.stderr))
            try:
                with self.assertRaisesRegex(ContractError, 'outside the physical root'):
                    resolve_member(root, 'linked/secret.txt')
                self.assertEqual((outside / 'secret.txt').read_bytes(), b'outside')
            finally:
                os.rmdir(junction)

    @unittest.skipIf(os.name == 'nt', 'POSIX symbolic-link scenario')
    def test_posix_directory_link_cannot_escape_the_physical_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'owned'
            outside = Path(temporary) / 'owned-other'
            root.mkdir()
            outside.mkdir()
            (outside / 'secret.txt').write_bytes(b'outside')
            (root / 'linked').symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(ContractError, 'outside the physical root'):
                resolve_member(root, 'linked/secret.txt')


class InstallationLifecycleTests(unittest.TestCase):
    def test_add_remove_and_rename_across_releases_do_not_change_restore_rules(self):
        old = {'bin/reader.py': b'old', 'LICENSE': b'license'}
        new = {'bin/read.py': b'new', 'LICENSE': b'license', 'NOTICE': b'new notice'}
        old_id, new_id = file_identity(old), file_identity(new)
        installed = switch_owned_files({}, file_identity({}), old, old_id)
        upgraded = switch_owned_files(installed, old_id, new, new_id)
        restored = switch_owned_files(upgraded, new_id, old, old_id)
        self.assertEqual(restored, old)
        self.assertEqual(switch_owned_files(restored, old_id, {}, file_identity({})), {})
        self.assertEqual(old, {'bin/reader.py': b'old', 'LICENSE': b'license'})

    def test_unknown_target_or_untrusted_incoming_bytes_preserve_all_inputs(self):
        old = {'bin/reader.py': b'old'}
        new = {'bin/reader.py': b'new'}
        for current, incoming, incoming_id in (
                ({**old, 'user.txt': b'preserve'}, new, file_identity(new)),
                (old, {'bin/reader.py': b'changed'}, file_identity(new))):
            with self.subTest(current=current, incoming=incoming):
                before = copy.deepcopy((current, incoming))
                with self.assertRaises(ContractError):
                    switch_owned_files(current, file_identity(old), incoming, incoming_id)
                self.assertEqual((current, incoming), before)


if __name__ == '__main__':
    unittest.main()
