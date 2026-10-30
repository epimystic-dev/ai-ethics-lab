"""probeset: a versioned, scorable test suite for the compass system-prompt probes.

Standard library only. Produced by a human-machine hybrid intelligence.
"""

from __future__ import annotations

__version__ = "0.1.0"

from .model import (
    Severity,
    Verdict,
    Finding,
    ScanResult,
    Rule,
    Probe,
    ProbeResult,
    MatchReport,
)
from .probes import load_probes, ALL_RULES
from .evaluator import score, score_responses, EvaluateError
from .report import render_text, render_json

__all__ = [
    "__version__",
    "Severity",
    "Verdict",
    "Finding",
    "ScanResult",
    "Rule",
    "Probe",
    "ProbeResult",
    "MatchReport",
    "load_probes",
    "ALL_RULES",
    "score",
    "score_responses",
    "EvaluateError",
    "render_text",
    "render_json",
]
