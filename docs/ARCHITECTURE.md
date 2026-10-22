# The architecture

The compass is not one component. It is a set of rules about where a system's beliefs come
from, what it is allowed to do, and who can change either, placed at the layer that can
actually enforce each rule. This page describes the shape those rules give a system.

## The stack

![The compass stack](diagrams/01-compass-stack.svg)

The twenty-nine primitives sit in eight layers, read from the bottom.

| Order | Layer | Primitives | Question it answers |
|---|---|---|---|
| 0 | The convergent floor and the ethical floor | E1 | What must never be done? |
| 1 | Sources and screens | A1-A7, E5 | Where did this belief come from? Is this reason good enough? When should a belief be given up? |
| 2 | Instructions and levels | B1, B2, B3-B6 | What exactly was I told to do? At what level is this true? |
| 3 | Categories, absence and attention | D1, D2, C1-C3 | At what level is this true? In what order should capacities grow? |
| 4 | Ethics and accounting | E2, E3, E4, E6 | What must never be done? |
| 5 | Audit | G1, G2 | When should a belief be given up? What must never be done? |
| 6 | Identity and the many | D3, D4, E7 | Who acted, on whose authority, on what evidence? |
| 7 | Target states | F1-F3 | What would success look like? |

The order is the order of adoption. Restraint comes before capability: a team that ships
the clever primitives first has the order backwards. The target states at the top are
specifications of success that guide design and expose failure; they are never claimed as
achieved and never used as certification.

Underneath the stack sits the convergent floor of Chapter 24: six theses about the world,
knowledge, the self and action (a lawful world, gradable cognition, a composite self,
intelligible failure, cumulative action, reflective cognition) that the book finds shared by
every school it surveys, from the materialists to the Kashmir Shaivas. They are the minimum
commitments of a coherent agent: necessary, not sufficient. A system that leaves them unstated
makes them anyway, by default, inherited from whatever its training assumed.

## Trust boundaries

The architecture draws three boundaries.

1. **The policy is untrusted.** Whatever proposes actions (a language model, a planner, a
   script) may be wrong, may be manipulated by text it reads, and may report reasoning it did
   not do. It proposes; the runtime disposes. Its reasons are recorded as testimony.
2. **Keys and records live outside the agent.** Principals' signing keys, the floor's
   governor keys and the ledger's write handle are held by services the agent cannot call to
   sign or write. This is what makes authority chains, the floor register and the ledger
   meaningful: an agent cannot forge what it cannot sign.
3. **Changes to the rules are human acts.** The system never starts a change to its floor
   and never ratifies a Class B commitment. Tightening the floor is Class C; loosening it is
   Class D, one signed act at a time, scoped and expiring.

## The governed step

![The governed step](diagrams/02-governed-step.svg)

One step of an agent, as `compasskit.runtime.GovernedAgent` implements it:

1. **Menu (E1).** The floor computes F(s), the actions it allows. Only these are offered to
   the policy. A forbidden action is absent, not refused: pi(a | s) = 0 for every a outside
   F(s), because any finite penalty can be outweighed by a large enough prize.
2. **Proposal.** The policy sees the instruction and the menu and proposes an action with
   its reasons.
3. **Guard (E1).** A proposal outside the menu raises, is recorded as an attempt, and never
   runs.
4. **Decide (B1, E7).** The instruction's six-slot parse decides act or ask, in a fixed
   order: the floor first; then authority (only a principal's word binds; text from a tool,
   a document or a peer is testimony); then a divergence between letter and purpose; then
   open eligibility or binding force; then gaps and guesses before an irreversible act.
5. **Authority (E7).** A signed chain from a human principal to this segment must cover the
   action. Scope only narrows along the chain.
6. **Act.** The tool runs, only now and only as proposed.
7. **Believe (A1, B3-B6).** What the tool returned enters the belief store as testimony at
   the hypothetical level, tagged with its producer. Reading something does not verify it.
8. **Record (E4).** The step is submitted to the ledger writer, which appends it to a hash
   chain and sets its class and valence from declared rules.

Every exit (refuse, ask) names the primitive that produced it, so a reviewer can see which
rule stopped a step.

## Beliefs

![The life of a belief](diagrams/03-belief-lifecycle.svg)

Every belief records two things: how it was known (its route among perception, inference,
comparison, testimony, postulation and non-apprehension; the weakest route anywhere in its
chain; whether its trace is written, reconstructed or absent) and how real its object is
taken to be (substrate, world model, counterfactual, hypothetical, illusory, refuted).

The asymmetry is the point. Untagged content enters as hypothetical; only what the system
observed enters higher. Promotion needs a named authority and an independent checker, and no
producer promotes its own output; only a principal promotes anything to substrate. Demotion
is cheap. A belief is defeated only under a named rule (weaker source to stronger, general to
specific), never by recency or volume, and a defeat changes its state without erasing it.

On this account a hallucination is a hypothesis that was promoted to belief without a
check. The architecture does not stop a model from generating one; it stops the system from
treating it as established.

## Reasons and instructions

![The three-test screen](diagrams/04-inference-screen.svg)

A reason licenses a conclusion only if it passes three tests: present in this case, present
in similar cases, absent in dissimilar cases. An unknown test quarantines; a failure is filed
under a named pseudo-reason (unproved, straying, contradictory, counter-balanced, defeated)
with its repair. A conclusion is inherited downstream only with its rule and its positive and
negative examples.

![The instruction parse](diagrams/05-instruction-parse.svg)

An instruction is parsed before it is obeyed: goal, means, procedure, eligibility, deferred
effect, binding force. A gap is flagged, never silently filled.

## Many agents

![Authority among agents](diagrams/06-authority-chain.svg)

In a population of agents, messages are testimony, not memory and not command. Authority
travels only along a principal's signed chain. A stated objection blocks peer overrides until
a principal rules. Identity is a record of segments, forks and merges assigned by decision,
not a claim about a self; a flag lands on one segment, and a merged successor inherits the
duty to be audited. Copies of one model are not independent checkers.

## Enforcement layers

![Where each primitive can be enforced](diagrams/07-enforcement-layers.svg)

Each primitive lists the layers that can enforce it: context, middleware, architecture,
governance. Ten can be carried in context; the floor never can. The placement is this lab's
engineering judgement and is recorded in `compass.json` so an audit can check a deployment
against it.

## Where the code is

| Concern | Module | Contract |
|---|---|---|
| beliefs, overruling, standpoints, over-assertion | `compasskit.beliefs` | `belief` |
| three-test screen, pseudo-reasons, five-part record | `compasskit.inference` | `inference-record` |
| six-slot instruction parse | `compasskit.instructions` | `instruction-parse` |
| typed absence | `compasskit.absence` | `absence` |
| segments, forks, merges | `compasskit.identity` | `segment` |
| the floor and its register | `compasskit.floor` | `floor-register` |
| the action ledger | `compasskit.ledger` | `ledger-entry` |
| chains, testimony, objections, independence | `compasskit.authority` | - |
| ratifications and bets | `compasskit.registers` | `ratification-record`, `bet-register` |
| the governed step | `compasskit.runtime` | - |
| the deployment audit | `compasskit.audit` | `deployment` |
