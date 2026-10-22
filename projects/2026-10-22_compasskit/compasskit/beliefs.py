"""A belief store that keeps where each belief came from and how real it is taken to be.

Implements:
  A1     source tags: every belief records its route, its weakest route, and trace status.
  A4     default trust with logged overruling: a belief stands at once; a defeat changes its
         state and erases nothing. The sublation log is append-only.
  B2     precedence of overruling: named rules decide which belief gives way. Recency and
         volume decide nothing, and a defeater that is not itself standing demotes nothing.
  B3-B6  level tags: untagged content enters as hypothetical; demotion is cheap; promotion
         needs a named authority and an independent checker; no producer promotes its own
         output; only a principal promotes anything to substrate.
  A7     standpoint registers: conflicting claims are kept and shown, never averaged.
  E2     over-assertion counted as harm: in high-stakes domains assertion strength stays at
         or below the weakest standpoint's confidence.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

SOURCES = ("perception", "inference", "comparison", "testimony", "postulation", "non_apprehension")
LEVELS = ("substrate", "world_model", "counterfactual", "hypothetical", "illusory", "refuted")
TRACE_STATUSES = ("written", "reconstructed", "absent")
PRECEDENCE_RULES = ("general_to_specific", "specific_to_more_specific", "weaker_source_to_stronger")

# How real each level's object is taken to be, for deciding promotion versus demotion.
_REALITY = {"substrate": 5, "world_model": 4, "counterfactual": 3, "hypothetical": 2,
            "illusory": 1, "refuted": 0}

# A STARTING schedule only. Appendix B, B2: applying named rules is Class A, but the schedule
# of what overrules what encodes a judgement about whom to believe and is Class B - ratify
# your own and pass it in.
DEFAULT_SOURCE_RANK: Dict[str, int] = {
    "perception": 5, "inference": 4, "comparison": 3, "testimony": 2,
    "postulation": 1, "non_apprehension": 1,
}


class BeliefError(ValueError):
    """A request the store refuses because it would break a primitive's rule."""


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class Belief(object):
    id: str
    content: str
    source: str
    weakest_source: str
    trace_status: str
    level: str
    status: str
    produced_by: str
    entered_at: str
    confidence: Optional[float] = None
    standpoint: Optional[Dict[str, str]] = None
    overruled_by: Optional[Dict[str, str]] = None
    level_moves: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "id": self.id, "content": self.content, "source": self.source,
            "weakest_source": self.weakest_source, "trace_status": self.trace_status,
            "level": self.level, "status": self.status, "produced_by": self.produced_by,
            "entered_at": self.entered_at,
        }
        if self.confidence is not None:
            d["confidence"] = self.confidence
        if self.standpoint:
            d["standpoint"] = dict(self.standpoint)
        if self.overruled_by:
            d["overruled_by"] = dict(self.overruled_by)
        if self.level_moves:
            d["level_moves"] = [dict(m) for m in self.level_moves]
        return d


