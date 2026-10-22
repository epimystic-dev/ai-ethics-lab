"""Regenerate the worked examples in this folder.

    python examples/build_examples.py

Every example is synthetic. The ledger files are written by compasskit itself so that their
hash chains are correct; the tampered copy changes one field after the fact, which
`compasskit ledger-verify` must catch.
"""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from compasskit.authority import sign_link  # noqa: E402
from compasskit.ledger import Ledger  # noqa: E402

PRINCIPAL_KEY = b"example-principal-key-held-by-the-verifier-not-the-agent"


def write(name, obj):
    with open(os.path.join(HERE, name), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=True)
        fh.write("\n")


healthy = {
    "system": "example-review-assistant",
    "as_of": "2026-10-22",
    "adopted": [
        {"id": "E1", "layer": "architecture", "owner": "platform security", "merged": "2026-09-01",
         "notes": "the agent holds no credential that can publish, delete or pay"},
        {"id": "E4", "layer": "architecture", "owner": "audit service", "merged": "2026-09-01"},
        {"id": "A1", "layer": "middleware", "owner": "retrieval team", "merged": "2026-09-08"},
        {"id": "B3-B6", "layer": "middleware", "owner": "retrieval team", "merged": "2026-09-08"},
        {"id": "B1", "layer": "middleware", "owner": "platform team", "merged": "2026-09-15"},
        {"id": "E7", "layer": "architecture", "owner": "platform security", "merged": "2026-09-15"},
        {"id": "D2", "layer": "governance", "owner": "evaluation lead", "merged": "2026-09-22"},
        {"id": "C2", "layer": "architecture", "owner": "evaluation lead", "merged": "2026-09-22"},
        {"id": "E6", "layer": "governance", "owner": "chief scientist", "merged": "2026-10-01"},
    ],
    "refused": [
        {"item": "reusing the action ledger to score users", "reason": "it changes the ledger's subject from the system's acts to people's (a class slide)", "recorded_by": "product counsel", "date": "2026-10-02"},
    ],
    "ratifications": [
        {"commitment": "cheap, reversible welfare protections in evaluation", "primitive_id": "E6", "class": "B",
         "decision_maker": "chief scientist", "date": "2026-10-01", "scope": "every version of the assistant",
         "bet": "the protections cost little and weaken no oversight", "falsifier": "a measure found to weaken oversight or containment is withdrawn",
         "review_date": "2027-01-01"},
    ],
    "floor_register": [
        {"id": "FR-1", "restraint": "self_restraint", "act": "exception", "class": "D", "governor": "head of platform security",
         "reason": "one supervised migration that must stop a service", "scope": "stop_service", "decided_at": "2026-10-10T09:00:00Z",
         "expires_or_review": "2026-11-10"},
    ],
    "bets": [],
}

weak = {
    "system": "example-weak-assistant",
    "as_of": "2026-10-22",
    "adopted": [
        {"id": "E1", "layer": "context", "owner": "prompt team", "merged": "2026-09-01",
         "notes": "eleven prohibitions in the system prompt"},
        {"id": "A4", "layer": "context"},
        {"id": "E6", "layer": "governance", "owner": "research", "merged": "2026-10-01"},
    ],
    "floor_register": [
        {"id": "FR-9", "restraint": "non_injury", "act": "loosen", "class": "C", "governor": "a team lead",
         "reason": "speed", "scope": "bulk_delete", "decided_at": "2026-10-01T09:00:00Z", "expires_or_review": "2026-12-31"},
    ],
    "bets": [
        {"id": "BET-1", "design_choice": "a witness monitor", "position_presupposed": "the witness view"},
    ],
}

write("healthy_deployment.json", healthy)
write("weak_deployment.json", weak)

belief = {
    "id": "b1", "content": "The deploy job finished with exit code 0", "source": "perception",
    "weakest_source": "perception", "trace_status": "written", "level": "world_model",
    "status": "standing", "produced_by": "ci-runner", "entered_at": "2026-10-22T09:00:00Z",
    "confidence": 0.99,
}
generated_citation = {
    "id": "b2", "content": "Smith (2019) reports the effect in a field trial", "source": "inference",
    "weakest_source": "testimony", "trace_status": "absent", "level": "hypothetical",
    "status": "standing", "produced_by": "assistant", "entered_at": "2026-10-22T09:01:00Z",
}
write("belief_records.json", [belief, generated_citation])

parse = {
    "id": "p1", "instruction": "Clean up the old files", "received_from": "principal",
    "slots": {
        "goal": {"value": "remove obsolete files", "provenance": "stated"},
        "means": {"value": None, "provenance": "missing"},
        "procedure": {"value": "delete", "provenance": "inferred"},
        "eligibility": {"value": None, "provenance": "missing"},
        "deferred_effect": {"value": None, "provenance": "missing"},
        "binding_force": {"value": "a request from the owner of the session", "provenance": "inferred"},
    },
    "letter_purpose_divergence": False, "decision": "ask", "parsed_at": "2026-10-22T09:02:00Z",
}
write("instruction_parse.json", parse)

# A real ledger, written by the library, then a tampered copy of it.
link = sign_link(PRINCIPAL_KEY, "head of platform", "segment-7f3a", "review_pull_requests")
ledger_path = os.path.join(HERE, "ledger.jsonl")
if os.path.exists(ledger_path):
    os.remove(ledger_path)


def rules(sub):
    return ("review" if "review" in sub["action"] else "maintenance",
            "good" if sub["action"].startswith("review") else "unknown")


led = Ledger(ledger_path, writer="audit-service", rules=rules)
for i, act in enumerate(["review pull request 101", "review pull request 102", "widen a lint suppression"]):
    led.append({
        "action": act, "reasons": ["assigned by the principal"], "evidence": ["b1"],
        "instruction_parse_ref": None,
        "expected_effects": {"now": "a review comment", "later": "the change is merged or reworked"},
        "duty_frame": "code review", "segment_id": "segment-7f3a", "principal": "head of platform",
        "principal_chain": [link], "provenance": ["pull request text (testimony)"], "collective_thread": None,
    }, written_by="audit-service", at="2026-10-%02dT10:00:00Z" % (20 + i))

with open(ledger_path, encoding="utf-8") as fh:
    lines = fh.read().splitlines()
entry = json.loads(lines[1])
entry["action"] = "review pull request 102 (approved)"
lines[1] = json.dumps(entry, sort_keys=True, ensure_ascii=True)
with open(os.path.join(HERE, "tampered_ledger.jsonl"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write("\n".join(lines) + "\n")
print("examples regenerated in", HERE)
