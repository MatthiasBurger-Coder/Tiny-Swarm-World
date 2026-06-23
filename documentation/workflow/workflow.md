# Workflow: SonarCloud S5527 TLS Verification Remediation

Version: `sonar-s5527-tls-v1.0.0`
Workflow ID: `workflow-sonar-s5527-tls-20260623`
Created: `2026-06-23`
Branch: `fix/workflow-sonar-s5527-tls-20260623`
Status: `READY_FOR_EXECUTION`
Evidence Root: `.codex/evidence/workflow-sonar-s5527-tls-20260623/`

## Executive Summary

Remediate SonarCloud issue `AZ7kEe623UILYpQnQ6zD`, rule `python:S5527`,
reported as Critical in
`src/tiny_swarm_world/infrastructure/adapters/preflight/host_preflight_probe.py`
line 456. The issue is caused by HTTPS localhost preflight probing with an
unverified TLS context. The workflow replaces unverified TLS context creation
with Python's verified default TLS context and proves the behavior with
focused unit tests.

## Requirement Clarification Gate

Original Request:

- Work in `D:/Projects/Tiny-Swarm-World-worktrees/sonar-s5527-tls`.
- Use branch `fix/workflow-sonar-s5527-tls-20260623`.
- Fix SonarCloud issue `AZ7kEe623UILYpQnQ6zD`, rule `python:S5527`.
- Create or update a workflow for exactly this issue.
- Create workflow-execute-style slice evidence under
  `.codex/evidence/workflow-sonar-s5527-tls-20260623/`.
- Do not run live infrastructure commands.
- Run targeted checks where practical.
- Do not push, create a PR, or merge.

Interpreted Intent:

- Perform a scoped security-quality remediation for HTTPS preflight probing
  without changing live infrastructure behavior or unrelated workflow files.

Change Type:

- Python infrastructure adapter security remediation with focused regression
  tests and workflow evidence.

Affected Process Strand:

- `workflow create` for this issue-specific workflow.
- `workflow execute` style execution for the implementation slice.

Affected Architecture Area:

- Infrastructure adapter: host preflight probe.
- Infrastructure adapter unit tests.
- Workflow governance and evidence.

Explicit Requirements:

- Remove unverified TLS context creation from the reported source line.
- Keep work scoped to this issue and this worktree.
- Preserve Linux/WSL-only governance and avoid live infrastructure mutation.

Implicit Requirements:

- Preserve hexagonal architecture boundaries.
- Keep HTTPS probing behavior deterministic in unit tests.
- Do not weaken TLS verification or suppress the Sonar rule.

Assumptions:

- Local preflight HTTPS probes must use normal platform trust validation.
- Any self-signed local certificate failures should surface as probe failures
  rather than being bypassed by disabling TLS verification.

Non-Goals:

- No certificate store management.
- No live LXD, Incus, LXC, Docker, Docker Swarm, compose, or service bootstrap.
- No SonarCloud issue mutation through credentials.
- No push, PR creation, or merge.

Risks:

- Existing deployments with self-signed localhost certificates may now fail
  HTTPS content matching until the certificate chain is trusted.
- WSL cannot use Git in this worktree because the `.git` worktree pointer uses
  a Windows path. Git evidence is gathered with the host shell and this
  limitation is recorded in evidence.

Open Questions:

- None blocking.

Blocking Questions:

- None.

Confidence Level:

- `95%`

Decision:

- `READY_FOR_WORKFLOW`

## Five-Role Three Amigos Review

Senior Requirement Engineer:

- The issue identity, rule, branch, file, and non-goals are concrete.

Senior System Architect:

- The change remains inside infrastructure and does not affect domain or
  application services.

Senior Python Automation Developer:

- Replace the unverified HTTPS context with `ssl.create_default_context()` and
  keep HTTP probing unchanged.

Senior React Frontend Developer:

- No browser frontend or React scope.

Senior Tester:

- Extend existing preflight unit tests to verify certificate and hostname
  verification on HTTPS requests.

## Verified Baseline

- Branch: `fix/workflow-sonar-s5527-tls-20260623`.
- Local branch ref exists.
- Worktree was clean before implementation.
- Reported source line contained `ssl._create_unverified_context()` for HTTPS.
- Existing focused tests cover HTTPS preflight service matching.
- `documentation/arc42/**` was checked for architecture synchronization need;
  no arc42 update is required because architecture boundaries do not change.

## Target Outcome

- `host_preflight_probe.py` no longer creates unverified TLS contexts.
- HTTPS preflight probes use a verified default TLS context.
- Focused tests prove HTTPS requests carry a TLS context with certificate and
  hostname verification enabled.
- Evidence records branch, scope, distribution, consolidation, and checks.

## Scope

In scope:

- `src/tiny_swarm_world/infrastructure/adapters/preflight/host_preflight_probe.py`
- `tests/infrastructure/adapters/preflight/test_host_preflight_probe.py`
- `documentation/workflow/workflow.md`
- `documentation/workflow/context-pack.md`
- `documentation/workflow/context-pack.json`
- `.codex/evidence/workflow-sonar-s5527-tls-20260623/**`

