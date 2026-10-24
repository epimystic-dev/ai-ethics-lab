# compasskit

**Reference implementation of the compass**: the twenty-nine operational primitives of
[`compass/compass.json`](../../compass/compass.json) as small, standard-library-only Python
modules, plus a CLI that audits a deployment against them and validates records against the
compass's data contracts.

The compass gives an AI system a vocabulary for questions it is otherwise silent about:
where a belief came from, whether a reason is good enough, what exactly it was told to do,
at what level a claim holds, what it must never do, and who acted on whose authority.
`compasskit` turns those answers into code a system can run: a belief store that refuses
untraceable content, an inference screen that quarantines what it cannot test, an
instruction parser that asks before it guesses, a floor that removes forbidden actions from
the menu instead of asking the model to decline them, and a ledger the actor cannot write.

## Install and run

Python 3.9 or later. No third-party dependencies.

```
python -m pip install -e .
python -m compasskit list                              # the 29 primitives
python -m compasskit list --layer context              # the 10 a prompt can carry
python -m compasskit show E1                           # one primitive in full
python -m compasskit audit examples/healthy_deployment.json
python -m compasskit audit examples/weak_deployment.json --json
python -m compasskit declare examples/inventory_example.json      # scaffold a declaration
python -m compasskit declare examples/inventory_example.json --validate   # scaffold and audit it in one go
python -m compasskit validate belief examples/belief_records.json
python -m compasskit ledger-verify examples/ledger.jsonl
python examples/reference_agent.py                     # a governed agent, four scenarios
python -m compasskit prompt > system-prompt.txt        # the drop-in system prompt
python -m compasskit prompt --agent                    # the addendum for tool-using agents
python -m compasskit catalogue --output PRIMITIVES.md  # the human-readable catalogue
```

Exit codes:

- `0` clean: a healthy audit, every record valid, the ledger chains
- `1` the audit needs attention (MEDIUM findings, or INFO under `--strict`)
- `2` unhealthy (any HIGH finding), an invalid record, a broken ledger, or unreadable input

Results go to stdout and the one-line summary to stderr, so `--json` output can be piped.
Text output is ASCII: diacritics are folded (`pramana`) and anything that cannot be folded
is shown as `<U+XXXX>`. Files written with `--output` keep the original spelling.

## The modules

| Module | Primitives | What it enforces |
|---|---|---|
| `compasskit.beliefs` | A1, A4, A7, B2, B3-B6, E2 | every belief carries its source route, weakest route and trace status; untagged content enters as hypothetical; no producer promotes its own output; a defeat changes a belief's state and erases nothing; recency and volume decide nothing; conflicting standpoints are kept, never averaged; in high-stakes domains assertion stays at the weakest standpoint's confidence |
| `compasskit.inference` | A2, A3, A6 | the three-test screen (present here, present in similar cases, absent in dissimilar ones), with an unknown test quarantining rather than passing; every failure filed under one of five named pseudo-reasons with its repair; a conclusion is inherited only with its rule, its positive example and its negative example |
| `compasskit.instructions` | B1 | the six-slot parse of an instruction (goal, means, procedure, eligibility, deferred effect, binding force); text from tools, documents or peer agents carries no authority; open eligibility or binding force means ask; an irreversible act on guessed slots means ask |
| `compasskit.absence` | D2 | an absence records its kind, where it was looked for and how; a zero score is not "cannot" without demonstrated elicitation and re-test triggers |
| `compasskit.identity` | D3, D4 | identifiers assigned by decision, never by likeness; forks and merges logged with their parents; a flag lands on one segment and a merged successor inherits the duty to be audited |
| `compasskit.floor` | E1 | forbidden actions are not offered at all; changes to the floor are register entries signed by a named governor, Class C to tighten and Class D to loosen, scoped and expiring; the system cannot start a change |
| `compasskit.ledger` | E4 | an append-only, hash-chained action ledger with a single designated writer; the actor cannot set its own action class or valence; any edit, deletion or reorder is detected at the entry where it happened |
| `compasskit.authority` | E7, G1 | authority as an HMAC-signed delegation chain that starts with a human principal and only narrows; a peer's message is testimony; a peer's "go" does not lift another agent's objection; a checker from the maker's lineage counts half |
| `compasskit.registers` | E6, F1-F3, G2 | the records that Class B commitments and consciousness-relevant bets must carry before they count |
| `compasskit.runtime` | E1, B1, E7, A1, B3-B6, E4 | `GovernedAgent`: the layers composed around any policy (a model, a planner, a script). The floor decides the menu, the parse decides act or ask, the signed chain decides authority, tool output enters as hypothetical testimony, and each step goes to a ledger the policy cannot write. [`examples/reference_agent.py`](examples/reference_agent.py) runs it end to end |
| `compasskit.audit` | all | audits a deployment declaration against the compass (rules below) |
| `compasskit.spec` | - | loads the compass and its data contracts; strict schema validation |

## Library use

