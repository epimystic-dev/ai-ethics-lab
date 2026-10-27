"""The lab's worked inventory and audit stays in sync with the floor theses.

The document walks step 1 (inventory) and step 2 (audit) of the book's six-step adoption
procedure for a synthetic system. The audit lists one finding per floor thesis in
`compass.json`. If a thesis is added, renamed or removed in the compass data, the document
must be updated too; this test fails loudly rather than letting the two drift.
"""

from __future__ import annotations

import os
import re
import unittest

import compasskit

from tests.support import LAB_ROOT

DOC_PATH = os.path.join(LAB_ROOT, "docs", "WORKED-INVENTORY-AND-AUDIT.md")


class WorkedInventoryAndAudit(unittest.TestCase):
    def setUp(self):
        with open(DOC_PATH, encoding="utf-8") as fh:
            self.text = fh.read()
        self.compass = compasskit.load()
        self.theses = self.compass.floor()["theses"]

    def test_both_steps_are_present(self):
        self.assertRegex(self.text, r"(?mi)^## Step 1 .*inventory")
        self.assertRegex(self.text, r"(?mi)^## Step 2 .*audit")

    def test_every_floor_thesis_has_a_finding(self):
        audit_match = re.search(
            r"^## Step 2 .*?audit.*?(?=^## )", self.text, re.M | re.S | re.I,
        )
        self.assertIsNotNone(audit_match, "audit section not found")
        audit = audit_match.group(0)
        for thesis in self.theses:
            tid, name = thesis["id"], thesis["name"]
            with self.subTest(thesis=tid):
                row = re.search(
                    r"^\| *" + re.escape(tid) + r" *-[^|]*\|[^|]*\|([^|]*)\|",
                    audit,
                    re.M,
                )
                self.assertIsNotNone(
                    row, f"no audit row for floor thesis {tid}",
                )
                self.assertIn(
                    name, audit,
                    f"audit does not name floor thesis {tid} ({name!r})",
                )
                finding = row.group(1).strip()
                self.assertTrue(
                    len(finding) >= 20,
                    f"finding for {tid} is empty or trivial: {finding!r}",
                )

    def test_ascii_only(self):
        for i, ch in enumerate(self.text):
            if ord(ch) > 0x7f:
                self.fail(
                    f"non-ASCII character {ch!r} (U+{ord(ch):04X}) at byte offset "
                    f"{i}; the doc must use plain ASCII punctuation",
                )

    def test_calls_out_the_C_series_naming_clash(self):
        catalogue_cids = [
            p for p in self.compass.ids() if p.startswith("C")
        ]
        if catalogue_cids:
            self.assertRegex(
                self.text,
                r"(?i)floor thes[ei]s? are numbered C1-C6"
                r"|three primitives in the catalogue are also"
                r"|clash",
                "the compass has catalogue C-series primitives; the doc must warn "
                "the reader about the C1-C6 vs catalogue-C naming clash",
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
