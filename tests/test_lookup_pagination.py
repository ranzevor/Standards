"""Traverse verified lookup results without changing the existing output contract."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tests.test_release_bundle import fixture_source, bundle_parts, write_directory
from tests import test_skill_consumption
from tools.skill_lookup import find
from tools.verify_release_bundle import canonical, VerificationError

ROOT = Path(__file__).resolve().parents[1]


class LookupPaginationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='standards-pages-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / '规范 源码'
        self.root.mkdir()
        test_skill_consumption.SkillConsumptionTests.write_fixture(self.root)

    def test_old_positional_call_and_default_response_are_unchanged(self):
        old = find(self.root, None, None, None, 'core', 20, '完整要求')
        explicit = find(self.root, domain='core', text_query='完整要求', offset=0)
        self.assertEqual(old, explicit)
        self.assertEqual(set(old), {'version', 'total', 'results'})
        self.assertEqual((old['total'], len(old['results'])), (162, 20))

    def test_all_metadata_and_text_results_are_reachable_once_in_order(self):
        expected = [f'STD-L0-{i:03d}' for i in range(1, 163)]
        for options in ({'domain': 'core'}, {'domain': 'core', 'text_query': '完整要求'}):
            with self.subTest(options=options):
                rows = []
                for offset in range(0, 162, 37):
                    result = find(self.root, limit=37, offset=offset, **options)
                    self.assertEqual(result['total'], 162)
                    self.assertEqual(len(result['results']), min(37, 162 - offset))
                    rows.extend(result['results'])
                self.assertEqual([row['document_id'] for row in rows], expected)
                self.assertEqual(len({row['document_id'] for row in rows}), 162)
                self.assertEqual(find(self.root, limit=100, offset=100, **options)['results'], rows[100:])
                self.assertEqual(find(self.root, limit=1, offset=161, **options)['results'], rows[-1:])

    def test_offsets_past_end_and_empty_queries_preserve_total(self):
        for offset in (162, 163, 10**100):
            result = find(self.root, offset=offset)
            self.assertEqual((result['total'], result['results']), (162, []))
        result = find(self.root, text_query='NO_MATCH_IN_SOURCE', offset=4)
        self.assertEqual((result['total'], result['results']), (0, []))

    def test_offset_is_applied_after_combined_filters(self):
        options = dict(query='测试规范', document_id='STD-L0-100', domain='CORE',
                       clause_id='arc-100', text_query='完整要求', limit=1)
        result = find(self.root, offset=0, **options)
        self.assertEqual(result['results'][0]['document_id'], 'STD-L0-100')
        second = find(self.root, offset=1, **options)
        self.assertEqual((second['total'], second['results']), (1, []))

    def test_invalid_offsets_rejected_by_api_and_cli(self):
        for offset in (-1, True, False, 0.0, '0', None):
            with self.subTest(offset=offset), self.assertRaisesRegex(ValueError, 'offset'):
                find(self.root, offset=offset)
        for value in ('-1', '1.5', 'invalid'):
            result = subprocess.run(
                [sys.executable, '-B', str(ROOT / 'tools/skill_lookup.py'),
                 '--root', str(self.root), '--offset', value], capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 2, result.stderr.decode('utf-8'))
            self.assertEqual(result.stdout, b'')
            self.assertIn('offset', result.stderr.decode('utf-8'))

    def test_pagination_does_not_hide_invalid_records_in_other_pages(self):
        path = self.root / 'registry/requirements.json'
        rows = json.loads(path.read_bytes())
        rows[-1]['fields'] = {'机制': '不属于正文的内容'}
        path.write_bytes(canonical(rows))
        for offset in (0, 200):
            with self.subTest(offset=offset), self.assertRaisesRegex(VerificationError, 'contract fields'):
                find(self.root, text_query='完整要求', limit=1, offset=offset)

    def test_source_and_skill_entrypoints_page_from_foreign_working_directory(self):
        source = fixture_source()
        for kind in ('source', 'agent-skill'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temp:
                records, _, metadata = bundle_parts(source, kind)
                directory = write_directory(temp, records, metadata)
                foreign = Path(temp) / '项目 工作目录'
                foreign.mkdir()
                script = directory / ('source/tools/skill_lookup.py' if kind == 'source' else 'scripts/lookup.py')
                result = subprocess.run(
                    [sys.executable, '-S', '-X', 'utf8', '-B', str(script),
                     '--text-query', '完整要求', '--domain', 'core', '--limit', '100', '--offset', '100'],
                    cwd=foreign, capture_output=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr.decode('utf-8'))
                data = json.loads(result.stdout.decode('utf-8'))
                self.assertEqual((data['total'], len(data['results'])), (162, 62))
                self.assertEqual(data['results'][0]['document_id'], 'STD-L0-101')
                self.assertEqual(data['results'][-1]['document_id'], 'STD-L0-162')


if __name__ == '__main__':
    unittest.main()
