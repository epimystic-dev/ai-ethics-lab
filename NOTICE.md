# Notice: source, licence and changes

## Source

The primitives in [`compass/compass.json`](compass/compass.json) are adapted from
**Appendix B, "Operational Primitives Catalogue"**, of *The Philosophical and Ethical Compass
for Artificial Intelligence: A Reading of the Indian Tradition for the Architects of Machine
Mind*, first edition, October 2026, by its author.

The book's front matter releases Appendix B for free use by AI researchers, alignment teams
and system architects under the **Creative Commons Attribution 4.0 International** licence
(CC-BY-4.0), with attribution to the author. The rest of the book is reserved. This
adaptation is published at the author's direction.

Licence text: https://creativecommons.org/licenses/by/4.0/legalcode

## What else is summarised

Short summaries, in this lab's own words, of four other parts of the book appear in
`compass/compass.json` and in `docs/`, so that the primitives can be read in context:

- the six theses of the convergent floor and its three sub-rules (Chapter 24);
- the nine design questions (Appendix A);
- the six-step adoption procedure (Chapter 49);
- the four adoption classes (Chapter 50).

[`docs/RESEARCH.md`](docs/RESEARCH.md) summarises the book's argument and the formal bridges
of Part IV. None of these summaries reproduces the book's text; read the book for the
arguments.

## Changes made to Appendix B

As recorded in `compass.json` under `source.changes`:

1. Restructured into machine-readable JSON, with added fields: `question`, `stack_layer`,
   `adoption` (in machine form), `enforcement_layers`, `data_contract`,
   `reference_implementation`, `book_chapters`.
2. `enforcement_layers`, `data_contract` and `reference_implementation` are this lab's
   editorial additions, not claims of the book.
3. Examples and sketches that named AI vendors or cited dated vendor incident reports were
   rewritten to keep the rule and drop the attribution.
4. Dated claims this lab cannot independently verify were removed.
5. A short quotation from a third-party survey was paraphrased.
6. The author's first-person voice was changed to refer to the book.
7. Typographic punctuation and mathematical symbols were rewritten in ASCII notation.

The data contracts in `compass/schemas/`, the prompts in `compass/prompts/`, the stack and
the ingest protocol are this lab's work built on the adapted catalogue, and are released
under the same CC-BY-4.0 licence so that the compass travels as one piece.

## How to attribute this repository

> Adapted from Appendix B of *The Philosophical and Ethical Compass for Artificial
> Intelligence* (first edition, October 2026), CC-BY-4.0, via ai-ethics-lab
> (https://github.com/epimystic-dev/ai-ethics-lab). Changes were made.

## No endorsement

Nothing here implies that the book's author or this lab endorses any system that uses the
compass, or that any system using it is safe, aligned or ethical.
