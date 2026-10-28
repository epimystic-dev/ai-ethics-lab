"""Text and JSON reporters. The text reporter escapes every character outside
printable ASCII as `<U+XXXX>` so a console in cp1252 cannot crash, and so
hidden characters stay visible in the report meant to expose them.

The JSON reporter is already safe as long as ensure_ascii is left at its
default. We leave it there."""

from __future__ import annotations

import json
from typing import Iterable, Tuple

from .model import Finding, ScanResult, Severity


# ---------------------------------------------------------------------------
# ASCII escaping
# ---------------------------------------------------------------------------

def _ascii_escape(s) -> str:
    """Render every character outside printable ASCII as <U+XXXX>. Tabs and
    newlines are kept so a report stays readable; anything else above 0x7E or
    below 0x20 is escaped."""
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


# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------

def _severity_rank(sev: str) -> int:
    try:
        return Severity.ladder().index(sev)
    except ValueError:
        return len(Severity.ladder())


def _group_by_severity(findings: Iterable[Finding]) -> Tuple[list, list, list]:
    highs, meds, infos = [], [], []
    for f in findings:
        if f.severity == Severity.HIGH:
            highs.append(f)
        elif f.severity == Severity.MEDIUM:
            meds.append(f)
        else:
            infos.append(f)
    return highs, meds, infos


def render_text(result: ScanResult) -> str:
    """Compact, cp1252-safe text report. All non-ASCII rendered as <U+XXXX>."""
    lines = []
    lines.append("corpuslint: " + _ascii_escape(result.source or "<stdin>"))
    lines.append("scanned: %d document(s)" % result.scanned)
    lines.append("")
    highs, meds, infos = _group_by_severity(result.findings)
    for label, group in (("HIGH", highs), ("MEDIUM", meds), ("INFO", infos)):
        if not group:
            continue
        lines.append(label + ":")
        for f in group:
            where = f.where or "(manifest)"
            msg = _ascii_escape(f.message)
            lines.append("  %s  %s  %s" % (f.rule_id, _ascii_escape(where), msg))
            if f.hint:
                lines.append("     hint: " + _ascii_escape(f.hint))
        lines.append("")
    if not result.findings:
        lines.append("(no findings)")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_summary(result: ScanResult) -> str:
    """One-line summary written to stderr: verdict, counts, rule ids."""
    highs, meds, infos = _group_by_severity(result.findings)
    parts = [
        "verdict=" + result.verdict,
        "scanned=%d" % result.scanned,
        "high=%d" % len(highs),
        "medium=%d" % len(meds),
        "info=%d" % len(infos),
    ]
    return "corpuslint: " + " ".join(parts) + "\n"


# ---------------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------------

def render_json(result: ScanResult) -> str:
    """A JSON report. Fields are stable: verdict, scanned, source, findings."""
    obj = {
        "verdict": result.verdict,
        "scanned": result.scanned,
        "source": result.source,
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
