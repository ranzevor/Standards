"""Scope-safe installation and recovery for host-selected discovery directories."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tests.platform_support import make_symlink
from tests.test_release_bundle import fixture_source, bundle_parts, write_directory
from tools import install_skill
from tools.verify_release_bundle import verify_directory

ROOT = Path(__file__).resolve().parents[1]


class SkillInstallationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='standards-install-')
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.project = self.base / '示例 项目'
        self.project.mkdir()
        self.home = self.base / '独立 用户'
        self.home.mkdir()
        source = fixture_source()
        source['tools/install_skill.py'] = (ROOT / 'tools/install_skill.py').read_bytes()
        self.source_files = source
        records, _, metadata = bundle_parts(source, 'agent-skill')
        (self.base / 'download').mkdir()
        self.source = write_directory(self.base / 'download', records, metadata)
        self.relative = Path('client/skills')
        self.skills = self.project / self.relative
        self.target = self.skills / 'ranzevor-standards'

    def install(self, **kwargs):
        return install_skill.install(self.source, self.project, self.relative, **kwargs)

    def assert_no_installation(self):
        self.assertFalse(os.path.lexists(self.target))
        self.assertEqual(list(self.project.glob('.standards-install-*')), [])

    def test_host_selected_directories_and_explicit_scopes_keep_complete_bundles(self):
        for relative in (Path('.agents/skills'), Path('.claude/skills'), Path('extensions/custom-skills')):
            for scope in (self.project, self.home):
                with self.subTest(relative=relative, scope=scope.name):
                    result = install_skill.install(self.source, scope, relative)
                    target = scope / relative / 'ranzevor-standards'
                    self.assertEqual(result['version'], '0.1.0')
                    self.assertTrue(Path(result['path']).samefile(target))
                    verify_directory(target)
                    output = subprocess.run(
                        [sys.executable, '-S', '-X', 'utf8', '-B', str(target / 'scripts/lookup.py'),
                         '--document-id', 'STD-L0-001', '--text-query', '完整要求'],
                        cwd=self.project, capture_output=True, timeout=30)
                    self.assertEqual(output.returncode, 0, output.stderr.decode('utf-8'))
                    hit = json.loads(output.stdout)['results'][0]
                    self.assertTrue((target / hit['path']).is_file())
                    verify_directory(target)

    def test_existing_empty_or_populated_installation_is_not_overlaid(self):
        self.target.mkdir(parents=True)
        with self.assertRaises(FileExistsError):
            self.install()
        self.assertEqual(list(self.target.iterdir()), [])
        original = self.target / 'keep.txt'
        original.write_text('original', encoding='utf-8')
        with self.assertRaises(FileExistsError):
            self.install()
        self.assertEqual(original.read_text(encoding='utf-8'), 'original')
        self.assertEqual(list(self.target.iterdir()), [original])
        self.assertEqual(list(self.project.glob('.standards-install-*')), [])

    def test_invalid_package_does_not_create_installation_parents(self):
        (self.source / 'references/project.json').write_text('{}', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.install()
        self.assertEqual(list(self.project.iterdir()), [])

    def test_links_at_each_target_parent_cannot_write_outside_scope(self):
        for scope in (self.project, self.home):
            for linked in (Path('client'), Path('client/skills')):
                with self.subTest(scope=scope.name, linked=linked):
                    outside = self.base / ('outside-' + scope.name + '-' + str(len(linked.parts)))
                    outside.mkdir()
                    link = scope / linked
                    link.parent.mkdir(parents=True, exist_ok=True)
                    make_symlink(link, outside, target_is_directory=True)
                    try:
                        with self.assertRaisesRegex(ValueError, 'link or reparse'):
                            install_skill.install(self.source, scope, self.relative)
                        self.assertEqual(list(outside.iterdir()), [])
                    finally:
                        link.unlink()

    @unittest.skipUnless(os.name == 'nt', 'Windows junction requires Windows')
    def test_native_windows_junction_cannot_redirect_project_installation(self):
        for linked in (Path('client'), Path('client/skills')):
            with self.subTest(linked=linked):
                outside = self.base / ('junction-outside-' + str(len(linked.parts)))
                outside.mkdir()
                link = self.project / linked
                link.parent.mkdir(parents=True, exist_ok=True)
                result = subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(outside)],
                                        capture_output=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                try:
                    with self.assertRaisesRegex(ValueError, 'link or reparse'):
                        self.install()
                    self.assertEqual(list(outside.iterdir()), [])
                finally:
                    link.rmdir()

    def test_linked_staging_and_dangling_existing_target_are_rejected(self):
        outside = self.base / 'outside'; outside.mkdir()
        link = self.project / 'staging'
        make_symlink(link, outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'link or reparse'):
            self.install(staging_parent=Path('staging'))
        self.assertEqual(list(outside.iterdir()), [])
        self.skills.mkdir(parents=True)
        make_symlink(self.target, self.base / 'absent', target_is_directory=True)
        with self.assertRaises(FileExistsError):
            self.install()
        self.assertTrue(self.target.is_symlink())

    def test_redirect_inserted_during_copy_is_rejected_before_publication(self):
        outside = self.base / 'late-outside'; outside.mkdir()
        self.skills.mkdir(parents=True)
        probe = self.project / 'link-probe'
        make_symlink(probe, outside, target_is_directory=True)
        probe.unlink()
        copytree = shutil.copytree
        def redirect(src, dst, *args, **kwargs):
            result = copytree(src, dst, *args, **kwargs)
            if Path(src) == self.source:
                self.skills.rmdir()
                self.skills.symlink_to(outside, target_is_directory=True)
            return result
        with patch('shutil.copytree', side_effect=redirect), self.assertRaisesRegex(ValueError, 'link or reparse'):
            self.install()
        self.assertEqual(list(outside.iterdir()), [])
        self.assertEqual(list(self.project.glob('.standards-install-*')), [])

    def test_scope_escape_and_discoverable_staging_are_rejected(self):
        for relative, stage in ((Path('../outside'), Path('.')),
                                (self.base / 'outside', Path('.')),
                                (self.relative, Path('../outside')),
                                (self.relative, self.relative),
                                (self.relative, self.relative / 'temporary'),
                                (Path('.'), Path('.'))):
            with self.subTest(relative=relative, stage=stage), self.assertRaises(ValueError):
                install_skill.install(self.source, self.project, relative, stage)
        self.assertEqual(list(self.project.iterdir()), [])

    def test_source_cannot_contain_its_own_staging_copy(self):
        with self.assertRaisesRegex(ValueError, 'inside the source'):
            install_skill.install(self.source, self.source, Path('client/skills'))
        verify_directory(self.source)

    def test_copy_error_and_keyboard_interrupt_leave_no_discoverable_skill_and_retry(self):
        original = shutil.copyfile
        for failure in (OSError('copy failed'), KeyboardInterrupt()):
            with self.subTest(error=type(failure).__name__):
                calls = []
                def copy(src, dst, *args, **kwargs):
                    calls.append(dst)
                    self.assertFalse(self.target.exists())
                    if len(calls) == 3:
                        raise failure
                    return original(src, dst, *args, **kwargs)
                with patch('shutil.copyfile', side_effect=copy), self.assertRaises(type(failure)):
                    self.install()
                self.assert_no_installation()
        result = self.install()
        self.assertTrue(Path(result['path']).samefile(self.target))
        verify_directory(self.target)

    def test_copied_content_is_verified_before_publication(self):
        copytree = shutil.copytree
        def corrupt(src, dst, *args, **kwargs):
            result = copytree(src, dst, *args, **kwargs)
            if Path(src) == self.source:
                (Path(dst) / 'references/project.json').write_bytes(b'{}')
            return result
        with patch('shutil.copytree', side_effect=corrupt), self.assertRaises(ValueError):
            self.install()
        self.assert_no_installation()
        self.install()
        verify_directory(self.target)

    def test_publish_error_cleans_only_its_staging_and_preserves_other_skills(self):
        other = self.skills / 'other-skill'
        other.mkdir(parents=True)
        (other / 'SKILL.md').write_text('keep', encoding='utf-8')
        with patch('tools.install_skill._publish', side_effect=OSError('move failed')), self.assertRaises(OSError):
            self.install()
        self.assert_no_installation()
        self.assertEqual((other / 'SKILL.md').read_text(encoding='utf-8'), 'keep')
        self.install()
        verify_directory(self.target)

    def test_competing_empty_target_is_not_replaced(self):
        publish = install_skill._publish
        def compete(source, target):
            target.mkdir()
            publish(source, target)
        with patch('tools.install_skill._publish', side_effect=compete), self.assertRaises(FileExistsError):
            self.install()
        self.assertTrue(self.target.is_dir())
        self.assertEqual(list(self.target.iterdir()), [])
        self.assertEqual(list(self.project.glob('.standards-install-*')), [])

    def test_concurrent_installations_have_one_complete_winner(self):
        def attempt(_):
            try:
                self.install()
                return 'installed'
            except FileExistsError:
                return 'exists'
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt, range(2)))
        self.assertEqual(sorted(results), ['exists', 'installed'])
        verify_directory(self.target)
        self.assertEqual(list(self.project.glob('.standards-install-*')), [])

    def test_abrupt_exit_keeps_partial_copy_outside_discovery_and_retry_is_independent(self):
        code = '''
import os, shutil, sys
from pathlib import Path
from tools.install_skill import install
copyfile = shutil.copyfile
count = 0
def crash(src, dst, *args, **kwargs):
    global count
    count += 1
    if count == 3:
        os._exit(29)
    return copyfile(src, dst, *args, **kwargs)
shutil.copyfile = crash
install(Path(sys.argv[1]), Path(sys.argv[2]), Path('client/skills'))
'''
        crashed = subprocess.run([sys.executable, '-B', '-c', code, str(self.source), str(self.project)],
                                 cwd=ROOT, capture_output=True, timeout=30)
        self.assertEqual(crashed.returncode, 29, crashed.stderr)
        self.assertFalse(self.target.exists())
        self.assertEqual(list(self.skills.rglob('SKILL.md')), [])
        abandoned = list(self.project.glob('.standards-install-*'))
        self.assertEqual(len(abandoned), 1)
        self.install()
        verify_directory(self.target)
        self.assertEqual(list(self.project.glob('.standards-install-*')), abandoned)

    def test_packaged_installer_runs_from_a_foreign_working_directory(self):
        for kind in ('source', 'agent-skill'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                records, _, metadata = bundle_parts(self.source_files, kind)
                bundle = write_directory(temporary, records, metadata)
                script = bundle / ('source/tools/install_skill.py' if kind == 'source'
                                   else 'references/tools/install_skill.py')
                scope = Path(temporary) / '安装 项目'; scope.mkdir()
                result = subprocess.run([sys.executable, '-S', '-X', 'utf8', '-B', str(script),
                                         '--source', str(self.source), '--scope-root', str(scope),
                                         '--skills-dir', 'extensions/local'], cwd=self.project,
                                        env={**os.environ, 'PYTHONIOENCODING': 'ascii'},
                                        capture_output=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr.decode('utf-8'))
                installed = Path(json.loads(result.stdout)['path'])
                verify_directory(installed)
                verify_directory(bundle)


class InstallationPromptTests(unittest.TestCase):
    def test_readme_prompts_match_the_two_installation_guide_languages(self):
        guide = (ROOT / 'guides/SKILL-INSTALLATION.md').read_text(encoding='utf-8')
        prompts = re.findall(r'```text\n(.*?)\n```', guide, re.S)
        self.assertEqual(len(prompts), 2)
        for index, name in enumerate(('README.md', 'README.en.md')):
            readme = (ROOT / name).read_text(encoding='utf-8')
            actual = re.findall(r'```text\n(.*?)\n```', readme, re.S)
            self.assertEqual(actual, [prompts[index]])


if __name__ == '__main__':
    unittest.main()
