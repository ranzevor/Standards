"""Agent Skill entrypoint and verified offline clause consumption."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest

from tests.test_release_bundle import fixture_source
from tools.skill_lookup import find
from tools.verify_release_bundle import VerificationError, canonical

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
    def refresh_fixture_source(source):
        documents = json.loads(source['registry/standards.json'])
        clauses = json.loads(source['registry/requirements.json'])
        by_id = {document['id']: document for document in documents}
        for document in documents:
            raw = source[document['path']]
            document['sha256'] = hashlib.sha256(raw).hexdigest()
        for row in clauses:
            document = by_id[row['document_id']]
            row['document_sha256'] = document['sha256']
            physical_lines = source[document['path']].splitlines(keepends=True)
            section = b''.join(physical_lines[row['line'] - 1:row['end_line']])
            row['section_sha256'] = hashlib.sha256(section).hexdigest()
            normative = b''.join(physical_lines[row['normative_start_line'] - 1:
                                                row['normative_end_line']])
            row['normative_sha256'] = hashlib.sha256(normative).hexdigest()
        source['registry/standards.json'] = canonical(documents)
        source['registry/requirements.json'] = canonical(clauses)
        return source

    @staticmethod
    def write_fixture(directory, source=None):
        for name, content in (source or fixture_source()).items():
            path = directory / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)

    def test_exact_text_returns_clause_and_original_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_fixture(root)
            result = find(root, text_query='完整要求', document_id='STD-L0-001')
            self.assertEqual(result['version'], '0.1.0')
            self.assertEqual(result['total'], 1)
            hit = result['results'][0]
            self.assertEqual(hit['clause_id'], 'ARC-001')
            self.assertEqual(hit['line'], 5)
            self.assertEqual(hit['matched_line'], 6)
            self.assertIn('完整要求', hit['matched_excerpt'])
            clause = json.loads((root / 'registry/requirements.json').read_text(encoding='utf-8'))[0]
            self.assertEqual(hit['section_sha256'], clause['section_sha256'])
            self.assertEqual(hit['sha256'], clause['document_sha256'])

    def test_no_match_is_empty_and_metadata_query_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_fixture(root)
            self.assertEqual(find(root, text_query='不存在的唯一词组')['total'], 0)
            self.assertEqual(find(root, query='STD-L0-001')['total'], 1)
            self.assertEqual(find(root, document_id='STD-L0-001', clause_id='ARC-001')['total'], 1)
            self.assertEqual(find(root, document_id='STD-L0-001', text_query='完整要求',
                                  clause_id='ARC-999')['total'], 0)

    def test_missing_clause_row_is_an_integrity_error_not_an_empty_result(self):
        source=fixture_source()
        rows=json.loads(source['registry/requirements.json'])
        rows=[row for row in rows if row['document_id']!='STD-L0-002']
        source['registry/requirements.json']=canonical(rows)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            self.write_fixture(root,source)
            for options in ({'document_id':'STD-L0-002','clause_id':'ARC-002'},
                            {'document_id':'STD-L0-002','text_query':'完整要求'},
                            {'document_id':'STD-L0-002','text_query':'ABSENT_PHRASE_123456'}):
                with self.subTest(options=options),self.assertRaisesRegex(
                        VerificationError,'clause registry coverage mismatch'):
                    find(root,**options)
            self.assertEqual(find(root,document_id='STD-L0-001',
                                  clause_id='ARC-001')['total'],1)

    def test_unindexed_second_real_clause_in_existing_document_is_rejected(self):
        source=fixture_source()
        document='standards/L0/001-测试规范--v0.1.0.md'
        source[document]+='## ARC-999 第二条款\nSECOND_UNINDEXED_BODY\n'.encode('utf-8')
        self.refresh_fixture_source(source)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            self.write_fixture(root,source)
            with self.assertRaisesRegex(VerificationError,'clause registry coverage mismatch'):
                find(root,document_id='STD-L0-001',clause_id='ARC-001')

    def test_extra_clause_index_record_is_rejected(self):
        source=fixture_source()
        rows=json.loads(source['registry/requirements.json'])
        extra=dict(rows[0])
        extra.update(id='STD-L0-001::ARC-999',clause_id='ARC-999')
        rows.append(extra)
        source['registry/requirements.json']=canonical(rows)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            self.write_fixture(root,source)
            with self.assertRaisesRegex(VerificationError,'clause heading identity mismatch'):
                find(root,document_id='STD-L0-001',clause_id='ARC-001')

    def test_forged_clause_id_is_rejected_even_when_index_composite_id_is_rewritten(self):
        source = fixture_source()
        clauses = json.loads(source['registry/requirements.json'])
        clauses[0]['clause_id'] = 'NOT-A-REAL-CLAUSE'
        clauses[0]['id'] = clauses[0]['document_id'] + '::NOT-A-REAL-CLAUSE'
        source['registry/requirements.json'] = canonical(clauses)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_fixture(root, source)
            with self.assertRaisesRegex(ValueError, 'clause heading identity mismatch'):
                find(root, document_id='STD-L0-001', text_query='完整要求')

    def test_duplicate_clause_identity_is_rejected(self):
        source = fixture_source()
        clauses = json.loads(source['registry/requirements.json'])
        clauses.append(dict(clauses[0]))
        source['registry/requirements.json'] = canonical(clauses)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_fixture(root, source)
            with self.assertRaisesRegex(ValueError, 'duplicate clause registry identity'):
                find(root, document_id='STD-L0-001', text_query='完整要求')

    def test_clause_span_cannot_be_repointed_to_a_different_source_line(self):
        source = fixture_source()
        clauses = json.loads(source['registry/requirements.json'])
        row = clauses[0]
        physical_lines = source[row['path']].splitlines(keepends=True)
        row['line'] = 6
        row['end_line'] = 6
        row['section_sha256'] = hashlib.sha256(physical_lines[5]).hexdigest()
        source['registry/requirements.json'] = canonical(clauses)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_fixture(root, source)
            with self.assertRaisesRegex(ValueError, 'clause heading location mismatch'):
                find(root, document_id='STD-L0-001', text_query='完整要求')


    def test_normative_chapter_and_contract_are_verified_and_searched_separately(self):
        source = fixture_source()
        path = 'standards/L0/001-测试规范--v0.1.0.md'
        lines = source[path].splitlines(keepends=True)
        lines[4:] = [
            '## 测试章节\n'.encode('utf-8'),
            '章节正文独有短语。\n'.encode('utf-8'),
            '### ARC-001 核验合同\n'.encode('utf-8'),
            '完整要求。\n'.encode('utf-8'),
        ]
        source[path] = b''.join(lines)
        clauses = json.loads(source['registry/requirements.json'])
        row = clauses[0]
        row.update(line=7, end_line=8, heading='ARC-001 核验合同',
                   title='核验合同', normative_start_line=5, normative_end_line=8)
        source['registry/requirements.json'] = canonical(clauses)
        self.refresh_fixture_source(source)
        registered = json.loads(source['registry/requirements.json'])[0]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_fixture(root, source)
            chapter = find(root, document_id='STD-L0-001',
                           text_query='章节正文独有短语')['results'][0]
            self.assertEqual(chapter['clause_id'], 'ARC-001')
            self.assertEqual((chapter['line'], chapter['end_line']), (7, 8))
            self.assertEqual((chapter['normative_start_line'], chapter['normative_end_line']), (5, 8))
            self.assertEqual(chapter['matched_line'], 6)
            self.assertIn('章节正文独有短语', chapter['matched_excerpt'])
            self.assertEqual(chapter['normative_sha256'], registered['normative_sha256'])
            contract = find(root, document_id='STD-L0-001',
                            text_query='完整要求')['results'][0]
            self.assertEqual(contract['matched_line'], 8)
            self.assertEqual(contract['section_sha256'], registered['section_sha256'])
            self.assertIn('完整要求', contract['matched_excerpt'])

            corrupted = json.loads(source['registry/requirements.json'])
            corrupted[0]['normative_sha256'] = '0' * 64
            (root / 'registry/requirements.json').write_bytes(canonical(corrupted))
            with self.assertRaisesRegex(ValueError, 'normative clause digest mismatch'):
                find(root, document_id='STD-L0-001', text_query='完整要求')

    def test_real_normative_chapter_text_is_searchable_by_clauses(self):
        hit = find(ROOT, document_id='STD-L0-001', clause_id='ARC-01',
                   text_query='L1至L6为六层实施与治理结构')['results'][0]
        self.assertEqual((hit['normative_start_line'], hit['line'],
                          hit['matched_line'], hit['normative_end_line']), (7, 13, 9, 25))
        self.assertIn('L1至L6为六层实施与治理结构', hit['matched_excerpt'])

    def test_fenced_heading_cannot_impersonate_a_real_clause(self):
        for fence in ('~~~', chr(96) * 3):
            with self.subTest(fence=fence):
                source = fixture_source()
                path = 'standards/L0/001-测试规范--v0.1.0.md'
                source[path] += (f'## 示例资料\n{fence}md\n## ARC-001 条款\n'
                                 f'FAKE_SECRET_IN_FENCE\n{fence}\n').encode('utf-8')
                self.refresh_fixture_source(source)
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    self.write_fixture(root, source)
                    genuine = find(root, document_id='STD-L0-001', text_query='完整要求')
                    self.assertEqual(genuine['total'], 1)
                    self.assertEqual(genuine['results'][0]['line'], 5)
                    self.assertEqual(find(root, document_id='STD-L0-001',
                                          text_query='FAKE_SECRET_IN_FENCE')['total'], 0)

                forged = json.loads(source['registry/requirements.json'])
                forged[0].update(line=9, end_line=10,
                                 normative_start_line=9, normative_end_line=10)
                source['registry/requirements.json'] = canonical(forged)
                self.refresh_fixture_source(source)
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    self.write_fixture(root, source)
                    with self.assertRaisesRegex(ValueError, 'clause heading location mismatch'):
                        find(root, document_id='STD-L0-001', clause_id='ARC-001',
                             text_query='FAKE_SECRET_IN_FENCE')


    def test_duplicate_real_heading_is_rejected_even_if_index_and_digests_agree(self):
        source = fixture_source()
        path = 'standards/L0/001-测试规范--v0.1.0.md'
        source[path] += '## ARC-001 条款\nFORGED_DUPLICATE_BODY\n'.encode('utf-8')
        clauses = json.loads(source['registry/requirements.json'])
        clauses[0].update(line=7, end_line=8, normative_start_line=7, normative_end_line=8)
        source['registry/requirements.json'] = canonical(clauses)
        self.refresh_fixture_source(source)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_fixture(root, source)
            with self.assertRaisesRegex(ValueError, 'duplicate parsed clause identity'):
                find(root, document_id='STD-L0-001', clause_id='ARC-001',
                     text_query='FORGED_DUPLICATE_BODY')

    def test_index_cannot_extend_clause_into_next_real_heading(self):
        source = fixture_source()
        path = 'standards/L0/001-测试规范--v0.1.0.md'
        source[path] += '## ARC-002 其他条款\nSECOND_CLAUSE_ONLY\n'.encode('utf-8')
        clauses = json.loads(source['registry/requirements.json'])
        clauses[0].update(end_line=8, normative_end_line=8)
        source['registry/requirements.json'] = canonical(clauses)
        self.refresh_fixture_source(source)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_fixture(root, source)
            with self.assertRaisesRegex(ValueError, 'clause span boundary mismatch'):
                find(root, document_id='STD-L0-001', clause_id='ARC-001',
                     text_query='SECOND_CLAUSE_ONLY')

    def test_adjacent_real_clauses_keep_their_independent_boundaries(self):
        source = fixture_source()
        path = 'standards/L0/001-测试规范--v0.1.0.md'
        source[path] += '## ARC-002 其他条款\nSECOND_CLAUSE_ONLY\n'.encode('utf-8')
        clauses = json.loads(source['registry/requirements.json'])
        adjacent = dict(clauses[0])
        adjacent.update(id='STD-L0-001::ARC-002', clause_id='ARC-002',
                        heading='ARC-002 其他条款', title='其他条款',
                        line=7, end_line=8, normative_start_line=7, normative_end_line=8)
        clauses.append(adjacent)
        source['registry/requirements.json'] = canonical(clauses)
        self.refresh_fixture_source(source)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_fixture(root, source)
            first = find(root, document_id='STD-L0-001', clause_id='ARC-001',
                         text_query='完整要求')
            self.assertEqual((first['total'], first['results'][0]['end_line']), (1, 6))
            self.assertEqual(find(root, document_id='STD-L0-001', clause_id='ARC-001',
                                  text_query='SECOND_CLAUSE_ONLY')['total'], 0)
            second = find(root, document_id='STD-L0-001', clause_id='ARC-002',
                          text_query='SECOND_CLAUSE_ONLY')
            self.assertEqual(second['total'], 1)
            self.assertEqual((second['results'][0]['line'], second['results'][0]['matched_line']),
                             (7, 8))

    def test_long_line_excerpt_is_centered_on_match_and_contains_search_text(self):
        source = fixture_source()
        document_path = 'standards/L0/001-测试规范--v0.1.0.md'
        physical_lines = source[document_path].splitlines(keepends=True)
        long_line = '前缀' * 150 + '中段' * 20 + 'y-containers/ver'
        physical_lines[5] = (long_line + '\n').encode('utf-8')
        source[document_path] = b''.join(physical_lines)
        self.refresh_fixture_source(source)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_fixture(root, source)
            hit = find(root, document_id='STD-L0-001', text_query='y-containers/ver')['results'][0]
            self.assertEqual(hit['matched_line'], 6)
            self.assertIn('y-containers/ver', hit['matched_excerpt'].casefold())
            self.assertLessEqual(len(hit['matched_excerpt']), 242)
            self.assertTrue(hit['matched_excerpt'].endswith('y-containers/ver'))

    def test_reported_real_long_line_excerpt_contains_late_match(self):
        hit = find(ROOT, document_id='STD-L4-CLOUD-002', clause_id='§06',
                   text_query='y-containers/ver')['results'][0]
        self.assertEqual(hit['matched_line'], 194)
        self.assertIn('y-containers/ver', hit['matched_excerpt'].casefold())

    def test_unicode_casefold_expansion_maps_back_to_original_excerpt(self):
        source = fixture_source()
        document_path = 'standards/L0/001-测试规范--v0.1.0.md'
        physical_lines = source[document_path].splitlines(keepends=True)
        physical_lines[5] = ('前缀' * 130 + 'Straße' + '尾部' * 60 + '\n').encode('utf-8')
        source[document_path] = b''.join(physical_lines)
        self.refresh_fixture_source(source)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_fixture(root, source)
            hit = find(root, document_id='STD-L0-001', text_query='STRASSE')['results'][0]
            self.assertEqual(hit['matched_line'], 6)
            self.assertIn('strasse', hit['matched_excerpt'].casefold())

    def test_unicode_line_separators_do_not_change_physical_line_numbers(self):
        source = fixture_source()
        document_path = 'standards/L0/001-测试规范--v0.1.0.md'
        physical_lines = source[document_path].splitlines(keepends=True)
        physical_lines[5] = '前半段\u2028中间段\u0085后半段\n'.encode('utf-8')
        source[document_path] = b''.join(physical_lines)
        self.refresh_fixture_source(source)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_fixture(root, source)
            for phrase in ('中间段', '后半段'):
                with self.subTest(phrase=phrase):
                    hit = find(root, document_id='STD-L0-001', text_query=phrase)['results'][0]
                    self.assertEqual((hit['line'], hit['end_line'], hit['matched_line']), (5, 6, 6))
                    self.assertIn(phrase, hit['matched_excerpt'])

    def test_corrupted_source_and_clause_hash_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_fixture(root)
            clause_path = root / 'registry/requirements.json'
            clauses = json.loads(clause_path.read_text(encoding='utf-8'))
            clauses[0]['section_sha256'] = '0' * 64
            clause_path.write_text(json.dumps(clauses, ensure_ascii=False), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'clause content digest mismatch'):
                find(root, text_query='完整要求')
            source = fixture_source()
            self.write_fixture(root, source)
            doc_path = next((root / 'standards').rglob('001-测试规范--v0.1.0.md'))
            doc_path.write_bytes(doc_path.read_bytes() + b'\n')
            with self.assertRaises(VerificationError):
                find(root, text_query='完整要求')

    def test_reject_blank_overlong_or_ambiguous_text_query(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_fixture(root)
            for phrase in ('', '   ', '\x00', 'x' * 257):
                with self.subTest(phrase=repr(phrase)), self.assertRaisesRegex(ValueError, 'text-query'):
                    find(root, text_query=phrase)

    def test_cli_from_another_directory_emits_utf8_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / '中文 源目录'
            root.mkdir()
            self.write_fixture(root)
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
