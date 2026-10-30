"""Direct failures and lawful neighbors for the software-repository profile."""
from __future__ import annotations

import copy
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from checks.software_repository import main, validate_profile, validate_template_contracts
from checks.validation_common import read_json, ValidationError

ROOT = Path(__file__).resolve().parents[1]


class SoftwareRepositoryProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = read_json(ROOT / 'registry/schemas/software-repository-profile.schema.json')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.profile = {
            'schema_version': 'standards-software-repository/1',
            'id': 'synthetic-public-project',
            'profile_state': 'defined',
            'example_only': True,
            'operation_authorized': False,
            'repository': {
                'visibility': 'public',
                'distribution': 'open-source',
                'collaboration': 'contributions',
                'maintenance': 'active',
                'release': 'published',
                'maintainer': 'synthetic-maintainer',
                'final_identity': 'synthetic-release:v1.0.0@0123456789abcdef',
            },
            'files': {
                'readme': 'README.md',
                'license': 'LICENSE',
                'rights': 'THIRD_PARTY_NOTICES.md',
                'contributing': 'CONTRIBUTING.md',
                'security': 'SECURITY.md',
                'pull_request_template': '.github/pull_request_template.md',
                'issue_templates': [
                    '.github/ISSUE_TEMPLATE/defect.md',
                    '.github/ISSUE_TEMPLATE/proposal.md',
                ],
                'platform_controls': 'governance/platform-controls.md',
                'workflows': ['.github/workflows/quality.yml'],
            },
            'quick_start': {'commands': ['python -m example --help']},
            'evidence_exclusions': [
                'evidence/local-validation/',
                'evidence/local-runtime/',
            ],
        }
        for relative in (
            'README.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md', 'CONTRIBUTING.md',
            'SECURITY.md', '.github/pull_request_template.md',
            '.github/ISSUE_TEMPLATE/defect.md', '.github/ISSUE_TEMPLATE/proposal.md',
            'governance/platform-controls.md',
        ):
            self.write(relative, relative + '\n')
        self.write(
            '.github/workflows/quality.yml',
            'steps:\n  - uses: actions/checkout@0123456789abcdef0123456789abcdef01234567\n',
        )
        self.write(
            '.gitignore',
            'evidence/local-validation/\nevidence/local-runtime/\n',
        )

    def tearDown(self):
        self.temp.cleanup()

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8', newline='\n')

    def git(self, *args):
        result = subprocess.run(
            ['git', '-C', str(self.root), *args],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode('utf-8', errors='replace'))

    def test_public_open_source_profile_accepts_full_action_sha(self):
        result = validate_profile(self.profile, self.schema, self.root)
        self.assertTrue(result['contract_valid'])
        self.assertEqual(result['action_pins_checked'], 1)

    def test_open_source_without_license_is_rejected(self):
        profile = copy.deepcopy(self.profile)
        profile['files']['license'] = None
        with self.assertRaisesRegex(ValidationError, 'requires license'):
            validate_profile(profile, self.schema, self.root)

    def test_private_no_distribution_and_no_license_is_legal(self):
        (self.root / '.github/workflows/quality.yml').unlink()
        profile = copy.deepcopy(self.profile)
        profile['repository'].update({
            'visibility': 'private',
            'distribution': 'none',
            'collaboration': 'closed',
            'release': 'not-published',
            'final_identity': None,
        })
        profile['files'].update({
            'license': None,
            'rights': None,
            'contributing': None,
            'security': None,
            'pull_request_template': None,
            'issue_templates': [],
            'workflows': [],
        })
        result = validate_profile(profile, self.schema, self.root)
        self.assertTrue(result['contract_valid'])
        self.assertEqual(result['action_pins_checked'], 0)

    def test_floating_action_ref_is_rejected(self):
        self.write('.github/workflows/quality.yml', 'steps:\n  - uses: actions/checkout@v4\n')
        with self.assertRaisesRegex(ValidationError, 'full commit SHA'):
            validate_profile(self.profile, self.schema, self.root)

    def test_quoted_full_action_sha_is_legal(self):
        self.write(
            '.github/workflows/quality.yml',
            'steps:\n  - uses: "actions/checkout@0123456789abcdef0123456789abcdef01234567"\n',
        )
        result = validate_profile(self.profile, self.schema, self.root)
        self.assertEqual(result['action_pins_checked'], 1)

    def test_flow_and_quoted_uses_keys_reject_floating_refs(self):
        cases = (
            'steps:\n  - {uses: actions/checkout@v4}\n',
            'steps:\n  - {"uses": "actions/checkout@v4"}\n',
        )
        for workflow in cases:
            with self.subTest(workflow=workflow):
                self.write('.github/workflows/quality.yml', workflow)
                with self.assertRaisesRegex(ValidationError, 'full commit SHA'):
                    validate_profile(self.profile, self.schema, self.root)

    def test_flow_quoted_uses_key_accepts_full_sha(self):
        self.write(
            '.github/workflows/quality.yml',
            'steps:\n'
            '  - {"uses": "actions/checkout@0123456789abcdef0123456789abcdef01234567"}\n',
        )
        result = validate_profile(self.profile, self.schema, self.root)
        self.assertEqual(result['action_pins_checked'], 1)

    def test_block_scalar_uses_text_is_not_an_action(self):
        self.write(
            '.github/workflows/quality.yml',
            'steps:\n'
            '  - run: |\n'
            '      echo "uses: actions/checkout@v4"\n'
            '  - uses: actions/checkout@0123456789abcdef0123456789abcdef01234567\n',
        )
        result = validate_profile(self.profile, self.schema, self.root)
        self.assertEqual(result['action_pins_checked'], 1)

    def test_apostrophe_in_plain_yaml_scalar_is_legal(self):
        self.write(
            '.github/workflows/quality.yml',
            "steps:\n"
            "  - name: Retrieve this run's artifacts\n"
            '    uses: actions/checkout@0123456789abcdef0123456789abcdef01234567\n',
        )
        result = validate_profile(self.profile, self.schema, self.root)
        self.assertEqual(result['action_pins_checked'], 1)

    def test_missing_evidence_ignore_is_rejected(self):
        self.write('.gitignore', 'evidence/local-validation/\n')
        with self.assertRaisesRegex(ValidationError, 'missing from .gitignore'):
            validate_profile(self.profile, self.schema, self.root)

    def test_later_gitignore_negation_is_rejected(self):
        self.git('init', '-q')
        self.write(
            '.gitignore',
            'evidence/local-validation/\n'
            '!evidence/local-validation/\n'
            'evidence/local-runtime/\n',
        )
        with self.assertRaisesRegex(ValidationError, 'exclusion is not effective'):
            validate_profile(self.profile, self.schema, self.root)

    def test_tracked_evidence_is_rejected_even_when_forced(self):
        self.git('init', '-q')
        self.write('evidence/local-validation/output.txt', 'synthetic output\n')
        self.git('add', '-f', 'evidence/local-validation/output.txt')
        with self.assertRaisesRegex(ValidationError, 'tracked implementation evidence'):
            validate_profile(self.profile, self.schema, self.root)

    def test_noncanonical_evidence_exclusions_are_rejected(self):
        for value in ('./evidence/local-validation/', 'evidence//local-validation/'):
            profile = copy.deepcopy(self.profile)
            profile['evidence_exclusions'][0] = value
            with self.subTest(value=value), self.assertRaisesRegex(
                    ValidationError, 'canonical spelling'):
                validate_profile(profile, self.schema)

    def test_archived_example_keeps_final_identity(self):
        profile = read_json(ROOT / 'examples/repository-adoption/archived-open-source.json')
        result = validate_profile(profile, self.schema)
        self.assertTrue(result['contract_valid'])

    def test_current_repository_templates_cover_required_fields(self):
        result = validate_template_contracts(ROOT)
        self.assertEqual(result['templates'], 6)
        self.assertGreater(result['required_fields'], 30)

    def test_cli_uses_bundled_schema_for_external_repository(self):
        self.write('governance/software-repository.json',
                   json.dumps(self.profile, ensure_ascii=False, indent=2) + '\n')
        output = StringIO()
        with redirect_stdout(output):
            exit_code = main([
                '--root', str(self.root),
                '--profile', 'governance/software-repository.json',
            ])
        self.assertEqual(exit_code, 0)
        self.assertTrue(json.loads(output.getvalue())['contract_valid'])


if __name__ == '__main__':
    unittest.main()
