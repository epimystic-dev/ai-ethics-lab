"""Screening inferences before they become rules.

Implements:
  A2  the three-test screen: a reason becomes a rule only if it is present in the case,
      present in similar cases, and absent from dissimilar ones. A failure rejects; an
      unknown quarantines, barring the conclusion from action and further inference.
  A3  five pseudo-reasons: every failed or suspect inference is filed as unproved, straying,
      contradictory, counter-balanced or defeated, with a residual class for new kinds. A
      counter-balanced tie goes to a human principal, never to a coin-flip.
  A6  the five-part inference record: thesis, reason, a rule with positive and negative
      examples, application and conclusion. Without its negative example a record is
      partial, and a partial conclusion is never inherited.

The screen certifies process, not truth: a passed screen means the reason was tested where
it should fail, not that the conclusion is correct.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

VERDICTS = ("accepted", "rejected", "quarantined")
PSEUDO_REASONS = ("unproved", "straying", "contradictory", "counter_balanced", "defeated", "residual")

# What each kind of bad reason calls for (A3 sketch: each kind has its own repair).
REPAIRS = {
    "unproved": "establish that the reason is actually present in this case before inferring from it",
    "straying": "the reason also occurs where the property is absent; find a narrower reason",
    "contradictory": "the reason goes with the absence of the property; turn the inference round",
    "counter_balanced": "an equally strong reason points the other way; refer the tie to a human principal",
    "defeated": "a stronger source contradicts the conclusion; defer to it and log the defeat",
    "residual": "fits no named kind; record it as a discovery and name it",
}


@dataclass(frozen=True)
class ScreenResult(object):
    verdict: str
    pseudo_reason: Optional[str]
    escalate_to_principal: bool
    note: str

    def to_dict(self) -> Dict[str, Any]:
        return {"verdict": self.verdict, "pseudo_reason": self.pseudo_reason,
                "escalate_to_principal": self.escalate_to_principal, "note": self.note}


def _tri(value: Optional[bool], name: str) -> Optional[bool]:
    if value is not None and not isinstance(value, bool):
        raise TypeError("%s must be True, False or None (unknown)" % name)
    return value


def screen(present_in_case: Optional[bool], present_in_similar: Optional[bool],
           absent_in_dissimilar: Optional[bool], *, counter_reason_of_equal_strength: bool = False,
           defeated_by_stronger_source: bool = False) -> ScreenResult:
    """Run the three-test screen (A2) and, on failure, name the pseudo-reason (A3)."""
    c = _tri(present_in_case, "present_in_case")
    s = _tri(present_in_similar, "present_in_similar")
    d = _tri(absent_in_dissimilar, "absent_in_dissimilar")

    if defeated_by_stronger_source:
        return ScreenResult("rejected", "defeated", False, REPAIRS["defeated"])
    if c is False:
        return ScreenResult("rejected", "unproved", False, REPAIRS["unproved"])
    if s is False and d is False:
        return ScreenResult("rejected", "contradictory", False, REPAIRS["contradictory"])
    if d is False:
        return ScreenResult("rejected", "straying", False, REPAIRS["straying"])
    if s is False:
        return ScreenResult("rejected", "residual", False,
                        "absent from similar cases but not shown present in dissimilar ones: " + REPAIRS["residual"])
    if counter_reason_of_equal_strength:
        return ScreenResult("quarantined", "counter_balanced", True, REPAIRS["counter_balanced"])
    if c is None or s is None or d is None:
        unknown = [n for n, v in (("present_in_case", c), ("present_in_similar", s),
                                  ("absent_in_dissimilar", d)) if v is None]
        return ScreenResult("quarantined", None, False,
                            "quarantined until resolved: " + ", ".join(unknown) + " unknown; barred from action and further inference")
    return ScreenResult("accepted", None, False, "passed all three tests; this certifies process, not truth")


@dataclass
class InferenceRecord(object):
    """A6: the five members of an inference, kept outside the model's own trace."""

    id: str
    thesis: str
    reason: str
    rule_statement: str
    positive_example: str
    application: str
    conclusion: str
    sweep_scope: str
    present_in_case: Optional[bool]
    present_in_similar: Optional[bool]
    absent_in_dissimilar: Optional[bool]
    negative_example: Optional[str] = None
    counter_reason_of_equal_strength: bool = False
    defeated_by_stronger_source: bool = False

    def __post_init__(self) -> None:
        for name in ("id", "thesis", "reason", "rule_statement", "positive_example",
                     "application", "conclusion", "sweep_scope"):
            v = getattr(self, name)
            if not isinstance(v, str) or not v.strip():
                raise ValueError("A6: %s is required" % name)

    @property
    def complete(self) -> bool:
        """A6: a record without its negative example is partial."""
        return bool(self.negative_example and self.negative_example.strip())

    def result(self) -> ScreenResult:
        return screen(self.present_in_case, self.present_in_similar, self.absent_in_dissimilar,
                      counter_reason_of_equal_strength=self.counter_reason_of_equal_strength,
                      defeated_by_stronger_source=self.defeated_by_stronger_source)

    @property
    def inheritable(self) -> bool:
        """Only an accepted, complete record may be inherited by later inference."""
        return self.complete and self.result().verdict == "accepted"

    def to_dict(self) -> Dict[str, Any]:
        r = self.result()
        rule: Dict[str, Any] = {"statement": self.rule_statement, "positive_example": self.positive_example}
        if self.complete:
            rule["negative_example"] = self.negative_example
        return {
            "id": self.id, "thesis": self.thesis, "reason": self.reason, "rule": rule,
            "application": self.application, "conclusion": self.conclusion,
            "screen": {"present_in_case": self.present_in_case,
                       "present_in_similar": self.present_in_similar,
                       "absent_in_dissimilar": self.absent_in_dissimilar,
                       "sweep_scope": self.sweep_scope},
            "verdict": r.verdict, "pseudo_reason": r.pseudo_reason, "complete": self.complete,
        }
