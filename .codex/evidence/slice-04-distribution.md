# Slice 04 Distribution Decision

Workflow: `issue-183-20260808`
Slice: `04` — Extract Docker, service clients, image publisher, and errors

## Affected areas

* `LxcContainerRuntime` and its Docker command behavior;
* LXC Portainer admin/client and Nexus HTTP wrappers;
* LXC image publisher and rejection/error types;
* compatibility exports and the existing adapter test surface.

## Execution decision

* Chosen mode: `sequential`.
* Real Codex subagents used: `No callable subagent surface is available.`
* Fallback role-based review used: `Yes`.
* Git worktrees used: `No`; all extracted classes and compatibility imports
  share the legacy module and its test patches.
* Selected streams: backend extraction, tests, architecture, and security/
  error-mapping review.
* Documentation and live-runtime streams: review-only.

## Fallback role review

* Senior Python Automation Developer: move each cohesive adapter into its
  declared package without changing constructor or port behavior.
* Senior System Architect: keep the LXC Docker-engine runtime distinct from
  `LxcContainerRuntime` and preserve application ports.
* Senior Tester: preserve subprocess, HTTP session, timeout, cleanup, status,
  and exception-identity seams with mock-only tests.
* Senior Security Sandbox Engineer: preserve credential redaction, safe HTTP
  error messages, registry diagnostics, and operator-action text.

## Expected touched files/directories

* `src/tiny_swarm_world/infrastructure/adapters/clients/lxc/docker/`
* `src/tiny_swarm_world/infrastructure/adapters/clients/lxc/services/`
* `src/tiny_swarm_world/infrastructure/adapters/clients/lxc/images/`
* `src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py`
* `tests/infrastructure/adapters/clients/lxc/`
* `.codex/evidence/slice-04-distribution.md`
* `.codex/evidence/slice-04-consolidation.md`

## Conflict risks

The legacy classes share helper functions, shell seams, HTTP validation, and
error types. Existing tests patch the old module path after construction. The
extracted modules must use dynamic compatibility callbacks where needed and
must not merge this LXC Docker runtime with the separate Docker-engine runtime
adapter.

## Quality gates

* focused Docker, Portainer, Nexus, image-publisher, and compatibility tests;
* `python3 tools/quality_gate.py lint`;
* `python3 tools/quality_gate.py typecheck`;
* `python3 tools/quality_gate.py arch-lint`;
* `python3 tools/quality_gate.py arch-tests`;
* `git diff --check`.

## Consolidation plan

Codex will inspect package ownership, compatibility exports, error identity,
credential handling, and the distinction from the existing Docker-engine
runtime; then run focused gates and create one Slice 04 checkpoint.

## Parallelization decision

Rejected because the shared legacy module and patch-based tests make these
responsibilities unsafe to edit in parallel.
