---
name: agent-handoff-protocol
description: Use to define and validate handoffs between workflow roles, callable subagents and reviewers so slice execution has explicit ownership, inputs, outputs, status and blockers.
---

# Skill: Agent Handoff Protocol

## Mission

Make agent and role handoffs explicit, auditable and deadlock-resistant during workflow execution.

This skill governs coordination artifacts. It does not implement product functionality and does not override specialist review authority.

## Responsibilities

- Define required fields for every handoff.
- Define status transitions for slices and review work.
- Ensure each slice has exactly one accountable owner at a time.
- Ensure input artifacts, output expectations, assumptions, blockers and validation state are explicit.
- Prevent parallel work on the same files unless ownership and ordering are documented.
- Require isolated Git worktrees for parallel `workflow execute` streams.
- Ensure stream handoffs record whether real subagents or fallback role-based
  reviews were used.
- Preserve review provenance for architecture, quality, security, API, data ownership and release decisions.

## Authority

The Agent Handoff Protocol may block parallel or delegated work when:

- the target agent or role is not verified;
- inputs or outputs are ambiguous;
- blockers are unclassified;
- file ownership overlaps;
- a handoff chain is cyclic without orchestrator decision.

## Forbidden

- Do not invent agents, roles, files, contracts or expected outputs.
- Do not allow handoff status to hide unresolved blockers.
- Do not mark work `DONE` before required validation is complete or explicitly documented as not applicable.
- Do not allow a reviewer to become the sole implementer of the decision it reviews.
- Do not use handoff artifacts as a substitute for quality-gate evidence.

## Inputs

- Active `documentation/workflow/**`
- `.agents/orchestrator/**`
- `.agents/roles/**`
- `.agents/skills/**`
- `.codex/agents/**` when callable subagents are used
- current git status and changed-file ownership
- slice outputs and validation evidence

## Outputs

- handoff contract
- status model
- handoff report
- blocker classification
- owner and reviewer map
- stream distribution and consolidation summary
- validation handoff summary

## Collaboration Rules

- Use with `agent-swarm-coordination-specialist` for multi-agent execution.
- Use with `workflow-executor` for slice-by-slice execution.
- Use with `workflow-conflict-resolution` when files or ownership overlap.
- Use with `quality-gate-orchestrator` before declaring a slice ready for commit.
- Use with specialist skills whenever a handoff crosses architecture, API, data, security, observability or release boundaries.

## STOP Rules

Stop and report when:

- `target_agent` or target role is undefined;
- required input artifacts are missing;
- output expectations are unclear;
- blockers are not classified;
- validation status is unknown;
- parallel work would modify the same files without explicit ownership and merge order;
- parallel stream work would run without isolated worktrees;
- a stream worker would merge directly to the main workflow branch;
- a handoff chain is cyclic and no orchestrator decision resolves it;
- continuing would require guessing another agent's assumptions or outputs.
