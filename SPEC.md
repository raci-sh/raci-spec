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

`strict` is a preset that enables `single-accountable`, `single-responsible`, `one-role-per-party` and `min-ra`. `separation-of-duties` is opt-in because it needs a conflict list.

A change that violates an enabled constraint is **rejected**. There is no silent auto-demotion (raci.ai did this). An explicit, logged "replace" action may transfer a role in a single audited change.

## 3. Inheritance

- Constraint policy is **tighten-only**: a sub-realm may add constraints but never relax or disable one set by an ancestor. The effective policy is the union along the realm path.
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
- If no rule matches, the target gets an empty RACI (a "zombie" object in ESIS). RACI.sh should instead report this as a validation finding.

Inferred changes pass through the section 2 constraints like any other change and are audited with the rule that produced them.

Inference is **non-recursive**: a change produced by an inference rule does not fire further inference rules. Only the original (user or agent) change is evaluated against the rule set, once. This makes loops impossible by construction, so no cycle detection is needed. Chains such as module to audit to recommendation must be written as separate rules, each triggered by the original change, not by another rule's output.

**Evaluation order.** Rules are evaluated in rule-id order, with a deterministic tie-break (realm depth, then name). Rule evaluation is therefore reproducible and auditable.

**Conflicts.** If two rules set different roles for the same party on the same resource, the stricter outcome wins, and the conflict is recorded in the audit log together with both rule ids. "Stricter" means the result that satisfies more enabled constraints; ties go to the earlier rule.

**`strip` and tighten-only.** Tighten-only governs constraints (section 2), not entries. `strip` changes entries, so it is allowed as a rule action. It is never a way to relax a constraint, and its result still has to satisfy every enabled constraint (e.g. `min-ra`).

## 4. Audit

Every change is an append-only event: who, when, what changed, previous state, and the realm it applied in. The event format is open: see beads.

## 5. Out of scope

RACI.sh manages RACI. Enforcing it is the customer's job. The service can answer "who is R/A/C/I" and "does this change violate a constraint", not "may this call proceed".

## Open questions

Tracked in beads (`bd list`): inference style, audit event format, default SteerSpec rule-management rule set, separation-of-duties semantics, `.raci` file format.
