# Issue #232 — Slice 02 distribution

- Workflow: `issue-232-20260808`
- Slice: `02` — Application ports and local file-storage boundary
- Execution profile: `FULL_PATH`
- Dependency state: Slice 01 checkpoint `aa510b82523d5decefb88c21ee5a7fe74226d716` is complete and pushed.
- Scheduling: serial; parallel execution rejected because application port contracts,
  readiness result schemas and local-storage capabilities share locks.

## Execution streams

No callable Codex subagent interface is available in this execution context.
The required specialist review is therefore performed as an explicit role-based
fallback in the main execution thread:

| Stream | Role | Scope | Expected files |
|---|---|---|---|
| backend | Senior Python Automation Developer | define the smallest inward-facing storage and readiness contracts | `src/tiny_swarm_world/application/ports/**`, `src/tiny_swarm_world/domain/inventory/**`, `src/tiny_swarm_world/domain/preflight/**` |
| tests | Senior Tester | verify contract typing, redaction, scope distinction and adapter compatibility | `tests/application/ports/**`, `tests/domain/inventory/**`, `tests/infrastructure/adapters/file_management/**` |
| architecture | Senior System Architect | review inward dependencies and prevent concrete I/O leakage | application ports, domain models, architecture tests |
| requirement | Senior Requirement Engineer | map REQ-004, REQ-009, REQ-011 and REQ-017 to implementation and evidence | requirement matrix and slice evidence |
| security | Senior DevOps / security review | check bounded-operation metadata and secret-safe outcomes | readiness result model and tests |

No frontend, live infrastructure, Docker deployment, registry bootstrap or
external integration stream is authorized for this slice. No separate worktrees
are used because the workflow explicitly serializes this contract boundary.

## Constraints and consolidation

- Keep concrete `Path`, YAML parsing, permission and atomic-write details in
  infrastructure adapters.
- Extend `PortLocalFileStorage` only for a verified preflight capability; do not
  add broad filesystem traversal or mutation methods.
- Keep live readiness observations behind typed application ports and safe domain
  outcomes; credentials, raw command output and response bodies are forbidden.
- Run focused tests first, then the required targeted gates and the full quality
  gate before the slice checkpoint commit.
- Record the independent role-based architecture, tester and requirement review
  in the consolidation evidence.
