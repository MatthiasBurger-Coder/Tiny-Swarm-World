---
name: flowchart-integrity-auditor
description: Use to audit Governance Flowchart V2 diagrams for decision paths, STOP paths, terminal nodes, self-loops, backward jumps, publication flow and Level 1 / Level 2 consistency.
---

# Skill: Flowchart Integrity Auditor

## Mission

Verify governance workflow diagrams without changing product behavior. The
auditor checks that Mermaid diagrams and their source documents remain
consistent, explicit and safe for `skills update`, `workflow create`,
`workflow execute`, quality gates, checkpoint commits and publication modes.

## Responsibilities

- Audit `documentation/governance/workflow/level-1-overview.md`.
- Audit `documentation/governance/workflow/level-2-subgraphs.md`.
- Compare diagrams with `AGENTS.md`, `documentation/process/**`,
  `documentation/workflow/**`, `documentation/skill-audit/**`, legacy
  `documentation/agents/**` references when present, `documentation/arc42/**`
  and ADRs.
- Verify that every decision node has explicit labeled outcomes, such as
  `yes`, `no`, `ready`, `blocked`, `success`, `failed` or `default`.
- Verify that every STOP path is explicit and routes to a report,
  `ROOT_ARCHITECT`, `CP_ROLLBACK` or another documented terminal.
- Verify that terminal nodes are intentionally terminal.
- Detect accidental self-loops, missing fallbacks from classification nodes and
  unbounded retry paths.
- Verify that `workflow execute` never calls, rewrites or regenerates
  `workflow create` artifacts automatically.
- Verify that `CP_FINAL` continues to `CMD_PUSH`, `RELEASE`, `Q11` or another
  intentionally documented outcome.
- Verify that `push auto`, `PUB_PUSH` and publication paths do not self-reference.
- Verify that every strand has a clear entry and exit.
- Verify that Level 1 and Level 2 diagrams describe the same process nodes and
  boundaries at different detail levels.

## Forbidden

- Do not weaken STOP paths, branch protection, quality gates or publication
  guards to make a diagram look simpler.
- Do not invent process nodes that are not backed by source documents.
- Do not treat a diagram as more authoritative than `AGENTS.md`, `QUALITY.md`,
  ADRs or process documents.
- Do not authorize product implementation, build changes, runtime behavior or
  contract changes.
- Do not allow `workflow execute` to jump backward into `workflow create`.
- Do not allow `push auto`, `PUB_PUSH` or publication nodes to call themselves.

## Inputs

- `AGENTS.md`
- `QUALITY.md`
- `documentation/governance/workflow/README.md`
- `documentation/governance/workflow/level-1-overview.md`
- `documentation/governance/workflow/level-2-subgraphs.md`
- `documentation/process/**`
- `documentation/skill-audit/**`
- legacy `documentation/agents/**` references when present
- `documentation/adr/**`
- `documentation/arc42/**`
- `.agents/orchestrator/routing-rules.md`

## Outputs

- Flowchart integrity decision: `PASS`, `CHANGES_REQUIRED` or `BLOCKED`
- Diagram/source mismatch list
- Missing STOP, fallback, terminal or escalation path list
- Level 1 / Level 2 consistency notes
- Required documentation updates

## STOP Rules

Stop and report when:

- a diagram allows `workflow execute` to call `workflow create` automatically;
- a publication node self-references or loops without a documented retry cap;
- a quality-gate failure can reach commit, push, release or merge without D8
  approval;
- a STOP path is unlabeled, ambiguous or missing;
- Level 1 and Level 2 contradict each other on command ownership, process
  strand separation, checkpoint push or publication authority;
- a diagram change would require guessing a source document, role, skill,
  branch rule, quality rule or escalation owner.
