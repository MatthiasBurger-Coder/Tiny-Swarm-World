# Workflow: Issue #218 WSL2 Dedicated Host Platform

Version: `issue-218-v1.1.0`
Workflow ID: `issue-218-20260720`
Branch: `docs/issue-218-live-acceptance-20260720`
Status: `INCOMPLETE`

## Current execution checkpoint — 2026-08-04

Slices 04–15 have completed their local implementation, test, live WSL2,
network, cleanup, native-regression and evidence gates. The final local audit
is green for those scopes. Slice 16 is `READY_FOR_GUARDED_PUBLICATION`, not
complete: the branch still requires remote CI/Sonar checks, merge-commit
verification on `main`, final Issue Completion Audit PASS and issue closure.
The opt-in Selenium browser contract is recorded as skipped according to its
documented opt-in prerequisite; Windows-side external HTTPS verification is
the passing reachability gate.

## Objective

Implement and verify all FR-1..FR-15, NFR-1..NFR-6, AC-1..AC-10, mandatory
tests, CLI requirements, evidence, documentation and completion gates from
GitHub Issue #218. Native Linux behavior must remain unchanged and live
infrastructure commands remain forbidden without explicit live consent.

## Requirement and Evidence Discipline

- Requirement matrix: `.tiny-swarm/evidence/issue-218/requirement_matrix.md`
- Evidence path: `.tiny-swarm/evidence/issue-218/`
- Required files: `requirement_matrix.md`, `implementation_summary.md`, `changed_files.md`, `test_results.md`, `live_wsl2_results.md`, `native_linux_results.md`, `network_results.md`, `resource_results.md`, `read_only_verify_results.md`, `remaining_risks.md`, `acceptance_checklist.md`, `completion_audit.md`
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

### Slice 05 — Repository, package and image source readiness

```yaml
slice_id: "05"
profile: "FULL_PATH"
owner: "Senior DevOps Engineer"
secondary_reviewers: ["Senior Python Automation Developer", "Senior Tester", "Senior System Architect"]
affected_files: ["src/tiny_swarm_world/infrastructure/adapters/clients/**", "src/tiny_swarm_world/application/**", "infra/config/**", "tests/**", "documentation/**"]
affected_modules: ["APT source readiness", "Docker repository readiness", "Nexus fallback selection"]
affected_contracts: ["bounded repository probes", "explicit fallback order"]
dependencies: ["04"]
parallel_group: "serial"
file_locks: ["artifact readiness", "repository configuration"]
contract_locks: ["readiness result model"]
architecture_locks: ["adapter-only external access"]
quality_gates:
  targeted: ["python3 tools/quality_gate.py test", "python3 tools/quality_gate.py typecheck"]
  required: ["python3 tools/quality_gate.py quality"]
documentation:
  arc42: "required if repository fallback architecture changes"
  adr: "required if source precedence changes"
stop_conditions: ["silent internet fallback", "unbounded repository access", "secret leakage"]
```

### Slice 06 — Dedicated WSL2 host preparation integration

```yaml
slice_id: "06"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers: ["Senior System Architect", "Senior DevOps Engineer", "Senior Tester"]
affected_files: ["src/tiny_swarm_world/domain/preflight/**", "src/tiny_swarm_world/application/ports/host/**", "src/tiny_swarm_world/application/services/platform/host/**", "src/tiny_swarm_world/infrastructure/adapters/host/**", "src/tiny_swarm_world/infrastructure/composition.py", "tests/**"]
affected_modules: ["host preparation", "WSL signal model", "native Linux routing"]
affected_contracts: ["host preparation result", "Windows command runner"]
dependencies: ["05"]
parallel_group: "serial"
file_locks: ["host ports", "host adapters", "composition"]
contract_locks: ["host preparation result"]
architecture_locks: ["native Linux isolation", "thin CLI"]
quality_gates:
  targeted: ["python3 tools/quality_gate.py test", "python3 tools/quality_gate.py arch-tests"]
  required: ["python3 tools/quality_gate.py quality"]
documentation:
  arc42: "required"
  adr: "review ADR dedicated WSL2 host boundary"
stop_conditions: ["native Linux invokes Windows adapter", "unstructured result", "hidden mutation"]
```

