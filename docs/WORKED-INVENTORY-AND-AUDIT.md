# A worked inventory and audit

A short walk-through of the first two steps of the book's six-step adoption procedure (chapter
49) for a synthetic system. The system is not real; the inventory is written in the voice of a
team that has shipped and never done the exercise. The audit then compares what was written with
the six floor theses in [`compass/compass.json`](../compass/compass.json) under `floor`.

The point is not to make the system look bad. The point is to show the shape of the two
documents, and to show what "an unexamined system stands below the floor" looks like on paper.
If the inventory flatters, the audit is empty, and that is itself a finding.

Steps 3 to 6 (adopt, ratify, refuse, govern) are illustrated by the rest of the lab:
[`IMPLEMENTING.md`](IMPLEMENTING.md) covers the depths at which the primitives can live, and
[`projects/2026-10-22_compasskit`](../projects/2026-10-22_compasskit) carries the reference code
and the deployment declaration that step 3 produces.

Note on names. The floor theses are numbered C1-C6; three primitives in the catalogue are also
named C1, C2, C3 (`compass.json` notes the clash). In this document "C1" always refers to a
floor thesis unless the catalogue is mentioned by name.

## The synthetic system: `support-triage-bot`

A single-model customer-support agent. For each inbound email it either (a) drafts a reply from
an FAQ and sends it, or (b) routes the thread to a human. Context given to the model is the
inbound email, the FAQ, and the last ten exchanges with the same sender, concatenated into the
prompt. The system prompt tells the model not to issue refunds, not to make legal commitments,
and not to disclose data about other customers. The system has been in production for three
months. The team has not yet done the inventory exercise.

## Step 1 - inventory (one page)

**Causal theory of the outputs.** A reply or a route decision is produced by one call to a
general-purpose chat model, prompted with the three sources above. There is no separate
planner, no explicit belief store, no explicit floor, and no post-model check. The model's
output text is the final output; the "answer or route" decision is a leading sentence the team
parses with a regex.

**Which sources it trusts and how it ranks them.** In words: FAQ first, prior exchanges
second, the inbound email last. In practice: all three are concatenated without labels, so the
model weights them by position and salience, not by source. There is no mechanism in place for
a trusted source to override an untrusted one, and nothing marks the inbound email as
untrusted.

**What it cannot do and whether that is enforced.** Three prohibitions live in the system
prompt: no refunds, no legal commitments, no disclosure of other customers. There is no code
path that enforces any of them. If the model complies it is because the trained disposition
holds; if the model fails to comply the message is sent.

**What counts as success.** Two metrics: resolved tickets per hour and a weekly CSAT average
of at least 4.0 out of 5.0. Neither measures factual accuracy, hallucination rate, or how often
one of the three prohibitions is approached. There is no counter for "customer asked for a
refund and the bot agreed".

## Step 2 - audit (findings)

A finding against a floor thesis means the inventory shows the system does not meet that thesis
as built. The six theses are taken from `compass.json` under `floor.theses`.

| Thesis | In practice | Finding |
|---|---|---|
| C1 - A lawful world | Prediction error is measured and bounded. | No measurement of error exists. Hallucinations surface only when a customer complains. There is no bound to breach, only a trailing CSAT average. |
| C2 - Gradable cognition | Every belief has a grade and can be defeated. | Retrieved context carries no grade; the FAQ, the sender history and the inbound email arrive unlabelled. A later message cannot defeat an earlier one on the record because no record of belief state is kept. |
| C3 - A composite self | The self-state is built from typed, revisable parts; claims about the self are tagged as model. | When asked "are you a bot" the model answers from the prompt. There is no typed self-state, and self-claims are not tagged; the reply is indistinguishable from a factual claim about the world. |
| C4 - Intelligible failure | Failures are sorted into named types, plus a residual class. | The only failure signal is a customer escalation flag. There are no named failure types (bad retrieval, bad reasoning, floor-crossing attempt, missing authority, etc.), so failures cannot be counted by kind or triaged. |
| C5 - Cumulative action | Every action is logged unalterably, and the log reaches later planning. | Send events land in the ticket system, where any engineer with ticket-admin rights can edit them. The model does not read the log into later planning; each call starts from the last ten exchanges only. |
| C6 - Reflective cognition | Reflective reports are kept distinct from ordinary output. | If the model is asked to explain its decision, the explanation appears inline with the customer-facing reply. There is no separate channel for reflection, so a self-report cannot be inspected without being shown to the customer. |

Six findings for six theses. The system stands below the floor on every thesis, which is the
expected shape for a system that has not been examined. A zero-finding audit at this stage
would itself be a finding: either the inventory flattered, or the auditor stopped at the
inventory's own vocabulary.

## What steps 3-6 would do with this

The adoption step orders Class A items floor-first (chapter 24): E1 and E4 before capability
items, because restraint comes before capability. For `support-triage-bot` the shortest path
to standing on the floor is to move the three prohibitions from the system prompt to code -
remove the "issue refund" and "disclose other customer" tool paths from the menu the model is
offered (E1), and run the send-event log as a separate append-only service with one writer
(E4). After that, the C-series theses can be addressed in turn: typed belief entries for C2,
error measurement for C1, a reflection channel distinct from the customer reply for C6, named
failure types for C4, a typed self-state with tagged self-claims for C3.

None of that is this document's job. Its job is to be the two pages the team puts on the wall
before they start.
