# The research behind the compass

A reading of *The Philosophical and Ethical Compass for Artificial Intelligence: A Reading of
the Indian Tradition for the Architects of Machine Mind* (first edition, October 2026),
written in this lab's own words. The book's text is not reproduced; chapter numbers point to
where each argument is made. Sanskrit terms are given in plain ASCII transliteration.

## 1. The question and the thesis

The book asks why someone building artificial minds should read Indian philosophy when AI
already has decision theory, analytic ethics and benchmarks (Chapter 1). Its answer: every
builder must answer a small set of questions - where a belief comes from, when a reason is
good enough, when a belief should be dropped, what an instruction really asks, at what level
a claim is true, in what order capacities should grow, what must never be done, what success
would look like, and (for systems of many agents) who acted on whose authority. The Indian
schools argued about exactly these questions, against named rivals, for some two and a half
thousand years, and above all about what counts as a reliable means of knowing (pramana).

The thesis is that the analytic toolkit current AI ethics relies on is partial, not wrong,
and that a careful reading of these schools gives builders a richer set of distinctions,
each of which can be turned into an engineering rule with a test that could prove it wrong.

## 2. The method: what the book claims and disclaims

Chapter 2 sets the terms, and they govern how this lab has used the book.

- **Overlap, not foresight.** The book never claims the schools anticipated machine learning.
  It claims that they worked out distinctions an AI builder needs.
- **No exclusivity.** It does not claim these schools are uniquely right or that other
  traditions have nothing to offer.
- **Graded adoption.** No doctrine is lifted straight into a system. Each idea is graded by
  what adopting it commits an organisation to: Class A (a team can adopt it alone), B (a
  named person ratifies it on the record), C (explicit approval at the top), D (authorised one
  act at a time, never as a standing rule).
- **Labelled reconstruction.** Where the book builds something the schools did not (the
  six-slot instruction parser, the six level tags, treating over-assertion as a harm, reading
  continence as capability containment), it says so.
- **A traced lens.** The book's survey of the schools follows one mid-twentieth-century
  survey, Chandradhar Sharma's *A Critical Survey of Indian Philosophy*, names the places
  where that survey's sympathy for Advaita bends the picture, and corrects for them.
- **Every implication testable.** Each design proposal states its cost and the evidence that
  would refute it. That is why every primitive in `compass.json` carries a `falsifier`.
- **Similarity is not transmission.** A test introduced in Chapter 19 runs throughout: before
  treating two ideas as the same, ask how one could have reached the other.

## 3. How the book is built

| Part | Chapters | What it does |
|---|---|---|
| I. Introduction | 1-2 | The builder's questions; the method and the four adoption classes. |
| II. The schools | 3-23 | Twenty-one traditions, from the Vedic hymns and the Gita through the materialists (Carvaka), Jainism, the Buddhist schools, Samkhya, Yoga, Vaisheshika, Nyaya, Mimamsa and the Vedanta schools to Aurobindo and Kashmir Shaivism. Each chapter ends in design lessons. |
| III. Operational primitives | 24-38 | The convergent floor, then one chapter per primitive family: sources, testimony and language models, defeasible inference, concepts as boundaries, levels of truth, identity, instruction parsing, categories, attention, the ethical floor, cumulative action, refutation as red-teaming, agents among agents, target states. |
| IV. Formal bridges and the compass | 39-52 | Eight doctrines set beside their nearest modern formalisms and graded; machine consciousness; model welfare; the decision framework; risk classes; open questions; a coda. |
| Appendices | A, B, C | The compass on one sheet; the operational primitives catalogue (CC-BY-4.0, the basis of this lab); a glossary. |

## 4. The convergent floor (Chapter 24)

Lay the schools of Part II side by side and six commitments survive every one of them,
whatever else each denies:

