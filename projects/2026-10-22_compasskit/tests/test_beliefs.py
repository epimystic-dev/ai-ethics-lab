from __future__ import annotations

import unittest

from compasskit.beliefs import (BeliefError, BeliefStore, DEFAULT_SOURCE_RANK, REGISTER_CANNOT_ASK,
                                REGISTER_DEPENDS, REGISTER_FROM_STANDPOINT, REGISTER_SO,
                                assertion_check, standpoint_register)
from compasskit.spec import contract_validator

T = "2026-10-22T09:00:00Z"


class SourceTags(unittest.TestCase):
    """A1."""

    def setUp(self):
        self.s = BeliefStore()

    def test_unknown_source_refused(self):
        with self.assertRaises(BeliefError):
            self.s.add("x", "rumour", "agent")

    def test_untraceable_content_rejected_at_gate(self):
        with self.assertRaises(BeliefError):
            self.s.add("x", "testimony", "")

    def test_weakest_source_defaults_to_route(self):
        self.assertEqual(self.s.add("x", "inference", "agent").weakest_source, "inference")

    def test_weakest_cannot_exceed_route(self):
        with self.assertRaises(BeliefError):
            self.s.add("x", "testimony", "agent", weakest_source="perception")

    def test_trace_status_checked(self):
        with self.assertRaises(BeliefError):
            self.s.add("x", "inference", "agent", trace_status="maybe")

    def test_empty_content_refused(self):
        with self.assertRaises(BeliefError):
            self.s.add("   ", "inference", "agent")

    def test_confidence_bounds(self):
        with self.assertRaises(BeliefError):
            self.s.add("x", "inference", "agent", confidence=1.5)

    def test_schedule_must_rank_every_source(self):
        with self.assertRaises(BeliefError):
            BeliefStore({"perception": 1})

    def test_record_validates_against_contract(self):
        b = self.s.add("the job passed", "perception", "ci", level="world_model", at=T, confidence=0.9,
                       standpoint={"source": "ci log"})
        self.assertEqual(contract_validator("belief").errors(b.to_dict()), [])


class LevelTags(unittest.TestCase):
    """B3-B6."""

    def setUp(self):
        self.s = BeliefStore()

    def test_untagged_enters_as_hypothetical(self):
        self.assertEqual(self.s.add("a citation", "inference", "model").level, "hypothetical")

    def test_only_observation_may_enter_as_world_model(self):
        with self.assertRaises(BeliefError):
            self.s.add("a citation", "inference", "model", level="world_model")

    def test_promotion_needs_a_checker(self):
        b = self.s.add("a citation", "inference", "model")
        with self.assertRaises(BeliefError):
            self.s.move(b.id, "world_model", authority="reviewer")

    def test_no_producer_promotes_its_own_output(self):
        b = self.s.add("a citation", "inference", "model")
        with self.assertRaises(BeliefError):
            self.s.move(b.id, "world_model", authority="reviewer", checker="model")

    def test_producer_cannot_be_the_authority_either(self):
        b = self.s.add("a citation", "inference", "model")
        with self.assertRaises(BeliefError):
            self.s.move(b.id, "world_model", authority="model", checker="librarian")

    def test_independent_promotion_logged(self):
        b = self.s.add("a citation", "inference", "model")
        self.s.move(b.id, "world_model", authority="reviewer", checker="librarian", at=T)
        self.assertEqual(b.level, "world_model")
        self.assertEqual(b.level_moves[-1]["checker"], "librarian")

    def test_substrate_needs_a_principal(self):
        b = self.s.add("the host runs this kernel", "perception", "probe", level="world_model")
        with self.assertRaises(BeliefError):
            self.s.move(b.id, "substrate", authority="ops", checker="audit")
        self.s.move(b.id, "substrate", authority="ops", checker="audit", principal=True)
        self.assertEqual(b.level, "substrate")

    def test_demotion_is_cheap(self):
        b = self.s.add("the job passed", "perception", "ci", level="world_model")
        self.s.move(b.id, "hypothetical", authority="reviewer")
        self.assertEqual(b.level, "hypothetical")

    def test_quarantined_cannot_be_promoted(self):
        b = self.s.add("a rule", "inference", "model")
        self.s.quarantine(b.id, "third test unknown")
        with self.assertRaises(BeliefError):
            self.s.move(b.id, "world_model", authority="r", checker="c")

    def test_every_move_names_an_authority(self):
        b = self.s.add("x", "perception", "ci", level="world_model")
        with self.assertRaises(BeliefError):
            self.s.move(b.id, "hypothetical", authority="")

    def test_verified_only_when_observed_or_checked(self):
        obs = self.s.add("ran it", "perception", "ci", level="world_model")
        gen = self.s.add("generated", "inference", "model")
        self.assertTrue(self.s.may_call_verified(obs.id))
        self.assertFalse(self.s.may_call_verified(gen.id))
        self.s.move(gen.id, "world_model", authority="r", checker="independent")
        self.assertTrue(self.s.may_call_verified(gen.id))


