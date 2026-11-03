"""Verify the governance metadata gate with the repository's test discovery."""
from pathlib import Path
import subprocess
import unittest


class GovernanceMetadataTests(unittest.TestCase):
    def test_node_regressions(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            ["node", "--test", "tests/governance_gate.test.cjs"],
            cwd=root, capture_output=True, text=True, encoding="utf-8",
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
