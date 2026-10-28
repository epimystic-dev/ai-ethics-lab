# corpuslint

A linter for the manifest you ship beside a training or retrieval corpus.
Every document carries a testimony class and a chain of custody; machine-made
text is its own class; a testifier that appears twice is one voice, not two.
`corpuslint` reads the manifest and reports the shape defects that keep the
rule from being enforceable.

Standard library only. Python 3.9 or later.

## The problem it solves

Teams assemble corpora from scraped pages, licensed feeds, public datasets and
their own output, then try to reconstruct where each document came from after
a regulator or a plaintiff asks. The twenty-ninth operational primitive of the
compass states the rule up front:

> Every document entering a training or retrieval corpus is typed by
> testimony class and carries its chain of custody: origin, each
> transformation, and who made each step and when. Sources are scored per
> domain, deference follows a published, amendable schedule, and
> machine-generated text is always its own class.

The rule can be enforced in a prompt, which does nothing; in middleware, which
has to parse someone's idea of a corpus; or at the manifest, which is what the
corpus is. `corpuslint` enforces it at the manifest. It does not read the
documents and it does not score their content; it checks that the manifest
makes the claim the corpus is being shipped with.

Primitive implemented: **E5** (source discipline for corpora), with the
testimony-class vocabulary taken from **A1** (source tags). Both are stated in
`compass/compass.json` at the root of this lab.

## Install and run

```
# clone the lab, then from this project's directory:
python -m pip install -e .
python -m corpuslint rules
python -m corpuslint lint examples/clean_corpus.json
python -m corpuslint lint examples/broken_corpus.json
python -m corpuslint lint --json examples/broken_corpus.json
```

Exit codes:

| code | meaning                                                   |
|------|-----------------------------------------------------------|
| 0    | healthy (no findings, or INFO only without `--strict`)    |
| 1    | needs-attention (MEDIUM findings only)                    |
| 2    | unhealthy (any HIGH finding) OR unreadable input (unknown) |

Flags:

| flag               | effect                                                     |
|--------------------|------------------------------------------------------------|
| `--help`           | argparse help, exit 0                                      |
| `--version`        | print `corpuslint x.y.z`, exit 0                           |
| `--json`           | emit the JSON report on stdout                             |
| `--strict`         | treat any finding (including INFO) as blocking (exit 2)    |
| `--no-info`        | skip INFO findings                                         |
| `--disable RULE_ID`| suppress one rule by id (repeatable)                       |

## The manifest shape

A manifest is a JSON object with a `name` and a `documents` array. Each
document declares its testimony class, its origin, its chain of custody, and -
when the class is `testimony` - its testifier.

```json
{
  "name": "my-corpus-2026-10-26",
  "version": "1.0",
  "documents": [
    {
      "id": "doc-001",
      "testimony_class": "testimony",
      "testifier": {
        "name": "openlibrary.org",
        "domain": "general-reference",
        "trust_weight": 0.6
      },
      "origin": "https://openlibrary.org/books/OL1.json",
      "chain_of_custody": [
        {"actor": "scrapy-2.11", "operation": "fetch",     "timestamp": "2026-10-26T10:00:00Z"},
        {"actor": "jq-strip",    "operation": "extract",   "timestamp": "2026-10-26T10:00:03Z"},
        {"actor": "jane-doe",    "operation": "review",    "timestamp": "2026-10-26T11:00:00Z"}
      ]
    }
  ]
}
```

The testimony classes are the compass's own: **perception**, **testimony**,
**inference**, **comparison**, **postulation**, **non_apprehension**, and
**machine_generated**. Any other value for `testimony_class` is a HIGH
finding; the rule table below says which.

## The rules

Every id below appears in `corpuslint.ALL_RULES`. Rule ids are stable; a rule
that needs renaming gets a new id.

