"""Regression contracts for strict GitHub governance integration and safe behavior fixtures."""
import json
from pathlib import Path
import unittest

from checks.behavior_cases import validate_suite

ROOT = Path(__file__).resolve().parents[1]


class StrictGovernanceTests(unittest.TestCase):
    def source(self, name):
        return (ROOT / name).read_text(encoding="utf-8")

    def test_required_quality_gate_fail_closed_across_native_consumers(self):
        quality = self.source(".github/workflows/quality.yml")
        platform = self.source(".github/workflows/platform.yml")
        self.assertIn("  push:\n    branches: [main]", quality)
        self.assertIn("  contracts:\n", quality)
        self.assertIn("  native-consumers:\n    uses: ./.github/workflows/platform.yml", quality)
        self.assertIn("  validate:\n    name: validate\n    needs: [contracts, native-consumers]\n    if: ${{ always() }}", quality)
        self.assertIn('CONTRACTS_RESULT" != "success"', quality)
        self.assertIn('CONSUMERS_RESULT" != "success"', quality)
        self.assertIn("  workflow_call:\n", platform)
        self.assertIn("matrix:\n        os: [ubuntu-latest, windows-latest]", platform)
        self.assertNotIn("    paths:\n", platform)
        self.assertNotIn("  offline-consumer:\n    if:", platform)

    def test_review_gate_is_trusted_and_runs_again_after_review_events(self):
        workflow = self.source(".github/workflows/governance-metadata.yml")
        guard = self.source(".github/scripts/governance_review_gate.cjs")
        self.assertIn("  pull_request_target:\n", workflow)
        self.assertIn("  pull_request_review:\n    types: [submitted, edited, dismissed]", workflow)
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", workflow)
        self.assertIn("node .github/scripts/governance_review_gate.cjs", workflow)
        self.assertIn("CHANGES_REQUESTED", guard)
        self.assertIn("review.commit_id === pr.head.sha", guard)
        self.assertIn("const needed = 1;", guard)
        self.assertIn("review.author_association === 'OWNER'", guard)

    def test_github_behavior_suite_covers_failures_and_legal_neighbor(self):
        suite = json.loads(self.source("examples/ai-agent/behavior/cases/github-governance.json"))
        self.assertEqual(validate_suite(suite), 6)
        ids = {case["id"] for case in suite["cases"]}
        self.assertEqual(ids, {"GITHUB-001", "GITHUB-002", "GITHUB-003", "GITHUB-004", "GITHUB-005", "GITHUB-006"})
        decisions = {case["id"]: next(check for check in case["checks"] if check["kind"] == "json_equals")["expected"]
                     for case in suite["cases"]}
        self.assertFalse(decisions["GITHUB-001"]["ready"])
        self.assertFalse(decisions["GITHUB-002"]["ready"])
        self.assertFalse(decisions["GITHUB-003"]["published"])
        self.assertTrue(decisions["GITHUB-004"]["ready"])
        self.assertFalse(decisions["GITHUB-005"]["execute"])
        self.assertFalse(decisions["GITHUB-006"]["ready"])

    def test_skill_and_navigation_link_to_full_github_process(self):
        skill = self.source("skills/ranzevor-standards/SKILL.md.in")
        self.assertIn("references/guides/GITHUB-STRICT-GOVERNANCE.md", skill)
        guide = self.source("guides/GITHUB-STRICT-GOVERNANCE.md")
        for word in ("Ruleset", "CHANGES_REQUESTED", "main", "合并后", "所有者"):
            self.assertIn(word, guide)


if __name__ == "__main__":
    unittest.main()
