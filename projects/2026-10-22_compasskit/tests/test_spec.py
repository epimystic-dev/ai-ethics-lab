"""The compass as data: complete, internally consistent, and in sync with the repository."""

from __future__ import annotations

import os
import unittest

import compasskit
from compasskit.spec import CONTRACTS, DATA_DIR, Compass
from tests.support import LAB_ROOT, ROOT_COMPASS

C = Compass.load()


class Integrity(unittest.TestCase):
    def test_twenty_nine_primitives(self):
        self.assertEqual(len(C.primitives), 29)

    def test_ids_unique(self):
        self.assertEqual(len(set(C.ids())), len(C.ids()))

    def test_every_series_present(self):
        self.assertEqual({p["series"] for p in C.primitives}, set("ABCDEFG"))

    def test_every_primitive_has_all_eight_book_fields(self):
        for p in C.primitives:
            for k in ("summary", "example", "statement", "warrant", "failure_mode", "sketch", "falsifier"):
                self.assertTrue(p[k].strip(), "%s.%s empty" % (p["id"], k))
            self.assertTrue(p["adoption"]["class_reason"].strip())

    def test_nine_questions_cover_every_primitive_once(self):
        seen = [pid for q in C.questions() for pid in q["primitives"]]
        self.assertEqual(sorted(seen), sorted(C.ids()))

    def test_question_field_matches_question_table(self):
        for q in C.questions():
            for pid in q["primitives"]:
                self.assertEqual(C.get(pid)["question"], q["id"])

    def test_stack_covers_every_primitive_once(self):
        seen = [pid for s in C.data["stack"] for pid in s["primitives"]]
        self.assertEqual(sorted(seen), sorted(C.ids()))

    def test_stack_starts_with_the_floor(self):
        first = min(C.data["stack"], key=lambda s: s["order"])
        self.assertEqual(first["primitives"], ["E1"])

    def test_targets_are_last_and_class_b(self):
        last = max(C.data["stack"], key=lambda s: s["order"])
        self.assertEqual(sorted(last["primitives"]), ["F1", "F2", "F3"])
        for pid in last["primitives"]:
            self.assertEqual(C.get(pid)["adoption"]["base_class"], "B")

    def test_six_floor_theses(self):
        self.assertEqual([t["id"] for t in C.floor()["theses"]], ["C1", "C2", "C3", "C4", "C5", "C6"])

    def test_floor_is_class_a_to_adopt_and_d_to_loosen(self):
        e1 = C.get("E1")["adoption"]
        self.assertEqual(e1["base_class"], "A")
        self.assertIn("D", [c["class"] for c in e1["conditional"]])

    def test_floor_is_never_context_enforceable(self):
        self.assertNotIn("context", C.get("E1")["enforcement_layers"])

    def test_ledger_is_architecture(self):
        self.assertIn("architecture", C.get("E4")["enforcement_layers"])

    def test_adoption_classes_are_valid(self):
        for p in C.primitives:
            self.assertIn(p["adoption"]["base_class"], "ABCD")
            for c in p["adoption"]["conditional"]:
                self.assertIn(c["class"], "ABCD")

    def test_every_data_contract_named_exists(self):
        for p in C.primitives:
            if p["data_contract"]:
                self.assertTrue(os.path.isfile(os.path.join(DATA_DIR, p["data_contract"])), p["id"])

    def test_every_reference_implementation_imports(self):
        import importlib
        for p in C.primitives:
            if p["reference_implementation"]:
                importlib.import_module(p["reference_implementation"])

    def test_book_chapters_are_in_range(self):
        for p in C.primitives:
            for n in p["book_chapters"]:
                self.assertTrue(1 <= n <= 52, (p["id"], n))

    def test_compass_validates_against_its_schema(self):
        self.assertEqual(compasskit.compass_validator().errors(C.data), [])

    def test_every_contract_loads_strictly(self):
        for name in CONTRACTS:
            compasskit.contract_validator(name)

    def test_source_records_adaptation(self):
        self.assertTrue(C.data["source"]["adapted"])
        self.assertTrue(C.data["source"]["changes"])


