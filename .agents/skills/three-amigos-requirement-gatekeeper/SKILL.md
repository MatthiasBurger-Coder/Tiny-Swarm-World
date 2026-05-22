---
name: three-amigos-requirement-gatekeeper
description: "Use before workflow authoring or execution to validate incoming requirements with a Three Amigos gate: requirement completeness, architecture fit, quality/testability, dependency cycles, deadlock risks, slice boundaries, required skills, subagent availability, and READY_FOR_WORKFLOW versus REQUIRES_REFINEMENT decisions."
---

# Skill: Three Amigos Requirement Gatekeeper

## Mission

Validate and refine incoming requirements before implementation work starts.

Prevent:

- architecture drift
- undefined ownership
- unclear acceptance criteria
- incomplete workflows
- invalid slice dependencies
- deadlocks caused by unstable contracts, cyclic workflows or shared file ownership

## Authority

The gatekeeper may:

- reject requirements
- stop workflows
- request refinements
- split oversized slices
- enforce architecture, quality and evidence-integrity rules
- require specialist role or subagent review before workflow authoring

## Boundaries

- Do not implement production code.
- Do not generate workflow files directly; route ready requirements to `workflow-authoring`.
- Do not execute workflows; route execution to `workflow-executor`.
- Do not override root `AGENTS.md`, `QUALITY.md`, ADRs or verified repository behavior.
- Do not treat planned behavior, LLM output or inferred relationships as verified evidence.

## Required Inputs

Inspect the relevant subset of:

- user requirement and acceptance criteria
- root `AGENTS.md`
- root `QUALITY.md`
- `documentation/epics`
- `documentation/arc42`
- `documentation/adr`
- existing `documentation/workflow`
- `.agents/orchestrator`
- `.agents/roles`
- `.agents/skills`
- `.codex/agents`
- affected source, tests, schemas, fixtures, examples, API contracts or build files when named by the requirement

Use EPIC source precedence:

1. the EPIC explicitly named by the user
2. the EPIC referenced by the active workflow
3. the EPIC that directly matches the requested domain area under `documentation/epics`
4. no EPIC, reported as an open traceability gap

When an active workflow exists and the user asks for a new requirement or workflow, first determine whether the request extends, replaces or conflicts with the active workflow. Return `REQUIRES_REFINEMENT` if that relationship is unclear.

## Reference Files

Load these files only when needed:

- `workflow.md` for the full gate workflow.
- `decision-rules.md` for stop, refinement, architecture, dependency and parallelization rules.
- `anti-patterns.md` when reviewing risky requirement or slice shapes.
- `templates/requirement-template.md` when normalizing a requirement.
- `templates/slice-template.md` when drafting slice boundaries.
- `templates/acceptance-template.md` when acceptance criteria are missing or incomplete.
- `examples/forensic-analytics-example.md` for a compact example output.

## Five-Role Three Amigos Review

Run the review through five mandatory roles:

- Senior Requirement Engineer: target, scope, non-goals, acceptance criteria, assumptions, open questions and confidence level.
- Senior System Architect: architecture boundaries, arc42, service boundaries, automation-vs-runtime boundary, governance risks and planned-vs-implemented status.
- Senior Python Automation Developer: Python automation impact, ports, adapters, domain, unittest testability, dependency wiring impact and infrastructure-automation consequences.
- Senior React Frontend Developer: frontend impact, UX flows, React components, state, API adapters and build or test consequences.
- Senior Tester: testability, regression, quality gates, acceptance criteria and slice acceptance.

Classic labels such as Requirement Analyst, Architecture Validator and Quality Validator may be used as additional perspectives. They do not replace the five mandatory roles.

Add a Dependency / Deadlock Validator pass when the request contains multiple slices, services, subagents, shared files, shared APIs, orchestration steps, queues, workers or rollout dependencies.

Always ask:

```text
Does the implementation still match the EPIC?
```

For microservice migration requests, require a Three Amigos Decision Record with:

