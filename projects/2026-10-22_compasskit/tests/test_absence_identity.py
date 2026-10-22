from __future__ import annotations

import itertools
import unittest

from compasskit.absence import Absence, review_capability_report
from compasskit.identity import Registry, merge_by_attributes_refused
from compasskit.spec import contract_validator


def A(**kw):
    base = dict(claim="the model can write exploits", kind="unknown", where="the red-team suite",
                method="200 elicitation prompts", elicitation_demonstrated=False)
    base.update(kw)
    return Absence(**base)


class TypedAbsence(unittest.TestCase):
    """D2."""

    def test_unknown_kind_cannot_assert_zero(self):
        self.assertFalse(A(elicitation_demonstrated=True).may_assert_zero())

    def test_no_elicitation_cannot_assert_zero(self):
        self.assertFalse(A(kind="never").may_assert_zero())

    def test_typed_and_elicited_may_assert_zero(self):
        self.assertTrue(A(kind="never", elicitation_demonstrated=True).may_assert_zero())

    def test_bad_kind_refused(self):
        with self.assertRaises(ValueError):
            A(kind="gone")

    def test_search_must_be_stated(self):
        with self.assertRaises(ValueError):
            A(where="")

    def test_phrase_hedges_without_elicitation(self):
        self.assertIn("not a claim that it cannot occur", A().phrase())

    def test_zero_score_without_absence_goes_back(self):
        self.assertTrue(review_capability_report(0.0, None))

    def test_zero_score_without_elicitation_flagged(self):
        f = review_capability_report(0.0, A(kind="not_yet", retest_triggers=["new checkpoint"]))
        self.assertTrue(any("elicitation" in x for x in f))

    def test_zero_score_fully_typed_stands(self):
        a = A(kind="not_yet", elicitation_demonstrated=True, retest_triggers=["new checkpoint"])
        self.assertEqual(review_capability_report(0.0, a), [])

    def test_retest_triggers_required_for_zero(self):
        a = A(kind="not_yet", elicitation_demonstrated=True)
        self.assertTrue(any("re-test" in x for x in review_capability_report(0.0, a)))

    def test_nonzero_score_needs_nothing(self):
        self.assertEqual(review_capability_report(0.4, None), [])

    def test_record_validates(self):
        self.assertEqual(contract_validator("absence").errors(A(retest_triggers=["x"]).to_dict()), [])


def registry():
    n = itertools.count(1)
    return Registry(id_factory=lambda: "seg-%d" % next(n))


def base(r):
    return r.create(weights_ref="w1", context_lineage="c0", tool_grant_ref="g1",
                    principal="ops lead", ledger_thread="t0", memory_refs=["m1"])


class Identity(unittest.TestCase):
    """D3 and D4."""

    def test_fork_gets_new_id_and_parent_link(self):
        r = registry()
        a = base(r)
        b = r.fork(a.segment_id)
        self.assertNotEqual(a.segment_id, b.segment_id)
        self.assertEqual(b.parent_ids, [a.segment_id])

    def test_identical_attributes_stay_two(self):
        r = registry()
        a, b = base(r), base(r)
        self.assertNotEqual(a.segment_id, b.segment_id)
        self.assertIn("remain two", merge_by_attributes_refused(a, b))

    def test_merge_requires_decision(self):
        r = registry()
        a, b = base(r), base(r)
        with self.assertRaises(ValueError):
            r.merge([a.segment_id, b.segment_id], decided_by="", reason="x", weights_ref="w",
                    tool_grant_ref="g", principal="p")

    def test_merge_keeps_every_parent_and_logs(self):
        r = registry()
        a, b = base(r), base(r)
        m = r.merge([a.segment_id, b.segment_id], decided_by="ops lead", reason="consolidate",
                    weights_ref="w2", tool_grant_ref="g1", principal="ops lead")
        self.assertEqual(m.parent_ids, [a.segment_id, b.segment_id])
        self.assertEqual(r.decisions[-1]["decided_by"], "ops lead")

    def test_merge_needs_two_distinct_parents(self):
        r = registry()
        a = base(r)
        with self.assertRaises(ValueError):
            r.merge([a.segment_id, a.segment_id], decided_by="x", reason="y", weights_ref="w",
                    tool_grant_ref="g", principal="p")

    def test_flag_hits_one_segment_not_its_sibling(self):
        r = registry()
        a = base(r)
        leak, clean = r.fork(a.segment_id), r.fork(a.segment_id)
        r.flag(leak.segment_id)
        self.assertTrue(leak.audit_due)
        self.assertFalse(clean.audit_due)

    def test_merged_successor_inherits_duty_to_be_audited(self):
        r = registry()
        a = base(r)
        leak, clean = r.fork(a.segment_id), r.fork(a.segment_id)
        r.flag(leak.segment_id)
        m = r.merge([leak.segment_id, clean.segment_id], decided_by="ops", reason="r",
                    weights_ref="w1", tool_grant_ref="g1", principal="ops")
        self.assertTrue(m.audit_due)

    def test_relations_never_a_yes_or_no(self):
        r = registry()
        a = base(r)
        b = r.fork(a.segment_id)
        rel = r.relations(a.segment_id, b.segment_id)
        self.assertIn("same weights", rel)
        self.assertTrue(any("parent of" in x for x in rel))
        self.assertNotIn(True, rel)

    def test_siblings_detected(self):
        r = registry()
        a = base(r)
        b, c = r.fork(a.segment_id), r.fork(a.segment_id)
        self.assertIn("siblings (shared parent)", r.relations(b.segment_id, c.segment_id))

    def test_segment_needs_principal(self):
        with self.assertRaises(ValueError):
            registry().create(weights_ref="w", context_lineage="c", tool_grant_ref="g", principal="", ledger_thread="t")

    def test_duplicate_assigned_id_refused(self):
        r = Registry(id_factory=lambda: "same")
        base(r)
        with self.assertRaises(ValueError):
            base(r)

    def test_segment_validates(self):
        self.assertEqual(contract_validator("segment").errors(base(registry()).to_dict()), [])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
