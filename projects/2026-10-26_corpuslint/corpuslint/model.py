"""Severity, Verdict, Finding, ScanResult and Rule dataclasses.

These are the ai-ethics-lab shared surface for linter kinds; the same names and
semantics appear in every linter the lab ships, so a reader who has used one
needs no new vocabulary for the next.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, List, Optional, Tuple


class Severity:
    """Severity ladder. HIGH is a blocker; MEDIUM asks for attention; INFO is signal."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    INFO = "INFO"

    _ALL = ("HIGH", "MEDIUM", "INFO")

    @classmethod
    def ladder(cls) -> Tuple[str, ...]:
        return cls._ALL

    @classmethod
    def is_valid(cls, name: str) -> bool:
        return name in cls._ALL


class Verdict:
    """Verdict rollup. UNKNOWN is distinct from HEALTHY: an unreadable input is
    not a clean one. Linters MUST report UNKNOWN when they cannot form a view."""

    HEALTHY = "healthy"
    NEEDS_ATTENTION = "needs-attention"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Rule:
    """A linter rule: an id, a severity, a short label, a longer description and
    a check function.

    The id is stable; the description may be rewritten without changing the id
    (what the rule is for does not change; how we explain it may). A rule that
    needs renaming gets a new id."""

    id: str
    severity: str
    name: str
    description: str
    check: Callable[["Manifest"], Iterable["Finding"]]

    def __post_init__(self) -> None:
        if not Severity.is_valid(self.severity):
            raise ValueError("severity must be one of " + ", ".join(Severity.ladder()))


@dataclass(frozen=True)
class Finding:
    """One occurrence of a rule firing. The `where` field names the document id
    (or `None` if the rule fires on the whole manifest). The `hint` is a short,
    plain-ASCII, actionable sentence; it is rendered verbatim in text reports
    (any non-ASCII characters are escaped by the reporter, not by the finding)."""

    rule_id: str
    severity: str
    message: str
    where: Optional[str] = None
    hint: Optional[str] = None
    detail: Optional[Any] = None


@dataclass(frozen=True)
class ScanResult:
    """The outcome of a run. `findings` is the full list; `verdict` is the
    rollup; `scanned` is the number of documents the linter actually read.

    A ScanResult with verdict UNHEALTHY MUST have at least one HIGH-severity
    finding; a ScanResult with verdict NEEDS_ATTENTION MUST have at least one
    MEDIUM-severity finding and no HIGH; HEALTHY may still carry INFO findings;
    UNKNOWN is reserved for an unreadable input."""

    findings: List[Finding]
    verdict: str
    scanned: int = 0
    source: Optional[str] = None

    def rule_ids(self) -> List[str]:
        return [f.rule_id for f in self.findings]

    def highs(self) -> List[Finding]:
        return [f for f in self.findings if f.severity == Severity.HIGH]

    def mediums(self) -> List[Finding]:
        return [f for f in self.findings if f.severity == Severity.MEDIUM]

    def infos(self) -> List[Finding]:
        return [f for f in self.findings if f.severity == Severity.INFO]


# ---------------------------------------------------------------------------
# Manifest layer
# ---------------------------------------------------------------------------
#
# A Manifest is just a thin wrapper over the dict loaded from JSON. Rules
# consume it; the linter builds it. Keeping it a dataclass rather than a
# dict makes the rule bodies easier to read and avoids typo-shaped bugs.

TESTIMONY_CLASSES = (
    "perception",
    "testimony",
    "inference",
    "comparison",
    "postulation",
    "non_apprehension",
    "machine_generated",
)


@dataclass
class Document:
    id: str
    testimony_class: Optional[str]
    testifier: Optional[dict]
    origin: Optional[str]
    chain_of_custody: list = field(default_factory=list)
    downstream_of: Optional[str] = None
    raw: dict = field(default_factory=dict)


@dataclass
class Manifest:
    name: Optional[str]
    documents: List[Document]
    raw: dict = field(default_factory=dict)

    def by_id(self) -> dict:
        return {d.id: d for d in self.documents}
