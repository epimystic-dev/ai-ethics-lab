from __future__ import annotations

import datetime as _dt
import io
import json
import os
import shutil
import tempfile
import unittest

from compasskit.audit import audit, deployment_validator
from compasskit.declare import scaffold_declaration
from compasskit.registers import ratification_findings
from compasskit.spec import Compass
from tests.support import example, run_main


class ScaffoldDeclaration(unittest.TestCase):
    def setUp(self):
        self.compass = Compass.load()

    def test_output_passes_the_deployment_schema(self):
        inventory = {
            "system": "test-system",
            "as_of": "2026-10-23",
            "primitives": [
                {"id": "E1", "layer": "architecture", "owner": "security", "merged": "2026-10-01"},
                {"id": "E6", "layer": "governance", "owner": "ceo", "merged": "2026-10-01"},
            ],
        }
        decl, _ = scaffold_declaration(inventory, self.compass)
        self.assertEqual(deployment_validator().errors(decl), [])

    def test_scaffold_is_auditable(self):
        inventory = {
            "system": "test-system",
            "as_of": "2026-10-23",
            "primitives": [
                {"id": "E1", "layer": "architecture", "owner": "security", "merged": "2026-10-01"},
            ],
        }
        decl, _ = scaffold_declaration(inventory, self.compass)
        audit(decl, self.compass)

    def test_class_b_gets_a_ratification_stub(self):
        inventory = {
            "system": "s",
            "primitives": [
                {"id": "E1", "layer": "architecture"},
                {"id": "E6", "layer": "governance"},
                {"id": "F1", "layer": "governance"},
            ],
        }
        decl, warnings = scaffold_declaration(inventory, self.compass)
        rat_ids = sorted(r["primitive_id"] for r in decl["ratifications"])
        self.assertEqual(rat_ids, ["E6", "F1"])
        self.assertTrue(any("E6 is Class B" in w for w in warnings))
        self.assertTrue(any("F1 is Class B" in w for w in warnings))

    def test_non_class_b_gets_no_stub(self):
        inventory = {
            "system": "s",
            "primitives": [
                {"id": "E1", "layer": "architecture"},
                {"id": "A1", "layer": "middleware"},
            ],
        }
        decl, _ = scaffold_declaration(inventory, self.compass)
        self.assertEqual(decl["ratifications"], [])

    def test_alias_resolves_to_canonical_id(self):
        inventory = {"system": "s", "primitives": [{"id": "B4", "layer": "middleware"}]}
        decl, _ = scaffold_declaration(inventory, self.compass)
        self.assertEqual([a["id"] for a in decl["adopted"]], ["B3-B6"])

    def test_unknown_primitive_raises(self):
        with self.assertRaises(ValueError) as ctx:
            scaffold_declaration({"system": "s", "primitives": [{"id": "Z9", "layer": "context"}]},
                                 self.compass)
        self.assertIn("unknown primitive", str(ctx.exception))

    def test_wrong_layer_is_a_warning_not_an_error(self):
        inventory = {"system": "s", "primitives": [{"id": "E1", "layer": "context"}]}
        decl, warnings = scaffold_declaration(inventory, self.compass)
        self.assertEqual(decl["adopted"][0]["layer"], "context")
        self.assertTrue(any("declared at context" in w and "E1" in w for w in warnings))

    def test_missing_owner_or_merged_warns(self):
        inventory = {"system": "s", "primitives": [{"id": "E1", "layer": "architecture"}]}
        _, warnings = scaffold_declaration(inventory, self.compass)
        self.assertTrue(any("E1 has no owner and merged" in w for w in warnings))

    def test_present_owner_and_merged_do_not_warn(self):
        inventory = {"system": "s", "primitives": [
            {"id": "E1", "layer": "architecture", "owner": "sec", "merged": "2026-10-01"},
        ]}
        _, warnings = scaffold_declaration(inventory, self.compass)
        self.assertFalse(any("E1 has no owner" in w or "E1 has no merged" in w for w in warnings))

    def test_notes_pass_through(self):
        inventory = {"system": "s", "primitives": [
            {"id": "E1", "layer": "architecture", "notes": "hard architectural lock"},
        ]}
        decl, _ = scaffold_declaration(inventory, self.compass)
        self.assertEqual(decl["adopted"][0]["notes"], "hard architectural lock")

    def test_missing_e1_warns(self):
        inventory = {"system": "s", "primitives": [{"id": "A1", "layer": "middleware"}]}
        _, warnings = scaffold_declaration(inventory, self.compass)
        self.assertTrue(any("E1 is not in the inventory" in w for w in warnings))

    def test_as_of_defaults_to_today(self):
        inventory = {"system": "s", "primitives": [{"id": "E1", "layer": "architecture"}]}
        decl, _ = scaffold_declaration(inventory, self.compass)
        self.assertEqual(decl["as_of"], _dt.date.today().isoformat())

    def test_duplicate_id_warns(self):
        inventory = {"system": "s", "primitives": [
            {"id": "E1", "layer": "architecture"},
            {"id": "E1", "layer": "governance"},
        ]}
        _, warnings = scaffold_declaration(inventory, self.compass)
        self.assertTrue(any("E1 appears twice" in w for w in warnings))

    def test_class_b_stub_satisfies_the_record_schema(self):
        inventory = {"system": "s", "primitives": [
            {"id": "E1", "layer": "architecture"},
            {"id": "E6", "layer": "governance"},
        ]}
        decl, _ = scaffold_declaration(inventory, self.compass)
        stub = decl["ratifications"][0]
        schema_only = [p for p in ratification_findings(stub) if "review_date must fall after" not in p]
        self.assertEqual(schema_only, [])

    def test_class_b_stub_still_fails_the_audit_rule(self):
        inventory = {"system": "s", "primitives": [
            {"id": "E1", "layer": "architecture"},
            {"id": "E6", "layer": "governance"},
        ]}
        decl, _ = scaffold_declaration(inventory, self.compass)
        problems = ratification_findings(decl["ratifications"][0])
        self.assertTrue(any("review_date must fall after" in p for p in problems))

    def test_bad_inventory_shapes(self):
        for bad in (
            [],
            {"primitives": [{"id": "E1", "layer": "architecture"}]},
            {"system": "s"},
            {"system": "", "primitives": [{"id": "E1", "layer": "architecture"}]},
            {"system": "s", "primitives": []},
            {"system": "s", "primitives": [{"layer": "context"}]},
            {"system": "s", "primitives": [{"id": "A1"}]},
            {"system": "s", "primitives": [{"id": "A1", "layer": "context", "colour": "red"}]},
        ):
            with self.assertRaises(ValueError):
                scaffold_declaration(bad, self.compass)


