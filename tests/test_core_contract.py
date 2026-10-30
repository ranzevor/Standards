"""Direct failures and lawful neighbors for the published normative index."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from checks.core_contract import validate_clause_index, validate
from checks.validation_common import read_json, ValidationError
from checks.validate_product import validate_links

ROOT = Path(__file__).resolve().parents[1]


class PublishedCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry=read_json(ROOT/'registry/standards.json')
        cls.requirements=read_json(ROOT/'registry/requirements.json')
        cls.full_result=validate(ROOT)

    def make_fixture(self):
        temp=tempfile.TemporaryDirectory()
        root=Path(temp.name)
        doc=self.registry[0]
        src=ROOT/doc['path']
        dest=root/doc['path']
        dest.parent.mkdir(parents=True)
        dest.write_bytes(src.read_bytes())
        rows=[copy.deepcopy(r) for r in self.requirements if r['document_id']==doc['id']]
        (root/'registry').mkdir()
        (root/'registry/requirements.json').write_text(json.dumps(rows,ensure_ascii=False),encoding='utf-8')
        return temp,root,doc,rows

    def test_published_corpus_passes(self):
        result=self.full_result
        self.assertEqual(result['result'],'pass')
        self.assertEqual(result['documents'],162)
        self.assertEqual(result['clauses']['labelled_clauses'],3473)

    def test_baseline_clause_identity(self):
        temp,root,doc,rows=self.make_fixture()
        with temp:self.assertEqual(validate_clause_index(root,[doc])['labelled_clauses'],len(rows))

    def test_legal_json_key_reordering(self):
        temp,root,doc,rows=self.make_fixture()
        with temp:
            (root/'registry/requirements.json').write_text(json.dumps([{k:row[k] for k in reversed(row)}for row in rows],ensure_ascii=False),encoding='utf-8')
            self.assertEqual(validate_clause_index(root,[doc])['labelled_clauses'],len(rows))

    def assert_reject(self, mutation, message):
        temp,root,doc,rows=self.make_fixture()
        with temp:
            mutation(root,rows)
            (root/'registry/requirements.json').write_text(json.dumps(rows,ensure_ascii=False),encoding='utf-8')
            with self.assertRaisesRegex(ValidationError,message):validate_clause_index(root,[doc])

    def test_digest_mismatch_rejected(self):
        self.assert_reject(lambda root,rows:rows[0].__setitem__('section_sha256','0'*64),'source span changed')

    def test_wrong_clause_owner_rejected(self):
        self.assert_reject(lambda root,rows:rows[0].__setitem__('document_id','unknown'),'unregistered clause owner')

    def test_wrong_document_hash_rejected(self):
        self.assert_reject(lambda root,rows:rows[0].__setitem__('document_sha256','0'*64),'owner/version/hash drift')

    def test_out_of_bounds_line_rejected(self):
        self.assert_reject(lambda root,rows:rows[0].__setitem__('end_line',10**6),'invalid clause source span')

    def test_duplicate_clause_rejected(self):
        self.assert_reject(lambda root,rows:rows.append(copy.deepcopy(rows[0])),'duplicate clause identity')

    def test_missing_clause_rejected(self):
        self.assert_reject(lambda root,rows:rows.pop(),'enumeration differs')

    def test_wrong_clause_order_rejected(self):
        self.assert_reject(lambda root,rows:rows.reverse(),'enumeration differs')

    def test_extra_unregistered_document_rejected(self):
        self.assert_reject(lambda root,rows:rows[0].__setitem__('path','standards/L0/other.md'),'owner/version/hash drift')

    def test_edited_body_rejected(self):
        def mutation(root,rows):
            path=root/self.registry[0]['path']
            path.write_bytes(path.read_bytes().replace(b'ARC-01',b'ARC-99',1))
        self.assert_reject(mutation,'source span changed')

    def test_missing_link_rejected_with_real_neighbor(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/'README.md').write_text('# Links\n\n[Existing](a.md)\n',encoding='utf-8')
            (root/'a.md').write_text('# A\n',encoding='utf-8')
            self.assertGreaterEqual(validate_links(root)['local_links_checked'],1)
            (root/'a.md').unlink()
            with self.assertRaisesRegex(ValidationError,'missing target'):validate_links(root)

    def test_current_documents_are_adopted(self):
        self.assertEqual(self.full_result['adopted_documents'], 162)
        from tools.verify_release_bundle import valid_version
        self.assertTrue(all(valid_version(e['version']) and e['status'] == 'adopted'
                            and e['language'] == 'zh-Hans' for e in self.registry))

    def test_stable_document_metadata_is_bound_to_body(self):
        from checks.repository_registry import validate_document_metadata
        entry = self.registry[0]
        body = (ROOT/entry['path']).read_text()
        validate_document_metadata(entry, body)
        for field, value in [('status', 'draft'), ('effective_date', '2026-10-26'), ('version', '0.2.0')]:
            with self.subTest(field=field), self.assertRaises(ValidationError):
                validate_document_metadata(dict(entry, **{field: value}), body)


if __name__=='__main__':unittest.main()
