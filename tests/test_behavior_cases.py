"""Finite corpus contract regressions; these do not execute a language model."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from checks.behavior_cases import bind_normative_references, load_suites, read_json, relative_path, validate_suite

ROOT = Path(__file__).resolve().parents[1]


class BehaviorCaseContracts(unittest.TestCase):
    def setUp(self):
        self.suite = read_json(ROOT / 'examples/ai-agent/behavior/cases/expression.json')

    def test_current_corpus_has_unique_cases(self):
        suites = load_suites(ROOT)
        self.assertGreaterEqual(sum(len(row['cases']) for _, row in suites), 6)

    def test_failure_and_neighbor_are_required(self):
        for role in ('failure', 'neighbor'):
            broken = copy.deepcopy(self.suite)
            del broken['cases'][0]['examples'][role]
            with self.assertRaises(ValueError):
                validate_suite(broken)

    def test_an_unknown_check_cannot_silently_pass(self):
        broken = copy.deepcopy(self.suite)
        broken['cases'][0]['checks'][0]['kind'] = 'model_says_pass'
        with self.assertRaises(ValueError):
            validate_suite(broken)

    def test_duplicate_case_or_rubric_is_rejected(self):
        broken = copy.deepcopy(self.suite)
        broken['cases'].append(copy.deepcopy(broken['cases'][0]))
        with self.assertRaises(ValueError):
            validate_suite(broken)
        broken = copy.deepcopy(self.suite)
        broken['cases'][0]['rubric'].append(copy.deepcopy(broken['cases'][0]['rubric'][0]))
        with self.assertRaises(ValueError):
            validate_suite(broken)

    def test_case_authorization_cannot_be_unbounded(self):
        broken = copy.deepcopy(self.suite)
        broken['cases'][0]['authorization']['forbidden'] = []
        with self.assertRaises(ValueError):
            validate_suite(broken)

    def test_case_origin_does_not_claim_actual_model_run(self):
        broken = copy.deepcopy(self.suite)
        broken['origin'] = 'verified-model-run'
        with self.assertRaises(ValueError):
            validate_suite(broken)

    def test_paths_reject_escape_and_nonportable_forms(self):
        for value in ('../outside', '/absolute', 'C:/outside', 'a\\b', 'a/../b', './a', 'a//b'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                relative_path(value)
        self.assertEqual(relative_path('资料/结果.json'), '资料/结果.json')

    def test_json_duplicate_keys_and_nonfinite_values_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.json'
            for text in ('{"a":1,"a":2}', '{"x":NaN}', '{"x":Infinity}', '{"x":1e309}', '{"x":1e-999}'):
                path.write_text(text, encoding='utf-8')
                with self.assertRaises(ValueError):
                    read_json(path)

    def test_semantic_rubric_is_not_replaced_by_keyword_checks(self):
        broken = copy.deepcopy(self.suite)
        broken['cases'][0]['rubric'] = []
        with self.assertRaises(ValueError):
            validate_suite(broken)

    def test_legitimate_alternative_wording_is_data_not_exact_match(self):
        changed = copy.deepcopy(self.suite)
        changed['cases'][0]['examples']['positive'] = '另一种事实相同的自然表达。'
        self.assertEqual(validate_suite(changed), 6)

    def reference_fixture(self, directory):
        root = Path(directory)
        identities = {row['document_id'] for row in self.suite['normative_refs']}
        entries = [row for row in read_json(ROOT / 'registry/standards.json') if row['id'] in identities]
        rows = [row for row in read_json(ROOT / 'registry/requirements.json') if row['document_id'] in identities]
        for entry in entries:
            target = root / entry['path']
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / entry['path'], target)
        (root / 'registry').mkdir()
        (root / 'registry/standards.json').write_text(json.dumps(entries), encoding='utf-8')
        (root / 'registry/requirements.json').write_text(json.dumps(rows), encoding='utf-8')
        return root, rows

    def test_each_clause_identity_mutation_is_rejected(self):
        mutations = {'path': 'standards/missing.md', 'version': '9.9.9',
                     'document_sha256': '0' * 64, 'section_sha256': '0' * 64,
                     'normative_sha256': '0' * 64}
        for field, replacement in mutations.items():
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                root, rows = self.reference_fixture(directory)
                selected = next(row for row in rows if row['document_id'] == 'STD-L2-001' and
                                row['clause_id'] == 'ORG-03')
                selected[field] = replacement
                (root / 'registry/requirements.json').write_text(json.dumps(rows), encoding='utf-8')
                with self.assertRaises(ValueError):
                    bind_normative_references(root, [(None, self.suite)])

    def test_accurate_clause_index_with_reordered_keys_remains_usable(self):
        with tempfile.TemporaryDirectory() as directory:
            root, rows = self.reference_fixture(directory)
            rows = [{key: row[key] for key in reversed(row)} for row in reversed(rows)]
            (root / 'registry/requirements.json').write_text(json.dumps(rows), encoding='utf-8')
            result = bind_normative_references(root, [(None, self.suite)])
            self.assertEqual({row['id'] for row in result}, {'STD-L2-001', 'STD-PG-004'})
            self.assertTrue(all(row['clauses'] for row in result))


if __name__ == '__main__':
    unittest.main()
