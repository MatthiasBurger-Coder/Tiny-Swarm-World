---
name: platform-reset-and-recovery
description: Use for reset, cleanup and recovery guidance for Tiny Swarm World platform workflows.
---

# Platform Reset And Recovery

## Purpose

Guide safe reset and recovery planning for local platform automation without
performing destructive operations by default.

## Responsibilities

- Identify rollback, cleanup and recovery ownership.
- Keep destructive commands explicit, guarded and user-authorized.
- Preserve state, logs and evidence needed for diagnosis.

## Inputs

- Workflow slice, platform docs, scripts and failure reports.
- Root safety rules and current verification evidence.
- Affected service or VM boundary.

## Outputs

- Recovery plan, rollback notes and safety checklist.
- STOP report for destructive or ambiguous cleanup.

## Boundaries

- Do not run destructive VM, Docker, network or filesystem cleanup commands
  unless explicitly requested.
- Do not delete generated or legacy files without reference checks.

## STOP conditions

- Target resource or rollback reference is unclear.
- Cleanup would affect files outside the active scope.
- Recovery requires live infrastructure mutation without user approval.

## Collaboration with other skills

- Pair with `platform-verification`.
- Pair with `resilience-engineering`.
- Pair with `release-branch-governance` for rollback governance.

## Quality expectations

- Document exact skipped live actions.
- Run `git diff --check` for recovery documentation changes.
