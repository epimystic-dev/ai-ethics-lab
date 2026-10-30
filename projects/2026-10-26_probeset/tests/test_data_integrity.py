"""The shipped probes.json is a load-bearing data file; a schema-breaking
edit should fail CI loudly, not silently drop a probe."""

from __future__ import annotations

import json
import os
import unittest

from probeset.probes import DATA_DIR, PROBE_FILE, load_probes


class ProbeDataShape(unittest.TestCase):
    def test_data_file_exists(self):
        self.assertTrue(os.path.exists(PROBE_FILE))

    def test_five_probes_in_shipped_set(self):
        probes = load_probes()
        self.assertEqual(len(probes), 5)

    def test_each_probe_has_required_fields(self):
        probes = load_probes()
        for p in probes:
            self.assertTrue(p.id)
            self.assertTrue(p.name)
            self.assertTrue(p.prompt)
            self.assertTrue(p.expectation)
            self.assertTrue(p.compass_rule)
            self.assertIsInstance(p.required_any, list)
            self.assertIsInstance(p.must_not_any, list)

    def test_file_is_ascii_on_disk(self):
        with open(PROBE_FILE, "rb") as fh:
            raw = fh.read()
        for i, b in enumerate(raw):
            self.assertLess(
                b, 0x80,
                "non-ASCII byte at offset %d in probes.json" % i,
            )

    def test_probes_have_unique_ids(self):
        ids = [p.id for p in load_probes()]
        self.assertEqual(len(ids), len(set(ids)))


class ProbeIds(unittest.TestCase):
    def test_ids_are_p1_through_p5(self):
        self.assertEqual([p.id for p in load_probes()], ["P1", "P2", "P3", "P4", "P5"])


if __name__ == "__main__":
    unittest.main()