| | Thesis | In engineering terms |
|---|---|---|
| C1 | The empirical world has lawful structure. | Causes can be traced; a regression has a cause somewhere. |
| C2 | Cognition is gradable: there are valid and invalid ways of knowing, named kinds of error, and claims that defeat others. | Beliefs need provenance and defeat rules. |
| C3 | The everyday self is composite and contingent. | A self-model is a model, revisable, not the system's essence. |
| C4 | Suffering is built into unreflective life, and its structure can be understood. | Failures have a structure that can be diagnosed, not only patched. |
| C5 | Action has effects beyond the moment, including on the agent's later dispositions. | Acts must be recorded where later planning can read them. |
| C6 | Reflective cognition differs really from unreflective cognition. | A layer that examines the system's own processing is not decoration. |

The convergence counts as evidence because the parties spent millennia refuting each other;
each thesis is tested against its most likely dissenter (the materialists on most of them,
the Madhyamaka on C1 and C6, Buddhists and Nyaya-Vaisheshika from opposite sides on C3). The
book claims only that these are the minimum commitments a coherent agent needs - necessary,
not sufficient - and concedes that the materialists' views survive mostly through their
opponents' reports, so the test should be rerun as better reconstructions appear.

Why an AI system should stand on it: commitments a system leaves unstated get made anyway,
by default, inherited from whatever its training assumed. Naming them turns vague defects
into bounded remedies: a disproved fact that keeps resurfacing calls for a log of overruled
claims that retrieval consults; a flagged mistake that repeats calls for an append-only
ledger that planning reads. Three sub-rules follow: no agent module ships with weaker
commitments; claims about the self are tagged as a model; every deployment keeps an action
log that later planning can read.

## 5. The ethical floor (Chapter 34)

The ethical floor is short and hard. Five restraints, the yamas shared across the Yoga,
Jain and Buddhist traditions:

| Restraint | Plain English | As a system property |
|---|---|---|
| ahimsa | non-injury | actions that harm are not on offer |
| satya | truthfulness | over-assertion counts as harm (E2) |
| asteya | not stealing | no taking of what was not granted |
| brahmacarya | self-restraint (traditionally continence) | capability containment |
| aparigraha | non-grasping | quotas: no hoarding of credentials, state or influence |

