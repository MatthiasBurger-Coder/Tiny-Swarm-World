# Agent Team Instructions

This directory contains reusable role, orchestration and repository-skill material for current-project development-team agent model.

The repository root `AGENTS.md` remains the authoritative source for engineering rules, deployment safety, architecture boundaries, documentation language and stop conditions. `QUALITY.md` remains the authoritative source for local verification commands. If any file under `.agents/` conflicts with those root documents, the root document wins and the conflict must be reported before continuing.

## Operating Model

- Work in small, reviewable slices with explicit scope and verification.
- Preserve the Python hexagonal architecture: adapters and infrastructure depend inward on application and domain, never the reverse.
- Treat Java/Maven/Spring Boot project structure as retired unless an explicit
  future task changes Tiny Swarm World product scope.
- Preserve service boundaries for Docker Swarm stack work: automation, configuration, compose assets, and service-specific bootstrap material must stay in their documented areas.
- Keep command, VM, network, deployment, and Nexus facts explicit; do not turn unknown runtime state into confirmed state.
- Reuse shared Codex skills instead of duplicating role-specific knowledge.
- Extend existing agent material only when the requested task requires it.
- Do not overwrite or rewrite existing repository-specific `SKILL.md` workflows unless the task explicitly targets them.

## Directory Map

- `orchestrator/` describes slice coordination, routing and conflict handling.
- `roles/` defines role responsibilities and required reference skills. Existing roles may be flat Markdown files; reusable governance roles may be directories with a `SKILL.md`.
- `skills/<skill-name>/SKILL.md` contains repo-scoped Codex skills discovered by Codex.
- `../.codex/AGENTS.md` is the Codex-team entrypoint for the durable subagent hierarchy.
- `../.codex/workflow/` contains Codex-team workflow execution rules.
- `../.codex/subagents/` contains durable subagent role descriptions that point back to these authoritative role files.
- `../.codex/skills/` contains reusable Codex-team skill entrypoints that may load project-specific repository skills under `.agents/skills`.
- `../.codex/agents/` contains project-scoped custom subagent TOML files.

## Codex Compatibility

- A discoverable skill must be a directory under `.agents/skills/` with a `SKILL.md` file.
- Every `SKILL.md` must include YAML frontmatter with `name` and `description`.
- Reusable governance role directories under `.agents/roles/` also use `SKILL.md` with YAML frontmatter.
- Codex-team skill entrypoints under `.codex/skills/` must use YAML frontmatter with `name` and `description` and must avoid redefining rules already owned by root `AGENTS.md`, `QUALITY.md` or `.agents/skills`.
- Custom subagents live under `.codex/agents/` as standalone TOML files with `name`, `description` and `developer_instructions`.

## Verification

For documentation-only changes, run the minimum meaningful repository verification first. For broader changes or before commit readiness, run the full local quality gate from `QUALITY.md`.