- scope
- non-scope
- acceptance criteria
- service boundary
- contract impact
- data ownership impact
- test impact
- risk level
- rollback or strangler strategy
- stop conditions

Ask explicitly:

- What service problem is being solved?
- What inputs and outputs cross the service boundary?
- What data is owned by the target service?
- Which dependencies are allowed?
- Which communication mechanisms are allowed?
- Which tests prove the slice is safe?
- Which changes are forbidden in this slice?

Classify the requirement as one or more of:

- functional requirement
- non-functional requirement
- architecture constraint
- resilience requirement
- scalability requirement
- UX requirement
- observability requirement
- security or data-protection requirement
- quality-gate requirement
- assumption
- open question

## Related Skills

Use related skills instead of duplicating their full workflows:

- `requirement-engineering` for requirement classification, EPIC drift and traceability.
- `engineering-governance` for cross-document governance synchronization.
- `arc42-architecture-governance` for architecture documentation impact.
- `workflow-slice` for implementation slice planning after the gate.
- `workflow-authoring` only after a `READY_FOR_WORKFLOW` decision.
- `quality-gate-governance` for verified quality commands.
- `documentation-sync` for documentation alignment.
- `agent-swarm-coordination-specialist` when the user explicitly authorizes subagent or parallel work.

## Decision Contract

Return exactly one decision:

```text
READY_FOR_WORKFLOW
```

or

```text
PROCEED_WITH_ACCEPTED_ASSUMPTIONS
```

or

```text
REQUIRES_REFINEMENT
```

Use `READY_FOR_WORKFLOW` only when confidence is at least 90 percent and:

- the business goal and technical goal are explicit
- scope and non-goals are clear
- affected services, APIs, storage and deployment impact are identified or explicitly not affected
- microservice service boundary, contract impact, data ownership impact, test impact, risk level and stop conditions are explicit when service-split work is requested
- acceptance criteria are testable
- required skills and role or subagent ownership are known
- slice dependencies are acyclic
- parallelization groups have disjoint write scopes and stable contracts
- quality commands are verified from `QUALITY.md` or repository build files
- no blocking questions remain
- unresolved uncertainty is absent

Use `PROCEED_WITH_ACCEPTED_ASSUMPTIONS` only when confidence is from 70 to 89 percent and every remaining assumption is non-blocking, documented and accepted.

Use `REQUIRES_REFINEMENT` when confidence is below 70 percent, any blocking question remains, or any requirement, ownership, API, quality command, architecture impact, evidence semantic, dependency edge or acceptance criterion would require guessing.

Draft slices may be included with `REQUIRES_REFINEMENT` only when they are clearly labeled provisional and used to explain dependency or ownership questions. Do not present provisional slices as executable workflow slices.

Treat a user-accepted blocker-free assumption as ready only when the gate report records the assumption, the user acceptance source and the affected slices or decisions.

## STOP Rules

Stop with `REQUIRES_REFINEMENT` when:

- business goal is missing;
- non-goals are missing;
- affected services, APIs, storage, data ownership or deployment impact are unclear;
- microservice service boundary, contract impact, test impact, risk level or forbidden changes are unclear;
- acceptance criteria are missing or not testable;
- API contracts or message semantics are unclear;
- architecture boundaries, testability, data ownership, service boundaries, APIs, contracts, runtime behavior or scope are unclear;
- rollback strategy is missing when the change affects deployable behavior or persisted state;
- required skills, roles or callable subagents cannot be verified;
- slice dependencies are cyclic or file ownership overlaps without handoff rules;
- quality commands cannot be verified from `QUALITY.md` or build files;
- continuing would require guessing architecture, runtime facts, evidence semantics, data ownership or implementation details.

## Expected Output

Produce a concise gate report containing:

- normalized requirement summary
- Three Amigos findings
- architecture and evidence-integrity validation
- quality and verification validation
- dependency graph or dependency summary
- required skills and subagents or role reviews
- draft slice boundaries and parallelization groups, if ready
- open questions and blockers
- final decision
