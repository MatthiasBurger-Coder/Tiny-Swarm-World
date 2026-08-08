# Issue #232 — Slice 05 distribution

- Workflow: `issue-232-20260808`
- Slice: `05` — Infrastructure adapters for bounded live readiness
- Execution profile: `FULL_PATH`
- Dependency state: Slice 04 checkpoint `87a906f` is complete and pushed.
- Scheduling: serial; readiness result contracts, external-I/O adapters and
  composition locks are shared and must be consolidated together.

## Execution streams

No callable Codex subagent interface is available in this execution context.
The required specialist review is therefore recorded and performed as a
role-based fallback in the main execution thread:

| Stream | Role | Scope | Expected files |
|---|---|---|---|
| runtime | Senior DevOps Engineer | bounded Docker/HTTP readiness adapters and safe classification | `infrastructure/adapters/preflight/**`, `infrastructure/adapters/clients/**` |
| backend | Senior Python Automation Developer | preserve `PortLiveReadiness` and typed readiness outcome contracts | application ports and adapter boundaries |
| tests | Senior Tester | mock command/HTTP probes and distinguish timeout/unavailable/unknown | `tests/infrastructure/adapters/**` |
| architecture | Senior System Architect | keep all external I/O in infrastructure and prevent result leakage | import/architecture checks |
| requirement | Senior Requirement Engineer | map REQ-008, REQ-009, REQ-011, REQ-019, REQ-020 and REQ-021 | requirement matrix and slice evidence |
| security | live-evidence review | reject credentials, raw output and response bodies in evidence | redaction tests and review |

No live command, Docker deployment, registry bootstrap, Nexus mutation, Incus
operation or external integration is authorized for this slice. No separate
worktrees are used because the workflow serializes readiness contract changes.

## Constraints and consolidation

- Require explicit target coverage for manager Docker, registry/Nexus endpoint,
  repository state, manager storage, build inputs and public pull prerequisites.
- Pass only bounded timeout/attempt parameters across the port.
- Keep unavailable, timed-out, failed and unknown outcomes distinct from ready.
- Use injected runners/openers in tests; normal tests must not reach live
  infrastructure.
- Run focused tests, lint, architecture, typecheck and full quality before the
  checkpoint commit.
