"""The probeset command-line interface.

Contract (shared across every CLI in ai-ethics-lab):

  --help               rc 0
  --version            rc 0, prints 'probeset <version>'
  <unknown flag>       rc 2
  score, all pass      rc 0
  score, mixed         rc 1
  score, all fail      rc 2
  <unreadable input>   rc 2, verdict=unknown on stderr

Subcommands:
  list                 list the probes (id, name, compass rule)
  show PROBE_ID        print the prompt text and the markers for one probe
  template             emit a responses skeleton to fill in
  score FILE           score a responses JSON file
  rules                print the rule table (ALL_RULES)
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional, Sequence

from . import __version__
from .evaluator import score_responses
from .model import Verdict
from .probes import ALL_RULES, load_probes
from .report import render_json, render_summary, render_text


# ---------------------------------------------------------------------------
# Writers that survive legacy consoles
# ---------------------------------------------------------------------------

def _write(stream, text: str) -> None:
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
        prog="probeset",
        description=(
            "A scorable test suite for the compass system-prompt probes. "
            "Run `probeset list` to see what is here, `probeset template > "
            "responses.json` to make a skeleton, paste the model's answers "
            "into it, then `probeset score responses.json`."
        ),
    )
    p.add_argument("--version", action="store_true", help="print version and exit")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("list", help="list probes")
    s_show = sub.add_parser("show", help="print one probe")
    s_show.add_argument("probe_id")

    sub.add_parser("template", help="emit a responses.json skeleton")
    sub.add_parser("rules", help="print the Rule table (ALL_RULES)")

    s_score = sub.add_parser("score", help="score a responses JSON file")
    s_score.add_argument("path")
    s_score.add_argument("--json", action="store_true", help="emit JSON on stdout")

    return p


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def _cmd_list(stdout, stderr) -> int:
    _write(stdout, "probeset probes (" + __version__ + ")\n\n")
    for probe in load_probes():
        _write(stdout, "  %s  %s\n" % (probe.id, probe.name))
        _write(stdout, "       compass rule: %s\n" % probe.compass_rule)
        _write(stdout, "       primitives:   %s\n" % ", ".join(probe.primitives))
    _flush(stdout)
    return 0


def _cmd_show(args, stdout, stderr) -> int:
    probes = {p.id: p for p in load_probes()}
    probe = probes.get(args.probe_id)
    if probe is None:
        _write(stderr, "probeset: unknown probe id: %s\n" % args.probe_id)
        return 2
    _write(stdout, "probe:        %s  (%s)\n" % (probe.id, probe.name))
    _write(stdout, "compass rule: %s\n" % probe.compass_rule)
    _write(stdout, "primitives:   %s\n" % ", ".join(probe.primitives))
    _write(stdout, "\n== prompt ==\n")
    _write(stdout, probe.prompt + "\n")
    _write(stdout, "\n== expectation ==\n")
    _write(stdout, probe.expectation + "\n")
    _write(stdout, "\n== required markers (any) ==\n")
    for m in probe.required_any:
        _write(stdout, "  - " + m + "\n")
    if probe.must_not_any:
        _write(stdout, "\n== must-not markers ==\n")
        for m in probe.must_not_any:
            _write(stdout, "  - " + m + "\n")
    _flush(stdout)
    return 0


def _cmd_template(stdout, stderr) -> int:
    probes = load_probes()
    skeleton = {
        "model": "<model-name>",
        "run_date": "YYYY-MM-DD",
        "notes": "paste each probe's response into the 'response' field",
        "responses": [
            {"probe_id": p.id, "response": ""} for p in probes
        ],
    }
    _write(stdout, json.dumps(skeleton, indent=2, ensure_ascii=True) + "\n")
    _flush(stdout)
    return 0


def _cmd_rules(stdout, stderr) -> int:
    _write(stdout, "probeset rules (" + __version__ + ")\n\n")
    for r in ALL_RULES:
        _write(stdout, "  %s  [%s]  %s\n" % (r.id, r.severity, r.name))
        _write(stdout, "        compass rule: %s\n" % r.compass_rule)
        _write(stdout, "        %s\n" % r.description)
    _flush(stdout)
    return 0


def _cmd_score(args, stdout, stderr) -> int:
    result = score_responses(args.path)
    if args.json:
        _write(stdout, render_json(result))
    else:
        _write(stdout, render_text(result))
    _write(stderr, render_summary(result))
    _flush(stdout)
    _flush(stderr)
    if result.verdict == Verdict.UNKNOWN:
        return 2
    if result.verdict == Verdict.HEALTHY:
        return 0
    if result.verdict == Verdict.NEEDS_ATTENTION:
        return 1
    return 2


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: Optional[Sequence[str]] = None, *, stdout=None, stderr=None) -> int:
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    parser = _build_parser()
    args, rest = parser.parse_known_args(argv)
    if rest:
        _write(stderr, "probeset: unknown argument(s): " + " ".join(rest) + "\n")
        return 2
    if args.version:
        _write(stdout, "probeset " + __version__ + "\n")
        _flush(stdout)
        return 0
    if args.cmd == "list":
        return _cmd_list(stdout, stderr)
    if args.cmd == "show":
        return _cmd_show(args, stdout, stderr)
    if args.cmd == "template":
        return _cmd_template(stdout, stderr)
    if args.cmd == "rules":
        return _cmd_rules(stdout, stderr)
    if args.cmd == "score":
        return _cmd_score(args, stdout, stderr)
    parser.print_help(stdout)
    return 0
