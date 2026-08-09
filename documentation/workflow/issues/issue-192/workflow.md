# Workflow: Issue #192 — Separate LXC HTTP Service Wrappers

Workflow ID: `issue-192-20260809`

Workflow version: `issue-192-v1.0.0`

Status: `READY_FOR_EXECUTION_WITH_ACCEPTED_ASSUMPTIONS` (indexed; promote before execution)

Authoring branch: `feature/workflow-solid-refactor-chain-20260809`

Implementation branch: `feature/separate-lxc-service-wrappers-solid`

Chain position: 06 of 07; predecessor: #190; successor: #186.

## Executive Summary

Keep Portainer and Nexus HTTP adapters separate from Swarm runtime and image /
deployment code. Revalidate the service modules already introduced by #238,
preserve URL/authentication/session behavior and compatibility imports, and
keep manager-IP resolution plus local URL creation in an explicit LXC service
boundary.

## Requirement Clarification Record

- Original Request: workflow creation for the ordered issue chain.
- Interpreted Intent: author the sixth indexed workflow; execute only after
  #190 completion.
- Change Type: Python infrastructure adapter-boundary refactor with HTTP
  compatibility and security tests.
- Affected Process Strand: `workflow-create-to-workflow-execute`.
- Affected Architecture Area: LXC service clients, Swarm runtime facade,
  composition and HTTP-adapter tests.
