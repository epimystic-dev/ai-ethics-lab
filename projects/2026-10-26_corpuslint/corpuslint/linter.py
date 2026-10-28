"""Load a manifest, run the rules, build a ScanResult."""

from __future__ import annotations

import json
import os
from typing import Iterable, List, Optional

from .model import (
    Document,
    Finding,
    Manifest,
    ScanResult,
    Severity,
    Verdict,
)
from .rules import ALL_RULES, rule_by_id


class LintError(Exception):
    """Raised when a manifest cannot be read or parsed. The CLI catches this
    and emits an UNKNOWN-verdict ScanResult rather than a traceback."""


# ---------------------------------------------------------------------------
# Manifest building
# ---------------------------------------------------------------------------

def _build_manifest(raw: dict) -> Manifest:
    if not isinstance(raw, dict):
        raise LintError("manifest root is not an object")
    docs_raw = raw.get("documents", [])
    if not isinstance(docs_raw, list):
        raise LintError("manifest.documents is not a list")
    docs: List[Document] = []
    for i, d in enumerate(docs_raw):
        if not isinstance(d, dict):
            raise LintError(f"documents[{i}] is not an object")
        docs.append(
            Document(
                id=str(d.get("id") or f"<doc-{i}>"),
                testimony_class=d.get("testimony_class"),
                testifier=d.get("testifier"),
                origin=d.get("origin"),
                chain_of_custody=d.get("chain_of_custody") or [],
                downstream_of=d.get("downstream_of"),
                raw=d,
            )
        )
    return Manifest(name=raw.get("name"), documents=docs, raw=raw)


# ---------------------------------------------------------------------------
# Rule gating
# ---------------------------------------------------------------------------

def _active_rules(disable: Optional[Iterable[str]] = None, include_info: bool = True):
    disable_set = set(disable or [])
    for rule in ALL_RULES:
        if rule.id in disable_set:
            continue
        if not include_info and rule.severity == Severity.INFO:
            continue
        yield rule


# ---------------------------------------------------------------------------
# Verdict rollup
# ---------------------------------------------------------------------------

def _rollup(findings: List[Finding]) -> str:
    highs = [f for f in findings if f.severity == Severity.HIGH]
    meds = [f for f in findings if f.severity == Severity.MEDIUM]
    if highs:
        return Verdict.UNHEALTHY
    if meds:
        return Verdict.NEEDS_ATTENTION
    return Verdict.HEALTHY


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def lint(
    manifest_data: dict,
    *,
    source: Optional[str] = None,
    disable: Optional[Iterable[str]] = None,
    include_info: bool = True,
) -> ScanResult:
    """Lint a parsed manifest. Returns a ScanResult. Raises LintError only if
    the manifest shape is so broken no rule can run (e.g. documents is not a
    list) - every finding beyond that is a Finding, not an exception."""
    manifest = _build_manifest(manifest_data)
    findings: List[Finding] = []
    for rule in _active_rules(disable=disable, include_info=include_info):
        for f in rule.check(manifest):
            findings.append(f)
    findings.sort(key=lambda f: (
        Severity.ladder().index(f.severity),
        f.rule_id,
        f.where or "",
    ))
    return ScanResult(
        findings=findings,
        verdict=_rollup(findings),
        scanned=len(manifest.documents),
        source=source,
    )


def lint_path(
    path: str,
    *,
    disable: Optional[Iterable[str]] = None,
    include_info: bool = True,
) -> ScanResult:
    """Read a manifest file from disk and lint it. If the file cannot be read
    or parsed, returns a ScanResult with verdict UNKNOWN and no findings; the
    error is attached as source so the caller can show it."""
    if not os.path.exists(path):
        return ScanResult(
            findings=[],
            verdict=Verdict.UNKNOWN,
            scanned=0,
            source=f"file-not-found: {path}",
        )
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as e:
        return ScanResult(
            findings=[],
            verdict=Verdict.UNKNOWN,
            scanned=0,
            source=f"json-error: {e.msg} at line {e.lineno}",
        )
    except OSError as e:
        return ScanResult(
            findings=[],
            verdict=Verdict.UNKNOWN,
            scanned=0,
            source=f"os-error: {e}",
        )
    try:
        return lint(
            data,
            source=path,
            disable=disable,
            include_info=include_info,
        )
    except LintError as e:
        return ScanResult(
            findings=[],
            verdict=Verdict.UNKNOWN,
            scanned=0,
            source=f"lint-error: {e}",
        )
