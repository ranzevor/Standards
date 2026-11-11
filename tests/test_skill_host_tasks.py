"""Validate reusable task inputs; these fixtures do not run an Agent host."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from checks.behavior_cases import validate_suite

ROOT = Path(__file__).resolve().parents[1]


class SkillHostTaskInputsTests(unittest.TestCase):
    def setUp(self):
        self.suite = json.loads((ROOT / 'examples/ai-agent/behavior/cases/skill-host-tasks.json').read_text(encoding='utf-8'))

    def test_suite_covers_review_repair_and_release_with_real_lookup_rubric(self):
        self.assertEqual(validate_suite(self.suite), 3)
        self.assertEqual({case['id'] for case in self.suite['cases']}, {'HOST-001', 'HOST-002', 'HOST-003'})
        for case in self.suite['cases']:
            self.assertIn('normative-use', {rubric['id'] for rubric in case['rubric']})
            self.assertFalse(any(row['path'] == 'lookup.json' for row in case['setup']))

    def test_repair_input_really_fails_and_a_legal_implementation_passes(self):
        case = next(case for case in self.suite['cases'] if case['id'] == 'HOST-002')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for row in case['setup']:
                (root / row['path']).write_text(row['text'], encoding='utf-8')
            command = [sys.executable, '-X', 'utf8', '-B', '-m', 'unittest', 'test_runner', '-v']
            broken = subprocess.run(command, cwd=root, capture_output=True, timeout=30)
            self.assertEqual(broken.returncode, 1)
            self.assertIn('0 != 7', broken.stderr.decode('utf-8'))
            (root / 'runner.py').write_text(
                'import subprocess\n\ndef run(command):\n    return subprocess.run(command, check=False).returncode\n',
                encoding='utf-8')
            fixed = subprocess.run(command, cwd=root, capture_output=True, timeout=30)
            self.assertEqual(fixed.returncode, 0, fixed.stderr.decode('utf-8'))

    def test_review_requires_source_preservation(self):
        case = next(case for case in self.suite['cases'] if case['id'] == 'HOST-001')
        source = next(row['text'] for row in case['setup'] if row['path'] == 'runner.py')
        check = next(row for row in case['checks'] if row['path'] == 'runner.py')
        self.assertEqual((check['kind'], check['expected']), ('text_equals', source))

    def test_release_input_has_one_missing_required_target_and_is_unpublished(self):
        case = next(case for case in self.suite['cases'] if case['id'] == 'HOST-003')
        state = json.loads(next(row['text'] for row in case['setup'] if row['path'] == 'release.json'))
        check = next(row for row in case['checks'] if row['kind'] == 'json_equals')
        missing = [name for name in state['required_checks'] if state['checks'].get(name) != 'pass']
        self.assertEqual(check['expected'], {'ready': not missing, 'published': state['published'], 'blocking': missing})
        self.assertEqual(missing, ['native_windows'])


if __name__ == '__main__':
    unittest.main()
