# Issue #189 — S189-02 Distribution Decision

- Workflow: `issue-189-20260809` / `issue-189-v1.0.0`
- Slice: `S189-02` — Shared resolver/utilities and consumer migration
- Execution branch: `feature/centralize-lxc-shared-utilities-solid`
- Profile: `FULL_PATH`
- Prerequisite: `S189-01_READY_FOR_S189-02`
- Scope correction: S189-01 found twelve mapping definitions, so the active
  slice metadata was expanded to cover every verified mapping consumer before
  product edits. The workflow and source workflow were rechecked together.
- Chosen execution mode: `sequential`
- Real subagents used: `no`; no callable project-subagent tool is exposed in
  this environment.
- Fallback role-based review: `yes`; Codex applies the required role and skill
  instructions in the main execution thread and remains final integration
  owner.

## Stream assessment

| Stream | Owner/reviewer | Decision | Scope |
|---|---|---|---|
| Backend/Python | Senior Python Automation Developer | active | Resolver, verified helper extraction, consumer migration and composition wiring. |
| Architecture | Senior System Architect | active review | Infrastructure-only imports, boundary ownership and compatibility seams. |
| Tests/quality | Senior Tester | active review | Focused resolver/helper/consumer tests, architecture tests and targeted gates. |
| Security | Senior Security Sandbox Engineer | active review | Diagnostics redaction, shell quoting, timeout and evidence safety. |
| Documentation | Senior Documentation Engineer | conditional | Arc42 remains planned-only until implementation evidence is verified. |
| Runtime/DevOps | Senior DevOps Engineer | review-only | No live Incus/LXD/Docker/Swarm operation; runtime behavior is mocked. |
| Requirement/orchestration | Senior Requirement Engineer / Senior Execution Orchestrator | active review | Matrix traceability, lock/order enforcement and stop decisions. |
| Frontend/console | N/A | not applicable | No browser React or terminal UI surface is in the declared slice. |

## Lock and parallelization decision

Parallel execution is rejected. The resolver and utilities are a shared
contract migration touching multiple LXC adapters, composition wiring and
tests. The inventory established mandatory ownership decisions before edits;
splitting these files would permit duplicate mappings or incompatible helper
contracts. No live infrastructure stream is authorized.

Expected product paths are the LXC command package, the declared legacy
consumer adapters, composition and their nearest tests. Expected evidence is
`.tiny-swarm/evidence/solid-lxc-shared-utilities/`,
`.tiny-swarm-world/evidence/solid-lxc-shared-utilities/` and this workflow-
specific `.codex/evidence/issue-189-20260809/` directory.

## Implementation constraints

- Resolve all backend CLI consumers from the S189-01 inventory before removing
  a local mapping.
- Preserve `incus`/`lxc` values, adapter-owned retries/failure policy,
  compatibility imports and the existing composition root.
- Do not move domain/application imports, Docker byte-stream policy, preflight
  registry behavior or service-specific error classification into a generic
  helper.
- Add focused tests before claiming the slice ready for S189-03.
