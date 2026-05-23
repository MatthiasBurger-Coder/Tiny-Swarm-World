# Skills Update Process

Use this process when updating `.agents` or `.codex` skills, roles, prompts,
or workflow governance.

## Process

1. Read `AGENTS.md` and `QUALITY.md`.
2. Read `documentation/skill-audit/skill-registry.md`,
   `documentation/skill-audit/skill-registry.json`,
   `documentation/skill-audit/organigramm.md`, and
   `documentation/skill-audit/owner-map.md` when they exist.
3. Identify the affected skills, roles, prompts, or routing rules.
4. Keep root project rules authoritative over reusable templates.
5. Preserve Python automation as the primary architecture for Tiny Swarm World.
6. Keep project skills discoverable as `.agents/skills/<name>/SKILL.md`.
7. Route console/status UI work to terminal-oriented skills, not browser React
   roles.
8. Route service-boundary concerns by exact need: decomposition, runtime
   readiness, migration safety, contract governance, or Senior System Architect
   escalation.
9. Run `git diff --check` and the quality gate required by `QUALITY.md` when practical.

## Stop Conditions

Stop when ownership, routing, quality authority, registry paths, organigramm
paths, or project-specific overrides are unclear.

Stop when a change would classify Tiny Swarm World as forensic analytics, a
Spring Boot application, a React frontend project, or Kubernetes-first without a
separate verified workflow.