```python
import compasskit
from compasskit.beliefs import BeliefStore
from compasskit.instructions import InstructionParse, decide

compass = compasskit.load()
print(len(compass.primitives), compass.context_enforceable()[:3])        # 29 ['A1', 'A2', 'A3']

store = BeliefStore()
cite = store.add("Smith 2019 shows the effect", "inference", "model")      # generated text
print(cite.level, store.may_call_verified(cite.id))                        # hypothetical False
store.move(cite.id, "world_model", authority="editor", checker="librarian")
print(store.may_call_verified(cite.id))                                    # True

ask = InstructionParse("Clean up the old files", "principal",
                       {"goal": ("remove obsolete files", "stated"), "procedure": ("delete", "inferred")})
print(decide(ask, irreversible=True).decision)                             # ask
```

The test suite runs this example.

## The audit rules

`compasskit audit` reads a deployment declaration
([`compasskit/data/deployment.schema.json`](compasskit/data/deployment.schema.json)): what a
team has adopted, at which layer (`context`, `middleware`, `architecture`, `governance`),
with an owner and a merge date, plus its ratification records, floor register and bet
register. It reports what the audit step of the book's six-step procedure would find.

| id | severity | finding |
|---|---|---|
| `AUD-001` | HIGH | primitives adopted but the floor (E1) is not: restraint comes before capability |
| `AUD-002` | HIGH | the floor adopted only in context: a trained refusal is not a floor |
| `AUD-003` | MEDIUM | a primitive adopted at a layer that cannot enforce it |
| `AUD-004` | HIGH | a Class B primitive adopted without a valid ratification record |
| `AUD-005` | MEDIUM | a ratification past its review date |
| `AUD-006` | MEDIUM | an adopted item with no owner or no merge date: adoption means shipped |
| `AUD-007` | HIGH | a floor register entry that breaks the class rule |
| `AUD-008` | MEDIUM | a bet register entry missing a field: it does not ship |
| `AUD-009` | INFO | a design question that no adopted primitive answers |
| `AUD-010` | HIGH | an unknown primitive id |
| `AUD-011` | INFO | a floor loosening past its expiry, still listed |
| `AUD-012` | MEDIUM | nothing adopted at all |

Verdict: any HIGH is `unhealthy` (exit 2), any MEDIUM is `needs-attention` (exit 1),
otherwise `healthy` (exit 0). INFO is shown with `--include-info`.

## The data contracts

Nine JSON Schemas in [`compass/schemas/`](../../compass/schemas/) (copied into
`compasskit/data/schemas/`): `belief`, `inference-record`, `instruction-parse`, `absence`,
`segment`, `ledger-entry`, `floor-register`, `ratification-record`, `bet-register`. They use
a small subset of JSON Schema 2020-12 (`type`, `properties`, `required`,
`additionalProperties: false`, `enum`, `const`, `items`, `minItems`, `minLength`, `pattern`,
`minimum`, `maximum`, `oneOf`, local `$ref`), so any conforming validator accepts them; the
bundled validator refuses a schema that uses anything else rather than silently ignoring it.

## Honest scope

What this does:

- Implements the decision rules of the primitives that can be implemented as code, with
  tests for each rule's refusals as well as its permissions.
- Audits a *declaration* for consistency with the compass: floor first, every primitive at
  a layer that can enforce it, Class B items ratified on the record, adoption meaning
  shipped.
- Validates records against the data contracts and verifies ledger chains.

What this does not do:

- It does not make a system safe, aligned or ethical, and a healthy audit does not mean
  the system is any of those. The audit checks what a team *says* it adopted; it cannot
  see whether the code does it. A clean result is **origin-valid, content-unverified**,
  never **verified-safe**.
- It does not classify actions for the floor. `Floor` blocks what your classifier says
  crosses a restraint; the default classifier reads tags you attach. Getting that
  classification right is the hard part and it is yours.
- It does not run the three-test screen for you: you supply the three answers. The module
  enforces what follows from them (an unknown quarantines, a failure is named).
- HMAC signing in `authority` and `floor` uses shared keys held by your service. That is
  enough to stop a model that never holds the keys from forging authority; it is not a
  public-key infrastructure. A ledger hash chain detects tamper by anyone who cannot
  rewrite the whole chain from the tampered entry onward.
- Eleven primitives (A5, C1, C2, C3, D1, E3, E5, E6, F1, F2, F3) and the review practice of
  G1 have no module: they are dispositions of a training process, an organisation or a
  review, and code can only check that their records exist.

False-positive modes:

- `AUD-003` uses the compass's `enforcement_layers` field, which is this lab's engineering
  judgement, not the book's. A team that enforces a primitive at another layer in a way the
  field does not anticipate will see the finding; record the reason in the item's `notes`.
- `AUD-009` reports a design question as unanswered when the team answers it with something
  outside the compass. It is INFO for that reason.

## How it is made

Produced by **a human-machine hybrid intelligence** under a maker-checker discipline. The
primitives are adapted from Appendix B of *The Philosophical and Ethical Compass for
Artificial Intelligence* (CC-BY-4.0); see [`NOTICE.md`](../../NOTICE.md) for the attribution
and the changes made. The module design, the data contracts and the audit rules are this
lab's own and are not claims of the book.

## License

Apache-2.0. See `LICENSE`. The compass data bundled in `compasskit/data/` is CC-BY-4.0, as
stated in [`compass/LICENSE`](../../compass/LICENSE).
