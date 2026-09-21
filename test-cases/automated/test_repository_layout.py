from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ALLOWED_TOP_LEVEL_DIRECTORIES = {
    "collaborators",
    "source",
    "test-cases",
    "versions",
}


class RepositoryLayoutTests(unittest.TestCase):
    def test_top_level_directories_match_allowlist(self) -> None:
        result = subprocess.run(
            [
                "git",
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "-z",
            ],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        actual = {
            path.split("/", 1)[0]
            for path in result.stdout.split("\0")
            if "/" in path
        }

        self.assertSetEqual(actual, ALLOWED_TOP_LEVEL_DIRECTORIES)


if __name__ == "__main__":
    unittest.main()
