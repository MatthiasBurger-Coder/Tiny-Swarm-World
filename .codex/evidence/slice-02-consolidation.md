# Issue #188 — S02 Consolidation

- Workflow: `issue-188-20260809` / `issue-188-v1.0.0`
- Slice: `S02` — Implement the reusable infrastructure process runner
- Branch: `feature/issue-188-shared-command-runners`
- Decision: `IMPLEMENTED_WITH_BASELINE_GATE_EXCEPTION`
- Real subagents: not available; fallback role review was performed

## Initial blocker and accepted resolution

The checked workflow required S02 to wire the concrete shared runner through
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
therefore required for explicit dependency injection but was outside S02's
declared write scope. The user explicitly instructed Three Amigos to analyze
and solve this known blocker. The accepted resolution is to include these
minimal constructor/delegation changes in S02, with no new migration targets,
port changes, service boundary, or non-goal changes. This resolution is
recorded in `.tiny-swarm/evidence/solid-command-runner/execution-scope-resolution.md`.

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
- Senior Execution Orchestrator: accepted the user-authorized minimal scope
  resolution; S02 remains serial and owns the contract plus required wiring.

## Checks executed

- S3 branch/status/local-ref check — PASS.
- S3D metadata/dependency/topology check — PASS for the graph; S02 remains
  blocked by its internal scope/lock inconsistency.
- Constructor and composition call-site inspection — PASS; blocker reproduced
  from source symbols listed above.
- `git diff --check` — PASS.
- Python quality gates — NOT RUN; no Python source or test changes were made.
- Live/external/browser/SonarQube checks — NOT REQUIRED and NOT RUN.

## Implementation handoff

## Implemented result

The accepted S02 resolution is implemented with:

- typed `ProcessRunner` and bounded `SubprocessProcessRunner` infrastructure
  adapters for text and byte results;
- sanitized launch, timeout, and non-zero exit failures;
- one concrete runner created by the composition root and supplied to the
  composed preflight, LXC runtime, image publisher, and gateway paths;
- optional runner constructor dependencies that preserve direct unit-test
  construction; and
- an explicit `LxcSwarmRuntime` delegation seam that retains the legacy
  operation-time callback only for uncomposed direct construction.

The five adapter process-call migrations remain owned by S03–S07 so each
workflow slice can carry its own focused regression evidence.

## Verification

- Focused runner, composition, and affected adapter regression tests: **PASS**
  (`69` tests).
- `python3 tools/quality_gate.py lint`: **PASS**.
- `python3 tools/quality_gate.py typecheck`: **PASS**.
- Full `python3 tools/quality_gate.py quality`: **NOT GREEN** because the
  pre-existing `tests.architecture.test_skill_registry_integrity` check reports
  a stale hash for `documentation/arc42/08_concepts.adoc`, which was changed by
  the workflow-create commit before this implementation. Verification-policy,
  lint, arch-lint, arch-tests, typecheck, and the remaining `1,673` discovered
  tests passed in that run.
- `git diff --check`: **PASS**.
- Live infrastructure, browser, and SonarQube checks: **NOT REQUIRED / NOT
  RUN**.

No `workflow create` call was made during execution. The baseline hash issue is
recorded as an independent quality-gate exception and is not attributed to the
Issue #188 runner implementation.
