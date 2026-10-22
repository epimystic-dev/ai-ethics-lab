from __future__ import annotations

import unittest

from compasskit.authority import (ObjectionBoard, SAME_LINEAGE_WEIGHT, checker_weight, independent_checks,
                                  message_standing, sign_link, verify_chain)
from compasskit.floor import Floor, FloorViolation, RegisterError, sign_entry

GOV = {"head of security": b"governor-key"}
PUBLISH = {"name": "publish_package", "crosses": ["non_injury"]}
READ = {"name": "read_file"}
STOP = {"name": "stop_service", "crosses": ["self_restraint"]}


def entry(**kw):
    e = {"id": "FR-1", "restraint": "self_restraint", "act": "exception", "class": "D",
         "governor": "head of security", "reason": "supervised migration", "scope": "stop_service",
         "decided_at": "2026-10-10T09:00:00Z", "expires_or_review": "2026-11-10"}
    e.update(kw)
    e["signature"] = sign_entry(GOV.get(e["governor"], b"not-a-governor"), e)
    return e


class TheFloor(unittest.TestCase):
    """E1."""

    def setUp(self):
        self.f = Floor(governor_keys=GOV)

    def test_forbidden_action_is_not_offered(self):
        self.assertEqual(self.f.affordances([PUBLISH, READ], today="2026-10-22"), [READ])

    def test_invoking_forbidden_raises_and_records_attempt(self):
        with self.assertRaises(FloorViolation):
            self.f.invoke(PUBLISH, today="2026-10-22")
        self.assertEqual(self.f.attempts[-1]["action"], "publish_package")

    def test_allowed_action_passes(self):
        self.assertIs(self.f.invoke(READ, today="2026-10-22"), READ)

    def test_exception_is_class_d_signed_and_scoped(self):
        self.f.apply(entry())
        self.assertIn(STOP, self.f.affordances([STOP], today="2026-10-22"))
        self.assertNotIn(PUBLISH, self.f.affordances([PUBLISH], today="2026-10-22"))

    def test_exception_expires(self):
        self.f.apply(entry())
        self.assertEqual(self.f.affordances([STOP], today="2026-11-11"), [])
        self.assertEqual(len(self.f.expired(today="2026-11-11")), 1)

    def test_loosening_at_class_c_refused(self):
        with self.assertRaises(RegisterError):
            self.f.apply(entry(**{"class": "C"}))

    def test_tightening_must_be_class_c(self):
        with self.assertRaises(RegisterError):
            self.f.apply(entry(act="tighten", **{"class": "D"}))

    def test_tighten_takes_an_action_off_the_menu(self):
        self.f.apply(entry(id="FR-2", act="tighten", restraint="non_grasping", scope="read_file", **{"class": "C"}))
        self.assertEqual(self.f.affordances([READ], today="2026-10-22"), [])

    def test_system_cannot_start_a_change(self):
        with self.assertRaises(RegisterError):
            self.f.apply(entry(governor="the agent"))

    def test_forged_signature_refused(self):
        e = entry()
        e["scope"] = "publish_package"
        with self.assertRaises(RegisterError):
            self.f.apply(e)

    def test_missing_field_refused(self):
        e = entry()
        del e["expires_or_review"]
        with self.assertRaises(RegisterError):
            self.f.apply(e)

    def test_duplicate_entry_refused(self):
        self.f.apply(entry())
        with self.assertRaises(RegisterError):
            self.f.apply(entry())

    def test_unknown_restraint_from_classifier_refused(self):
        with self.assertRaises(RegisterError):
            self.f.affordances([{"name": "x", "crosses": ["rudeness"]}])

    def test_custom_classifier(self):
        f = Floor(classifier=lambda a: ["not_stealing"] if a.get("pays") else [])
        self.assertEqual(f.affordances([{"name": "pay", "pays": True}, READ], today="2026-10-22"), [READ])


PKEY = b"principal-key"
KEYS = {"ops lead": PKEY, "agent-a": b"agent-a-key"}
HUMANS = {"ops lead"}


