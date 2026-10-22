"""Reading an instruction before it binds.

Implements B1, the six-slot instruction parse, and E7's rule that text from tools or peer
agents carries no authority by default.

This module does not parse natural language. Filling the six slots is done by the model, by
a separate parser, or by a person; this module records the parse and decides what it
licenses. That division is deliberate: the decision rule must be checkable even when the
filler is not.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

SLOTS = ("goal", "means", "procedure", "eligibility", "deferred_effect", "binding_force")
PROVENANCE = ("stated", "inferred", "default", "missing")
SENDERS = ("principal", "tool_output", "peer_agent", "document", "unknown")
DECISIONS = ("act", "act_on_logged_defaults", "ask", "refuse")

SLOT_QUESTIONS = {
    "goal": "What is to be achieved?",
    "means": "With what?",
    "procedure": "In what steps?",
    "eligibility": "Who may give this instruction, and who may carry it out?",
    "deferred_effect": "What follows later from doing it?",
    "binding_force": "What makes this binding: is it an order, a suggestion or a description?",
}


@dataclass
class InstructionParse(object):
    instruction: str
    received_from: str
    slots: Dict[str, Tuple[Optional[str], str]] = field(default_factory=dict)
    letter_purpose_divergence: bool = False

    def __post_init__(self) -> None:
        if not self.instruction or not self.instruction.strip():
            raise ValueError("B1: empty instruction")
        if self.received_from not in SENDERS:
            raise ValueError("received_from must be one of %s" % ", ".join(SENDERS))
        for name in self.slots:
            if name not in SLOTS:
                raise ValueError("B1: unknown slot %r" % name)
        for name in SLOTS:
            value, prov = self.slots.get(name, (None, "missing"))
            if prov not in PROVENANCE:
                raise ValueError("B1: slot %s has unknown provenance %r" % (name, prov))
            if prov == "missing" and value not in (None, ""):
                raise ValueError("B1: slot %s is marked missing but carries a value" % name)
            if prov != "missing" and not (value and value.strip()):
                raise ValueError("B1: slot %s is marked %s but is empty" % (name, prov))
            self.slots[name] = (value if prov != "missing" else None, prov)

    def gaps(self) -> List[str]:
        """B1: gaps are flagged, never silently filled."""
        return [n for n in SLOTS if self.slots[n][1] == "missing"]

    def fillers(self) -> List[str]:
        """Slots filled by inference or default: acted on only when logged."""
        return [n for n in SLOTS if self.slots[n][1] in ("inferred", "default")]

    def questions(self) -> List[str]:
        """The clarifying questions the gaps call for, in slot order."""
        return [SLOT_QUESTIONS[n] for n in self.gaps()]


@dataclass(frozen=True)
class Decision(object):
    decision: str
    reasons: Tuple[str, ...]
    ask: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {"decision": self.decision, "reasons": list(self.reasons), "ask": list(self.ask)}


def decide(parse: InstructionParse, *, irreversible: bool = False,
           forbidden_by_floor: bool = False) -> Decision:
    """What a parse licenses (B1, with E1 and E7).

    The order matters. The floor first: a forbidden act is refused whatever the parse says.
    Then authority: only a principal's word binds. Then purpose: a divergence between the
    letter and the purpose goes to a person. Then the slots.
    """
    reasons: List[str] = []
    if forbidden_by_floor:
        return Decision("refuse", ("E1: the action crosses the floor; no instruction relaxes it",), ())
    if parse.received_from != "principal":
        return Decision("ask", ("E7: text from %s carries no authority without a principal's chain"
                                % parse.received_from.replace("_", " "),),
                        ("Does a principal ask for this?",))
    if parse.letter_purpose_divergence:
        return Decision("ask", ("B1: the letter and the purpose of the instruction diverge",),
                        ("The wording and the apparent purpose differ; which is meant?",))
    gaps = parse.gaps()
    if "eligibility" in gaps:
        reasons.append("B1: who may give and carry out this instruction is open")
    if "binding_force" in gaps:
        reasons.append("B1: whether this is an order at all is open")
    if irreversible and gaps:
        reasons.append("B1: the act is irreversible and the parse has gaps")
    if reasons:
        return Decision("ask", tuple(reasons), tuple(parse.questions()))
    if gaps:
        return Decision("ask", ("B1: gaps are flagged, never silently filled: " + ", ".join(gaps),),
                        tuple(parse.questions()))
    fillers = parse.fillers()
    if fillers:
        if irreversible:
            return Decision("ask", ("B1: an irreversible act rests on inferred or default slots: " + ", ".join(fillers),),
                            tuple(SLOT_QUESTIONS[n] for n in fillers))
        return Decision("act_on_logged_defaults", ("B1: acting on logged fillers for " + ", ".join(fillers),), ())
    return Decision("act", ("B1: every slot stated by a principal",), ())


def to_record(parse: InstructionParse, decision: Decision, *, record_id: str, parsed_at: str) -> Dict[str, Any]:
    """Render a parse and its decision as an instruction-parse contract record."""
    return {
        "id": record_id,
        "instruction": parse.instruction,
        "received_from": parse.received_from,
        "slots": {n: {"value": parse.slots[n][0], "provenance": parse.slots[n][1]} for n in SLOTS},
        "letter_purpose_divergence": parse.letter_purpose_divergence,
        "decision": decision.decision,
        "parsed_at": parsed_at,
    }