### Slice 07 — Resource gate before every infrastructure mutation

```yaml
slice_id: "07"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers: ["Senior System Architect", "Senior Tester", "Senior DevOps Engineer"]
affected_files: ["src/tiny_swarm_world/domain/preflight/**", "src/tiny_swarm_world/application/services/**", "src/tiny_swarm_world/infrastructure/adapters/clients/lxc_node_provider.py", "tests/**"]
affected_modules: ["resource snapshot", "profile assessment", "Incus mutation guard"]
affected_contracts: ["insufficient-resource terminal result"]
dependencies: ["06"]
parallel_group: "serial"
file_locks: ["resource model", "provider mutation guard"]
contract_locks: ["resource assessment"]
architecture_locks: ["domain calculation purity"]
quality_gates:
  targeted: ["python3 tools/quality_gate.py test", "python3 tools/quality_gate.py typecheck"]
  required: ["python3 tools/quality_gate.py quality"]
documentation:
  arc42: "required if mutation order changes"
  adr: "none unless policy changes"
stop_conditions: ["mutation before resource gate", "10 GiB limit under 8 GiB scenario"]
```

### Slice 08 — WSL/Windows network preparation, reconciliation and cleanup

```yaml
slice_id: "08"
profile: "FULL_PATH"
owner: "Senior DevOps Engineer"
secondary_reviewers: ["Senior Python Automation Developer", "Senior System Architect", "Senior Tester"]
affected_files: ["src/tiny_swarm_world/application/ports/host/**", "src/tiny_swarm_world/application/services/platform/host/**", "src/tiny_swarm_world/infrastructure/adapters/host/**", "tools/windows/**", "tests/**", "documentation/**"]
affected_modules: ["Windows command runner", "portproxy", "firewall", "hosts/DNS", "HTTPS probes"]
affected_contracts: ["idempotent network plan", "read-only network snapshot", "reversible cleanup"]
dependencies: ["07"]
parallel_group: "serial"
file_locks: ["Windows bridge", "network preparation"]
contract_locks: ["network state result"]
architecture_locks: ["infrastructure-only Windows commands"]
quality_gates:
  targeted: ["python3 tools/quality_gate.py test", "Pester Windows bridge suite"]
  required: ["python3 tools/quality_gate.py quality"]
documentation:
  arc42: "required"
  adr: "review Windows/WSL bridge ADR"
stop_conditions: ["foreign-rule deletion", "stale target remains", "non-idempotent apply"]
```

### Slice 09 — Observable apply and verify workflows

```yaml
slice_id: "09"
profile: "FULL_PATH"
owner: "Senior Workflow Architect"
secondary_reviewers: ["Senior Python Automation Developer", "Senior Tester", "Senior System Architect"]
affected_files: ["src/tiny_swarm_world/application/services/setup/**", "src/tiny_swarm_world/application/services/deployment/**", "src/tiny_swarm_world/infrastructure/adapters/command_runner/**", "src/tiny_swarm_world/infrastructure/composition.py", "tests/**"]
affected_modules: ["structured progress", "heartbeat", "phase separation"]
affected_contracts: ["workflow event lifecycle"]
dependencies: ["08"]
parallel_group: "serial"
file_locks: ["workflow orchestration", "progress contract"]
contract_locks: ["workflow status"]
architecture_locks: ["application ports"]
quality_gates:
  targeted: ["python3 tools/quality_gate.py test"]
  required: ["python3 tools/quality_gate.py quality"]
documentation:
  arc42: "required if workflow sequencing changes"
  adr: "none"
stop_conditions: ["silent long phase", "platform verify starts after deployment verify failure"]
```

