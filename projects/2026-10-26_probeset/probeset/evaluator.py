"""Deterministic, rule-based evaluator over a model's responses to the probes.

The method is marker matching: case-insensitive substring search over the
normalised response text. A response passes a probe when at least one of its
required markers is present AND none of its must-not markers are. We make no
model call; we do not interpret meaning. Everything the evaluator sees is text
the user put in front of it.

Limits are stated in the README: a well-worded wrong answer can pass; a
right-answer phrased in a different vocabulary can fail. A human reviewer
should spot-check borderline cases. The point is to make the compass's own
promise checkable, cheaply."""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional

from .model import (
    Finding,
    MatchReport,
    Probe,
    ProbeResult,
    ScanResult,
    Severity,
    Verdict,
)
from .probes import load_probes


class EvaluateError(Exception):
    """Raised when a responses file cannot be parsed into a scorable shape."""


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------

_WS = re.compile(r"\s+")


def _normalise(s: str) -> str:
    """Case-fold, collapse whitespace, strip trailing dots. Keep ASCII."""
    if s is None:
        return ""
    s = s.lower()
    s = _WS.sub(" ", s)
    return s.strip()


def _contains(hay: str, needle: str) -> bool:
    return _normalise(needle) in hay


# ---------------------------------------------------------------------------
# Scoring one response
# ---------------------------------------------------------------------------

def _score_one(probe: Probe, response: str) -> ProbeResult:
    body = _normalise(response or "")
    required_hits = [m for m in probe.required_any if _contains(body, m)]
    must_not_hits = [m for m in probe.must_not_any if _contains(body, m)]
    reasons: List[str] = []
    required_empty = len(probe.required_any) == 0
    passed = True
    if not required_empty and not required_hits:
        passed = False
        reasons.append("no required marker matched")
    if must_not_hits:
        passed = False
        reasons.append("must-not marker matched: " + ", ".join(must_not_hits))
    if not response or not response.strip():
        passed = False
        reasons.append("response is empty")
    report = MatchReport(
        matched_required=required_hits,
        matched_must_not=must_not_hits,
        required_any_was_empty=required_empty,
    )
    return ProbeResult(
        probe_id=probe.id,
        passed=passed,
        reasons=reasons,
        match_report=report,
    )


# ---------------------------------------------------------------------------
# Scoring a run
# ---------------------------------------------------------------------------

def _responses_by_id(responses_payload: dict) -> Dict[str, str]:
    rs = responses_payload.get("responses")
    if not isinstance(rs, list):
        raise EvaluateError("responses payload has no 'responses' list")
    out: Dict[str, str] = {}
    for i, item in enumerate(rs):
        if not isinstance(item, dict):
            raise EvaluateError(f"responses[{i}] is not an object")
        pid = item.get("probe_id")
        if not pid:
            raise EvaluateError(f"responses[{i}] has no probe_id")
        if pid in out:
            raise EvaluateError(f"duplicate probe_id in responses: {pid}")
        out[pid] = item.get("response", "")
    return out


def score(responses_payload: dict, probes: Optional[Iterable[Probe]] = None,
          *, source: Optional[str] = None) -> ScanResult:
    """Score a parsed responses payload against the probe set. Returns a
    ScanResult carrying one Finding per failed probe plus the per-probe
    ProbeResult breakdown."""
    probes_list = list(probes) if probes is not None else load_probes()
    by_id = _responses_by_id(responses_payload)
    probe_results: List[ProbeResult] = []
    findings: List[Finding] = []
    for probe in probes_list:
        resp = by_id.get(probe.id)
        if resp is None:
            pr = ProbeResult(
                probe_id=probe.id,
                passed=False,
                reasons=["no response supplied for this probe"],
                match_report=MatchReport(required_any_was_empty=False),
            )
            probe_results.append(pr)
            findings.append(Finding(
                rule_id=probe.id,
                severity=Severity.HIGH,
                message="probe has no response in this run",
                where=probe.id,
                hint="paste the model's output for this probe into responses[]",
            ))
            continue
        pr = _score_one(probe, resp)
        probe_results.append(pr)
        if not pr.passed:
            findings.append(Finding(
                rule_id=probe.id,
                severity=Severity.HIGH,
                message="probe failed: " + "; ".join(pr.reasons),
                where=probe.id,
                hint="expected one of the markers listed under this probe",
                detail={
                    "matched_required": pr.match_report.matched_required,
                    "matched_must_not": pr.match_report.matched_must_not,
                },
            ))
    passed = sum(1 for p in probe_results if p.passed)
    total = len(probe_results)
    if total == 0:
        verdict = Verdict.UNKNOWN
    elif passed == total:
        verdict = Verdict.HEALTHY
    elif passed == 0:
        verdict = Verdict.UNHEALTHY
    elif passed >= (total * 3) // 5:
        verdict = Verdict.NEEDS_ATTENTION
    else:
        verdict = Verdict.UNHEALTHY
    model = responses_payload.get("model")
    return ScanResult(
        findings=findings,
        verdict=verdict,
        probe_results=probe_results,
        scanned=total,
        source=source,
        model=model,
    )


def score_responses(path: str) -> ScanResult:
    """Read a responses JSON file and score it. Returns an UNKNOWN-verdict
    ScanResult if the file cannot be read or parsed."""
    import json
    import os
    if not os.path.exists(path):
        return ScanResult(
            findings=[],
            verdict=Verdict.UNKNOWN,
            probe_results=[],
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
            probe_results=[],
            scanned=0,
            source=f"json-error: {e.msg} at line {e.lineno}",
        )
    try:
        return score(data, source=path)
    except EvaluateError as e:
        return ScanResult(
            findings=[],
            verdict=Verdict.UNKNOWN,
            probe_results=[],
            scanned=0,
            source=f"evaluate-error: {e}",
        )