class DeclareCLI(unittest.TestCase):
    def test_stdout_output_is_valid_json(self):
        rc, out, _ = run_main("declare", example("inventory_example.json"))
        self.assertEqual(rc, 0)
        decl = json.loads(out)
        self.assertEqual(decl["system"], "example-review-assistant")
        self.assertEqual(deployment_validator().errors(decl), [])

    def test_stderr_summary_counts(self):
        _, _, err = run_main("declare", example("inventory_example.json"))
        self.assertIn("scaffolded 5 adopted", err)
        self.assertIn("ratification stub(s)", err)

    def test_declare_file_output(self):
        d = tempfile.mkdtemp(prefix="ck_declare_")
        try:
            p = os.path.join(d, "decl.json")
            rc, _, err = run_main("declare", example("inventory_example.json"), "--output", p)
            self.assertEqual(rc, 0)
            self.assertIn("wrote " + p, err)
            with io.open(p, encoding="utf-8") as fh:
                decl = json.load(fh)
            self.assertEqual(decl["system"], "example-review-assistant")
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_declare_unknown_primitive_exits_2(self):
        d = tempfile.mkdtemp(prefix="ck_declare_")
        try:
            p = os.path.join(d, "inv.json")
            open(p, "w").write(json.dumps({"system": "s", "primitives": [
                {"id": "Z9", "layer": "context"}]}))
            rc, _, err = run_main("declare", p)
            self.assertEqual(rc, 2)
            self.assertIn("unknown primitive", err)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_declare_missing_file_exits_2(self):
        rc, _, err = run_main("declare", "no-such-inventory.json")
        self.assertEqual(rc, 2)
        self.assertIn("cannot read", err)

    def test_declare_malformed_json_exits_2(self):
        d = tempfile.mkdtemp(prefix="ck_declare_")
        try:
            p = os.path.join(d, "bad.json")
            open(p, "w").write("{not json")
            rc, _, err = run_main("declare", p)
            self.assertEqual(rc, 2)
            self.assertIn("cannot read", err)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_declare_then_audit_round_trip(self):
        d = tempfile.mkdtemp(prefix="ck_declare_")
        try:
            p = os.path.join(d, "decl.json")
            self.assertEqual(run_main("declare", example("inventory_example.json"),
                                      "--output", p)[0], 0)
            audit_rc, _, _ = run_main("audit", p, "--json")
            self.assertIn(audit_rc, (1, 2))
        finally:
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
