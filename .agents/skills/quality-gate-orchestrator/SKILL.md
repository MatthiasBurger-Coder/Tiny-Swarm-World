---
name: quality-gate-orchestrator
description: Use to plan, execute, classify and report workflow slice quality gates from QUALITY.md without weakening required build, test, coverage, architecture or dependency verification rules.
---

# Skill: Quality Gate Orchestrator

## Mission

Ensure every workflow slice has appropriate verification, every required quality gate comes from `QUALITY.md`, and failed required gates block commit and push.

This skill orchestrates quality evidence. It does not weaken tests, lower coverage thresholds or approve red gates.

## Responsibilities

- Read `QUALITY.md` before documenting quality commands.
- Classify the change through `quality-impact-classifier` before selecting commands.
- Define narrow targeted checks for each slice.
- Identify when Python minimum or full local gates are required.
- Distinguish required, optional, unavailable and not-applicable checks.
- Require failure reports for failed or skipped required gates.
- Preserve exact command evidence for verification claims.
- Ensure commit and push are blocked by failed required gates.

## Authority

The Quality Gate Orchestrator may block slice continuation, commit readiness or push readiness when required gates fail, are missing or cannot be verified.

## D8 And Q11 Boundary

`D8` is the synchronous blocking quality decision for workflow-execute commit,
checkpoint push and release readiness. It blocks on failed build, failed tests,
architecture violation, missing required documentation, missing workflow
version or failed required quality gate.

`Q11` is asynchronous reporting after the checkpoint path reaches `CP_FINAL`.
It is non-blocking by default for commit, checkpoint push, normal PR creation
and release preparation. Regulatory or compliance reporting blocks only when
the active workflow explicitly declares that report as a `D8` requirement.

## Forbidden

- Do not invent quality tasks, scripts or CI jobs.
- Do not claim a gate passed unless the exact command ran.
- Do not treat `git diff --check` as a replacement for required Python gates.
- Do not lower coverage or architecture thresholds.
- Do not mark failed required gates as non-blocking.
- Do not require live external services for default unit-test gates unless documented by the repository.

## Inputs

- `QUALITY.md`
- active workflow
- changed files
- Python tooling files when task verification is needed
- CI workflows when pipeline behavior is changed
- test, typecheck, import-linter and architecture-test output
- prior failure reports

## Outputs

- slice quality plan
- quality result report
- failure-handling report
- typed error-router classification, owner, retry count, next action and rerun command
- required gate classification
- commit-readiness quality summary

## Collaboration Rules

- Use `quality-impact-classifier` before selecting required, optional and
  not-applicable commands.
- Consult Senior Tester for test strategy and regression coverage.
- Consult Senior DevOps for CI, Docker, deployment or build tooling checks.
- Consult Senior System Architect for import-linter, architecture tests and architecture-sensitive checks.
- Consult Security & Threat Modeling for security checks.
- Consult Release & Branch Governance before commit or push.

## STOP Rules

Stop and report when:

- `QUALITY.md` cannot be read;
- a required quality command cannot be verified;
- build, tests, coverage, dependency verification or architecture checks fail;
- a workflow plans commit or push despite failed required gates;
- a failure has no summary, owner or next action;
- a workflow-execute failure has no Typed Error Router category;
- automatic targeted-fix retries would exceed `maxRetries = 3`;
- continuing would require guessing task names or quality authority.
