---
name: engineering-governance
description: Use as umbrella governance for synchronizing EPIC, requirements, arc42, ADR references, workflows, quality gates, resilience requirements, architecture consistency checks, documentation consistency checks, skills, roles, and Codex agent coordination.
---

# Skill: Engineering Governance

## Purpose

Coordinate requirement, architecture, workflow, quality, resilience and agent-governance changes.

This skill applies repository rules. It does not replace root `AGENTS.md` or `QUALITY.md`.

## Required Inputs

Inspect the relevant subset of:

- user request
- `AGENTS.md`
- `QUALITY.md`
- `documentation/process/issue-completion-discipline.md`
- `documentation/epics`
- `documentation/arc42`
- `documentation/adr`
- `documentation/workflow`
- `.agents/skills`
- `.agents/roles`
- `.agents/orchestrator`
- `.codex/agents`
- affected source, tests, build or CI files

## Related Skills

Use these skills for focused work:

- `workflow-authoring` for full workflow lifecycle and slice plans
- `requirement-engineering` for EPIC and requirement drift
- `arc42-architecture-governance` for architecture documentation synchronization
- `documentation-sync` for documentation consistency
- `quality-gate` or `quality-gate-governance` for verification commands

## Synchronization Model

Keep these artifacts aligned:

```text
EPIC
  <-> requirements
  <-> arc42
  <-> ADR references
  <-> documentation/workflow
  <-> skills
  <-> roles
  <-> QUALITY.md
```

## Governance Checkpoints

Run governance checks:

- before creating a new workflow
- before changing architecture documentation
- before moving responsibilities across service boundaries
- before adding resilience behavior
- before changing quality-gate expectations
- before aligning existing skills or roles
- before marking issue-driven work complete
- before commit readiness review

## Architecture Rules

Require:

- no silent architecture drift
- no undocumented service boundary changes
- no undocumented resilience changes
- no undocumented deployment changes
- no stale EPIC assumptions
- no stale workflow slices
- no hidden compatibility governance

## Validation Checklists

### EPIC Consistency

- Current EPIC source identified.
- Requirement traces to EPIC, user request or verified implementation.
- EPIC assumptions still match implementation.
- Drift is recorded or ruled out.
- Unresolved conflicts are documented.

### arc42 Consistency

- Relevant arc42 sections reviewed.
- Architecture changes are reflected in the correct section.
- Runtime and deployment changes are documented when applicable.
- Planned behavior is not described as implemented behavior.

### Workflow Consistency

- Dedicated workflow branch created, checked out and verified before any workflow artifact is created or modified: `workflow.md`, `documentation/workflow/**`, workplans, slice definitions, workflow-specific documentation changes, implementation tasks or write-capable agent assignments.
- Working tree checked before branch creation; unrelated or unclear uncommitted changes stop workflow creation.
- Detached or unclear branch state and unresolved local or remote branch-name collisions stop workflow creation.
- No workflow creation or implementation work runs on `main`, `master`, `develop` or another shared branch.
- `documentation/workflow` deleted before new workflow generation, unless the user explicitly asks to preserve an existing workflow.
- Full workflow structure regenerated.
- No stale slices remain.
- Dependencies, parallelization, stop conditions and verification commands are explicit.

### Resilience Consistency

- Timeout, retry, circuit-breaker, bulkhead, health-check, cleanup or degraded-mode behavior is documented.
- Failure modes preserve state and diagnostic integrity.
- Tests or quality checks are planned where practical.

### Service Boundary Consistency

- Inbound and outbound responsibilities are named.
- Communication protocols are documented.
- Runtime, persistence and UI ownership are clear.
- Ambiguous ownership stops the work.

### Quality Gate Consistency

- `QUALITY.md` reviewed.
- Python quality-gate commands verified before documentation.
- Minimum and full local quality gates recorded when relevant.
- `git diff --check` run before commit readiness.

### Issue Completion Consistency

- `documentation/process/issue-completion-discipline.md` reviewed for
  issue-driven work.
- Requirement matrix exists before implementation.
- Every requirement maps to implementation evidence and verification evidence.
- Required `.tiny-swarm/evidence/<workflow-or-issue-id>/` files exist before
  `DONE`.
- `issue-completion-auditor` review is recorded before a final completion
  claim.
- Open or unverified requirements force `INCOMPLETE`, `BLOCKED` or `FAILED`,
  never `DONE`.

## Stop Conditions

Stop and report if:

- architecture conflicts are unclear
- EPIC contradicts implementation
- multiple workflows conflict
- service ownership is ambiguous
- resilience expectations are unclear
- quality-gate authority is unclear
- issue requirements, requirement matrix, evidence path or completion authority
  are unclear
- a governance decision would require guessing

## Expected Outputs

- synchronized governance plan or patch
- checklist results
- affected artifact list
- unresolved conflicts
- exact verification evidence
