---
name: acceptance-checks
description: Use for defining done criteria and verification evidence for Tiny Swarm World slices.
---

# Acceptance Checks

## Purpose

Define concrete acceptance checks for Tiny Swarm World workflow slices and
automation changes.

## Responsibilities

- Convert requirements into observable, repository-verifiable checks.
- Identify required files, commands and documentation updates.
- Keep assumptions, evidence and unresolved risks separate.

## Inputs

- User request, workflow slice and requirement notes.
- Root `AGENTS.md`, `QUALITY.md` and relevant docs.
- `documentation/process/issue-completion-discipline.md` for issue-driven
  work.
- Current changed files.

## Outputs

- Acceptance checklist and verification command list.
- Residual risk and blocker notes.
- Requirement-to-verification mapping for each acceptance criterion.

## Boundaries

- Do not treat generated text or inferred runtime state as verified evidence.
- Do not require product source or live infrastructure changes for governance
  slices.

## STOP conditions

- Acceptance criteria cannot be verified from repository evidence.
- A requirement from the matrix has no implementation evidence or verification
  evidence.
- A check would require forbidden live infrastructure execution.
- The changed file set escapes the active slice.

## Collaboration with other skills

- Pair with `bdd-expert` for scenario language.
- Pair with `platform-quality-gates` for command selection.
- Pair with `workflow-slice-execution` for handoff evidence.

## Quality expectations

- Include `git diff --check` for documentation and governance slices.
- Include focused tests when behavior changes.
- Record skipped full gates honestly.