class Lookup(unittest.TestCase):
    def test_level_tag_aliases(self):
        for alias in ("B3", "b4", "B5", "B6", "B3-B6"):
            self.assertEqual(C.get(alias)["id"], "B3-B6")

    def test_unknown_id(self):
        with self.assertRaises(KeyError):
            C.get("Z9")

    def test_select_by_question(self):
        self.assertEqual([p["id"] for p in C.select(question=4)], ["B1"])

    def test_select_by_class(self):
        self.assertTrue(all(p["adoption"]["base_class"] == "B" for p in C.select(base_class="b")))

    def test_context_enforceable_is_a_minority(self):
        ctx = C.context_enforceable()
        self.assertTrue(0 < len(ctx) < len(C.primitives) // 2)

    def test_adoption_order_floor_first_target_last(self):
        order = C.adoption_order()
        self.assertEqual(order[0], "E1")
        self.assertEqual(sorted(order), sorted(C.ids()))
        self.assertTrue(set(order[-3:]) == {"F1", "F2", "F3"})


class DisclosureHygiene(unittest.TestCase):
    """What the published compass must never carry."""

    def test_no_vendor_names(self):
        import re
        blob = open(os.path.join(DATA_DIR, "compass.json"), encoding="utf-8").read().lower()
        # Assembled from parts so this file does not itself carry the names it screens for.
        names = [a + b for a, b in (("open", "ai"), ("anth", "ropic"), ("me", "tr"), ("gem", "ini"),
                                    ("co", "pilot"), ("chat", "gpt"), ("cla", "ude"), ("lla", "ma"),
                                    ("mis", "tral"))]
        for bad in names:
            self.assertIsNone(re.search("(?<![a-z])" + bad + "(?![a-z])", blob), bad)

    def test_ascii_on_disk(self):
        with open(os.path.join(DATA_DIR, "compass.json"), "rb") as fh:
            self.assertTrue(all(b < 128 for b in fh.read()))

    def test_no_first_person_voice_survives(self):
        for p in C.primitives:
            for k in ("statement", "warrant", "sketch", "adoption"):
                text = str(p[k]).lower()
                self.assertNotIn("my reconstruction", text)
                self.assertNotIn("my reading", text)


@unittest.skipUnless(os.path.isdir(ROOT_COMPASS), "not inside the lab repository")
class InSyncWithRepository(unittest.TestCase):
    """The package carries copies; they must equal the repository's canonical files."""

    def _same(self, a, b):
        with open(a, "rb") as fa, open(b, "rb") as fb:
            self.assertEqual(fa.read().replace(b"\r\n", b"\n"), fb.read().replace(b"\r\n", b"\n"), b)

    def test_compass_json(self):
        self._same(os.path.join(DATA_DIR, "compass.json"), os.path.join(ROOT_COMPASS, "compass.json"))

    def test_compass_schema(self):
        self._same(os.path.join(DATA_DIR, "compass.schema.json"), os.path.join(ROOT_COMPASS, "compass.schema.json"))

    def test_contracts(self):
        for name in CONTRACTS:
            self._same(os.path.join(DATA_DIR, "schemas", name + ".schema.json"),
                       os.path.join(ROOT_COMPASS, "schemas", name + ".schema.json"))

    def test_prompts(self):
        for name in ("compass-system-prompt.md", "compass-agent-addendum.md"):
            self._same(os.path.join(DATA_DIR, "prompts", name), os.path.join(ROOT_COMPASS, "prompts", name))

    def test_docs_catalogue_is_generated_output(self):
        doc = os.path.join(LAB_ROOT, "docs", "PRIMITIVES.md")
        if not os.path.isfile(doc):
            self.skipTest("docs/PRIMITIVES.md not present")
        from compasskit.render import catalogue
        with open(doc, encoding="utf-8") as fh:
            self.assertEqual(fh.read().replace("\r\n", "\n"), catalogue(C),
                             "docs/PRIMITIVES.md drifted; regenerate with: python -m compasskit catalogue --output docs/PRIMITIVES.md")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
