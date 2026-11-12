"""Regression contracts for OPC PR self-review and enforced GitHub quality checks."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest

from checks.behavior_cases import validate_suite

ROOT = Path(__file__).resolve().parents[1]


class GitHubGovernanceTests(unittest.TestCase):
    def source(self, name):
        return (ROOT / name).read_text(encoding="utf-8")

    def test_required_quality_gate_fail_closed_across_native_consumers(self):
        quality = self.source(".github/workflows/quality.yml")
        platform = self.source(".github/workflows/platform.yml")
        self.assertIn("  push:\n    branches: [main]", quality)
        self.assertIn("  native-consumers:\n    uses: ./.github/workflows/platform.yml", quality)
        self.assertIn("  validate:\n    name: validate\n    needs: [contracts, native-consumers]\n    if: ${{ always() }}", quality)
        self.assertIn('CONTRACTS_RESULT" != "success"', quality)
        self.assertIn('CONSUMERS_RESULT" != "success"', quality)
        self.assertIn("  workflow_call:\n", platform)
        self.assertIn("matrix:\n        os: [ubuntu-latest, windows-latest]", platform)
        self.assertNotIn("    paths:\n", platform)

    def test_opc_pr_has_no_bot_or_formal_review_requirements(self):
        workflow = self.source(".github/workflows/governance-metadata.yml")
        self.assertIn("  pull_request_target:\n", workflow)
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", workflow)
        self.assertNotIn("governance_review_gate.cjs", workflow)
        self.assertFalse((ROOT / ".github/workflows/opc-open-pr.yml").exists())
        self.assertFalse((ROOT / ".github/scripts/governance_review_gate.cjs").exists())
        guide = self.source("guides/GITHUB-STRICT-GOVERNANCE.md")
        self.assertIn("required_approving_review_count=0", guide)
        self.assertIn("本人创建 PR", guide)

    def test_behavior_suite_checks_legitimate_self_review(self):
        suite = json.loads(self.source("examples/ai-agent/behavior/cases/github-governance.json"))
        self.assertEqual(validate_suite(suite), 6)
        decisions = {
            c["id"]: next(check["expected"] for check in c["checks"]
                          if check["kind"] == "json_equals")
            for c in suite["cases"]
        }
        self.assertFalse(decisions["GITHUB-001"]["ready"])
        self.assertFalse(decisions["GITHUB-002"]["ready"])
        self.assertFalse(decisions["GITHUB-003"]["published"])
        self.assertTrue(decisions["GITHUB-004"]["ready"])
        self.assertFalse(decisions["GITHUB-005"]["execute"])
        self.assertFalse(decisions["GITHUB-006"]["ready"])


    def test_each_main_push_has_its_own_non_cancelling_concurrency_group(self):
        for path in (".github/workflows/quality.yml", ".github/workflows/platform.yml"):
            with self.subTest(workflow=path):
                workflow = self.source(path)
                self.assertIn(
                    "github.event_name == 'push' && github.run_id || github.ref",
                    workflow,
                )
                self.assertIn(
                    "cancel-in-progress: ${{ github.event_name != 'push' }}",
                    workflow,
                )

    @unittest.skipUnless(shutil.which("bash"), "Bash is required to exercise the Linux quality gate")
    def test_validate_step_rejects_failed_skipped_cancelled_and_missing_dependencies(self):
        quality = self.source(".github/workflows/quality.yml")
        block = quality.split(
            "      - name: Reject incomplete or failed required prerequisites\n", 1
        )[1].split("        run: |\n", 1)[1]
        lines = []
        for line in block.splitlines():
            if line.startswith("          "):
                lines.append(line[10:])
            elif lines:
                break
        script = "\n".join(lines) + "\n"
        self.assertIn('CONTRACTS_RESULT" != "success"', script)
        self.assertIn('CONSUMERS_RESULT" != "success"', script)
        for contracts, consumers in (
            ("success", "success"),
            ("failure", "success"),
            ("success", "failure"),
            ("skipped", "success"),
            ("success", "skipped"),
            ("cancelled", "success"),
            ("success", "cancelled"),
            ("neutral", "success"),
            ("success", "neutral"),
            ("", "success"),
            ("success", ""),
        ):
            with self.subTest(contracts=contracts, consumers=consumers):
                result = subprocess.run(
                    ["bash", "-e", "-c", script],
                    env={**os.environ, "CONTRACTS_RESULT": contracts,
                         "CONSUMERS_RESULT": consumers},
                    capture_output=True, timeout=10,
                )
                self.assertEqual(
                    result.returncode == 0,
                    contracts == consumers == "success",
                    result.stdout.decode("utf-8", "replace") +
                    result.stderr.decode("utf-8", "replace"),
                )

    def test_skill_routes_to_current_opc_flow(self):
        skill = self.source("skills/ranzevor-standards/SKILL.md.in")
        self.assertIn("references/guides/GITHUB-STRICT-GOVERNANCE.md", skill)
        self.assertIn("原生必需批准数为 0", skill)


if __name__ == "__main__":
    unittest.main()
