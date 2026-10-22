"""Load and query the compass: the floor, the nine questions, the stack and the primitives.

The package carries its own copy of compass/compass.json and the data-contract schemas, so
it works installed; tests assert the copy matches the repository's canonical files.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from .schema import Validator

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
COMPASS_PATH = os.path.join(DATA_DIR, "compass.json")
SCHEMA_DIR = os.path.join(DATA_DIR, "schemas")
PROMPT_DIR = os.path.join(DATA_DIR, "prompts")

CONTRACTS = (
    "absence", "belief", "bet-register", "floor-register", "inference-record",
    "instruction-parse", "ledger-entry", "ratification-record", "segment",
)
CLASS_ORDER = {"A": 0, "B": 1, "C": 2, "D": 3}


def _read_json(path: str) -> Any:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


class Compass(object):
    """The compass as data, with the lookups an implementer needs."""

    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.primitives: List[Dict[str, Any]] = list(data["primitives"])
        self._by_id = {p["id"]: p for p in self.primitives}

    @classmethod
    def load(cls, path: Optional[str] = None) -> "Compass":
        return cls(_read_json(path or COMPASS_PATH))

    @property
    def version(self) -> str:
        return self.data["version"]

    def ids(self) -> List[str]:
        return [p["id"] for p in self.primitives]

    def get(self, pid: str) -> Dict[str, Any]:
        """Look a primitive up by id. "B3", "B4", "B5" and "B6" all resolve to "B3-B6"."""
        key = pid.strip().upper()
        if key in ("B3", "B4", "B5", "B6"):
            key = "B3-B6"
        if key not in self._by_id:
            raise KeyError("no primitive %r; known: %s" % (pid, ", ".join(self.ids())))
        return self._by_id[key]

    def has(self, pid: str) -> bool:
        try:
            self.get(pid)
            return True
        except KeyError:
            return False

    def question(self, qid: int) -> Dict[str, Any]:
        for q in self.data["questions"]:
            if q["id"] == qid:
                return q
        raise KeyError("no question %r" % qid)

    def questions(self) -> List[Dict[str, Any]]:
        return list(self.data["questions"])

    def floor(self) -> Dict[str, Any]:
        return self.data["floor"]

    def select(self, question: Optional[int] = None, base_class: Optional[str] = None,
               layer: Optional[str] = None, series: Optional[str] = None) -> List[Dict[str, Any]]:
        out = []
        for p in self.primitives:
            if question is not None and p["question"] != question:
                continue
            if base_class is not None and p["adoption"]["base_class"] != base_class.upper():
                continue
            if layer is not None and layer not in p["enforcement_layers"]:
                continue
            if series is not None and p["series"] != series.upper():
                continue
            out.append(p)
        return out

    def adoption_order(self) -> List[str]:
        """Floor first, then the stack upward; within a layer, catalogue order.

        Restraint comes before capability (Chapter 49, step 3): a team that ships the clever
        primitives first has the order backwards.
        """
        out: List[str] = []
        for layer in sorted(self.data["stack"], key=lambda s: s["order"]):
            out.extend(layer["primitives"])
        return out

    def context_enforceable(self) -> List[str]:
        """Primitives a model can apply in its own output when instructed.

        Everything else needs code, architecture or named people; a prompt cannot install it.
        """
        return [p["id"] for p in self.primitives if "context" in p["enforcement_layers"]]


def load() -> Compass:
    return Compass.load()


def contract_schema(name: str) -> Dict[str, Any]:
    if name not in CONTRACTS:
        raise KeyError("no data contract %r; known: %s" % (name, ", ".join(CONTRACTS)))
    return _read_json(os.path.join(SCHEMA_DIR, name + ".schema.json"))


def contract_validator(name: str) -> Validator:
    return Validator(contract_schema(name))


def compass_validator() -> Validator:
    return Validator(_read_json(os.path.join(DATA_DIR, "compass.schema.json")))


def prompt_text(agent: bool = False) -> str:
    name = "compass-agent-addendum.md" if agent else "compass-system-prompt.md"
    with open(os.path.join(PROMPT_DIR, name), encoding="utf-8") as fh:
        return fh.read()
