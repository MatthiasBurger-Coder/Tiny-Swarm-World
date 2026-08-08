# Slice 01 Distribution Decision

- Workflow: `issue-232-20260808`
- Slice: `01`
- Title: Domain image-contract and inventory invariants
- Affected areas: backend/domain, tests, architecture, security/evidence
- Execution mode: `sequential`
- Selected streams: backend, tests, architecture, security
- Real subagents used: `no`; no callable subagent interface is available in
  this execution context.
- Fallback role-based review: `yes`; Senior System Architect, Senior Python
  Automation Developer and Senior Tester review in the main execution thread.
- Git worktrees used: `no`; the checked workflow explicitly rejects parallel
  execution because domain contract and test locks overlap.
- Expected touched files/directories: `src/tiny_swarm_world/domain/artifacts/**`,
  `tests/domain/artifacts/**`, and directly required regression tests.
- Conflict risks: changing the contract model can affect artifact services,
  image publication tests and later Compose alignment; no unrelated files may
  be changed in this slice.
- Quality gates: `python3 tools/quality_gate.py test`,
  `python3 tools/quality_gate.py typecheck`, then
  `python3 tools/quality_gate.py quality`.
- Consolidation plan: review domain-only changes, run focused tests, record
  architecture and evidence findings, then create the slice checkpoint commit
  and push only the workflow branch.
- Parallelization decision: rejected because `domain artifact tests`,
  `image reference semantics`, `artifact target identity` and the domain
  isolation lock are shared with the same slice and later consumers.

## Role Review Fallback

### Senior System Architect

The change must remain parser- and adapter-independent. The domain may model
image requirements, contracts and safe validation issues, but must not inspect
Compose YAML, filesystem paths, Docker, HTTP or environment variables.

### Senior Python Automation Developer

Preserve the existing `ContainerImageContract` construction API for current
application consumers while adding explicit validation for the preflight. Keep
image-reference parsing deterministic and support the repository's existing
versioned-tag strategy without introducing implicit `latest`.

### Senior Tester

Add deterministic unit coverage for versioned tags, digest references,
implicit-`latest` rejection, duplicate identities, missing/extra contracts and
source/context mismatches. Do not use Docker or live registry calls.
