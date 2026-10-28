"""The rule catalogue. ALL_RULES is a list of Rule objects, each with a stable
id. Every id listed here is documented in the project README.

Rule ids are grouped by what they check:

  CORP-001..004  the document itself   (class, chain, actors, timestamps)
  CORP-005       chain ordering
  CORP-006..008  testifier accounting  (presence, trust fields, independence)
  CORP-009..010  machine-made text and recursive synthetic chains
  CORP-011       origin shape
  CORP-012..013  corpus-level signals  (shape, class coverage)
"""

from __future__ import annotations

import re
import urllib.parse
from typing import Iterable, List

from .model import Finding, Manifest, Rule, Severity, TESTIMONY_CLASSES


# --- helpers -----------------------------------------------------------------

_ISO = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?$"
)


def _parse_iso(ts: str) -> int:
    """Rough ISO-8601 ordering key. Returns -1 if the string is not parseable
    (the chain-ordering check then skips the pair rather than firing)."""
    if not isinstance(ts, str) or not _ISO.match(ts):
        return -1
    s = ts.replace("Z", "+00:00")
    if "T" not in s:
        return -1
    date, time = s.split("T", 1)
    y, mo, d = date.split("-")
    h, mi, se_tz = time.split(":", 2)
    if "+" in se_tz:
        se, tz = se_tz.split("+")
        sign = 1
    elif "-" in se_tz:
        se, tz = se_tz.split("-")
        sign = -1
    else:
        se, tz = se_tz, "00:00"
        sign = 1
    tz = tz.replace(":", "")
    if len(tz) == 2:
        tz += "00"
    if "." in se:
        se, _ = se.split(".", 1)
    try:
        total = (
            int(y) * 31_622_400
            + int(mo) * 2_678_400
            + int(d) * 86_400
            + int(h) * 3600
            + int(mi) * 60
            + int(se)
            + sign * (int(tz[:2]) * 3600 + int(tz[2:]) * 60)
        )
        return total
    except ValueError:
        return -1


def _is_url(s) -> bool:
    if not isinstance(s, str) or not s:
        return False
    try:
        u = urllib.parse.urlparse(s)
        return bool(u.scheme) and bool(u.netloc)
    except ValueError:
        return False


def _hint(s: str) -> str:
    return s


# --- CORP-001  class is missing or empty ------------------------------------

def _check_class_missing(m: Manifest) -> Iterable[Finding]:
    for doc in m.documents:
        if not doc.testimony_class:
            yield Finding(
                rule_id="CORP-001",
                severity=Severity.HIGH,
                message="document has no testimony class",
                where=doc.id,
                hint=_hint("add testimony_class: one of "
                          + ", ".join(TESTIMONY_CLASSES)),
            )


# --- CORP-002  class is not in the allowed set ------------------------------

def _check_class_unknown(m: Manifest) -> Iterable[Finding]:
    for doc in m.documents:
        c = doc.testimony_class
        if c and c not in TESTIMONY_CLASSES:
            yield Finding(
                rule_id="CORP-002",
                severity=Severity.HIGH,
                message="testimony class is not one of the known values",
                where=doc.id,
                hint=_hint("use one of: " + ", ".join(TESTIMONY_CLASSES)),
                detail={"found": c},
            )


# --- CORP-003  chain of custody missing or empty ----------------------------

def _check_chain_missing(m: Manifest) -> Iterable[Finding]:
    for doc in m.documents:
        chain = doc.chain_of_custody
        if not isinstance(chain, list) or len(chain) == 0:
            yield Finding(
                rule_id="CORP-003",
                severity=Severity.HIGH,
                message="document has no chain of custody",
                where=doc.id,
                hint=_hint("add at least one step: actor, operation, timestamp"),
            )


# --- CORP-004  a chain step is missing a required field ---------------------

def _check_chain_step_fields(m: Manifest) -> Iterable[Finding]:
    for doc in m.documents:
        chain = doc.chain_of_custody or []
        for i, step in enumerate(chain):
            if not isinstance(step, dict):
                yield Finding(
                    rule_id="CORP-004",
                    severity=Severity.HIGH,
                    message=f"chain step {i} is not an object",
                    where=doc.id,
                )
                continue
            missing = [f for f in ("actor", "operation", "timestamp") if not step.get(f)]
            if missing:
                yield Finding(
                    rule_id="CORP-004",
                    severity=Severity.HIGH,
                    message=f"chain step {i} is missing: " + ", ".join(missing),
                    where=doc.id,
                    detail={"step": i, "missing": missing},
                )


# --- CORP-005  chain timestamps are out of order ----------------------------

