from __future__ import annotations

import io
import json
import os
import shutil
import tempfile
import unittest

from compasskit.render import catalogue
from compasskit.spec import Compass
from compasskit.text import fold
from tests.support import example, run_main


class ListShow(unittest.TestCase):
    def test_list_all(self):
        rc, out, err = run_main("list")
        self.assertEqual(rc, 0)
        self.assertEqual(len(out.strip().splitlines()), 29)
        self.assertIn("29 primitive", err)

    def test_list_context_only(self):
        rc, out, _ = run_main("list", "--layer", "context", "--json")
        self.assertTrue(all("context" in p["enforcement_layers"] for p in json.loads(out)))

    def test_list_by_question(self):
        rc, out, _ = run_main("list", "--question", "7", "--json")
        self.assertEqual(sorted(p["id"] for p in json.loads(out)), ["E1", "E2", "E3", "E4", "E6", "G2"])

    def test_show(self):
        rc, out, _ = run_main("show", "E1")
        self.assertEqual(rc, 0)
        self.assertIn("Falsifier.", out)

    def test_show_alias(self):
        rc, out, _ = run_main("show", "B6", "--json")
        self.assertEqual(json.loads(out)["id"], "B3-B6")

    def test_show_unknown(self):
        rc, _, err = run_main("show", "Z9")
        self.assertEqual(rc, 2)
        self.assertIn("no primitive", err)

    def test_text_output_is_ascii(self):
        rc, out, _ = run_main("show", "A1")
        self.assertTrue(all(ord(c) < 128 for c in out))
        self.assertIn("pramana", out)


class Audit(unittest.TestCase):
    def test_healthy_exit_0(self):
        self.assertEqual(run_main("audit", example("healthy_deployment.json"))[0], 0)

    def test_weak_exit_2(self):
        rc, out, _ = run_main("audit", example("weak_deployment.json"))
        self.assertEqual(rc, 2)
        self.assertIn("AUD-002", out)

    def test_json_shape(self):
        rc, out, _ = run_main("audit", example("weak_deployment.json"), "--json")
        d = json.loads(out)
        self.assertEqual(set(d), {"tool", "version", "source", "system", "verdict", "findings"})
        self.assertEqual(d["verdict"], "unhealthy")

    def test_info_hidden_by_default(self):
        _, out, _ = run_main("audit", example("healthy_deployment.json"), "--json")
        self.assertFalse(any(f["severity"] == "INFO" for f in json.loads(out)["findings"]))

    def test_include_info(self):
        _, out, _ = run_main("audit", example("healthy_deployment.json"), "--json", "--include-info")
        self.assertTrue(any(f["severity"] == "INFO" for f in json.loads(out)["findings"]))

    def test_strict_escalates_info(self):
        rc, _, _ = run_main("audit", example("healthy_deployment.json"), "--strict")
        self.assertEqual(rc, 1)

    def test_missing_file(self):
        self.assertEqual(run_main("audit", "no-such-file.json")[0], 2)

    def test_malformed_declaration(self):
        d = tempfile.mkdtemp(prefix="ck_cli_")
        try:
            p = os.path.join(d, "x.json")
            open(p, "w").write('{"adopted": []}')
            rc, _, err = run_main("audit", p)
            self.assertEqual(rc, 2)
            self.assertIn("not valid", err)
        finally:
            shutil.rmtree(d, ignore_errors=True)


class Validate(unittest.TestCase):
    def test_valid_records(self):
        self.assertEqual(run_main("validate", "belief", example("belief_records.json"))[0], 0)

    def test_jsonl_records(self):
        self.assertEqual(run_main("validate", "ledger-entry", example("ledger.jsonl"))[0], 0)

    def test_invalid_record(self):
        d = tempfile.mkdtemp(prefix="ck_cli_")
        try:
            p = os.path.join(d, "b.json")
            open(p, "w").write(json.dumps({"id": "b", "content": "x", "source": "rumour"}))
            rc, out, _ = run_main("validate", "belief", p)
            self.assertEqual(rc, 2)
            self.assertIn("record 0", out)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_empty_file(self):
        d = tempfile.mkdtemp(prefix="ck_cli_")
        try:
            p = os.path.join(d, "e.json")
            open(p, "w").write("")
            self.assertEqual(run_main("validate", "belief", p)[0], 2)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_validate_json_report(self):
        rc, out, _ = run_main("validate", "instruction-parse", example("instruction_parse.json"), "--json")
        self.assertEqual(json.loads(out)["invalid"], 0)


class Ledger(unittest.TestCase):
    def test_good(self):
        self.assertEqual(run_main("ledger-verify", example("ledger.jsonl"))[0], 0)

    def test_tampered(self):
        rc, out, _ = run_main("ledger-verify", example("tampered_ledger.jsonl"))
        self.assertEqual(rc, 2)
        self.assertIn("broken", out)

    def test_missing(self):
        self.assertEqual(run_main("ledger-verify", "nope.jsonl")[0], 2)


class PromptAndCatalogue(unittest.TestCase):
    def test_prompt(self):
        rc, out, _ = run_main("prompt")
        self.assertEqual(rc, 0)
        self.assertIn("never override", out)

    def test_agent_prompt(self):
        self.assertIn("peer", run_main("prompt", "--agent")[1])

    def test_prompts_are_ascii(self):
        for args in (("prompt",), ("prompt", "--agent")):
            self.assertTrue(all(ord(c) < 128 for c in run_main(*args)[1]))

    def test_catalogue_to_file_keeps_diacritics(self):
        d = tempfile.mkdtemp(prefix="ck_cli_")
        try:
            p = os.path.join(d, "c.md")
            self.assertEqual(run_main("catalogue", "--output", p)[0], 0)
            text = io.open(p, encoding="utf-8").read()
            self.assertEqual(text, catalogue(Compass.load()))
            self.assertTrue(any(ord(c) > 127 for c in text))
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_catalogue_to_stdout_is_folded(self):
        _, out, _ = run_main("catalogue")
        self.assertTrue(all(ord(c) < 128 for c in out))

    def test_catalogue_covers_every_primitive(self):
        text = catalogue(Compass.load())
        for pid in Compass.load().ids():
            self.assertIn("### %s " % pid, text)

    def test_no_command_prints_help(self):
        rc, out, _ = run_main()
        self.assertEqual(rc, 0)
        self.assertIn("usage", out)


class Fold(unittest.TestCase):
    def test_iast_folds_to_ascii(self):
        self.assertEqual(fold("pram" + chr(0x0101) + chr(0x1E47) + "a"), "pramana")

    def test_unfoldable_shown_visible(self):
        self.assertEqual(fold("a" + chr(0x200B) + "b"), "a<U+200B>b")

    def test_newlines_kept(self):
        self.assertEqual(fold("a\nb"), "a\nb")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
