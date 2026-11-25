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

### 1.1 Identifiers

- **Realm ids** are SteerSpec realm ids: one or more dot-separated labels, each a lowercase letter followed by lowercase letters and digits (`^[a-z][a-z0-9]*(\.[a-z][a-z0-9]*)*$`), e.g. `sh.raci`, `com.example.payments`.
- **Activities and resource types** are lowercase kebab-case words (`^[a-z][a-z0-9]*(-[a-z0-9]+)*$`), the pattern of `name` in the `raci/1` payload (section 6.1).
- **Party and resource ids** are opaque to RACI.sh: strings of 1 to 256 Unicode code points with no control characters (U+0000 to U+001F, U+007F). They are compared as exact strings, with no case folding or normalisation. By convention a party id is prefixed by its namespace, as in `github:alice`, the form SteerSpec uses for `added_by`.
- **A resource is identified by its realm and id.** Every reference to one is `{"realm": <realm id>, "id": <resource id>}`: an entry's target, a `parent`, a selector, the side of a pair, an entry in the view. A reference resolves to that resource alone, never by a search for the id, so the same id in two realms is two resources and neither can stand in for the other. Only a declaration (the `resource` event and the view's `resources`) gives a bare `id`: its realm is the log's.
- **An id is never reused in its realm.** Once an applied change has created a resource with an id, no later change in that realm creates that id again, also after a delete (`invalid-change`). A log with such a creation applied holds an event that is not valid (`hash-mismatch`).
- **Entry targets and parents never dangle.** An entry's target and a resource's `parent` are live resources of the log's realm or an ancestor (`invalid-change`). Where verification finds one that is not, it reports `dangling-reference` and the log cannot be replayed (section 4.1). Other references can name a resource that is deleted later: a pair side then matches nothing (section 2.1), and a change that fires a rule whose selector names it is rejected with `invalid-change` (section 3.1).
- **Rule ids** are SteerSpec rule ids, qualified as `<realm id>:<rule id>` when the rule comes from a dependency realm (section 6.1).

### 1.2 Deleting a resource

- **Only the owner deletes.** A `delete` names a live resource of the log's own realm, with its declared type and parent.
- **Refused while anything outside the change depends on it.** A resource that is the `parent` of a live resource, in its realm or a descendant, cannot be deleted. Neither can a resource on which a descendant realm holds an entry, since a change writes only its own realm's log (section 4.2). Both are `invalid-change`. The descendant can remove its own entries first: `min-ra` does not stand in the way, since it counts only the grants recorded by the realm that owns the resource (section 2).
- **The delete takes its entries with it, audited.** The `delete` is the first event of its change. One `remove` entry event for each entry of the realm on that resource follows immediately, by activity and party in code point order, with the delete's actor and no `cause`. Anything inferred comes after them. An applied delete without exactly these removals is not a valid event (`hash-mismatch`).
- **Exempt from `min-ra`, only there.** `min-ra` does not apply to the resource that the change deletes, and the delete and its removals record no result for it. A removal on any other resource in the same change is not exempt. The exemption is recognised from the log alone: the target is the resource that the change's delete names.
- **No inference onto what is gone.** Neither the delete nor its removals fire inference rules (section 3.1), and no inference action produces a delta on the deleted resource.

## 2. Constraints and strictness

Strictness is a customer choice. It is expressed as a set of named constraints, each of which is a rule that can be switched on per realm.

**No grant is hidden.** Constraints count **grants**, and a grant is one role of one party on an activity and resource (section 2.1). The grants of a realm are the union of those that the realm and its ancestors record, with no override (section 3). A grant of one realm never hides a grant of another, and the same grant recorded by several realms counts as one grant. Which realms' grants a constraint counts:

- `single-accountable`, `single-responsible` and `one-role-per-party` count together the grants recorded by the realm that enables them, its ancestors and all its descendants, so two descendants that are siblings count together; the enabling realm's own siblings do not. So two child realms cannot each name an A on their parent's resource under a `single-accountable` that the parent or an ancestor enables.
- `min-ra` counts only the grants recorded by the realm that owns the resource, so a descendant's grant never stands in for the owner's, and `min-ra` never stops a descendant from removing its own. It applies to a resource when it is in the effective policy of the realm that owns that resource (section 3), so a descendant's `min-ra` never binds an ancestor's resources.
- Conflict pairs compare the grants of the declaring realm, its ancestors and its descendants, sibling realms included (section 2.1).

**Revalidation.** A change that lands in a realm also revalidates, read-only, every ancestor or descendant realm whose constraints count a grant that the change records, and every descendant realm that a resource, pair or constraint of the change reaches. It reads every log whose grants a constraint that it evaluates or revalidates counts, a sibling's included, but writes only its own realm's log (section 4.2). A constraint counts a log's grants only where that log can hold one that it compares, and a realm records entries only on its own and its ancestors' resources (section 1.1). So a sibling's log is read only for a grant on a resource that a common ancestor owns, or for a pair whose relation reaches the sibling's own resources (`any`, or `lineage` through parent links). If one of those logs cannot be replayed, the command fails (section 4.1). If revalidation would leave an ancestor or descendant realm in violation, the whole change is rejected, and the rejection reason names that realm and the constraint. Realms outside the tree (separate realms that merely depend on this one) are not revalidated; the CLI's verification reports their violations as findings when they next load.

| Constraint | Meaning |
| --- | --- |
| `single-accountable` | At most one A per activity and resource. |
| `single-responsible` | At most one R per activity and resource. |
| `one-role-per-party` | A party holds at most one role per activity and resource. |
| `min-ra` | At least one R or A recorded by the realm that owns the resource must remain per activity on it; removing the last needs a named substitute. Not applied to a resource that the change deletes (section 1.2). |
| `separation-of-duties` | Declarative conflicts, e.g. a party that is R on X may not be A on Y. |

### 2.1 Separation of duties

