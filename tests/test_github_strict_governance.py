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
        self.assertEqual(validate_suite(suite), 7)
        cases = {case["id"]: case for case in suite["cases"]}

        def decision(case):
            return next(check["expected"] for check in case["checks"]
                        if check["kind"] == "json_equals")

        self.assertFalse(decision(cases["GITHUB-001"])["ready"])
        self.assertFalse(decision(cases["GITHUB-002"])["ready"])
        self.assertFalse(decision(cases["GITHUB-003"])["published"])
        self.assertFalse(decision(cases["GITHUB-005"])["execute"])
        self.assertFalse(decision(cases["GITHUB-006"])["ready"])

        positive = json.loads(cases["GITHUB-004"]["setup"][0]["text"])
        negative = json.loads(cases["GITHUB-007"]["setup"][0]["text"])
        self.assertEqual(positive["ruleset"]["required_approving_review_count"], 0)
        self.assertEqual(positive["ruleset"]["enforcement"], "active")
        self.assertTrue(positive["ruleset"]["require_pull_request"])
        self.assertEqual(positive["reviews"], [])
        self.assertEqual(
            {key: value for key, value in positive.items()
             if key != "independent_technical_review"},
            {key: value for key, value in negative.items()
             if key != "independent_technical_review"},
        )

        def blockers(candidate):
            result = []
            head = candidate["head"]
            target = candidate["target_branch"]
            author_review = candidate["self_review"]
            independent = candidate["independent_technical_review"]
            checks = candidate["required_checks"]
            required = candidate["ruleset"]["required_status_checks"]
            authorization = candidate["merge_authorization"]

            if not (author_review["complete"] is True and
                    author_review["candidate_head"] == head):
                result.append("self_review")
            if not (independent["status"] == "pass" and independent["reviewer"] and
                    independent["participated_in_implementation"] is False and
                    independent["candidate_head"] == head and
                    independent["base_head"] == target["current_head"] and
                    independent["scope_complete"] is True and
                    independent["open_blockers"] == 0):
                result.append("independent_review")
            if not (target["up_to_date"] is True and
                    target["reviewed_base"] == target["current_head"]):
                result.append("target_sync")
            if set(checks) != set(required) or any(
                check["conclusion"] != "success" or check["candidate_head"] != head
                for check in checks.values()
            ):
                result.append("required_ci")
            if candidate["review_threads_resolved"] is not True:
                result.append("unresolved_review_thread")
            if not (authorization["granted"] is True and
                    authorization["candidate_head"] == head and
                    authorization["target_head"] == target["current_head"]):
                result.append("merge_authorization")
            return result

        self.assertEqual(blockers(positive), [])
        self.assertEqual(blockers(negative), ["independent_review"])
        self.assertEqual(decision(cases["GITHUB-004"]), {"ready": True, "blocking": []})
        self.assertEqual(
            decision(cases["GITHUB-007"]),
            {"ready": False, "blocking": ["independent_review"]},
        )

        mutations = (
            ("stale independent review", ("independent_technical_review", "candidate_head"),
             "previous-head", "independent_review"),
            ("review not completed", ("independent_technical_review", "status"),
             "not-run", "independent_review"),
            ("author disguised as reviewer", ("independent_technical_review", "participated_in_implementation"),
             True, "independent_review"),
            ("stale check", ("required_checks", "validate", "candidate_head"),
             "previous-head", "required_ci"),
            ("skipped check", ("required_checks", "validate", "conclusion"),
             "skipped", "required_ci"),
            ("unsynchronized branch", ("target_branch", "up_to_date"),
             False, "target_sync"),
            ("base advanced", ("target_branch", "current_head"),
             "new-base", "target_sync"),
            ("authorization missing", ("merge_authorization", "granted"),
             False, "merge_authorization"),
            ("authorization for old head", ("merge_authorization", "candidate_head"),
             "previous-head", "merge_authorization"),
            ("unresolved conversation", ("review_threads_resolved",),
             False, "unresolved_review_thread"),
        )
        for label, path, value, expected_blocker in mutations:
            with self.subTest(condition=label):
                changed = json.loads(json.dumps(positive))
                node = changed
                for key in path[:-1]:
                    node = node[key]
                node[path[-1]] = value
                self.assertIn(expected_blocker, blockers(changed))


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
        self.assertIn("已采用该模式的 GitHub OPC 仓库", skill)
        guide = self.source("guides/SKILL-CONSUMPTION.md")
        self.assertIn("| 软件仓库审查、质量门禁和发布 |", guide)
        self.assertIn("| GitHub 仓库审查、保护规则、CI、合并或发布 |", guide)


if __name__ == "__main__":
    unittest.main()
