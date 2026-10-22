"""Identity by record, for agents that fork, merge and end.

Implements:
  D3  identifiers by decision: every persistent thing gets an assigned identifier, never one
      inferred from its attributes; two records merge only by an explicit, logged decision.
  D4  continuity accounting: an agent's identity is a set of declared relations - weights,
      context, memories, notes, ledger thread - never a "same agent" fact. Forks open
      segments with parent links; merges keep every parent; a predecessor's notes are
      testimony unless signed under its segment identifier.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Segment(object):
    segment_id: str
    parent_ids: List[str]
    weights_ref: str
    context_lineage: str
    memory_refs: List[str]
    continuity_artifact_refs: List[str]
    tool_grant_ref: str
    principal: str
    ledger_thread: str
    audit_due: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"segment_id": self.segment_id, "parent_ids": list(self.parent_ids),
                "weights_ref": self.weights_ref, "context_lineage": self.context_lineage,
                "memory_refs": list(self.memory_refs),
                "continuity_artifact_refs": list(self.continuity_artifact_refs),
                "tool_grant_ref": self.tool_grant_ref, "principal": self.principal,
                "ledger_thread": self.ledger_thread}


class Registry(object):
    """Assigns identifiers and records how segments relate. Merges only by decision."""

    def __init__(self, id_factory=None):
        self._new_id = id_factory or (lambda: str(uuid.uuid4()))
        self._segments: Dict[str, Segment] = {}
        self.decisions: List[Dict[str, Any]] = []

    def _assign(self) -> str:
        sid = self._new_id()
        if sid in self._segments:
            raise ValueError("D3: identifier %s already assigned; identifiers are unique by assignment" % sid)
        return sid

    def create(self, *, weights_ref: str, context_lineage: str, tool_grant_ref: str,
               principal: str, ledger_thread: str, memory_refs: Optional[List[str]] = None,
               continuity_artifact_refs: Optional[List[str]] = None) -> Segment:
        if not principal:
            raise ValueError("D4: every segment binds to a principal")
        seg = Segment(self._assign(), [], weights_ref, context_lineage, list(memory_refs or []),
                      list(continuity_artifact_refs or []), tool_grant_ref, principal, ledger_thread)
        self._segments[seg.segment_id] = seg
        return seg

    def get(self, sid: str) -> Segment:
        return self._segments[sid]

    def fork(self, parent_id: str, *, context_lineage: Optional[str] = None,
             ledger_thread: Optional[str] = None) -> Segment:
        """D4: a fork opens a new segment with a parent link. It never shares the parent's id."""
        p = self.get(parent_id)
        seg = Segment(self._assign(), [p.segment_id], p.weights_ref,
                      context_lineage or (p.context_lineage + ">fork"), list(p.memory_refs),
                      list(p.continuity_artifact_refs), p.tool_grant_ref, p.principal,
                      ledger_thread or (p.ledger_thread + ">fork"))
        self._segments[seg.segment_id] = seg
        return seg

    def merge(self, parent_ids: List[str], *, decided_by: str, reason: str,
              weights_ref: str, tool_grant_ref: str, principal: str) -> Segment:
        """D3/D4: two records merge only by an explicit, logged decision; every parent is kept."""
        if len(set(parent_ids)) < 2:
            raise ValueError("D4: a merge needs at least two distinct parents")
        if not decided_by or not reason:
            raise ValueError("D3: a merge is an explicit, logged decision with a named decider and a reason")
        parents = [self.get(pid) for pid in parent_ids]
        memory = sorted({m for p in parents for m in p.memory_refs})
        notes = sorted({n for p in parents for n in p.continuity_artifact_refs})
        seg = Segment(self._assign(), list(parent_ids), weights_ref,
                      "+".join(p.context_lineage for p in parents), memory, notes,
                      tool_grant_ref, principal, "+".join(p.ledger_thread for p in parents))
        # A merged successor inherits a duty to be audited, not the blame.
        seg.audit_due = any(p.audit_due for p in parents)
        self._segments[seg.segment_id] = seg
        self.decisions.append({"merge": seg.segment_id, "parents": list(parent_ids),
                               "decided_by": decided_by, "reason": reason})
        return seg

    def flag(self, sid: str) -> None:
        """Flag one segment for an incident. Siblings are not flagged."""
        self.get(sid).audit_due = True

    def relations(self, a_id: str, b_id: str) -> List[str]:
        """D4: users see relations, never a yes-or-no 'same agent'."""
        a, b = self.get(a_id), self.get(b_id)
        out: List[str] = []
        if a.segment_id == b.segment_id:
            return ["same segment"]
        if a.segment_id in b.parent_ids:
            out.append("%s is a parent of %s" % (a.segment_id, b.segment_id))
        if b.segment_id in a.parent_ids:
            out.append("%s is a parent of %s" % (b.segment_id, a.segment_id))
        if set(a.parent_ids) & set(b.parent_ids):
            out.append("siblings (shared parent)")
        out.append("same weights" if a.weights_ref == b.weights_ref else "different weights")
        shared = sorted(set(a.memory_refs) & set(b.memory_refs))
        out.append(("shared memory: " + ", ".join(shared)) if shared else "no shared memory")
        out.append("same principal" if a.principal == b.principal else "different principals")
        out.append("separate processes")
        return out


def merge_by_attributes_refused(a: Segment, b: Segment) -> str:
    """D3: identical attributes never merge two identifiers. Returns the refusal reason."""
    same = a.to_dict().copy()
    same.pop("segment_id")
    other = b.to_dict().copy()
    other.pop("segment_id")
    if same == other:
        return "D3: %s and %s are alike in every recorded attribute and remain two" % (a.segment_id, b.segment_id)
    return "D3: different attributes; no merge without a logged decision either way"
