# Issue #192 — S192-01 Distribution Decision

- Workflow: `issue-192-20260809` / `issue-192-v1.0.0`
- Slice: `S192-01` — Wrapper/API responsibility inventory
- Execution branch: `feature/separate-lxc-service-wrappers-solid`
- Profile: `FULL_PATH`
- Chosen execution mode: sequential
- Real subagents used: `no`; no callable project-subagent tool is exposed.
- Fallback role-based review: `yes`; requirement, architecture, Python, tester,
  security and orchestration perspectives are recorded in the main thread.
- Parallelization: rejected because URL precedence, manager-IP resolution,
  sessions and compatibility facades form one locked contract.
- Stop conditions checked: URL precedence is explicit; no unknown consumer,
  credential-bearing evidence or duplicate wrapper was found.

## Consolidation plan

Treat #238's LXC service modules and composition imports as the implementation
baseline. Verify residual contracts before changing code: explicit Portainer
api_url wins over manager-IP resolution, local URLs are used otherwise,
sessions are retained, cookies are cleared by the admin flow, and legacy
facade imports remain compatibility-only.
