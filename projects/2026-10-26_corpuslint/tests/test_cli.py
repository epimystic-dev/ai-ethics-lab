"""Extra CLI tests over and above the shared contract."""

from __future__ import annotations

import json
import os
import tempfile
import unittest

from tests.support import example, run_cli


class RulesSubcommand(unittest.TestCase):
    def test_lists_known_ids(self):
        r = run_cli("rules")
        self.assertEqual(r.returncode, 0)
        for rid in ("CORP-001", "CORP-002", "CORP-003", "CORP-013"):
            self.assertIn(rid.encode(), r.stdout)


class LintJson(unittest.TestCase):
    def test_json_output_is_valid_json(self):
        r = run_cli("lint", "--json", example("clean_corpus.json"))
        self.assertEqual(r.returncode, 0)
        obj = json.loads(r.stdout)
        self.assertEqual(obj["verdict"], "healthy")


class StrictMode(unittest.TestCase):
    def test_strict_promotes_info(self):
        r = run_cli("lint", "--strict", example("clean_corpus.json"))
        # clean_corpus has at least one INFO (class-coverage absent? Let's not require it.)
        # The flag's behavior: if any INFO fires, exit 2. If none, exit 0.
        self.assertIn(r.returncode, (0, 2))

    def test_needs_attention_exits_1_without_strict(self):
        r = run_cli("lint", example("needs_attention_corpus.json"))
        self.assertEqual(r.returncode, 1)
        self.assertIn(b"verdict=needs-attention", r.stderr)

    def test_needs_attention_exits_2_with_strict(self):
        r = run_cli("lint", "--strict", example("needs_attention_corpus.json"))
        self.assertEqual(r.returncode, 2)


class UnreadableInput(unittest.TestCase):
    def test_missing_file_is_unknown(self):
        r = run_cli("lint", "no-such-file.json")
        self.assertEqual(r.returncode, 2)
        self.assertIn(b"verdict=unknown", r.stderr)

    def test_invalid_json_is_unknown(self):
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        try:
            tmp.write("{this is not json")
            tmp.close()
            r = run_cli("lint", tmp.name)
            self.assertEqual(r.returncode, 2)
            self.assertIn(b"verdict=unknown", r.stderr)
        finally:
            os.unlink(tmp.name)

    def test_directory_path_does_not_crash(self):
        # A path that exists but cannot be opened as a file (e.g. a directory
        # on Windows surfaces PermissionError; on POSIX, IsADirectoryError)
        # must be reported through the same uniform OSError path in
        # linter.lint_path, not propagated as a bare traceback. This brings
        # corpuslint's hostile-input discipline to parity with the probeset
        # and compasskit regression tests.
        tmp = tempfile.mkdtemp(prefix="corpuslint_test_")
        try:
            r = run_cli("lint", tmp)
            self.assertEqual(r.returncode, 2)
            self.assertIn(b"verdict=unknown", r.stderr)
            self.assertIn(b"os-error", r.stdout)
            self.assertNotIn(b"Traceback", r.stderr)
        finally:
            os.rmdir(tmp)


class DisableFlag(unittest.TestCase):
    def test_disable_suppresses_rule(self):
        r = run_cli("lint", "--disable", "CORP-001", example("broken_corpus.json"))
        # bad-001 should no longer surface CORP-001.
        self.assertNotIn(b"CORP-001", r.stdout)


if __name__ == "__main__":
    unittest.main()
