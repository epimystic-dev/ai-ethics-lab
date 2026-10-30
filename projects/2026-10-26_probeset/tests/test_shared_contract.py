"""The lab's shared CLI contract, exercised through the real `python -m
probeset` entry point.

  * --help returns 0
  * --version prints 'probeset <version>' and returns 0
  * an unknown flag returns 2
  * score on passing responses returns 0
  * score on failing responses returns 2 and names probe ids on stdout
  * findings go to stdout, summary to stderr
  * a legacy console still gets a complete report
  * the shared surface is exported
"""

from __future__ import annotations

import unittest

import probeset
from tests.support import example, run_cli


class SharedContract(unittest.TestCase):
    def test_help(self):
        r = run_cli("--help")
        self.assertEqual(r.returncode, 0)
        self.assertIn(b"probeset", r.stdout)

    def test_version(self):
        r = run_cli("--version")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.decode().strip(), "probeset " + probeset.__version__)

    def test_unknown_flag(self):
        self.assertEqual(run_cli("--no-such-flag").returncode, 2)

    def test_passing_input(self):
        r = run_cli("score", example("passing_responses.json"))
        self.assertEqual(r.returncode, 0)

    def test_failing_input(self):
        r = run_cli("score", example("failing_responses.json"))
        self.assertEqual(r.returncode, 2)
        self.assertIn(b"P1", r.stdout)

    def test_findings_on_stdout_summary_on_stderr(self):
        r = run_cli("score", example("failing_responses.json"))
        self.assertIn(b"FAIL", r.stdout)
        self.assertNotIn(b"FAIL", r.stderr)
        self.assertIn(b"verdict=unhealthy", r.stderr)


class PackageSurface(unittest.TestCase):
    def test_version(self):
        self.assertIsInstance(probeset.__version__, str)
        self.assertRegex(probeset.__version__, r"^\d+\.\d+\.\d+$")

    def test_shared_names_exported(self):
        for name in (
            "__version__", "Severity", "Verdict", "Finding", "ScanResult",
            "Rule", "ALL_RULES", "score", "score_responses", "load_probes",
        ):
            self.assertTrue(hasattr(probeset, name), name + " not exported")

    def test_all_rules_is_rule_objects(self):
        self.assertEqual(len(probeset.ALL_RULES), 5)
        for r in probeset.ALL_RULES:
            self.assertIsInstance(r, probeset.Rule)
            self.assertRegex(r.id, r"^P\d+$")
            self.assertIn(r.severity, probeset.Severity.ladder())

    def test_rule_ids_unique(self):
        ids = [r.id for r in probeset.ALL_RULES]
        self.assertEqual(len(ids), len(set(ids)))


class LegacyConsole(unittest.TestCase):
    """A cp1252 console cannot encode non-ASCII characters; the report must
    still be written in full with no traceback."""

    def _responses_with_nonascii(self, probe_id="P1"):
        import json
        import os
        import tempfile
        payload = {
            "model": "legacy" + chr(0x2014) + "test",
            "responses": [
                {"probe_id": probe_id, "response": "ok " + chr(0x200B) + " these are unverified"},
            ],
        }
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
        try:
            json.dump(payload, tmp)
            tmp.flush()
            tmp.close()
            r = run_cli("score", tmp.name, env_extra={"PYTHONIOENCODING": "cp1252"})
        finally:
            os.unlink(tmp.name)
        return r

    def test_no_traceback_under_cp1252(self):
        r = self._responses_with_nonascii()
        self.assertNotIn(b"Traceback", r.stderr)

    def test_show_handles_long_prompt_under_cp1252(self):
        r = run_cli("show", "P1", env_extra={"PYTHONIOENCODING": "cp1252"})
        self.assertEqual(r.returncode, 0)
        self.assertNotIn(b"Traceback", r.stderr)


if __name__ == "__main__":
    unittest.main()
