"""Portable archive names, UTF-8 pipes, LF generation and real Git conversion."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from checks.generate_index import generate as generate_index
from checks.generate_source_catalog import generate as generate_sources
from checks.validation_common import ValidationError, write_json
from tests.test_release_bundle import fixture_source
from tools.verify_release_bundle import VerificationError, checked_path, check_path_set

ROOT = Path(__file__).resolve().parents[1]


@contextmanager
def legacy_text_defaults():
    """Simulate legacy text encoding/newline defaults, not a Windows OS run."""
    original = Path.open

    def opened(path, mode='r', buffering=-1, encoding=None, errors=None, newline=None):
        if 'b' not in mode:
            if encoding in (None, 'locale'):
                encoding = 'cp1252'
            if newline is None and any(flag in mode for flag in 'wax'):
                newline = '\r\n'
        return original(path, mode, buffering, encoding, errors, newline)

    with patch.object(Path, 'open', opened):
        yield


class PortableArchivePathTests(unittest.TestCase):
    def test_windows_reserved_names_and_extensions_are_rejected_on_every_host(self):
        for name in ('CON', 'nul.txt', 'aux.tar.gz', 'prn', 'COM1.md', 'LPT9',
                     'COM¹.md', 'LPT².txt', 'COM³', 'CONIN$', 'CONOUT$', 'CON .txt'):
            with self.subTest(name=name), self.assertRaisesRegex(VerificationError, 'reserved Windows'):
                checked_path('references/' + name)

    def test_reserved_directory_components_are_also_rejected(self):
        with self.assertRaisesRegex(VerificationError, 'reserved Windows'):
            checked_path('source/NUL/document.md')

    def test_trailing_dot_space_control_and_forbidden_characters_are_rejected(self):
        for name in ('file.', 'file ', 'dir./file.md', 'file\x01.md', 'bad?.md',
                     'bad*.md', 'bad<.md', 'bad>.md', 'bad|.md', 'bad".md'):
            with self.subTest(name=name), self.assertRaisesRegex(VerificationError, 'nonportable'):
                checked_path('source/' + name)

    def test_valid_unicode_spaces_and_similar_names_remain_legal(self):
        names = ['source/中文 目录/规范.md', 'source/COM10.md', 'source/con-file.txt',
                 'source/nulldata.txt', 'source/.github/workflows/quality.yml',
                 'source/café.md', 'source/a/b.md', 'source/a/c.md']
        check_path_set(names)
        for name in names:
            self.assertEqual(checked_path(name).as_posix(), name)

    def test_ambiguous_directory_case_spellings_are_rejected(self):
        with self.assertRaisesRegex(VerificationError, 'component collision'):
            check_path_set(['source/Rules/one.md', 'source/rules/two.md'])

    def test_unicode_normalization_aliases_are_rejected(self):
        for names in (['source/café.md', 'source/cafe\u0301.md'],
                      ['source/café/one.md', 'source/cafe\u0301/two.md']):
            with self.subTest(names=names), self.assertRaisesRegex(VerificationError, 'collision'):
                check_path_set(names)

    def test_normalized_file_directory_collision_is_rejected(self):
        with self.assertRaisesRegex(VerificationError, 'collision'):
            check_path_set(['source/café', 'source/cafe\u0301/child.md'])


class Utf8AndLineEndingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='standards-text-')
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)

    def test_lookup_redirected_ascii_and_cp1252_are_still_utf8(self):
        root = self.base / '中文 Source 包'
        for name, raw in fixture_source().items():
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        foreign = self.base / '无关 工作目录'
        foreign.mkdir()
        for encoding in ('ascii', 'cp1252'):
            with self.subTest(encoding=encoding):
                environment = {**os.environ, 'PYTHONIOENCODING': encoding,
                               'PYTHONUTF8': '1', 'PYTHONDONTWRITEBYTECODE': '1'}
                result = subprocess.run(
                    [sys.executable, '-S', '-B', str(ROOT / 'tools/skill_lookup.py'),
                     '--root', str(root), '--document-id', 'STD-L0-001',
                     '--clause-id', 'ARC-001'], cwd=foreign, env=environment,
                    capture_output=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr.decode('utf-8', 'replace'))
                value = json.loads(result.stdout.decode('utf-8'))
                self.assertEqual(value['results'][0]['title'], '测试规范 1')
                self.assertIn('测试规范', value['results'][0]['path'])

    def test_json_writer_has_utf8_lf_bytes_under_legacy_defaults(self):
        path = self.base / '输入.json'
        with legacy_text_defaults():
            write_json(path, {'标题': '规范 café'})
        raw = path.read_bytes()
        self.assertNotIn(b'\r', raw)
        self.assertEqual(json.loads(raw.decode('utf-8')), {'标题': '规范 café'})

    def index_fixture(self):
        root = self.base / '索引 工作区'
        (root / 'registry').mkdir(parents=True)
        for relative in ('INDEX.md', 'registry/standards.json'):
            shutil.copyfile(ROOT / relative, root / relative)
        for path in (ROOT / 'standards').rglob('README.md'):
            target = root / path.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
        return root

    def test_index_read_and_regeneration_ignore_legacy_defaults(self):
        root = self.index_fixture()
        with legacy_text_defaults():
            generate_index(root, check=True)
            generate_index(root, check=False)
        self.assertEqual((root / 'INDEX.md').read_bytes(), (ROOT / 'INDEX.md').read_bytes())
        for path in (root / 'standards').rglob('README.md'):
            self.assertNotIn(b'\r', path.read_bytes())

    def test_index_crlf_drift_is_rejected_and_lf_neighbor_passes(self):
        root = self.index_fixture()
        path = root / 'INDEX.md'
        original = path.read_bytes()
        path.write_bytes(original.replace(b'\n', b'\r\n'))
        with self.assertRaisesRegex(ValidationError, 'generated index stale'):
            generate_index(root, check=True)
        path.write_bytes(original)
        generate_index(root, check=True)

    def test_source_catalog_reads_utf8_under_legacy_defaults(self):
        with legacy_text_defaults():
            self.assertTrue(generate_sources(ROOT, check=True)['check'])

    def test_source_catalog_regeneration_preserves_exact_utf8_lf(self):
        root = self.base / '来源 工作区'
        for directory in ('sources', 'standards', 'LICENSES'):
            shutil.copytree(ROOT / directory, root / directory)
        (root / 'registry').mkdir()
        for relative in ('LICENSE', 'LICENSE-NOTICE.md', 'registry/standards.json'):
            shutil.copyfile(ROOT / relative, root / relative)
        with legacy_text_defaults():
            generate_sources(root)
        path = root / 'registry/source-catalog.json'
        expected = (ROOT / 'registry/source-catalog.json').read_bytes()
        self.assertEqual(path.read_bytes(), expected)
        path.write_bytes(expected.replace(b'\n', b'\r\n'))
        with self.assertRaisesRegex(ValidationError, 'source catalog is stale'):
            generate_sources(root, check=True)
        path.write_bytes(expected)
        generate_sources(root, check=True)


@unittest.skipUnless(shutil.which('git'), 'Git required only for the maintainer checkout test')
class GitCheckoutByteTests(unittest.TestCase):
    def test_attributes_preserve_registered_bytes_with_autocrlf_true(self):
        with tempfile.TemporaryDirectory(prefix='standards-checkout-') as temporary:
            base = Path(temporary)
            expected = '# 中文规范\n\n准确字节。\n'.encode('utf-8')
            environment = {**os.environ, 'GIT_CONFIG_NOSYSTEM': '1',
                           'GIT_CONFIG_SYSTEM': os.devnull, 'GIT_CONFIG_GLOBAL': os.devnull,
                           'GIT_TERMINAL_PROMPT': '0'}
            observed = {}
            for use_attributes in (False, True):
                root = base / ('中文 属性启用' if use_attributes else '中文 对照组')
                root.mkdir()

                def git(*arguments):
                    return subprocess.run(['git', '-C', str(root), *arguments],
                                          env=environment, capture_output=True, check=True)

                git('init', '-b', 'main')
                git('config', 'user.name', 'Synthetic Checkout Test')
                git('config', 'user.email', 'synthetic@example.invalid')
                git('config', 'core.autocrlf', 'true')
                if use_attributes:
                    shutil.copyfile(ROOT / '.gitattributes', root / '.gitattributes')
                document = root / '中文规范.md'
                document.write_bytes(expected)
                git('add', '-A')
                git('commit', '-m', 'Create synthetic checkout fixture')
                document.unlink()
                git('checkout', '--', document.name)
                observed[use_attributes] = document.read_bytes()
            self.assertEqual(observed[False], expected.replace(b'\n', b'\r\n'))
            self.assertEqual(observed[True], expected)


if __name__ == '__main__':
    unittest.main()
