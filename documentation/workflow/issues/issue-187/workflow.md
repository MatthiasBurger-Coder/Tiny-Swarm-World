# Workflow: Issue #187 — Host Preflight Service Probe Registry

Workflow ID: `issue-187-20260809`

Workflow version: `issue-187-v1.0.0`

Status: `READY_FOR_EXECUTION_WITH_ACCEPTED_ASSUMPTIONS` (indexed; promote before execution)

Authoring branch: `feature/workflow-solid-refactor-chain-20260809`

Implementation branch: `feature/preflight-service-probe-registry-solid`

Chain position: 04 of 07; predecessor: #191; successor: #190.

## Executive Summary

Replace the service-name conditional chain in `HostPreflightProbe` with a
strategy/registry boundary while preserving every current service fingerprint,
port match and unsupported-service result. Keep host environment detection,
executable checks, secrets and Git scanning outside this issue.

## Requirement Clarification Record

- Original Request: workflow creation for the ordered issue chain.
- Interpreted Intent: author the fourth indexed workflow; implementation waits
  for #191 audit completion.
- Change Type: Python preflight architecture refactor with behavior-preserving
  contract tests.
- Affected Process Strand: `workflow-create-to-workflow-execute`.
- Affected Architecture Area: `infrastructure.adapters.preflight` service
  fingerprint and port matching.
