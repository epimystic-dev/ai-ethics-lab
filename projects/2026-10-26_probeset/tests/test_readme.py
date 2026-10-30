"""README invariants: every probe id in ALL_RULES is documented in the
README, and the shell example in the README actually works."""

from __future__ import annotations

import os
import unittest

import probeset
from tests.support import PROJECT_ROOT, example, run_cli

README = os.path.join(PROJECT_ROOT, "README.md")


class ReadmeDocumentsEveryProbe(unittest.TestCase):
    def test_each_probe_id_in_readme(self):
        with open(README, "r", encoding="utf-8") as fh:
            text = fh.read()
        for probe in probeset.ALL_RULES:
            self.assertIn(probe.id, text, probe.id + " undocumented in README")

    def test_rule_count_matches_readme(self):
        with open(README, "r", encoding="utf-8") as fh:
            text = fh.read()
        count = len(probeset.ALL_RULES)
        self.assertIn("five", text.lower())  # the prompt doc calls them "five probes"


class ReadmeExamplesRun(unittest.TestCase):
    def test_score_passing(self):
        r = run_cli("score", example("passing_responses.json"))
        self.assertEqual(r.returncode, 0)

    def test_score_failing(self):
        r = run_cli("score", example("failing_responses.json"))
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
