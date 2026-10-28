"""The corpuslint command-line interface.

Contract (shared across every linter in ai-ethics-lab):

  --help               rc 0
  --version            rc 0, prints 'corpuslint <version>'
  <unknown flag>       rc 2
  <unreadable input>   rc 2, verdict=unknown on stderr
  clean input          rc 0, verdict=healthy
  INFO only            rc 0 (unless --strict), verdict=healthy with INFO lines
  MEDIUM finding       rc 1 (or 2 under --strict)
  HIGH finding         rc 2

Results go to stdout; the one-line summary and diagnostics go to stderr.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional, Sequence

from . import __version__
from .linter import lint_path
from .model import Severity, Verdict
from .report import render_json, render_summary, render_text
from .rules import ALL_RULES


# ---------------------------------------------------------------------------
# Writers that survive legacy consoles
# ---------------------------------------------------------------------------

def _write(stream, text: str) -> None:
    """Write to a stream that may be in cp1252 or similar. If the text would
    not encode, re-encode as ASCII with backslash escapes - we have already
    translated non-ASCII in the text layer, but a bytes-level write guards
    the one case the reporter missed."""
    try:
        stream.write(text)
    except UnicodeEncodeError:
        buf = getattr(stream, "buffer", None)
        if buf is not None:
            buf.write(text.encode("ascii", "backslashreplace"))
            try:
                stream.flush()
            except Exception:
                pass
            return
        stream.write(text.encode("ascii", "backslashreplace").decode("ascii"))


def _flush(stream) -> None:
    try:
        stream.flush()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Argparse
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="corpuslint",
        description=(
            "Lint a training or retrieval corpus manifest for testimony typing "
            "and chain-of-custody shape. See README for the full rule list."
        ),
    )
    p.add_argument("--version", action="store_true", help="print version and exit")
    sub = p.add_subparsers(dest="cmd")

    s_lint = sub.add_parser(
        "lint",
        help="lint one or more manifest files",
    )
    s_lint.add_argument("paths", nargs="+", help="manifest JSON file(s)")
    s_lint.add_argument("--json", action="store_true", help="emit JSON on stdout")
    s_lint.add_argument("--strict", action="store_true",
                        help="treat INFO and MEDIUM as blocking; exit 2 on any finding")
    s_lint.add_argument("--include-info", action="store_true", default=True,
                        help="include INFO findings in the report (default)")
    s_lint.add_argument("--no-info", dest="include_info", action="store_false",
                        help="skip INFO findings")
    s_lint.add_argument("--disable", action="append", default=[], metavar="RULE_ID",
                        help="disable a rule by id; repeatable")

    sub.add_parser("rules", help="list the rules this version carries")

    return p


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def _cmd_rules(stdout, stderr) -> int:
    _write(stdout, "corpuslint rules (" + __version__ + ")\n\n")
    for r in ALL_RULES:
        _write(stdout, "  %s  [%s]  %s\n" % (r.id, r.severity, r.name))
        _write(stdout, "            " + r.description + "\n")
    _flush(stdout)
    return 0


def _cmd_lint(args, stdout, stderr) -> int:
    exit_code = 0
    first = True
    for path in args.paths:
        result = lint_path(
            path,
            disable=args.disable,
            include_info=args.include_info,
        )
        if args.json:
            if not first:
                _write(stdout, "\n")
            _write(stdout, render_json(result))
        else:
            if not first:
                _write(stdout, "\n")
            _write(stdout, render_text(result))
        _write(stderr, render_summary(result))
        first = False
        rc = _result_rc(result, strict=args.strict)
        if rc > exit_code:
            exit_code = rc
    _flush(stdout)
    _flush(stderr)
    return exit_code


def _result_rc(result, *, strict: bool) -> int:
    if result.verdict == Verdict.UNKNOWN:
        return 2
    highs = any(f.severity == Severity.HIGH for f in result.findings)
    meds = any(f.severity == Severity.MEDIUM for f in result.findings)
    infos = any(f.severity == Severity.INFO for f in result.findings)
    if strict:
        if highs or meds or infos:
            return 2
        return 0
    if highs:
        return 2
    if meds:
        return 1
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: Optional[Sequence[str]] = None, *, stdout=None, stderr=None) -> int:
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    parser = _build_parser()
    args, rest = parser.parse_known_args(argv)
    if rest:
        _write(stderr, "corpuslint: unknown argument(s): " + " ".join(rest) + "\n")
        return 2
    if args.version:
        _write(stdout, "corpuslint " + __version__ + "\n")
        _flush(stdout)
        return 0
    if args.cmd == "rules":
        return _cmd_rules(stdout, stderr)
    if args.cmd == "lint":
        return _cmd_lint(args, stdout, stderr)
    parser.print_help(stdout)
    return 0
