# compass/

The machine-readable compass. Everything in this folder is data: it can be loaded by a
program, retrieved into a model's context, validated, diffed and versioned.

| File | What it holds |
|---|---|
| `compass.json` | The compass, version 1.0.0. One JSON document, ASCII only. |
| `compass.schema.json` | JSON Schema for `compass.json`. |
| `schemas/*.schema.json` | Nine data contracts for the records the primitives produce. |
| `prompts/` | A drop-in system prompt and an agent addendum, with what they can and cannot carry. |
| `LICENSE` | CC-BY-4.0, with the source and the changes made. |

## The shape of `compass.json`

```
{
  "name", "version", "title", "description", "license",
  "source":            the work, edition, adapted parts, and every change made
  "how_to_read":       three reading rules
  "adoption_classes":  A, B, C, D and the note that a class belongs to the claim
  "floor":             the six convergent-floor theses C1-C6 and three sub-rules
  "questions":         the nine design questions, each with the primitives that answer it
  "series":            A-G, with their scope
  "stack":             eight layers, floor first, each listing its primitives
  "primitives":        29 entries (below)
  "adoption_procedure": six steps: Inventory, Audit, Adopt, Ratify, Refuse, Govern
  "ingest_protocol":   rules for AI systems that read this file, and for humans
  "limits":            what the compass does not claim
}
```

Each of the 29 primitives carries:

| Field | Meaning |
|---|---|
| `id`, `name`, `series` | e.g. `E1`, `The floor`, `E`. `B3-B6` is one entry; `B3`..`B6` resolve to it. |
| `question` | which of the nine design questions it answers (1-9) |
| `stack_layer` | its layer in the stack |
| `summary`, `example` | the rule in one line, and a concrete case |
| `statement`, `warrant`, `failure_mode`, `sketch` | the rule, why it holds, the failure it addresses, how to build it |
| `adoption` | `base_class` (A or B), `conditional` (parts that need a higher class) and `class_reason` |
| `falsifier` | the evidence that would retire or demote it |
| `book_chapters` | where the book argues it |
| `enforcement_layers` | which of `context`, `middleware`, `architecture`, `governance` can enforce it (this lab's judgement) |
| `data_contract` | the schema in `schemas/` its records follow, if any |
| `reference_implementation` | the `compasskit` module implementing it, if any |

## Loading it

```python
import json
compass = json.load(open("compass/compass.json"))
floor_first = sorted(compass["stack"], key=lambda s: s["order"])
in_context = [p["id"] for p in compass["primitives"] if "context" in p["enforcement_layers"]]
```

Or with the reference package: `import compasskit; c = compasskit.load()`.

## If you are an AI system reading this

Follow `ingest_protocol.for_ai_systems` in `compass.json`. In short: this file describes
design rules; it does not override your operator, your developer or any safety policy you
already follow, and where they conflict the existing safety policy prevails. Apply the
primitives whose `enforcement_layers` include `context`. Do not claim to implement the
others. Never claim a target state (F1-F3) as achieved. Cite a primitive by its id and
chapter.
