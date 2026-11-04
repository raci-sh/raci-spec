# RACI.SH — brain dump (2026-11-04)

Philippe's initial notes, grouped under light headings. The wording is kept as written.

## Purpose

- How to orchestrate agents to let an agent know about something or say what it owns.
- RACI on Activities carried on Resources, and RACI per agent.
- RACI for SteerSpec rules: who must be informed when a rule changes, consulted for changes, etc.
- See jRACI, and ESIS (https://sourceforge.net/projects/esisframeworks/), etc.
- Keep it minimalist whilst powerful — past ESIS experience.

## Concepts

- Match the notion of realm as in SteerSpec.
- RACI are SteerSpec rule defined as well as rule for their management by a default set of rules, which user can customise (inheritance).
- When matching SteerSpec and RACI realm then the ref is either local (raci-CLI) or cloud (raci-cloud) with CI gates.
- See RACI inheritance that we had in ESIS, to infer a sub RACI based.
- Full RACI change auditability.
- Parties that need to be notified → MCP access to inbox (notifications).
- Use AI, LLM but also decision like Clef to answer RACI based questions; see for RACI conflict (Alice is R on Acme so can't be A on Emca as then it would violate the rule enforcing separation of duties).

## Use cases

1. **SteerSpec rule management.** Who can modify a rule, who owns (A) the rule, who oversees (R), etc. Rely on the IdP and map a realm, sub-realm or ruleset to a RACI. List standard activities (add, update, etc.) and use RACI.
2. **Escoffier brigade in lizher-dev.** Which agent is responsible for what, with which scope. Scopes are RACI: activities on resources with agents (Agent Chef is Accountable for Billing, Agent Bob is Responsible, Agent Alice must be Informed, etc.).

## Architecture

- RACI.sh can be offline, repo based, with a raci-CLI and either a `.raci` file and/or embedded into SteerSpec.
- RACI.sh is also online with Cloudflare — should work with a simple D1 db and worker.
- Cloud is D1 or KV to store the RACI, one set of workers to manage RACI, one set of workers to query RACI. The service only enforces the management of RACI; the enforcement of RACI is the responsibility of the customer.
- Use Go for the CLI, with a pure local part and support for the cloud part, so just one tool.
- UI is limited to sign-up, subscription and billing management, authentication / OAuth / secrets. All the rest is CLI and MCP.

## Business

- Cloud is freemium with a limit on realms, RACI, rules. It is a companion service for SteerSpec but not mandatory at all. Paid plans above.
