# Workflow: Sonar S2083 Secret Test Path Remediation

Version: `sonar-s2083-path-v1.0.0`
Workflow ID: `workflow-sonar-s2083-path-20260623`
Created: `2026-06-23`
Branch: `fix/workflow-sonar-s2083-path-20260623`
Status: `IN_PROGRESS`
Evidence Root: `.codex/evidence/workflow-sonar-s2083-path-20260623/`

## Executive Summary

Remediate SonarCloud vulnerability `AZ7kEe0S3UILYpQnQ6zA`
(`pythonsecurity:S2083`, Blocker) in
`tests/application/services/deployment/test_secret_management.py`.

## Requirement Clarification Gate

Original Request:

- Work through all open SonarQube/SonarCloud vulnerability issues in logical
  order.
- Give each issue its own branch.
- Use subagents for non-overlapping issues.
- Execute through the ticket workflow.
- Verify that no matching SonarCloud vulnerability issues remain open.

Interpreted Intent:

- This workflow covers only the highest-priority Blocker issue for unsafe path
  construction in a secret-management regression test.

Change Type:

- Test security hardening and workflow evidence.

Affected Process Strand:

- `workflow execute`

Affected Architecture Area:

- Python test automation for deployment secret-management behavior.

Explicit Requirements:

- Preserve the test intent that the committed Pulsar compose file does not
  create a secret inventory blocker.
- Avoid unsafe temporary-path construction at the filesystem sink.
- Do not run live infrastructure commands.

Implicit Requirements:

- Preserve Linux/WSL-first repository behavior.
- Keep the fix isolated to the issue branch.
- Keep production deployment logic unchanged.

Assumptions:

- The Sonar finding is test-only and can be remediated with a small fixture
  writer that resolves and validates the temporary destination.

Non-Goals:

- No changes to the secret-discovery product implementation.
- No live Pulsar, Docker, LXC, Incus, LXD, or Swarm execution.

Risks:

- Over-broad fixture changes could weaken the committed-compose regression.

Open Questions:

- None.

Blocking Questions:

- None.

Confidence Level:

- `95%`

Decision:

- `READY_FOR_WORKFLOW`

## Five-Role Three Amigos Review

Senior Requirement Engineer:

- Scope is concrete: one SonarCloud Blocker issue in one test file.

Senior System Architect:

- No domain, application service, adapter, runtime, or composition boundary
  change is required.

Senior Python Automation Developer:

- Add a small test helper that resolves the temporary root and validates the
  fixture destination before writing.

Senior React Frontend Developer:

- No browser or React frontend impact.

Senior Tester:

- Run the focused secret-management unittest and local quality gate where
  practical.

## Verified Baseline

- SonarCloud API reported issue `AZ7kEe0S3UILYpQnQ6zA` open on
  `2026-06-23`.
- Current branch is `fix/workflow-sonar-s2083-path-20260623`.
- Working tree was clean before branch creation.

## Target Outcome

- The test no longer writes through an unchecked path expression.
- The Pulsar compose regression still reads the committed compose fixture.
- The matching SonarCloud issue is expected to disappear after PR analysis.

## Scope

In scope:

- `tests/application/services/deployment/test_secret_management.py`
- `documentation/workflow/**`
- `.codex/evidence/workflow-sonar-s2083-path-20260623/**`

Out of scope:

- Production secret-management behavior.
- Live infrastructure validation.

## Architecture Constraints

- Keep production code unchanged unless the test proves a real product defect.
- Preserve hexagonal boundaries.

## Test Strategy

Targeted:

- `PYTHONPATH=src python -m unittest tests.application.services.deployment.test_secret_management`

Required final:

- `python3 tools/quality_gate.py test`

## Ordered Slices

### Slice 01 - Fixture Path Hardening

Purpose:

- Fix the Sonar S2083 finding with a validated temporary fixture writer and
  record workflow evidence.

```yaml
slice_id: "01"
profile: "NORMAL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Tester"
  - "Senior System Architect"
affected_files:
  - "tests/application/services/deployment/test_secret_management.py"
  - "documentation/workflow/workflow.md"
  - "documentation/workflow/context-pack.md"
  - "documentation/workflow/context-pack.json"
  - ".codex/evidence/workflow-sonar-s2083-path-20260623/slice-01-distribution.md"
  - ".codex/evidence/workflow-sonar-s2083-path-20260623/slice-01-consolidation.md"
affected_modules:
  - "tests.application.services.deployment.test_secret_management"
affected_contracts:
  - "secret-management regression fixture path"
dependencies: []
parallel_group: "s2083"
file_locks:
  - "tests/application/services/deployment/test_secret_management.py"
  - "documentation/workflow/**"
  - ".codex/evidence/workflow-sonar-s2083-path-20260623/**"
contract_locks:
  - "secret-management fixture writing"
architecture_locks:
  - "production code unchanged"
quality_gates:
  targeted:
    - "PYTHONPATH=src python -m unittest tests.application.services.deployment.test_secret_management"
  required:
    - "python3 tools/quality_gate.py test"
documentation:
  arc42: "No arc42 update required; test-only security hardening."
  adr: "No ADR required."
stop_conditions:
  - "Stop if production behavior must change."
  - "Stop if the committed Pulsar compose fixture is no longer exercised."
```

## Parallel Execution

- Can this workflow run in parallel? Yes, with other workflows that do not
  touch this test file or active workflow files in the same worktree.
- Conflicting workflows: other active-workflow documentation edits in the same
  worktree.
- Shared files: none with the S5527 or S2068 worktrees.
- Shared infrastructure: none.
- Requires isolated worktree: yes for parallel execution.
- Requires serialized live validation: live validation is not allowed.
- Merge-order constraints: merge independently after checks pass.

## Automatic Work Distribution Policy

- Slice `01` runs sequentially in this branch because implementation and test
  fixture evidence are tightly coupled.
- Other SonarCloud issues are handled in separate worktrees where file locks
  are disjoint.
- Codex remains final integration owner.

## Git Worktree Execution Rule

- Parallel work uses isolated worktrees and issue branches.
- Subagents must not merge directly.
- This branch may be published only through the guarded `push auto` lifecycle.

## Definition Of Done

- Targeted secret-management unittest passes.
- Required quality gate is run or any blocker is reported.
- Evidence records the SonarCloud finding and fix.
- Follow-up SonarCloud API verification reports the issue absent or no longer
  open after PR analysis.

## Handoff To Workflow Execute

- Execute Slice `01`.
- Do not run live infrastructure commands.
