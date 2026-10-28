"""README invariants: every rule id in ALL_RULES is documented in the README,
and the shell example in the README actually works."""

from __future__ import annotations

import os
import unittest

import corpuslint
from tests.support import PROJECT_ROOT, example, run_cli

README = os.path.join(PROJECT_ROOT, "README.md")


class ReadmeDocumentsEveryRule(unittest.TestCase):
    def test_each_rule_id_in_readme(self):
        with open(README, "r", encoding="utf-8") as fh:
            text = fh.read()
        for rule in corpuslint.ALL_RULES:
            self.assertIn(rule.id, text, rule.id + " undocumented in README")


class ReadmeExamplesRun(unittest.TestCase):
    def test_lint_clean_corpus(self):
        r = run_cli("lint", example("clean_corpus.json"))
        self.assertEqual(r.returncode, 0)

    def test_lint_broken_corpus(self):
        r = run_cli("lint", example("broken_corpus.json"))
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