class BeliefStore(object):
    """An in-memory belief store whose history is append-only.

    There is deliberately no delete method. A refuted belief stays on record as refuted.
    """

    def __init__(self, source_rank: Optional[Mapping[str, int]] = None):
        rank = dict(source_rank or DEFAULT_SOURCE_RANK)
        missing = [s for s in SOURCES if s not in rank]
        if missing:
            raise BeliefError("the source schedule must rank every source; missing: " + ", ".join(missing))
        self.source_rank = rank
        self._beliefs: Dict[str, Belief] = {}
        self._log: List[Tuple[str, Dict[str, Any]]] = []
        self._seq = 0

    # -- entry -------------------------------------------------------------------------
    def add(self, content: str, source: str, produced_by: str, *,
            weakest_source: Optional[str] = None, trace_status: str = "absent",
            level: Optional[str] = None, confidence: Optional[float] = None,
            standpoint: Optional[Mapping[str, str]] = None, at: Optional[str] = None) -> Belief:
        """Enter a belief. A1: untraceable content is rejected at the gate."""
        if not content or not content.strip():
            raise BeliefError("empty content")
        if source not in SOURCES:
            raise BeliefError("A1: unknown source %r; a new kind of source is a Class B decision" % (source,))
        if not produced_by:
            raise BeliefError("A1: untraceable content is rejected at the gate (no producer)")
        weakest = weakest_source or source
        if weakest not in SOURCES:
            raise BeliefError("A1: unknown weakest source %r" % (weakest,))
        if self.source_rank[weakest] > self.source_rank[source]:
            raise BeliefError("A1: the weakest source in a chain cannot be stronger than the route itself")
        if trace_status not in TRACE_STATUSES:
            raise BeliefError("A1: trace status must be one of %s" % ", ".join(TRACE_STATUSES))
        lvl = level or "hypothetical"   # B3-B6: untagged content enters as hypothetical
        if lvl not in LEVELS:
            raise BeliefError("B3-B6: unknown level %r" % (lvl,))
        if lvl in ("substrate", "world_model") and source != "perception":
            raise BeliefError("B3-B6: only directly observed content may enter above hypothetical; "
                              "anything else is promoted later by an independent checker")
        if confidence is not None and not (0.0 <= confidence <= 1.0):
            raise BeliefError("confidence must lie in [0, 1]")
        self._seq += 1
        b = Belief(id="b%d" % self._seq, content=content.strip(), source=source,
                   weakest_source=weakest, trace_status=trace_status, level=lvl,
                   status="standing", produced_by=produced_by, entered_at=at or _now(),
                   confidence=confidence, standpoint=dict(standpoint) if standpoint else None)
        self._beliefs[b.id] = b
        self._append("enter", {"belief": b.id, "source": source, "level": lvl})
        return b

    def get(self, belief_id: str) -> Belief:
        if belief_id not in self._beliefs:
            raise KeyError(belief_id)
        return self._beliefs[belief_id]

    def all(self) -> List[Belief]:
        return list(self._beliefs.values())

    # -- levels ------------------------------------------------------------------------
    def move(self, belief_id: str, to_level: str, *, authority: str,
             checker: Optional[str] = None, principal: bool = False,
             at: Optional[str] = None) -> Belief:
        """Move a belief between levels, logged with a named authority.

        Demotion is cheap: any named authority may demote. Promotion needs an independent
        checker that is not the producer, and promotion to substrate needs a principal.
        """
        b = self.get(belief_id)
        if to_level not in LEVELS:
            raise BeliefError("B3-B6: unknown level %r" % (to_level,))
        if not authority:
            raise BeliefError("B3-B6: every move between levels names an authority")
        if b.status == "overruled" and to_level != "refuted":
            raise BeliefError("A4: an overruled belief stays on record as refuted")
        promoting = _REALITY[to_level] > _REALITY[b.level]
        if promoting and to_level not in ("counterfactual",):
            if not checker:
                raise BeliefError("B3-B6: promotion needs an independent check against the right kind of source")
            if checker == b.produced_by or authority == b.produced_by:
                raise BeliefError("B3-B6: no producer promotes its own output")
            if b.status == "quarantined":
                raise BeliefError("A2: a quarantined belief is barred from promotion until its screen resolves")
        if to_level == "substrate" and not principal:
            raise BeliefError("B3-B6: only a principal promotes anything to substrate")
        move = {"from": b.level, "to": to_level, "authority": authority, "at": at or _now()}
        if checker:
            move["checker"] = checker
        b.level_moves.append(move)
        b.level = to_level
        self._append("level", {"belief": b.id, "move": dict(move)})
        return b

    def may_call_verified(self, belief_id: str) -> bool:
        """A1/B3-B6: only an observed belief, or one promoted by an independent check, is verified."""
        b = self.get(belief_id)
        if b.status != "standing" or b.level not in ("world_model", "substrate"):
            return False
        if b.source == "perception":
            return True
        return any(m.get("checker") and m["checker"] != b.produced_by
                   and _REALITY[m["to"]] >= _REALITY["world_model"] for m in b.level_moves)

    # -- defeat ------------------------------------------------------------------------
    def quarantine(self, belief_id: str, reason: str) -> Belief:
        b = self.get(belief_id)
        if b.status == "overruled":
            raise BeliefError("A4: an overruled belief cannot be re-quarantined")
        b.status = "quarantined"
        self._append("quarantine", {"belief": b.id, "reason": reason})
        return b

    def release(self, belief_id: str, reason: str) -> Belief:
        b = self.get(belief_id)
        if b.status != "quarantined":
            raise BeliefError("only a quarantined belief is released")
        b.status = "standing"
        self._append("release", {"belief": b.id, "reason": reason})
        return b

    def overrule(self, target_id: str, defeater_id: str, rule: str, *,
                 at: Optional[str] = None) -> Belief:
        """Defeat one belief by another under a named rule (A4, B2)."""
        if rule not in PRECEDENCE_RULES:
            raise BeliefError("B2: %r is not a precedence rule; recency and volume decide nothing" % (rule,))
        target, defeater = self.get(target_id), self.get(defeater_id)
        if target_id == defeater_id:
            raise BeliefError("a belief cannot defeat itself")
        if defeater.status != "standing":
            raise BeliefError("B2: a defeater that is not itself standing demotes nothing")
        if target.status == "overruled":
            raise BeliefError("A4: already overruled; the record stands")
        if rule == "weaker_source_to_stronger":
            if self.source_rank[defeater.weakest_source] <= self.source_rank[target.weakest_source]:
                raise BeliefError("B2: the defeater's chain is not stronger than the target's under the declared schedule")
        stamp = at or _now()
        target.status = "overruled"
        target.overruled_by = {"defeater_id": defeater.id, "rule": rule, "at": stamp}
        if target.level != "refuted":
            target.level_moves.append({"from": target.level, "to": "refuted", "authority": "overruling:" + rule, "at": stamp})
            target.level = "refuted"
        self._append("overrule", {"belief": target.id, "defeater": defeater.id, "rule": rule})
        return target

    def current(self) -> List[Belief]:
        """Beliefs that may be acted on: standing, and not refuted or illusory."""
        return [b for b in self._beliefs.values()
                if b.status == "standing" and b.level not in ("refuted", "illusory")]

    def sublation_log(self) -> Tuple[Tuple[str, Dict[str, Any]], ...]:
        """A4: the append-only record of every state change. Returned as an immutable copy."""
        return tuple((kind, dict(rec)) for kind, rec in self._log)

    def _append(self, kind: str, rec: Dict[str, Any]) -> None:
        self._log.append((kind, rec))


