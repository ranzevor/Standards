"""Cloud interface endpoints bind to current bytes and visible source locations."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from checks.cloud_cross_interfaces import validate
from checks.validation_common import digest, read_json, ValidationError

ROOT = Path(__file__).resolve().parents[1]


class CloudInterfaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.row = deepcopy(next(row for row in read_json(ROOT/'registry/cloud-interfaces.json')
                                 if row['interface'] == 'business-operation-result'))
        paths = {self.row['consumer'], self.row['provider']}
        self.entries = [deepcopy(entry) for entry in read_json(ROOT/'registry/standards.json')
                        if entry['path'] in paths]
        for entry in self.entries:
            path = self.root/entry['path']
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT/entry['path']).read_bytes())
        (self.root/'registry').mkdir()
        self.save()

    def save(self, rows=None):
        (self.root/'registry/standards.json').write_text(json.dumps(self.entries), encoding='utf-8')
        (self.root/'registry/cloud-interfaces.json').write_text(
            json.dumps([self.row] if rows is None else rows), encoding='utf-8')

    def rebind_provider(self, body):
        path = self.root/self.row['provider']
        path.write_text(body, encoding='utf-8')
        value = digest(path.read_bytes())
        next(entry for entry in self.entries if entry['path'] == self.row['provider'])['sha256'] = value
        self.row['provider_sha256'] = value
        self.save()

    def test_current_interfaces_bind_to_registered_endpoints(self):
        self.assertEqual(validate(ROOT), {'interfaces': 47, 'endpoint_documents': 23})

    def test_narrative_provider_section_is_a_valid_exact_locator(self):
        self.assertEqual(validate(self.root), {'interfaces': 1, 'endpoint_documents': 2})

    def test_stale_consumer_clause_alias_is_rejected(self):
        self.row['consumer_clauses'][0] = 'CLD-IAC-01'
        self.save()
        with self.assertRaisesRegex(ValidationError, 'consumer clause mapping'):
            validate(self.root)

    def test_provider_locator_does_not_match_hidden_or_code_heading(self):
        body = (self.root/self.row['provider']).read_text(encoding='utf-8')
        self.row['provider_locators'] = ['不存在的提供方章节']
        self.rebind_provider(body + '\n<!--\n## 不存在的提供方章节\n-->\n\n```markdown\n## 不存在的提供方章节\n```\n')
        with self.assertRaisesRegex(ValidationError, 'provider heading mapping'):
            validate(self.root)

    def test_provider_body_edit_requires_current_digest(self):
        with (self.root/self.row['provider']).open('a', encoding='utf-8') as stream:
            stream.write('\n正文已改变。\n')
        with self.assertRaisesRegex(ValidationError, 'endpoint body drift'):
            validate(self.root)

    def test_duplicate_interface_is_rejected(self):
        self.save([self.row, deepcopy(self.row)])
        with self.assertRaisesRegex(ValidationError, 'duplicate cloud interface'):
            validate(self.root)

    def test_provider_version_is_bound_to_current_standard(self):
        self.row['provider_version'] = '0.2.0'
        self.save()
        with self.assertRaisesRegex(ValidationError, 'provider version drift'):
            validate(self.root)

    def test_empty_technical_guarantee_is_rejected(self):
        self.row['required_guarantee'] = ''
        self.save()
        with self.assertRaisesRegex(ValidationError, 'empty cloud interface condition'):
            validate(self.root)


if __name__ == '__main__':
    unittest.main()
