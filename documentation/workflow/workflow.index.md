# Indexed Workflow Set: SOLID Refactor Chain

Workflow set ID: `solid-refactor-chain-20260809`

Authoring branch: `feature/workflow-solid-refactor-chain-20260809`

Status: `EXECUTING_LOCAL` — Issues #189, #184 and #191 complete; #187 is next

Execution order requested by the user:

```text
#189 -> #184 -> #191 -> #187 -> #190 -> #192 -> #186
```

This is an indexed multi-issue workflow set. Issue #191 is currently promoted
to the active `documentation/workflow/workflow.md` on its execution branch;
#189, #184 and #191 are locally complete, while #187 through #186 remain
indexed and require serialized promotion after each predecessor.

## Three-Amigos decision

The Four-Role review was completed in the authoring thread with explicit
fallback review because callable project subagents were not available:

- Senior Requirement Engineer: all issue bodies were normalized into stable
  requirement matrices; the user-provided order is treated as the required
  dependency order.
- Senior System Architect: the work remains inside the existing Python
  hexagonal infrastructure boundary; no microservice or browser-React scope
  is introduced.
- Senior Python Automation Developer: current source and tests were inspected;
  #238 already contains partial service-wrapper and stack-prerequisite
  extraction that must be revalidated rather than duplicated.
- Senior Tester: deterministic unit, architecture and full local quality gates
  are defined from `QUALITY.md`; live, browser and external gates remain
  opt-in and state-classified.
- Dependency/deadlock pass: the chain is acyclic and intentionally serialized;
  overlapping LXC command, node, evidence, swarm, service and composition
  locks are not parallelizable.

Decision: `PROCEED_WITH_ACCEPTED_ASSUMPTIONS` at 85% confidence.

Accepted non-blocking assumption: the issue bodies are the authoritative
requirement source because no matching EPIC exists under `documentation/epics`.
This is recorded as an open traceability gap and must be reconciled before a
completion claim if an EPIC or ADR is required by a discovered contract
change. No implementation is authorized by this authoring step.

## Chain index

| Order | Issue | Workflow | Execution branch | Status | Depends on | Blockers |
|---:|---:|---|---|---|---|---|
| 01 | #189 | [issue-189/workflow.md](issues/issue-189/workflow.md) | `feature/centralize-lxc-shared-utilities-solid` | COMPLETED_LOCAL_AUDITED | none | matching EPIC traceability gap recorded; audit PASS |
| 02 | #184 | [issue-184/workflow.md](issues/issue-184/workflow.md) | `feature/split-lxc-node-provider-solid` | COMPLETED_LOCAL_AUDITED | #189 | audit PASS; #191 next |
| 03 | #191 | [issue-191/workflow.md](issues/issue-191/workflow.md) | `feature/typed-verification-evidence-solid` | COMPLETED_LOCAL_AUDITED | #184 | audit PASS; #187 next |
| 04 | #187 | [issue-187/workflow.md](issues/issue-187/workflow.md) | `feature/preflight-service-probe-registry-solid` | READY_FOR_EXECUTION_WITH_ACCEPTED_ASSUMPTIONS | #191 | ambiguous fingerprint behavior |
| 05 | #190 | [issue-190/workflow.md](issues/issue-190/workflow.md) | `feature/stack-prerequisite-strategies-solid` | READY_FOR_EXECUTION_WITH_ACCEPTED_ASSUMPTIONS | #187 | current partial registry requires residual inventory |
| 06 | #192 | [issue-192/workflow.md](issues/issue-192/workflow.md) | `feature/separate-lxc-service-wrappers-solid` | READY_FOR_EXECUTION_WITH_ACCEPTED_ASSUMPTIONS | #190 | URL/API precedence ambiguity |
| 07 | #186 | [issue-186/workflow.md](issues/issue-186/workflow.md) | `feature/replace-global-di-service-locator-solid` | READY_FOR_EXECUTION_WITH_ACCEPTED_ASSUMPTIONS | #192 | global runtime resolution, if discovered |

No issues were excluded. Every issue has an issue-local workflow and context
pack. #189, #184 and #191 are locally audited complete; the remaining four
workflows require promotion after the indexed predecessor chain advances.

## Dependency graph

```text
S189-01 -> S189-02 -> S189-03
                         |
                         v
S184-01 -> S184-02 -> S184-03
                         |
                         v
S191-01 -> S191-02 -> S191-03
                         |
                         v
S187-01 -> S187-02 -> S187-03
                         |
                         v
S190-01 -> S190-02 -> S190-03
                         |
                         v
S192-01 -> S192-02 -> S192-03
                         |
                         v
S186-01 -> S186-02 -> S186-03
```

The vertical edges are cross-workflow dependencies. They must be completed in
the indexed order. No parallel execution group is declared for the chain.

## Publication and promotion

- Authoring artifacts are committed and pushed only from
  `feature/workflow-solid-refactor-chain-20260809`.
- This is guarded workflow-create publication, not `push auto`.
- No pull request merge, branch deletion, force-push or cleanup is part of
  workflow creation.
- Issues #189, #184 and #191 were promoted to
  `documentation/workflow/workflow.md`, executed and independently audited
  locally; their context packs and issue evidence record the completion states.
- The promotion preserves the chain dependency and declared implementation
  branch; #187 is the next explicit promotion target.

## Excluded from this authoring set

None. Issue #188 is not part of this chain; its prior active-root status is
preserved in the promotion evidence and replaced only by the explicitly
requested first-chain promotion.
