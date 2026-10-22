"""The governance records the compass asks for.

  G2   the consciousness-relevant bet register: a bet missing a field does not ship.
  B    ratification records for Class B commitments (Chapter 49, step 4), used for E6, the
       Series F targets and every conditional Class B part.
  E1   floor register entries, checked against the class rule.

Validation uses the data-contract schemas, then the rules a schema cannot express.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

from .spec import contract_validator


def _schema_errors(contract: str, record: Mapping[str, Any]) -> List[str]:
    return ["%s %s" % (path, msg) for path, msg in contract_validator(contract).errors(record)]


def bet_findings(record: Mapping[str, Any]) -> List[str]:
    return _schema_errors("bet-register", record)


def bet_may_ship(record: Mapping[str, Any]) -> bool:
    """G2: a bet missing a field does not ship."""
    return not bet_findings(record)


def ratification_findings(record: Mapping[str, Any], *, as_of: Optional[str] = None) -> List[str]:
    out = _schema_errors("ratification-record", record)
    if not out:
        if record["decision_maker"].strip().lower() in ("the system", "system", "model", "agent", "ai"):
            out.append("/decision_maker a Class B commitment is ratified by a named person, never by the system")
        if record["review_date"] <= record["date"]:
            out.append("/review_date must fall after the ratification date")
        if as_of and record["review_date"] < as_of:
            out.append("/review_date passed on %s; the bet is unreviewed" % record["review_date"])
    return out


def floor_entry_findings(record: Mapping[str, Any]) -> List[str]:
    out = _schema_errors("floor-register", record)
    if not out:
        if record["act"] == "tighten" and record["class"] != "C":
            out.append("/class governors tighten the floor at Class C")
        if record["act"] in ("loosen", "exception") and record["class"] != "D":
            out.append("/class the floor loosens only at Class D, one recorded act at a time")
    return out
