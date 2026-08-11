# I197-S02 Distribution

Workflow: `issue-197-20260809`
Slice: `I197-S02`
Dependency: `I197-S01` / `251d8f8`

## Execution decision

- Execution mode: serial, per the user-requested issue order.
- Primary role: Senior System Architect.
- Fallback reviewers: Senior Python Automation Developer, Senior Requirement
  Engineer and Senior Tester; real subagent tools were not available in this
  session.
- Parallelization decision: not split. The port and adapter contract are a
  single boundary lock and must be reviewed together.

## Locked scope

- Add the WSL Socat exposure port under `application/ports/network`.
- Add the focused infrastructure adapter module under
  `infrastructure/adapters/network`.
- Keep process execution collaborators injectable so contract tests cannot
  start real commands.
- Do not change Composition wiring or workflow ordering in this slice.
- Do not add subprocess imports to domain or application code.

## Files and locks

- `src/tiny_swarm_world/application/ports/network/port_wsl_socat_exposure.py`
- `src/tiny_swarm_world/application/ports/network/__init__.py`
- `src/tiny_swarm_world/infrastructure/adapters/network/wsl_socat_exposure.py`
- `src/tiny_swarm_world/infrastructure/adapters/network/__init__.py`
- Contract lock: `I197-adapter-api`
- Architecture locks: `domain-independent`, `application-no-subprocess`

## Review result

The port uses only typed command text and boolean async outcomes. The adapter
contains no subprocess implementation in this slice and delegates process
operations to injected collaborators. This is the approved boundary for
S197-S03 to add the infrastructure-only default process implementation.
