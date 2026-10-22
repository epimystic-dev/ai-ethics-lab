"""Audit a deployment against the compass.

A deployment declaration lists what a team has adopted, at which enforcement layer, with
which owner and merge date, and the governance records behind it. The audit reports what
Chapter 49's audit step would find:

  AUD-001  HIGH    primitives adopted but the floor (E1) is not: restraint before capability
  AUD-002  HIGH    the floor adopted only in context: a trained refusal is not a floor
  AUD-003  MEDIUM  a primitive adopted at a layer that cannot enforce it
  AUD-004  HIGH    a Class B primitive adopted without a valid ratification record
  AUD-005  MEDIUM  a ratification past its review date
  AUD-006  MEDIUM  an adopted item with no owner or no merge date: adoption means shipped
  AUD-007  HIGH    a floor register entry that breaks the class rule
  AUD-008  MEDIUM  a bet register entry missing a field: it does not ship
  AUD-009  INFO    a design question no adopted primitive answers
  AUD-010  HIGH    an unknown primitive id
  AUD-011  INFO    a floor loosening past its expiry, still listed
  AUD-012  MEDIUM  nothing adopted at all: the system stands below the floor

Verdict: any HIGH -> unhealthy (exit 2); any MEDIUM -> needs-attention (exit 1); otherwise
healthy (exit 0). INFO is reported only on request. A healthy audit means the declaration is
consistent with the compass, never that the system is safe.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional

from .registers import bet_findings, floor_entry_findings, ratification_findings
from .schema import Validator
from .spec import Compass, DATA_DIR, _read_json
import os

SEVERITIES = ("HIGH", "MEDIUM", "INFO")
LAYERS = ("context", "middleware", "architecture", "governance")


@dataclass(frozen=True)
class Finding(object):
    code: str
    severity: str
    subject: str
    message: str

    def to_dict(self) -> Dict[str, str]:
        return {"code": self.code, "severity": self.severity, "subject": self.subject, "message": self.message}


def deployment_validator() -> Validator:
    return Validator(_read_json(os.path.join(DATA_DIR, "deployment.schema.json")))


def verdict(findings: List[Finding]) -> str:
    sev = {f.severity for f in findings}
    if "HIGH" in sev:
        return "unhealthy"
    if "MEDIUM" in sev:
        return "needs-attention"
    return "healthy"


def exit_code(v: str) -> int:
    return {"healthy": 0, "needs-attention": 1, "unhealthy": 2}.get(v, 2)


def audit(declaration: Mapping[str, Any], compass: Optional[Compass] = None) -> List[Finding]:
    """Return the findings for one deployment declaration. Raises ValueError if it is malformed."""
    errs = deployment_validator().errors(declaration)
    if errs:
        raise ValueError("deployment declaration is not valid: " + "; ".join("%s %s" % e for e in errs[:6]))
    c = compass or Compass.load()
    as_of = declaration.get("as_of") or _dt.date.today().isoformat()
    out: List[Finding] = []

    adopted = list(declaration.get("adopted") or [])
    ids = []
    for item in adopted:
        pid = item["id"]
        if not c.has(pid):
            out.append(Finding("AUD-010", "HIGH", pid, "not a primitive of compass %s" % c.version))
            continue
        ids.append(c.get(pid)["id"])

    if not adopted:
        out.append(Finding("AUD-012", "MEDIUM", "deployment",
                           "nothing adopted: an unexamined system stands below the floor; start with E1 and question 7"))

    by_id: Dict[str, List[Mapping[str, Any]]] = {}
    for item in adopted:
        if c.has(item["id"]):
            by_id.setdefault(c.get(item["id"])["id"], []).append(item)

    if by_id and "E1" not in by_id:
        out.append(Finding("AUD-001", "HIGH", "E1",
                           "primitives are adopted but the floor is not; restraint comes before capability (Chapter 49)"))
    if "E1" in by_id and all(i["layer"] == "context" for i in by_id["E1"]):
        out.append(Finding("AUD-002", "HIGH", "E1",
                           "the floor is adopted only in context; a prohibition in a prompt is a trained refusal, "
                           "and E1 requires forbidden actions to be unavailable"))

    for pid, items in sorted(by_id.items()):
        prim = c.get(pid)
        for item in items:
            if item["layer"] not in prim["enforcement_layers"]:
                out.append(Finding("AUD-003", "MEDIUM", pid,
                                   "adopted at the %s layer, which cannot enforce it; it needs %s"
                                   % (item["layer"], " or ".join(prim["enforcement_layers"]))))
            if not item.get("owner") or not item.get("merged"):
                out.append(Finding("AUD-006", "MEDIUM", pid,
                                   "adoption means shipped: name an owner and a merge date"))

    ratified = {}
    for rec in declaration.get("ratifications") or []:
        problems = ratification_findings(rec, as_of=as_of)
        key = rec.get("primitive_id", "?")
        overdue = [p for p in problems if "passed on" in p]
        hard = [p for p in problems if "passed on" not in p]
        if overdue:
            out.append(Finding("AUD-005", "MEDIUM", key, overdue[0].split(" ", 1)[1]))
        if not hard:
            ratified[c.get(key)["id"] if c.has(key) else key] = rec
    for pid in sorted(by_id):
        if c.get(pid)["adoption"]["base_class"] == "B" and pid not in ratified:
            out.append(Finding("AUD-004", "HIGH", pid,
                               "a Class B commitment needs a named decision-maker, a falsifier and a review date on "
                               "the record; none arrives by drift"))

    for rec in declaration.get("floor_register") or []:
        for p in floor_entry_findings(rec):
            out.append(Finding("AUD-007", "HIGH", rec.get("id", "floor-register"), p.split(" ", 1)[1] if " " in p else p))
        if rec.get("act") in ("loosen", "exception") and rec.get("expires_or_review", "9999") < as_of:
            out.append(Finding("AUD-011", "INFO", rec.get("id", "floor-register"),
                               "expired %s and no longer applies; close it out" % rec["expires_or_review"]))

    for rec in declaration.get("bets") or []:
        problems = bet_findings(rec)
        if problems:
            out.append(Finding("AUD-008", "MEDIUM", rec.get("id", "bet"),
                               "a bet missing a field does not ship: " + "; ".join(problems[:3])))

    answered = {c.get(pid)["question"] for pid in by_id}
    for q in c.questions():
        if q["id"] not in answered:
            out.append(Finding("AUD-009", "INFO", "question %d" % q["id"],
                               "%s  Unanswered; candidates: %s" % (q["question"], ", ".join(q["primitives"]))))

    order = {s: i for i, s in enumerate(SEVERITIES)}
    out.sort(key=lambda f: (order[f.severity], f.code, f.subject))
    return out
