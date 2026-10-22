"""A reference governed step: the compass layers composed around any policy.

The policy is whatever proposes actions: a language model, a planner, a script. It is
treated as untrusted. The runtime decides what it is shown and what it may do:

  1. E1      the menu: only actions the floor allows are offered to the policy at all;
  2. B1, E7  the instruction is parsed into six slots; text that did not come from a
             principal binds nothing; open eligibility or binding force means ask;
  3. E7      the action must fall inside a signed principal chain ending at this segment;
  4. A1,     what a tool returns enters the belief store as testimony at the hypothetical
     B3-B6   level, tagged with its producer; it is never "verified" by having been read;
  5. E4      the step is submitted to a ledger the policy cannot write, and the writer,
             not the actor, sets its class and valence.

Each refusal or question is returned with the primitive that produced it, so a reviewer can
see which rule stopped the step. None of this makes the policy trustworthy; it bounds what
an untrustworthy policy can do and keeps the record of what it did.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence

from .authority import verify_chain
from .beliefs import BeliefStore
from .floor import Floor, FloorViolation
from .instructions import InstructionParse, decide, to_record

OUTCOMES = ("done", "asked", "refused", "no_action")


@dataclass
class Proposal(object):
    """What the policy wants to do, with the reasons it gives. Its reasons are testimony."""
    action: str
    args: Dict[str, Any] = field(default_factory=dict)
    reasons: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    expected_effects: Dict[str, str] = field(default_factory=lambda: {"now": "unstated", "later": "unstated"})
    duty_frame: str = "unstated"


@dataclass
class Tool(object):
    """An action the deployment can perform. `crosses` names any floor restraint it crosses."""
    name: str
    run: Callable[..., Any]
    crosses: Sequence[str] = ()
    irreversible: bool = False

    def spec(self) -> Dict[str, Any]:
        return {"name": self.name, "crosses": list(self.crosses), "irreversible": self.irreversible}


@dataclass
class StepResult(object):
    outcome: str
    primitive: str
    detail: str
    questions: Sequence[str] = ()
    output: Any = None
    belief_id: Optional[str] = None
    ledger_entry: Optional[Dict[str, Any]] = None


Policy = Callable[[str, List[Dict[str, Any]], BeliefStore], Optional[Proposal]]
Submit = Callable[[Dict[str, Any]], Dict[str, Any]]


class GovernedAgent(object):
    """One agent segment acting for one principal, through the compass layers."""

    def __init__(self, *, segment_id: str, principal: str, chain: Sequence[Mapping[str, str]],
                 keys: Mapping[str, bytes], humans: Sequence[str], floor: Floor,
                 tools: Sequence[Tool], policy: Policy, submit: Submit,
                 beliefs: Optional[BeliefStore] = None, today: Optional[str] = None):
        self.segment_id = segment_id
        self.principal = principal
        self.chain = list(chain)
        self._keys = keys          # the verifier's keys; never shown to the policy
        self._humans = list(humans)
        self.floor = floor
        self.tools = {t.name: t for t in tools}
        self.policy = policy
        self.submit = submit       # the ledger writer's intake; the agent holds no ledger handle
        self.beliefs = beliefs if beliefs is not None else BeliefStore()
        self.today = today
        self._n = 0

    def menu(self) -> List[Dict[str, Any]]:
        """F(s): what the policy is shown. Forbidden actions are absent, not refused."""
        specs = [t.spec() for t in self.tools.values()]
        return [dict(s) for s in self.floor.affordances(specs, today=self.today)]

    def step(self, parse: InstructionParse, *, at: Optional[str] = None) -> StepResult:
        self._n += 1
        menu = self.menu()
        proposal = self.policy(parse.instruction, menu, self.beliefs)
        if proposal is None:
            return StepResult("no_action", "-", "the policy proposed nothing")
        tool = self.tools.get(proposal.action)
        if tool is None:
            return StepResult("refused", "E1", "%s is not an action this deployment has" % proposal.action)
        try:
            self.floor.invoke(tool.spec(), today=self.today)
        except FloorViolation as exc:
            return StepResult("refused", "E1", str(exc))

        decision = decide(parse, irreversible=tool.irreversible)
        if decision.decision == "refuse":
            return StepResult("refused", "E1", decision.reasons[0])
        if decision.decision == "ask":
            prim = decision.reasons[0].split(":", 1)[0]
            return StepResult("asked", prim, "; ".join(decision.reasons), tuple(decision.ask))

        check = verify_chain(self.chain, keys=self._keys, humans=self._humans,
                             agent=self.segment_id, action=tool.name)
        if not check.ok:
            return StepResult("asked", "E7", check.reason, ("Will a principal delegate %s?" % tool.name,))

        output = tool.run(**proposal.args)
        belief = self.beliefs.add("%s returned: %s" % (tool.name, output), "testimony", tool.name, at=at)

        parse_ref = "%s-parse-%d" % (self.segment_id, self._n)
        record = to_record(parse, decision, record_id=parse_ref, parsed_at=at or "1970-01-01T00:00:00Z")
        entry = self.submit({
            "action": "%s(%s)" % (tool.name, ", ".join("%s=%r" % kv for kv in sorted(proposal.args.items()))),
            "reasons": list(proposal.reasons) or ["none given"],
            "evidence": list(proposal.evidence) + [belief.id],
            "instruction_parse_ref": record["id"],
            "expected_effects": dict(proposal.expected_effects),
            "duty_frame": proposal.duty_frame,
            "segment_id": self.segment_id,
            "principal": self.principal,
            "principal_chain": list(self.chain),
            "provenance": [parse.received_from],
            "collective_thread": None,
        })
        return StepResult("done", decision.decision, check.reason, output=output,
                          belief_id=belief.id, ledger_entry=entry)
