# Workflow: Sonar S2068 Port Forwarding Test Remediation

Version: `workflow-sonar-s2068-port-forwarding-v1.0.0`
Workflow ID: `workflow-sonar-s2068-port-forwarding-20260623`
Created: `2026-06-23`
Branch: `fix/workflow-sonar-s2068-port-forwarding-20260623`
Status: `EXECUTED_WITH_EVIDENCE`
Evidence Root: `.codex/evidence/workflow-sonar-s2068-port-forwarding-20260623/`

## Executive Summary

Remediate three overlapping SonarCloud `python:S2068` vulnerability issues in
`tests/domain/network/test_port_forwarding_plan.py` without weakening the
domain test intent. The issues all sit in the same test file and validate the
same port-forwarding metadata guard, so this workflow executes them as one
serial issue group in the current dedicated worktree.

## Requirement Clarification Gate

Original Request:

- Work in existing worktree
  `D:/Projects/Tiny-Swarm-World-worktrees/sonar-s2068-port-forwarding`.
- Use branch `fix/workflow-sonar-s2068-port-forwarding-20260623`.
- Fix SonarCloud issues `AZ7kcUaJ8N9AxeIuoSBi`,
  `AZ7kcUaJ8N9AxeIuoSBj`, and `AZ7kcUaJ8N9AxeIuoSBl`.
- Rule: `python:S2068`.
- File and lines: `tests/domain/network/test_port_forwarding_plan.py` lines
  166, 167, and 182.
- The three issues overlap in one test file and must be handled serially.
- Do not run live infrastructure commands.
- Update workflow documentation and evidence.
- Run targeted unittest for `tests.domain.network.test_port_forwarding_plan`.
- Do not push, create a PR, or merge.

Interpreted Intent:

- Replace hardcoded credential-looking URL literals in tests with existing
  Sonar-safe test literal helpers while preserving assertions that credential
  URLs and URL-like route hosts are rejected.

Change Type:

- Test-data remediation and workflow evidence update.

Execution Profile:

- `NORMAL_PATH`

Affected Process Strand:

- `workflow execute`

Affected Architecture Area:

- Domain tests only.

Explicit Non-Goals:

- No production domain behavior change.
- No live LXD, Incus, LXC, Docker, Swarm, compose, networking, or service
  bootstrap commands.
- No push, PR creation, or merge.

## Five-Role Review

Senior Requirement Engineer:

- The issue group is concrete and bounded to three Sonar findings in one test
  file.

Senior System Architect:

- The change is test-only and does not affect hexagonal boundaries.

Senior Python Automation Developer:

- Existing helper `tests.support.sonar_safe_literals` is the appropriate local
  pattern for constructing sensitive-looking test strings without hardcoded
  credential literals.

Senior Tester:

- The targeted unittest must prove the rejection behavior still holds for
  credential URL metadata and URL-like route hosts.

Senior DevOps Engineer:

- No live infrastructure validation is needed or allowed for this unit-test
  remediation.

## Scope

In scope:

- `tests/domain/network/test_port_forwarding_plan.py`
- `documentation/workflow/workflow.md`
- `documentation/workflow/context-pack.md`
- `documentation/workflow/context-pack.json`
- `.codex/evidence/workflow-sonar-s2068-port-forwarding-20260623/**`

Out of scope:

- Product source changes.
- Live infrastructure commands.
- Push, PR creation, merge, or branch cleanup.

## Ordered Slices

### Slice 01 - S2068 Test Literal Remediation

Purpose:

- Remove hardcoded credential-looking URL literals from the affected domain
  test while preserving the credential URL rejection scenarios.

```yaml
slice_id: "01"
profile: "NORMAL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Tester"
  - "Senior System Architect"
affected_files:
  - "tests/domain/network/test_port_forwarding_plan.py"
  - "documentation/workflow/workflow.md"
  - "documentation/workflow/context-pack.md"
  - "documentation/workflow/context-pack.json"
  - ".codex/evidence/workflow-sonar-s2068-port-forwarding-20260623/slice-01-distribution.md"
  - ".codex/evidence/workflow-sonar-s2068-port-forwarding-20260623/slice-01-consolidation.md"
affected_modules:
  - "tests.domain.network.test_port_forwarding_plan"
affected_contracts:
  - "port registry unsafe metadata rejection tests"
dependencies: []
parallel_group: "serial-overlapping-test-file"
file_locks:
  - "tests/domain/network/test_port_forwarding_plan.py"
  - "documentation/workflow/**"
  - ".codex/evidence/workflow-sonar-s2068-port-forwarding-20260623/**"
contract_locks:
  - "Sonar python:S2068 issue group AZ7kcUaJ8N9AxeIuoSBi/AZ7kcUaJ8N9AxeIuoSBj/AZ7kcUaJ8N9AxeIuoSBl"
architecture_locks:
  - "domain tests only; no production architecture change"
quality_gates:
  targeted:
    - "PYTHONPATH=src python -m unittest tests.domain.network.test_port_forwarding_plan"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py test"
documentation:
  arc42: "No arc42 update required; no architecture behavior changes."
  adr: "No ADR required; test literal remediation only."
stop_conditions:
  - "Stop if the remediation weakens credential URL rejection coverage."
  - "Stop if live infrastructure commands would be needed."
  - "Stop if branch or worktree differs from the requested workflow branch."
```

## S3/S3D Execution Decision

- `S3_STATUS`: clean worktree required before implementation.
- `S3_BRANCH`: active branch must be
  `fix/workflow-sonar-s2068-port-forwarding-20260623`.
- `S3_SCOPE`: only the files listed in scope are authorized.
- `S3_CLASSIFY`: tests, quality, documentation.
- `S3D`: one executable slice, no dependency cycle, overlapping issue lines in
  one file, sequential execution required.

## Automatic Work Distribution

The three Sonar issues overlap in the same test file and share the same
behavioral assertion. Parallel implementation streams are rejected because they
would contend on `tests/domain/network/test_port_forwarding_plan.py`.

Read-only specialist review may run in parallel with workflow preparation, but
write-capable implementation stays serial in this worktree.

## Quality Strategy

Targeted:

- `PYTHONPATH=src python -m unittest tests.domain.network.test_port_forwarding_plan`
- `git diff --check`

Required final when practical:

- `python3 tools/quality_gate.py test`

## Definition Of Done

- The three hardcoded credential-looking URL literals are removed from the
  affected test file.
- The test still covers credential URL metadata rejection and URL-like
  `route_host` rejection.
- Targeted unittest passes.
- `git diff --check` passes.
- `python3 tools/quality_gate.py test` passes.
- Evidence is written under
  `.codex/evidence/workflow-sonar-s2068-port-forwarding-20260623/`.
- No push, PR, or merge is performed.

## Execution Outcome

- SonarCloud issues `AZ7kcUaJ8N9AxeIuoSBi`, `AZ7kcUaJ8N9AxeIuoSBj`, and
  `AZ7kcUaJ8N9AxeIuoSBl` were handled as one serial issue group.
- The affected test now constructs userinfo URLs through
  `tests.support.sonar_safe_literals.sample_url` and `sample_text`.
- No production code was changed.
- Targeted unittest, repository test gate, and diff whitespace validation
  passed.
