"""Agent Skill entrypoint and verified offline clause consumption."""
from pathlib import Path
import json
import re
import subprocess
import sys
import tempfile
import unittest

from tools.skill_lookup import find
from tests.test_release_bundle import fixture_source
from tools.verify_release_bundle import VerificationError

ROOT = Path(__file__).resolve().parents[1]


class SkillConsumptionTests(unittest.TestCase):
    def test_entrypoint_metadata_and_progressive_disclosure(self):
        raw = (ROOT / 'skills/ranzevor-standards/SKILL.md.in').read_text(encoding='utf-8')
        self.assertTrue(raw.startswith('---\n'))
        front, body = raw[4:].split('\n---\n', 1)
        self.assertRegex(front, r'(?m)^name: ranzevor-standards$')
        self.assertRegex(front, r'(?m)^license: references/LICENSE$')
        self.assertRegex(front, r'(?m)^description: .{50,1024}$')
        self.assertLess(len(raw.splitlines()), 500)
        version = json.loads((ROOT / 'project.json').read_text(encoding='utf-8'))['version']
        self.assertIn(f'  version: "{version}"', front)
        self.assertIn('scripts/lookup.py', body)
        self.assertIn('references/guides/SKILL-CONSUMPTION.md', body)
        self.assertTrue((ROOT / 'guides/SKILL-CONSUMPTION.md').is_file())

    @staticmethod
    def build_fixture(directory):
        for name, content in fixture_source().items():
            path = directory / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)

    def test_exact_text_returns_clause_and_original_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.build_fixture(root)
            result = find(root, text_query='完整要求', document_id='STD-L0-001')
            self.assertEqual(result['version'], '0.1.0')
            self.assertEqual(result['total'], 1)
            hit = result['results'][0]
            self.assertEqual(hit['clause_id'], 'ARC-001')
            self.assertEqual(hit['matched_line'], 6)
            self.assertIn('完整要求', hit['matched_excerpt'])
            clause = json.loads((root / 'registry/requirements.json').read_text(encoding='utf-8'))[0]
            self.assertEqual(hit['section_sha256'], clause['section_sha256'])
            self.assertEqual(hit['sha256'], clause['document_sha256'])

    def test_no_match_is_empty_and_metadata_query_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.build_fixture(root)
            self.assertEqual(find(root, text_query='不存在的唯一词组')['total'], 0)
            self.assertEqual(find(root, query='测试规范 1')['total'], 1)
            self.assertEqual(find(root, document_id='STD-L0-001', clause_id='ARC-001')['total'], 1)
            self.assertEqual(find(root, document_id='STD-L0-001', text_query='完整要求',
                                  clause_id='ARC-999')['total'], 0)

    def test_corrupted_source_and_clause_hash_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.build_fixture(root)
            clause_path = root / 'registry/requirements.json'
            clauses = json.loads(clause_path.read_text(encoding='utf-8'))
            clauses[0]['section_sha256'] = '0' * 64
            clause_path.write_text(json.dumps(clauses, ensure_ascii=False), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'clause content digest mismatch'):
                find(root, text_query='完整要求')
            self.build_fixture(root)
            doc_path = next((root / 'standards').rglob('001-测试规范--v0.1.0.md'))
            doc_path.write_bytes(doc_path.read_bytes() + b'\n')
            with self.assertRaises(VerificationError):
                find(root, text_query='完整要求')

    def test_reject_blank_overlong_or_ambiguous_text_query(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.build_fixture(root)
            for phrase in ('', '   ', '\x00', 'x' * 257):
                with self.subTest(phrase=repr(phrase)), self.assertRaisesRegex(ValueError, 'text-query'):
                    find(root, text_query=phrase)

    def test_cli_from_another_directory_emits_utf8_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / '中文 源目录'
            root.mkdir()
            self.build_fixture(root)
            result = subprocess.run(
                [sys.executable, '-X', 'utf8', '-B', str(ROOT / 'tools/skill_lookup.py'),
                 '--root', str(root), '--text-query', '完整要求', '--document-id', 'STD-L0-001'],
                cwd=tmp, capture_output=True, timeout=30, check=False)
            self.assertEqual(result.returncode, 0, result.stderr.decode('utf-8'))
            payload = json.loads(result.stdout.decode('utf-8'))
            self.assertEqual(payload['total'], 1)
            self.assertEqual(payload['results'][0]['matched_line'], 6)


if __name__ == '__main__':
    unittest.main()
