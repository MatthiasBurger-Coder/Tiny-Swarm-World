# Workflow

## Phase 1 - Determine ADR Need

Require ADR review when a slice changes:

- service boundaries
- communication protocol
- persistence ownership
- graph, vector, event or runtime trace storage policy
- quality gate policy
- security architecture
- deployment topology
- workflow governance
- compatibility or breaking-change policy

## Phase 2 - Inspect Existing Decisions

Read `documentation/adr/README.md` and relevant ADRs. Verify next available number from existing files.

Do not infer supersession. If an existing ADR appears inconsistent, report the conflict and route to Senior System Architect.

## Phase 3 - Draft Or Backlog

Use `templates/adr-template.md`.

For future decisions that are not ready, create backlog entries in workflow documentation rather than accepted ADR files.

## Phase 4 - Review

ADR review requires:

- decision owner
- context
- decision
- rationale
- consequences
- status
- related workflow or architecture documents

## Phase 5 - Synchronize

Update `documentation/adr/README.md` only after an ADR file is created and reviewed.

Route active architecture consequences to arc42 governance when applicable.