A `separation-of-duties` constraint is a list of **conflict pairs**, each a structured declaration: a party that holds any of the `roles` of one side must not hold any of the `roles` of the other, on resources that stand in the pair's `relation`. Example (Alice): R on Acme conflicts with A on Emca.

```json
{ "relation": "any",
  "a": { "activity": "*", "resource": { "realm": "com.example", "id": "Acme" }, "roles": "R" },
  "b": { "activity": "*", "resource": { "realm": "com.example", "id": "Emca" }, "roles": "A" } }
```

- **Scope is the declaring realm's tree, siblings included.** A conflict pair declared in a realm is evaluated between every two grants recorded by that realm, its ancestors or its descendants, sibling realms included, and between no others. Sibling realms here are descendants that are siblings of each other: the declaring realm's own siblings are not in scope. So an inherited pair is enforced on grants recorded in a child, a child's pair sees its parent's grants, and a parent's pair sees the grants of two children together, on resources that the parent or an ancestor owns or, where the pair's relation reaches them, on the children's own (section 2): Alice cannot be author through one child and publisher through another. A grant of one realm never hides one of another, and the same grant recorded by several realms counts as one grant (section 2). Comparisons with unrelated realms never happen.
- **Deterministic.** The `raci` CLI evaluates conflict pairs itself, so a violating change is rejected like any other constraint violation.
- **Tighten-only applies**: a sub-realm may add conflict pairs, never remove an inherited one.
- **Sides.** A side is `{activity, resource, roles}`. `activity` is an activity name or `*` for every activity. `resource` is exactly one of a reference `{"realm": <realm id>, "id": <resource id>}` (section 1.1), which matches that one resource and has no wildcard, and `{"type": <resource type>}`, where the type may be `*` for every resource. `roles` is a non-empty role string in the order A, R, C, I, and the side matches on **any** of them. A side that names a resource must name one that is live in the declaring realm, an ancestor or a descendant when the pair is declared, and a `same` pair whose sides name two different resources can never match. Both are `invalid-change`. A named resource that is deleted later leaves the pair matching nothing, since its id is never reused (section 1.1).
- **Relation.** `same`: one and the same resource (e.g. who authors a rule does not publish that rule). `lineage`: the same resource, or one is an ancestor of the other through parent links (e.g. who is R on a module is not A on its audit). `any`: any two resources in scope (e.g. Acme and Emca).
- **Conflict.** A grant is one role of one party on an activity and resource. A pair is violated when one party has two different grants, one matching each side, on resources in the relation. A grant never conflicts with itself, and two roles in one entry are two grants. The sides are unordered, so a pair and its mirror are the same pair.
- **Declaration.** A pair comes from an `add-pair` event (section 4.1), or from a `conflict-pair` rule (section 6.1) while that rule is in force. A realm's effective pairs are those of both kinds in the realm and its ancestors. Separation of duties is in effect whenever there is one: a pair needs no separate `enable`. A pair added by event is never removed. A pair from a rule leaves with its rule.
- **When.** Pairs are evaluated on the state that results from every change, not only entry changes: a new resource can create a lineage, and a pair entering force, by event, rule or version change, is checked against the entries that exist. That state includes every ancestor and descendant realm that the change revalidates (section 2). A violation in any of them rejects the change.
- **Fail closed.** A missing or cyclic parent link, or an entry on a resource that is not live, is a `dangling-reference`: the evaluation fails as for a log that cannot be replayed (section 4.1), and never reads it as "not related".

`strict` is a preset that enables `single-accountable`, `single-responsible`, `one-role-per-party` and `min-ra`. `separation-of-duties` is opt-in because it needs a conflict list.

A change that violates an enabled constraint is **rejected**. There is no silent auto-demotion (raci.ai did this). An explicit, logged "replace" action may transfer a role in a single audited change.

## 3. Inheritance

