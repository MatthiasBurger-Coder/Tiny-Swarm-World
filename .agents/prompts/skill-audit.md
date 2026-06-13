# Skill Audit Prompt

Use for auditing skill compatibility before workflow authoring or execution.

Use for `skills update` before changing skills, agents, roles, prompts, Codex agent definitions, routing rules, organigramm, skill registry or process documentation.

## Required Inputs

- `AGENTS.md`
- `QUALITY.md`
- active `documentation/workflow/**`
- `.agents/skills/**`
- `.agents/roles/**`
- `.agents/orchestrator/**`
- `.codex/skills/**`
- `.codex/agents/**`
- `documentation/adr/**`
- `documentation/skill-audit/**`

## Required Output

- skill inventory
- missing skills
- overlapping responsibilities
- conflict classification
- required specialist reviews
- blockers
- process strand classification
- `push auto` lifecycle eligibility for task-scoped changes, including Python
  product code and Python product-behavior tests

## Decision

Return `CONTINUE` only when no blocking skill or governance conflict remains.

For `skills update`, return `CONTINUE` only when the change belongs to skills,
agents, process-governance, or governance-only workflow documentation and no
Python product code, Python product-behavior tests, product implementation,
services, contracts, Docker/runtime, build logic, frontend or analytics files
are in scope.

For `push auto`, return `CONTINUE` only when the diff is task-scoped, no
unrelated or sensitive files are in scope, and the publication path can create
or reuse a pull request, wait or retry until required checks are green
including SonarQube when configured, merge, delete the merged remote head
branch and run local cleanup.
