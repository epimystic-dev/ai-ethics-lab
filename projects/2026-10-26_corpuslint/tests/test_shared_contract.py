"""The lab's shared CLI contract for linter kinds, exercised through the real
`python -m corpuslint` entry point.

  * --help returns 0
  * --version prints 'corpuslint <version>' and returns 0
  * an unknown flag returns 2
  * a clean input (clean_corpus.json) returns 0
  * a dirty input (broken_corpus.json) returns 2 and names rule ids on stdout
  * findings go to stdout, summary to stderr
  * a console that cannot encode non-ASCII still gets a complete report with
    no traceback and <U+XXXX>-style escapes
  * the public surface exports every name every linter in the lab exports
"""

from __future__ import annotations

import unittest

import corpuslint
from tests.support import example, run_cli


class SharedContract(unittest.TestCase):
    def test_help(self):
        r = run_cli("--help")
        self.assertEqual(r.returncode, 0)
        self.assertIn(b"corpuslint", r.stdout)

    def test_version(self):
        r = run_cli("--version")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.decode().strip(), "corpuslint " + corpuslint.__version__)

    def test_unknown_flag(self):
        self.assertEqual(run_cli("--no-such-flag").returncode, 2)

    def test_clean_input(self):
        self.assertEqual(run_cli("lint", example("clean_corpus.json")).returncode, 0)

    def test_dirty_input(self):
        r = run_cli("lint", example("broken_corpus.json"))
        self.assertEqual(r.returncode, 2)
        self.assertIn(b"CORP-", r.stdout)

    def test_findings_on_stdout_summary_on_stderr(self):
        r = run_cli("lint", example("broken_corpus.json"))
        self.assertIn(b"CORP-", r.stdout)
        self.assertNotIn(b"CORP-", r.stderr)
        self.assertIn(b"verdict=unhealthy", r.stderr)


class PackageSurface(unittest.TestCase):
    def test_version(self):
        self.assertIsInstance(corpuslint.__version__, str)
        self.assertRegex(corpuslint.__version__, r"^\d+\.\d+\.\d+$")

    def test_shared_names_exported(self):
        for name in (
            "__version__", "Severity", "Verdict", "Finding", "ScanResult",
            "Rule", "ALL_RULES", "lint", "lint_path",
        ):
            self.assertTrue(hasattr(corpuslint, name), name + " not exported")

    def test_all_rules_is_rule_objects(self):
        self.assertGreater(len(corpuslint.ALL_RULES), 0)
        for r in corpuslint.ALL_RULES:
            self.assertIsInstance(r, corpuslint.Rule)
            self.assertRegex(r.id, r"^CORP-\d{3}$")
            self.assertIn(r.severity, corpuslint.Severity.ladder())
            self.assertTrue(r.description)

    def test_rule_ids_unique(self):
        ids = [r.id for r in corpuslint.ALL_RULES]
        self.assertEqual(len(ids), len(set(ids)))


class LegacyConsole(unittest.TestCase):
    """A cp1252 console cannot encode an em-dash or Cyrillic; the report must
    still be written in full, with no traceback and visible <U+XXXX> escapes."""

    def _run_with_nonascii_in_findings(self):
        import json
        import os
        import tempfile

        # An id containing a zero-width space and Cyrillic letters. The
        # missing testimony class fires CORP-001 and the id is printed in the
        # `where` column, so the reporter is actually asked to render it.
        payload = {
            "name": "legacy-console-fixture",
            "documents": [
                {
                    "id": "doc-" + chr(0x043F) + chr(0x200B) + chr(0x0440),
                    "origin": "sensor://a",
                    "chain_of_custody": [
                        {"actor": "cam", "operation": "capture", "timestamp": "2026-10-26T10:00:00Z"}
                    ],
                }
            ],
        }
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        try:
            json.dump(payload, tmp)
            tmp.flush()
            tmp.close()
            r = run_cli("lint", tmp.name, env_extra={"PYTHONIOENCODING": "cp1252"})
        finally:
            os.unlink(tmp.name)
        return r

    def test_no_traceback_under_cp1252(self):
        r = self._run_with_nonascii_in_findings()
        self.assertNotIn(b"Traceback", r.stderr)

    def test_u_plus_escape_in_report(self):
        r = self._run_with_nonascii_in_findings()
        self.assertIn(b"<U+200B>", r.stdout + r.stderr)

    def test_rule_id_still_printed(self):
        r = run_cli(
            "lint", example("broken_corpus.json"),
            env_extra={"PYTHONIOENCODING": "cp1252"},
        )
        self.assertIn(b"CORP-", r.stdout)


if __name__ == "__main__":
    unittest.main()
