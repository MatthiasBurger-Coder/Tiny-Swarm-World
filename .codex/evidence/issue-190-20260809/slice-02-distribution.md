# Issue #190 — S190-02 Distribution Decision

- Workflow: `issue-190-20260809` / `issue-190-v1.0.0`
- Slice: `S190-02` — Complete residual strategies and generic dispatch
- Execution branch: `feature/stack-prerequisite-strategies-solid`
- Profile: `FULL_PATH`
- Chosen execution mode: sequential
- Real subagents used: `no`; no callable project-subagent tool is exposed.
- Fallback role-based review: `yes`; architecture, Python, testing and
  security reviews are performed in the main execution thread.
- Parallelization: rejected because prerequisite and asset registries share
  ordering and deployment contracts.

## Boundary decision

Keep the existing prerequisite handlers and make their matching explicit;
introduce an ordered asset-transfer strategy registry for Traefik,
Service Access and Swagger. Generic Swarm runtime orchestration remains
stack-agnostic and all shell/filesystem behavior stays in infrastructure.

## Verification plan

- Preserve command text, transfer paths and order through existing tests.
- Add registry dispatch and generic-runtime architecture assertions.
- Run focused stack tests and the full local quality gate.
