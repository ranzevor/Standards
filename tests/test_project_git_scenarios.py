"""Exercise real Git transitions, including semantic mutations and legal neighbors."""
import importlib.util
import contextlib
import io
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / 'examples/project-governance/git_scenarios.py'
SPEC = importlib.util.spec_from_file_location('project_git_scenarios', MODULE_PATH)
git_scenarios = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(git_scenarios)


class ProjectGitScenarios(unittest.TestCase):
    def assert_scenario(self, name):
        r = git_scenarios.run_scenario(name)
        self.assertEqual(r['status'], 'passed', r['report_path'])
        self.assertTrue(r['commands'])
        self.assertTrue(r['assertions'])
        self.assertTrue(r['snapshots'])
        self.assertTrue(all(c['matches'] for c in r['commands']))
        self.assertTrue(all(c['matches'] for c in r['assertions']))
        saved = json.loads(Path(r['report_path']).read_text())
        self.assertEqual(saved['status'], 'passed')
        self.assertFalse((Path(r['evidence_dir']) / 'sandbox').exists())

    def test_index_snapshot(self): self.assert_scenario('index_snapshot')
    def test_ignore_rules(self): self.assert_scenario('ignore_rules')
    def test_dirty_switch_and_restore(self): self.assert_scenario('dirty_switch')
    def test_stash_conflict_preserves_three_layers(self): self.assert_scenario('stash_conflict')
    def test_worktree_branch_and_index_isolation(self): self.assert_scenario('worktree')
    def test_fetch_and_explicit_ff_only(self): self.assert_scenario('fetch_ff')
    def test_merge_conflict_abort_and_continue(self): self.assert_scenario('merge_conflict')
    def test_rebase_conflict_abort_and_continue(self): self.assert_scenario('rebase_conflict')
    def test_revert_tag_and_failed_commit(self): self.assert_scenario('revert_tag')
    def test_push_history_and_exact_lease(self): self.assert_scenario('push_history')
    def test_submodule_gitlink(self): self.assert_scenario('submodule_pointer')

    def test_semantic_command_mutations_are_detected(self):
        for mutation, (scenario, check_id) in git_scenarios.MUTATIONS.items():
            with self.subTest(mutation=mutation):
                r = git_scenarios.run_scenario(scenario, mutation=mutation)
                self.assertEqual(r['status'], 'failed', r['report_path'])
                self.assertEqual(r['error'], check_id, r['report_path'])
                self.assertTrue(r['sandbox_retained'])
                self.assertTrue((Path(r['evidence_dir']) / 'sandbox').exists())
                self.assertEqual([c['id'] for c in r['assertions'] if not c['matches']], [check_id])
                self.assertTrue(all(c['matches'] for c in r['commands']))

    def test_cleanup_failure_is_recorded_as_failure(self):
        with patch.object(git_scenarios.shutil, 'rmtree', side_effect=PermissionError('synthetic cleanup denial')):
            result = git_scenarios.run_scenario('index_snapshot')
        self.assertEqual(result['status'], 'failed')
        self.assertIn('sandbox cleanup failed', result['error'])
        self.assertTrue(result['sandbox_retained'])
        saved = json.loads(Path(result['report_path']).read_text(encoding='utf-8'))
        self.assertEqual(saved['status'], 'failed')

    def test_invalid_mutation_does_not_create_case(self):
        with self.assertRaises(ValueError):
            git_scenarios.run_scenario('index_snapshot', mutation='skip-conflicting-commit')

    def test_unknown_scenario_is_not_pass(self):
        with self.assertRaises(ValueError):
            git_scenarios.run_scenario('not-a-scenario')

    def test_space_gate_before_case_creation(self):
        with self.assertRaises(RuntimeError):
            git_scenarios.run_scenario('index_snapshot', min_free_bytes=10**30)

    def test_cli_precondition_is_not_run_with_exit_two(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = git_scenarios.main(['--scenario', 'index_snapshot', '--min-free-bytes', str(10**30)])
        self.assertEqual(code, 2)
        result = json.loads(output.getvalue())['results'][0]
        self.assertEqual(result['status'], 'not-run')
        self.assertEqual(result['commands'], [])

    def test_timeout_records_unknown_exit_and_partial_output(self):
        failure = subprocess.TimeoutExpired(['git'], 30, output=b'partial', stderr=b'timeout')
        with patch.object(git_scenarios.subprocess, 'run', side_effect=failure):
            result = git_scenarios.run_scenario('index_snapshot')
        self.assertEqual(result['status'], 'failed')
        self.assertTrue(result['sandbox_retained'])
        command = result['commands'][0]
        self.assertIsNone(command['actual_exit'])
        self.assertEqual(command['outcome'], 'timeout')
        self.assertEqual(command['stdout'], 'partial')
        self.assertFalse(command['matches'])

    def test_launch_failure_is_not_a_successful_git_command(self):
        with patch.object(git_scenarios.subprocess, 'run', side_effect=FileNotFoundError('synthetic missing executable')):
            result = git_scenarios.run_scenario('index_snapshot')
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['commands'][0]['outcome'], 'not-started')
        self.assertIsNone(result['commands'][0]['actual_exit'])

    def test_source_claims_identify_their_publisher_and_supported_scope(self):
        root = MODULE_PATH.parents[2]
        catalog = json.loads((root/'sources/project-governance/git-operations.json').read_text())
        sources = catalog['sources']
        self.assertTrue(sources)
        self.assertEqual(len({row['source_id'] for row in sources}), len(sources))
        for row in sources:
            self.assertTrue(row['url'].startswith('https://'))
            self.assertTrue(row.get('supported_claim') or row.get('supported_claims'))


if __name__ == '__main__':
    unittest.main()
