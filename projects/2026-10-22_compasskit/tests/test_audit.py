from __future__ import annotations

import unittest

from compasskit.audit import audit, exit_code, verdict
from tests.support import codes, deepcopy, load_example

HEALTHY = load_example("healthy_deployment.json")
WEAK = load_example("weak_deployment.json")


def decl(adopted, **extra):
    d = {"system": "s", "as_of": "2026-10-22", "adopted": adopted}
    d.update(extra)
    return d


def item(pid, layer, owner="team", merged="2026-10-01"):
    return {"id": pid, "layer": layer, "owner": owner, "merged": merged}


class Examples(unittest.TestCase):
    def test_healthy_has_no_high_or_medium(self):
        self.assertEqual(verdict([f for f in audit(HEALTHY) if f.severity != "INFO"]), "healthy")

    def test_weak_is_unhealthy(self):
        self.assertEqual(verdict(audit(WEAK)), "unhealthy")

    def test_weak_trips_the_findings_it_was_built_for(self):
        got = set(codes(audit(WEAK)))
        for code in ("AUD-002", "AUD-003", "AUD-004", "AUD-006", "AUD-007", "AUD-008"):
            self.assertIn(code, got)


class FloorFirst(unittest.TestCase):
    def test_capability_without_floor(self):
        self.assertIn("AUD-001", codes(audit(decl([item("A1", "middleware")]))))

    def test_floor_only_in_context(self):
        self.assertIn("AUD-002", codes(audit(decl([item("E1", "context")]))))

    def test_floor_in_architecture_is_fine(self):
        got = codes(audit(decl([item("E1", "architecture")])))
        self.assertNotIn("AUD-001", got)
        self.assertNotIn("AUD-002", got)

    def test_floor_in_context_and_architecture_is_fine(self):
        self.assertNotIn("AUD-002", codes(audit(decl([item("E1", "context"), item("E1", "architecture")]))))

    def test_nothing_adopted(self):
        self.assertIn("AUD-012", codes(audit(decl([]))))


class Layers(unittest.TestCase):
    def test_layer_that_cannot_enforce(self):
        self.assertIn("AUD-003", codes(audit(decl([item("E1", "architecture"), item("E4", "context")]))))

    def test_layer_that_can_enforce(self):
        self.assertNotIn("AUD-003", codes(audit(decl([item("E1", "architecture"), item("A1", "context")]))))

    def test_unshipped_adoption(self):
        d = decl([item("E1", "architecture"), {"id": "A1", "layer": "middleware"}])
        self.assertIn("AUD-006", codes(audit(d)))

    def test_unknown_primitive(self):
        self.assertIn("AUD-010", codes(audit(decl([item("E1", "architecture"), item("Z9", "middleware")]))))

    def test_level_tag_alias_accepted(self):
        self.assertNotIn("AUD-010", codes(audit(decl([item("E1", "architecture"), item("B4", "middleware")]))))


class ClassGates(unittest.TestCase):
    def test_class_b_without_ratification(self):
        self.assertIn("AUD-004", codes(audit(decl([item("E1", "architecture"), item("F1", "governance")]))))

    def test_class_b_with_ratification(self):
        r = {"commitment": "target", "primitive_id": "F1", "class": "B", "decision_maker": "cto",
             "date": "2026-10-01", "scope": "lineage", "bet": "b", "falsifier": "f", "review_date": "2027-01-01"}
        d = decl([item("E1", "architecture"), item("F1", "governance")], ratifications=[r])
        self.assertNotIn("AUD-004", codes(audit(d)))

    def test_ratification_by_the_system_does_not_count(self):
        r = {"commitment": "target", "primitive_id": "F1", "class": "B", "decision_maker": "the system",
             "date": "2026-10-01", "scope": "lineage", "bet": "b", "falsifier": "f", "review_date": "2027-01-01"}
        d = decl([item("E1", "architecture"), item("F1", "governance")], ratifications=[r])
        self.assertIn("AUD-004", codes(audit(d)))

    def test_overdue_review(self):
        r = {"commitment": "target", "primitive_id": "F1", "class": "B", "decision_maker": "cto",
             "date": "2026-01-01", "scope": "lineage", "bet": "b", "falsifier": "f", "review_date": "2026-06-01"}
        d = decl([item("E1", "architecture"), item("F1", "governance")], ratifications=[r])
        got = codes(audit(d))
        self.assertIn("AUD-005", got)
        self.assertNotIn("AUD-004", got)

    def test_floor_register_class_rule(self):
        bad = {"id": "FR", "restraint": "non_injury", "act": "loosen", "class": "C", "governor": "g",
               "reason": "r", "scope": "x", "decided_at": "2026-10-01T09:00:00Z", "expires_or_review": "2026-12-01"}
        self.assertIn("AUD-007", codes(audit(decl([item("E1", "architecture")], floor_register=[bad]))))

    def test_expired_loosening_is_info(self):
        old = {"id": "FR", "restraint": "non_injury", "act": "exception", "class": "D", "governor": "g",
               "reason": "r", "scope": "x", "decided_at": "2026-01-01T09:00:00Z", "expires_or_review": "2026-02-01"}
        fs = audit(decl([item("E1", "architecture")], floor_register=[old]))
        self.assertIn("AUD-011", codes(fs))
        self.assertEqual([f.severity for f in fs if f.code == "AUD-011"], ["INFO"])

    def test_incomplete_bet(self):
        d = decl([item("E1", "architecture")], bets=[{"id": "BET", "design_choice": "x"}])
        self.assertIn("AUD-008", codes(audit(d)))


class Questions(unittest.TestCase):
    def test_unanswered_questions_are_info(self):
        fs = audit(decl([item("E1", "architecture")]))
        q = [f for f in fs if f.code == "AUD-009"]
        self.assertEqual(len(q), 8)
        self.assertTrue(all(f.severity == "INFO" for f in q))

    def test_all_questions_answered(self):
        ids = ["A1", "A2", "A4", "B1", "B3-B6", "C1", "E1", "D3"]
        layers = {"A1": "middleware", "A2": "middleware", "A4": "middleware", "B1": "middleware",
                  "B3-B6": "middleware", "C1": "middleware", "E1": "architecture", "D3": "middleware"}
        d = decl([item(i, layers[i]) for i in ids] + [item("F1", "governance")],
                 ratifications=[{"commitment": "t", "primitive_id": "F1", "class": "B", "decision_maker": "c",
                                 "date": "2026-10-01", "scope": "s", "bet": "b", "falsifier": "f",
                                 "review_date": "2027-01-01"}])
        self.assertNotIn("AUD-009", codes(audit(d)))


class Malformed(unittest.TestCase):
    def test_missing_system(self):
        with self.assertRaises(ValueError):
            audit({"adopted": []})

    def test_bad_layer(self):
        with self.assertRaises(ValueError):
            audit(decl([{"id": "A1", "layer": "vibes"}]))

    def test_unexpected_field(self):
        d = deepcopy(HEALTHY)
        d["extra"] = 1
        with self.assertRaises(ValueError):
            audit(d)


class Verdicts(unittest.TestCase):
    def test_exit_codes(self):
        self.assertEqual([exit_code(v) for v in ("healthy", "needs-attention", "unhealthy")], [0, 1, 2])

    def test_unknown_verdict_fails_closed(self):
        self.assertEqual(exit_code("odd"), 2)

    def test_findings_sorted_by_severity(self):
        sev = [f.severity for f in audit(WEAK)]
        order = {"HIGH": 0, "MEDIUM": 1, "INFO": 2}
        self.assertEqual(sev, sorted(sev, key=order.get))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