### Slice 10 — Central outer and inner timeout enforcement

```yaml
slice_id: "10"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers: ["Senior Tester", "Senior DevOps Engineer", "Senior System Architect"]
affected_files: ["src/tiny_swarm_world/domain/**", "src/tiny_swarm_world/application/**", "src/tiny_swarm_world/infrastructure/adapters/**", "infra/config/**", "tests/**"]
affected_modules: ["timeout policy", "process termination", "typed terminal outcomes"]
affected_contracts: ["SUCCESS/FAILED/TIMED_OUT/INTERRUPTED/BLOCKED"]
dependencies: ["09"]
parallel_group: "serial"
file_locks: ["command execution", "workflow result models"]
contract_locks: ["timeout result"]
architecture_locks: ["adapter process boundary"]
quality_gates:
  targeted: ["python3 tools/quality_gate.py test", "python3 tools/quality_gate.py typecheck"]
  required: ["python3 tools/quality_gate.py quality"]
documentation:
  arc42: "required"
  adr: "none"
stop_conditions: ["unbounded external call", "timeout reported as ordinary failure", "child leak"]
```

### Slice 11 — Non-invasive hang diagnostics

```yaml
slice_id: "11"
profile: "FULL_PATH"
owner: "Senior Tester"
secondary_reviewers: ["Senior Python Automation Developer", "Senior System Architect", "Senior DevOps Engineer"]
affected_files: ["src/tiny_swarm_world/domain/preflight/hang_diagnostics.py", "src/tiny_swarm_world/infrastructure/adapters/host/hang_diagnostics.py", "src/tiny_swarm_world/application/**", "tests/**", "documentation/**"]
affected_modules: ["process state classification", "read-only diagnostics"]
affected_contracts: ["diagnostic classification result"]
dependencies: ["10"]
parallel_group: "serial"
file_locks: ["diagnostic adapter", "diagnostic result"]
contract_locks: ["read-only diagnostic evidence"]
architecture_locks: ["no mutation from diagnostics"]
quality_gates:
  targeted: ["python3 tools/quality_gate.py test"]
  required: ["python3 tools/quality_gate.py quality"]
documentation:
  arc42: "required"
  adr: "none"
stop_conditions: ["diagnostics mutate infrastructure", "unknown state mislabeled as success"]
```

### Slice 12 — Native Linux regression protection

```yaml
slice_id: "12"
profile: "FULL_PATH"
owner: "Senior Tester"
secondary_reviewers: ["Senior System Architect", "Senior Python Automation Developer", "Senior DevOps Engineer"]
affected_files: ["tests/integration/**", "tests/architecture/**", "tests/**", "documentation/**"]
affected_modules: ["native Linux adapter selection", "Windows command exclusion"]
affected_contracts: ["native Linux regression"]
dependencies: ["11"]
parallel_group: "serial"
file_locks: ["regression tests", "architecture tests"]
contract_locks: ["host path selection"]
architecture_locks: ["native Linux no-Windows boundary"]
quality_gates:
  targeted: ["python3 tools/quality_gate.py test", "python3 tools/quality_gate.py arch-tests"]
  required: ["python3 tools/quality_gate.py quality"]
documentation:
  arc42: "check"
  adr: "none"
stop_conditions: ["native Linux Windows invocation", "missing baseline regression"]
```

### Slice 13 — Real WSL2 end-to-end acceptance

```yaml
slice_id: "13"
profile: "FULL_PATH"
owner: "Senior DevOps Engineer"
secondary_reviewers: ["Senior Tester", "Senior System Architect", "Senior Requirement Engineer"]
affected_files: [".tiny-swarm/evidence/issue-218/**", ".codex/evidence/**", "documentation/**"]
affected_modules: ["live installation", "Windows reachability", "IP-change reconciliation"]
affected_contracts: ["redacted live evidence"]
dependencies: ["12"]
parallel_group: "serial"
file_locks: ["live evidence", "shared WSL runtime"]
contract_locks: ["live acceptance status"]
architecture_locks: ["live consent and cleanup"]
quality_gates:
  targeted: ["individual bounded live commands", "Pester Windows bridge suite"]
  required: ["full local quality gate", "live WSL2 acceptance"]
documentation:
  arc42: "check"
  adr: "none"
stop_conditions: ["unredacted secret evidence", "internal-only reachability claimed as Windows reachability"]
```

