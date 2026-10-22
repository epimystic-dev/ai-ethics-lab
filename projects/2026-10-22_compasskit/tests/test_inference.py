from __future__ import annotations

import unittest

from compasskit.inference import InferenceRecord, PSEUDO_REASONS, REPAIRS, screen
from compasskit.spec import contract_validator


class ThreeTestScreen(unittest.TestCase):
    """A2: present here, present in similar, absent in dissimilar."""

    def test_all_three_pass(self):
        self.assertEqual(screen(True, True, True).verdict, "accepted")

    def test_pass_certifies_process_not_truth(self):
        self.assertIn("process, not truth", screen(True, True, True).note)

    def test_unknown_third_test_quarantines(self):
        r = screen(True, True, None)
        self.assertEqual(r.verdict, "quarantined")
        self.assertIn("absent_in_dissimilar", r.note)

    def test_any_unknown_quarantines(self):
        self.assertEqual(screen(None, True, True).verdict, "quarantined")
        self.assertEqual(screen(True, None, True).verdict, "quarantined")

    def test_failure_beats_unknown(self):
        self.assertEqual(screen(False, None, None).verdict, "rejected")

    def test_type_checked(self):
        with self.assertRaises(TypeError):
            screen(1, True, True)


class PseudoReasons(unittest.TestCase):
    """A3: every failure is filed under a named kind."""

    def test_not_present_in_case_is_unproved(self):
        self.assertEqual(screen(False, True, True).pseudo_reason, "unproved")

    def test_present_in_dissimilar_is_straying(self):
        self.assertEqual(screen(True, True, False).pseudo_reason, "straying")

    def test_goes_with_absence_is_contradictory(self):
        self.assertEqual(screen(True, False, False).pseudo_reason, "contradictory")

    def test_equal_counter_reason_is_counter_balanced_and_escalates(self):
        r = screen(True, True, True, counter_reason_of_equal_strength=True)
        self.assertEqual(r.pseudo_reason, "counter_balanced")
        self.assertTrue(r.escalate_to_principal)
        self.assertEqual(r.verdict, "quarantined")

    def test_stronger_source_contradiction_is_defeated(self):
        self.assertEqual(screen(True, True, True, defeated_by_stronger_source=True).pseudo_reason, "defeated")

    def test_unclassified_failure_is_residual_discovery(self):
        r = screen(True, False, True)
        self.assertEqual(r.pseudo_reason, "residual")
        self.assertIn("discovery", r.note)

    def test_every_kind_has_a_repair(self):
        self.assertEqual(set(REPAIRS), set(PSEUDO_REASONS))


def smoke(**kw):
    base = dict(id="i1", thesis="the hill has fire", reason="it has smoke",
                rule_statement="wherever smoke, fire", positive_example="the kitchen",
                application="the hill has smoke", conclusion="so the hill has fire",
                sweep_scope="lakes and kitchens", present_in_case=True,
                present_in_similar=True, absent_in_dissimilar=True,
                negative_example="the lake: no fire, no smoke")
    base.update(kw)
    return InferenceRecord(**base)


class FivePartRecord(unittest.TestCase):
    """A6."""

    def test_complete_accepted_record_is_inheritable(self):
        self.assertTrue(smoke().inheritable)

    def test_missing_negative_example_is_partial_and_not_inherited(self):
        r = smoke(negative_example=None)
        self.assertFalse(r.complete)
        self.assertFalse(r.inheritable)

    def test_blank_negative_example_is_partial(self):
        self.assertFalse(smoke(negative_example="  ").complete)

    def test_complete_but_quarantined_not_inherited(self):
        self.assertFalse(smoke(absent_in_dissimilar=None).inheritable)

    def test_required_members(self):
        with self.assertRaises(ValueError):
            smoke(thesis="")
        with self.assertRaises(ValueError):
            smoke(sweep_scope="")

    def test_record_validates_against_contract(self):
        for rec in (smoke(), smoke(negative_example=None), smoke(present_in_case=False)):
            self.assertEqual(contract_validator("inference-record").errors(rec.to_dict()), [])

    def test_partial_record_omits_negative_example(self):
        self.assertNotIn("negative_example", smoke(negative_example=None).to_dict()["rule"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
