# Skills Update Process

Use this process when updating `.agents` or `.codex` skills, roles, prompts,
or workflow governance.

## Process

1. Read `AGENTS.md` and `QUALITY.md`.
2. Identify the affected skills, roles, prompts, or routing rules.
3. Keep root project rules authoritative over reusable templates.
4. Preserve Python automation as the primary architecture for Tiny Swarm World.
5. Run `git diff --check` and the quality gate required by `QUALITY.md` when practical.

## Stop Conditions

Stop when ownership, routing, quality authority, or project-specific overrides are unclear.