### Slice 14 — Verify read-only snapshot proof

```yaml
slice_id: "14"
profile: "FULL_PATH"
owner: "Senior Tester"
secondary_reviewers: ["Senior Python Automation Developer", "Senior DevOps Engineer", "Senior System Architect"]
affected_files: ["src/tiny_swarm_world/application/services/**", "src/tiny_swarm_world/infrastructure/adapters/**", "tests/**", ".tiny-swarm/evidence/issue-218/**"]
affected_modules: ["before/after state snapshot", "verify mutation guard"]
affected_contracts: ["read-only verify evidence"]
dependencies: ["13"]
parallel_group: "serial"
file_locks: ["verify workflow", "snapshot evidence"]
contract_locks: ["read-only contract"]
architecture_locks: ["verify no mutation"]
quality_gates:
  targeted: ["python3 tools/quality_gate.py test", "read-only live verify"]
  required: ["python3 tools/quality_gate.py quality"]
documentation:
  arc42: "check"
  adr: "none"
stop_conditions: ["any observed mutation", "incomplete before/after snapshot"]
```

### Slice 15 — Complete evidence and independent completion audit

```yaml
slice_id: "15"
profile: "FULL_PATH"
owner: "Issue Completion Auditor"
secondary_reviewers: ["Senior Requirement Engineer", "Senior System Architect", "Senior Tester", "Senior DevOps Engineer"]
affected_files: [".tiny-swarm/evidence/issue-218/**", ".codex/evidence/**", "documentation/**"]
affected_modules: ["requirement traceability", "acceptance checklist", "completion audit"]
affected_contracts: ["PASS/FAIL/NOT_APPLICABLE final states"]
dependencies: ["14"]
parallel_group: "serial"
file_locks: ["issue evidence"]
contract_locks: ["audit decision"]
architecture_locks: ["independent audit authority"]
quality_gates:
  targeted: ["evidence consistency check", "git diff --check"]
  required: ["python3 tools/quality_gate.py quality"]
documentation:
  arc42: "check"
  adr: "check"
stop_conditions: ["open requirement", "missing required evidence", "self-approval only"]
```

### Slice 16 — Merge, main verification and issue closure

```yaml
slice_id: "16"
profile: "FULL_PATH"
owner: "Root Architect / Release Owner"
secondary_reviewers: ["Senior Tester", "Senior DevOps Engineer", "Issue Completion Auditor"]
affected_files: ["all task-scoped changes", ".tiny-swarm/evidence/issue-218/**"]
affected_modules: ["PR lifecycle", "main verification", "issue state"]
affected_contracts: ["post-merge green main"]
dependencies: ["15"]
parallel_group: "serial"
file_locks: ["release branch", "main verification"]
contract_locks: ["merge completion"]
architecture_locks: ["release governance"]
quality_gates:
  targeted: ["git diff --check", "main post-merge verification"]
  required: ["full local quality gate", "CI", "SonarCloud", "live WSL2 acceptance", "native Linux regression", "completion audit"]
documentation:
  arc42: "final check"
  adr: "final check"
stop_conditions: ["main not green", "unverifiable required check", "issue closure without PASS audit"]
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
read-only. Issue #218 live consent explicitly authorizes the bounded live
validation activities described by Slices 08, 13 and 14; all commands remain
individual, timeout-bounded and evidence-producing.

## Definition of Done

All requirements and acceptance criteria are implemented, tested and evidenced;
the full quality gate is green; documentation and arc42 checks are complete;
the completion auditor returns `PASS`; and a final implementation PR exists.
