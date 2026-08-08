# Issue #154 Slice 01 Consolidation

Workflow: `issue-154-20260808`
Slice: `01 — Extract Docker and Swarm ownership from platform phases`

Decision: `ACCEPTED — SERIAL FALLBACK REVIEW`

## Role review

No callable subagent tools were exposed, so the required review was performed
explicitly in the main execution thread by the Senior Python Automation
Developer, Senior System Architect, Senior Tester and Senior Requirement
Engineer roles. Senior DevOps boundary review found no host, Incus, Docker,
Swarm or deployment command was executed. Frontend and console/UI streams were
not applicable.

## Implemented ownership change

- Added an explicit `ClusterWorkflows` bundle to the composition model.
- Kept `platform init` limited to managed-node ensure steps.
- Kept `platform reconcile` limited to managed-node ensure steps.
- Moved Docker installation and Swarm bootstrap step assembly to the cluster
  bundle.
- Moved Docker and Swarm verification out of final `platform verify` and into
  cluster verification.
- Reused the existing typed services, ports, workflow runners and per-node
  steps; no duplicate runtime implementation was introduced.
- Updated composition tests to assert the ownership boundary and the separate
  cluster workflow step lists.

Setup phase names and installation-plan/YAML mapping remain intentionally
deferred to Slice 02 and setup-boundary wiring to Slice 04. The attached file
`port_local_file_storage.py` was not changed because the active workflow marks
local-storage behavior outside Issue #154 scope.

## Verification evidence

Baseline focused suite before implementation: 142 tests passed.

Focused post-change suite:

```text
PYTHONPATH=src python3 -m unittest \
  tests.application.services.platform.test_lxc_docker_install \
  tests.application.services.platform.test_lxc_swarm_bootstrap \
  tests.application.services.platform.test_platform_workflows \
  tests.infrastructure.test_composition
Ran 142 tests ... OK
```

Required gates:

- `python3 tools/quality_gate.py test`: PASS, 1623 tests, 28 skipped.
- `python3 tools/quality_gate.py typecheck`: PASS, no mypy issues.
- `python3 tools/quality_gate.py arch-tests`: PASS, 18 tests.
- `python3 tools/quality_gate.py quality`: PASS; verification policy,
  lint, arch-lint, arch-tests, typecheck and test all passed.

The first 120-second test-gate invocation timed out without a test result;
the same gate was rerun with a longer bounded timeout and passed. This is an
execution-history note, not a product failure.

## Scope and consolidation decision

Changed files are limited to the composition model, composition root and
focused composition tests. No host-preparation, artifact, deployment,
network, local-storage or live-provider files were changed. Existing root
`.codex/evidence/slice-01-*` history was preserved; this issue-scoped record
is used for Issue #154 execution evidence.

Slice 01 is accepted for checkpointing. Remaining Issue #154 requirements are
not claimed complete and continue in the dependent slices.
