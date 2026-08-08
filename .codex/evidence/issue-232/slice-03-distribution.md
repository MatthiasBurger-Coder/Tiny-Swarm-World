# Issue #232 — Slice 03 distribution

- Workflow: `issue-232-20260808`
- Slice: `03` — Profile inventory, Compose alignment and override resolution
- Execution profile: `FULL_PATH`
- Dependency state: Slice 02 checkpoint `2004c17` is complete and pushed.
- Scheduling: serial; Compose parsing, profile selection, image override
  resolution and contract alignment share the same repository/composition locks.

## Execution streams

No callable Codex subagent interface is available in this execution context.
The required specialist review is therefore recorded and performed as a
role-based fallback in the main execution thread:

| Stream | Role | Scope | Expected files |
|---|---|---|---|
| backend | Senior Python Automation Developer | expose profile-scoped Compose image requirements and one effective override path | Compose port/repository, deployment value objects, composition |
| tests | Senior Tester | cover default/service-access profiles, all supported overrides, drift and missing contracts | Compose and composition tests |
| architecture | Senior System Architect | keep YAML parsing in infrastructure and preserve composition-root ownership | application port, repository adapter, architecture checks |
| requirement | Senior Requirement Engineer | map REQ-001, REQ-002, REQ-004, REQ-005, REQ-006, REQ-014, REQ-015, REQ-016 and REQ-017 | requirement matrix and slice evidence |
| security | Senior DevOps / security review | reject implicit latest, unsafe context resolution and divergent override paths | image resolver and contract inventory |

No frontend, live infrastructure, Docker deployment, registry bootstrap or
external integration stream is authorized for this slice. No separate worktrees
are used because the workflow explicitly serializes this shared contract work.

## Constraints and consolidation

- Compose YAML remains an infrastructure concern; application code receives
  typed image requirements through `PortComposeFileRepository`.
- Profile selection must come from the existing `ServiceStackProfile` contract,
  not inferred from runtime state.
- Every supported `TSW_*_IMAGE` override must feed both effective Compose
  inventory and artifact contracts through one resolver.
- Missing, duplicate or mismatched image contracts remain static failures and
  must not trigger artifact mutation.
- Run targeted repository/composition tests and typecheck first, then the full
  quality gate before the slice checkpoint commit.