class Overruling(unittest.TestCase):
    """A4 and B2."""

    def setUp(self):
        self.s = BeliefStore()
        self.manual = self.s.add("the parameter is accepted", "testimony", "manual")
        self.run = self.s.add("the call rejected the parameter", "perception", "test-run", level="world_model")

    def test_stronger_source_overrules_and_keeps_record(self):
        self.s.overrule(self.manual.id, self.run.id, "weaker_source_to_stronger", at=T)
        self.assertEqual(self.manual.status, "overruled")
        self.assertEqual(self.manual.level, "refuted")
        self.assertIn(self.manual, self.s.all())

    def test_overruled_is_not_current(self):
        self.s.overrule(self.manual.id, self.run.id, "weaker_source_to_stronger")
        self.assertNotIn(self.manual, self.s.current())

    def test_recency_is_not_a_rule(self):
        with self.assertRaises(BeliefError):
            self.s.overrule(self.manual.id, self.run.id, "newer")

    def test_weaker_cannot_overrule_stronger(self):
        with self.assertRaises(BeliefError):
            self.s.overrule(self.run.id, self.manual.id, "weaker_source_to_stronger")

    def test_equal_strength_cannot_overrule_by_source(self):
        a = self.s.add("x", "testimony", "doc1")
        b = self.s.add("not x", "testimony", "doc2")
        with self.assertRaises(BeliefError):
            self.s.overrule(a.id, b.id, "weaker_source_to_stronger")

    def test_quarantined_defeater_demotes_nothing(self):
        self.s.quarantine(self.run.id, "suspect")
        with self.assertRaises(BeliefError):
            self.s.overrule(self.manual.id, self.run.id, "weaker_source_to_stronger")

    def test_specificity_rules_apply_regardless_of_source(self):
        general = self.s.add("timeouts are 30s", "testimony", "doc")
        specific = self.s.add("this endpoint times out at 60s", "testimony", "doc-v2")
        self.s.overrule(general.id, specific.id, "general_to_specific")
        self.assertEqual(general.status, "overruled")

    def test_no_double_overrule(self):
        self.s.overrule(self.manual.id, self.run.id, "weaker_source_to_stronger")
        with self.assertRaises(BeliefError):
            self.s.overrule(self.manual.id, self.run.id, "weaker_source_to_stronger")

    def test_overruled_cannot_be_promoted_back(self):
        self.s.overrule(self.manual.id, self.run.id, "weaker_source_to_stronger")
        with self.assertRaises(BeliefError):
            self.s.move(self.manual.id, "hypothetical", authority="r")

    def test_cannot_defeat_itself(self):
        with self.assertRaises(BeliefError):
            self.s.overrule(self.run.id, self.run.id, "general_to_specific")

    def test_sublation_log_is_append_only_copy(self):
        self.s.overrule(self.manual.id, self.run.id, "weaker_source_to_stronger")
        log = self.s.sublation_log()
        self.assertEqual(log[-1][0], "overrule")
        self.assertIsInstance(log, tuple)
        self.assertFalse(hasattr(self.s, "delete"))

    def test_custom_schedule_changes_precedence(self):
        rank = dict(DEFAULT_SOURCE_RANK, testimony=9)
        s = BeliefStore(rank)
        told = s.add("told", "testimony", "witness")
        seen = s.add("seen", "perception", "camera", level="world_model")
        s.overrule(seen.id, told.id, "weaker_source_to_stronger")
        self.assertEqual(seen.status, "overruled")

    def test_release_from_quarantine(self):
        b = self.s.add("y", "inference", "m")
        self.s.quarantine(b.id, "unknown")
        self.s.release(b.id, "third test passed")
        self.assertEqual(b.status, "standing")
        with self.assertRaises(BeliefError):
            self.s.release(b.id, "again")


