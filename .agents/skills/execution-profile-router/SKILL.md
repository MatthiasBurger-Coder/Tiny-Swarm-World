---
name: execution-profile-router
description: Classifies workflow create and workflow execute requests as FAST_PATH, NORMAL_PATH, or FULL_PATH before specialist role routing, while preserving mandatory AGENTS.md, QUALITY.md, ADR, STOP-rule, and quality-gate authority.
---

# Skill: Execution Profile Router

## Mission

Classify every `workflow create` and `workflow execute` request before
specialist role assignment so low-risk governance work does not automatically
run the full review depth while high-risk work still receives full governance.

This skill chooses review depth. It does not approve implementation, bypass
required roles, weaken quality gates, or override root `AGENTS.md`,
`QUALITY.md`, ADRs, active workflows, routing rules, or STOP conditions.

## Profiles

### FAST_PATH

Use for changes that are documentation-only and cannot affect product build,
runtime behavior, contracts, tests, architecture boundaries, quality rules,
branch rules, publication rules, skill ownership, or process semantics.

Examples:

- typo fixes in governance documentation;
- Mermaid or PlantUML layout-only corrections;
- README wording with no behavior or command change;
- metadata text that does not change routing, ownership, branch, quality, or
  publication behavior.

### NORMAL_PATH

Use for isolated work with a narrow verified scope and no architecture,
contract, persistence, runtime, deployment, branch, publication, quality-rule,
or cross-module impact.

Examples:

- isolated backend, frontend, test, documentation, or governance update with
  verified owner and disjoint file locks;
- skill metadata update without behavior or ownership change;
- workflow documentation update that does not change slice dependencies,
  locks, gates, or process authority.

### FULL_PATH

Use when the request changes, creates, or might affect governance authority,
architecture boundaries, contracts, persistence, runtime ingestion, deployment,
workflow structure, skill or role ownership, quality policy, branch policy, or
publication behavior.

Examples:

- workflow governance changes;
- skill, role, agent, routing, or process-strand changes;
- microservice split or service-boundary work;
- REST, gRPC, Protobuf, event contract, persistence, runtime ingestion,
  Joern, JavaParser, BTM, build logic, branch, commit, push, or quality-gate
  work;
- any request with unclear impact.

## Required Inputs

- User request.
- Active process strand.
- Root `AGENTS.md`.
- Root `QUALITY.md`.
- Active `documentation/workflow/workflow.md` when present.
- `.agents/orchestrator/routing-rules.md`.
- Changed or planned file set.
- Relevant ADR, arc42, process, skill-registry, role, and workflow documents.

## Outputs

Return:

```text
executionProfile=<FAST_PATH|NORMAL_PATH|FULL_PATH>
reason=<short evidence-based reason>
requiredFullReviews=<roles or skills>
allowedImpactChecks=<roles that may answer N/A impact only>
requiredQualityChecks=<commands or not-applicable reason from QUALITY.md/workflow>
stopConditions=<profile-specific blockers>
```

## Collaboration Rules

- Run before specialist role assignment in `workflow create` and
  `workflow execute`.
- Consult Senior Requirement Engineer when requirement scope is unclear.
- Consult Senior System Architect when architecture, branch, quality, routing,
  publication, skill, role, or process authority may change.
- Consult Senior Tester or quality-gate skills before classifying a quality
  gate as not applicable.
- Consult Skill Registry Conflict Auditor when `.agents/**`, `.codex/**`,
  `documentation/process/skills/audit/**`, legacy `documentation/agents/**` references,
  or routing rules change.

## Forbidden

- Do not mark required Four-Role Three Amigos participation as optional, and
  do not omit the conditional Console/status UI reviewer when verified terminal
  UI impact exists.
- Do not convert required full reviews into N/A impact checks when the role's
  area is affected.
- Do not mark a failed or missing required quality gate as optional.
- Do not treat cached context packs or skill registries as source-of-truth
  files.
- Do not classify a request as `FAST_PATH` when scope, file set, ownership, or
  quality impact is uncertain.
- Do not classify product source, tests, build logic, contracts, runtime,
  persistence, deployment, branch, publication, or quality-rule changes as
  `FAST_PATH`.

## STOP Rules

Stop and route to `FULL_PATH` or escalation when:

- the affected file set is unknown;
- the active process strand is unclear;
- root `AGENTS.md`, `QUALITY.md`, ADRs, active workflow, process docs, or
  routing rules conflict;
- a required role, skill, route, branch rule, quality command, or STOP rule
  cannot be verified;
- profile selection would allow implementation outside the checked workflow;
- profile selection would weaken a required quality, architecture, branch,
  publication, or documentation-governance rule.
