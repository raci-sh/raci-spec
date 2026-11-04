# RACI.sh

RACI for agents: who is Responsible, Accountable, Consulted and Informed for activities carried out on resources, per realm.

RACI.sh is a companion service for [SteerSpec](https://github.com/SteerSpec). It is not mandatory. It works offline, repo-based, with a Go CLI (`raci`) and a `.raci` file, or embedded in SteerSpec. It also works online on Cloudflare (Workers + D1/KV), with CI gates and MCP access. The service manages RACI; enforcing it is the customer's job.

Status: brain dump stage. See [BRAINDUMP.md](BRAINDUMP.md) (2026-11-04).

## Conventions

- Commits follow [Conventional Commits](https://www.conventionalcommits.org/). `npm install` once to get the local `commit-msg` check; CI runs commitlint on every PR and push to `main`.
- Versions follow semver. [release-please](https://github.com/googleapis/release-please) keeps a release PR open from the `feat:` and `fix:` commits on `main`; merging it tags the release and updates `CHANGELOG.md`.
- Issues live in [beads](https://github.com/gastownhall/beads) (`bd ready`, `bd create`, `bd close`). On a fresh clone run `bd bootstrap --yes`. See `AGENTS.md`.