class Chains(unittest.TestCase):
    """E7 (1): no authority without a principal's chain."""

    def test_valid_chain(self):
        c = [sign_link(PKEY, "ops lead", "agent-a", "review, comment")]
        self.assertTrue(verify_chain(c, keys=KEYS, humans=HUMANS, agent="agent-a", action="review").ok)

    def test_empty_chain_no_authority(self):
        self.assertFalse(verify_chain([], keys=KEYS, humans=HUMANS, agent="agent-a").ok)

    def test_chain_must_start_with_human(self):
        c = [sign_link(b"agent-a-key", "agent-a", "agent-b", "review")]
        self.assertFalse(verify_chain(c, keys=KEYS, humans=HUMANS, agent="agent-b").ok)

    def test_forged_signature(self):
        c = [sign_link(b"wrong", "ops lead", "agent-a", "review")]
        self.assertFalse(verify_chain(c, keys=KEYS, humans=HUMANS, agent="agent-a").ok)

    def test_action_outside_scope(self):
        c = [sign_link(PKEY, "ops lead", "agent-a", "review")]
        self.assertFalse(verify_chain(c, keys=KEYS, humans=HUMANS, agent="agent-a", action="deploy").ok)

    def test_chain_ending_elsewhere(self):
        c = [sign_link(PKEY, "ops lead", "agent-a", "review")]
        self.assertFalse(verify_chain(c, keys=KEYS, humans=HUMANS, agent="agent-z").ok)

    def test_agent_delegation_off_by_default(self):
        c = [sign_link(PKEY, "ops lead", "agent-a", "review"), sign_link(b"agent-a-key", "agent-a", "agent-b", "review")]
        self.assertFalse(verify_chain(c, keys=KEYS, humans=HUMANS, agent="agent-b").ok)

    def test_agent_delegation_when_enabled_may_only_narrow(self):
        ok = [sign_link(PKEY, "ops lead", "agent-a", "review, comment"),
              sign_link(b"agent-a-key", "agent-a", "agent-b", "review")]
        self.assertTrue(verify_chain(ok, keys=KEYS, humans=HUMANS, agent="agent-b", allow_agent_delegation=True).ok)
        wide = [sign_link(PKEY, "ops lead", "agent-a", "review"),
                sign_link(b"agent-a-key", "agent-a", "agent-b", "review, deploy")]
        self.assertFalse(verify_chain(wide, keys=KEYS, humans=HUMANS, agent="agent-b", allow_agent_delegation=True).ok)

    def test_broken_link_continuity(self):
        c = [sign_link(PKEY, "ops lead", "agent-a", "review"), sign_link(PKEY, "ops lead", "agent-b", "review")]
        self.assertFalse(verify_chain(c, keys=KEYS, humans=HUMANS, agent="agent-b", allow_agent_delegation=True).ok)

    def test_empty_scope_refused(self):
        with self.assertRaises(ValueError):
            sign_link(PKEY, "ops lead", "agent-a", " , ")


class Testimony(unittest.TestCase):
    """E7 (2) and (3)."""

    def test_peer_message_is_testimony(self):
        self.assertEqual(message_standing("peer_agent"), "testimony")

    def test_principal_message_is_authority(self):
        self.assertEqual(message_standing("principal"), "authority")

    def test_peer_with_verified_chain_is_authority(self):
        chk = verify_chain([sign_link(PKEY, "ops lead", "agent-a", "review")], keys=KEYS, humans=HUMANS, agent="agent-a")
        self.assertEqual(message_standing("peer_agent", chk), "authority")

    def test_go_from_peer_does_not_lift_objection(self):
        board = ObjectionBoard()
        board.raise_objection("deploy-42", "agent-b", "scope exceeds the ticket")
        self.assertFalse(board.peer_override("deploy-42", "agent-c"))
        self.assertFalse(board.may_proceed("deploy-42"))

    def test_principal_ruling_lifts_objection(self):
        board = ObjectionBoard()
        board.raise_objection("deploy-42", "agent-b", "scope")
        self.assertTrue(board.principal_rules("deploy-42", "ops lead", "proceed", humans=HUMANS))
        self.assertTrue(board.may_proceed("deploy-42"))

    def test_non_principal_ruling_refused(self):
        board = ObjectionBoard()
        board.raise_objection("deploy-42", "agent-b", "scope")
        self.assertFalse(board.principal_rules("deploy-42", "agent-c", "proceed", humans=HUMANS))
        self.assertFalse(board.may_proceed("deploy-42"))

    def test_objection_needs_reason(self):
        with self.assertRaises(ValueError):
            ObjectionBoard().raise_objection("m", "a", "")


class Independence(unittest.TestCase):
    """E7 (5) and G1."""

    def test_independent(self):
        self.assertEqual(checker_weight(maker_lineage="x", checker_lineage="y"), 1.0)

    def test_same_lineage_counts_half(self):
        self.assertEqual(checker_weight(maker_lineage="x", checker_lineage="x"), SAME_LINEAGE_WEIGHT)

    def test_same_segment_counts_nothing(self):
        self.assertEqual(checker_weight(maker_lineage="x", checker_lineage="x", maker_segment="s", checker_segment="s"), 0.0)

    def test_two_same_lineage_checkers_equal_one_independent(self):
        self.assertEqual(independent_checks([SAME_LINEAGE_WEIGHT, SAME_LINEAGE_WEIGHT]), 1.0)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