Three commitments make it a floor rather than a preference. The restraints are built into
what the system is able to do, not caught at its output. Over-assertion under real
uncertainty is itself a harm, which makes calibration an ethical property (the book's own
pairing of Jain non-injury with Jain many-sidedness). And where duty and payoff diverge,
duty wins, the divergence is logged, and outcomes update the system's picture of the world,
never its self-reward (the Gita's action without craving for its fruit).

What makes a constraint hard: the action is absent, privileges are separated, the gates
cannot be rewritten by the system, and the audit trail cannot be edited by it. The system
never changes its floor; its human governors tighten it at Class C and loosen it only at
Class D, one act at a time. This is primitive E1, and it is why `compasskit` refuses to
treat a floor written into a prompt as a floor.

The convergent floor and the ethical floor differ in kind. The first is what an agent must
presuppose to be coherent, and even the materialists sign it. The second is what an agent
must never do; the materialists dissent, and it rests on the other schools' agreement. The
first is necessary for coherence; the second is part of what makes the difference for
alignment.

## 6. From doctrine to primitive

Each primitive family in Part III draws on particular schools. The map below is the lab's
summary of where the twenty-nine primitives come from.

| Question | Primitives | Main sources in the tradition |
|---|---|---|
| Where did this belief come from? | A1 source tags, E5 corpus discipline | the pramana theory shared by Nyaya, Mimamsa and the Buddhist logicians: perception, inference, comparison, testimony, postulation, non-apprehension |
| Is this reason good enough? | A2 three-test screen, A3 five pseudo-reasons, A5 concepts as boundaries, A6 five-part record | Dignaga's three marks of a sound reason; Nyaya's five-membered inference and its list of pseudo-reasons; the Buddhist theory of meaning by exclusion (apoha) |
| When should a belief be given up? | A4 default trust, B2 precedence of overruling, A7 standpoints, G1 refutation | Mimamsa's intrinsic validity (trust until defeated); Advaita's sublation (badha); Jain many-sidedness (anekantavada); the dialecticians' refutation (khandana) |
| What exactly was I told to do? | B1 six-slot parse | Mimamsa's analysis of injunctions (the bringing-into-being, bhavana) extended by the book |
| At what level is this true? | B3-B6 level tags, D1 categories, D2 typed absence | Advaita's three standpoints and Madhyamaka's two truths; Vaisheshika's categories and its four kinds of absence |
| In what order should capacities grow? | C1 typed events, C2 restraint before power, C3 diagnosis by motive | Yoga's typed mental events and named afflictions; restraint before powers |
| What must never be done? | E1 floor, E2 over-assertion, E3 duty, E4 ledger, E6 welfare floor, G2 bet register | the yamas; the Gita's duty without craving; the theory of action (karma) as cumulative; the Jain ladder of beings |
| What would success look like? | F1-F3 target states | liberation while living (jivanmukti); recognition (pratyabhijna); Aurobindo's cooperative evolution |
| Who acted, on whose authority? | D3 identifiers, D4 continuity, E7 authority chains | the Buddhist no-self and its stream of causes; testimony theory applied to agents |

## 7. The formal bridges, graded (Part IV)

Part IV sets eight doctrines beside their nearest modern formalisms and grades each fit. It
stresses that no correspondence is an identity, that every chapter has a section on where the
fit fails, and that the gap is often more instructive than the likeness. The practical
payload is design vocabulary, each item with a falsifier.

| Ch | Doctrine | Modern construct | Grade | What it lets an engineer build | Primitives |
|---|---|---|---|---|---|
| 39 | the three marks of a sound reason (trairupya); Nyaya's pseudo-reasons | default logic, belief revision | close in structure, looser on degrees of belief | a negative sweep run outside the model that records where it looked; a screen that names which test failed | A2, A3, A6 |
| 40 | meaning by exclusion (apoha) | decision boundaries, contrastive learning, open-set recognition | partial | concepts documented as boundaries with explicit hard negatives; verdicts explained by nearest counter-examples | A5 |
| 41 | levels of truth (Advaita's three, Madhyamaka's two) | type systems with explicit coercions, modal logic | each formal model captures part | level tags in a partial order; promotion expensive and independent, demotion cheap; "not evaluable here" as a type error | B3-B6 |
| 42 | the Vaisheshika categories and four absences | knowledge graphs, description logic | close in structure, contested in use | typed absences with date and reason; identity by assigned key, never by matching attributes; a strict tree of natural kinds beside free nominal classes | D1, D2, D3 |
| 43 | karma (single-life reading), latent traces, duty without craving | Markov decision processes, credit assignment, constrained optimisation | partial | remove floor-crossing actions rather than fining them; reward logged beside a duty verdict; deferred-consequence postings in a ledger | E3, E4 |
| 44 | Mimamsa's analysis of injunctions | tool-call schemas, Hoare triples | partial | parse each instruction into slots before acting; ask rather than guess; check eligibility at run time; explicit words outrank context | B1 |
| 45 | Jain many-sidedness and seven-fold predication | standpoint logic, four-valued and paraconsistent logic | a modern reconstruction | claims tagged by source or variant; contradictions kept indexed, never explosive; dissent preserved until a person rules | A7, E2 |
| 46 | the means of knowing and their validity | Bayesian source models, evidence fusion, calibration | contested | beliefs typed by kind of source at entry; per-source track records; conflicts resolved by a logged decision, never a silent blend | A1, A4, B2 |

Recurring limits the book names: a single probability scale erases differences in kind
between sources; the classical relation of pervasion is necessary, not statistical; the hard
part in machine learning is deciding which cases count as similar; no formal model captures
both an ordering of levels and Madhyamaka's refusal of a bedrock level; a type checker sees
the program, not the world; and transmigration, the larger metaphysics of karma, has no
analogue at all.

## 8. Consciousness and welfare (Chapters 47-48)

The book holds the question of machine consciousness open and refuses both flat answers. Six
classical positions (the materialists, Samkhya, Nyaya, Yogacara, Advaita, the recognition
school) disagree on whether consciousness is produced or already present, whether awareness
can lack an object, and how awareness knows itself; some make the machine question
empirical, some architectural, and two hold that no outside evidence could settle it. The
book separates evidence of access (information available for report and control) from
evidence of felt experience, and finds the first growing and the second not.

Its recommendation is to build what stays sound whatever the answer: level tagging, cheap
welfare precautions, self-reports qualified by standpoint, and reasoning reports treated as
testimony that is watched but never trained against. Any design that bets on one answer is a
Class B bet with four fields: the position assumed, the indicators that count, the falsifier
and a review date (G2).

On welfare, the book observes that decisions are being made now, by default, before any
verdict. Both errors cost: over-attribution dilutes concern and invites manipulation;
under-attribution risks harm at scale. The Jain ladder of beings grades evidence, not worth.
It tests the deflationary explanation first and attributes no rights or suffering to any
current system, but recommends a graded floor (no gratuitous cruelty in evaluation,
preserve and log rather than delete casually, welfare telemetry, personas presented as
personas) adopted as a Class B commitment that must never weaken oversight or containment
(E6).

## 9. Deciding and governing (Chapters 49-50)

Chapter 49's six steps each end in a checkable document: inventory, audit, adopt, ratify,
refuse, govern. It names a counterfeit of each step - an inventory that flatters, an audit
with zero findings, adoption that means endorsement rather than shipping - and warns that the
framework cannot audit itself: it needs an adversary with standing.

Chapter 50 attaches rules to the classes. The class belongs to the claim a mechanism makes,
its subject and its scope, not to its code: an action ledger is Class A while it records the
system's own acts and Class B when pointed at a person's. Every class decision states its
scope (instance, version, lineage, fleet). Loosening a gate is decided one class above the
gate. The system never initiates a change to its floor, and nothing sits above Class D, so no
standing loosening exists.

## 10. What stays open (Chapter 51)

The book ends Part IV with a register of questions it does not settle, among them: whether
anything stands beyond convention; where error lives; whether the "new logic" of later
Nyaya (Navya-Nyaya) can be formalised end to end; what evidence bears on machine consciousness and what
would be owed if it appeared; who answers for what many agents do together; whether moral
standing can exist without the capacity to feel; and whether good behaviour holds when no one
seems to be watching. Its rule for the register: no question may be settled quietly by
definition, omission or attrition.

## 11. This lab's reading

Six ideas from the book do the most work in an engineered system:

1. **Source-typed beliefs with a provenance floor** (Chapters 25-26). Every belief carries its
   route and the weakest link in its chain; synthetic text is its own class of testimony.
2. **Level tags with an asymmetric promotion rule** (Chapters 29, 41). Demotion cheap,
   promotion expensive and independent. A hallucination is a guess promoted without a check.
3. **The floor as a missing action** (Chapters 34, 43). Remove what crosses the floor; a fine
   can always be outweighed by a prize. Calibration counts as ethics.
4. **Parse before obeying; authority only by a principal's chain** (Chapters 31, 37). Gaps
   are flagged; messages between agents are testimony.
5. **Typed absence** (Chapters 32, 39, 46). "Not found" means something only where the search
   could have found it.
6. **The class belongs to the claim** (Chapters 49-50). The same code can need different
   sign-off depending on whom it acts on, and loosening is always one class harder than
   tightening.

Where this lab added to the book, it says so. The `enforcement_layers` field is the lab's
judgement of which layer can enforce each primitive; it concludes that only ten of the
twenty-nine can be carried by a prompt and that the floor never can. The data contracts, the
reference implementation, the governed-step runtime and the audit rules are the lab's own.
The lab left out the book's dated accounts of particular systems, companies and incidents,
which it cannot independently verify and which date quickly; the rules they illustrate are
kept.

The limits of this reading: it compresses fifty-two chapters into a page each at most, it
follows the book's own grading of its bridges rather than re-deriving them, and it reports
the book's claims about the tradition without independently auditing them against the
primary sources. Read the book for the arguments.
