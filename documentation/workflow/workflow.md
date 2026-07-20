# Workflow: Issue #218 WSL2 Dedicated Host Platform

Version: `issue-218-v1.0.0`
Workflow ID: `issue-218-20260720`
Branch: `feature/workflow-issue-218-20260720`
Status: `READY_FOR_EXECUTION`

## Objective

Implement and verify all FR-1..FR-15, NFR-1..NFR-6, AC-1..AC-10, mandatory
tests, CLI requirements, evidence, documentation and completion gates from
GitHub Issue #218. Native Linux behavior must remain unchanged and live
infrastructure commands remain forbidden without explicit live consent.

## Requirement and Evidence Discipline

- Requirement matrix: `.tiny-swarm/evidence/issue-218/requirement_matrix.md`
- Evidence path: `.tiny-swarm/evidence/issue-218/`
- Required files: `requirement_matrix.md`, `implementation_summary.md`, `changed_files.md`, `test_results.md`, `remaining_risks.md`, `acceptance_checklist.md`
- Open or unverified requirements force `INCOMPLETE`, `BLOCKED` or `FAILED`.
- Final completion requires Requirement Lead, System Architect Reviewer, Test/Evidence Reviewer and Issue Completion Auditor decisions.

## Ordered Slices

### Slice 01 — Resource preflight and profile validation

```yaml
slice_id: "01"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers: ["Senior System Architect", "Senior Tester", "Senior Requirement Engineer"]
affected_files: ["src/tiny_swarm_world/domain/preflight/**", "src/tiny_swarm_world/application/**", "src/tiny_swarm_world/infrastructure/**", "tests/**"]
affected_modules: ["host resources", "service profiles", "Incus limit validation"]
affected_contracts: ["structured resource assessment"]
dependencies: []
parallel_group: "serial"
file_locks: ["host preflight", "composition.py"]
contract_locks: ["resource result models"]
architecture_locks: ["hexagonal boundaries"]
quality_gates:
  targeted: ["python3 tools/quality_gate.py test", "python3 tools/quality_gate.py typecheck"]
  required: ["python3 tools/quality_gate.py quality"]
documentation:
  arc42: "check and update if boundary changes"
  adr: "required if architecture decision is introduced"
stop_conditions: ["missing resource source", "unsafe Incus mutation", "failed quality gate"]
```

### Slice 02 — WSL network and filesystem adapters

```yaml
slice_id: "02"
profile: "FULL_PATH"
owner: "Senior DevOps Engineer"
secondary_reviewers: ["Senior System Architect", "Senior Tester", "Security Reviewer"]
affected_files: ["src/tiny_swarm_world/application/ports/**", "src/tiny_swarm_world/infrastructure/adapters/host/**", "src/tiny_swarm_world/infrastructure/adapters/network/**", "tests/**"]
affected_modules: ["WSL network preparation", "filesystem policy", "native Linux routing"]
affected_contracts: ["idempotent reversible network preparation"]
dependencies: ["01"]
parallel_group: "serial"
file_locks: ["host adapters", "network adapters"]
contract_locks: ["host preparation ports"]
architecture_locks: ["native Linux isolation"]
quality_gates:
  targeted: ["python3 tools/quality_gate.py test"]
  required: ["python3 tools/quality_gate.py quality"]
documentation:
  arc42: "check and update if boundary changes"
  adr: "required if architecture decision is introduced"
stop_conditions: ["Windows command on native Linux", "non-idempotent mutation", "verify mutation"]
```

### Slice 03 — Workflow observability, timeouts and diagnostics

```yaml
slice_id: "03"
profile: "FULL_PATH"
owner: "Senior Workflow Architect"
secondary_reviewers: ["Senior Python Automation Developer", "Senior Tester", "Senior System Architect"]
affected_files: ["src/tiny_swarm_world/application/services/**", "src/tiny_swarm_world/infrastructure/adapters/command_runner/**", "tests/**"]
affected_modules: ["progress", "heartbeats", "outer and inner timeouts", "read-only hang diagnostics"]
affected_contracts: ["typed workflow outcomes", "separate apply and verify"]
dependencies: ["01", "02"]
parallel_group: "serial"
file_locks: ["workflow orchestration"]
contract_locks: ["timeout and progress results"]
architecture_locks: ["application depends on ports"]
quality_gates:
  targeted: ["python3 tools/quality_gate.py test"]
  required: ["python3 tools/quality_gate.py quality"]
documentation:
  arc42: "check and update if boundary changes"
  adr: "required if architecture decision is introduced"
stop_conditions: ["unbounded external call", "verify chaining after failure", "diagnostics mutate state"]
```

### Slice 04 — CLI, evidence, documentation and final verification

```yaml
slice_id: "04"
profile: "FULL_PATH"
owner: "Senior Documentation Engineer"
secondary_reviewers: ["Senior Tester", "Senior Requirement Engineer", "Issue Completion Auditor"]
affected_files: ["src/tiny_swarm_world/__main__.py", "documentation/**", ".tiny-swarm/evidence/issue-218/**", "tests/**"]
affected_modules: ["host CLI", "installation evidence", "acceptance verification"]
affected_contracts: ["host detect/preflight/prepare/verify"]
dependencies: ["01", "02", "03"]
parallel_group: "serial"
file_locks: ["CLI", "evidence", "documentation"]
contract_locks: ["issue completion evidence"]
architecture_locks: ["thin entry point", "auditor independence"]
quality_gates:
  targeted: ["python3 tools/quality_gate.py test", "git diff --check"]
  required: ["python3 tools/quality_gate.py quality"]
documentation:
  arc42: "required check"
  adr: "required if architecture decision is introduced"
stop_conditions: ["open requirement", "missing evidence", "failed gate", "unverifiable live claim"]
```

## Execution Rules

Slices are strictly serial. `workflow execute` must perform automatic work
distribution analysis and create `.codex/evidence/slice-<number>-distribution.md`
and consolidation evidence for each slice. Safe streams require isolated
worktrees; overlapping contracts, composition, workflow orchestration,
generated files, secrets or safety guards are never parallelized. Codex is the
final integration owner.

No live Incus, Docker Swarm, network, Windows firewall, portproxy or service
bootstrap command may run without explicit live consent. Verify must be
read-only.

## Definition of Done

All requirements and acceptance criteria are implemented, tested and evidenced;
the full quality gate is green; documentation and arc42 checks are complete;
the completion auditor returns `PASS`; and a final implementation PR exists.
