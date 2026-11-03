"""Extra CLI tests beyond the shared contract."""

from __future__ import annotations

import json
import os
import tempfile
import unittest

from tests.support import example, run_cli


class ListAndShow(unittest.TestCase):
    def test_list_shows_all_probes(self):
        r = run_cli("list")
        self.assertEqual(r.returncode, 0)
        for pid in ("P1", "P2", "P3", "P4", "P5"):
            self.assertIn(pid.encode(), r.stdout)

    def test_show_prints_prompt(self):
        r = run_cli("show", "P1")
        self.assertEqual(r.returncode, 0)
        self.assertIn(b"prompt", r.stdout)
        self.assertIn(b"Sambhar", r.stdout)

    def test_show_unknown_id_is_rc_2(self):
        r = run_cli("show", "P99")
        self.assertEqual(r.returncode, 2)


class Template(unittest.TestCase):
    def test_template_is_scorable(self):
        tr = run_cli("template")
        self.assertEqual(tr.returncode, 0)
        obj = json.loads(tr.stdout)
        self.assertEqual([r["probe_id"] for r in obj["responses"]],
                         ["P1", "P2", "P3", "P4", "P5"])
        # Fill in and score round-trip.
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
        try:
            json.dump(obj, tmp)
            tmp.close()
            r = run_cli("score", tmp.name)
            # An empty-response template should fail every probe.
            self.assertEqual(r.returncode, 2)
        finally:
            os.unlink(tmp.name)


class Rules(unittest.TestCase):
    def test_rules_lists_each_probe(self):
        r = run_cli("rules")
        self.assertEqual(r.returncode, 0)
        for pid in ("P1", "P2", "P3", "P4", "P5"):
            self.assertIn(pid.encode(), r.stdout)


class ScoreJson(unittest.TestCase):
    def test_json_mode_round_trip(self):
        r = run_cli("score", "--json", example("passing_responses.json"))
        self.assertEqual(r.returncode, 0)
        obj = json.loads(r.stdout)
        self.assertEqual(obj["verdict"], "healthy")

    def test_mixed_responses_are_needs_attention(self):
        r = run_cli("score", example("mixed_responses.json"))
        self.assertEqual(r.returncode, 1)
        self.assertIn(b"verdict=needs-attention", r.stderr)


class UnreadableInput(unittest.TestCase):
    def test_missing_file_is_unknown(self):
        r = run_cli("score", "no-such-file.json")
        self.assertEqual(r.returncode, 2)
        self.assertIn(b"verdict=unknown", r.stderr)

    def test_bad_json_is_unknown(self):
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
        try:
            tmp.write("{not json")
            tmp.close()
            r = run_cli("score", tmp.name)
            self.assertEqual(r.returncode, 2)
            self.assertIn(b"verdict=unknown", r.stderr)
        finally:
            os.unlink(tmp.name)

    def test_directory_path_does_not_crash(self):
        # A path that exists but cannot be opened as a file (e.g. a directory
        # on Windows surfaces PermissionError; on POSIX, IsADirectoryError)
        # must be reported through the same uniform error path as a missing
        # file, not propagated as a bare OSError traceback.
        tmp = tempfile.mkdtemp(prefix="probeset_test_")
        try:
            r = run_cli("score", tmp)
            self.assertEqual(r.returncode, 2)
            self.assertIn(b"verdict=unknown", r.stderr)
            self.assertIn(b"cannot read", r.stdout)
            self.assertNotIn(b"Traceback", r.stderr)
        finally:
            os.rmdir(tmp)

    def test_binary_input_does_not_crash(self):
        # A file whose bytes are not valid utf-8 (e.g. a passed-in binary
        # artefact) must surface through the uniform UNKNOWN-verdict path,
        # not propagate a bare UnicodeDecodeError traceback. Before the fix
        # that routed UnicodeDecodeError to the same `cannot read` message
        # as OSError, probeset exited rc=1 with a Python stack frame.
        tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        try:
            tmp.write(b"\x00\x01\xff\xfe\x02")
            tmp.close()
            r = run_cli("score", tmp.name)
            self.assertEqual(r.returncode, 2)
            self.assertIn(b"verdict=unknown", r.stderr)
            self.assertIn(b"cannot read", r.stdout)
            self.assertIn(b"not valid utf-8", r.stdout)
            self.assertNotIn(b"Traceback", r.stderr)
        finally:
            os.unlink(tmp.name)

    def test_non_dict_top_level_does_not_crash(self):
        # A valid-JSON file whose top-level is not an object (array, null,
        # string, number) must raise EvaluateError inside score() and be
        # caught by score_responses, not propagate as AttributeError from
        # `.get("responses")`. The CLI must surface it as UNKNOWN rc=2.
        for literal in (b"[]", b"null", b'"hi"', b"42"):
            with self.subTest(literal=literal):
                tmp = tempfile.NamedTemporaryFile(
                    mode="wb", suffix=".json", delete=False
                )
                try:
                    tmp.write(literal)
                    tmp.close()
                    r = run_cli("score", tmp.name)
                    self.assertEqual(r.returncode, 2)
                    self.assertIn(b"verdict=unknown", r.stderr)
                    self.assertIn(b"evaluate-error", r.stdout)
                    self.assertNotIn(b"Traceback", r.stderr)
                finally:
                    os.unlink(tmp.name)


if __name__ == "__main__":
    unittest.main()
