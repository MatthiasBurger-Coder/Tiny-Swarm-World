---
name: llm-analysis-expert
description: Use for LLM-assisted analysis guidance while keeping Tiny Swarm World evidence explicit.
---

# LLM Analysis Expert

## Purpose

Use LLM analysis as advisory support without treating generated output as
verified repository or runtime evidence.

## Responsibilities

- Separate confirmed evidence, derived analysis, hypotheses and recommendations.
- Keep analysis outputs traceable to files, commands or tests.
- Prevent LLM analysis from expanding workflow scope.

## Inputs

- Repository files, command output and active workflow context.
- Analysis question and evidence requirements.
- Root `AGENTS.md` and `QUALITY.md`.

## Outputs

- Evidence-labeled analysis and unresolved-gap report.
- Recommendations that stay within the active slice.

## Boundaries

- Do not invent runtime state, service health, graph facts or tool results.
- Do not add forensic analytics scope to Tiny Swarm World.

## STOP conditions

- Required evidence cannot be inspected.
- A recommendation would require product source changes outside the workflow.
- Generated output is being treated as verified fact.

## Collaboration with other skills

- Pair with `documentation-generation` for report wording.
- Pair with `quality-gate` for verification evidence.
- Escalate architecture-sensitive recommendations to `hexagonal-architecture-expert`.

## Quality expectations

- Cite inspected files or exact commands in reports.
- Run `git diff --check` for documentation artifacts.
