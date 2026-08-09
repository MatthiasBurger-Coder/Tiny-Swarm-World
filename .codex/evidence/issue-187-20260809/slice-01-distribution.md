# Issue #187 — S187-01 Distribution Decision

- Workflow: `issue-187-20260809` / `issue-187-v1.0.0`
- Slice: `S187-01` — Service/fingerprint behavior inventory
- Execution branch: `feature/preflight-service-probe-registry-solid`
- Profile: `FULL_PATH`
- Chosen execution mode: sequential
- Real subagents used: `no`; no callable project-subagent tool is exposed.
- Fallback role-based review: `yes`; requirement, architecture, Python, tester,
  security and orchestration perspectives are recorded in the main thread.
- Parallelization: rejected because the inventory freezes one shared ordered
  service/fingerprint contract before extraction.
- Expected touched paths: `.tiny-swarm/evidence/solid-host-preflight-probe/**`,
  `.tiny-swarm-world/evidence/solid-host-preflight-probe/**`,
  `.codex/evidence/issue-187-20260809/**`.
- Stop conditions checked: no ambiguous service fingerprint or missing current
  test case found.

## Consolidation plan

Freeze the ordered service matrix, exact HTTP/TCP semantics, fallback behavior
and responsibility boundary. S187-02 may extract only the service matching
strategies and registry; host detection, executable checks, secret scanning,
Git scanning and evidence policy remain outside the slice.
