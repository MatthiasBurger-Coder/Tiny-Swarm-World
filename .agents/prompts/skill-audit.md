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
- `push auto` eligibility for skills-agents changes

## Decision

Return `CONTINUE` only when no blocking skill or governance conflict remains.

For `skills update`, return `CONTINUE` only when the change belongs to `skills-agents` and no product implementation, services, contracts, Docker/runtime, build logic, frontend or analytics files are in scope.
