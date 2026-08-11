# I197-S03 Distribution

Workflow: `issue-197-20260809`
Slice: `I197-S03`
Dependency: `I197-S02` / `b835e47`

## Execution decision

- Execution mode: serial, per the user-requested issue order.
- Primary role: Senior Python Automation Developer.
- Fallback reviewers: Senior System Architect and Senior Tester; real
  subagent tools were not available in this session.
- Parallelization decision: not split. The adapter implementation and its
  process-boundary tests share the `I197-adapter-api` contract lock.

## Locked scope

- Add the default optional-tool lookup to the infrastructure adapter.
- Move `pgrep -f` process inspection into the adapter.
- Move `sh -lc` plus detached `nohup` startup into the adapter.
- Preserve arguments, output suppression and exit-code-to-boolean semantics.
- Keep all subprocess calls in infrastructure and mock every call in tests.
- Do not rewire Composition or change workflow result semantics in this slice.

## Safety constraints

- Tests must patch `asyncio.create_subprocess_exec`; no process may be
  started by the test suite.
- No Socat, LXC, Incus, Docker or Swarm command is run live.
- The adapter remains usable with injected collaborators for deterministic
  unit tests.
