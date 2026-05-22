# Codex Team Instructions

This directory defines a Codex development-team structure for Tiny Swarm World.

The repository root `AGENTS.md`, when present, is the authoritative source for project-specific engineering rules, safety rules, architecture boundaries, stop conditions, documentation language, and final reporting. `QUALITY.md`, when present, is the authoritative source for verification commands. If this file conflicts with a root project document, the root document wins and the conflict must be reported before continuing.

## Directory Map

- `workflow/workflow-execution-rules.md` defines the reusable team execution workflow.
- `subagents/` describes the durable role hierarchy and responsibilities.
- `skills/<skill-name>/SKILL.md` contains reusable Codex-team skill entrypoints.
- `agents/` may contain project-scoped custom subagent TOML definitions used by Codex runtimes that support callable subagents.
- `.agents/`, when present, may contain project-specific role and skill extensions.

## Project Model

Tiny Swarm World is a Python automation repository for Linux/WSL-local
infrastructure. Root `AGENTS.md` and `QUALITY.md` override reusable team
defaults.

Reusable `.codex` files should:

- avoid hard-coded package names when root documents already define them,
- avoid project-specific build tasks unless they are discovered from repository files,
- avoid hard dependencies on `.agents/skills/<project-name>-*`,
- prefer root `AGENTS.md`, `QUALITY.md`, and discovered local role or skill files for project-specific rules.

Project-specific rules belong in root `AGENTS.md`, `QUALITY.md`, `.agents/`, or project documentation.

## Portable Copy Set

To reuse this team model in another project, copy these paths:

- `.codex/AGENTS.md`
- `.codex/workflow/`
- `.codex/subagents/`
- `.codex/skills/`

Do not copy `.codex/agents/` as part of the portable template unless those TOML files have been generalized for the target project. That directory is allowed to contain runtime-specific or project-specific callable-agent definitions.

## Mandatory Subagent Workflow

All non-trivial work must be routed through the subagent workflow before implementation.

The Agent Workflow Orchestrator coordinates:

- workflow discovery and reading,
- slice detection,
- subagent or role assignment,
- architecture-rule enforcement,
- quality-gate enforcement,
- stop-rule enforcement,
- result aggregation.

Direct implementation without subagent or role review is forbidden for non-trivial work.

Callable subagents should be used when the active request or workflow command authorizes delegated execution. If callable subagents are unavailable, apply the matching file under `subagents/` or a discovered project role file as an explicit local review checklist and report that no callable subagent was used.

## Mandatory Command

Root `AGENTS.md` remains authoritative for project-specific exact commands. In this repository, exact command routing includes:

- `skills update` -> project `skills-agents` strand
- `workflow create` -> project workflow creation strand
- `workflow execute` -> project workflow execution strand

When the user writes exactly:

```text
workflow execute
```

Codex must:

1. Locate the active workflow.
2. Read all slices.
3. Assign subagents or role reviews.
4. Execute slice by slice.
5. Run tests and quality checks after each slice.
6. Review `git diff` and `git diff --check`.
7. Run the project-defined slice checkpoint push after each successful slice when the active workflow requires it.
8. Continue only when the slice is clean or a documented blocker is explicitly allowed by the workflow.

If a project-specific workflow-executor skill exists, use it after reading this reusable workflow.

## Workflow Executor Resolution

`.codex/skills/workflow-executor/SKILL.md` is the reusable base protocol.
When a project-specific executor exists under `.agents/skills/workflow-executor/SKILL.md`,
the project-specific file is the active executor for that repository. Read the
`.codex` base for portable context and conflict detection only.

## Team Hierarchy

```text
Agent Workflow Orchestrator
|
+-- Workflow Executor Skill
|
+-- Senior System Architect
    |
    +-- Senior Python Automation Developer
    +-- Senior React Frontend Developer
    +-- Senior UX Designer
    +-- Senior DevOps Engineer
    +-- Senior Tester
    +-- Documentation Engineer
    +-- Microservice Senior Expert
```

## Default Service Guardrails

For service or stack-split work, apply these guardrails unless the root project
rules define a stricter or incompatible policy:

- No shared implementation modules between independently deployable services.
- No shared domain models between services.
- No shared event implementation classes between services.
- No direct class dependencies between services.
- Communication must use explicit external contracts such as REST/OpenAPI, gRPC/protobuf, or message contracts.
- Every service must be independently runnable, testable, containerized when containers are in scope, and deployable through the project's documented deployment targets.

These guardrails do not authorize speculative service extraction. Service
extraction requires a dedicated verified slice or explicit user request.

For this repository, Python automation under `src/tiny_swarm_world` is the
primary architecture. Java deployment-example files are handled only when a task
explicitly targets them.
