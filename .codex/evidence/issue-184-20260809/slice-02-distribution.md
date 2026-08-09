# Issue #184 — S184-02 Distribution Decision

- Workflow: `issue-184-20260809` / `issue-184-v1.0.0`
- Slice: `S184-02` — Extract modules and preserve compatibility
- Execution branch: `feature/split-lxc-node-provider-solid`
- Profile: `FULL_PATH`
- Chosen execution mode: `sequential`
- Real subagents used: `no`; no callable project-subagent tool is exposed.
- Fallback role-based review: `yes`; role reviews are performed in the main thread and Codex remains final integration owner.
- Git worktrees used: `no`; overlapping LXC contracts and mandatory serial order make stream work unsafe here.
- Expected touched files/directories: `src/tiny_swarm_world/infrastructure/adapters/clients/lxc/{command,node,profile,resource}/**`, `lxc_node_provider.py`, focused LXC tests and architecture tests.
- Conflict risks: same facade and compatibility imports across backend, tests and architecture streams; #191 must not redesign evidence in this slice.
- Quality gates: targeted lint, typecheck, focused tests, arch-lint and arch-tests; required `python3 tools/quality_gate.py quality`.
- Consolidation plan: integrate one serial refactor, verify all legacy imports and public outcomes, then record the after-inventory in S184-03.

## Stream assessment

| Stream | Owner/reviewer | Decision | Reason |
|---|---|---|---|
| Backend/Python | Senior Python Automation Developer | active | Extract command, node model, profile policy and resource resolution mechanics. |
| Architecture | Senior System Architect | active review | Keep infrastructure-only dependencies, orchestration ownership and #189 resolver reuse. |
| Tests/quality | Senior Tester | active review | Preserve lifecycle outcomes, evidence keys, timeout/failure behavior and old import seams. |
| Security | Senior Security Sandbox Engineer | conditional review | Retain bounded subprocesses, safe diagnostics and no live mutation in tests. |
| Documentation | Senior Documentation Engineer | deferred to S184-03 | Arc42 receives only verified responsibility status after regression evidence. |
| Frontend/runtime | N/A | not applicable | No browser UI or live infrastructure scope is declared. |
| Orchestration | Senior Execution Orchestrator | active | File, contract and architecture locks require serial execution. |

## Parallelization decision

Parallel execution is rejected. Backend, tests and architecture streams overlap
the same facade, compatibility surface and package locks; independent worktree
streams would create merge-order and seam conflicts. The implementation is
therefore executed as one serial slice in the verified workflow branch.
