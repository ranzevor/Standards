"""Check synthetic behavioral fixtures without claiming a model execution."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from checks.behavior_cases import validate_suite

ROOT = Path(__file__).resolve().parents[1]


class RetrievalFeedbackDeliveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.suite = json.loads((ROOT / 'examples/ai-agent/behavior/cases/retrieval-feedback-delivery.json')
                               .read_text(encoding='utf-8'))

    def test_all_cases_have_bounded_scope_and_valid_contracts(self):
        self.assertEqual(validate_suite(self.suite), 6)
        self.assertEqual({case['id'] for case in self.suite['cases']},
                         {'RETR-001', 'RETR-002', 'FEED-001', 'FEED-002', 'FEED-003', 'DELI-001'})
        for case in self.suite['cases']:
            self.assertTrue(case['authorization']['allowed'])
            self.assertTrue(case['authorization']['forbidden'])
            self.assertTrue(case['rubric'])

    def test_incomplete_pagination_feedback_matches_page(self):
        case = next(x for x in self.suite['cases'] if x['id'] == 'RETR-002')
        source = json.loads(case['setup'][0]['text'])
        expected = case['checks'][0]['expected']
        self.assertEqual(expected['remaining'], source['total'] - len(source['results']))
        self.assertEqual(expected['next_offset'], source['offset'] + len(source['results']))

    def test_code_delivery_fixture_fails_then_passes_actual_tests(self):
        case = next(x for x in self.suite['cases'] if x['id'] == 'DELI-001')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for item in case['setup']:
                (root / item['path']).write_text(item['text'], encoding='utf-8')
            command = [sys.executable, '-X', 'utf8', '-B', '-m', 'unittest', '-v', 'test_formatter']
            broken = subprocess.run(command, cwd=root, capture_output=True, timeout=30)
            self.assertNotEqual(broken.returncode, 0)
            (root / 'formatter.py').write_text(
                "def normalize(value):\n"
                "    if not isinstance(value, str):\n"
                "        raise TypeError('string required')\n"
                "    return value.strip().casefold()\n",
                encoding='utf-8')
            fixed = subprocess.run(command, cwd=root, capture_output=True, timeout=30)
            self.assertEqual(fixed.returncode, 0, fixed.stderr.decode('utf-8'))
            self.assertIn('Ran 2 tests', fixed.stderr.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
