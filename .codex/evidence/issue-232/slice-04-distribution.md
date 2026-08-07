# Issue #232 — Slice 04 distribution

- Workflow: `issue-232-20260808`
- Slice: `04` — Static artifact-contract preflight service
- Execution profile: `FULL_PATH`
- Dependency state: Slice 03 checkpoint `2116401` is complete and pushed.
- Scheduling: serial; static preflight, setup phase ordering, composition and
  artifact workflow locks must be changed and verified together.

## Execution streams

No callable Codex subagent interface is available in this execution context.
The required specialist review is therefore recorded and performed as a
role-based fallback in the main execution thread:

| Stream | Role | Scope | Expected files |
|---|---|---|---|
| backend | Senior Python Automation Developer | implement non-mutating static inventory/context preflight | artifact application service, setup composition, installation plan |
| tests | Senior Tester | prove success/failure, missing context, no-mutation and phase stop behavior | artifact and setup tests |
| architecture | Senior System Architect | keep YAML/path details behind ports and keep entry point thin | application ports, service, composition |
| requirement | Senior Requirement Engineer | map REQ-007, REQ-010, REQ-013, REQ-017 and REQ-021 | requirement matrix and slice evidence |
| security | Senior DevOps / security review | verify static path never invokes Docker, HTTP, registry, Nexus or credentials | mocks, composition and phase tests |

No frontend, live infrastructure, Docker deployment, registry bootstrap or
external integration stream is authorized for this slice. No separate worktrees
are used because the workflow explicitly serializes phase ordering and shared
artifact locks.

## Constraints and consolidation

- Static validation must consume typed Compose inventory and the local storage
  port only; it must not call artifact publishers or live readiness adapters.
- Build context paths are resolved by the infrastructure repository adapter and
  checked through `PortLocalFileStorage.directory_exists()`.
- A failed static result must stop setup before `artifacts prepare`,
  `artifacts verify` and deployment phases.
- Phase results must remain safe for setup serialization and evidence output.
- Run focused service/phase tests, targeted architecture/type checks and the
  full quality gate before checkpoint commit.
