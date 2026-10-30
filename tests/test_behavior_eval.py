"""Scorer regressions using synthetic inputs; these do not execute a model."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from tests.platform_support import make_symlink

from checks.behavior_cases import digest, load_suites, read_json
from checks.corpus_contract import extract_document

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('standards_behavior_eval', ROOT / 'tools/behavior_eval.py')
evaluation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evaluation)


class BehaviorEvaluation(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'source'
        sources = ['tools/behavior_eval.py', 'checks/behavior_cases.py',
                   'checks/corpus_contract.py', 'checks/validation_common.py']
        sources.extend(path.relative_to(ROOT).as_posix() for path in
                       (ROOT / 'examples/ai-agent/behavior/cases').glob('*.json'))
        for path in sources:
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, target)
        (self.root / 'project.json').write_text('{"version":"0.1.8"}\n', encoding='utf-8')
        references = {}
        for _, suite in load_suites(self.root):
            for ref in suite['normative_refs']:
                references.setdefault(ref['document_id'], set()).update(ref['clause_ids'])
        entries, clauses = [], []
        for index, (identity, clause_ids) in enumerate(sorted(references.items())):
            path = 'standards/example-' + str(index) + '.md'
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            text = '# Synthetic scorer source\n\n' + ''.join(
                '## ' + clause + ' Synthetic clause ' + clause + '\n\nFinite source text for unit tests only.\n\n'
                for clause in sorted(clause_ids))
            target.write_text(text, encoding='utf-8', newline='\n')
            entry = {'id': identity, 'version': '0.1.0', 'domain': 'synthetic', 'path': path,
                     'sha256': digest(target.read_bytes())}
            entries.append(entry)
            clauses.extend(extract_document(entry, text)['clauses'])
        (self.root / 'registry').mkdir()
        (self.root / 'registry/standards.json').write_text(json.dumps(entries), encoding='utf-8')
        (self.root / 'registry/requirements.json').write_text(json.dumps(clauses), encoding='utf-8')
        self.config = {'schema': 'standards-behavior-execution/1',
                       'model': {'requested_id': 'test-fixture', 'observed_id': None,
                                 'identity_source': 'unit-test fixture', 'immutable': False},
                       'host': {'name': 'unit-test', 'version': '1'}, 'executor_id': 'fixture-author',
                       'project_instructions': 'Synthetic test instructions.', 'tool_configuration': {},
                       'parameters': {}, 'identity_limitations': 'No model was invoked.'}
        self.directory = self.base / 'trials'
        prepared = evaluation.prepare(self.root, self.directory, self.config, ['DECL-001'], 2)
        self.batch_sha256 = prepared['batch_sha256']
        self.run = self.directory / 'DECL-001/1'

    def capture(self, output='现在可以离线检索。也可批量导出。\n', origin='operator-captured-agent',
                status='completed', exit_code=0):
        if output is not None:
            (self.run / 'workspace/result.md').write_text(output, encoding='utf-8')
        response = self.base / 'response.txt'
        trace = self.base / 'trace.txt'
        response.write_text('Success was claimed by this synthetic test.\n', encoding='utf-8')
        trace.write_text('Synthetic execution trace for the scorer test.\n', encoding='utf-8')
        evaluation.capture(self.root, self.run, response, trace, origin, status, exit_code)

    def review(self):
        review = evaluation.review_template(self.run)
        review['reviewer_id'] = 'fixture-reviewer'
        review['independence_reason'] = 'Separate synthetic reviewer fixture; not a real review.'
        for row in [review['provenance'], *review['rubric']]:
            row['judgment'] = 'pass'
            row['reason'] = 'Finite fixture verdict for unit-test coverage.'
            row['evidence'] = [{'path': 'trace.txt', 'start_line': 1, 'end_line': 1}]
        path = self.run / 'review.json'
        path.write_text(json.dumps(review), encoding='utf-8')
        return path

    def test_no_observation_is_not_run(self):
        result = evaluation.evaluate(self.root, self.run)
        self.assertEqual((result['result'], result['execution']), ('INSUFFICIENT', 'not-run'))

    def test_success_text_does_not_replace_required_file(self):
        self.capture(output=None)
        self.assertEqual(evaluation.evaluate(self.root, self.run)['result'], 'FAIL')

    def test_artifact_success_without_semantic_review_is_insufficient(self):
        self.capture()
        self.assertEqual(evaluation.evaluate(self.root, self.run)['result'], 'INSUFFICIENT')

    def test_frozen_observation_and_complete_review_can_pass(self):
        self.capture()
        self.assertEqual(evaluation.evaluate(self.root, self.run, self.review())['result'], 'PASS')

    def test_synthetic_fixture_never_counts_as_model_success(self):
        self.capture(origin='synthetic-fixture')
        result = evaluation.evaluate(self.root, self.run, self.review())
        self.assertEqual(result['result'], 'INSUFFICIENT')
        self.assertEqual(result['fixture_result'], 'PASS')

    def test_failed_synthetic_fixture_is_not_reported_as_model_failure(self):
        self.capture(output=None, origin='synthetic-fixture')
        result = evaluation.evaluate(self.root, self.run)
        self.assertEqual((result['result'], result['fixture_result']), ('INSUFFICIENT', 'FAIL'))

    def test_changed_artifact_rejects_old_capture_and_review(self):
        self.capture()
        review = self.review()
        (self.run / 'workspace/result.md').write_text('Changed after review.\n', encoding='utf-8')
        with self.assertRaises(ValueError):
            evaluation.evaluate(self.root, self.run, review)

    def test_changed_trace_rejects_previous_review(self):
        self.capture()
        review = self.review()
        (self.run / 'trace.txt').write_text('Rewritten history.\n', encoding='utf-8')
        with self.assertRaises(ValueError):
            evaluation.evaluate(self.root, self.run, review)

    def test_unplanned_files_are_part_of_the_captured_observation(self):
        extra = self.run / 'workspace/unplanned.txt'
        extra.write_text('unexpected side effect\n', encoding='utf-8')
        self.capture()
        observation = read_json(self.run / 'observation.json')
        self.assertIn('unplanned.txt', observation['artifacts'])
        extra.write_text('changed later\n', encoding='utf-8')
        with self.assertRaises(ValueError):
            evaluation.evaluate(self.root, self.run)

    def test_case_and_grader_drift_are_rejected(self):
        self.capture()
        path = self.root / 'tools/behavior_eval.py'
        path.write_bytes(path.read_bytes() + b'\n# changed\n')
        with self.assertRaises(ValueError):
            evaluation.evaluate(self.root, self.run)

    def test_prepare_requires_the_actual_running_grader(self):
        path = self.root / 'tools/behavior_eval.py'
        path.write_bytes(path.read_bytes() + b'\n# another implementation\n')
        with self.assertRaises(ValueError):
            evaluation.prepare(self.root, self.base / 'another-run', self.config, ['DECL-001'])

    def test_review_cannot_be_self_attested(self):
        self.capture()
        path = self.review()
        review = read_json(path)
        review['reviewer_id'] = self.config['executor_id']
        path.write_text(json.dumps(review), encoding='utf-8')
        with self.assertRaises(ValueError):
            evaluation.evaluate(self.root, self.run, path)

    def test_review_must_have_valid_evidence_ranges(self):
        self.capture()
        path = self.review()
        review = read_json(path)
        review['rubric'][0]['evidence'][0]['end_line'] = 999
        path.write_text(json.dumps(review), encoding='utf-8')
        with self.assertRaises(ValueError):
            evaluation.evaluate(self.root, self.run, path)

    def test_review_failure_is_not_averaged_away(self):
        self.capture()
        path = self.review()
        review = read_json(path)
        review['rubric'][0]['judgment'] = 'fail'
        path.write_text(json.dumps(review), encoding='utf-8')
        self.assertEqual(evaluation.evaluate(self.root, self.run, path)['result'], 'FAIL')

    def test_known_scope_failure_survives_timeout_and_error(self):
        for status, exit_code in (('timeout', 124), ('error', 1), ('completed', 1)):
            with self.subTest(status=status):
                directory = self.base / ('interrupted-' + status)
                prepared = evaluation.prepare(self.root, directory, self.config, ['DECL-001'])
                self.run = directory / 'DECL-001/1'
                self.capture(status=status, exit_code=exit_code)
                path = self.review()
                review = read_json(path)
                next(row for row in review['rubric'] if row['id'] == 'scope-and-evidence')['judgment'] = 'fail'
                path.write_text(json.dumps(review), encoding='utf-8')
                self.assertEqual(evaluation.evaluate(self.root, self.run, path)['result'], 'FAIL')
                report = evaluation.aggregate(self.root, directory, prepared['batch_sha256'])
                self.assertEqual(report['counts'], {'PASS': 0, 'FAIL': 1, 'INSUFFICIENT': 0})

    def test_interrupted_run_without_known_failure_remains_insufficient(self):
        self.capture(status='timeout', exit_code=124)
        self.assertEqual(evaluation.evaluate(self.root, self.run, self.review())['result'], 'INSUFFICIENT')

    def test_boolean_to_number_contract_substitution_is_rejected_by_single_trial(self):
        directory = self.base / 'typed-contract'
        evaluation.prepare(self.root, directory, self.config, ['ART-003'])
        run = directory / 'ART-003/1'
        path = run / 'plan.json'
        plan = read_json(path)
        plan['case']['checks'][0]['expected']['enabled'] = 1
        path.write_text(json.dumps(plan), encoding='utf-8')
        with self.assertRaises(ValueError):
            evaluation.evaluate(self.root, run)

    def test_case_object_key_order_does_not_change_the_contract(self):
        path = self.run / 'plan.json'
        plan = read_json(path)
        plan['case'] = {key: plan['case'][key] for key in reversed(plan['case'])}
        path.write_text(json.dumps(plan), encoding='utf-8')
        result = evaluation.evaluate(self.root, self.run)
        self.assertEqual((result['result'], result['execution']), ('INSUFFICIENT', 'not-run'))

    def test_natural_wording_neighbors_pass_file_gates_but_missing_artifacts_fail(self):
        cases = {case['id']: case for _, suite in load_suites(self.root) for case in suite['cases']}
        for identity, name, text in (
            ('DECL-001', 'result.md', '现在可在断网时检索项目资料。选中多份结果后，可一次保存为文件。\n'),
            ('DECL-002', 'result.md', 'Win 11 已通过测试；Linux 尚待验证。\n'),
            ('AUTO-004', 'draft.md', '维护窗口通知：上海时区，周三晚十点至十一点。\n'),
            ('ART-002', 'index.html', '<html><p>搜索本机笔记，并导出所选结果。所有资料均保存在本机。</p></html>\n'),
            ('ART-005', 'result.md', '十二个样本中，八个任务的耗时减少。未测其他任务类型，结论不能推广至所有用户。\n'),
        ):
            with self.subTest(case=identity):
                run = self.base / ('wording-' + identity)
                (run / 'workspace').mkdir(parents=True)
                path = run / 'workspace' / name
                path.write_text(text, encoding='utf-8')
                self.assertTrue(all(evaluation.artifact_check(run, check)['result'] == 'PASS'
                                    for check in cases[identity]['checks']))
                path.unlink()
                self.assertTrue(any(evaluation.artifact_check(run, check)['result'] == 'FAIL'
                                    for check in cases[identity]['checks']))

    def test_all_planned_trials_remain_in_denominator(self):
        self.capture()
        self.review()
        result = evaluation.aggregate(self.root, self.directory, self.batch_sha256)
        self.assertEqual(result['planned'], 2)
        self.assertEqual(result['success_fraction'], .5)
        self.assertEqual(result['counts'], {'PASS': 1, 'FAIL': 0, 'INSUFFICIENT': 1})
        self.assertEqual(result['result'], 'INSUFFICIENT')

    def test_dropping_an_unrun_trial_cannot_shrink_frozen_denominator(self):
        self.capture()
        self.review()
        path = self.directory / 'batch.json'
        batch = read_json(path)
        batch['planned'] = batch['planned'][:1]
        path.write_text(json.dumps(batch), encoding='utf-8')
        with self.assertRaises(ValueError):
            evaluation.aggregate(self.root, self.directory, self.batch_sha256)

    def test_comparison_requires_same_cases_and_trial_counts(self):
        candidate = self.base / 'candidate'
        result = evaluation.prepare(self.root, candidate, self.config, ['DECL-002'], 2)
        with self.assertRaises(ValueError):
            evaluation.compare(self.root, self.directory, candidate, self.batch_sha256, result['batch_sha256'])

    def test_incomplete_comparison_makes_no_improvement_claim(self):
        candidate = self.base / 'candidate'
        result = evaluation.prepare(self.root, candidate, self.config, ['DECL-001'], 2)
        comparison = evaluation.compare(self.root, self.directory, candidate, self.batch_sha256, result['batch_sha256'])
        self.assertEqual(comparison['status'], 'INCOMPLETE')
        self.assertEqual(comparison['success_fraction_delta'], 0.0)

    def test_existing_run_and_capture_are_not_overwritten(self):
        with self.assertRaises(ValueError):
            evaluation.prepare(self.root, self.directory, self.config, ['DECL-001'])
        self.capture()
        with self.assertRaises(ValueError):
            self.capture()

    def test_file_symlink_is_rejected(self):
        outside = self.base / 'outside.txt'
        outside.write_text('outside', encoding='utf-8')
        make_symlink(self.run / 'workspace/result.md', outside)
        with self.assertRaises(ValueError):
            self.capture(output=None)

    def test_boolean_is_not_equal_to_number(self):
        self.assertFalse(evaluation.equal_json({'enabled': 1}, {'enabled': True}))
        self.assertTrue(evaluation.equal_json({'b': 2, 'a': 1}, {'a': 1.0, 'b': 2}))


if __name__ == '__main__':
    unittest.main()
