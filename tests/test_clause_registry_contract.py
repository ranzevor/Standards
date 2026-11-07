"""Complete offline clause records and their Markdown-derived field values."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile

from checks.corpus_contract import extract_document, fields_of
from tests.test_release_bundle import fixture_source, bundle_parts, write_directory
from tools.build_release_bundle import manifest, sha256, verify_normative
from tools.verify_release_bundle import (
    CLAUSE_FIELDS, MANIFEST, VerificationError, _contract_fields, canonical,
    validate_clause_registry, verify_directory, verify_zip,
)

ROOT = Path(__file__).resolve().parents[1]


class ClauseRegistryContractTests(unittest.TestCase):
    @staticmethod
    def with_contract():
        source = fixture_source()
        documents = json.loads(source['registry/standards.json'])
        document = documents[0]
        source[document['path']] += (
            '\n**机制：** 根据输入选择对应行为。\n\n'
            '**验收：** 正例返回有效结果，错误输入被拒绝。\n'
        ).encode('utf-8')
        document['sha256'] = sha256(source[document['path']])
        expected = extract_document(document, source[document['path']].decode('utf-8'))['clauses']
        clauses = json.loads(source['registry/requirements.json'])
        clauses[0] = expected[0]
        source['registry/standards.json'] = canonical(documents)
        source['registry/requirements.json'] = canonical(clauses)
        return source

    def test_record_shape_matches_repository_schema(self):
        schema = json.loads((ROOT / 'registry/schemas/requirements.schema.json').read_text(encoding='utf-8'))
        self.assertEqual(CLAUSE_FIELDS, set(schema['items']['required']))
        self.assertEqual(CLAUSE_FIELDS, set(schema['items']['properties']))
        self.assertFalse(schema['items']['additionalProperties'])

    def test_complete_fixture_and_repository_corpus_are_accepted(self):
        self.assertEqual(verify_normative(fixture_source())['documents'], 162)
        self.assertEqual(verify_normative(self.with_contract())['documents'], 162)
        documents = json.loads((ROOT / 'registry/standards.json').read_text(encoding='utf-8'))
        clauses = json.loads((ROOT / 'registry/requirements.json').read_text(encoding='utf-8'))
        self.assertIs(validate_clause_registry(
            clauses, documents, lambda path: (ROOT / path).read_bytes()), clauses)

    def test_all_missing_and_extra_fields_are_rejected(self):
        source = fixture_source()
        for field in sorted(CLAUSE_FIELDS):
            with self.subTest(missing=field):
                clauses = json.loads(source['registry/requirements.json'])
                del clauses[0][field]
                with self.assertRaisesRegex(VerificationError, 'invalid clause registry fields'):
                    verify_normative({**source, 'registry/requirements.json': canonical(clauses)})
        clauses = json.loads(source['registry/requirements.json'])
        clauses[0]['unexpected'] = '未声明的字段'
        with self.assertRaisesRegex(VerificationError, 'invalid clause registry fields'):
            verify_normative({**source, 'registry/requirements.json': canonical(clauses)})

    def test_wrong_types_and_invalid_enumerations_are_rejected(self):
        mutations = [
            ('fields', []), ('fields', {'机制': []}), ('fields', {'机制': ''}),
            ('acceptance_fields', {}), ('acceptance_fields', [False]),
            ('acceptance_fields', ['']), ('kind', []), ('kind', 'unknown'),
            ('check_scope', None), ('check_scope', 'full-compliance'),
            ('line', True), ('end_line', 6.0), ('title', ''),
            ('document_sha256', 'bad'), ('heading', 7),
        ]
        source = fixture_source()
        for field, value in mutations:
            with self.subTest(field=field, value=value):
                clauses = json.loads(source['registry/requirements.json'])
                clauses[0][field] = value
                with self.assertRaises(VerificationError):
                    verify_normative({**source, 'registry/requirements.json': canonical(clauses)})

    def test_source_derived_fields_and_kind_cannot_be_replaced(self):
        source = self.with_contract()
        for field, value, error in (
            ('fields', {}, 'contract fields mismatch'),
            ('fields', {'机制': '另一种未经正文规定的行为。'}, 'contract fields mismatch'),
            ('acceptance_fields', [], 'acceptance fields mismatch'),
            ('acceptance_fields', ['所有输入均成功。'], 'acceptance fields mismatch'),
            ('kind', 'narrative-section', 'clause kind mismatch'),
        ):
            with self.subTest(field=field, value=value):
                clauses = json.loads(source['registry/requirements.json'])
                clauses[0][field] = value
                with self.assertRaisesRegex(VerificationError, error):
                    verify_normative({**source, 'registry/requirements.json': canonical(clauses)})

    def test_narrative_clause_kind_is_derived_from_real_headings(self):
        source = fixture_source()
        document = json.loads(source['registry/standards.json'])[0]
        text = source[document['path']].decode().replace('## ARC-001 条款', '## 使用条件')
        document['sha256'] = sha256(text.encode())
        clauses = extract_document(document, text)['clauses']
        self.assertEqual(clauses[0]['kind'], 'narrative-section')
        validate_clause_registry(clauses, [document], lambda path: text.encode())
        clauses[0]['kind'] = 'labelled-clause'
        with self.assertRaisesRegex(VerificationError, 'clause kind mismatch'):
            validate_clause_registry(clauses, [document], lambda path: text.encode())

    def test_portable_field_parser_matches_authoring_parser(self):
        examples = [
            '## ARC-01 条款\n\n**机制：** 实际行为。\n\n**验收：** 可复现结果。\n',
            '## ARC-01 条款\n\n`**验收：** 示例文本`\n\n**机制：** 实际行为。\n',
            '## ARC-01 条款\n\n<!-- **验收：** 隐藏文本 -->\n\n**机制：** 实际行为。\n',
            '## ARC-01 条款\n\n~~~md\n**验收：** 示例文本\n~~~\n\n**机制：** 实际行为。\n',
            '## ARC-01 条款\n\n**验收：**\n\n```sh\npython -B verify.py\n```\n',
            '## ARC-01 条款\n\n- **机制：** 实际行为。\n- **验收：** 正确结果。\n',
            '## ARC-01 条款\n\n| 字段 | 内容 |\n| --- | --- |\n| **验收：** 正确结果 | 示例 |\n',
            '## ARC-01 条款\n\n**机制：** Unicode\u2028分隔文本。\n',
            '## ARC-01 条款\n\n**机制：** 文本<!-- 隐藏内容 -->继续。\n',
        ]
        for text in examples:
            with self.subTest(text=text):
                self.assertEqual(_contract_fields(text), fields_of(text))
        for text in ('**验收：** TODO\n', '**验收：** 结果一。\n\n**验收：** 结果二。\n'):
            with self.subTest(invalid=text), self.assertRaises(VerificationError):
                _contract_fields(text)

    def test_self_consistent_tampered_bundles_fail_both_offline_entrypoints(self):
        source = self.with_contract()
        mutations = (
            ('fields', {'机制': '错误的行为。'}),
            ('acceptance_fields', ['错误的验收结果。']),
            ('kind', 'narrative-section'),
            ('check_scope', 'unverified'),
        )
        for kind in ('source', 'agent-skill'):
            valid_records, summary, _ = bundle_parts(source, kind)
            prefix = 'source/' if kind == 'source' else 'references/'
            for field, value in mutations:
                with self.subTest(kind=kind, field=field), tempfile.TemporaryDirectory() as temp:
                    records = dict(valid_records)
                    clauses = json.loads(records[prefix + 'registry/requirements.json'])
                    clauses[0][field] = value
                    records[prefix + 'registry/requirements.json'] = canonical(clauses)
                    changed_summary = {**summary, 'source_tree_sha256': sha256(canonical(sorted(
                        (path, len(records[prefix + path]), sha256(records[prefix + path]))
                        for path in source)))}
                    metadata = json.loads(manifest(kind, records, changed_summary))
                    directory = write_directory(temp, records, metadata)
                    with self.assertRaisesRegex(VerificationError, 'clause'):
                        verify_directory(directory)
                    archive_path = Path(temp) / 'changed.zip'
                    with zipfile.ZipFile(archive_path, 'w') as archive:
                        for path, raw in {**records, MANIFEST: canonical(metadata)}.items():
                            archive.writestr(metadata['root'] + '/' + path, raw)
                    with self.assertRaisesRegex(VerificationError, 'clause'):
                        verify_zip(archive_path)
                    verifier = 'verify.py' if kind == 'source' else 'scripts/verify_bundle.py'
                    lookup = 'source/tools/skill_lookup.py' if kind == 'source' else 'scripts/lookup.py'
                    for command in ([sys.executable, '-B', verifier],
                                    [sys.executable, '-B', lookup, '--document-id', 'STD-L0-001',
                                     '--text-query', 'ABSENT_PHRASE']):
                        result = subprocess.run(command, cwd=directory, capture_output=True, timeout=30)
                        self.assertNotEqual(result.returncode, 0, result.stdout.decode('utf-8'))
                        self.assertIn('clause', result.stderr.decode('utf-8'))
            with self.subTest(kind=kind, legal=True), tempfile.TemporaryDirectory() as temp:
                metadata = json.loads(manifest(kind, valid_records, summary))
                directory = write_directory(temp, valid_records, metadata)
                verify_directory(directory)
                lookup = 'source/tools/skill_lookup.py' if kind == 'source' else 'scripts/lookup.py'
                for phrase, expected in (('完整要求', 1), ('ABSENT_PHRASE', 0)):
                    result = subprocess.run([sys.executable, '-B', lookup, '--document-id',
                                             'STD-L0-001', '--text-query', phrase],
                                            cwd=directory, capture_output=True, timeout=30)
                    self.assertEqual(result.returncode, 0, result.stderr.decode('utf-8'))
                    self.assertEqual(json.loads(result.stdout)['total'], expected)


if __name__ == '__main__':
    unittest.main()
