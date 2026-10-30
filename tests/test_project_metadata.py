"""Project metadata contains only durable normative and product attributes."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from checks.validation_common import read_json, ValidationError
from checks.validate_product import validate_project_metadata

ROOT = Path(__file__).resolve().parents[1]


class ProjectMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project = read_json(ROOT / "project.json")
        cls.entries = read_json(ROOT / "registry/standards.json")

    def test_valid_stable_metadata(self):
        self.assertEqual(validate_project_metadata(self.project, self.entries)["adopted_documents"], 162)

    def test_release_patch_is_independent_of_document_versions(self):
        for version in ('0.1.0', '0.1.1', '0.1.10'):
            with self.subTest(version=version):
                result = validate_project_metadata(dict(self.project, version=version), self.entries)
                self.assertEqual(result['adopted_documents'], 162)

    def test_unsupported_or_ambiguous_release_versions_are_rejected(self):
        for version in ('0.1.01', '0.2.0', 'v0.1.1', '', None, True):
            with self.subTest(version=version), self.assertRaises(ValidationError):
                validate_project_metadata(dict(self.project, version=version), self.entries)

    def test_runtime_state_fields_are_rejected(self):
        invalid = dict(self.project, ephemeral_state="unused")
        with self.assertRaises(ValidationError):
            validate_project_metadata(invalid, self.entries)

    def test_unselected_or_wrong_license_state_is_rejected(self):
        for state in ('license-not-selected','MIT',''):
            with self.subTest(state=state),self.assertRaises(ValidationError):
                validate_project_metadata(dict(self.project,license_status=state),self.entries)

    def test_document_identity_mismatch_is_rejected(self):
        invalid = dict(self.project, adopted_documents=self.project["adopted_documents"][:-1])
        with self.assertRaises(ValidationError):
            validate_project_metadata(invalid, self.entries)


if __name__ == "__main__":
    unittest.main()
