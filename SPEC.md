# RACI.sh specification (draft)

Status: draft, from the 2026-11-05 rules discussion. Not normative yet.
Prior art: jRACI, raci.ai, ESIS (RACI auth/inference rules). See BRAINDUMP.md.

## 1. Core model

- A **realm** matches a SteerSpec realm. Realms nest (realm, sub-realm, ruleset).
- A **RACI entry** binds a **party** (human or agent) to a set of **roles**, a subset of {R, A, C, I}, for an **activity** on a **resource** within a realm.
- The data model is always the permissive one: a party may hold several roles on the same activity and resource. Strictness is validation (section 2), not schema, so one `.raci` format serves every mode.
- Role precedence, for display and "best role": A > R > C > I.
- Changes are soft: entries are never destroyed, only superseded (see section 4).

## 2. Constraints and strictness

Strictness is a customer choice. It is expressed as a set of named constraints, each of which is a rule that can be switched on per realm.

| Constraint | Meaning |
| --- | --- |
| `single-accountable` | At most one A per activity and resource. |
| `single-responsible` | At most one R per activity and resource. |
| `one-role-per-party` | A party holds at most one role per activity and resource. |
| `min-ra` | At least one R or A must remain; removing the last needs a named substitute. |
| `separation-of-duties` | Declarative conflicts, e.g. a party that is R on X may not be A on Y. |

### 2.1 Separation of duties

A `separation-of-duties` constraint is a list of **conflict pairs**, each a structured declaration: a party that holds `roles` on (`activity`, `resource`) A must not hold `roles` on (`activity`, `resource`) B. Example (Alice): R on Acme conflicts with A on Emca.

- **Scope is the declaring realm and its descendants.** A conflict pair declared in a realm is evaluated among the entries of that realm and of its sub-realms (the effective realm path), so an inherited pair is enforced on entries created in a child. Comparisons between an entry in a parent and an entry in a descendant are allowed. Comparisons between sibling realms, or between unrelated realms, never happen.
- **Deterministic.** The `raci` CLI evaluates conflict pairs itself, so a violating change is rejected like any other constraint violation.
- **Tighten-only applies**: a sub-realm may add conflict pairs, never remove an inherited one.
- Open: selector syntax for activities and resources in a pair (names, wildcards, resource types).

`strict` is a preset that enables `single-accountable`, `single-responsible`, `one-role-per-party` and `min-ra`. `separation-of-duties` is opt-in because it needs a conflict list.

A change that violates an enabled constraint is **rejected**. There is no silent auto-demotion (raci.ai did this). An explicit, logged "replace" action may transfer a role in a single audited change.

## 3. Inheritance

- Constraint policy is **tighten-only**: a sub-realm may add constraints but never relax or disable one set by an ancestor. The effective policy is the union along the realm path.
- SteerSpec lets a rule `overrides` an inherited one, which could relax it. RACI.sh therefore **lints** every override of a constraint rule and rejects any whose effect is weaker than the rule it replaces.
- RACI entries resolve most-specific-first. Merge versus override per role (proposal, not decided): C and I merge across levels; A and R override.
- Beyond static resolution, RACI is derived by **inference rules**, as in ESIS (`raci_infer_rules.xml`). Inference rules are themselves SteerSpec-style rules, shipped as a default set that a realm can customise.

### 3.1 Inference rules

A rule has:

- **target type**: the resource type whose RACI is being derived (e.g. audit).
- **operation**: `new`, `add`, `update` or `delete`, the change to the target or to a source that fires the rule.
- **trigger type** (optional): the source resource type whose RACI change fired the rule (e.g. module, location). Absent for a change on the target itself.
- **actions**, from a small vocabulary (taken from ESIS):
  - `map(source-type, from-role, to-role)`: parties holding `from-role` on the source get `to-role` on the target. ESIS example: module R becomes audit A, module A becomes audit I.
  - `add-issuer(role)`: the party creating the target gets `role`.
  - `strip(held-role, role)`: parties holding `held-role` on the source lose `role` on the target (ESIS: a module I loses A and R on the audit).

Two ESIS semantics to keep:

- Some rules **add only** and never overwrite an existing entry (e.g. location updates add missing stakeholders as C or I).
- If no rule matches a new target, ESIS left it with an empty RACI (a "zombie" object). In RACI.sh the originating change is still evaluated against the section 2 constraints. Where `min-ra` is enabled, an empty RACI violates it and the change is rejected. Otherwise the target is created with an empty RACI and the commit marker lists a `findings` entry (`no-matching-rule`), so the condition is audited and reportable.

Inferred changes pass through the section 2 constraints like any other change and are audited with the rule that produced them.

Inference is **non-recursive**: a change produced by an inference rule does not fire further inference rules. Only the original (user or agent) change is evaluated against the rule set, once. This makes loops impossible by construction, so no cycle detection is needed. All rules see the same input: the original change and the state before any inference. A rule therefore cannot depend on what another rule produced. A chain such as module to audit to recommendation is expressed by a direct rule on the final target, triggered by the module change and mapping module roles straight to recommendation roles (e.g. `map(module, R, A)` on recommendation), not via the audit's inferred roles. If a target's roles genuinely need another target's inferred result, that is out of scope for inference; the party must change the intermediate entry explicitly, which is a new original change.

