# RACI.sh specification (draft)

Status: draft, from the 2026-11-05 rules discussion. Not normative yet.
Prior art: jRACI, raci.ai, ESIS (RACI auth/inference rules). See BRAINDUMP.md.

## 1. Core model

- A **realm** matches a SteerSpec realm. Realms nest (realm, sub-realm). Rules live in **entities** within a realm, and entities inherit from other entities (`inherits`), as in SteerSpec.
- A **RACI entry** binds a **party** (human or agent) to a set of **roles**, a subset of {R, A, C, I}, for an **activity** on a **resource** within a realm.
- The data model is always the permissive one: a party may hold several roles on the same activity and resource. Strictness is validation (section 2), not schema, so one `.raci` format serves every mode.
- A **resource** has a type, a realm, and an optional parent resource (e.g. an audit's parent is a module). Resource creation and deletion are audited events (section 4.1).
- Role precedence, for display and "best role": A > R > C > I.
- Entries are never erased. A removal is an event, and the full history stays in the audit log (section 4).

## 2. Constraints and strictness

Strictness is a customer choice. It is expressed as a set of named constraints, each of which is a rule that can be switched on per realm.

Constraints are evaluated against the **effective entries** of the realm in which a change lands: the entries visible there after inheritance and overrides are resolved (section 3). This is what lets a parent's separation-of-duties pair apply to a child's entries. (Proposal, not decided.)

**Revalidation of descendants.** A change that lands in a realm also revalidates the descendant realms of the same realm tree that its effective entries reach: a change to a parent entry, or a new or tightened constraint. The change reads those descendants but writes only its own realm's log. If any descendant would be left in violation, the whole change is rejected, and the rejection reason names the descendant realm and the constraint. Realms outside the tree (separate realms that merely depend on this one) are not revalidated; the CLI's verification reports their violations as findings when they next load.

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
- Two hierarchies are involved. The **realm tree** decides which entries and which constraint policy apply to a change (entry scope and separation-of-duties scope follow the realm path). **Rules** (constraints, inference rules) live in entities and inherit through `inherits`; that is the chain the override lint below acts on.
- Only rules in state `P` (Published) or `I` (Implemented) are in force. Rules in `D`, `A`, `R` or `T` are not evaluated.
- SteerSpec lets a rule `overrides` an inherited one, which could relax it. RACI.sh therefore **lints** every override of a constraint rule and rejects any whose effect is weaker than the rule it replaces. For constraint rules, an override is **not weaker** only if its enabled constraints and conflict pairs are a superset of the overridden rule's. Inference rules are not compared for strength (they set entries, not policy, and their output passes the constraints anyway). Any override the lint cannot prove not-weaker is rejected.
- RACI entries resolve most-specific-first. Merge versus override per role (proposal, not decided): C and I merge across levels; A and R override.
- Beyond static resolution, RACI is derived by **inference rules**, as in ESIS (`raci_infer_rules.xml`). Inference rules are themselves SteerSpec-style rules, shipped as a default set that a realm can customise.

### 3.1 Inference rules

A rule has:

- **target type**: the resource type whose RACI is being derived (e.g. audit).
- **operation**: the change that fires the rule. `new` or `delete` are resource events; `add`, `update` or `remove` are entry events (on the trigger type, or on the target itself when there is no trigger type).
- **trigger type** (optional): the resource type whose entry change fires the rule (e.g. module, location). Absent for a change on the target itself. A rule with a trigger type must have an entry operation (`add`, `update` or `remove`), never `new` or `delete`, and fires on entry events of that type with that operation, for each target whose source (below) binds to the changed resource.
- **selector** (optional): names the source resource explicitly, instead of the default search below (open: selector syntax).
- **actions**, from a small vocabulary (taken from ESIS):
  - `map(source-type, from-role, to-role)`: parties holding `from-role` on the source get `to-role` on the target. ESIS example: module R becomes audit A, module A becomes audit I.
  - `add-issuer(role)`: the party creating the target gets `role`. Only valid in rules whose operation is `new`, the one operation that has a creating party.
  - `strip(source-type, held-role, role)`: parties holding `held-role` on the source of `source-type` lose `role` on the target (ESIS: a module I loses A and R on the audit).

Any action may carry the attribute `add-only`: it then adds missing entries and never changes an existing one.

**Source binding.** `map` and `strip` locate their source as the nearest resource of the action's `source-type`, searching the target itself first and then its parent links. So an action whose source type is the target's own type reads the target (the case of an entry event on the target with no trigger type), and `map(module, R, A)` on a new audit reads the audit's parent module. A rule that names a selector uses it instead.

Two ESIS semantics to keep:

- Some rules are **add-only** (the attribute above), e.g. location updates add missing stakeholders as C or I without touching existing entries.
- If no rule matches a new target, ESIS left it with an empty RACI (a "zombie" object). In RACI.sh the originating change is still evaluated against the section 2 constraints. Where `min-ra` is enabled, an empty RACI violates it and the change is rejected. Otherwise the target is created with an empty RACI and the commit marker lists a `findings` entry (`no-matching-rule`), so the condition is audited and reportable.

Inferred changes pass through the section 2 constraints like any other change and are audited with the rule that produced them.

Inference is **non-recursive**: a change produced by an inference rule does not fire further inference rules. Only the original (user or agent) change is evaluated against the rule set, once. This makes loops impossible by construction, so no cycle detection is needed. All rules see the same input: the original change and the state before any inference. A rule therefore cannot depend on what another rule produced. A chain such as module to audit to recommendation is expressed by a direct rule on the final target, triggered by the module change and mapping module roles straight to recommendation roles (e.g. `map(module, R, A)` on recommendation), not via the audit's inferred roles. If a target's roles genuinely need another target's inferred result, that is out of scope for inference; the party must change the intermediate entry explicitly, which is a new original change.

**Evaluation order.** Rules are evaluated in rule-id order, with a deterministic tie-break (realm depth, then name). Rule evaluation is therefore reproducible and auditable.

**Composition.** Each rule action produces **deltas**, not states: `map`, `add-issuer` produce role additions, `strip` produces role removals. An `add-only` action produces additions only for missing entries and never a removal or a change to an existing entry. Deltas are composed per (party, activity, resource, role) on top of the state before inference:

1. Non-contradicting deltas compose directly: the result is the prior roles plus all additions, minus all removals.
2. Two deltas contradict when one adds and another removes the same role for the same party, activity and resource. The stricter outcome wins: the one whose resulting state satisfies more enabled constraints. Ties go to the earlier rule (section 3.1 evaluation order). An `add-only` addition takes part in this like any other addition. The losing delta is discarded and recorded in the audit log with both rule ids.
3. If the composed result still violates an enabled constraint, the change is rejected (all or nothing, section 4.1).

**`strip` and tighten-only.** Tighten-only governs constraints (section 2), not entries. `strip` changes entries, so it is allowed as a rule action. It is never a way to relax a constraint, and its result still has to satisfy every enabled constraint (e.g. `min-ra`).

## 4. Audit

Every change is an append-only event. Policy and rule changes (constraints, inference rules) are audited too, as separate event types, since they change the RACI system itself. Rules follow the SteerSpec lifecycle (section 6): a published rule is never edited, so these events are state transitions and supersessions, not edits.

### 4.1 Event shape

One JSON object per event. Every event has a common envelope and a `type` discriminator, `entry`, `resource`, `constraint`, `rule`, `pin` or `commit`, which selects the payload.

Envelope (all types):

- `id`, `seq` (per realm), `ts`, `realm`, `type`
- `change_id`: groups the original change with every inferred change it produced (the transaction).
- `actor`: the party, and how the change arrived: `user`, `agent`, `import` or `inference`.
- `cause`: for inferred events, the rule id and the originating event id. Inferred events are never causes, which makes non-recursion verifiable from the log.
- `constraints`: each enabled constraint that was evaluated, with its result.
- `outcome`: `applied` or `rejected`, with a reason.
- `hash`, `prev_hash`: `hash` is blake3 over the canonical JSON of the event without the `hash` field and with `prev_hash` included. **Canonical JSON** throughout this specification is RFC 8785 (JCS): keys sorted, no insignificant whitespace, defined string escaping and number formatting. Every digest in the log and in the `.raci` file (`hash`, `prev_hash`, `body_hash`, `head_hash`) is the string `blake3:` followed by 64 lowercase hexadecimal characters, as in SteerSpec's `rule_set.hash`. The first event of a realm has the all-zero `prev_hash`, `blake3:` followed by 64 zeros.

Payload for `type: entry`:

- `op`: `add`, `update`, `remove` or `replace`.
- `target`: activity, resource and party.
- `before`, `after`: the role sets. A `remove` has an empty `after`; materialisation and replay treat the entry as absent from that point, and the earlier events stay in the log.
- `conflict`: both rule ids, when stricter-wins resolution applied.
- `replace` is linked `entry` events (the one losing the role and the one gaining it) sharing one `change_id`, made atomic by the commit marker below.

Payload for `type: commit`:

- `change_id` and `events`: the ids of the events of that change. The commit marker is appended last, after all other events of the change.
- `outcome`: `applied` or `rejected`, with a reason when rejected.
- `findings` (optional): a list of non-blocking findings, each `{code, detail}`, e.g. `no-matching-rule`.
- Replay applies a change only if its commit marker is present **and** has `outcome: applied`. Events of a rejected marker are ignored for materialisation but stay in the log as the record of the rejection. Events of a `change_id` without any marker (for example after a crash) are incomplete: they are ignored and the CLI reports them.

A change is **all or nothing**. If the original change or any change inferred from it violates an enabled constraint, the whole `change_id` is rejected: nothing applies, the rejection is logged with the violating event and constraint, and the commit marker has `outcome: rejected`.

Payload for `type: resource`:

- `op`: `new` or `delete`.
- `resource`: id, type, realm and optional parent resource.
- A resource event can be the `cause` of inferred entries (e.g. `add-issuer` on `new`).

Payload for `type: constraint`:

- `constraint`: the constraint name (e.g. `single-accountable`, `separation-of-duties`).
- `op`: `enable` or `add-pair` (tighten-only, so there is no disable or remove).
- `params`: for `add-pair`, the conflict pair.

Payload for `type: rule`:

- `rule_id`, `revision`.
- `transition`: the SteerSpec lifecycle state change (`from` and `to`), or `supersedes` naming the rule it replaces.
- `body`: the full structured rule body, so replay is self-contained, and `body_hash`, blake3 over the canonical JSON of `body` alone, to verify the rendered SteerSpec rule and the authoring source against it.

Payload for `type: pin`:

- `dependency_realm`, `version`: the dependency realm (e.g. `sh.raci`; distinct from the envelope's `realm`, which is the realm that owns the event) and the version this realm's rules are evaluated against from this event on.
- `op`: `set`. A later `pin` event for the same `dependency_realm` replaces the earlier one. Replay derives the realm's current pins from these events, so `pins` in the `.raci` file (section 7) is reconstructible and verifiable. The `rule` events that follow a version change record the structured rules that the pin brings in.

### 4.2 Rules

- **Rejected changes are logged** (`outcome: rejected`), not only applied ones.
- **Tamper evidence:** a per-realm hash chain via `prev_hash`, identical for the offline log and the cloud store. Verification recomputes every `hash` and checks each `prev_hash` link, failing at the first mismatch. It also checks each `rule` event's `body_hash` against its `body`, and against the rendered SteerSpec rule and the authoring source (section 6).
- **Source of truth:** the log is the source and the `.raci` file is a materialised view that can be rebuilt and verified by replay.
- **One realm per change:** a change and everything inferred from it are written to the log of the realm where the original change lands. Resources in ancestor realms can be read as sources, and descendant realms are read for revalidation (section 2), but neither is written by that change. So a `change_id`, its commit marker and the hash chain never span two realms.
- **Offline storage:** one JSONL log per realm, next to the `.raci` file; the CLI is its only writer. Offline mode is single-writer per realm. Concurrent clones diverge the hash chain, and merging them is deferred (open); multi-writer is the cloud mode's job. Git history is not a substitute, as it does not record rejected attempts or causes.

## 5. Out of scope

RACI.sh manages RACI. Enforcing it is the customer's job. The service can answer "who is R/A/C/I" and "does this change violate a constraint", not "may this call proceed".

## 6. SteerSpec mapping

- RACI.sh rules (constraints, inference rules, default rule-management rules) have a **structured source** that the `raci` CLI evaluates deterministically. It is the authoring format. The canonical record of which rule was in force is the audit log (section 4.2): loading a new or changed structured rule source appends a `rule` event carrying the full structured body, and the CLI evaluates only rules recorded in the log. A source that differs from the log's latest rule event is reported as unrecorded and not evaluated.

**Bootstrap.** A realm's log starts empty, and until rules are recorded nothing is in force, so entry changes are rejected with `no-rules-in-force`. An explicit init appends a `pin` event for each dependency realm (e.g. `sh.raci`), then `rule` events (actor `import`) for the in-force rules that have a structured source, of the pinned versions and of the realm's own entities. Every later change of a pinned version appends a `pin` event and the `rule` events of the rules with a structured source that the new version brings in, so inherited rules are recorded in the log of the realm that uses them.
- The specification is **hand-authored as normative prose rules** in the `sh.raci` realm (`RACI`, `RACICNS`, `RACIINH`, `RACIINF`, `RACIAUD`, `RACIFILE`, `RACIMGT`), with SteerSpec ids, lifecycle states and supersession. The default configuration rules (the strict preset, separation of duties, default inference and rule-management rules) are **rendered into SteerSpec rules** from their structured source: prose `MUST` bodies, plus notes carrying the structured form. A rendered rule is derived, never hand-edited.
- Rendering to prose gives the SteerSpec/LLM path (CI gates, advisory review of rule changes) without making enforcement depend on an LLM. Deterministic checks reject; the LLM path only reviews.
- Customer realms depend on `sh.raci` like any SteerSpec realm and customise by authoring structured rules in their own realm, which are rendered to SteerSpec rules like the defaults. They add rules or override inherited ones, subject to the override lint in section 3.
- Open: realm id and versioning of `sh.raci`, and the exact mapping of structured fields into rule bodies and notes.

## 7. The `.raci` file

The `.raci` file is a **materialised view** of one realm's audit log (section 4.2). It holds RACI and nothing else: no findings, no history. The CLI is its only writer and it is never hand-edited.

- **Encoding:** one canonical JSON document (RFC 8785, the same canonical form that the event hashes use, section 4.1). Output is deterministic, so the same log always yields byte-identical files. The example below is pretty-printed for reading; the stored file has no insignificant whitespace.
- **Scope:** the realm's own state. The entries and resources of ancestor and descendant realms are read at load time (effective entries, revalidation) and never embedded, so the file cannot drift from its source. What is embedded about other realms is derived from this realm's own log: `pins` and `rules_in_force`, both recorded there (sections 4.1 and 6).
- **No paths:** the view carries no filesystem paths, so the same log yields the same bytes in any checkout. The log is found by convention, next to the `.raci` file (section 4.2).
- **Staleness:** `log.head_seq` and `log.head_hash` identify the log state the view reflects. A view whose head differs from the log's is stale and is rebuilt by replay. For an empty log the head is `head_seq` 0 and `head_hash` the all-zero digest, the same sentinel as the first event's `prev_hash`.

Shape:

```json
{
  "constraints": {
    "enabled": [ "min-ra", "single-accountable" ],
    "pairs": [ { "a": { "activity": "<selector>", "resource": "<selector>", "roles": "R" },
                 "b": { "activity": "<selector>", "resource": "<selector>", "roles": "A" } } ]
  },
  "entries": [ { "activity": "<activity>", "party": "<party>", "resource": "<id>", "roles": "AR" } ],
  "log": { "head_hash": "<hash of the head event>", "head_seq": 412 },
  "pins": [ { "dependency_realm": "<dependency realm>", "version": "<pinned version>" } ],
  "raci": "1",
  "realm": "<realm id>",
  "resources": [ { "id": "<id>", "parent": "<id or absent>", "type": "<type>" } ],
  "rules_in_force": [ { "body_hash": "<hash>", "revision": 2, "rule_id": "<id>" } ]
}
```

- `roles` is a string of the held roles in the fixed precedence order A, R, C, I (section 1), so `"AR"`, never `"RA"`. An entry with no roles is absent, not stored empty.
- Object members are in the canonical (sorted) order, as in the example. Array ordering is canonical too: `resources` by `id`; `entries` by (`resource`, `activity`, `party`); `rules_in_force` by `rule_id`; `pins` by (`dependency_realm`, `version`); `enabled` alphabetically; `pairs` by their canonical JSON.
- `rules_in_force` lists every rule recorded in force in this realm's log (section 6, including inherited ones) with its `body_hash`. Verification compares these with the log's `rule` events and with the structured rule sources without replaying the whole log.
- `pins` is derived from the log's `pin` events (section 4.1): the current version of each dependency realm the log was evaluated against (e.g. the `sh.raci` version). Verification recomputes it by replay.
- `constraints` lists the constraints recorded by this realm's own `constraint` events. The effective set (the union along the realm path, section 3) is computed at load and not embedded.
- Selectors in `pairs` follow the selector syntax, which is open (section 2.1).

### 7.1 Verification report

Findings are not part of `.raci`. `raci verify` computes them on demand and emits a separate report, and nothing about it is persisted in the view.

```json
{ "realm": "<realm id>", "log_head": { "seq": 412, "hash": "<hash>" },
  "findings": [ { "code": "<code>", "severity": "error", "realm": "<realm id>", "detail": "<text>" } ] }
```

| Code | Severity | Meaning |
| --- | --- | --- |
| `hash-mismatch` | error | A recomputed `hash` or a `prev_hash` link of the log fails (section 4.2). |
| `view-mismatch` | error | Replaying the log gives a different state than the `.raci` file. |
| `stale-view` | warning | The view's log head differs from the log's; rebuild by replay. |
| `unrecorded-rule` | error | A structured rule source differs from the log's latest `rule` event, so it is not evaluated (section 6). |
| `incomplete-change` | warning | A `change_id` has events but no commit marker (section 4.1). |
| `no-matching-rule` | warning | A target was created with an empty RACI because no inference rule matched. |
| `descendant-violation` | error | A realm outside the change's tree, which depends on this one, now violates a constraint (section 2). |

A commit marker's `findings` (section 4.1) are the subset recorded at change time. The report carries them with `severity` and `realm` added, next to the findings that only a fresh verification can produce.

## Open questions

Tracked in beads (`bd list`): default SteerSpec rule-management rule set, selector syntax for activities and resources, the `sh.raci` realm and rendering, and merging concurrent offline logs. Also undecided: merge-versus-override of roles across realm levels, and evaluating constraints against effective entries (sections 2 and 3).
