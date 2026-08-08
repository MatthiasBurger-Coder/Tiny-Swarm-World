# Issue #154 Slice 04 Consolidation

Workflow: `issue-154-20260808`
Slice: `04 — Wire setup boundaries and downstream not_run`

Decision: `ACCEPTED — SERIAL FALLBACK REVIEW`

## Role review

No callable subagent tools were exposed. The required Python Automation
Developer, System Architect, Tester and Requirement Engineer reviews were
performed explicitly in the main execution thread. No live infrastructure
operation was required or executed.

## Implemented setup boundary

The composition root now assembles the executable setup sequence as:

```text
platform init
platform reconcile
cluster docker
cluster swarm bootstrap
cluster verify
platform expose
deployment bootstrap
artifact bootstrap
artifact readiness gate
artifacts prepare
artifacts verify
deployment apply
deployment verify
platform verify
```

The installation plan arranges the same names, so the cluster verification
result is the sole generic `SetupWorkflow` gate before routing and all later
work. No second stop mechanism or duplicated `not_run` logic was introduced.

## Verification evidence

Focused setup/composition suite: 125 tests passed.

Required gates:

- `python3 tools/quality_gate.py test`: PASS, 1630 tests, 28 skipped.
- `python3 tools/quality_gate.py typecheck`: PASS, no mypy issues.
- `python3 tools/quality_gate.py arch-tests`: PASS, 18 tests.
- `python3 tools/quality_gate.py quality`: PASS; verification policy,
  lint, arch-lint, arch-tests, typecheck and test all passed.

The added setup-boundary test confirms that a blocked `cluster verify` leaves
`platform expose`, deployment bootstrap, artifact bootstrap/readiness/prepare/
verify, deployment apply/verify and final platform verify as `not_run`.

## Scope and consolidation decision

Changed product scope is limited to setup composition and the existing setup/
composition tests. The generic setup workflow was reused unchanged. No
installation-plan/YAML, runtime, host, artifact, deployment, network or local
storage behavior was changed in this slice.

Slice 04 is accepted for checkpointing. Regression and completion evidence
remain in Slices 05 and 06.
