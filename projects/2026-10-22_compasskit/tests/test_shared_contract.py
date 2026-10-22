"""The lab's shared CLI contract, exercised through the real `python -m compasskit` entry point.

  * --help returns 0;
  * --version answers on its own;
  * an unknown flag returns 2;
  * a clean input (the healthy deployment) returns 0;
  * a dirty input (the weak deployment) returns non-zero with a compasskit finding code on stdout;
  * a console that cannot encode the compass's diacritics still gets a complete report.
"""

from __future__ import annotations

import unittest

import compasskit
from tests.support import example, run_cli


class SharedContract(unittest.TestCase):
    def test_help(self):
        r = run_cli("--help")
        self.assertEqual(r.returncode, 0)
        self.assertIn(b"compasskit", r.stdout)

    def test_version(self):
        r = run_cli("--version")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.decode().strip(), "compasskit " + compasskit.__version__)

    def test_unknown_flag(self):
        self.assertEqual(run_cli("--no-such-flag").returncode, 2)

    def test_clean_input(self):
        self.assertEqual(run_cli("audit", example("healthy_deployment.json")).returncode, 0)

    def test_dirty_input(self):
        r = run_cli("audit", example("weak_deployment.json"))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn(b"AUD-002", r.stdout)

    def test_findings_on_stdout_summary_on_stderr(self):
        r = run_cli("audit", example("weak_deployment.json"))
        self.assertIn(b"AUD-", r.stdout)
        self.assertNotIn(b"AUD-", r.stderr)
        self.assertIn(b"unhealthy", r.stderr)


class LegacyConsole(unittest.TestCase):
    """A cp1252 console cannot encode IAST; the report must still be written in full."""

    def _run(self, *args):
        r = run_cli(*args, env_extra={"PYTHONIOENCODING": "cp1252"})
        self.assertNotIn(b"Traceback", r.stderr, r.stderr.decode("cp1252", "replace"))
        return r

    def test_show_with_diacritics(self):
        r = self._run("show", "A1")
        self.assertEqual(r.returncode, 0)
        self.assertIn(b"pramana", r.stdout)

    def test_catalogue_to_console(self):
        self.assertEqual(self._run("catalogue").returncode, 0)

    def test_audit_to_console(self):
        self.assertEqual(self._run("audit", example("weak_deployment.json")).returncode, 2)

    def test_list_to_console(self):
        self.assertEqual(self._run("list").returncode, 0)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
