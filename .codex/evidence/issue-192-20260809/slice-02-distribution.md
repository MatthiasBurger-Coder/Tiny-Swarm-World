# Issue #192 — S192-02 Distribution Decision

- Workflow: `issue-192-20260809` / `issue-192-v1.0.0`
- Slice: `S192-02` — Wrapper/resolver boundary and compatibility migration
- Execution branch: `feature/separate-lxc-service-wrappers-solid`
- Profile: `FULL_PATH`
- Chosen execution mode: sequential
- Real subagents used: `no`; no callable project-subagent tool is exposed.
- Fallback role-based review: `yes`; architecture, Python, testing and
  security reviews are performed in the main execution thread.
- Parallelization: rejected because URL precedence, sessions, compatibility
  facades and composition ownership share one contract lock.

## Boundary decision

The residual #238 implementation is behaviorally complete; close the gap with
contract and architecture tests rather than moving already-separated HTTP
policy. Tests must prove explicit/local URL precedence, session retention,
credential rejection, old facade compatibility and absence of HTTP calls in
the Swarm facade.

## Verification plan

- Add deterministic service-wrapper contract tests.
- Add an architecture guard for the Swarm facade HTTP boundary.
- Run focused tests and the required local quality gate.
