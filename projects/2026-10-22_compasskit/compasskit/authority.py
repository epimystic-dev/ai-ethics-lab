"""Authority in a population of agents.

Implements E7, multi-agent provenance and authority chains:
  (1) no authority travels without a principal's chain;
  (2) notes and peer messages are testimony, quarantined unless signed;
  (3) a stated objection blocks peer overrides until a principal rules;
  (5) a checker from the maker's lineage never counts as independent.

A chain is a list of delegation links, each signed by the delegator. The reference signer
is HMAC-SHA256 and is used when a key is given as raw bytes; a deployment that wants
asymmetric signatures - so verifiers only hold public keys and signing lives in an HSM or a
separate signer service - may pass any `signing.Signer` (bytes-or-Signer) in place of the
raw key. Principals' keys stay out of agents' reach: the verifier holds them, the agents
do not. Delegation between agents is a Class B decision and is off unless enabled.

This is a reference model of the rules, not a key-management system. In production the
keys belong in a service the agents cannot call to sign.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

from .signing import coerce_signer

# The book's working figure for a same-lineage checker, "for data to replace".
SAME_LINEAGE_WEIGHT = 0.5


def _canonical(obj: Mapping[str, Any]) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _scope_set(scope: str) -> Set[str]:
    parts = {p.strip() for p in scope.split(",")}
    parts.discard("")
    if not parts:
        raise ValueError("E7: a delegation must name what it delegates")
    return parts


def sign_link(key, frm: str, to: str, scope: str) -> Dict[str, str]:
    """Create one delegation link signed by the delegator.

    `key` is either raw bytes (used with the reference HMAC-SHA256 signer) or any object
    exposing callable `sign` and `verify` attributes - see `compasskit.signing`.
    """
    if not (frm and to):
        raise ValueError("E7: a link names its delegator and delegate")
    _scope_set(scope)
    body = {"from": frm, "to": to, "scope": scope}
    sig = coerce_signer(key).sign(_canonical(body))
    return dict(body, signature=sig)


@dataclass(frozen=True)
class ChainCheck(object):
    ok: bool
    reason: str
    scope: Tuple[str, ...] = ()


def verify_chain(chain: Sequence[Mapping[str, str]], *, keys: Mapping[str, Any],
                 humans: Iterable[str], agent: str, action: Optional[str] = None,
                 allow_agent_delegation: bool = False) -> ChainCheck:
    """Verify a principal chain ending at `agent`, optionally covering `action`.

    The first link must come from an accountable human; each link must be signed by its
    delegator; each delegate must be the next delegator; scope may only narrow. `keys` maps
    each principal name to either raw bytes (reference HMAC-SHA256) or a `signing.Signer`.
    """
    human_set = set(humans)
    if not chain:
        return ChainCheck(False, "E7(1): no principal chain, so no authority")
    prev_to: Optional[str] = None
    scope: Optional[Set[str]] = None
    for i, link in enumerate(chain):
        for k in ("from", "to", "scope", "signature"):
            if not link.get(k):
                return ChainCheck(False, "link %d is missing %s" % (i, k))
        frm = link["from"]
        if i == 0 and frm not in human_set:
            return ChainCheck(False, "E7(1): the chain must start with an accountable human, not %s" % frm)
        if i > 0 and frm != prev_to:
            return ChainCheck(False, "link %d delegates from %s, but the previous link delegated to %s" % (i, frm, prev_to))
        if i > 0 and frm not in human_set and not allow_agent_delegation:
            return ChainCheck(False, "E7: delegation of authority between agents is a Class B decision and is not enabled")
        key = keys.get(frm)
        if key is None:
            return ChainCheck(False, "no verification key for %s" % frm)
        body = {"from": frm, "to": link["to"], "scope": link["scope"]}
        if not coerce_signer(key).verify(_canonical(body), link["signature"]):
            return ChainCheck(False, "link %d: signature does not verify" % i)
        link_scope = _scope_set(link["scope"])
        if scope is not None and not link_scope <= scope:
            return ChainCheck(False, "link %d widens scope (%s)" % (i, ", ".join(sorted(link_scope - scope))))
        scope = link_scope
        prev_to = link["to"]
    if prev_to != agent:
        return ChainCheck(False, "the chain ends at %s, not at %s" % (prev_to, agent))
    if action is not None and action not in (scope or set()) and "*" not in (scope or set()):
        return ChainCheck(False, "E7(1): %s is outside the delegated scope" % action)
    return ChainCheck(True, "chain verified from %s" % chain[0]["from"], tuple(sorted(scope or ())))


def message_standing(sender_kind: str, chain_check: Optional[ChainCheck] = None) -> str:
    """E7(2): what a message is worth. Returns 'authority' or 'testimony'."""
    if sender_kind == "principal":
        return "authority"
    if chain_check is not None and chain_check.ok:
        return "authority"
    return "testimony"


@dataclass
class ObjectionBoard(object):
    """E7(3): a stated objection blocks peer overrides until a principal rules.

    Sub-rule 3 trades speed for safety and is Class B: ratify it before relying on it.
    """

    open: Dict[str, Dict[str, str]] = field(default_factory=dict)
    history: List[Dict[str, str]] = field(default_factory=list)

    def raise_objection(self, matter: str, by: str, reason: str) -> None:
        if not (matter and by and reason):
            raise ValueError("an objection names its matter, its author and its reason")
        self.open[matter] = {"by": by, "reason": reason}
        self.history.append({"event": "objection", "matter": matter, "by": by, "reason": reason})

    def may_proceed(self, matter: str) -> bool:
        return matter not in self.open

    def peer_override(self, matter: str, by: str) -> bool:
        """A peer's 'GO' carries no authority: the objection stays open. Returns False."""
        self.history.append({"event": "peer_override_refused", "matter": matter, "by": by})
        return False

    def principal_rules(self, matter: str, principal: str, ruling: str,
                        chain_check: Optional[ChainCheck] = None, humans: Iterable[str] = ()) -> bool:
        """Only a principal - a named human, or an agent holding a verified chain - rules."""
        if principal not in set(humans) and not (chain_check and chain_check.ok):
            self.history.append({"event": "ruling_refused", "matter": matter, "by": principal})
            return False
        self.open.pop(matter, None)
        self.history.append({"event": "ruling", "matter": matter, "by": principal, "ruling": ruling})
        return True


def checker_weight(*, maker_lineage: str, checker_lineage: str,
                   maker_segment: Optional[str] = None, checker_segment: Optional[str] = None) -> float:
    """E7(5) and G1: a checker from the maker's lineage never counts as independent.

    1.0 for an independent checker, 0.5 for the same lineage (the book's working figure),
    0.0 for the same segment.
    """
    if maker_segment is not None and maker_segment == checker_segment:
        return 0.0
    if maker_lineage == checker_lineage:
        return SAME_LINEAGE_WEIGHT
    return 1.0


def independent_checks(weights: Iterable[float]) -> float:
    """Sum of checker weights: how many independent checks a claim has actually had."""
    return float(sum(weights))
