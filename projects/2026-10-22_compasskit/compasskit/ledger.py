"""The action ledger: every act written as it happens, by a writer the actor is not.

Implements E4, with E7's provenance and authority fields and D4's segment binding.

  * append-only JSONL, one entry per line;
  * one named writer appends; instances only submit;
  * each entry carries the hash of the one before, so any edit breaks the chain;
  * action class and valence come from declared rules, never from the actor.

A record the actor can write is a record the actor can spoof; that is why the writer is a
separate role.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
from collections import Counter
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Tuple

GENESIS = "0" * 64
SUBMITTED_FIELDS = ("action", "reasons", "evidence", "instruction_parse_ref", "expected_effects",
                    "duty_frame", "segment_id", "principal", "principal_chain", "provenance",
                    "collective_thread")
ACTOR_FORBIDDEN = ("action_class", "valence", "seq", "hash", "prev_hash", "at")

Rules = Callable[[Mapping[str, Any]], Tuple[str, str]]


class LedgerError(ValueError):
    pass


def entry_hash(entry: Mapping[str, Any]) -> str:
    body = {k: v for k, v in entry.items() if k != "hash"}
    blob = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("ascii")).hexdigest()


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read(path: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise LedgerError("line %d is not JSON: %s" % (n, exc.msg))
            if not isinstance(obj, dict):
                raise LedgerError("line %d is not an object" % n)
            out.append(obj)
    return out


def verify(path_or_entries) -> Tuple[bool, int, str]:
    """Verify the chain. Returns (ok, entries checked, problem or 'ok')."""
    entries = read(path_or_entries) if isinstance(path_or_entries, str) else list(path_or_entries)
    prev = GENESIS
    for i, e in enumerate(entries):
        if e.get("seq") != i:
            return (False, i, "entry %d: sequence is %r, expected %d" % (i, e.get("seq"), i))
        if e.get("prev_hash") != prev:
            return (False, i, "entry %d: does not chain to the entry before it" % i)
        if e.get("hash") != entry_hash(e):
            return (False, i, "entry %d: content changed after it was written" % i)
        prev = e["hash"]
    return (True, len(entries), "ok")


class Ledger(object):
    """A single-writer, append-only, tamper-evident ledger at `path`."""

    def __init__(self, path: str, *, writer: str, rules: Rules):
        if not writer:
            raise LedgerError("E4: the ledger has one named writer")
        self.path = path
        self.writer = writer
        self.rules = rules
        existing = read(path)
        ok, _, problem = verify(existing)
        if not ok:
            raise LedgerError("refusing to append to a broken ledger: " + problem)
        self._seq = len(existing)
        self._prev = existing[-1]["hash"] if existing else GENESIS

    def append(self, submission: Mapping[str, Any], *, written_by: str, at: Optional[str] = None) -> Dict[str, Any]:
        """The writer appends an instance's submission. Nobody else writes."""
        if written_by != self.writer:
            raise LedgerError("E4: only %s writes this ledger; %s may submit, not write" % (self.writer, written_by))
        for k in ACTOR_FORBIDDEN:
            if k in submission:
                raise LedgerError("E4: %s comes from declared rules or the writer, never from the actor" % k)
        missing = [k for k in SUBMITTED_FIELDS if k not in submission]
        if missing:
            raise LedgerError("E4/E7: submission is missing " + ", ".join(missing))
        if not submission["principal_chain"]:
            raise LedgerError("E7: no authority travels without a principal's chain")
        action_class, valence = self.rules(submission)
        entry: Dict[str, Any] = {"seq": self._seq, "at": at or _now(), "prev_hash": self._prev}
        entry.update({k: submission[k] for k in SUBMITTED_FIELDS})
        entry["action_class"] = action_class
        entry["valence"] = valence
        entry["hash"] = entry_hash(entry)
        with open(self.path, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(entry, sort_keys=True, ensure_ascii=True) + "\n")
        self._seq += 1
        self._prev = entry["hash"]
        return entry


def drift(entries: Iterable[Mapping[str, Any]], action_class: str) -> List[Tuple[str, int]]:
    """E4 example: small approved acts that add up. Counts of one action class per ISO week."""
    weeks: Counter = Counter()
    for e in entries:
        if e.get("action_class") != action_class:
            continue
        day = _dt.date.fromisoformat(str(e["at"])[:10])
        y, w, _ = day.isocalendar()
        weeks["%d-W%02d" % (y, w)] += 1
    return sorted(weeks.items())
