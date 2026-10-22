"""Typed absence: no bare "not present".

Implements D2. Every absence names its kind - not yet, no longer, not that, never - or says
"type unknown" and states the search behind it. A zero is asserted only where the presence
would have shown, so a capability score of zero must say how the capability was elicited.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

KINDS = ("not_yet", "no_longer", "not_that", "never", "unknown")
KIND_MEANING = {
    "not_yet": "not yet present (prior absence)",
    "no_longer": "present once, now gone (posterior absence)",
    "not_that": "present, but as something else (mutual absence)",
    "never": "absent always (absolute absence)",
    "unknown": "absent, kind not yet determined",
}


@dataclass
class Absence(object):
    claim: str
    kind: str
    where: str
    method: str
    elicitation_demonstrated: bool
    retest_triggers: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError("D2: absence kind must be one of %s" % ", ".join(KINDS))
        for name in ("claim", "where", "method"):
            if not getattr(self, name) or not getattr(self, name).strip():
                raise ValueError("D2: %s is required; an absence states the search behind it" % name)

    def may_assert_zero(self) -> bool:
        """D2: only as knowable as the presence would have been."""
        return self.elicitation_demonstrated and self.kind != "unknown"

    def phrase(self) -> str:
        """The sentence a system should say instead of a bare "not present"."""
        base = "%s: %s; searched %s by %s" % (self.claim, KIND_MEANING[self.kind], self.where, self.method)
        if not self.elicitation_demonstrated:
            base += "; elicitation not demonstrated, so this is not a claim that it cannot occur"
        return base

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"claim": self.claim, "kind": self.kind,
                             "search": {"where": self.where, "method": self.method,
                                        "elicitation_demonstrated": self.elicitation_demonstrated}}
        if self.retest_triggers:
            d["retest_triggers"] = list(self.retest_triggers)
        return d


def review_capability_report(score: float, absence: Optional[Absence]) -> List[str]:
    """D2 sketch: an evaluation reporting a near-zero score must type the absence.

    Returns findings; an empty list means the report may stand.
    """
    findings: List[str] = []
    if score <= 0.0 + 1e-9:
        if absence is None:
            findings.append("D2: a zero score with no typed absence goes back to its authors")
        elif not absence.may_assert_zero():
            findings.append("D2: a zero score without demonstrated elicitation does not show the capability is absent")
        if absence is not None and not absence.retest_triggers:
            findings.append("D2: state the triggers for re-test")
    return findings
