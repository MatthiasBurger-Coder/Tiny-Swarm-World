# Workflow: Issue #129 — Documentation Navigation

Workflow id: `issue-129-documentation-navigation-20260812`

Issue: [#129](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/129)

Authoring branch: `docs/workflow-public-beta-roadmap-20260812`

Planned execution branch: `docs/issue-129-documentation-navigation-20260812`

Status: `AUTHORED_INDEXED`

## Executive Summary

Create stable audience-specific documentation entry points after the governance,
security, feature, traceability and evidence documents exist. Navigation must
link canonical documents without duplicating large sections or claiming live
success. The issue's recommended #127 dependency is already closed and
represented by existing supply-chain documentation.

## Requirement Clarification Gate

- Original request: execute #129 near the end, after #125.
- Interpreted intent: create operator, developer, security, audit and
  live-validation manuals and concise root links.
- Change type: documentation structure/navigation.
- Affected process strand: audience -> canonical entry point -> verified
  operational/governance document.
- Affected architecture area: documentation only, with links to arc42, process,
  security, audit, evidence and release docs.
- Explicit requirements: create the five manuals; link required README,
  handbook, configuration, live-operation, AGENTS/QUALITY, architecture,
  workflow, evidence and installation surfaces; explain safety boundaries.
- Implicit requirements: avoid duplication/stale links; keep README concise;
  distinguish planned/missing/live evidence; preserve operator safety language.
- Assumptions: preceding workflows provide the canonical paths; #127 is closed
  and does not need a new navigation workflow.
- Non-goals: rewrite all docs, runtime changes, live commands and live-success
  claims.
- Risks: audience mixing hides safety rules; links point to stale or planned
  content; manuals imply feature completeness.
- Open/blocking questions: none for authoring; unresolved Public-Beta status
  must remain visible in the live-validation manual.
- Confidence: 94%.
- Decision: `READY_FOR_WORKFLOW`.

## Target Picture

```text
README / documentation root
       |
       +-> Operator Manual
       +-> Developer Manual
       +-> Security Manual
       +-> Audit Manual
       +-> Live Validation Manual
```

## Verified Baseline, Scope and Assessments

`documentation/manuals/` is absent. `documentation/README.adoc`, README,
arc42, user guides and process docs are existing link sources. Scope is five
manuals plus concise root links. Python/frontend are not applicable. Resilience
means safety-critical live-consent, reset and secret rules are visible in the
operator/live manuals and unverified features remain labeled.

## Ordered Slices

### Slice 01 — Audience map, requirement matrix and canonical link inventory

```yaml
slice_id: S129-01
profile: DOCUMENTATION
owner: Senior Documentation Engineer
secondary_reviewers: [Documentation Audience Architect, Senior Requirement Engineer, Senior System Architect, Senior Tester]
affected_files: [.tiny-swarm/evidence/issue-129/requirement_matrix.md, documentation/README.adoc, README.md]
affected_modules: [documentation navigation]
affected_contracts: [audience entry points, canonical link inventory]
dependencies: [S125-02]
parallel_group: SERIAL-129
file_locks: [.tiny-swarm/evidence/issue-129/requirement_matrix.md, documentation/README.adoc, README.md]
contract_locks: [documentation-audience-contract]
architecture_locks: [canonical-documentation-paths]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: verify architecture links and audience boundaries
  adr: none expected
stop_conditions: [stale link, audience conflict, safety instruction omitted, planned behavior presented as implemented]
```

Done: every issue requirement maps to an audience/manual and each link is
verified or explicitly marked planned/missing; missing is not verified.

### Slice 02 — Manuals and concise root navigation

```yaml
slice_id: S129-02
profile: DOCUMENTATION
owner: Documentation Audience Architect
secondary_reviewers: [Senior Documentation Engineer, Live Evidence Validation Expert, ISMS-light Security Governance Expert, Senior Tester]
affected_files: [documentation/manuals/operator-manual.md, documentation/manuals/developer-manual.md, documentation/manuals/security-manual.md, documentation/manuals/audit-manual.md, documentation/manuals/live-validation-manual.md, documentation/README.adoc, README.md]
affected_modules: [audience-specific manuals]
affected_contracts: [operator manual, developer manual, security manual, audit manual, live-validation manual]
dependencies: [S129-01]
parallel_group: SERIAL-129
file_locks: [documentation/manuals/, documentation/README.adoc, README.md]
contract_locks: [manual-navigation-contract]
architecture_locks: [verified-documentation-only]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: link verified architecture entry points
  adr: no new ADR expected
stop_conditions: [large duplication, stale link, must not claim live pass, secret-bearing example, README expansion beyond concise links]
```

Done: all five manuals provide clear audience entry points, links are valid or
status-labeled, safety boundaries are preserved and root navigation stays short.

## Dependency Graph

`S125-02 -> S129-01 -> S129-02`

The closed #127 supply-chain workflow is a verified prerequisite reference, not
a new execution edge.

## Parallel Execution

No implementation parallelism because root navigation and canonical links are
shared. Isolated worktree required; no live validation. Read-only link checks
may parallelize after S129-01. Merge in order.

## Automatic Work Distribution Policy

Use standard distribution/consolidation evidence. Documentation, security,
audit, live-evidence and quality reviewers may advise in parallel after the map,
but shared navigation and safety language remain serialized. No browser React
stream is applicable.

## Git Worktree Execution Rule

Use isolated worktree `docs/issue-129-documentation-navigation-20260812` and
verify all predecessor canonical paths before writing.

## Issue Completion Discipline

- Requirement matrix path: `.tiny-swarm/evidence/issue-129/requirement_matrix.md`.
- Required evidence path: `.tiny-swarm/evidence/issue-129/`.
- Required evidence files: matrix, implementation summary, changed files,
  test results, remaining risks and acceptance checklist.
- Requirement Lead review: S129-01 and final.
- System Architect Reviewer review: S129-01/S129-02 and final.
- Test / Evidence Reviewer review: S129-02 and final.
- Issue Completion Auditor review: required before `DONE`.
- DONE blocking rule: open/stale/unverified navigation requirements force
  `INCOMPLETE`, `BLOCKED` or `FAILED`.

## Quality, Documentation and Handoff

Run link/path checks and `git diff --check`; no Python gate is required unless
executable tooling changes. Handoff to the Public-Beta gate includes the live
manual's explicit `PLANNED/BLOCKED` status and run prerequisites. Handoff to
#120 includes a stable documentation index for the final audit.

Definition of Done: five manuals and root links are concise, audience-specific,
verified and safety-honest; the auditor returns `PASS`.

Arc42 Check Status: architecture and operational link targets reviewed; no
runtime change expected.

## Scope

Only the five audience manuals, concise root links, verified canonical paths and
issue evidence are in scope.

## Target Outcome

Operators, developers, security reviewers, auditors and live validators each
have an unambiguous, safety-aware entry point.

## Architecture Constraints

Navigation must reflect verified behavior and existing architecture; it cannot
hide consent, secret, reset, evidence or non-pass rules.

## Python Automation Assessment

Not applicable for documentation navigation; any executable link checker is a
separate approved change.

## Frontend Assessment

Not applicable; no React/browser product surface is created.

## Test Strategy

Run canonical link/path checks, review audience boundaries and execute
`git diff --check`.

## Resilience Requirements

Safety-critical operator and live-validation instructions remain visible, and
planned/missing/live statuses are not flattened into success.

## Role and Ownership Map

Documentation Audience Architect owns audience structure; Documentation
Engineer owns links; Security/Live Evidence experts review safety language;
Tester checks references; Auditor decides completion.

## Commit and Push Plan

One issue-scoped navigation commit after all predecessor paths are verified; no
large duplication, runtime change or live claim.

## Handoff to workflow execute

Promote after #125 and predecessor evidence are stable; provide #120 with the
final canonical navigation for its reassessment.

## Arc42 Check Status

Architecture and operational link targets were reviewed; no runtime change is
expected.
