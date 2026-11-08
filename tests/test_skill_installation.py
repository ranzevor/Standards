"""Execute the documented installation with isolated project and home directories."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from tests.test_release_bundle import fixture_source, bundle_parts, write_directory
from tools.verify_release_bundle import verify_directory

ROOT = Path(__file__).resolve().parents[1]


def install_code(source, host, scope):
    text = (ROOT / 'guides/SKILL-INSTALLATION.md').read_text(encoding='utf-8')
    code = re.search(r'```python\n(.*?)\n```', text, re.S)[1]
    return (code.replace("source = Path('/absolute/path/ranzevor-standards')", f'source = Path({str(source)!r})')
            .replace("host = 'codex'", f'host = {host!r}')
            .replace("scope = 'project'", f'scope = {scope!r}'))


class SkillInstallationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='standards-install-')
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.project = self.base / '示例 项目'
        self.project.mkdir()
        self.home = self.base / '独立 用户'
        self.home.mkdir()
        records, _, metadata = bundle_parts(fixture_source(), 'agent-skill')
        (self.base / 'staging').mkdir()
        self.source = write_directory(self.base / 'staging', records, metadata)
        self.env = {**os.environ, 'HOME': str(self.home), 'USERPROFILE': str(self.home),
                    'PYTHONDONTWRITEBYTECODE': '1'}

    def install(self, host, scope):
        return subprocess.run([sys.executable, '-S', '-X', 'utf8', '-B', '-c',
                               install_code(self.source, host, scope)],
                              cwd=self.project, env=self.env, capture_output=True, timeout=30)

    def test_both_hosts_and_scopes_keep_the_whole_bundle_usable(self):
        for host, folder in (('codex', '.agents'), ('claude-code', '.claude')):
            for scope, parent in (('project', self.project), ('user', self.home)):
                with self.subTest(host=host, scope=scope):
                    result = self.install(host, scope)
                    self.assertEqual(result.returncode, 0, result.stderr.decode('utf-8'))
                    target = parent / folder / 'skills/ranzevor-standards'
                    self.assertTrue((target / 'SKILL.md').is_file())
                    self.assertFalse((target / 'ranzevor-standards').exists())
                    verify_directory(target)
                    lookup = subprocess.run([sys.executable, '-S', '-X', 'utf8', '-B',
                                             str(target / 'scripts/lookup.py'), '--document-id', 'STD-L0-001',
                                             '--text-query', '完整要求'], cwd=self.project, env=self.env,
                                            capture_output=True, timeout=30)
                    self.assertEqual(lookup.returncode, 0, lookup.stderr.decode('utf-8'))
                    hit = json.loads(lookup.stdout)['results'][0]
                    self.assertTrue((target / hit['path']).is_file())
                    verify_directory(target)

    def test_existing_installation_is_not_overlaid(self):
        for host, folder in (('codex', '.agents'), ('claude-code', '.claude')):
            with self.subTest(host=host):
                target = self.project / folder / 'skills/ranzevor-standards'
                target.mkdir(parents=True)
                original = target / 'keep.txt'
                original.write_text('original', encoding='utf-8')
                result = self.install(host, 'project')
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(original.read_text(encoding='utf-8'), 'original')
                self.assertEqual([path.name for path in target.iterdir()], ['keep.txt'])

    def test_invalid_package_never_creates_an_installation(self):
        (self.source / 'references/project.json').write_text('{}', encoding='utf-8')
        for host, folder in (('codex', '.agents'), ('claude-code', '.claude')):
            with self.subTest(host=host):
                result = self.install(host, 'project')
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((self.project / folder).exists())

    def test_unsupported_host_or_scope_does_not_write(self):
        for host, scope in (('unknown', 'project'), ('codex', 'unknown')):
            with self.subTest(host=host, scope=scope):
                self.assertNotEqual(self.install(host, scope).returncode, 0)
        self.assertEqual(list(self.project.iterdir()), [])
        self.assertEqual(list(self.home.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