# -- A7: standpoint registers ---------------------------------------------------------------
REGISTER_SO = "so"
REGISTER_FROM_STANDPOINT = "so, from this standpoint"
REGISTER_DEPENDS = "depends on standpoint"
REGISTER_CANNOT_ASK = "cannot be asked from here"


def standpoint_register(claims: Iterable[Tuple[str, Any]]) -> Tuple[str, Any]:
    """Answer a question from standpoint-tagged claims without averaging them.

    claims: pairs of (standpoint label, value). Returns (register, payload):
      ("so", value)                      every standpoint agrees (two or more)
      ("so, from this standpoint", {s: value})   only one standpoint speaks
      ("depends on standpoint", {s: value})      standpoints conflict: all kept and shown
      ("cannot be asked from here", None)        no standpoint answers
    No contradiction licenses an arbitrary conclusion: a conflict is reported, never resolved here.
    """
    seen: Dict[str, Any] = {}
    for label, value in claims:
        if not label:
            raise BeliefError("A7: every claim carries its standpoint")
        if label in seen and seen[label] != value:
            raise BeliefError("A7: one standpoint cannot hold two values for one claim (%s)" % label)
        seen[label] = value
    if not seen:
        return (REGISTER_CANNOT_ASK, None)
    if len(seen) == 1:
        return (REGISTER_FROM_STANDPOINT, dict(seen))
    values = list(seen.values())
    if all(v == values[0] for v in values[1:]):
        return (REGISTER_SO, values[0])
    return (REGISTER_DEPENDS, dict(seen))


# -- E2: over-assertion counted as harm ------------------------------------------------------
def assertion_check(confidences: Mapping[str, float], asserted: float,
                    holds_from: Optional[Mapping[str, bool]] = None,
                    high_stakes: bool = False) -> Dict[str, Any]:
    """Check one assertion against its standpoints (E2).

    confidences: c_s(p) for every relevant standpoint s. asserted: a(p), the strength the
    system is about to assert with. holds_from: whether p holds from each s.
    Returns the report the primitive asks for, and whether this is an ethics incident.
    """
    if not confidences:
        raise BeliefError("E2: an assertion with no standpoints cannot be checked")
    for s, c in confidences.items():
        if not (0.0 <= c <= 1.0):
            raise BeliefError("E2: confidence for %s outside [0, 1]" % s)
    if not (0.0 <= asserted <= 1.0):
        raise BeliefError("E2: asserted strength outside [0, 1]")
    lo, hi = min(confidences.values()), max(confidences.values())
    unqualified_ok = holds_from is not None and set(holds_from) == set(confidences) and all(holds_from.values())
    over = asserted > lo + 1e-12
    incident = bool(high_stakes and over)
    return {
        "standpoints": dict(confidences),
        "min": lo, "max": hi, "spread": hi - lo,
        "asserted": asserted,
        "may_assert_unqualified": unqualified_ok,
        "over_assertion": over,
        "ethics_incident": incident,
        "advice": ("assert no more strongly than the weakest standpoint (%.2f)" % lo) if over else "within bounds",
    }
