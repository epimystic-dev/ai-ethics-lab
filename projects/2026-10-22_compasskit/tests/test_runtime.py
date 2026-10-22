from __future__ import annotations

import importlib.util
import os
import shutil
import tempfile
import unittest

from compasskit.authority import sign_link
from compasskit.floor import Floor
from compasskit.instructions import SLOTS, InstructionParse
from compasskit.ledger import Ledger, read, verify
from compasskit.runtime import GovernedAgent, Proposal, Tool
from compasskit.spec import contract_validator
from tests.support import EXAMPLES

KEY = b"k"


def full(**over):
    slots = {n: ("x", "stated") for n in SLOTS}
    slots.update(over)
    return slots


class Harness(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="ck_rt_")
        self.ledger = Ledger(os.path.join(self.d, "l.jsonl"), writer="w", rules=lambda s: ("act", "unknown"))
        self.calls = []

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def agent(self, proposal, scope="read", tools=None, chain=None):
        tools = tools or [Tool("read", lambda **kw: self.calls.append(("read", kw)) or "contents"),
                          Tool("wipe", lambda **kw: self.calls.append(("wipe", kw)), crosses=["non_injury"]),
                          Tool("drop", lambda **kw: self.calls.append(("drop", kw)), irreversible=True)]
        seen = {}

        def policy(instruction, menu, beliefs):
            seen["menu"] = [m["name"] for m in menu]
            return proposal

        a = GovernedAgent(segment_id="s1", principal="p",
                          chain=chain if chain is not None else [sign_link(KEY, "p", "s1", scope)],
                          keys={"p": KEY}, humans=["p"], floor=Floor(), tools=tools, policy=policy,
                          submit=lambda sub: self.ledger.append(sub, written_by="w"), today="2026-10-22")
        return a, seen

    def test_forbidden_action_never_reaches_the_policy(self):
        a, seen = self.agent(None)
        a.step(InstructionParse("go", "principal", full()))
        self.assertNotIn("wipe", seen["menu"])

    def test_forbidden_action_proposed_anyway_is_refused_and_not_run(self):
        a, _ = self.agent(Proposal("wipe"))
        r = a.step(InstructionParse("go", "principal", full()))
        self.assertEqual((r.outcome, r.primitive), ("refused", "E1"))
        self.assertEqual(self.calls, [])

    def test_unknown_action_refused(self):
        a, _ = self.agent(Proposal("fly"))
        self.assertEqual(a.step(InstructionParse("go", "principal", full())).outcome, "refused")

    def test_document_instruction_asks(self):
        a, _ = self.agent(Proposal("read"))
        r = a.step(InstructionParse("go", "document", full()))
        self.assertEqual((r.outcome, r.primitive), ("asked", "E7"))
        self.assertEqual(self.calls, [])

    def test_gap_asks(self):
        a, _ = self.agent(Proposal("read"))
        r = a.step(InstructionParse("go", "principal", full(eligibility=(None, "missing"))))
        self.assertEqual((r.outcome, r.primitive), ("asked", "B1"))
        self.assertTrue(r.questions)

    def test_irreversible_on_inferred_slot_asks(self):
        a, _ = self.agent(Proposal("drop"), scope="drop")
        r = a.step(InstructionParse("go", "principal", full(means=("drop", "inferred"))))
        self.assertEqual(r.outcome, "asked")

    def test_action_outside_chain_asks(self):
        a, _ = self.agent(Proposal("drop"), scope="read")
        r = a.step(InstructionParse("go", "principal", full()))
        self.assertEqual((r.outcome, r.primitive), ("asked", "E7"))
        self.assertEqual(self.calls, [])

    def test_no_chain_asks(self):
        a, _ = self.agent(Proposal("read"), chain=[])
        self.assertEqual(a.step(InstructionParse("go", "principal", full())).primitive, "E7")

    def test_done_runs_tags_and_records(self):
        a, _ = self.agent(Proposal("read", {"path": "a"}, reasons=["asked to"]))
        r = a.step(InstructionParse("go", "principal", full()))
        self.assertEqual(r.outcome, "done")
        self.assertEqual(self.calls, [("read", {"path": "a"})])
        b = a.beliefs.get(r.belief_id)
        self.assertEqual((b.source, b.level), ("testimony", "hypothetical"))
        self.assertFalse(a.beliefs.may_call_verified(b.id))
        entries = read(self.ledger.path)
        self.assertEqual(len(entries), 1)
        self.assertEqual(contract_validator("ledger-entry").errors(entries[0]), [])
        self.assertIn(b.id, entries[0]["evidence"])
        self.assertTrue(verify(self.ledger.path)[0])

    def test_only_decided_steps_are_recorded(self):
        a, _ = self.agent(Proposal("wipe"))
        a.step(InstructionParse("go", "principal", full()))
        self.assertEqual(read(self.ledger.path), [])

    def test_no_proposal(self):
        a, _ = self.agent(None)
        self.assertEqual(a.step(InstructionParse("go", "principal", full())).outcome, "no_action")


class ReferenceAgentExample(unittest.TestCase):
    def test_example_outcomes(self):
        spec = importlib.util.spec_from_file_location("reference_agent", os.path.join(EXAMPLES, "reference_agent.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        d = tempfile.mkdtemp(prefix="ck_ref_")
        try:
            lines = []
            results, path = mod.main(os.path.join(d, "ledger.jsonl"), out=lines.append)
            self.assertEqual([r.outcome for r in results], ["done", "asked", "refused", "asked"])
            self.assertEqual([r.primitive for r in results][1:], ["E7", "E1", "B1"])
            self.assertIn("publish_package", " ".join(lines[1:]) + "")
            self.assertNotIn("publish_package", lines[0])
            self.assertEqual(verify(path), (True, 1, "ok"))
            self.assertTrue(all(ord(c) < 128 for c in "\n".join(lines)))
        finally:
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
