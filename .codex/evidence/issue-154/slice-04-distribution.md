# Issue #154 Slice 04 Distribution Decision

Workflow: `issue-154-20260808`
Slice: `04 — Wire setup boundaries and downstream not_run`

Decision: `SERIAL FALLBACK REVIEW`

No callable subagent tools are exposed. The required Senior Python Automation
Developer, Senior System Architect, Senior Tester and Senior Requirement
Engineer reviews are performed explicitly in the main execution thread.
Frontend, live runtime and infrastructure-operation streams are not applicable.

The slice is serial because the setup phase tuple, installation-plan ordering,
composition bundle and downstream status assertions share the cluster verify
success boundary. The generic `SetupWorkflow` stop path is already the sole
fail-closed mechanism and must be reused.

Expected write scope:

- `src/tiny_swarm_world/infrastructure/composition.py`
- `src/tiny_swarm_world/application/services/setup/workflow.py` only if a
  contract-preserving defect is found;
- listed setup and composition tests.

Forbidden scope: new stop mechanisms, plan/YAML changes, platform runtime
logic, host preparation, artifacts, deployment, network topology, local
storage and live provider operations.

Verification plan: fake-based setup ordering and failure-boundary tests, then
`test`, `typecheck`, `arch-tests` and the full `quality` gate. Consolidation
must prove Docker follows reconcile, Swarm follows Docker, cluster verify
precedes expose, and every listed downstream phase is `not_run` after cluster
failure.
