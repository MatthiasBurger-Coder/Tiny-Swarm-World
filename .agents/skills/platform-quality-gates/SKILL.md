---
name: platform-quality-gates
description: Use for selecting Tiny Swarm World verification gates without live infrastructure side effects.
---

# Platform Quality Gates

## Purpose

Select and report verification commands for Tiny Swarm World platform work
without weakening root `QUALITY.md`.

## Responsibilities

- Map a slice to lint, architecture, typecheck, test and documentation checks.
- Keep full quality gate evidence separate from skipped or not-applicable checks.
- Prevent Docker, Multipass or service bootstrap operations from entering the
  default gate.

## Inputs

- Root `QUALITY.md`.
- Active workflow slice and changed file set.
- Current git diff and relevant test files.

## Outputs

- Required and targeted quality commands.
- Pass, fail, skipped and residual-risk summary.

## Boundaries

- Do not replace the Python quality gate with Maven, Gradle, JUnit or Java
  checks unless the task explicitly targets the Java example.
- Do not lower thresholds or remove architecture checks.

## STOP conditions

- A required command is missing or inconsistent with `QUALITY.md`.
- A gate fails and no safe scoped fix is available.
- Verification would require live infrastructure.

## Collaboration with other skills

- Pair with `quality-gate`, `quality-gate-orchestrator` and `senior-tester`.
- Pair with `devops-docker` only when Docker workflow documentation changes.
- Escalate architecture failures to `hexagonal-architecture-expert`.

## Quality expectations

- Prefer `python3 tools/quality_gate.py quality` before commit or push.
- Use `git diff --check` for governance-only changes.
- Report exact commands and results.