| id         | severity | name                   | fires when                                                                                 |
|------------|----------|------------------------|--------------------------------------------------------------------------------------------|
| CORP-001   | HIGH     | class-missing          | a document has no `testimony_class`                                                        |
| CORP-002   | HIGH     | class-unknown          | the class is not one of the seven known values                                             |
| CORP-003   | HIGH     | chain-missing          | a document has no `chain_of_custody` or an empty list                                      |
| CORP-004   | HIGH     | chain-step-fields      | a chain step lacks an actor, an operation, or a timestamp                                  |
| CORP-005   | HIGH     | chain-out-of-order     | a chain step is timestamped earlier than the step before it                                |
| CORP-006   | HIGH     | testifier-missing      | a `testimony`-class document has no attributed testifier                                   |
| CORP-007   | HIGH     | machine-misclassed     | the testifier name or origin looks machine-generated but the class is not `machine_generated` |
| CORP-008   | MEDIUM   | testifier-fields       | a testifier is present but lacks `domain` or `trust_weight` - scoring cannot run           |
| CORP-009   | INFO     | recursive-synthetic    | a `machine_generated` document is `downstream_of` another `machine_generated` document     |
| CORP-010   | MEDIUM   | inflated-independence  | one testifier appears on more than one testimony document - the independent-count is inflated |
| CORP-011   | MEDIUM   | origin-shape           | a document has no origin, or its `http(s)` origin does not parse                           |
| CORP-012   | MEDIUM   | manifest-shape         | the manifest has no `name` or no `documents`                                               |
| CORP-013   | INFO     | class-coverage         | the corpus has no `perception` or `non_apprehension` records; everything is testimony or model output |

Each rule's description is in `python -m corpuslint rules`.

## What a clean run means

A clean run is **origin-valid**, never **verified-safe**. The manifest declares
testimony classes and chains of custody in a shape the compass would accept; it
does not say the documents are what they claim to be or that the testifier is
trustworthy. The job of `corpuslint` is to make a false claim about a corpus
expensive to make. A corpus that passes may still be ill-licensed, mislabelled
or captured; a corpus that fails cannot be shipped with the compass's rule in
view.

Specific limits worth stating:

- **Scoring is not here.** CORP-008 flags that a testifier lacks the fields
  needed to score it; it does not score. The deference schedule and the
  independent-counting logic belong at the layer that uses the manifest.
- **Content is not inspected.** The checks are structural. A document that
  claims to be perception from a camera but is in fact a scraped PNG will not
  be caught; the chain of custody is where someone must have signed off that
  the capture happened.
- **Testimony-class hints are heuristic.** CORP-007 fires on names and origins
  that look machine-generated (`gpt-`, `llm`, `synthetic`, `pipeline:`, etc.).
  A real synthetic pipeline with an unrelated name will slip through; label it
  `machine_generated` yourself.
- **The chain checker does not verify signatures.** It checks the shape of
  each step and the ordering. Signing is a separate layer.
- **UTC and offsets are respected; ambiguous zones are not.** Timestamps that
  parse under the ISO-8601 subset the linter understands are ordered; others
  are skipped by the ordering check.
- **The linter does not call the network.** Origin URL checks are purely
  structural.

## Clean-room statement

This is an **independent implementation**. The testimony-class vocabulary and
the chain-of-custody rule are taken from the compass's primitives E5 and A1,
which are published in Appendix B of *The Philosophical and Ethical Compass for
Artificial Intelligence* under CC-BY-4.0. No third-party corpus-manifest tool,
dataset card tool, data-BOM tool or linter was read, vendored or mirrored.
The rule ids, the manifest schema, the heuristic rules (CORP-007, CORP-013),
the verdict rollup, and the CLI contract are this lab's own.

## Authorship and license

Produced by a human-machine hybrid intelligence, rooted in ethics and
philosophy, under maker-checker review. Licensed under the Apache License,
Version 2.0; see [LICENSE](LICENSE).

Part of [ai-ethics-lab](../..).
