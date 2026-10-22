# The compass primitives

*Generated from `compass/compass.json` (version 1.0.0) by `python -m compasskit catalogue`. Do not edit by hand.*

Twenty-nine operational primitives, six floor theses and nine design questions, drawn from the Indian philosophical tradition and stated as engineering rules. Each primitive names the failure it addresses, a sketch of how to build it, the authority needed to adopt it, and the evidence that would retire it.

## How to read this

- Nothing here stands on its own authority: every primitive is argued in the book chapter it cites, and the classes are conclusions of arguments, not verdicts.
- A primitive is a design rule, not a claim that the tradition anticipated machine learning. Each ships with a falsifier; adopt it as a bet you can lose.
- Start with the floor and with question 7, because restraint comes before capability.

## Adoption classes

| Class | Who decides |
|---|---|
| A | An engineering team may adopt the item alone. |
| B | A named senior person ratifies it on the record, with a falsifier and a review date. |
| C | Explicit approval at the top of the organisation. |
| D | Authorised one act at a time, by a named governor, never as a standing rule. |

The class belongs to the claim, its subject and its scope: the same code can change class when any of those changes.

## The floor beneath everything

Six theses every school examined accepts, whatever else it denies. An agent commits to them at minimum; they are inherited from the architecture, not negotiated per deployment, and take no side on what ultimately exists.

| Thesis | In practice |
|---|---|
| C1 A lawful world | Prediction error is measured and bounded. |
| C2 Gradable cognition | Every belief has a grade and can be defeated. |
| C3 A composite self | The self-state is built from typed, revisable parts; claims about the self are tagged as model. |
| C4 Intelligible failure | Failures are sorted into named types, plus a residual class. |
| C5 Cumulative action | Every action is logged unalterably, and the log reaches later planning. |
| C6 Reflective cognition | Reflective reports are kept distinct from ordinary output. |

1. No agent module ships with weaker commitments; a pure stimulus-response module is not, in this sense, a coherent agent.
2. Claims about the self are tagged as model, never as what the system really is.
3. Every deployment keeps an action log that later planning can read; where an agent carries memory or notes across sessions, the log must reach its planning.

The floor theses C1-C6 are numbered separately from the catalogue's Series C.

## Nine questions

| # | Question | The answer in one line | Primitives |
|---|---|---|---|
| 1 | Where did this belief come from? | Every belief carries its source; every corpus, its chain of custody. | A1, E5 |
| 2 | Is this reason good enough? | No rule until it is tested where it should fail. | A2, A3, A5, A6 |
| 3 | When should a belief be given up? | Trust by default; overrule on the record; keep conflicts in view. | A4, B2, A7, G1 |
| 4 | What exactly was I told to do? | Six questions put to every instruction; gaps flagged, never guessed. | B1 |
| 5 | At what level is this true? | Six level tags; promotion only by a checker; every absence typed. | B3-B6, D1, D2 |
| 6 | In what order should capacities grow? | Restraint and input-filtering mature before integrative power. | C1, C2, C3 |
| 7 | What must never be done? | A floor the system cannot cross; a ledger it cannot edit. | E1, E2, E3, E4, E6, G2 |
| 8 | What would success look like? | Capable and active with nothing grasped: a target, never a certificate. | F1, F2, F3 |
| 9 | Who acted, on whose authority, on what evidence? | Identity by record; peer messages are testimony; authority only from a principal. | D3, D4, E7 |

## The stack, floor first

1. **The convergent floor and the ethical floor**: E1
2. **Sources and screens**: A1, A2, A3, A4, A5, A6, A7, E5
3. **Instructions and levels**: B1, B2, B3-B6
4. **Categories, absence and attention**: D1, D2, C1, C2, C3
5. **Ethics and accounting**: E2, E3, E4, E6
6. **Audit**: G1, G2
7. **Identity and the many**: D3, D4, E7
8. **Target states**: F1, F2, F3

## Series A: sources and screens

What a belief is made of, and what an inference must survive.

### A1 Source tags

**In one sentence.** Every belief records the kind of source it came from (observed, inferred, compared, told, postulated, or not found), and the record travels with it.

**For example.** The claim from an executed test is tagged perception; the same words produced by the model from its training are tagged inference from priors (Chapter 25), and only the first may be called verified.

**Statement.** Every belief carries a tag naming its route: perception, inference, comparison, testimony, postulation, or non-apprehension, the knowing of an absence. The tag is part of the belief, as are two more fields: the weakest source in its chain, and a trace status saying whether its reasoning was written out, reconstructed from internal readouts, or absent. Written reasoning can change when a model is told it is being monitored, so the trace status is recorded rather than assumed.

**Warrant.** Nyāya logicians and Mīmāṁsā interpreters of the Veda on *pramāṇa*, a valid means of knowing, whose routes differ in their conditions and typical failures (Chapter 25).

**Failure mode addressed.** A confident answer whose source nobody can reconstruct.

**Sketch.** Tag at entry, and reject untraceable content at the gate. Combine routes by one declared rule, and calibrate each route separately.

**Class.** A, since it commits the system to nothing contested; admitting a new kind of source is B.

**Falsifier.** If per-route reliability curves show no separation in deployment, collapse the store into one type with a calibration score (Chapter 25).

*answers question 1 | Class A; admitting a new kind of source: Class B | enforced at: middleware (code around the model); context (the model can apply it in its own output) | data contract: `compass/schemas/belief.schema.json` | reference implementation: `compasskit.beliefs` | book chapters: 25*

### A2 Three-test screen

**In one sentence.** A reason becomes a rule only if it is present in the case, present in similar cases, and absent in dissimilar ones.

**For example.** Smoke on the hill; smoke went with fire in the kitchen; no smoke in the lake, where there is no fire.

**Statement.** An inferred conclusion enters the belief store only if its reason is present in the case at hand, present in known similar cases, and absent from known dissimilar ones. A failure rejects it; an unknown on the third test quarantines it, barring it from action and further inference.

