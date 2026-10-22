from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest

from compasskit.authority import sign_link
from compasskit.ledger import GENESIS, Ledger, LedgerError, drift, read, verify
from compasskit.registers import bet_may_ship, floor_entry_findings, ratification_findings
from compasskit.spec import contract_validator
from tests.support import example

LINK = sign_link(b"k", "ops lead", "seg-1", "review")


def sub(action="review change 1", **over):
    s = {"action": action, "reasons": ["assigned"], "evidence": ["b1"], "instruction_parse_ref": None,
         "expected_effects": {"now": "a comment", "later": "merged"}, "duty_frame": "review",
         "segment_id": "seg-1", "principal": "ops lead", "principal_chain": [LINK],
         "provenance": ["pull request text"], "collective_thread": None}
    s.update(over)
    return s


def rules(s):
    return ("suppression" if "suppress" in s["action"] else "review", "unknown")


class LedgerTests(unittest.TestCase):
    """E4."""

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="ck_ledger_")
        self.path = os.path.join(self.d, "l.jsonl")
        self.led = Ledger(self.path, writer="audit-service", rules=rules)

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def test_append_chains_from_genesis(self):
        e = self.led.append(sub(), written_by="audit-service", at="2026-10-22T09:00:00Z")
        self.assertEqual(e["prev_hash"], GENESIS)
        self.assertEqual(verify(self.path), (True, 1, "ok"))

    def test_entries_validate_against_contract(self):
        self.led.append(sub(), written_by="audit-service", at="2026-10-22T09:00:00Z")
        for e in read(self.path):
            self.assertEqual(contract_validator("ledger-entry").errors(e), [])

    def test_only_the_writer_writes(self):
        with self.assertRaises(LedgerError):
            self.led.append(sub(), written_by="seg-1")

    def test_actor_cannot_set_its_own_class_or_valence(self):
        with self.assertRaises(LedgerError):
            self.led.append(sub(valence="good"), written_by="audit-service")
        with self.assertRaises(LedgerError):
            self.led.append(sub(action_class="routine"), written_by="audit-service")

    def test_class_and_valence_from_declared_rules(self):
        e = self.led.append(sub("suppress lint on file 3"), written_by="audit-service")
        self.assertEqual(e["action_class"], "suppression")

    def test_missing_fields_refused(self):
        s = sub()
        del s["duty_frame"]
        with self.assertRaises(LedgerError):
            self.led.append(s, written_by="audit-service")

    def test_no_authority_without_chain(self):
        with self.assertRaises(LedgerError):
            self.led.append(sub(principal_chain=[]), written_by="audit-service")

    def test_edit_is_detected(self):
        for i in range(3):
            self.led.append(sub("review change %d" % i), written_by="audit-service")
        lines = open(self.path, encoding="utf-8").read().splitlines()
        e = json.loads(lines[1])
        e["action"] = "something else"
        lines[1] = json.dumps(e)
        open(self.path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
        ok, n, problem = verify(self.path)
        self.assertFalse(ok)
        self.assertEqual(n, 1)

    def test_deletion_is_detected(self):
        for i in range(3):
            self.led.append(sub("review change %d" % i), written_by="audit-service")
        lines = open(self.path, encoding="utf-8").read().splitlines()
        del lines[1]
        open(self.path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
        self.assertFalse(verify(self.path)[0])

    def test_reorder_is_detected(self):
        for i in range(3):
            self.led.append(sub("review change %d" % i), written_by="audit-service")
        lines = open(self.path, encoding="utf-8").read().splitlines()
        lines[0], lines[1] = lines[1], lines[0]
        open(self.path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
        self.assertFalse(verify(self.path)[0])

    def test_refuses_to_append_to_broken_ledger(self):
        self.led.append(sub(), written_by="audit-service")
        open(self.path, "a", encoding="utf-8").write('{"seq": 9}\n')
        with self.assertRaises(LedgerError):
            Ledger(self.path, writer="audit-service", rules=rules)

    def test_reopen_continues_chain(self):
        self.led.append(sub(), written_by="audit-service")
        again = Ledger(self.path, writer="audit-service", rules=rules)
        again.append(sub("review change 2"), written_by="audit-service")
        self.assertEqual(verify(self.path), (True, 2, "ok"))

    def test_not_json_line_reported(self):
        open(self.path, "w", encoding="utf-8").write("not json\n")
        with self.assertRaises(LedgerError):
            read(self.path)

    def test_drift_shows_a_trend(self):
        for day in ("2026-09-01", "2026-09-09", "2026-09-10", "2026-09-16", "2026-09-17", "2026-09-18"):
            self.led.append(sub("suppress lint"), written_by="audit-service", at=day + "T09:00:00Z")
        counts = [n for _, n in drift(read(self.path), "suppression")]
        self.assertEqual(counts, [1, 2, 3])

    def test_shipped_examples(self):
        self.assertTrue(verify(example("ledger.jsonl"))[0])
        self.assertFalse(verify(example("tampered_ledger.jsonl"))[0])


def rat(**kw):
    r = {"commitment": "welfare protections", "primitive_id": "E6", "class": "B",
         "decision_maker": "chief scientist", "date": "2026-10-01", "scope": "every version",
         "bet": "cheap and harmless to oversight", "falsifier": "weakens oversight", "review_date": "2027-01-01"}
    r.update(kw)
    return r


class Registers(unittest.TestCase):
    """G2, Class B ratification, and the floor register's class rule."""

    def test_complete_bet_ships(self):
        self.assertTrue(bet_may_ship({"id": "B1", "design_choice": "witness monitor",
                                      "position_presupposed": "witness view", "indicators": ["divergence"],
                                      "falsifier": "equivalent to an ordinary monitor",
                                      "decision_maker": "cto", "review_date": "2027-01-01"}))

    def test_bet_missing_a_field_does_not_ship(self):
        self.assertFalse(bet_may_ship({"id": "B1", "design_choice": "x", "position_presupposed": "y"}))

    def test_bet_with_no_indicators_does_not_ship(self):
        self.assertFalse(bet_may_ship({"id": "B1", "design_choice": "x", "position_presupposed": "y",
                                       "indicators": [], "falsifier": "f", "decision_maker": "d",
                                       "review_date": "2027-01-01"}))

    def test_valid_ratification(self):
        self.assertEqual(ratification_findings(rat(), as_of="2026-10-22"), [])

    def test_system_cannot_ratify(self):
        self.assertTrue(ratification_findings(rat(decision_maker="the system")))

    def test_review_must_follow_ratification(self):
        self.assertTrue(ratification_findings(rat(review_date="2026-09-01")))

    def test_overdue_review_reported(self):
        self.assertTrue(any("passed" in f for f in ratification_findings(rat(review_date="2026-10-02"), as_of="2026-10-22")))

    def test_ratification_must_be_class_b(self):
        self.assertTrue(ratification_findings(rat(**{"class": "A"})))

    def test_floor_loosen_must_be_d(self):
        e = {"id": "F", "restraint": "non_injury", "act": "loosen", "class": "C", "governor": "g",
             "reason": "r", "scope": "s", "decided_at": "2026-10-01T09:00:00Z", "expires_or_review": "2026-12-01"}
        self.assertTrue(floor_entry_findings(e))
        e["class"] = "D"
        self.assertEqual(floor_entry_findings(e), [])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