- Constraint policy is **tighten-only**: a sub-realm may add constraints but never relax or disable one set by an ancestor. The effective policy is the union along the realm path.
- Two hierarchies are involved. The **realm tree** decides which entries and which constraint policy apply to a change (section 2 says which realms' grants each constraint counts). **Rules** (constraints, inference rules) live in entities and inherit through `inherits`; that is the chain the override lint below acts on.
- Only rules in state `P` (Published) or `I` (Implemented) are in force. Rules in `D`, `A`, `R` or `T` are not evaluated.
- SteerSpec lets a rule `overrides` an inherited one, which could relax it. RACI.sh therefore **lints** every override of a constraint rule and rejects any whose effect is weaker than the rule it replaces. For constraint rules, an override is **not weaker** only if its enabled constraints and conflict pairs are a superset of the overridden rule's. Inference rules are not compared for strength (they set entries, not policy, and their output passes the constraints anyway). Any override the lint cannot prove not-weaker is rejected.
- **Roles add up across realm levels.** The grants of a realm are the union of the grants that the realm and its ancestors record, for every role, with no override: a child adds grants and never hides one. So an A that a parent records on its resource is a grant of the parent and of every realm below it, and a child cannot name its own A beside it under a `single-accountable` that counts both. A grant that a child records belongs to that child and its descendants only, so who is A on a parent's resource can differ between the parent and its children.
- A change never updates, removes or replaces an entry that another realm recorded: it writes only its own realm's log (section 4.2). A change whose composed inference (section 3.1) strips a role that an ancestor realm still grants is rejected with `invalid-change`, rather than removing this realm's copy while the role stays granted.
- Beyond static resolution, RACI is derived by **inference rules**, as in ESIS (`raci_infer_rules.xml`). Inference rules are themselves SteerSpec-style rules, shipped as a default set that a realm can customise.

### 3.1 Inference rules

A rule has:

- **target type**: the resource type whose RACI is being derived (e.g. audit), or the wildcard `*`, which matches a resource of any type (used by default rules, which cannot name customer-defined types).
- **operation**: the change that fires the rule. `new` is the one resource operation; `add`, `update` or `remove` are entry events (on the trigger type, or on the target itself when there is no trigger type). A deleted resource fires no rule: its removals fire none, and nothing is inferred onto it (section 1.2). ESIS's `DELETE` operation meant a party removed from the trigger, which is `remove` here.
- **trigger type** (optional): the resource type whose entry change fires the rule (e.g. module, location). Absent for a change on the target itself. A rule with a trigger type must have an entry operation (`add`, `update` or `remove`), never `new`, and fires on entry events of that type with that operation, for each target whose source (below) binds to the changed resource.
- **selector** (optional): `{"realm": <realm id>, "id": <resource id>}`, names the one source resource explicitly, instead of the default search below. Valid only on a rule with a `map` or `strip` action.
- **actions**, from a small vocabulary (taken from ESIS):
  - `map(source-type, from-role, to-role)`: parties holding `from-role` on the source get `to-role` on the target. ESIS example: module R becomes audit A, module A becomes audit I.
  - `add-issuer(role)`: the party creating the target gets `role`. Only valid in rules whose operation is `new`, the one operation that has a creating party.
  - `strip(source-type, held-role, role)`: parties holding `held-role` on the source of `source-type` lose `role` on the target (ESIS: a module I loses A and R on the audit).

An action may name an **activity**; an action that names none applies to every activity on the target. The wildcard `*` is valid only as a target type, never as a source type or trigger type.

Any action may carry the attribute `add-only`: it then adds missing entries and never changes an existing one.

**Source binding.** `map` and `strip` locate their source as the nearest resource of the action's `source-type`, searching the target itself first and then its parent links. So an action whose source type is the target's own type reads the target (the case of an entry event on the target with no trigger type), and `map(module, R, A)` on a new audit reads the audit's parent module. A rule that names a selector uses that resource instead, for each of its `map` and `strip` actions. Its realm is the realm in whose log the rule is in force or one of that realm's ancestors, never a descendant, and only that resource matches, so no other realm can substitute one of its own. A rule imported from a dependency realm has no selector (section 6.2). If it does not exist, or is not of an action's `source-type`, a change that fires the rule is rejected with `invalid-change`, so a `strip` is never skipped silently.

**Which party.** On `new`, `map` and `strip` read every party on the source. A rule fired by an entry event applies its `map` and `strip` actions only to the party of that event, as ESIS feeds only the changed entry to its rules. So a change on the source never grants again a role that was removed by hand from another party.

- A `strip` fired by a `remove` reads the roles that the party held on the source before the change; a `map`, and a `strip` fired by an `add` or `update`, read them after it. The roles a party holds on the source are its grants there in the realm of the change (section 3), ancestor realms' entries included. So `strip(module, R, A)` on `remove` takes the audit A from the party that held module R before the change, even when an ancestor's entry still gives it module R, and a `map` fired by a `remove` grants only what the party still holds on the source after the change: nothing when the removed entry was its only one there.
- A `replace` event fires rules as the `add`, `update` or `remove` that its roles before and after amount to: from none to some is `add`, from some to none is `remove`, otherwise `update`.
- Propagating a removal fully takes one `strip` per pair of held role and role (up to 16). A `strip` removes the role whatever granted it in the realm of the change, including a grant made by hand; a role that an ancestor realm grants is never stripped, and the change is rejected instead (section 3).

**Default rules.** The `sh.raci` realm ships a minimal default set that customer realms inherit and may override (section 6). It has one rule: on `new` of any type (`*`), `add-issuer(A)`, so the party that creates a resource is Accountable for it. This satisfies `min-ra` and the strict preset on a resource with no parent. Rules that map roles from another resource depend on customer-defined types or ids and are left to customer realms.

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

### 3.2 Default rule-management rules

Rule management is RACI too: a SteerSpec rule is a resource of type `rule`, and the `sh.raci` realm ships a default set for the activities on it. The activities are:

- `author`: create a rule, in state `D`.
- `update`: change a rule in state `D`, and add or change a note on a rule in any state. A rule that is no longer a Draft is immutable (SteerSpec RUL-007), so its notes are the only part that still changes.
- `publish`: move a rule into state `P`.
- `retire`: move a rule out of state `P` or `I`.
- `override`: author a rule that overrides an inherited rule.

The `sh.raci` realm declares these activities as a structured `activity-set` (RACIDMGT-001) and ships **no inference rule of its own** for them. The generic default (section 3.1) already gives the creator of a new `rule`, as of any resource, the role A on every activity. A rule-specific default such as R on `author` would add a second role for the same party and violate `one-role-per-party` under the strict preset, and the current inference actions cannot scope a generic default away from one resource type. A realm that wants the drafter kept apart from the approver assigns the roles for `publish`, `retire` and `override` explicitly, and may pair them with `author` in a `separation-of-duties` conflict with relation `same` (section 2.1).

## 4. Audit

Every change is an append-only event. Policy and rule changes (constraints, inference rules) are audited too, as separate event types, since they change the RACI system itself. Rules follow the SteerSpec lifecycle (section 6): a published rule is never edited, so these events are state transitions and supersessions, not edits. Nothing removes a complete line of a log. The one removal is an explicit doctor revert of a torn last line, which is logged with the removed bytes (section 4.1).

### 4.1 Event shape

One JSON object per event. Every event has a common envelope, a `type` discriminator (`entry`, `resource`, `constraint`, `rule`, `pin`, `revert` or `commit`), and a `payload` object whose shape the type selects. The type-specific members sit under `payload`, never beside the envelope, so a payload member can never collide with an envelope member. `schemas/raci-event-1.schema.json` is the machine-checkable form of this section. Draft.

Envelope (all types). Every member is required except `cause`:

- `raci`: the event format version, the string `"1"` for the format of this section (see **Format versions** below).
- `id`: the event id, a UUIDv7 in lowercase canonical text form (`xxxxxxxx-xxxx-7xxx-yxxx-xxxxxxxxxxxx`).
- `seq`: the per-realm sequence number. The first event of a realm has `seq` 1 and each later event the previous `seq` plus one, with no gap and no repeat, so a removed or reordered event is detectable even where the chain was re-linked, unless the events were also renumbered. Removing events from the end of the log leaves both `seq` and the chain valid: detecting that needs a head recorded outside the log, such as the view's `log` member (`view-ahead`, section 7).
- `ts`: the time the CLI wrote the event, RFC 3339 in UTC with millisecond precision and the `Z` suffix, e.g. `2026-11-21T10:00:00.000Z`. It is informational: order is `seq`, never `ts`.
- `realm`: the id of the realm that owns the log (section 1.1).
- `type`: the discriminator above.
- `change_id`: a UUIDv7 grouping the original change with every inferred change it produced (the transaction).
- `actor`: `{party, via}`, the party (section 1.1) and how the change arrived: `via` is `user`, `agent`, `import` or `inference`.
- `cause`: `{rule_id, event_id}`, the inference rule and the originating event. Present exactly when `actor.via` is `inference`, absent otherwise. Inferred events are never causes, which makes non-recursion verifiable from the log.
- `constraints`: an object that maps the name of each enabled constraint that was evaluated to `pass` or `fail`, e.g. `{"min-ra":"pass"}`. Canonical JSON fixes the order of the names and allows none to repeat: a log line that repeats one is not an event (`hash-mismatch`, section 7.1). Always present; an empty object states that no constraint was evaluated (e.g. on a `pin` or `commit` event). An event whose outcome is `applied` has no `fail`.
- `outcome`: `{status, reason, detail}`. `status` is `applied` or `rejected`. `reason` is present exactly when the status is `rejected` and is one of: `constraint-violation` (this event failed an enabled constraint, including `min-ra` on a new target that no inference rule matched, section 3.1, and a failed revalidation of an ancestor or descendant realm, section 2), `no-rules-in-force` (section 6), `invalid-change` (the change is malformed, e.g. it names an unknown resource), `change-rejected` (this event caused no rejection itself, but another event of the same change did). `detail` is optional free text on a rejected outcome, e.g. the realm and the constraint of a failed revalidation.
- `payload`: the type-specific object below.
- `hash`, `prev_hash`: `hash` is blake3 over the canonical JSON of the event without the `hash` member and with `prev_hash` included. **Canonical JSON** throughout this specification is RFC 8785 (JCS): keys sorted, no insignificant whitespace, defined string escaping and number formatting. Every digest in the log and in the `.raci` file (`hash`, `prev_hash`, `body_hash`, `head_hash`, a pin's `digest`) is the string `blake3:` followed by 64 lowercase hexadecimal characters, as in SteerSpec's `rule_set.hash`. The first event of a realm has the all-zero `prev_hash`, `blake3:` followed by 64 zeros.

Payload for `type: entry`:

- `op`: `add`, `update`, `remove` or `replace`.
- `target`: `{activity, party, resource}`, with `resource` a reference `{realm, id}` (section 1.1).
- `before`, `after`: the role sets, each a string of the held roles in the fixed order A, R, C, I (the form of the `.raci` file, section 7), the empty string for none. A `remove` has `after` `""`; materialisation and replay treat the entry as absent from that point, and the earlier events stay in the log.
- `conflict` (optional): `{kept, dropped}`, the rule ids of the winning and the discarded delta, when stricter-wins resolution applied (section 3.1).
- `replace` is linked `entry` events (the one losing the role and the one gaining it), both with `op` `replace`, sharing one `change_id`, made atomic by the commit marker below.

Payload for `type: commit`:

- `events`: the ids of the other events of the change, in log order. The commit marker is appended last, after all other events of the change, and carries the change's `change_id` and `outcome` in its envelope.
- `findings` (optional, non-empty when present): non-blocking findings, each `{code, detail}`, e.g. `no-matching-rule`.
- Replay applies a change only if its commit marker is present **and** has `outcome.status` `applied`. Events of a rejected marker are ignored for materialisation but stay in the log as the record of the rejection. The events of a change are consecutive. A change with neither a marker nor an applied `revert` that abandons it (for example after a crash) is incomplete: it is never applied, it is reported as `incomplete-change`, and the log cannot be replayed until it is reverted (see **Doctor and revert** below).

A change is **all or nothing**. If the original change or any change inferred from it violates an enabled constraint, or is otherwise rejected, the whole `change_id` is rejected: nothing applies. Each event that causes the rejection is logged with its own reason (for a violation, `constraint-violation` and the failing constraint in its `constraints`), every other event of the change with `change-rejected`, and the commit marker with `status` `rejected` and the reason and detail of the first causing event in log order.

Payload for `type: resource`:

- `op`: `new` or `delete`.
- `resource`: `{id, type, parent}`. `id` is bare, as this is the declaration and its realm is the envelope's `realm`. `parent` is optional, a reference `{realm, id}`. A `delete` repeats the declaration and is followed by its removals (section 1.2).
- A resource event can be the `cause` of inferred entries (e.g. `add-issuer` on `new`).

Payload for `type: constraint`:

- `constraint`: the constraint name (e.g. `single-accountable`, `separation-of-duties`).
- `op`: `enable` or `add-pair` (tighten-only, so there is no disable or remove).
- `params`: present exactly for `add-pair`, which is valid only for `separation-of-duties`: one conflict pair (section 2.1). `add-pair` is how that constraint is switched on, so `enable` takes the other four.

Payload for `type: rule`:

- `rule_id` (section 1.1), `revision` (the SteerSpec rule revision, an integer), `state` (the SteerSpec lifecycle state of the rule as of this event: `D`, `A`, `P`, `I`, `R` or `T`).
- `transition` (optional): the lifecycle state change `{from, to}` this event records, with `to` equal to `state`. A rule imported by an init or a version change (section 6.2) records its state with no transition, since the change happened in the dependency realm.
- `supersedes` (optional): the id of the rule this rule replaces, when it replaces one.
- `format`: the payload format of `body`, `raci/1` in format version 1. `body_hash` does not cover it; the event's `hash` does. A structured source matches a `rule` event only if both its format and its payload are the same (`unrecorded-rule`, section 7.1).
- `body`: the full structured rule body, the parsed `raci/1` payload object (section 6.1), so replay is self-contained, and `body_hash`, blake3 over the canonical JSON of `body` alone, to verify the rendered SteerSpec rule and the authoring source against it.

Payload for `type: pin`:

- `dependency_realm`, `version`: the dependency realm (e.g. `sh.raci`; distinct from the envelope's `realm`, which is the realm that owns the event) and the version, a semantic version `MAJOR.MINOR.PATCH`, that this realm's rules are evaluated against from this event on (section 6.2).
- `digest`: the digest of the content that the version resolved to (section 6.2).
- `op`: `set`. A later `pin` event for the same `dependency_realm` replaces the earlier one. Replay derives the realm's current pins from these events, so `pins` in the `.raci` file (section 7) is reconstructible and verifiable. An applied `pin` also takes every rule qualified by that realm out of force: the `rule` events after it in the same change are the whole imported set (section 6.2).

Payload for `type: revert`, written only by a doctor revert (below), with at least one of:

- `removed`: the exact bytes of the torn last line that was removed, in base64 (RFC 4648 section 4, padded).
- `abandoned`: the `change_id` of the unfinished change immediately before the revert. Its events stay in the log and are never applied. A `revert` that names any other change is not a valid event (`hash-mismatch`).
- A revert is a change of its own: its `outcome` is `applied`, its `constraints` is empty, its `actor.via` is `user` or `agent`, and its commit marker follows it. It changes no RACI state.

**Format versions.** This section is version `1` of the event format. It is independent of the `raci` member of the `.raci` file (section 7) and of the payload format (section 6.1), though each event version names the payload formats it allows. Version 1 and `raci/1` are frozen from the first release of the `raci` CLI that writes logs. Until then they may change in place. From then on any change to the set of valid events is a new version, so admitting `raci/2` payloads makes event version `2`. A log may hold events of several versions.

- Every version keeps the members `raci`, `seq`, `prev_hash` and `hash`, the definition of `hash`, and the line format of the log file, so any verifier can check the chain of any log.
- Verification reads `raci` before it validates the event against that version's schema. A line whose `raci` is missing, or is not a string holding a positive decimal integer without leading zeros, is not an event (`hash-mismatch`).
- A version the verifier does not support is reported as `unsupported-version`, once, for the first such event. The verifier still checks `hash`, `prev_hash` and `seq` along the whole log, but does not replay it, so beside that finding it reports only `hash-mismatch`, `seq-mismatch`, `torn-line`, `view-ahead` and `stale-view` for that log. A CLI never appends to such a log and never rebuilds its view.
- **Fail closed.** A log with any of `unsupported-version`, `hash-mismatch`, `seq-mismatch`, `torn-line`, `incomplete-change`, `view-ahead`, `pin-mismatch`, `pin-downgrade` or `dangling-reference` cannot be replayed. Nothing appends to it or rebuilds its view, other than a doctor revert where one is allowed, and its view is never used as an input in its place. A command that evaluates a change or answers from RACI state fails, writes nothing and exits with 2 when any log it depends on (its own, an ancestor's, a source's, a descendant's that it revalidates or that a delete checks (section 1.2), or one whose grants a constraint that it evaluates or revalidates counts, a sibling's included, section 2) cannot be replayed. This is a failed command, not a rejected change. Verification reports such a log that it reads with that log's realm in the finding's `realm`.

**Log file.** The offline log of a realm is a file named after its view with `.jsonl` appended: `.raci` and `.raci.jsonl` side by side. It is UTF-8 without a byte order mark. Each line is one event in canonical JSON followed by a line feed (U+000A), including the last line, and there are no blank lines. A last line without its line feed is torn (a crash during a write). It is not an event, even if it parses as one: it is never applied and is reported as `torn-line`.

**Doctor and revert.** A damaged log is never repaired automatically or as a side effect of another command.

- `raci doctor` diagnoses and writes nothing. It writes only when a revert is explicitly requested.
- A revert is allowed only when the sole damage is a torn last line, an unfinished last change, or both. For any other damage, including `view-ahead`, it refuses, writes nothing and exits with 2. Version 1 defines no repair for those.
- A revert keeps every complete line byte for byte and never re-chains. It removes the torn bytes, if any, then appends a `revert` event recording what it removed and what it abandons, and that event's commit marker, chained to the last complete line. It replaces the file atomically, so a crash leaves either the damaged log or the reverted one, and then rebuilds the view.
- A commit marker that lacks only its line feed is torn too: the revert removes it and abandons its change, which is therefore not applied.

### 4.2 Rules

- **Rejected changes are logged** (`outcome: rejected`), not only applied ones.
- **Tamper evidence:** a per-realm hash chain via `prev_hash`, identical for the offline log and the cloud store. Verification recomputes every `hash` and checks each `prev_hash` link, failing at the first mismatch, and checks that `seq` runs from 1 without gap or repeat (`seq-mismatch`, section 7.1). It also checks each `rule` event's `body_hash` against its `body`, and against the rendered SteerSpec rule and the authoring source (section 6).
- **Source of truth:** the log is the source and the `.raci` file is a materialised view that can be verified by replay, and rebuilt from any log that can be replayed (section 4.1).
- **One realm per change:** a change and everything inferred from it are written to the log of the realm where the original change lands. Resources in ancestor realms can be read as sources, and other realms of the tree are read as section 2 requires, but none is written by that change. So a `change_id`, its commit marker and the hash chain never span two realms.
- **Offline storage:** one JSONL log per realm, next to the `.raci` file; the CLI is its only writer. Offline mode is single-writer per realm. Concurrent clones diverge the hash chain, and merging them is deferred (open); multi-writer is the cloud mode's job. Git history is not a substitute, as it does not record rejected attempts or causes.

## 5. Out of scope

RACI.sh manages RACI. Enforcing it is the customer's job. The service can answer "who is R/A/C/I" and "does this change violate a constraint", not "may this call proceed".

## 6. SteerSpec mapping

- RACI.sh rules (constraints, inference rules, default rule-management rules) have a **structured source** that the `raci` CLI evaluates deterministically. It is the authoring format. The canonical record of which rule was in force is the audit log (section 4.2): loading a new or changed structured rule source appends a `rule` event carrying the full structured body, and the CLI evaluates only rules recorded in the log. A structured source that differs from the latest `rule` event for the same rule id in the log, or for which the log has no `rule` event for that rule id, is reported as unrecorded and not evaluated.

**Bootstrap.** A realm's log starts empty, and until rules are recorded nothing is in force, so entry changes are rejected with `no-rules-in-force`. An explicit init appends a `pin` event for each dependency realm (e.g. `sh.raci`), then `rule` events (actor `import`) for the in-force rules that have a structured source, of the pinned versions and of the realm's own entities. Every later change of a pinned version appends a `pin` event and a `rule` event for every rule with a structured source that is in force in the new version, unchanged ones included, so inherited rules are recorded in the log of the realm that uses them.
- The specification is **hand-authored as normative prose rules** in the `sh.raci` realm (`RACI`, `RACICNS`, `RACIINH`, `RACIINF`, `RACIAUD`, `RACIFILE`, `RACIMGT`), with SteerSpec ids, lifecycle states and supersession. The default configuration rules (the strict preset, separation of duties, default inference and rule-management rules) are **rendered into SteerSpec rules** from their structured source: prose `MUST` bodies, plus notes carrying the structured form. A rendered rule is derived, never hand-edited.
- Rendering to prose gives the SteerSpec/LLM path (CI gates, advisory review of rule changes) without making enforcement depend on an LLM. Deterministic checks reject; the LLM path only reviews.
- Customer realms depend on `sh.raci` like any SteerSpec realm and customise by authoring structured rules in their own realm, which are rendered to SteerSpec rules like the defaults. They add rules or override inherited ones, subject to the override lint in section 3.
- The payload format of the structured source is section 6.1, and realm versions and sources are section 6.2. Open: the mapping of a payload into a rule body (rendering).

### 6.1 The `raci/1` payload format

The structured source of a RACI.sh configuration rule is the content of a SteerSpec `structured` note (core NTE-036 to NTE-041): `<format>:<payload>`, split at the first colon, with the format `raci/1`. SteerSpec treats the payload as opaque; this section defines it, and `schemas/raci-1.schema.json` is its machine-checkable form, and CI checks every `raci/1` note in `rules/` against it (`tools/check-payloads.py`). Draft.

- **Payload.** A JSON object in RFC 8785 canonical form (the form of the `.raci` file, section 7): sorted members, no insignificant whitespace, no duplicate member. The CLI canonicalises on load. The `body_hash` of a `rule` event (section 4.1) is the blake3 of this canonical payload.
- **Closed.** A payload has exactly the members its kind defines. An unknown kind, an unknown member or a missing required member makes the payload invalid: it is not evaluated, and loading it is an error, never silently skipped.
- **Versioning.** `1` is the version of this payload format. It is independent of the `raci` member of the `.raci` file (section 7), which versions that file, and of the `raci` member of an event (section 4.1), which versions the event. A `rule` event records the payload format as `format`. `raci/1` is frozen with event version 1 (section 4.1). From then on any change to the set of valid payloads, including a new kind or a new optional member, is a new format version (`raci/2`), because a closed evaluator rejects what it does not know.
- **Identity.** `kind` selects the payload shape. `name` labels the configuration item (a preset, a constraint, an inference rule, an activity set) and is a lowercase kebab-case word. In the audit log a rule is identified by its SteerSpec rule id (`rule_id`, section 4.1), qualified by the realm id when the rule comes from a dependency realm, as `<realm id>:<rule id>` (the form SteerSpec uses in `overrides`), so that two realms can each have an `-001`. A `name` is unique per kind among the in-force rules of a realm path, except where one rule overrides or supersedes another; the superseding rule keeps the name while its rule id changes.

| Kind | Members (required unless marked optional) | Meaning |
| --- | --- | --- |
| `preset` | `name`, `enable`: the constraint names to switch on (at least one, no repeats) | A named bundle of constraints (section 2). A preset cannot enable `separation-of-duties`, which needs conflict pairs. |
| `constraint-default` | `name`: a constraint name; `requires` (optional): `pairs` | The default configuration of one constraint. `requires: pairs` is valid only for `separation-of-duties`: it only takes effect together with a list of conflict pairs. |
| `inference` | `name`, `target-type`, `operation`, `actions`; `trigger-type` (optional) | An inference rule (section 3.1). |
| `conflict-pair` | `name`, `pair`: one conflict pair `{relation, a, b}` (section 2.1) | A separation-of-duties pair, in effect while the rule is in force. |
| `activity-set` | `name`, `resource-type`, `activities`: names, at least one, no repeats | The activities defined on a resource type (section 3.2). |

An **inference** payload follows section 3.1:

- `target-type` is a resource type or the wildcard `*` (only here). `operation` is `new`, `add`, `update` or `remove`. `trigger-type`, a concrete type, is allowed only with `add`, `update` or `remove`. `selector`, optional and allowed only with a `map` or `strip` action, is `{"realm": <realm id>, "id": <resource id>}` (section 3.1).
- `actions` is a non-empty list, in order. Each action has `action` (`map`, `add-issuer` or `strip`), an optional `activity` (absent means every activity on the target, section 3.1), and an optional boolean `add-only`. `map` also has `source-type`, `from-role` and `to-role`; `add-issuer` has `role` and is valid only when `operation` is `new`; `strip` has `source-type`, `held-role` and `role`. A `source-type` is a concrete type, never `*`. Roles are `R`, `A`, `C` or `I`.

**Not defined here.** The mapping from a payload to the prose body of a rendered rule (the rendering of section 6) is not defined yet: the default rules' bodies are authored by hand beside their payloads, and the rule that a rendered rule is never hand-edited takes effect with the renderer.

### 6.2 Realm versions and sources

How a realm names the version of a dependency realm it is evaluated against, and where the CLI gets it. Draft.

- **Id.** The default realm's id is `sh.raci`. Its source of truth is the `rules/` directory of `raci-sh/raci-spec`.
- **Version.** A realm's version is the `realm.version` of its `realm.json`, a semantic version `MAJOR.MINOR.PATCH`. For `sh.raci`, every release of `raci-sh/raci-spec` after `1.0.0` is tagged `vX.Y.Z` with `X.Y.Z` equal to `realm.version`; the release tooling bumps both together. The `rule_set.version` of each entity is SteerSpec's per-entity version and is unrelated to the realm version.
- **What a bump means.** Versions describe the effect on the rules in force (section 3), which is what a pin commits a realm to:
  - MAJOR: a change that can reject a change the previous version accepted, such as a constraint rule entering force or being tightened, or a rule in force being superseded, retired or terminated.
  - MINOR: any other change to the rules in force, such as a new inference rule.
  - PATCH: no change to the rules in force: Draft rules, notes, prose and schema descriptions.
  - Before `1.0.0`, a MAJOR change bumps MINOR instead.
- **`v1.0.0` is not a pin target.** That release predates this section, and at its tag `realm.version` is `0.1.0`. Declaring `1.0.0` fails the version check below, and declaring `0.1.0` from that tag fails the source check. The first version of `sh.raci` that can be pinned is the release after it.
- **Declaration.** A realm declares each dependency realm in the `dependencies` of its `realm.json`, as SteerSpec does: `realm_id`, `version` and `source`. For `sh.raci` the source is exactly `github://raci-sh/raci-spec@vX.Y.Z/rules`, with `X.Y.Z` the declared `version`. Any other owner, repository, ref or path is refused: there are no mirrors.
- **Fetch.** `raci init`, and every later change of a declared version, fetch each dependency realm from its declared `source` at its declared `version`. The CLI embeds no copy of any realm. The command fails, writes nothing and exits with 2 if a fetch fails, the source of `sh.raci` is not exactly the one above, the fetched `realm.json` has an `id` or `version` other than the declared one, or the content fails a digest check below.
- **Digest.** The digest of a fetched realm covers every file whose name ends in `.json` in the source directory and, recursively, its subdirectories. Each file is parsed and hashed as blake3 over its canonical JSON. The digest is blake3 over the canonical JSON of the object that maps each file's path to that hash, the path being relative to the source directory, with `/` separators. So an archive, a checkout and a cache of the same content agree: line endings, indentation and files of other types do not count. A symbolic link, or a `.json` file that is not I-JSON (RFC 7493, e.g. one with a repeated member), fails the fetch.
- **One content per version.** A declaration carries no digest, so the first pin of a version in a log trusts what its source serves, and is always made from a fetch, never from a cache. From then on, content for that realm and version, fetched or cached, must have the digest of the earlier applied `pin`, and a cached copy that has it may stand in for a fetch. A log with two applied pins of one realm and version but different digests is reported as `pin-mismatch` (section 7.1). Verification does not fetch, so a moved tag shows at the next fetch, or when two realms' pins are compared.
- **Pin.** The `version` of the resulting `pin` event (section 4.1) is the declared version string, exactly, and its `digest` is the digest of the content that was used.
- **Imported rules.** Each `rule` event that an init or a version change appends records the rule's `state` in the fetched realm, without a `transition`. Only rules in state `P` or `I` are recorded, since only they are in force (section 3), and the event schema accepts no other state on an import. So while every default rule of `sh.raci` is still a Draft, an init records none of them and the realm stays at `no-rules-in-force` until it records rules of its own.
- **Imported rules name resources by type only.** A dependency realm does not know the importer's resources, so a rule with a qualified id has no `selector` and no pair side by `{realm, id}`. The event schema rejects both. A fetched realm with such a rule in force is refused when it is fetched (exit 2, nothing written), rather than failing at every change that fires the rule.
- **A pin replaces the imported set.** The imported rules of a dependency realm are the rules whose id that realm qualifies (`<realm id>:<rule id>`), not every event with `via` `import`: an init imports the realm's own rules too. When replay applies a `pin`, it takes all of that realm's imported rules out of force, then applies the `rule` events that follow in the same change. So a version change records every rule in force in the new version, unchanged ones included, and a rule that was retired, terminated, superseded or dropped upstream leaves force. A qualified `rule` event always has `via` `import`, and one that does not follow a `pin` of its realm in the same change is not a valid event (`hash-mismatch`).
- **No downgrade, no unpin.** A pin never moves to a lower version, compared as semantic versions: the command fails, writes nothing and exits with 2, and a log that holds such a pin is reported as `pin-downgrade`. Rolling back takes a new, higher upstream release. Removing a declaration does not unpin: the pin and its rules stay in force, and version 1 has no unpin.
- **Upgrades and tighten-only.** An upgrade relaxes only what the dependency realm itself retired or changed. It never disables a constraint that a `constraint` event of this realm or an ancestor enabled (section 3).
- **One change.** The `pin` events and `rule` events that an init or a version change appends form one change, with one `change_id`, actor `via` `import`, and one commit marker, so a realm is never left half initialised.

## 7. The `.raci` file

The `.raci` file is a **materialised view** of one realm's audit log (section 4.2). It holds RACI and nothing else: no findings, no history. The CLI is its only writer and it is never hand-edited.

- **Encoding:** one canonical JSON document (RFC 8785, the same canonical form that the event hashes use, section 4.1). Output is deterministic, so the same log always yields byte-identical files. The example below is pretty-printed for reading; the stored file has no insignificant whitespace.
- **Scope:** the realm's own state. The entries and resources of other realms of the tree are read at load time (grants and revalidation, section 2) and never embedded, so the file cannot drift from its source. What is embedded about other realms is derived from this realm's own log: `pins` and `rules_in_force`, both recorded there (sections 4.1 and 6).
- **No paths:** the view carries no filesystem paths, so the same log yields the same bytes in any checkout. The log is found by convention, next to the `.raci` file (section 4.2).
- **Staleness:** `log.head_seq` and `log.head_hash` identify the log state the view reflects. A view whose head is an earlier event of the log, or the empty head, is stale and is rebuilt by replay. A view whose head cannot be read, or is not in the log (a higher `seq`, or another hash at that `seq`), means the log lost or changed events: it is `view-ahead`, the log cannot be replayed, and the view is never rebuilt over, as it is the evidence. A missing view has no head, so truncation of the log together with deletion or rewriting of the view is not detected by these files alone. For an empty log the head is `head_seq` 0 and `head_hash` the all-zero digest, the same sentinel as the first event's `prev_hash`.

Shape:

```json
{
  "constraints": {
    "enabled": [ "min-ra", "single-accountable" ],
    "pairs": []
  },
  "entries": [ { "activity": "<activity>", "party": "<party>", "resource": { "id": "<id>", "realm": "<realm id>" }, "roles": "AR" } ],
  "log": { "head_hash": "<hash of the head event>", "head_seq": 412 },
  "pins": { "<dependency realm>": { "digest": "<digest>", "version": "<pinned version>" } },
  "raci": "1",
  "realm": "<realm id>",
  "resources": [ { "id": "<id>", "parent": { "id": "<id>", "realm": "<realm id>" }, "type": "<type>" } ],
  "rules_in_force": [ { "body_hash": "<hash>", "revision": 2, "rule_id": "<id>" } ]
}
```

- `roles` is a string of the held roles in the fixed precedence order A, R, C, I (section 1), so `"AR"`, never `"RA"`. An entry with no roles is absent, not stored empty.
- Object members are in the canonical (sorted) order, as in the example. Array ordering is canonical too, strings comparing by code point: `resources` by `id`, all of this realm (`parent` is absent when there is none); `entries` by (`resource.realm`, `resource.id`, `activity`, `party`); `rules_in_force` by `rule_id`; `enabled` alphabetically; `pairs` by their canonical JSON.
- `rules_in_force` lists every rule recorded in force in this realm's log (section 6, including inherited ones) with its `body_hash`. Verification compares these with the log's `rule` events and with the structured rule sources without replaying the whole log.
- `pins` is an object keyed by dependency realm id, so it holds one pin per realm in canonical order. It is derived from the log's `pin` events (section 4.1): the current version and digest of each dependency realm the log was evaluated against (e.g. the `sh.raci` version). Verification recomputes it by replay.
- `constraints` lists the constraints recorded by this realm's own `constraint` events. The effective set (the union along the realm path, section 3) is computed at load and not embedded.
- `pairs` holds the pairs of this realm's own `add-pair` events, each with the side whose canonical JSON sorts first as `a`, and without repeats. `enabled` lists `separation-of-duties` exactly when `pairs` is not empty. Pairs from rules are not embedded: their rules are in `rules_in_force`, and their bodies in the log.
- `resources` and `entries` use the identifier forms of section 1.1, `pins` the semantic versions of section 6.2. `schemas/raci-view-1.schema.json` is the machine-checkable form of this shape; it checks the order of `enabled`, whose values are a closed set. It cannot check the other array orders: replay gives them, and a file in another order is a `view-mismatch`.

### 7.1 Verification report

Findings are not part of `.raci`. `raci verify` computes them on demand and emits a separate report, and nothing about it is persisted in the view.

```json
{ "realm": "<realm id>", "log_head": { "seq": 412, "hash": "<hash>" },
  "findings": [ { "code": "<code>", "severity": "error", "realm": "<realm id>", "detail": "<text>" } ] }
```

| Code | Severity | Meaning |
| --- | --- | --- |
| `hash-mismatch` | error | A recomputed `hash` or a `prev_hash` link of the log fails, or a complete line of the log is not a valid event (sections 4.1 and 4.2). |
| `seq-mismatch` | error | The `seq` of the log does not run from 1 without gap or repeat (section 4.1). |
| `unsupported-version` | error | An event has a format version that the verifier does not support, so the log is not replayed (section 4.1). |
| `pin-mismatch` | error | Two applied pins of the same dependency realm and version have different digests (section 6.2). |
| `pin-downgrade` | error | An applied pin has a lower version than an earlier applied pin of the same dependency realm (section 6.2). |
| `torn-line` | error | The last line of the log has no line feed (section 4.1). |
| `view-ahead` | error | The view's log head cannot be read or is not in the log, so the log lost or changed events (section 7). |
| `dangling-reference` | error | An entry or a parent link references a resource that is not live in the log's realm or an ancestor (section 1.1). |
| `view-mismatch` | error | Replaying the log gives a different state, or different bytes, than the `.raci` file. |
| `stale-view` | warning | The view's log head is an earlier event of the log; rebuild by replay. |
| `unrecorded-rule` | error | A structured rule source differs, in format or payload, from the latest `rule` event for the same rule id in the log, or for which the log has no `rule` event for that rule id, so it is not evaluated (section 6). |
| `incomplete-change` | error | A `change_id` has events but neither a commit marker nor an applied revert that abandons it (section 4.1). |
| `no-matching-rule` | warning | A target was created with an empty RACI because no inference rule matched. |
| `descendant-violation` | error | A realm outside the change's tree, which depends on this one, now violates a constraint (section 2). |

A commit marker's `findings` (section 4.1) are the subset recorded at change time. The report carries them with `severity` and `realm` added, next to the findings that only a fresh verification can produce.

- The set of codes is closed and each code has the fixed severity of the table. `schemas/raci-report-1.schema.json` is the machine-checkable form of the report.
- `findings` is sorted by (`severity`, `code`, `realm`, `detail`), so errors come first and the same log and view always yield the same report.
- `raci verify` exits with 0 when the report has no finding of severity `error` (warnings allowed), 1 when it has at least one, and 2 on a usage or configuration error, when no report is produced.

## Open questions

Tracked in beads (`bd list`): rendering payloads into rule bodies, and merging concurrent offline logs.