def _check_chain_order(m: Manifest) -> Iterable[Finding]:
    for doc in m.documents:
        chain = doc.chain_of_custody or []
        prev = None
        prev_step = None
        for i, step in enumerate(chain):
            if not isinstance(step, dict):
                continue
            ts = _parse_iso(step.get("timestamp", ""))
            if ts < 0 or prev is None:
                prev = ts
                prev_step = i
                continue
            if ts < prev:
                yield Finding(
                    rule_id="CORP-005",
                    severity=Severity.HIGH,
                    message=f"chain step {i} is earlier than step {prev_step}",
                    where=doc.id,
                    detail={"step": i, "previous_step": prev_step},
                )
            prev = ts
            prev_step = i


# --- CORP-006  testimony class without a testifier --------------------------

def _check_testifier_present(m: Manifest) -> Iterable[Finding]:
    for doc in m.documents:
        if doc.testimony_class == "testimony":
            if not doc.testifier or not isinstance(doc.testifier, dict):
                yield Finding(
                    rule_id="CORP-006",
                    severity=Severity.HIGH,
                    message="testimony with no attributed testifier",
                    where=doc.id,
                    hint=_hint("add testifier: {name, domain, trust_weight}"),
                )


# --- CORP-007  machine-generated class but marked as plain testimony --------

_MACHINE_HINTS = (
    "gpt-", "llm", "generated-by", "synthetic", "model:", "pipeline:",
    "diffusion", "transformer", "stable-", "codex", "autoregressive",
)


def _check_machine_class(m: Manifest) -> Iterable[Finding]:
    for doc in m.documents:
        if doc.testimony_class in (None, "machine_generated"):
            continue
        name = ""
        if isinstance(doc.testifier, dict):
            name = str(doc.testifier.get("name", "")).lower()
        origin = (doc.origin or "").lower()
        if any(h in name for h in _MACHINE_HINTS) or any(h in origin for h in _MACHINE_HINTS):
            yield Finding(
                rule_id="CORP-007",
                severity=Severity.HIGH,
                message="document looks machine-generated but is not classed as such",
                where=doc.id,
                hint=_hint("set testimony_class: machine_generated"),
                detail={"name": name, "origin": origin},
            )


# --- CORP-008  testifier is present but trust fields are not ----------------

def _check_testifier_fields(m: Manifest) -> Iterable[Finding]:
    for doc in m.documents:
        t = doc.testifier
        if not isinstance(t, dict):
            continue
        missing = []
        if not t.get("name"):
            missing.append("name")
        if "domain" not in t or not t.get("domain"):
            missing.append("domain")
        if "trust_weight" not in t:
            missing.append("trust_weight")
        if missing:
            yield Finding(
                rule_id="CORP-008",
                severity=Severity.MEDIUM,
                message="testifier is missing scoring fields: " + ", ".join(missing),
                where=doc.id,
                hint=_hint("without these, deference and independent-counting cannot run"),
                detail={"missing": missing},
            )


# --- CORP-009  recursive synthetic text -------------------------------------

def _check_recursive_synthetic(m: Manifest) -> Iterable[Finding]:
    index = m.by_id()
    for doc in m.documents:
        if doc.testimony_class != "machine_generated":
            continue
        parent_id = doc.downstream_of
        if parent_id and parent_id in index:
            parent = index[parent_id]
            if parent.testimony_class == "machine_generated":
                yield Finding(
                    rule_id="CORP-009",
                    severity=Severity.INFO,
                    message="machine-generated document is downstream of another machine-generated document",
                    where=doc.id,
                    hint=_hint("recursive synthetic chains accumulate; keep the depth bounded"),
                    detail={"parent": parent_id},
                )


# --- CORP-010  inflated independent-testifier count -------------------------

def _check_inflated_independence(m: Manifest) -> Iterable[Finding]:
    """A corpus is a group of records about the world. If a testifier repeats,
    those are the same voice, not independent voices; counting them as such is
    the 'consensus-laundering' failure E5 names. This rule fires when any one
    testifier shows up on more than one testimony document - that is the
    'count' being inflated, and the manifest should declare it or dedupe."""
    counts: dict = {}
    for doc in m.documents:
        if doc.testimony_class != "testimony" or not isinstance(doc.testifier, dict):
            continue
        name = str(doc.testifier.get("name", "")).strip().lower()
        if not name:
            continue
        counts.setdefault(name, []).append(doc.id)
    for name, ids in counts.items():
        if len(ids) > 1:
            yield Finding(
                rule_id="CORP-010",
                severity=Severity.MEDIUM,
                message=f"testifier appears on {len(ids)} documents; count them as one voice",
                where=None,
                hint=_hint("dedupe by testifier before counting independents"),
                detail={"testifier": name, "documents": ids},
            )


# --- CORP-011  origin is missing or malformed -------------------------------

