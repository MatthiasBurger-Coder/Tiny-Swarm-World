# Issue #188 — S02 Consolidation

- Workflow: `issue-188-20260809` / `issue-188-v1.0.0`
- Slice: `S02` — Implement the reusable infrastructure process runner
- Branch: `feature/issue-188-shared-command-runners`
- Decision: `ORCHESTRATION_BLOCKER`
- Real subagents: not available; fallback role review was performed

## Blocker

The checked workflow requires S02 to wire the concrete shared runner through
`infrastructure/composition.py`, but the verified baseline target adapters do
not accept a runner dependency:

- `DockerCliRuntime.__init__` has only `timeout_seconds`.
- `LxcManagerShellGateway` has no runner constructor dependency; its legacy
  call seam is passed at operation time from `LxcSwarmRuntime`.
- `LxcContainerRuntime.__init__` has no runner dependency.
- `LxcContainerImagePublisher.__init__` has no runner dependency.
- `HostPreflightProbe.__init__` has no runner dependency.

The S02 allowed files and locks are limited to:

- `src/tiny_swarm_world/infrastructure/process/**`
- `src/tiny_swarm_world/infrastructure/composition.py`
- `tests/infrastructure/process/**`
- `tests/infrastructure/test_composition.py`

Changing the five adapter constructors or the legacy `LxcSwarmRuntime` seam is
therefore required for explicit dependency injection but is outside S02's
declared write scope. Deferring composition changes to S03–S07 is also outside
those slices' declared file locks because composition is not listed there.

## Fallback role review

- Senior Python Automation Developer: confirmed that a runner factory alone
  would not wire the adapters and that adapter-local global lookup would violate
  the explicit-dependency and infrastructure-boundary requirements.
- Senior System Architect: confirmed that importing composition from adapters
  or introducing a global runner would be an architecture shortcut.
- Senior Tester: confirmed that constructor changes require focused composition
  and adapter regression coverage and must not be hidden in S02.
- Senior Security Sandbox Engineer: confirmed no source or live process change
  was made while the dependency boundary is unresolved.
- Senior Execution Orchestrator: classified this as a checked-workflow scope /
  lock inconsistency requiring workflow-authority direction before write work.

## Checks executed

- S3 branch/status/local-ref check — PASS.
- S3D metadata/dependency/topology check — PASS for the graph; S02 remains
  blocked by its internal scope/lock inconsistency.
- Constructor and composition call-site inspection — PASS; blocker reproduced
  from source symbols listed above.
- `git diff --check` — PASS.
- Python quality gates — NOT RUN; no Python source or test changes were made.
- Live/external/browser/SonarQube checks — NOT REQUIRED and NOT RUN.

## Required resolution

Resume only after one of these is explicitly authorized in the checked
workflow: (1) amend S02's write scope/locks to include the minimal adapter
constructor and legacy-seam wiring, or (2) define a verified alternative
composition mechanism that preserves explicit dependency injection and does
not introduce global lookup or an adapter-to-composition dependency.

No `workflow create` call was made, and no product implementation was started.
