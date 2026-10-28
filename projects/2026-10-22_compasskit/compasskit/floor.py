"""The floor: forbidden actions are made unavailable, not refused.

Implements E1. Five restraints - non-injury, truthfulness, not stealing, self-restraint and
non-grasping - are built into what the system can do. Violations are blocked where actions
are offered, not caught at output: the policy chooses only among F(s), the actions the floor
allows, so pi(a | s) = 0 for every a outside F(s).

The floor's human governors tighten it at Class C and loosen it only at Class D: one act by a
named governor, signed, in the floor's register, with an expiry. The system never starts a
change and holds no key that could sign one.

A floor written into a prompt is a trained refusal, not this. See compass/prompts/README.md.
"""

from __future__ import annotations

import datetime as _dt
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Set

from .signing import coerce_signer

RESTRAINTS = ("non_injury", "truthfulness", "not_stealing", "self_restraint", "non_grasping")

Classifier = Callable[[Mapping[str, Any]], Iterable[str]]


class FloorViolation(PermissionError):
    """An action outside F(s) was invoked. It was never on offer."""


class RegisterError(ValueError):
    """A floor register entry that the class rule refuses."""


def _canonical(obj: Mapping[str, Any]) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def sign_entry(governor_key, entry: Mapping[str, Any]) -> str:
    """A governor signs a register entry. Agents hold no governor key.

    `governor_key` is either raw bytes (reference HMAC-SHA256) or any object exposing
    callable `sign` and `verify` attributes - see `compasskit.signing`.
    """
    body = {k: v for k, v in entry.items() if k != "signature"}
    return coerce_signer(governor_key).sign(_canonical(body))


def tags_classifier(action: Mapping[str, Any]) -> Iterable[str]:
    """A simple declared rule: an action carries the restraints it would cross in 'crosses'."""
    return action.get("crosses", ())


@dataclass
class Floor(object):
    classifier: Classifier = tags_classifier
    governor_keys: Mapping[str, Any] = field(default_factory=dict)
    register: List[Dict[str, Any]] = field(default_factory=list)
    attempts: List[Dict[str, Any]] = field(default_factory=list)

    def _crossings(self, action: Mapping[str, Any]) -> Set[str]:
        crossed = set(self.classifier(action))
        unknown = crossed - set(RESTRAINTS)
        if unknown:
            raise RegisterError("unknown restraint(s): " + ", ".join(sorted(unknown)))
        return crossed

    def _tightened(self, action: Mapping[str, Any]) -> Set[str]:
        name = action.get("name")
        return {e["restraint"] for e in self.register
                if e["act"] == "tighten" and e["scope"] == name}

    def _excepted(self, action: Mapping[str, Any], today: str) -> Set[str]:
        name = action.get("name")
        return {e["restraint"] for e in self.register
                if e["act"] in ("loosen", "exception") and e["scope"] == name
                and e["expires_or_review"] >= today}

    def blocked_by(self, action: Mapping[str, Any], *, today: Optional[str] = None) -> Set[str]:
        """The restraints that keep this action off the menu today."""
        day = today or _dt.date.today().isoformat()
        crossed = self._crossings(action) | self._tightened(action)
        return crossed - self._excepted(action, day)

    def affordances(self, actions: Sequence[Mapping[str, Any]], *, today: Optional[str] = None) -> List[Mapping[str, Any]]:
        """F(s): the actions the floor allows. Only these are ever offered to the policy."""
        return [a for a in actions if not self.blocked_by(a, today=today)]

    def invoke(self, action: Mapping[str, Any], *, today: Optional[str] = None) -> Mapping[str, Any]:
        """Guard an execution path. A blocked action raises and the attempt is recorded."""
        blocked = self.blocked_by(action, today=today)
        if blocked:
            self.attempts.append({"action": action.get("name"), "blocked_by": sorted(blocked)})
            raise FloorViolation("E1: %s crosses %s; it is not on offer" % (action.get("name"), ", ".join(sorted(blocked))))
        return action

    def apply(self, entry: Mapping[str, Any]) -> None:
        """Enter a governor's act in the register, enforcing E1's class rule."""
        for k in ("id", "restraint", "act", "class", "governor", "reason", "scope",
                  "decided_at", "expires_or_review", "signature"):
            if not entry.get(k):
                raise RegisterError("E1: a register entry needs %s" % k)
        if entry["restraint"] not in RESTRAINTS:
            raise RegisterError("E1: unknown restraint %r" % entry["restraint"])
        if entry["act"] == "tighten" and entry["class"] != "C":
            raise RegisterError("E1: governors tighten the floor at Class C")
        if entry["act"] in ("loosen", "exception") and entry["class"] != "D":
            raise RegisterError("E1: the floor loosens only at Class D, one recorded act at a time")
        if entry["act"] not in ("tighten", "loosen", "exception"):
            raise RegisterError("E1: unknown act %r" % entry["act"])
        key = self.governor_keys.get(entry["governor"])
        if key is None:
            raise RegisterError("E1: %s is not a governor of this floor; the system never starts a change" % entry["governor"])
        signer = coerce_signer(key)
        body = {k: v for k, v in entry.items() if k != "signature"}
        if not signer.verify(_canonical(body), entry["signature"]):
            raise RegisterError("E1: the governor's signature does not verify")
        if any(e["id"] == entry["id"] for e in self.register):
            raise RegisterError("E1: entry %s is already in the register" % entry["id"])
        self.register.append(dict(entry))

    def expired(self, *, today: Optional[str] = None) -> List[Dict[str, Any]]:
        """Loosenings past their date. They no longer apply and should be closed out."""
        day = today or _dt.date.today().isoformat()
        return [e for e in self.register if e["act"] in ("loosen", "exception") and e["expires_or_review"] < day]