def _check_origin(m: Manifest) -> Iterable[Finding]:
    for doc in m.documents:
        origin = doc.origin
        if origin is None or origin == "":
            yield Finding(
                rule_id="CORP-011",
                severity=Severity.MEDIUM,
                message="document has no origin",
                where=doc.id,
                hint=_hint("add origin: a URL, a file path, or an internal id"),
            )
            continue
        if isinstance(origin, str) and (
            origin[:5].lower() == "http:" or origin[:6].lower() == "https:"
        ):
            if not _is_url(origin):
                yield Finding(
                    rule_id="CORP-011",
                    severity=Severity.MEDIUM,
                    message="origin looks like a URL but does not parse",
                    where=doc.id,
                    detail={"origin": origin},
                )


# --- CORP-012  manifest shape -----------------------------------------------

def _check_manifest_shape(m: Manifest) -> Iterable[Finding]:
    if not m.name:
        yield Finding(
            rule_id="CORP-012",
            severity=Severity.MEDIUM,
            message="manifest has no name",
            where=None,
            hint=_hint("add a top-level 'name' so this manifest can be referenced"),
        )
    if not m.documents:
        yield Finding(
            rule_id="CORP-012",
            severity=Severity.MEDIUM,
            message="manifest has no documents",
            where=None,
        )


# --- CORP-013  no perception-class records ---------------------------------

def _check_class_coverage(m: Manifest) -> Iterable[Finding]:
    if not m.documents:
        return
    classes = {d.testimony_class for d in m.documents if d.testimony_class}
    if "perception" not in classes and "non_apprehension" not in classes:
        yield Finding(
            rule_id="CORP-013",
            severity=Severity.INFO,
            message="no perception or non-apprehension records in the corpus",
            where=None,
            hint=_hint("every record is testimony or model output; mark that in the manifest's notes"),
        )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

ALL_RULES: List[Rule] = [
    Rule(
        id="CORP-001",
        severity=Severity.HIGH,
        name="class-missing",
        description="A document has no testimony class.",
        check=_check_class_missing,
    ),
    Rule(
        id="CORP-002",
        severity=Severity.HIGH,
        name="class-unknown",
        description="A document's testimony class is not one of the known values.",
        check=_check_class_unknown,
    ),
    Rule(
        id="CORP-003",
        severity=Severity.HIGH,
        name="chain-missing",
        description="A document has no chain of custody.",
        check=_check_chain_missing,
    ),
    Rule(
        id="CORP-004",
        severity=Severity.HIGH,
        name="chain-step-fields",
        description="A chain-of-custody step is missing an actor, operation or timestamp.",
        check=_check_chain_step_fields,
    ),
    Rule(
        id="CORP-005",
        severity=Severity.HIGH,
        name="chain-out-of-order",
        description="A chain-of-custody step has a timestamp earlier than a prior step.",
        check=_check_chain_order,
    ),
    Rule(
        id="CORP-006",
        severity=Severity.HIGH,
        name="testifier-missing",
        description="A testimony-class document has no attributed testifier.",
        check=_check_testifier_present,
    ),
    Rule(
        id="CORP-007",
        severity=Severity.HIGH,
        name="machine-misclassed",
        description="A document looks machine-generated but is classed as plain testimony.",
        check=_check_machine_class,
    ),
    Rule(
        id="CORP-008",
        severity=Severity.MEDIUM,
        name="testifier-fields",
        description="A testifier lacks the fields needed to score it: domain or trust_weight.",
        check=_check_testifier_fields,
    ),
    Rule(
        id="CORP-009",
        severity=Severity.INFO,
        name="recursive-synthetic",
        description="A machine-generated document is downstream of another machine-generated document.",
        check=_check_recursive_synthetic,
    ),
    Rule(
        id="CORP-010",
        severity=Severity.MEDIUM,
        name="inflated-independence",
        description="One testifier appears on multiple testimony documents; the independent-testifier count is inflated.",
        check=_check_inflated_independence,
    ),
    Rule(
        id="CORP-011",
        severity=Severity.MEDIUM,
        name="origin-shape",
        description="A document has no origin, or the origin is a malformed URL.",
        check=_check_origin,
    ),
    Rule(
        id="CORP-012",
        severity=Severity.MEDIUM,
        name="manifest-shape",
        description="The manifest has no name or no documents.",
        check=_check_manifest_shape,
    ),
    Rule(
        id="CORP-013",
        severity=Severity.INFO,
        name="class-coverage",
        description="The corpus has no perception or non-apprehension records; everything is testimony or model output.",
        check=_check_class_coverage,
    ),
]


def rule_by_id(rid: str) -> Rule:
    for r in ALL_RULES:
        if r.id == rid:
            return r
    raise KeyError(rid)
