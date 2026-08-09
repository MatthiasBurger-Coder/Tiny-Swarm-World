# Issue #187 — S187-02 Distribution Decision

- Workflow: `issue-187-20260809` / `issue-187-v1.0.0`
- Slice: `S187-02` — Registry and probe extraction
- Execution branch: `feature/preflight-service-probe-registry-solid`
- Profile: `FULL_PATH`
- Chosen execution mode: sequential
- Real subagents used: `no`; no callable project-subagent tool is exposed.
- Fallback role-based review: `yes`; architecture, Python, testing and
  security reviews are recorded in the main thread.
- Parallelization: rejected because registry order, public delegation and
  network probe callbacks form one compatibility-locked unit.

## Boundary decision

Create an ordered infrastructure registry with typed HTTP, callback and TCP
probe strategies. The registry owns service-pattern dispatch only. Existing
low-level HTTP/TLS/TCP helpers and host/preflight responsibilities remain in
their current owner. Tests continue to patch deterministic module-level I/O
boundaries and do not require a live service.

## Verification plan

- Add registry order, specific-before-generic and unsupported-service tests.
- Add an architecture guard proving the public method delegates rather than
  retaining the conditional chain.
- Run focused preflight tests and the full local quality gate.