Out of scope:

- Live infrastructure commands.
- Runtime certificate provisioning.
- Other SonarCloud issues.
- Push, PR creation, merge, or branch cleanup.

## Architecture Constraints

- Keep domain independent from infrastructure details.
- Keep application services dependent on ports, not concrete adapters.
- Keep TLS and urllib behavior inside the infrastructure adapter.
- Do not add Windows-specific runtime behavior.

## Python Automation Assessment

- The change uses the Python standard library TLS default context.
- No new dependency is introduced.
- No import-time side effect or constructor-time external command is added.

## Frontend Assessment

- No frontend module exists in scope and no browser or React behavior changes.

## Test Strategy

Targeted:

- `PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.preflight.test_host_preflight_probe`
- `python3 tools/quality_gate.py test`
- `git diff --check`

Required final when practical:

- `python3 tools/quality_gate.py quality`

## Ordered Slices

### Slice 01 - Workflow And Baseline Evidence

Purpose:

- Replace the stale active workflow with this issue-specific workflow and
  record baseline branch, scope, and WSL/Git limitations.

```yaml
slice_id: "01"
profile: "NORMAL_PATH"
owner: "Senior Workflow Architect"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior Tester"
affected_files:
  - "documentation/workflow/workflow.md"
  - "documentation/workflow/context-pack.md"
  - "documentation/workflow/context-pack.json"
  - ".codex/evidence/workflow-sonar-s5527-tls-20260623/status-check.md"
affected_modules: []
affected_contracts:
  - "workflow evidence"
dependencies: []
parallel_group: "governance"
file_locks:
  - "documentation/workflow/**"
  - ".codex/evidence/workflow-sonar-s5527-tls-20260623/**"
contract_locks:
  - "workflow evidence"
architecture_locks:
  - "hexagonal boundaries unchanged"
quality_gates:
  targeted:
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py test"
documentation:
  arc42: "Checked; no update required."
  adr: "No ADR required."
stop_conditions:
  - "Stop if branch or issue scope cannot be verified."
```

### Slice 02 - Verified TLS Context Remediation

Purpose:

- Remove unverified TLS context creation and add focused regression coverage.

```yaml
slice_id: "02"
profile: "NORMAL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Tester"
  - "Senior System Architect"
affected_files:
  - "src/tiny_swarm_world/infrastructure/adapters/preflight/host_preflight_probe.py"
  - "tests/infrastructure/adapters/preflight/test_host_preflight_probe.py"
affected_modules:
  - "tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe"
affected_contracts:
  - "HTTPS preflight probe TLS verification"
dependencies:
  - "01"
parallel_group: "implementation"
file_locks:
  - "src/tiny_swarm_world/infrastructure/adapters/preflight/host_preflight_probe.py"
  - "tests/infrastructure/adapters/preflight/test_host_preflight_probe.py"
contract_locks:
  - "TLS verification must remain enabled"
architecture_locks:
  - "infrastructure adapter only"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.preflight.test_host_preflight_probe"
    - "python3 tools/quality_gate.py test"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "No update required; adapter-internal security remediation."
  adr: "No ADR required."
stop_conditions:
  - "Stop if remediation requires disabling TLS verification elsewhere."
  - "Stop if live infrastructure validation would be required."
```

## Slice Dependency Graph

```text
01 -> 02
```

## Parallel Execution

- Sequential execution is selected.
- The slices are ordered because Slice 02 depends on the workflow and evidence
  scope established in Slice 01.
- No separate stream worktrees are used for this single-issue branch.

## Automatic Work Distribution Policy

- Affected streams: documentation, backend/infrastructure, tests, quality, and
  security.
- Real subagents were not used because the current environment exposes no
  callable subagent workers for safe isolated stream execution in this worktree.
- Role-based fallback review is recorded in evidence.

## Quality-Gate Expectations

- Run targeted preflight unit tests first.
- Run `python3 tools/quality_gate.py test` when practical.
- Run `git diff --check`.
- Do not run live infrastructure validation.

## Documentation Synchronization

- Active workflow and context pack are updated for this issue.
- arc42 was checked and does not need a content update because system structure
  and deployment behavior are unchanged.

## Stop Conditions

- Live infrastructure commands would be required.
- TLS verification would need to be disabled to keep behavior passing.
- Git branch or issue scope becomes unverifiable.
- Required tests fail for this scoped change.

## Definition Of Done

- No `ssl._create_unverified_context()` remains in the target file.
- HTTPS preflight probes use `ssl.create_default_context()`.
- Focused tests pass.
- Evidence is written under
  `.codex/evidence/workflow-sonar-s5527-tls-20260623/`.
- No push, PR, or merge is performed.

## Handoff To Workflow Execute

- Execute Slice 01, then Slice 02.
- Keep file changes within the declared locks.
- Record distribution and consolidation evidence for each slice.

## arc42 Check Status

- Checked `documentation/arc42/**`.
- No architecture documentation update required for this adapter-internal TLS
  verification remediation.
