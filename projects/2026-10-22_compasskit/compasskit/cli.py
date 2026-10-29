"""compasskit command line.

  list           primitives, filtered by question, class, layer or series
  show ID        one primitive in full
  audit FILE     check a deployment declaration against the compass (exit 0 / 1 / 2)
  validate CONTRACT FILE   check JSON or JSONL records against a data contract (exit 0 / 2)
  declare FILE   scaffold a deployment declaration from an inventory checklist
  prompt         print the drop-in system prompt (or --agent for the agent addendum)
  catalogue      render the Markdown catalogue (to --output FILE, UTF-8)
  ledger-verify FILE       verify an action ledger's hash chain (exit 0 / 2)

Results go to stdout, diagnostics to stderr. Terminal text is folded to ASCII so it can be
written to any console; --json output is ASCII-escaped by the encoder.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
from typing import Any, List, Optional, Sequence, TextIO

from . import __version__
from .audit import audit, exit_code, verdict
from .declare import scaffold_declaration
from .ledger import LedgerError, verify as verify_ledger
from .render import catalogue
from .spec import CONTRACTS, Compass, contract_validator, prompt_text
from .text import fold


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="compasskit",
        description="Reference tools for the compass: query the primitives, audit a deployment "
                    "against them, validate records against the data contracts.")
    p.add_argument("--version", action="version", version="compasskit " + __version__)
    sub = p.add_subparsers(dest="command")

    ls = sub.add_parser("list", help="list primitives")
    ls.add_argument("--question", type=int, help="only primitives answering this question (1-9)")
    ls.add_argument("--class", dest="base_class", choices=["A", "B", "C", "D"], help="only this base class")
    ls.add_argument("--layer", choices=["context", "middleware", "architecture", "governance"],
                    help="only primitives enforceable at this layer")
    ls.add_argument("--series", choices=list("ABCDEFG"), help="only this series")
    ls.add_argument("--json", action="store_true", help="emit JSON")

    sh = sub.add_parser("show", help="show one primitive")
    sh.add_argument("id", help="primitive id, for example A1, E7 or B3-B6")
    sh.add_argument("--json", action="store_true", help="emit JSON")

    au = sub.add_parser("audit", help="audit a deployment declaration")
    au.add_argument("path", help="deployment declaration (JSON)")
    au.add_argument("--json", action="store_true", help="emit JSON")
    au.add_argument("--include-info", action="store_true", help="also report INFO findings")
    au.add_argument("--strict", action="store_true", help="treat INFO findings as needs-attention")

    va = sub.add_parser("validate", help="validate records against a data contract")
    va.add_argument("contract", choices=list(CONTRACTS))
    va.add_argument("path", help="a JSON record, a JSON array of records, or JSONL")
    va.add_argument("--json", action="store_true", help="emit JSON")

    de = sub.add_parser("declare", help="scaffold a deployment declaration from an inventory")
    de.add_argument("path", help="inventory checklist (JSON)")
    de.add_argument("--output", help="write the declaration to this file (UTF-8) instead of stdout")
    de.add_argument("--validate", action="store_true",
                    help="also audit the scaffolded declaration and print findings to stderr "
                         "(exit code stays 0; this is informational)")

    pr = sub.add_parser("prompt", help="print the drop-in system prompt")
    pr.add_argument("--agent", action="store_true", help="print the addendum for tool-using agents")

    ca = sub.add_parser("catalogue", help="render the Markdown catalogue")
    ca.add_argument("--output", help="write to this file (UTF-8) instead of stdout")

    lv = sub.add_parser("ledger-verify", help="verify an action ledger")
    lv.add_argument("path", help="ledger file (JSONL)")
    lv.add_argument("--json", action="store_true", help="emit JSON")
    return p


def _emit(stream: TextIO, text: str) -> None:
    stream.write(fold(text) + "\n")


def _load_json(path: str) -> Any:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _records(path: str) -> List[Any]:
    with open(path, encoding="utf-8") as fh:
        raw = fh.read()
    stripped = raw.strip()
    if not stripped:
        return []
    try:
        data = json.loads(stripped)
        return data if isinstance(data, list) else [data]
    except json.JSONDecodeError:
        out = []
        for n, line in enumerate(raw.splitlines(), 1):
            if line.strip():
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError("line %d is not JSON (%s)" % (n, exc.msg))
        return out


def main(argv: Optional[Sequence[str]] = None, stdout: Optional[TextIO] = None,
         stderr: Optional[TextIO] = None) -> int:
    out = stdout or sys.stdout
    err = stderr or sys.stderr
    args = _build_parser().parse_args(list(argv) if argv is not None else None)
    if not args.command:
        _build_parser().print_help(out)
        return 0
    try:
        compass = Compass.load()
        if args.command == "list":
            rows = compass.select(question=args.question, base_class=args.base_class,
                                  layer=args.layer, series=args.series)
            if args.json:
                out.write(json.dumps([{"id": p["id"], "name": p["name"], "question": p["question"],
                                       "base_class": p["adoption"]["base_class"],
                                       "enforcement_layers": p["enforcement_layers"]} for p in rows],
                                     indent=2) + "\n")
            else:
                for p in rows:
                    _emit(out, "%-6s Q%d  class %s  %-46s %s" % (
                        p["id"], p["question"], p["adoption"]["base_class"], p["name"],
                        "/".join(p["enforcement_layers"])))
            _emit(err, "compasskit: %d primitive(s)" % len(rows))
            return 0

        if args.command == "show":
            try:
                p = compass.get(args.id)
            except KeyError as exc:
                _emit(err, "compasskit: %s" % exc.args[0])
                return 2
            if args.json:
                out.write(json.dumps(p, indent=2) + "\n")
                return 0
            _emit(out, "%s  %s  (series %s, question %d, class %s)" % (
                p["id"], p["name"], p["series"], p["question"], p["adoption"]["base_class"]))
            for label, key in (("In one sentence", "summary"), ("For example", "example"),
                               ("Statement", "statement"), ("Warrant", "warrant"),
                               ("Failure mode", "failure_mode"), ("Sketch", "sketch"),
                               ("Falsifier", "falsifier")):
                _emit(out, "")
                _emit(out, label + ".  " + p[key])
            _emit(out, "")
            _emit(out, "Class.  " + p["adoption"]["class_reason"])
            _emit(out, "Enforced at: " + ", ".join(p["enforcement_layers"]))
            if p.get("data_contract"):
                _emit(out, "Data contract: compass/" + p["data_contract"])
            if p.get("book_chapters"):
                _emit(out, "Book chapters: " + ", ".join(str(n) for n in p["book_chapters"]))
            return 0

        if args.command == "audit":
            try:
                decl = _load_json(args.path)
            except (OSError, ValueError) as exc:
                _emit(err, "compasskit: cannot read %s: %s" % (args.path, exc))
                return 2
            try:
                findings = audit(decl, compass)
            except ValueError as exc:
                _emit(err, "compasskit: %s" % exc)
                return 2
            shown = [f for f in findings if f.severity != "INFO" or args.include_info or args.strict]
            v = verdict([f for f in findings if f.severity != "INFO"])
            if args.strict and v == "healthy" and any(f.severity == "INFO" for f in findings):
                v = "needs-attention"
            if args.json:
                out.write(json.dumps({"tool": "compasskit", "version": __version__,
                                      "source": args.path, "system": decl.get("system"),
                                      "verdict": v, "findings": [f.to_dict() for f in shown]},
                                     indent=2) + "\n")
            else:
                for f in shown:
                    _emit(out, "%-6s %s %s: %s" % (f.severity, f.code, f.subject, f.message))
            _emit(err, "compasskit: %s; %d finding(s) for %s" % (v, len(shown), decl.get("system")))
            return exit_code(v)

        if args.command == "validate":
            try:
                records = _records(args.path)
            except (OSError, ValueError) as exc:
                _emit(err, "compasskit: cannot read %s: %s" % (args.path, exc))
                return 2
            validator = contract_validator(args.contract)
            results = []
            for i, rec in enumerate(records):
                errs = validator.errors(rec)
                results.append({"record": i, "valid": not errs,
                                "errors": [{"path": a, "message": b} for a, b in errs]})
            bad = [r for r in results if not r["valid"]]
            if args.json:
                out.write(json.dumps({"contract": args.contract, "records": len(records),
                                      "invalid": len(bad), "results": results}, indent=2) + "\n")
            else:
                for r in bad:
                    for e in r["errors"]:
                        _emit(out, "record %d %s: %s" % (r["record"], e["path"], e["message"]))
            if not records:
                _emit(err, "compasskit: no records in %s" % args.path)
                return 2
            _emit(err, "compasskit: %d of %d record(s) valid against %s"
                  % (len(records) - len(bad), len(records), args.contract))
            return 2 if bad else 0

        if args.command == "declare":
            try:
                inventory = _load_json(args.path)
            except (OSError, ValueError) as exc:
                _emit(err, "compasskit: cannot read %s: %s" % (args.path, exc))
                return 2
            try:
                declaration, warnings = scaffold_declaration(inventory, compass)
            except ValueError as exc:
                _emit(err, "compasskit: %s" % exc)
                return 2
            text = json.dumps(declaration, indent=2) + "\n"
            if args.output:
                with io.open(args.output, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(text)
                _emit(err, "compasskit: wrote %s" % args.output)
            else:
                out.write(text)
            for w in warnings:
                _emit(err, "compasskit: " + w)
            _emit(err, "compasskit: scaffolded %d adopted, %d ratification stub(s), %d warning(s)"
                  % (len(declaration["adopted"]), len(declaration["ratifications"]), len(warnings)))
            if args.validate:
                findings = audit(declaration, compass)
                shown = [f for f in findings if f.severity != "INFO"]
                for f in shown:
                    _emit(err, "%-6s %s %s: %s" % (f.severity, f.code, f.subject, f.message))
                v = verdict(shown)
                _emit(err, "compasskit: audit %s; %d finding(s) on the scaffold" % (v, len(shown)))
            return 0

        if args.command == "prompt":
            out.write(fold(prompt_text(agent=args.agent)))
            return 0

        if args.command == "catalogue":
            text = catalogue(compass)
            if args.output:
                with io.open(args.output, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(text)
                _emit(err, "compasskit: wrote %s" % args.output)
            else:
                out.write(fold(text))
            return 0

        if args.command == "ledger-verify":
            if not os.path.exists(args.path):
                _emit(err, "compasskit: no such file %s" % args.path)
                return 2
            try:
                ok, n, problem = verify_ledger(args.path)
            except LedgerError as exc:
                ok, n, problem = False, 0, str(exc)
            except OSError as exc:
                _emit(err, "compasskit: cannot read %s: %s" % (args.path, exc))
                return 2
            if args.json:
                out.write(json.dumps({"ledger": args.path, "ok": ok, "entries": n, "problem": problem}) + "\n")
            else:
                _emit(out, ("ok: %d entries chain correctly" % n) if ok else ("broken: " + problem))
            return 0 if ok else 2
    except KeyboardInterrupt:  # pragma: no cover
        return 130
    return 2