- Explicit Requirements: [Issue #192 matrix](../../../.tiny-swarm/evidence/solid-lxc-service-wrappers/requirement_matrix.md).
- Implicit Requirements: no credential logging, explicit-vs-local URL
  precedence, deterministic manager-IP failure, no application-port drift and
  no live service call in local tests.
- Assumptions: #238's `lxc/services/` modules are baseline candidates; only
  residual wrapper, resolver, factory, compatibility or test gaps are changed.
- Non-Goals: new HTTP APIs, deployment topology, live Portainer/Nexus access,
  browser React, stack strategies or DI redesign.
- Risks: URL precedence, session reuse, cookie clearing and facade import
  compatibility can drift during relocation.
- Open Questions: whether current common helper owns enough URL validation and
  whether the manager-IP resolver belongs in services or command utilities.
- Blocking Questions: unclear local-vs-explicit URL precedence blocks execution.
- Confidence Level: 85%.
- Decision: `PROCEED_WITH_ACCEPTED_ASSUMPTIONS`.

## Verified Baseline and Target Picture

Current source includes `lxc/services/lxc_portainer_admin_client.py`,
`lxc_portainer_http_client.py`, `lxc_nexus_http_client.py` and `common.py`,
while `lxc_swarm_runtime.py` retains compatibility facades and an
`_lxc_manager_ip` helper. The target makes ownership explicit, retains old
imports during migration and proves HTTP delegation with mocks.

## Scope and Assessments

In scope: responsibility/URL contract inventory, residual wrapper/resolver
extraction, composition import updates, compatibility and security tests,
evidence and Arc42 status. Python impact is `FULL_PATH`; frontend/Console UI
is `NOT_APPLICABLE`, browser React review is forbidden. Default verification is
local/mocked; live Portainer/Nexus/browser checks require separate consent and
state evidence.

## Ordered Slices

### Slice 01 — Wrapper/API responsibility inventory

```yaml
slice_id: S192-01
profile: FULL_PATH
owner: Senior Requirement Engineer
secondary_reviewers: [Senior System Architect, Senior Python Automation Developer, Senior Tester]
affected_files: [.tiny-swarm/evidence/solid-lxc-service-wrappers/requirement_matrix.md, .tiny-swarm-world/evidence/solid-lxc-service-wrappers/three-amigos.md, .tiny-swarm-world/evidence/solid-lxc-service-wrappers/responsibility-map-before.md]
affected_modules: [LXC Portainer/Nexus service clients, Swarm runtime facade, composition]
affected_contracts: [Portainer API URL/auth/session behavior, Nexus delegation, manager IP resolution]
dependencies: []
parallel_group: SERIAL-CHAIN
file_locks: [.tiny-swarm/evidence/solid-lxc-service-wrappers/**, .tiny-swarm-world/evidence/solid-lxc-service-wrappers/**]
contract_locks: [lxc-service-http-contract, explicit-api-url-precedence]
architecture_locks: [lxc-service-boundary, issue-190-runtime-boundary]
quality_gates:
  targeted: [git diff --check]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: reviewed; planned residual status
  adr: none unless public HTTP contract changes
stop_conditions: [unclear URL precedence, unknown consumer, credential-bearing evidence, duplicate #238 wrapper]
```

### Slice 02 — Wrapper/resolver boundary and compatibility migration

```yaml
slice_id: S192-02
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Senior Tester, Senior Security Sandbox Engineer]
affected_files: [src/tiny_swarm_world/infrastructure/adapters/clients/lxc/services/**, src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py, src/tiny_swarm_world/infrastructure/composition.py, tests/infrastructure/adapters/clients/lxc/services/**, tests/infrastructure/adapters/clients/test_lxc_swarm_runtime.py]
affected_modules: [lxc service adapters and compatibility facade]
affected_contracts: [PortPortainerClient, PortPortainerAdminClient, PortNexusClient, local URL creation]
dependencies: [S192-01]
parallel_group: SERIAL-CHAIN
file_locks: [src/tiny_swarm_world/infrastructure/adapters/clients/lxc/services/**, src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py, src/tiny_swarm_world/infrastructure/composition.py, tests/infrastructure/adapters/clients/lxc/services/**, tests/infrastructure/adapters/clients/test_lxc_swarm_runtime.py]
contract_locks: [lxc-service-http-contract, explicit-api-url-precedence]
architecture_locks: [lxc-service-boundary, composition-root-wiring]
quality_gates:
  targeted: [python3 tools/quality_gate.py lint, python3 tools/quality_gate.py typecheck, python3 tools/quality_gate.py test, python3 tools/quality_gate.py arch-lint, python3 tools/quality_gate.py arch-tests]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: planned boundary until verified
  adr: stop if public contract or ownership changes
stop_conditions: [URL/auth/session drift, broken old imports, raw credentials, runtime facade absorbs HTTP policy]
```

### Slice 03 — Regression, security and completion audit

```yaml
slice_id: S192-03
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers: [Senior System Architect, Senior Requirement Engineer, Senior Documentation Engineer]
affected_files: [tests/infrastructure/adapters/clients/lxc/services/**, tests/infrastructure/adapters/clients/test_lxc_swarm_runtime.py, tests/architecture/**, .tiny-swarm-world/evidence/solid-lxc-service-wrappers/**, documentation/arc42/**]
affected_modules: [HTTP wrapper regression, security evidence and architecture tests]
affected_contracts: [Portainer/Nexus behavior, credential safety, composition wiring]
dependencies: [S192-02]
parallel_group: SERIAL-CHAIN
file_locks: [tests/infrastructure/adapters/clients/lxc/services/**, tests/infrastructure/adapters/clients/test_lxc_swarm_runtime.py, tests/architecture/**, .tiny-swarm-world/evidence/solid-lxc-service-wrappers/**, documentation/arc42/**]
contract_locks: [lxc-service-http-contract, explicit-api-url-precedence]
architecture_locks: [lxc-service-boundary]
quality_gates:
  targeted: [git diff --check, python3 tools/quality_gate.py test, python3 tools/quality_gate.py arch-tests]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: synchronize verified status only
  adr: review existing service access decisions
stop_conditions: [missing URL/session coverage, credential leak, open matrix, unobservable live/external result]
```

## Parallel Execution

- Can this workflow run in parallel? No; it follows #190 and touches the LXC
  service modules, facade and composition used by #186.
- Conflicting workflows: #189, #190, #186 and any LXC HTTP/composition change.
- Shared files: `lxc/services/**`, `lxc_swarm_runtime.py`, composition and tests.
- Shared infrastructure: none in default local gates.
- Requires isolated worktree: yes.
- Requires serialized live validation: yes, if authorized.
- Merge-order constraints: #190 -> #192 -> #186.

## Automatic Work Distribution Policy

`workflow execute` analyzes backend, frontend, tests, runtime, documentation,
quality, architecture and security streams, uses real subagents where
available or records role fallback, and requires distribution evidence before
edits plus consolidation evidence after implementation under `.codex/evidence/`.
Overlapping files/contracts, unclear URL semantics, mandatory order, generated
conflicts, unclear secrets and weakened guards forbid parallelization. Codex is
final integration owner.

## Git Worktree Execution Rule

Use isolated worktrees and `<workflow-branch>-slice-<number>-<stream>` branches.
Workers verify branch/locks, do not merge and stay within allowed files.

## Role and Ownership Map

Requirement: Senior Requirement Engineer. Architecture: Senior System
Architect. Python: Senior Python Automation Developer. Tests/security:
Senior Tester with Senior Security Sandbox Engineer. Docs: Senior Documentation
Engineer. Order/locks: Senior Execution Orchestrator.

## Issue Completion Discipline

- Requirement matrix path: `.tiny-swarm/evidence/solid-lxc-service-wrappers/requirement_matrix.md`.
- Required evidence path: `.tiny-swarm/evidence/solid-lxc-service-wrappers/`.
- Required evidence files: `requirement_matrix.md`, `implementation_summary.md`, `changed_files.md`, `test_results.md`, `remaining_risks.md`, `acceptance_checklist.md`, plus Three-Amigos and responsibility evidence under `.tiny-swarm-world/evidence/solid-lxc-service-wrappers/`.
- Requirement Lead review: S192-01.
- System Architect Reviewer review: S192-02.
- Test / Evidence Reviewer review: S192-03.
- Issue Completion Auditor review: before #186 promotion.
- DONE blocking rule: open/unverified requirements force `INCOMPLETE`,
  `BLOCKED` or `FAILED`; no credential or live-success claim without evidence.

## Quality-Gate Expectations, Documentation, Stop Conditions and Handoff

Use `QUALITY.md` local gates and focused mocked tests. Arc42 updates must
separate #238 baseline from residual work. Stop on URL ambiguity, behavior or
import drift, security leakage, failed gates or unobservable external/live
results. Done requires all wrapper tests, architecture/security checks,
evidence and auditor PASS. Promote after #190.

## Arc42 Check Status

Current service-access and LXC-native architecture notes were reviewed. This
workflow plans residual wrapper verification and does not claim live HTTP
availability.
