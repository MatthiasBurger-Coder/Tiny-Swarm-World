# Issue #154 Slice 03 Consolidation

Workflow: `issue-154-20260808`
Slice: `03 — Harden structured managed-cluster verification`

Decision: `ACCEPTED — SERIAL FALLBACK REVIEW`

## Role review

No callable subagent tools were exposed. Senior Python Automation Developer,
Senior System Architect, Senior Tester and Senior DevOps Engineer reviews were
performed explicitly in the main execution thread. The runtime review confirms
that verification remains inside managed LXC/Incus nodes and does not query
host Docker. All tests use fakes; no live infrastructure command was run.

## Implemented contract hardening

- Extended `SwarmNodeReadinessEvidence` with normalized manager state and
  explicit manager-leader validation for manager nodes.
- Extended `PortContainerSwarmBootstrap` with manager-observed structured
  membership inspection.
- Added managed-manager `docker node ls --format '{{json .}}'` inspection in
  the LXC adapter, with typed mapping for expected nodes, Docker Ready state,
  Swarm Active state, observed role, manager count and leader state.
- Missing, malformed, unobserved, non-Ready, inactive and wrong-manager
  observations remain non-success; expected-node completeness is preserved.
- Routed the provider-selected runtime bridge to the new port method. This
  bridge file was changed because the new application port otherwise could not
  reach the selected managed adapter.
- Changed cluster membership verification to consume manager-observed DTOs,
  rather than local worker/manager `docker info` checks.
- Added a `usable` credential predicate and blocked worker joins when the
  adapter returns an unavailable placeholder, before any join call.
- Kept credential values out of results, evidence and representations.
- Added all-expected-node Docker verification coverage and updated affected
  verification fakes to implement the new contract.

## Verification evidence

Focused structured Docker/Swarm/DTO/adapter suite: 54 tests passed.

Required gates:

- `python3 tools/quality_gate.py test`: PASS, 1629 tests, 28 skipped.
- `python3 tools/quality_gate.py typecheck`: PASS, no mypy issues.
- `python3 tools/quality_gate.py arch-lint`: PASS, 3 contracts kept.
- `python3 tools/quality_gate.py arch-tests`: PASS, 18 tests.
- `python3 tools/quality_gate.py quality`: PASS; verification policy,
  lint, arch-lint, arch-tests, typecheck and test all passed.

The first repository-wide test run after the port change correctly exposed
three stale test doubles/fixtures. They were updated to the explicit
membership contract and leader-state requirement; the rerun passed. This is
recorded as a repaired contract regression, not an accepted failing gate.

## Scope and consolidation decision

Changed files are limited to the listed DTO, port, platform service, managed
adapter and focused tests, plus the necessary provider-selected runtime bridge
and its affected verification fake. No setup composition, installation plan,
host preparation, artifact, deployment, network, local-storage or live
provider files were changed.

Slice 03 is accepted for checkpointing. Setup phase wiring and downstream
`not_run` behavior remain in Slice 04.
