"""Source citations retain their license and byte identities without a repository inventory."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from tests.platform_support import make_symlink

from checks.generate_source_catalog import build, generate
from checks.validation_common import ValidationError

ROOT = Path(__file__).resolve().parents[1]


class SourceCatalogueTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for name in ('sources', 'registry', 'LICENSES'):
            (self.root / name).mkdir()
        for name in ('LICENSE', 'LICENSE-NOTICE.md', 'LICENSES/Apache-2.0.txt',
                     'LICENSES/CC-BY-4.0.txt'):
            shutil.copyfile(ROOT / name, self.root / name)
        (self.root / 'registry/standards.json').write_text('[]\n')
        (self.root / 'sources/reference.json').write_text('{"url":"https://example.invalid"}\n')

    def test_root_license_applies_to_source_metadata_with_third_party_boundary(self):
        row = build(self.root)['source_objects'][0]
        self.assertEqual(row['license_status'],
                         'CC-BY-4.0-project-authored-metadata; third-party-material-excluded')
        self.assertIn('underlying third-party', row['rights_scope'])
        self.assertTrue(row['public_redistribution_authorized'])

    def test_source_objects_keep_case_sensitive_relative_path_order(self):
        for name in ('README.md', 'a.json', 'nested/README.md', 'nested/a.json'):
            path = self.root / 'sources' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'{}\n' if path.suffix == '.json' else b'Source\n')
        self.assertEqual([row['path'] for row in build(self.root)['source_objects']], [
            'sources/README.md',
            'sources/a.json',
            'sources/nested/README.md',
            'sources/nested/a.json',
            'sources/reference.json',
        ])

    def test_missing_or_changed_license_policy_is_rejected(self):
        (self.root / 'LICENSE').write_text('No material license allocation\n')
        with self.assertRaisesRegex(ValidationError, 'license allocation'):
            build(self.root)
        shutil.copyfile(ROOT / 'LICENSE', self.root / 'LICENSE')
        (self.root / 'LICENSES/Apache-2.0.txt').write_text('changed license text\n')
        with self.assertRaisesRegex(ValidationError, 'canonical license'):
            build(self.root)

    def test_changed_source_or_license_row_requires_current_source_index(self):
        generate(self.root)
        (self.root / 'sources/reference.json').write_text('{"url":"https://changed.invalid"}\n')
        with self.assertRaisesRegex(ValidationError, 'source catalog is stale'):
            generate(self.root, check=True)
        generate(self.root)
        path = self.root / 'registry/source-catalog.json'
        value = json.loads(path.read_text())
        value['source_objects'][0]['license_status'] = 'unestablished'
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValidationError, 'source catalog is stale'):
            generate(self.root, check=True)

    def test_unrelated_file_edit_does_not_require_a_source_catalog_change(self):
        generate(self.root)
        previous = (self.root / 'registry/source-catalog.json').read_bytes()
        (self.root / 'local-tool.py').write_text('print("updated tool")\n')
        self.assertTrue(generate(self.root, check=True)['check'])
        self.assertEqual((self.root / 'registry/source-catalog.json').read_bytes(), previous)

    def test_duplicate_nonfinite_json_and_source_symlinks_are_rejected(self):
        path = self.root / 'sources/reference.json'
        for content, message in [('{"url":1,"url":2}', 'duplicate JSON'),
                                 ('{"value":NaN}', 'nonfinite JSON')]:
            path.write_text(content)
            with self.subTest(content=content), self.assertRaisesRegex(ValidationError, message):
                build(self.root)
        path.unlink()
        make_symlink(path, self.root / 'LICENSE')
        with self.assertRaisesRegex(ValidationError, 'symlink'):
            build(self.root)


if __name__ == '__main__':
    unittest.main()
