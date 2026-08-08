# Issue #154 Slice 03 Distribution Decision

Workflow: `issue-154-20260808`
Slice: `03 — Harden structured managed-cluster verification`

Decision: `SERIAL FALLBACK REVIEW`

No callable subagent tools are exposed. The required Senior Python Automation
Developer, Senior System Architect, Senior Tester and Senior DevOps Engineer
reviews are performed explicitly in the main execution thread. The work is
backend/runtime/contract/test focused; frontend and console streams are not
applicable.

The slice is serial because the Docker/Swarm DTOs, application port, service,
managed LXC adapter and provider-selected runtime share contract locks for
expected-node completeness, Ready/Active state, manager/leader state and valid
join credentials.

Expected write scope:

- listed domain node-provider DTOs;
- the container Docker/Swarm application ports and platform services;
- the managed LXC Docker/Swarm adapters and provider-selected runtime bridge
  when required to implement the port contract;
- listed focused domain, application and infrastructure tests.

Forbidden scope: setup phase ordering, installation-plan/YAML changes,
host-preparation, artifacts, deployment, network topology, local storage,
provider-wide refactors and live infrastructure commands.

Verification plan: focused fake-based Docker/Swarm/DTO/adapter tests, then
`test`, `typecheck`, `arch-lint`, `arch-tests` and the full `quality` gate.
Consolidation must prove structured manager observation, missing/non-Ready/
inactive/uninitialized/wrong-manager rejection, manager-before-worker order,
unavailable-token blocking and redacted evidence.
