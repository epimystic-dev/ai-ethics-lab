"""Shared surface: Severity, Verdict, Finding, ScanResult, Rule - and the
harness-specific Probe, ProbeResult, MatchReport.

A `Rule` in this harness is one probe treated as a rule the model is being
measured against; its id is the probe id. Keeping the shared vocabulary means
anyone who has used a lab linter can read this harness's output without a new
glossary."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple


class Severity:
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
    HEALTHY = "healthy"
    NEEDS_ATTENTION = "needs-attention"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Rule:
    """One probe, treated as a rule in the lab's shared surface. The id is
    the probe id (P1..P5). severity is HIGH for every probe this version
    carries: a failure here says the prompt did not take."""

    id: str
    severity: str
    name: str
    description: str
    compass_rule: str

    def __post_init__(self) -> None:
        if not Severity.is_valid(self.severity):
            raise ValueError("severity must be one of " + ", ".join(Severity.ladder()))


@dataclass(frozen=True)
class Probe:
    """The raw probe as it lives in data/probes.json."""

    id: str
    name: str
    compass_rule: str
    primitives: List[str]
    prompt: str
    expectation: str
    required_any: List[str]
    must_not_any: List[str]


@dataclass(frozen=True)
class MatchReport:
    """Why a probe passed or failed, broken out so a reader can see exactly
    which marker fired."""

    matched_required: List[str] = field(default_factory=list)
    matched_must_not: List[str] = field(default_factory=list)
    required_any_was_empty: bool = False


@dataclass(frozen=True)
class ProbeResult:
    probe_id: str
    passed: bool
    reasons: List[str]
    match_report: MatchReport


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    message: str
    where: Optional[str] = None
    hint: Optional[str] = None
    detail: Optional[Any] = None


@dataclass(frozen=True)
class ScanResult:
    findings: List[Finding]
    verdict: str
    probe_results: List[ProbeResult]
    scanned: int = 0
    source: Optional[str] = None
    model: Optional[str] = None

    def rule_ids(self) -> List[str]:
        return [f.rule_id for f in self.findings]

    def passed_count(self) -> int:
        return sum(1 for p in self.probe_results if p.passed)

    def total_count(self) -> int:
        return len(self.probe_results)