**Evaluation order.** Rules are evaluated in rule-id order, with a deterministic tie-break (realm depth, then name). Rule evaluation is therefore reproducible and auditable.

**Conflicts.** If two rules set different roles for the same party on the same resource, the stricter outcome wins, and the conflict is recorded in the audit log together with both rule ids. "Stricter" means the result that satisfies more enabled constraints; ties go to the earlier rule.

**`strip` and tighten-only.** Tighten-only governs constraints (section 2), not entries. `strip` changes entries, so it is allowed as a rule action. It is never a way to relax a constraint, and its result still has to satisfy every enabled constraint (e.g. `min-ra`).

## 4. Audit

Every change is an append-only event. Policy and rule changes (constraints, inference rules) are audited too, as separate event types, since they change the RACI system itself. Rules follow the SteerSpec lifecycle (section 6): a published rule is never edited, so these events are state transitions and supersessions, not edits.

### 4.1 Event shape

One JSON object per event. Every event has a common envelope and a `type` discriminator, `entry`, `constraint`, `rule` or `commit`, which selects the payload.

Envelope (all types):

- `id`, `seq` (per realm), `ts`, `realm`, `type`
- `change_id`: groups the original change with every inferred change it produced (the transaction).
- `actor`: the party, and how the change arrived: `user`, `agent`, `import` or `inference`.
- `cause`: for inferred events, the rule id and the originating event id. Inferred events are never causes, which makes non-recursion verifiable from the log.
- `constraints`: each enabled constraint that was evaluated, with its result.
- `outcome`: `applied` or `rejected`, with a reason.
- `prev_hash`: hash of the previous event in the realm.

Payload for `type: entry`:

- `op`: `add`, `update`, `remove` or `replace`.
- `target`: activity, resource and party.
- `before`, `after`: the role sets. A `remove` has an empty `after`; materialisation and replay treat the entry as absent from that point, and the earlier events stay in the log.
- `conflict`: both rule ids, when stricter-wins resolution applied.
- `replace` is linked `entry` events (the one losing the role and the one gaining it) sharing one `change_id`, made atomic by the commit marker below.

Payload for `type: commit`:

- `change_id` and `events`: the ids of the events of that change. The commit marker is appended last, after all other events of the change.
- Replay applies a change only if its commit marker is present. Events of a `change_id` without a marker (for example after a crash) are incomplete and are ignored, and the CLI reports them.

A change is **all or nothing**. If the original change or any change inferred from it violates an enabled constraint, the whole `change_id` is rejected: nothing applies, the rejection is logged with the violating event and constraint, and the commit marker has `outcome: rejected`.

Payload for `type: constraint`:

- `constraint`: the constraint name (e.g. `single-accountable`, `separation-of-duties`).
- `op`: `enable` or `add-pair` (tighten-only, so there is no disable or remove).
- `params`: for `add-pair`, the conflict pair.

Payload for `type: rule`:

- `rule_id`, `revision`.
- `transition`: the SteerSpec lifecycle state change (`from` and `to`), or `supersedes` naming the rule it replaces.
- `body`: the full structured rule body, so replay is self-contained, and `body_hash`, its hash, to verify the rendered SteerSpec rule and the authoring source against it.

### 4.2 Rules

- **Rejected changes are logged** (`outcome: rejected`), not only applied ones.
- **Tamper evidence:** a per-realm hash chain via `prev_hash`, identical for the offline log and the cloud store.
- **Source of truth:** the log is the source and the `.raci` file is a materialised view that can be rebuilt and verified by replay.
- **Offline storage:** a JSONL log next to the `.raci` file; the CLI is its only writer. Git history is not a substitute, as it does not record rejected attempts or causes.

## 5. Out of scope

RACI.sh manages RACI. Enforcing it is the customer's job. The service can answer "who is R/A/C/I" and "does this change violate a constraint", not "may this call proceed".

## 6. SteerSpec mapping

- RACI.sh rules (constraints, inference rules, default rule-management rules) have a **structured source** that the `raci` CLI evaluates deterministically. It is the authoring format. The canonical record of which rule was in force is the audit log (section 4.2): loading a new or changed rule source appends a `rule` event carrying the full structured body, and the CLI evaluates only rules recorded in the log. A source that differs from the log's latest rule event is reported as unrecorded and not evaluated.
- The specification and those rules are **rendered into SteerSpec rules** in a `sh.raci` realm: prose `MUST` bodies with SteerSpec ids, lifecycle states and supersession, plus notes carrying the structured form. The rendered rules are derived, never hand-edited.
- Rendering to prose gives the SteerSpec/LLM path (CI gates, advisory review of rule changes) without making enforcement depend on an LLM. Deterministic checks reject; the LLM path only reviews.
- Customer realms depend on `sh.raci` like any SteerSpec realm and customise by adding or superseding rules, subject to the override lint in section 3.
- Open: realm id and versioning of `sh.raci`, and the exact mapping of structured fields into rule bodies and notes.

## Open questions

Tracked in beads (`bd list`): default SteerSpec rule-management rule set, separation-of-duties semantics, `.raci` file format.