- Explicit Requirements: [Issue #187 matrix](../../../.tiny-swarm/evidence/solid-host-preflight-probe/requirement_matrix.md).
- Implicit Requirements: public method compatibility, deterministic network
  failure behavior, no host-detection scope expansion, redacted evidence.
- Assumptions: #191 establishes evidence construction boundaries; current
  service strings and tests are the behavior baseline.
- Non-Goals: host environment strategy extraction, stack deployment, live
  network/browser checks, React, microservices and unrelated evidence changes.
- Risks: overlapping service names, probe ordering, HTTPS/TCP semantics and
  changes to fallback behavior.
- Open Questions: exact strategy protocol and registry ordering; Slice 01
  resolves these from current tests and service contracts.
- Blocking Questions: ambiguous service fingerprint behavior blocks execution.
- Confidence Level: 85%.
- Decision: `PROCEED_WITH_ACCEPTED_ASSUMPTIONS`.

## Verified Baseline and Target Picture

`HostPreflightProbe.port_matches_expected_service` currently contains ordered
conditionals for Portainer, Docker Registry, Nexus, Jenkins, Pulsar, SonarQube,
Swagger, Traefik, Service Access and Infisical. Existing focused tests cover
many of these branches. The target introduces a protocol such as
`supports(service_name)`/`matches(port)` plus a deterministic registry while
retaining the public method.

## Scope and Assessments

In scope: service behavior inventory, registry/probe modules, method delegation,
focused and architecture tests, evidence and Arc42 status. Infrastructure-only
boundary is preserved. Python impact is `FULL_PATH`; frontend/Console UI is
`NOT_APPLICABLE`, browser React review is forbidden. Default verification uses
mocks/static checks and cannot mutate live hosts or services.

## Ordered Slices

### Slice 01 — Service/fingerprint behavior inventory

```yaml
slice_id: S187-01
profile: FULL_PATH
owner: Senior Requirement Engineer
secondary_reviewers: [Senior System Architect, Senior Python Automation Developer, Senior Tester]
affected_files: [.tiny-swarm/evidence/solid-host-preflight-probe/requirement_matrix.md, .tiny-swarm-world/evidence/solid-host-preflight-probe/three-amigos.md, .tiny-swarm-world/evidence/solid-host-preflight-probe/responsibility-map-before.md]
affected_modules: [preflight HostPreflightProbe and service fingerprint tests]
affected_contracts: [service names, port matching, HTTP/TCP probe semantics]
dependencies: []
parallel_group: SERIAL-CHAIN
file_locks: [.tiny-swarm/evidence/solid-host-preflight-probe/**, .tiny-swarm-world/evidence/solid-host-preflight-probe/**]
contract_locks: [host-service-probe-contract]
architecture_locks: [preflight-strategy-registry-boundary]
quality_gates:
  targeted: [git diff --check]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: reviewed; planned only
  adr: none unless preflight public contract changes
stop_conditions: [ambiguous fingerprint, missing current test case, changed unsupported behavior assumption]
```

### Slice 02 — Registry and probe extraction

```yaml
slice_id: S187-02
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Senior Tester, Senior Security Sandbox Engineer]
affected_files: [src/tiny_swarm_world/infrastructure/adapters/preflight/host_preflight_probe.py, src/tiny_swarm_world/infrastructure/adapters/preflight/service_probes/**, tests/infrastructure/adapters/preflight/test_host_preflight_probe.py, tests/infrastructure/adapters/preflight/service_probes/**]
affected_modules: [infrastructure.adapters.preflight]
affected_contracts: [PortHostPreflightProbe, HostPreflightProbe public method, service probe registry]
dependencies: [S187-01]
parallel_group: SERIAL-CHAIN
file_locks: [src/tiny_swarm_world/infrastructure/adapters/preflight/**, tests/infrastructure/adapters/preflight/**]
contract_locks: [host-service-probe-contract]
architecture_locks: [preflight-strategy-registry-boundary, issue-191-evidence-boundary]
quality_gates:
  targeted: [python3 tools/quality_gate.py lint, python3 tools/quality_gate.py typecheck, python3 tools/quality_gate.py test, python3 tools/quality_gate.py arch-lint, python3 tools/quality_gate.py arch-tests]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: planned registry boundary until tested
  adr: none unless service contract changes
stop_conditions: [public signature drift, probe order drift, live network dependency in tests, unrelated host-detection expansion]
```

### Slice 03 — Regression and completion audit

```yaml
slice_id: S187-03
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers: [Senior System Architect, Senior Requirement Engineer, Senior Documentation Engineer]
affected_files: [tests/infrastructure/adapters/preflight/**, tests/architecture/**, .tiny-swarm-world/evidence/solid-host-preflight-probe/**, documentation/arc42/**]
affected_modules: [preflight regression and architecture validation]
affected_contracts: [service matching behavior, evidence and quality gate]
dependencies: [S187-02]
parallel_group: SERIAL-CHAIN
file_locks: [tests/infrastructure/adapters/preflight/**, tests/architecture/**, .tiny-swarm-world/evidence/solid-host-preflight-probe/**, documentation/arc42/**]
contract_locks: [host-service-probe-contract]
architecture_locks: [preflight-strategy-registry-boundary]
quality_gates:
  targeted: [git diff --check, python3 tools/quality_gate.py test, python3 tools/quality_gate.py arch-tests]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: synchronize verified planned/implemented status
  adr: review only
stop_conditions: [missing service coverage, open requirement, failed quality gate, unverified live claim]
```

## Parallel Execution

- Can this workflow run in parallel? No; it follows #191 and owns the shared
  preflight probe surface used by later #190 verification.
- Conflicting workflows: any preflight behavior, host probe or evidence change.
- Shared files: `host_preflight_probe.py`, preflight tests and evidence.
- Shared infrastructure: none in local gates.
- Requires isolated worktree: yes.
- Requires serialized live validation: yes, if authorized.
- Merge-order constraints: #191 -> #187 -> #190.

## Automatic Work Distribution Policy

`workflow execute` analyzes backend, frontend, tests, runtime, documentation,
quality, architecture and security streams per slice; uses real subagents when
available or records role-based fallback. Distribution evidence is required
before implementation and consolidation evidence after implementation under
`.codex/evidence/`. Overlapping files, unclear behavior, mandatory ordering,
generated conflicts, unclear secrets and weakened guards forbid parallel work.
Codex remains final integration owner.

## Git Worktree Execution Rule

Use isolated worktrees and `<workflow-branch>-slice-<number>-<stream>` branches.
Workers verify branch and locks, do not merge, and do not edit shared branches.

## Role and Ownership Map

Requirement: Senior Requirement Engineer. Architecture: Senior System
Architect. Python: Senior Python Automation Developer. Tests: Senior Tester.
Docs: Senior Documentation Engineer. Lock/order: Senior Execution Orchestrator.

## Issue Completion Discipline

- Requirement matrix path: `.tiny-swarm/evidence/solid-host-preflight-probe/requirement_matrix.md`.
- Required evidence path: `.tiny-swarm/evidence/solid-host-preflight-probe/`.
- Required evidence files: `requirement_matrix.md`, `implementation_summary.md`, `changed_files.md`, `test_results.md`, `remaining_risks.md`, `acceptance_checklist.md`, plus Three-Amigos and before/after responsibility evidence under `.tiny-swarm-world/evidence/solid-host-preflight-probe/`.
- Requirement Lead review: S187-01.
- System Architect Reviewer review: S187-02.
- Test / Evidence Reviewer review: S187-03.
- Issue Completion Auditor review: before #190 promotion.
- DONE blocking rule: open/unverified requirements force `INCOMPLETE`,
  `BLOCKED` or `FAILED`; local pass does not prove live service reachability.

## Quality-Gate Expectations, Documentation, Stop Conditions and Handoff

Use only `QUALITY.md` commands, with full local quality before completion.
Arc42 updates are planned/implemented status only. Stop on ambiguous service
behavior, method signature drift, incomplete evidence, failed gates or
unobservable external/live results. Done requires all named service tests,
unsupported-name behavior, architecture guard, evidence and auditor PASS.
Promote after #191 is complete.

## Arc42 Check Status

Current preflight and quality documentation was reviewed. This plan does not
claim a registry implementation or live host verification.
