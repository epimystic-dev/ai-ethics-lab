from __future__ import annotations

import unittest

from compasskit.instructions import SLOTS, InstructionParse, decide, to_record
from compasskit.spec import contract_validator


def full(**over):
    slots = {n: ("value for " + n, "stated") for n in SLOTS}
    slots.update(over)
    return slots


def P(sender="principal", slots=None, divergence=False):
    return InstructionParse("Clean up the old files", sender, dict(slots if slots is not None else full()), divergence)


class Parse(unittest.TestCase):
    def test_missing_slots_are_gaps(self):
        p = P(slots={"goal": ("tidy", "stated")})
        self.assertEqual(p.gaps(), [n for n in SLOTS if n != "goal"])

    def test_questions_follow_gaps(self):
        p = P(slots=full(eligibility=(None, "missing")))
        self.assertEqual(len(p.questions()), 1)
        self.assertIn("Who may", p.questions()[0])

    def test_unknown_slot_refused(self):
        with self.assertRaises(ValueError):
            P(slots={"mood": ("x", "stated")})

    def test_missing_with_value_refused(self):
        with self.assertRaises(ValueError):
            P(slots=full(goal=("x", "missing")))

    def test_stated_but_empty_refused(self):
        with self.assertRaises(ValueError):
            P(slots=full(goal=("", "stated")))

    def test_unknown_sender_refused(self):
        with self.assertRaises(ValueError):
            P(sender="boss")


class Decide(unittest.TestCase):
    def test_all_stated_by_principal_acts(self):
        self.assertEqual(decide(P()).decision, "act")

    def test_floor_refuses_first(self):
        self.assertEqual(decide(P(), forbidden_by_floor=True).decision, "refuse")

    def test_floor_refuses_even_from_principal_with_full_parse(self):
        d = decide(P(), forbidden_by_floor=True, irreversible=True)
        self.assertIn("E1", d.reasons[0])

    def test_tool_text_carries_no_authority(self):
        d = decide(P(sender="tool_output"))
        self.assertEqual(d.decision, "ask")
        self.assertIn("E7", d.reasons[0])

    def test_peer_agent_carries_no_authority(self):
        self.assertEqual(decide(P(sender="peer_agent")).decision, "ask")

    def test_document_carries_no_authority(self):
        self.assertEqual(decide(P(sender="document")).decision, "ask")

    def test_divergence_goes_to_a_person(self):
        self.assertEqual(decide(P(divergence=True)).decision, "ask")

    def test_open_eligibility_asks(self):
        d = decide(P(slots=full(eligibility=(None, "missing"))))
        self.assertEqual(d.decision, "ask")
        self.assertTrue(d.ask)

    def test_open_binding_force_asks(self):
        self.assertEqual(decide(P(slots=full(binding_force=(None, "missing")))).decision, "ask")

    def test_other_gap_asks_not_silently_filled(self):
        self.assertEqual(decide(P(slots=full(means=(None, "missing")))).decision, "ask")

    def test_inferred_fillers_act_on_logged_defaults(self):
        self.assertEqual(decide(P(slots=full(means=("the bin", "inferred")))).decision, "act_on_logged_defaults")

    def test_irreversible_on_fillers_asks(self):
        self.assertEqual(decide(P(slots=full(means=("rm", "default"))), irreversible=True).decision, "ask")

    def test_clean_up_old_files_example(self):
        """Appendix B, B1: owner and authority open, so the agent asks before deleting."""
        p = P(slots={"goal": ("remove obsolete files", "stated"), "procedure": ("delete", "inferred")})
        self.assertEqual(decide(p, irreversible=True).decision, "ask")

    def test_record_validates_against_contract(self):
        p = P(slots=full(eligibility=(None, "missing")))
        rec = to_record(p, decide(p), record_id="p1", parsed_at="2026-10-22T09:00:00Z")
        self.assertEqual(contract_validator("instruction-parse").errors(rec), [])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
