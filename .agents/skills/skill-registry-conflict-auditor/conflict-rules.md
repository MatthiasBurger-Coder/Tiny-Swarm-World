# Conflict Rules

## Conflict Types

### Architecture Conflict

A skill, role, workflow or prompt contradicts `AGENTS.md`, ADRs, arc42 constraints, hexagonal boundaries or verified module responsibilities.

Blocking examples:

- domain or application code depends on adapter or infrastructure rules;
- Workflow Executor is allowed to make sole architecture decisions;
- service extraction is planned without architecture ownership.

### Ownership Conflict

Two or more skills own the same decision or output with incompatible authority, or no verified owner exists.

Blocking examples:

- two skills generate the same ADR with different acceptance rules;
- a workflow assigns a slice to a skill that does not exist and no fallback role is documented.

### Quality Conflict

A skill, prompt or workflow weakens `QUALITY.md` or treats failed required gates as non-blocking.

Blocking examples:

- commit is allowed after failed tests;
- `git diff --check` is documented as replacing the required Python minimum gate.

### Security Conflict

A rule allows unsafe handling of secrets, untrusted repositories, runtime traces, credentials, containers or supply-chain risks.

Blocking examples:

- secrets may be logged;
- external repositories are processed without isolation;
- containers run with unnecessary privileges without review.

### Workflow Conflict

Workflow order, slice dependencies, handoffs or executor authority are inconsistent.

Blocking examples:

- implementation starts before requirement gate approval;
- parallel slices write the same files without ownership rules;
- cyclic handoff chains lack an orchestrator decision.

### Tooling Conflict

Tooling paths, prompts, quality commands, CI jobs or generated artifacts are referenced without verification.

Blocking examples:

- undocumented quality command is required by a workflow;
- project-specific rules are added to portable `.codex` files without a portability decision.

### Microservice Boundary Conflict

A skill or workflow permits coupling between services that violates service autonomy.

Blocking examples:

- shared Java implementation modules between services;
- shared domain model modules;
- direct class dependencies between services.

### Data Ownership Conflict

Data ownership, write authority, projection ownership or persistence boundaries are unclear or contradictory.

Blocking examples:

- multiple services write the same owned data;
- direct cross-service database access;
- shared tables used as hidden coupling.

## Required Report Fields

- conflict type
- classification: `BLOCKING` or `NON_BLOCKING`
- affected files
- expected rule
- observed rule
- owner role or skill
- required resolution