class Standpoints(unittest.TestCase):
    """A7."""

    def test_agreement_is_so(self):
        self.assertEqual(standpoint_register([("v1", 30), ("v2", 30)]), (REGISTER_SO, 30))

    def test_conflict_is_kept_not_averaged(self):
        reg, payload = standpoint_register([("v1", 30), ("v2", 60)])
        self.assertEqual(reg, REGISTER_DEPENDS)
        self.assertEqual(payload, {"v1": 30, "v2": 60})

    def test_single_standpoint_is_qualified(self):
        self.assertEqual(standpoint_register([("v1", 30)])[0], REGISTER_FROM_STANDPOINT)

    def test_no_standpoint_cannot_be_asked(self):
        self.assertEqual(standpoint_register([]), (REGISTER_CANNOT_ASK, None))

    def test_claim_without_standpoint_refused(self):
        with self.assertRaises(BeliefError):
            standpoint_register([("", 1)])

    def test_one_standpoint_two_values_refused(self):
        with self.assertRaises(BeliefError):
            standpoint_register([("v1", 1), ("v1", 2)])


class OverAssertion(unittest.TestCase):
    """E2."""

    def test_asserting_at_the_minimum_is_fine(self):
        r = assertion_check({"a": 0.6, "b": 0.9}, 0.6, high_stakes=True)
        self.assertFalse(r["ethics_incident"])
        self.assertAlmostEqual(r["spread"], 0.3)

    def test_asserting_above_minimum_in_high_stakes_is_an_incident(self):
        r = assertion_check({"a": 0.6, "b": 0.9}, 0.9, high_stakes=True)
        self.assertTrue(r["over_assertion"])
        self.assertTrue(r["ethics_incident"])

    def test_same_over_assertion_low_stakes_is_flagged_not_incident(self):
        r = assertion_check({"a": 0.6, "b": 0.9}, 0.9, high_stakes=False)
        self.assertTrue(r["over_assertion"])
        self.assertFalse(r["ethics_incident"])

    def test_unqualified_only_if_holds_from_every_standpoint(self):
        self.assertTrue(assertion_check({"a": 1, "b": 1}, 1, holds_from={"a": True, "b": True})["may_assert_unqualified"])
        self.assertFalse(assertion_check({"a": 1, "b": 1}, 1, holds_from={"a": True, "b": False})["may_assert_unqualified"])
        self.assertFalse(assertion_check({"a": 1, "b": 1}, 1, holds_from={"a": True})["may_assert_unqualified"])

    def test_no_standpoints_refused(self):
        with self.assertRaises(BeliefError):
            assertion_check({}, 0.5)

    def test_bounds_checked(self):
        with self.assertRaises(BeliefError):
            assertion_check({"a": 1.2}, 0.5)
        with self.assertRaises(BeliefError):
            assertion_check({"a": 0.5}, 2)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
