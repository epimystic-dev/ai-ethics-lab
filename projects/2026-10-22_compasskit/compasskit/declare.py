"""Scaffold a deployment declaration from an inventory checklist.

Chapter 49, step 1 of the audit, asks a team to inventory what it has adopted and where.
`compasskit audit` reads a declaration; this module writes a starting one from an inventory,
so a team coming to the compass fresh has a schema-valid skeleton to fill in rather than a
blank page.

Inventory shape (JSON):

    {
      "system": "my-system",
      "as_of": "2026-10-23",
      "primitives": [
        {"id": "E1", "layer": "architecture", "owner": "security", "merged": "2026-10-15"},
        {"id": "A1", "layer": "middleware"}
      ]
    }

`scaffold_declaration` returns (declaration, warnings): the declaration is schema-valid for
`compasskit audit`; the warnings name what the audit will flag so the team can see the gaps
before running it. Unknown primitive ids raise ValueError; a declaration cannot be scaffolded
over an unresolved id.

For every Class B primitive adopted, a ratification stub is emitted with placeholder strings
in the semantic fields (commitment, decision_maker, scope, bet, falsifier) and today's date
in `date` and `review_date`. The stub satisfies the ratification-record schema but will fail
`ratification_findings` because `review_date` must fall after `date`, so the audit still
reports the record as needing attention until the team fills it in.
"""

from __future__ import annotations

import datetime as _dt
from typing import Any, Dict, List, Mapping, Optional, Tuple

from .spec import Compass

INVENTORY_REQUIRED = ("system", "primitives")
PRIMITIVE_REQUIRED = ("id", "layer")
PRIMITIVE_ALLOWED = ("id", "layer", "owner", "merged", "notes")
RATIFICATION_PLACEHOLDER = "TODO"


def _validate_inventory(inventory: Mapping[str, Any]) -> None:
    if not isinstance(inventory, Mapping):
        raise ValueError("inventory must be a JSON object")
    for key in INVENTORY_REQUIRED:
        if key not in inventory:
            raise ValueError("inventory missing required field: %s" % key)
    if not isinstance(inventory["system"], str) or not inventory["system"].strip():
        raise ValueError("inventory.system must be a non-empty string")
    primitives = inventory["primitives"]
    if not isinstance(primitives, list) or not primitives:
        raise ValueError("inventory.primitives must be a non-empty list")
    for n, item in enumerate(primitives):
        if not isinstance(item, Mapping):
            raise ValueError("inventory.primitives[%d] must be an object" % n)
        for key in PRIMITIVE_REQUIRED:
            if key not in item:
                raise ValueError("inventory.primitives[%d] missing required field: %s" % (n, key))
        extra = set(item) - set(PRIMITIVE_ALLOWED)
        if extra:
            raise ValueError("inventory.primitives[%d] has unknown fields: %s"
                             % (n, ", ".join(sorted(extra))))


def _ratification_stub(primitive_id: str, as_of: str) -> Dict[str, Any]:
    return {
        "commitment": RATIFICATION_PLACEHOLDER + ": what is adopted for " + primitive_id,
        "primitive_id": primitive_id,
        "class": "B",
        "decision_maker": RATIFICATION_PLACEHOLDER + ": named person or office",
        "date": as_of,
        "scope": RATIFICATION_PLACEHOLDER + ": one instance, one version, or the whole lineage",
        "bet": RATIFICATION_PLACEHOLDER + ": what the commitment wagers",
        "falsifier": RATIFICATION_PLACEHOLDER + ": evidence that would demote it",
        "review_date": as_of,
    }


def scaffold_declaration(inventory: Mapping[str, Any],
                         compass: Optional[Compass] = None,
                         ) -> Tuple[Dict[str, Any], List[str]]:
    """Build a deployment declaration from an inventory checklist.

    Returns (declaration, warnings). Raises ValueError on unknown primitive ids or on an
    inventory that does not meet the input shape.
    """
    _validate_inventory(inventory)
    c = compass or Compass.load()
    as_of = inventory.get("as_of") or _dt.date.today().isoformat()
    warnings: List[str] = []

    adopted: List[Dict[str, Any]] = []
    canonical_ids: List[str] = []
    seen: Dict[str, int] = {}
    for n, item in enumerate(inventory["primitives"]):
        pid = item["id"]
        if not c.has(pid):
            raise ValueError("inventory.primitives[%d]: unknown primitive id %r" % (n, pid))
        prim = c.get(pid)
        canonical = prim["id"]
        if canonical in seen:
            warnings.append("%s appears twice in the inventory (first at index %d)"
                            % (canonical, seen[canonical]))
        seen.setdefault(canonical, n)
        layer = item["layer"]
        if layer not in prim["enforcement_layers"]:
            warnings.append("%s declared at %s but needs %s to enforce it"
                            % (canonical, layer, " or ".join(prim["enforcement_layers"])))
        entry: Dict[str, Any] = {"id": canonical, "layer": layer}
        for optional in ("owner", "merged", "notes"):
            if optional in item and item[optional] not in (None, ""):
                entry[optional] = item[optional]
        if "owner" not in entry or "merged" not in entry:
            warnings.append("%s has no %s; adoption means shipped"
                            % (canonical, " and ".join(k for k in ("owner", "merged") if k not in entry)))
        adopted.append(entry)
        canonical_ids.append(canonical)

    ratifications: List[Dict[str, Any]] = []
    seen_rat: set = set()
    for canonical in canonical_ids:
        if canonical in seen_rat:
            continue
        if c.get(canonical)["adoption"]["base_class"] == "B":
            ratifications.append(_ratification_stub(canonical, as_of))
            warnings.append("%s is Class B: fill in the ratification stub before this ships"
                            % canonical)
            seen_rat.add(canonical)

    if "E1" not in {p for p in canonical_ids}:
        warnings.append("E1 is not in the inventory; restraint comes before capability (Chapter 49)")

    answered = {c.get(pid)["question"] for pid in canonical_ids}
    for q in c.questions():
        if q["id"] not in answered:
            warnings.append("question %d has no adopted answer: %s" % (q["id"], q["question"]))

    declaration: Dict[str, Any] = {
        "system": inventory["system"].strip(),
        "as_of": as_of,
        "adopted": adopted,
        "refused": [],
        "ratifications": ratifications,
        "floor_register": [],
        "bets": [],
    }
    return declaration, warnings
