"""Reporter tests - including the hidden-character case the shared contract
calls out. If a scraped document carries a zero-width space in its origin and
the reporter echoes it raw, the text report re-hides exactly the character the
report was meant to expose."""

from __future__ import annotations

import json
import unittest

from corpuslint import lint, render_json, render_text


class TextRender(unittest.TestCase):
    def test_hidden_character_is_escaped_in_text(self):
        # An id containing a zero-width space and an em dash. The missing
        # testimony class fires CORP-001 and the id is printed as `where`.
        payload = {
            "name": "hidden",
            "documents": [
                {
                    "id": "doc" + chr(0x2014) + chr(0x200B) + "01",
                    "origin": "sensor://a",
                    "chain_of_custody": [
                        {"actor": "cam", "operation": "capture", "timestamp": "2026-10-26T10:00:00Z"}
                    ],
                }
            ],
        }
        r = lint(payload)
        text = render_text(r)
        self.assertNotIn(chr(0x200B), text)
        self.assertNotIn(chr(0x2014), text)
        self.assertIn("<U+2014>", text)
        self.assertIn("<U+200B>", text)

    def test_text_report_shows_verdict_in_json_payload_for_dirty(self):
        r = lint({"name": "", "documents": []})
        txt = render_text(r)
        self.assertIn("corpuslint:", txt)
        self.assertIn("CORP-012", txt)

    def test_empty_findings_handled(self):
        payload = {
            "name": "clean",
            "documents": [
                {
                    "id": "p1",
                    "testimony_class": "perception",
                    "origin": "sensor://a",
                    "chain_of_custody": [
                        {"actor": "cam", "operation": "capture", "timestamp": "2026-10-26T10:00:00Z"}
                    ],
                }
            ],
        }
        r = lint(payload)
        txt = render_text(r)
        self.assertIn("(no findings)", txt)


class JsonRender(unittest.TestCase):
    def test_json_round_trip(self):
        r = lint({"name": "x", "documents": []})
        obj = json.loads(render_json(r))
        self.assertEqual(obj["verdict"], r.verdict)
        self.assertEqual(len(obj["findings"]), len(r.findings))

    def test_json_ensure_ascii_escapes_unicode(self):
        payload = {
            "name": "x",
            "documents": [
                {
                    "id": "d1",
                    "testimony_class": "testimony",
                    "testifier": {"name": "em" + chr(0x2014), "domain": "ref", "trust_weight": 0.4},
                    "origin": "https://example.com/x",
                    "chain_of_custody": [
                        {"actor": "fetch", "operation": "fetch", "timestamp": "2026-10-26T10:00:00Z"}
                    ],
                }
            ],
        }
        r = lint(payload)
        js = render_json(r)
        self.assertNotIn(chr(0x2014), js)


if __name__ == "__main__":
    unittest.main()
