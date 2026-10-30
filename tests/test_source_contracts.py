"""Source propositions retain independent identities and actual clause targets."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from checks.source_contracts import validate, validate_claims
from checks.validation_common import ValidationError

ROOT = Path(__file__).resolve().parents[1]


class SourceContractTests(unittest.TestCase):
    def test_current_claims_and_clause_mappings(self):
        result = validate(ROOT)
        self.assertEqual(result['source_claims'], 594)
        self.assertEqual(result['clause_mappings'], 1233)

    def test_single_and_multiple_supported_propositions(self):
        row = {'id': 'S1', 'url': 'https://example.invalid/spec', 'supported_claim': 'A finite statement.'}
        self.assertEqual(validate_claims([row], 'synthetic'), {'S1'})
        row.pop('supported_claim')
        row['propositions'] = [{'supported': 'First finite statement.'}, {'supported': 'Second finite statement.'}]
        self.assertEqual(validate_claims([row], 'synthetic'), {'S1'})

    def test_identity_url_and_support_fields_are_required(self):
        baseline = {'id': 'S1', 'url': 'https://example.invalid/spec', 'supported_claim': 'A finite statement.'}
        for changes in ({'id': ''}, {'url': 'local-file'}, {'supported_claim': ''}):
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                validate_claims([dict(baseline, **changes)], 'synthetic')
        with self.assertRaisesRegex(ValidationError, 'duplicate or missing source identity'):
            validate_claims([baseline, deepcopy(baseline)], 'synthetic')

    def test_broken_clause_mapping_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT/'sources', root/'sources')
            shutil.copytree(ROOT/'standards', root/'standards')
            (root/'registry').mkdir()
            shutil.copy2(ROOT/'registry/standards.json', root/'registry/standards.json')
            path = root/'sources/desktop-mobile-source-claims.json'
            packet = json.loads(path.read_text(encoding='utf-8'))
            packet['claims'][0]['supports'][0]['clause'] = 'UNKNOWN-999'
            path.write_text(json.dumps(packet), encoding='utf-8')
            with self.assertRaisesRegex(ValidationError, 'source mapping clause not found'):
                validate(root)


if __name__ == '__main__':
    unittest.main()