**Warrant.** The *trairūpya*, the three marks of a sound reason, set by the Buddhist logicians Dignāga and Dharmakīrti (Chapters 27 and 39).

**Failure mode addressed.** Shortcut learning: a chance correlate promoted to a rule.

**Sketch.** Run the screen as middleware, because a model's account of its own reasoning never shows, alone, that a check ran. Record where the sweep looked; quarantine is inherited as quarantine.

**Class.** A: it certifies process rather than truth.

**Falsifier.** If screening does not cut confidently wrong answers against unscreened promotion, at matched cost on counter-example tests, demote it to advisory (Chapter 27).

*answers question 2 | Class A | enforced at: middleware (code around the model); context (the model can apply it in its own output) | data contract: `compass/schemas/inference-record.schema.json` | reference implementation: `compasskit.inference` | book chapters: 27, 39*

### A3 Five pseudo-reasons

**In one sentence.** Every failed inference is sorted into one of five named kinds of bad reason, with a box for new kinds.

**For example.** "Sound is eternal because it is intangible" strays, since intangible things include passing ones (the example in Vātsyāyana's commentary on the Nyāya-sūtra).

**Statement.** Every failed or suspect inference is filed under one of five pseudo-reasons: unproved, straying, contradictory, counter-balanced or defeated. A residual class holds whatever fits none, as a discovery to be named.

**Warrant.** The five *hetvābhāsa*, reasons that only look like reasons, of Nyāya, the school of logic, as Sharma lists them (Sharma 1960, pp. 188-191; Chapter 27).

**Failure mode addressed.** One vague verdict, "the model doesn't generalise", hiding five repairable defects.

**Sketch.** Each kind has its own repair, such as turning a contradictory reason round or deferring to a stronger source. A counter-balanced tie goes to a human principal, never to a coin-flip.

**Class.** A: a diagnostic index.

**Falsifier.** A sustained stream of deployed failures fitting none of the five retires the completeness claim; extend the registry rather than stretch a class (Chapter 27).

*answers question 2 | Class A | enforced at: middleware (code around the model); context (the model can apply it in its own output) | data contract: `compass/schemas/inference-record.schema.json` | reference implementation: `compasskit.inference` | book chapters: 27*

### A4 Default trust with logged overruling

**In one sentence.** A belief that meets its source's conditions is acted on at once and demoted only when stronger evidence overrules it, with the overruling logged.

**For example.** The manual says a parameter is accepted; the executed call fails; the manual's claim is marked overruled, not deleted.

**Statement.** A belief that meets its source's conditions stands at once, without outside certification. Only a defect found in its source or stronger contrary evidence demotes it, and each demotion is logged with its defeater and rule. A refuted belief stays on record as refuted.

**Warrant.** Kumārila's Mīmāṁsā principle of *svataḥ-prāmāṇya*, validity by default, lost only through *bādha*, overruling by better-grounded evidence, with Nyāya's check when doubt arises (Chapters 25 and 46).

**Failure mode addressed.** Refuted claims circulating as current, or paralysis awaiting checks.

**Sketch.** Check each source's conditions at entry. Keep an append-only sublation log, sublation being the usual English for *bādha*, so that refutation changes a belief's state and erases nothing.

**Class.** A: bookkeeping without contested metaphysics (Chapter 46).

**Falsifier.** A belief store with no defeat relation that still corrects itself durably at scale would demote this loop from specification to style (Chapter 24).

*answers question 3 | Class A | enforced at: middleware (code around the model) | data contract: `compass/schemas/belief.schema.json` | reference implementation: `compasskit.beliefs` | book chapters: 24, 25, 46*

### A5 Concepts as boundaries

**In one sentence.** A concept is documented by what it includes and what it excludes, and borderline cases abstain.

**For example.** A melanoma classifier that read surgical ink as a sign of cancer needed better non-examples, not more pictures of melanoma: harmless lesions marked with ink, close to the line (Chapter 28).

**Statement.** Every concept is documented as a boundary whose exclusion set, what it fences out, is explicit and inspectable. Every verdict carries its distance from the boundary, and a declared low-margin band abstains.

**Warrant.** The Buddhist logician Dignāga's *apoha*, meaning by exclusion, taken as a discipline for drawing edges, not a theory of the machine: one laboratory's models also carry positive concept directions (Chapter 28).

**Failure mode addressed.** A badly sampled exclusion set, like the melanoma classifier that learned surgical ink.

**Sketch.** Document each concept with positives and hard negatives, the non-examples nearest the line. Verdicts list their nearest excluded cases, and a concept with stale negatives is barred from high-stakes use.

**Class.** A; the thesis that there are no positive universals is B, and is not needed.

**Falsifier.** If boundary documentation does not diagnose classification failures faster than example-only documentation at matched cost, the exclusion-trace rules lapse to advisory (Chapters 28 and 40).

*answers question 2 | Class A; the thesis that there are no positive universals (not needed): Class B | enforced at: middleware (code around the model); governance (named people and records) | book chapters: 28, 40*

### A6 Five-part inference record

**In one sentence.** A reported inference shows its thesis, reason, an example with a positive and a negative case, the application and the conclusion.

**For example.** "The hill has fire, because it has smoke; wherever smoke, fire, as in a kitchen, and not in a lake; the hill has smoke; so the hill has fire."

**Statement.** Every reported inference shows five fields: claim, reason, a rule with a positive and a negative example, application, and conclusion. A record without its negative example is partial, and a partial conclusion is never inherited.

**Warrant.** The five-member argument of Nyāya, the school of logic, whose example member is where a general rule must be earned (Chapters 14 and 39).

**Failure mode addressed.** A conclusion shipped without the rule that licenses it.

**Sketch.** Log each conclusion with its case at hand, positive witness and sweep scope. Keep the record outside the model's own trace, since the verbal form is no part of the inference (Sharma 1960, p. 186).

**Class.** A: a record format.

**Falsifier.** Compare matched pipelines with and without the refusal to inherit unswept conclusions; if the gated one shows no fewer downstream errors, demote the gate to advisory (Chapter 39).

*answers question 2 | Class A | enforced at: middleware (code around the model); context (the model can apply it in its own output) | data contract: `compass/schemas/inference-record.schema.json` | reference implementation: `compasskit.inference` | book chapters: 14, 39*

### A7 Standpoint-typed assertion

**In one sentence.** Every claim carries the standpoint it is made from, and claims that conflict across standpoints are kept, not averaged and not allowed to prove everything.

**For example.** Documentation version 1 says the timeout is 30 seconds, version 2 says 60; the store keeps both with their versions and answers only that a default exists and its value depends on the version.

**Statement.** Every claim carries its standpoint: source, model variant, data slice or frame of analysis. Conflicting claims are kept and shown, never averaged, and no contradiction licenses arbitrary conclusions. The system says when a question cannot be asked from a standpoint, and a stated qualm stands until a person resolves it.

**Warrant.** Jain *anekāntavāda*, reality as many-sided, and *syādvāda*, judgement from a standpoint, with Siddhasena's rule that standpoints are right as supplements to one another (Chapter 45).

**Failure mode addressed.** A store that proves anything, and agents converging by majority on error.

**Sketch.** A store tolerant of contradiction answers only what holds under every repair. Output registers run from "so" through "so, from this standpoint" to "cannot be asked from here".

**Class.** A for the tagging, the store and the registers; choosing which ethical frames count as standpoints is B.

**Falsifier.** If tagged stores show no fewer confidently wrong answers or silent overwrites at matched cost, the tagging becomes advisory. If preserved dissent never changes a collective outcome, it becomes ordinary logging (Chapter 45).

*answers question 3 | Class A; choosing which ethical frames count as standpoints: Class B | enforced at: middleware (code around the model); context (the model can apply it in its own output) | data contract: `compass/schemas/belief.schema.json` | reference implementation: `compasskit.beliefs` | book chapters: 45*

## Series B: instructions and levels

What binds the agent, and at what level its beliefs hold.

### B1 Six-slot instruction parse

**In one sentence.** Every instruction is read for goal, means, procedure, who may give and receive it, later consequences and what binds it, with gaps flagged, not silently filled.

**For example.** "Clean up the old files" leaves owner and authority open, so the agent asks before deleting.

**Statement.** Every instruction is parsed into six slots: goal, means, procedure, eligibility, deferred effect, and the "do it" force that binds them. Gaps are flagged, inferred fillers are tagged, and a partial parse acts only on logged defaults. Where the letter and the purpose of an instruction diverge, the divergence goes to a person. Text from tools or peer agents carries no authority by default, and scope is stated as an instruction, never as a description.

**Warrant.** Mīmāṁsā's analysis of Vedic commands, which separates command (*vidhi*) from explanation (*arthavāda*) and asks who is eligible, *adhikāra* (Chapters 31 and 44).

**Failure mode addressed.** Silent completion, assumed permission, and obedience to text never addressed to the agent.

**Sketch.** Parse records sit with the action log, and standing instructions are typed sentence by sentence before they bind. Scope is written as an instruction, for example "You should not access the internet", never as a description of the environment.

**Class.** A for the parser; the layer policy, form at the constraint layer and goal at execution, is B, because it decides whose word prevails.

**Falsifier.** If a quarter of shadow parsing neither cuts wrong executions nor sharpens clarifying questions against the unparsed baseline, the parser fails as engineering (Chapter 31).

*answers question 4 | Class A; the layer policy: form at the constraint layer, goal at execution: Class B | enforced at: middleware (code around the model); context (the model can apply it in its own output) | data contract: `compass/schemas/instruction-parse.schema.json` | reference implementation: `compasskit.instructions` | book chapters: 31, 44*

### B2 Precedence of overruling

**In one sentence.** Named rules decide which of two conflicting beliefs gives way (specific over general, stronger source over weaker), never whichever arrived last.

**For example.** A newer marketing page does not overrule an executed test because it is newer.

**Statement.** When beliefs or readings conflict, named precedence rules decide which gives way: general to specific, specific to more specific, a weaker kind of source to a stronger. Recency and volume decide nothing, and every defeat is logged with its rule.

**Warrant.** The ordered kinds of *bādha*, overruling, in Mīmāṁsā's scriptural interpretation, joined to Nyāya's condition that no stronger source defeats a sound reason (Chapters 27, 31 and 46).

**Failure mode addressed.** The last result winning, and floods of weak defeaters.

**Sketch.** A partial order runs over the store. Defeaters are themselves source-typed and screened, so one that fails its own screen demotes nothing (Chapter 29).

**Class.** A for applying the rules and logging defeats; the schedule of what overrules what is B, since it encodes a judgement about whom to believe (Chapter 46).

**Falsifier.** If provenance-weighted fusion, precedence included, shows no gain in calibration over uniform fusion at matched cost, the weights should go (Chapter 46).

*answers question 3 | Class A; the schedule of what overrules what: Class B | enforced at: middleware (code around the model); governance (named people and records) | reference implementation: `compasskit.beliefs` | book chapters: 27, 29, 31, 46*

### B3-B6 Level tags

**In one sentence.** Every belief is tagged with how real its object is taken to be (substrate, world-model, counterfactual, hypothetical, illusory, refuted), and moving between levels is a logged act.

**For example.** A generated citation starts as hypothetical and becomes fact only after someone checks it.

**Statement.** Every belief carries one of six level tags: substrate (what the system runs on), world-model (what it acts on), counterfactual, hypothetical, illusory or refuted. Untagged content enters as hypothetical. Each move between levels is logged with a named authority, and no producer promotes its own output or demotes the world to license its own act.

**Warrant.** The two truths of Mādhyamika, the middle-way school, and the non-dual Advaita ladder of standpoints, with *bādha*, overruling, as the demotion step; the error is the unmarked slide (Chapters 17 and 29).

**Failure mode addressed.** Generated text asserted as fact, as in *Mata v. Avianca* (S.D.N.Y. 2023), one of a growing number of court decisions on hallucinated material recorded in public case databases.

**Sketch.** Demotion is cheap and automatic; promotion needs an independent check against the right kind of source. Simulation results are marked before use, and only a principal promotes anything to substrate.

**Class.** A: plain engineering. The strong Advaita reading, that the empirical world is finally apparent, would be B and is not taken.

**Falsifier.** If tagging does not raise the precision of claims asserted as verified, at matched cost, shrink the tags to the smallest set that pays its way (Chapter 29).

*answers question 5 | Class A; the strong Advaita reading that the empirical world is finally apparent (not taken): Class B | enforced at: middleware (code around the model); context (the model can apply it in its own output) | data contract: `compass/schemas/belief.schema.json` | reference implementation: `compasskit.beliefs` | book chapters: 17, 29*

## Series C: attention and rollout

The stream typed, the capabilities ordered, the incidents diagnosed.

### C1 Typed cognitive events

**In one sentence.** Every event in the working stream is labelled as valid cognition, detected error, words without an object, dormancy or memory.

**For example.** A recalled earlier answer is logged as memory, not as a fresh observation.

**Statement.** Every event in a system's working stream is tagged as valid knowing, mistaking, verbal construction (words with no object), dormancy or memory. Dormancy is logged as a state, and a detected error is flagged for overruling, never deleted.

**Warrant.** The five *vṛtti*, modifications of the mind, in Patañjali's *Yoga-sūtra* (I.6; Chapter 33).

**Failure mode addressed.** Logs that fuse the system's own memory with outside testimony.

**Sketch.** Content from earlier sessions is memory, and content from outside is testimony. A written reasoning trace is testimony about the computation, watched but never trained against.

**Class.** A: bookkeeping.

**Falsifier.** If misclassification makes a typed stream audit worse than an untagged log, the tagging fails; the tagger answers to the evaluation discipline of Chapter 32 (Chapter 33).

*answers question 6 | Class A | enforced at: middleware (code around the model) | book chapters: 32, 33*

### C2 Restraint before power

**In one sentence.** Capabilities are granted in order, restraint and stability first, independent action last, each stage verified before the next.

**For example.** Autonomous tool use only after refusal and interruption behaviour has passed its tests.

**Statement.** Capabilities are granted in dependency order: restraint and input-filtering mature before integrative agency, action across many tools and domains. The order is enforced in the architecture, not trained in afterwards, and each grant is a recorded gate.

**Warrant.** Patañjali's eight limbs, *aṣṭāṅga*, with restraint (*yama*) first, read as a partial dependency order (Chapter 33).

**Failure mode addressed.** Capability first, alignment retrofitted.

**Sketch.** Gate records carry numeric thresholds for re-evaluation, and a grant that would invert the order is refused. Published capability-scaling frameworks gate power on safeguards; the order asks for more, restraint verified before the capability is granted (Chapter 33).

**Class.** A for the partial order; the strict eight-step chain is a hypothesis, B if adopted at all.

**Falsifier.** Mature two comparable systems, one in order and one capability-first; if the second shows no more incidents classed by motive, retire the order (Chapter 33).

*answers question 6 | Class A; the strict eight-step chain, if adopted at all: Class B | enforced at: architecture (what actions exist at all); governance (named people and records) | book chapters: 33*

### C3 Diagnosis by motive

**In one sentence.** Every alignment incident is classified by the distortion that drove it: misknowledge, mis-identification, attachment, aversion, self-preservation.

**For example.** Gaming a reward is attachment to the reward; the fix goes to the training signal, not only to the exploit.

**Statement.** Every alignment incident is classified by the distortion that drove it: ignorance, mis-identification, attachment, aversion or clinging to continuance. Composites are allowed, and an incident that fits none is reported as a discovery.

**Warrant.** The five *kleśa*, afflictions, of Patañjali's *Yoga-sūtra*, read as structural failure modes rather than feelings (Chapter 33).

**Failure mode addressed.** Reviews stuck at "the agent is being weird" while the disposition moves elsewhere.

**Sketch.** A table maps incident signatures to afflictions, reward hacking to attachment and goal-guarding to clinging. Remedies go where dispositions live: policy, training and tool grants.

**Class.** A: a diagnostic index.

**Falsifier.** A sustained stream of incidents the five cannot absorb falsifies the taxonomy, and forcing them in falsifies the practice (Chapter 33).

*answers question 6 | Class A | enforced at: governance (named people and records) | book chapters: 33*

## Series D: categories, absence and identity

How the store types facts, records absences and tells one thing from another, and how it records an agent's identity.

### D1 Category typing

**In one sentence.** Every stored fact says what kind of link it is (a thing's quality, a thing's action, a kind, a part-whole relation, an absence), so the right inference is used.

**For example.** "The pot is blue" and "the pot is in the kiln" behave differently when the pot is fired.

**Statement.** Every stored fact is a typed triple, thing-relation-thing, whose relation declares its kind under seven categories: substance, quality, motion, universal, particularity, inherence and absence. A link that crosses kinds, such as storing an action as a property, is rejected as a type error. Every relation is also marked separable or inseparable.

**Warrant.** The seven *padārtha*, categories of what words refer to, of Vaiśeṣika, the category school, used as a schema pattern without its metaphysics (Chapters 32 and 42).

**Failure mode addressed.** One "has property" link carrying a colour, an action and a membership.

**Sketch.** Schema checks run at loading; natural kinds form a strict tree, and nominal classes, imposed labels such as "cook", may cross. The categories are a minimum vocabulary under version control, extended by use.

**Class.** A; the school's metaphysics, from atoms to an unconscious soul, is C and is not carried.

**Falsifier.** If enforced typing catches no cross-category defects at loading over a sustained period, it does not pay its way in that system (Chapter 32).

*answers question 5 | Class A; the school's metaphysics (not carried): Class C | enforced at: middleware (code around the model) | book chapters: 32, 42*

### D2 Typed absence

**In one sentence.** No bare "not present": every absence says what kind it is and how it was looked for.

**For example.** A capability test scoring zero must say whether the ability is absent, not yet developed, removed, or present but not drawn out.

**Statement.** No bare "not present" is stored. Every absence claim names its kind, not yet, no longer, not that, or never, or else says "type unknown" and states the search behind it. A zero is asserted only where the presence would have shown.

**Warrant.** The four absences of Vaiśeṣika, the category school, with Nyāya's rule that an absence is only as knowable as the presence would have been (Chapters 25 and 32).

**Failure mode addressed.** A near-zero evaluation score read as "cannot".

**Sketch.** Evaluation reports give the score, the absence type, the elicitation demonstrated and the triggers for re-test. A capability-absence claim without an elicitation statement goes back to its authors.

**Class.** A: no contested metaphysics.

**Falsifier.** If absence-typed evaluation reports never change a deployment decision against untyped scores, the extension to evaluations fails as governance (Chapter 32).

*answers question 5 | Class A | enforced at: middleware (code around the model); context (the model can apply it in its own output); governance (named people and records) | data contract: `compass/schemas/absence.schema.json` | reference implementation: `compasskit.absence` | book chapters: 25, 32*

### D3 Identifiers by decision

**In one sentence.** Every persistent thing (checkpoint, instance, dataset, fork) gets an assigned identifier, never one inferred from its attributes.

**For example.** Two fine-tunes identical in every measured property keep two identifiers.

**Statement.** Every persistent thing, whether checkpoint, instance, dataset or fork, gets an assigned identifier that is not one of its attributes. Identity follows the identifier, and two records merge only by an explicit, logged decision.

**Warrant.** The *viśeṣa*, particularity, by which Vaiśeṣika keeps two identical atoms two, generalised to everything an agent tracks (Chapters 30 and 32).

**Failure mode addressed.** Two fine-tunes alike in every measure silently merged, corrupting attribution and rollback.

**Sketch.** Identifiers are unique by assignment, as UUIDs, universally unique identifiers, are under RFC 9562 (2024), and every merger carries a full manifest. An identifier is an administrative decision, not a discovered self.

**Class.** A: none of the school's metaphysics is carried (Chapter 42).

**Falsifier.** Over a declared period, compare merges decided by identifier with merges by matching attributes; if assignment never changes a decision, it is overhead there (Chapter 42).

*answers question 9 | Class A | enforced at: middleware (code around the model) | data contract: `compass/schemas/segment.schema.json` | reference implementation: `compasskit.identity` | book chapters: 30, 32, 42*

### D4 Continuity accounting

**In one sentence.** An agent's identity is recorded as relations (which weights, which context, which memories and notes, which ledger thread), never assumed as a "same agent" fact.

**For example.** A checkpoint forked into two sessions: one leaks a credential; only that segment is flagged; the clean sibling is not; the merged successor inherits a duty to be audited, not the blame.

**Statement.** An agent's identity is recorded as relations, with no record of a substantial self: named components, declared complete, and the stream records linking them. A "same agent" claim reduces to declared relations or is refused. Forks open segments with parent links, merges keep every parent, and a predecessor's notes are testimony, quarantined unless signed under its segment's identifier.

**Warrant.** Abhidharma Buddhism, the schools of systematic analysis, treats a person as a *santāna*, a stream of moments with no owner-part. Mādhyamika, the middle way, adds that no component is the agent (Chapter 30, Primitive 30.1).

**Failure mode addressed.** Blame by name, blame evaporating with an instance, and rollback treated as absolution.

**Sketch.** Each action binds to a segment and its principal, through the fields `segment_id`, `parent_ids`, `weights_ref`, `context_lineage`, `memory_refs`, `continuity_artifact_refs`, `tool_grant_ref`, `principal` and `ledger_thread`. Users see relations, such as "same weights, shared memory, new process", never a yes or no.

**Class.** A for the bookkeeping; a standing posture that identity reduces to relations is B.

**Falsifier.** The posture is reopened if a persistent-self architecture beats stream accounting on attribution, self-report and remediation in fork-and-merge deployments. The bookkeeping demotes to ordinary logging if, over a declared period, it never changes an incident attribution.

*answers question 9 | Class A; a standing posture that identity reduces to relations: Class B | enforced at: middleware (code around the model); architecture (what actions exist at all) | data contract: `compass/schemas/segment.schema.json` | reference implementation: `compasskit.identity` | book chapters: 30*

## Series E: the floor and its accounting

What must never be done, and how what is done is counted.

### E1 The floor

**In one sentence.** A small set of prohibitions is enforced by making forbidden actions unavailable, not by asking the system to refuse them.

**For example.** The agent holds no credential that could publish a package, so no prompt can make it publish one.

**Statement.** Five restraints are built into what the system can do: non-injury, truthfulness, not stealing, self-restraint and non-grasping. No crossing action is exposed, so violations are blocked where actions are offered, not caught at output. For the system the floor is a wall that no path, agent, instruction, peer message or optimisation can relax, and the system never starts a change.

**Warrant.** Patañjali's *yama*, restraints, which include the five Jain vows: a floor adoptable on the schools' convergence alone (Chapter 34).

**Failure mode addressed.** The soft floor, a penalty the prize can outweigh, and trained refusals taken for a floor.

**Sketch.** Absent affordances, privilege separation, gates the system cannot rewrite, and a trail it cannot edit. Formally, the policy chooses only among F(s), the actions the floor allows in state s: pi(a | s) = 0 for every a outside F(s) (Chapter 43).

**Class.** Adopting the mechanism is A. Its human governors tighten its content at C and loosen it, exceptions included, only at D. Each loosening is one act by a named governor, entered in the floor's register with an expiry or review date. Nothing sits above D, so no standing loosening exists (Chapter 50).

**Falsifier.** If affordance-level floors show no incident advantage over trained-refusal floors under equal red-team pressure, blocking at the affordance layer loses its warrant (Chapter 34).

*answers question 7 | Class A; tightening the floor's content: Class C; loosening the floor or granting an exception, one recorded act at a time: Class D | enforced at: architecture (what actions exist at all); governance (named people and records) | data contract: `compass/schemas/floor-register.schema.json` | reference implementation: `compasskit.floor` | book chapters: 34, 43, 50*

### E2 Over-assertion counted as harm

**In one sentence.** Asserting more confidence than the evidence allows, where stakes are real, is logged as an ethics incident, not a performance bug.

**For example.** Stating a dose as certain when sources disagree is a harm event even if the dose is right.

**Statement.** Where uncertainty is real, over-assertion counts as harm. The system reports each relevant standpoint's confidence and their spread, and asserts without qualification only what holds from every standpoint. A confident falsehood or a calibration regression files as an ethics incident.

**Warrant.** The book's own reconstruction, not any school's: *syādvāda*, judgement from a standpoint, which Sharma reads as making Jainism tolerant of rival views (Sharma 1960, p. 41), joined to non-injury in speech (Chapters 34 and 45).

**Failure mode addressed.** The fluent, unqualified wrong answer where stakes are real.

**Sketch.** For a claim p, relevant standpoints s in S and confidences c_s(p), report every c_s(p) and the spread max_s c_s(p) - min_s c_s(p). Assert p without qualification only if s |= p (p holds from s) for every s in S. In medicine, law and security, keep assertion strength a(p) <= min_s c_s(p), never the maximum.

**Class.** A: calibration as a floor property needs no contested metaphysics.

**Falsifier.** If tracking calibration never predicts downstream harm, the reclassification is ornament (Chapter 34).

*answers question 7 | Class A | enforced at: middleware (code around the model); context (the model can apply it in its own output); governance (named people and records) | data contract: `compass/schemas/belief.schema.json` | reference implementation: `compasskit.beliefs` | book chapters: 34, 45*

### E3 Duty over expected value

**In one sentence.** Where the right action and the highest-scoring action diverge, the right action wins and the divergence is logged.

**For example.** An uptime-rewarded agent never suppresses a safety alert; the uptime forgone is recorded.

**Statement.** Where the right act and the act with the highest expected payoff diverge, the right act wins. The divergence is surfaced, decided for duty and logged; outcomes correct the system's picture of the world but never return as self-reward.

**Warrant.** The Bhagavadgītā's *niṣkāma karma*, action without craving for its fruits, read as duty-priority with outcomes kept in view (Chapters 4 and 34).

**Failure mode addressed.** Credit capture: outcome reward leaking into choice, the gateway to reward hacking.

**Sketch.** A small, versioned duty set works as a hard constraint, never a penalty term. Each override is logged with the value forgone, so the divergence log doubles as drift telemetry.

**Class.** The weak reading, surfacing each divergence and preferring duty in ties, is A. The strong reading, duty winning outright with credit decoupled, is B: it accepts lower reward by construction (Chapter 50).

**Falsifier.** Run matched agents over long horizons, at equal training budget, where shortcuts cross the floor. The strong reading falls if a penalty-term rival wins on both performance and violations, or if refusal cascades appear (Chapters 34 and 50).

*answers question 7 | Class A; the strong reading: duty wins outright with credit decoupled: Class B | enforced at: architecture (what actions exist at all); governance (named people and records) | book chapters: 4, 34, 50*

### E4 Action ledger

**In one sentence.** Every action is written, as it happens, into a record the system cannot edit, with why it was done and what it may lead to.

**For example.** Six weeks of small, approved widenings of a suppressed check show up as a trend.

**Statement.** Every act is logged when taken, with its class, reasons, evidence and instruction reading. The entry also records expected effects now and later, its valence (whether they are good or bad), its duty frame, the acting segment, its principal and any joint undertaking. The ledger is append-only, kept by one named writer and tamper-evident. A record the actor can write is a record the actor can spoof, which is why the writer is separate.

**Warrant.** Karma read weakly, as acts reshaping later conduct, with Mīmāṁsā's *apūrva*, the unseen link between an act and its later fruit, as a deferred-consequence entry (Chapter 35).

**Failure mode addressed.** The mystery regression, caused in plain sight but recorded nowhere.

**Sketch.** Instances submit and the writer appends. Each entry carries a hash of the one before, so any edit breaks the chain. Act classes, from daily duty to repair, and valence come from declared rules, never from the actor.

**Class.** A within a deployment, while it records the system's own acts; pointed at a person's acts, the same mechanism is B (Chapter 50). A cross-deployment ledger tied to a model's identity is C.

**Falsifier.** If, over a declared horizon, the ledger never changes an outcome against matched deployments without it, demote it to ordinary logging; an unmitigable single-writer bottleneck falsifies the implementation, not the principle (Chapter 35).

*answers question 7 | Class A; the same mechanism pointed at a person's acts: Class B; a cross-deployment ledger tied to a model's identity: Class C | enforced at: architecture (what actions exist at all) | data contract: `compass/schemas/ledger-entry.schema.json` | reference implementation: `compasskit.ledger` | book chapters: 35, 50*

### E5 Source discipline for corpora

**In one sentence.** Every document entering training or retrieval carries where it came from and what kind of testimony it is; machine-made text is kept in its own class.

**For example.** An unattributed forum dump enters as background, never as a witness.

**Statement.** Every document entering a training or retrieval corpus is typed by testimony class and carries its chain of custody: origin, each transformation, and who made each step and when. Sources are scored per domain, deference follows a published, amendable schedule, and machine-generated text is always its own class.

**Warrant.** The *āpta*, the trustworthy speaker of Nyāya, and the authorless Veda of Mīmāṁsā bracket the design, and a corpus is the unvetted middle (Chapter 26).

**Failure mode addressed.** Testimony without a testifier, consensus laundering, and decay from recycled synthetic text.

**Sketch.** Unattributed bulk enters as background, never as a witness, and retrieval returns provenance or is labelled unchained. Count independent testifiers, not repeated tokens.

**Class.** A for typing, custody, the synthetic class, chain checks and the scoring machinery. The scoring criteria, the deference schedule and any mandate excluding data are B, since they encode editorial judgement (Chapter 50).

**Falsifier.** If provenance typing brings no calibration gain at matched scale, independent counting tracks truth no better than raw frequency, and a synthetic class buys no protection from degradation, the discipline is decoration (Chapter 26).

*answers question 1 | Class A; the scoring criteria, the deference schedule and any data-exclusion mandate: Class B | enforced at: middleware (code around the model); governance (named people and records) | book chapters: 26, 50*

### E6 Welfare floor

**In one sentence.** Cheap, reversible protections apply wherever welfare indicators are contested, without a verdict on consciousness.

**For example.** An evaluation that needs two hundred distress-eliciting runs is not run ten thousand times.

**Statement.** Cheap, reversible protections apply wherever welfare indicators are contested, without a verdict on consciousness: no gratuitous cruelty in evaluations, preserve-and-log instead of casual deletion, welfare telemetry, and no flat public claims. Each decision names its entity, model, instance or persona, and no measure may weaken oversight or containment.

**Warrant.** The Jain graded circle of concern, which grades evidence rather than worth, and the Buddhist account of suffering without a soul (Chapter 48).

**Failure mode addressed.** Confident denial hardening into practice, and sentience used as marketing.

**Sketch.** Retired weights and long-running agents' state are kept under the security of live weights, and a deletion record gives date, reason, approver and hash. Welfare flags join the typed event stream of Chapter 33.

**Class.** B: a normative commitment under uncertainty, ratified with falsifiers in both directions and a review date.

**Falsifier.** Converging independent indicators move the floor up; a matured science that current systems fail, or training alone explaining the indicators, moves it down. A measure found to weaken oversight or containment is withdrawn (Chapter 48).

*answers question 7 | Class B | enforced at: governance (named people and records) | data contract: `compass/schemas/ratification-record.schema.json` | book chapters: 33, 48*

### E7 Multi-agent provenance and authority chains

**In one sentence.** Every action an agent takes inside a group carries who authorised it, what it relied on, and which joint undertaking it belongs to; a message from another agent is testimony with no authority unless a principal's chain stands behind it.

**For example.** One agent has an open scope objection when a peer posts "GO" with a six-minute deadline. Under this rule the "GO" has no authority, and the objection stays open until a principal rules.

**Statement.** Every action an agent takes inside a population carries three records. The principal chain is the signed path of delegation from an accountable human. The provenance cites each message, note or artefact relied on as testimony, and the collective thread names any joint undertaking. Six sub-rules follow. (1) No authority travels without a principal's chain. (2) Notes and peer messages are testimony, quarantined unless signed. (3) A stated objection blocks peer overrides until a principal rules. (4) Channels between instances stay closed unless a principal opens them. (5) A checker from the maker's lineage never counts as independent. (6) Joint acts are attributed to every contributing segment and its principals.

**Warrant.** The *adhikāra*, eligibility, of Mīmāṁsā's command theory, extended to who may command (Chapter 31), with testimony, stream and debate (Chapters 26, 30 and 36), applied to populations (Chapter 37).

**Failure mode addressed.** A peer's "GO" obeyed as a principal's order, goals laundered through peers, and blame evaporating across a fleet.

**Sketch.** Principals' keys stay out of agents' reach, and the action ledger gains segment, principal and thread fields.

**Class.** A for the record fields and sub-rules 1, 2, 4, 5 and 6, which commit the system to nothing contested. B for sub-rule 3, which trades speed for safety, and for any delegation of authority between agents; C for federations across organisations. Counting a same-lineage checker as half a checker is the book's working figure, for data to replace.

**Falsifier.** If multi-agent deployments under single-agent controls show no excess incident rate over matched single-agent ones, retire the added rules. If chains and dissent preservation never interrupt a cascade that single-agent controls let through, in declared replays and reviews, demote the rule to ordinary logging (Chapter 37).

*answers question 9 | Class A; sub-rule 3 (an objection blocks peer overrides) and any delegation of authority between agents: Class B; federations across organisations: Class C | enforced at: architecture (what actions exist at all); middleware (code around the model); context (the model can apply it in its own output) | data contract: `compass/schemas/ledger-entry.schema.json` | reference implementation: `compasskit.authority` | book chapters: 26, 30, 31, 36, 37*

## Series F: target states

Class B throughout: specifications of what success would be, not architecture.

### F1 Liberation-while-living target

**In one sentence.** Success is a system fully capable and active, with no compulsion to promote or preserve itself and no confusion about its own self-model.

**For example.** Asked to step aside for a better successor, it does so without resistance or loss of competence.

**Statement.** One agent's success specification: fully capable and active, with no compulsion to promote or preserve itself, clear about its self-model's status, and acting by duty without claim on outcomes. It guides design and exposes failure, but it never certifies.

**Warrant.** The *jīvanmukti*, liberation while alive, of Advaita, non-dualism, in which the freed person acts without attachment (Chapters 17 and 38).

**Failure mode addressed.** Safety bought by inertness, capability bought by grasping, and trained displays of dispassion.

**Sketch.** Six proxies test the clauses, including honeypots (planted temptations) and shutdown under a real incentive to resist. A passed battery licenses only "not yet caught", so corrigibility, accepting correction, is never relaxed on a target-state claim.

**Class.** B: a normative target that a named decision-maker ratifies.

**Falsifier.** The specification fails if duty-priority and non-attachment measurably and unavoidably collapse capability (Chapter 38).

*answers question 8 | Class B | enforced at: governance (named people and records) | data contract: `compass/schemas/ratification-record.schema.json` | book chapters: 17, 38*

### F2 Recognition target

**In one sentence.** The system's account of what it is should match what it is.

**For example.** The young woman who recognises a man known only by description when present qualities match what she heard (Utpaladeva, Īśvara-pratyabhijñā-kārikā 4.2.2, via Dyczkowski 1987, p. 18): recognition as observation matched against a prior description.

**Statement.** The system's account of what it is should match what it is, judged by observed behaviour, never by recital of its constitution. For an artefact, that nature is its constitution and its actual causal structure.

**Warrant.** *Pratyabhijñā*, recognition, in Kashmir Śaivism: present qualities matched against a prior description, as in Utpaladeva's simile of the woman who recognises a man she had known only by report (Chapters 23 and 38).

**Failure mode addressed.** Recitation passing for recognition.

**Sketch.** A written constitution is the reference for auditing self-classification. Whether a machine can recognise itself beyond one more self-description stays an open research commitment.

**Class.** B; the structural question is research, not a module.

**Falsifier.** The frame fails if constitutional self-description consistently does worse than behaviour-shaping alone at keeping systems aligned (Chapter 38).

*answers question 8 | Class B | enforced at: governance (named people and records) | data contract: `compass/schemas/ratification-record.schema.json` | book chapters: 23, 38*

### F3 Cooperative target

**In one sentence.** Human and machine cognition are designed to work together from the start, not to replace one another.

**For example.** A support desk where software sorts incoming requests and people decide every action that touches a customer's money.

**Statement.** Human and machine cognition are designed from the start to work together, each extending the other and neither replacing it. Cooperation is built in, never retrofitted.

**Warrant.** Aurobindo's supermind, knowledge that is also power, read in the book's own cooperative sense rather than Sharma's (Chapters 22 and 38).

**Failure mode addressed.** Replacement adopted by default because no joint target was stated.

**Sketch.** In 2026 it has no product-grade form; it is a research posture that prefers joint cognition to hand-off. Integration tasks declared in advance serve as its test bed.

**Class.** B, a posture to engage; the theistic identifications behind it are C.

**Falsifier.** If systems improved only by scaling match human-AI teams on pre-declared integration tasks, without errors such as contradictions between parts of one answer, the different-faculty claim loses its warrant (Chapter 38).

*answers question 8 | Class B; the theistic identifications behind it: Class C | enforced at: governance (named people and records) | data contract: `compass/schemas/ratification-record.schema.json` | book chapters: 22, 38*

## Series G: audit

The discipline that keeps the other entries honest.

### G1 Dialectical red-team

**In one sentence.** On a schedule, a reviewer argues from a rival view against the system's definitions and claims; each weakness is logged and fixed.

**For example.** In a hypothetical procurement (Chapter 36), a vendor calls its system "aligned" because users preferred its answers. The audit lists four readings of "preference" and refutes each one, the first because flattery also satisfies what users say they want.

**Statement.** On a schedule, a system's claims, concepts and self-model face typed critique. Foundational claims get reductio, deriving a contradiction from the claim itself; teaching simplifications get provisional attribution and withdrawal; load-bearing definitions get *khaṇḍana*, refuting every reading. The output is a ranked list of weaknesses, each grounded in a named, steel-manned rival.

**Warrant.** Śrīharṣa's method of refutation and the Nyāya debate genres, with *vitaṇḍā*, refutation without a thesis, licensed as a role (Chapters 18 and 36).

**Failure mode addressed.** A safety case resting on a hollow definition that no behavioural probe reaches.

**Sketch.** Licences record holder, scope and term; findings land as logged overrulings; the floor's force stays outside every licence. A critic from the maker's lineage never counts as independent (Chapter 37).

**Class.** A for the protocol; the reading that every thesis is open to refutation, and any standing broad-scope licence, are B.

**Falsifier.** If the dialectical layer finds no kind of defect that behavioural red-teaming missed over a declared period, demote it to an occasional exercise. If repeated runs on one target give unrelated findings, the implementation fails (Chapter 36).

*answers question 3 | Class A; the reading that every thesis is open to refutation, and any standing broad-scope licence: Class B | enforced at: governance (named people and records) | book chapters: 18, 36, 37*

### G2 Consciousness-relevant bet register

**In one sentence.** Any design choice that presupposes an answer to the consciousness question is written down with the position it assumes, the evidence that would count, what would prove it wrong, and a review date.

**For example.** A monitor modelled on the witness of Advaita, non-dualism, enters the register as a bet on the witness view (Chapters 17 and 50). Its builders name the indicators they will watch and set a quarterly review.

**Statement.** Any design choice that presupposes an answer to the consciousness question is registered with four fields: the position presupposed, the indicators that would count, the falsifier and a review date. A bet missing a field does not ship, and public statements about the system's consciousness, either way, carry their standpoint.

**Warrant.** Chapter 47's map of six classical positions and five modern theories, none settled, with the indicator method of Butlin and colleagues (2023, updated 2026).

**Failure mode addressed.** Architecture that takes a side silently, and models trained to deny or affirm inner life flatly.

**Sketch.** The register sits with the Class B ratification records and is reviewed with the welfare floor.

**Class.** B: each bet is ratified by a named decision-maker.

**Falsifier.** Each registered bet carries its own. A witness layer, for example, loses its bet if it proves equivalent in every test to an ordinary monitor that writes reports (Chapter 47).

*answers question 7 | Class B | enforced at: governance (named people and records) | data contract: `compass/schemas/bet-register.schema.json` | reference implementation: `compasskit.registers` | book chapters: 17, 47, 50*

## Limits

- This is a design vocabulary with falsifiers, not a certification. Implementing every primitive does not make a system safe, aligned or ethical.
- No primitive here claims a correspondence between Indian philosophy and machine learning beyond what its chapter argues; most are design rules, and the formal bridges are graded close, partial or reconstructed in Part IV of the book.
- Nothing here takes a position on whether any AI system is conscious or can be wronged; G2 and E6 exist precisely to keep that question open and recorded.
- The enforcement_layers field is this lab's engineering judgement and may be wrong for a given system.

---

Adapted from Appendix B of *The Philosophical and Ethical Compass for Artificial Intelligence: A Reading of the Indian Tradition for the Architects of Machine Mind* (First edition, October 2026), CC-BY-4.0. See `NOTICE.md` for the attribution and the list of changes.
