"""Real unpacked consumers plus corrupt/mismatched archive rejection."""
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from tests.test_release_bundle import fixture_source, bundle_parts
from tools.build_release_bundle import archive_names, archive_zip, build
from tools.check_offline_consumers import ConsumerCheckError, run
from tools.verify_release_bundle import VerificationError

ROOT = Path(__file__).resolve().parents[1]


class OfflineConsumerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='standards-offline-consumer-test-')
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.base = Path(cls.temporary.name)
        cls.assets = cls.base / 'assets'
        result = build(ROOT, cls.assets)
        source_name, skill_name = archive_names(result['version'])
        cls.source = cls.assets / source_name
        cls.skill = cls.assets / skill_name

    def test_actual_source_and_skill_work_from_foreign_unicode_directory(self):
        evidence = self.base / 'actual-native-consumers'
        result = run(self.source, self.skill, evidence)
        self.assertEqual(result['status'], 'pass')
        self.assertEqual(len(result['commands']), 7)
        self.assertEqual(result['other_platforms'], 'not-run')
        self.assertTrue(all(row['exit_code'] == 0 for row in result['commands']))
        self.assertEqual(set(result['post_run_integrity']), {'source', 'agent-skill'})
        stored = json.loads((evidence / 'execution.json').read_bytes())
        self.assertEqual(stored, result)
        for row in result['commands']:
            self.assertIn('无关 工作目录', row['cwd'])
            self.assertTrue((evidence / row['stdout']['path']).is_file())
            self.assertTrue((evidence / row['stderr']['path']).is_file())

    def test_swapped_archive_kinds_fail_before_any_consumer_executes(self):
        evidence = self.base / 'wrong-kinds'
        with self.assertRaisesRegex(ConsumerCheckError, 'wrong archive kind'):
            run(self.skill, self.source, evidence)
        result = json.loads((evidence / 'execution.json').read_bytes())
        self.assertEqual((result['status'], result['commands']), ('fail', []))

    def test_corrupt_archive_retains_failure_and_never_extracts_or_executes(self):
        damaged = self.base / 'damaged-source.zip'
        with zipfile.ZipFile(self.source) as original, zipfile.ZipFile(damaged, 'w') as output:
            for info in original.infolist():
                raw = original.read(info)
                if info.filename.endswith('/source/project.json'):
                    raw += b'\n'
                output.writestr(info, raw)
        evidence = self.base / 'corrupt-input'
        with self.assertRaises(VerificationError):
            run(damaged, self.skill, evidence)
        result = json.loads((evidence / 'execution.json').read_bytes())
        self.assertEqual(result['status'], 'fail')
        self.assertEqual(result['commands'], [])
        self.assertFalse((evidence / '独立 离线消费者').exists())

    def test_cross_release_inputs_fail_before_any_consumer_executes(self):
        source = fixture_source('0.1.0')
        records, summary, _ = bundle_parts(source, 'agent-skill')
        older = self.base / 'older-skill.zip'
        archive_zip(older, 'agent-skill', records, summary)
        evidence = self.base / 'mixed-release'
        with self.assertRaisesRegex(ConsumerCheckError, 'Source/Skill inputs differ'):
            run(self.source, older, evidence)
        result = json.loads((evidence / 'execution.json').read_bytes())
        self.assertEqual((result['status'], result['commands']), ('fail', []))

    def test_same_release_number_does_not_hide_a_different_snapshot(self):
        version = json.loads((ROOT / 'project.json').read_bytes())['version']
        records, summary, _ = bundle_parts(fixture_source(version), 'agent-skill')
        other = self.base / 'same-version-other-snapshot.zip'
        archive_zip(other, 'agent-skill', records, summary)
        evidence = self.base / 'mixed-snapshot'
        with self.assertRaisesRegex(ConsumerCheckError, 'current_snapshot_sha256'):
            run(self.source, other, evidence)
        result = json.loads((evidence / 'execution.json').read_bytes())
        self.assertEqual((result['status'], result['commands']), ('fail', []))

    def test_existing_evidence_cannot_be_overwritten(self):
        evidence = self.base / 'retained-evidence'
        evidence.mkdir()
        marker = evidence / 'keep.txt'
        marker.write_bytes(b'previous evidence\n')
        with self.assertRaisesRegex(ConsumerCheckError, 'already exists'):
            run(self.source, self.skill, evidence)
        self.assertEqual(marker.read_bytes(), b'previous evidence\n')

    def test_evidence_cannot_pollute_the_reviewed_source(self):
        evidence = ROOT / 'consumer-evidence-must-not-be-created'
        with self.assertRaisesRegex(ConsumerCheckError, 'outside the reviewed source'):
            run(self.source, self.skill, evidence)
        self.assertFalse(evidence.exists())


if __name__ == '__main__':
    unittest.main()
