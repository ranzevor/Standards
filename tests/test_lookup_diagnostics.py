"""Regressions for conjunctive verified lookup and categorized runtime errors."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tests.test_skill_consumption import SkillConsumptionTests
from tools.skill_lookup import find

ROOT = Path(__file__).resolve().parents[1]


class LookupDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'source'
        self.root.mkdir()
        SkillConsumptionTests.write_fixture(self.root)

    def cli(self, *options, root=None):
        return subprocess.run(
            [sys.executable, '-X', 'utf8', '-B', str(ROOT / 'tools/skill_lookup.py'),
             '--root', str(self.root if root is None else root), *options],
            capture_output=True, timeout=30)

    def test_all_terms_can_match_different_verified_lines(self):
        found = find(self.root, document_id='STD-L0-001',
                     text_query='ARC-001', text_all=['完整要求'])
        self.assertEqual(found['total'], 1)
        clause = found['results'][0]
        self.assertEqual((clause['matched_line'], len(clause['term_matches'])), (5, 2))
        self.assertEqual([row['matched_line'] for row in clause['term_matches']], [5, 6])
        self.assertIn('完整要求', clause['term_matches'][1]['matched_excerpt'])

    def test_single_term_and_metadata_output_are_backward_compatible(self):
        result = find(self.root, document_id='STD-L0-001', text_query='完整要求')
        self.assertEqual(set(result), {'version', 'total', 'results'})
        self.assertNotIn('term_matches', result['results'][0])
        self.assertEqual(result['results'][0]['matched_line'], 6)
        self.assertNotIn('matched_line', find(self.root, document_id='STD-L0-001')['results'][0])

    def test_repeated_cli_terms_are_conjunctive_not_last_wins(self):
        found = self.cli('--document-id', 'STD-L0-001', '--text-query', '不存在的字面词',
                         '--text-query', '完整要求')
        self.assertEqual(found.returncode, 0, found.stderr.decode('utf-8'))
        self.assertEqual(json.loads(found.stdout)['total'], 0)
        found = self.cli('--document-id', 'STD-L0-001', '--text-query', 'ARC-001',
                         '--text-query', '完整要求')
        self.assertEqual(found.returncode, 0, found.stderr.decode('utf-8'))
        self.assertEqual(len(json.loads(found.stdout)['results'][0]['term_matches']), 2)

    def test_bad_terms_rejected_without_losing_prior_filters(self):
        for kwargs in ({'text_all': 'word'}, {'text_all': ['']},
                       {'text_query': 'a', 'text_all': ['b'] * 8}):
            with self.subTest(kwargs=kwargs), self.assertRaisesRegex(ValueError, 'text'):
                find(self.root, **kwargs)

    def test_error_json_distinguishes_invalid_query_missing_and_integrity(self):
        unknown = self.cli('--error-json', '--document-id', 'STD-NOT-FOUND')
        self.assertEqual((unknown.returncode, unknown.stdout), (1, b''))
        self.assertEqual(json.loads(unknown.stderr)['code'], 'INVALID_QUERY')
        missing_source = self.root / 'standards/L0/001-测试规范--v0.1.0.md'
        missing_source.unlink()
        missing = self.cli('--error-json')
        self.assertEqual((missing.returncode, missing.stdout), (1, b''))
        self.assertEqual(json.loads(missing.stderr)['code'], 'SOURCE_MISSING')

    def test_parsed_out_of_range_values_respect_error_output_mode(self):
        cases = (
            ('--limit', '0', 'limit must be 1..100'),
            ('--limit', '101', 'limit must be 1..100'),
            ('--offset', '-1', 'offset must be a nonnegative integer'),
        )
        for flag, value, message in cases:
            with self.subTest(flag=flag, value=value, mode='json'):
                response = self.cli('--error-json', flag, value)
                self.assertEqual((response.returncode, response.stdout), (1, b''))
                error = json.loads(response.stderr.decode('utf-8'))
                self.assertEqual(set(error), {'code', 'message', 'next_action'})
                self.assertEqual((error['code'], error['message']),
                                 ('INVALID_QUERY', message))
                self.assertIn('Correct the query', error['next_action'])
                self.assertEqual(len(response.stderr.decode('utf-8').splitlines()), 1)
            with self.subTest(flag=flag, value=value, mode='legacy'):
                response = self.cli(flag, value)
                self.assertEqual((response.returncode, response.stdout), (2, b''))
                stderr = response.stderr.decode('utf-8')
                self.assertIn('usage:', stderr)
                self.assertIn('error: ' + message, stderr)
                self.assertNotIn('INVALID_QUERY', stderr)

    def test_file_and_missing_roots_are_input_errors_in_both_modes(self):
        ordinary_file = Path(self.temp.name) / 'not-a-directory'
        ordinary_file.write_text('not a lookup release', encoding='utf-8')
        missing_directory = Path(self.temp.name) / 'not-created'
        for root in (ordinary_file, missing_directory):
            with self.subTest(root=root, mode='json'):
                response = self.cli('--error-json', root=root)
                self.assertEqual((response.returncode, response.stdout), (1, b''))
                error = json.loads(response.stderr.decode('utf-8'))
                self.assertEqual(error['code'], 'INVALID_QUERY')
                self.assertEqual(error['message'], 'lookup root is not a plain directory')
                self.assertIn('Set --root', error['next_action'])
            with self.subTest(root=root, mode='legacy'):
                response = self.cli(root=root)
                self.assertEqual((response.returncode, response.stdout), (1, b''))
                self.assertEqual(response.stderr.decode('utf-8').strip(),
                                 'lookup failed: lookup root is not a plain directory')

    def test_argparse_syntax_errors_keep_exit_two_even_with_error_json(self):
        for flag, value in (('--limit', 'not-an-integer'), ('--offset', '1.5')):
            with self.subTest(flag=flag):
                response = self.cli('--error-json', flag, value)
                self.assertEqual((response.returncode, response.stdout), (2, b''))
                stderr = response.stderr.decode('utf-8')
                self.assertIn('usage:', stderr)
                self.assertIn('invalid int value', stderr)

    def test_corrupt_clause_index_has_integrity_error_not_zero_results(self):
        path = self.root / 'registry/requirements.json'
        rows = json.loads(path.read_text(encoding='utf-8'))
        rows[0]['section_sha256'] = '0' * 64
        path.write_text(json.dumps(rows), encoding='utf-8')
        response = self.cli('--error-json', '--document-id', 'STD-L0-001',
                            '--text-query', '完整要求')
        self.assertEqual((response.returncode, response.stdout), (1, b''))
        error = json.loads(response.stderr)
        self.assertEqual(error['code'], 'INTEGRITY_ERROR')
        self.assertIn('digest', error['message'])
        self.assertTrue(error['next_action'])
        legacy = self.cli('--document-id', 'STD-L0-001', '--text-query', '完整要求')
        self.assertEqual(legacy.returncode, 1)
        self.assertIn('lookup failed:', legacy.stderr.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
