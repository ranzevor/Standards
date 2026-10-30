"""Each mutation changes a delivery invariant; an inert comment remains legal."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CDCMutationTests(unittest.TestCase):
    def run_variant(self, old, new):
        source = (ROOT / 'checks/database_examples.py').read_text()
        self.assertEqual(source.count(old), 1, 'mutation target must be unambiguous')
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for folder in ('checks', 'tests'):
                (root / folder).mkdir(); (root / folder / '__init__.py').write_text('')
            (root / 'checks/database_examples.py').write_text(source.replace(old, new))
            shutil.copyfile(ROOT / 'tests/test_database_cdc_progress.py', root / 'tests/test_database_cdc_progress.py')
            return subprocess.run([sys.executable, '-B', '-m', 'unittest', 'tests.test_database_cdc_progress'],
                                  cwd=root, capture_output=True, text=True, timeout=30)

    def test_early_duplicate_return_is_killed(self):
        old = "            need(known[0]==payload,'same event identity, different payload')"
        result = self.run_variant(old, old + "\n            connection.rollback();return 'duplicate'")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('test_same_source_event_at_new_delivery_position_advances_cursor_once', result.stderr)

    def test_epoch_in_source_content_is_killed(self):
        result = self.run_variant("if k!='epoch'", 'if True')
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('test_current_epoch_replay_preserves_source_identity_and_progress', result.stderr)

    def test_cursor_not_advanced_is_killed(self):
        result = self.run_variant("(next_cursor,stream,event['epoch'],predecessor)", "(predecessor,stream,event['epoch'],predecessor)")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('test_same_source_event_at_new_delivery_position_advances_cursor_once', result.stderr)

    def test_stale_writer_fence_removed_is_killed(self):
        result = self.run_variant("need(row[0]==event['epoch'],'stale writer fenced at effect time')",
                                  "need(True,'stale writer fenced at effect time')")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('test_stale_epoch_is_fenced_even_for_an_already_known_event', result.stderr)

    def test_source_comment_neighbor_is_accepted(self):
        old = '# LSN alone is deliberately not the event identity.'
        result = self.run_variant(old, old + ' Delivery metadata is separate.')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('Ran 16 tests', result.stderr)


if __name__ == '__main__': unittest.main(verbosity=2)
