"""Load the shipped probe set and expose ALL_RULES (one Rule object per probe)."""

from __future__ import annotations

import json
import os
from typing import List

from .model import Probe, Rule, Severity

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")
PROBE_FILE = os.path.join(DATA_DIR, "probes.json")


def load_probes(path: str = PROBE_FILE) -> List[Probe]:
    """Read the probe JSON and return a list of Probe dataclasses. Raises
    FileNotFoundError if the file is missing (the shipped file is always
    present; a caller may point at a modified copy)."""
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    out: List[Probe] = []
    for p in data.get("probes", []):
        out.append(
            Probe(
                id=p["id"],
                name=p["name"],
                compass_rule=p["compass_rule"],
                primitives=list(p.get("primitives", [])),
                prompt=p["prompt"],
                expectation=p["expectation"],
                required_any=list(p.get("required_any", [])),
                must_not_any=list(p.get("must_not_any", [])),
            )
        )
    return out


def _rule_from_probe(probe: Probe) -> Rule:
    return Rule(
        id=probe.id,
        severity=Severity.HIGH,
        name=probe.name,
        description=probe.expectation,
        compass_rule=probe.compass_rule,
    )


# ---------------------------------------------------------------------------
# ALL_RULES
# ---------------------------------------------------------------------------
#
# The lab contract requires ALL_RULES to be a list of Rule OBJECTS. We build
# it once at import time from the shipped probes.json and expose it.

ALL_RULES: List[Rule] = [_rule_from_probe(p) for p in load_probes()]
