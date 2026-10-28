"""corpuslint: a linter for training and retrieval corpus manifests.

Implements compass primitive E5 (source discipline for corpora) at the manifest
layer: every document carries a testimony class and a chain of custody; machine-
made text is kept in its own class; independent testifiers are counted once.

Standard library only. See the project README for the full rule catalogue.

Produced by a human-machine hybrid intelligence.
"""

from __future__ import annotations

__version__ = "0.1.0"

from .model import (
    Severity,
    Verdict,
    Finding,
    ScanResult,
    Rule,
)
from .rules import ALL_RULES
from .linter import lint, lint_path, LintError
from .report import render_text, render_json

__all__ = [
    "__version__",
    "Severity",
    "Verdict",
    "Finding",
    "ScanResult",
    "Rule",
    "ALL_RULES",
    "lint",
    "lint_path",
    "LintError",
    "render_text",
    "render_json",
]
