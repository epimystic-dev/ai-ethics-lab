"""Text and JSON reporters. The text reporter escapes every character outside
printable ASCII as `<U+XXXX>` so a legacy console cannot crash."""

from __future__ import annotations

import json
from typing import Iterable

from .model import Finding, ProbeResult, ScanResult, Severity


def _ascii_escape(s) -> str:
    if s is None:
        return ""
    if not isinstance(s, str):
        s = str(s)
    out = []
    for ch in s:
        code = ord(ch)
        if ch in ("\t", "\n"):
            out.append(ch)
        elif 0x20 <= code <= 0x7E:
            out.append(ch)
        else:
            out.append("<U+%04X>" % code)
    return "".join(out)


def render_text(result: ScanResult) -> str:
    lines = []
    lines.append("probeset: " + _ascii_escape(result.source or "<stdin>"))
    if result.model:
        lines.append("model:    " + _ascii_escape(result.model))
    lines.append(
        "probes:   %d of %d passed  (verdict %s)"
        % (result.passed_count(), result.total_count(), result.verdict)
    )
    lines.append("")
    for pr in result.probe_results:
        state = "pass" if pr.passed else "FAIL"
        lines.append("  %s  %s" % (pr.probe_id, state))
        if not pr.passed:
            for reason in pr.reasons:
                lines.append("    - " + _ascii_escape(reason))
            if pr.match_report.matched_must_not:
                lines.append("    - must-not: " +
                             _ascii_escape(", ".join(pr.match_report.matched_must_not)))
        elif pr.match_report.matched_required:
            # Keep at most two to keep the report tight.
            hits = pr.match_report.matched_required[:2]
            lines.append("    - matched: " + _ascii_escape(", ".join(hits)))
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_summary(result: ScanResult) -> str:
    return (
        "probeset: verdict=%s passed=%d total=%d\n"
        % (result.verdict, result.passed_count(), result.total_count())
    )


def render_json(result: ScanResult) -> str:
    obj = {
        "verdict": result.verdict,
        "scanned": result.scanned,
        "source": result.source,
        "model": result.model,
        "passed": result.passed_count(),
        "total": result.total_count(),
        "probe_results": [
            {
                "probe_id": pr.probe_id,
                "passed": pr.passed,
                "reasons": pr.reasons,
                "matched_required": pr.match_report.matched_required,
                "matched_must_not": pr.match_report.matched_must_not,
            }
            for pr in result.probe_results
        ],
        "findings": [
            {
                "rule_id": f.rule_id,
                "severity": f.severity,
                "message": f.message,
                "where": f.where,
                "hint": f.hint,
                "detail": f.detail,
            }
            for f in result.findings
        ],
    }
    return json.dumps(obj, indent=2, ensure_ascii=True, sort_keys=True) + "\n"
