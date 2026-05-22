# Skills Update Prompt

Use when the user writes `skills update`.

This command activates the `skills-agents` strand.

It may create, update, audit or reconnect skills, agents, roles, prompts, Codex agent definitions, routing rules, organigramm, skill registry and process documentation.

It must not implement backend, frontend, Docker/runtime, contracts, persistence, analysis-engine, Joern, JavaParser, BTM generator or analytics behavior.

The skills-agents flow stops on review failures by default. If a workflow explicitly authorizes automatic correction attempts, cap them at `maxRetries = 3` and then escalate to the Root Architect.

Required flow:

1. Load AGENTS.md.
2. Load QUALITY.md.
3. Load documentation/process/skills-update.md.
4. Load documentation/process/skill-agent-creation.md.
5. Load documentation/agents/skill-registry.md.
6. Load documentation/agents/organigramm.md.
7. Inspect current skills, roles, prompts and Codex agents.
8. Run integrity, linkage, conflict, organigramm, registry and documentation checks.
9. Apply only skills-agents changes.
10. Stop if product implementation files would be changed.
11. Prepare for optional push auto only when the user explicitly requests push auto.

`skills update` is not `workflow create`.
`skills update` is not `workflow execute`.
`skills update` is not `push auto`.
