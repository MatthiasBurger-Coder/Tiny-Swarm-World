# Skills Update Process

Use this process when updating `.agents` or `.codex` skills, roles, prompts,
or workflow governance.

## Process

1. Read `AGENTS.md`, `QUALITY.md`, and
   `documentation/process/issue-completion-discipline.md`.
2. Read `documentation/process/skills/audit/skill-registry.md`,
   `documentation/process/skills/audit/skill-registry.json`,
   `documentation/process/skills/audit/organigramm.md`, and
   `documentation/process/skills/audit/owner-map.md` when they exist.
3. Identify the affected skills, roles, prompts, or routing rules.
4. Keep root project rules authoritative over reusable templates.
5. Preserve Python automation as the primary architecture for Tiny Swarm World.
6. Keep project skills discoverable as `.agents/skills/<name>/SKILL.md`.
7. Ensure issue-driven skills either apply the completion discipline
   requirement matrix, evidence, verification and status rules or document why
   they are review-only and N/A.
8. Route console/status UI work to terminal-oriented skills, not browser React
   roles.
9. Route service-boundary concerns by exact need: decomposition, runtime
   readiness, migration safety, contract governance, or Senior System Architect
   escalation.
10. Stop if Python product code, Python product-behavior tests, or other
    product implementation files would be changed.
11. Prepare optional `push auto` only when explicitly requested and only
    through the full commit, pull request, green required-checks, SonarQube
    when configured, merge and cleanup lifecycle.
12. Run `git diff --check` and the quality gate required by `QUALITY.md` when practical.

## Stop Conditions

Stop when ownership, routing, quality authority, completion-discipline
authority, registry paths, organigramm paths, or project-specific overrides are
unclear.

Stop when a change would classify Tiny Swarm World as forensic analytics, a
Spring Boot application, a React frontend project, or Kubernetes-first without a
separate verified workflow.
