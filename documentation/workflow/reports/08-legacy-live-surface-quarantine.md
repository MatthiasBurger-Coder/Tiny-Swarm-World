# Slice 08 Report: Legacy Live-Surface Quarantine

## Status

```text
COMPLETED_PUSHED
```

## Changes

- Added `documentation/system/live-operation-surfaces.adoc` as the canonical
  static catalog for guarded, transitional, deprecated, legacy, and supported
  asset surfaces.
- Classified guarded CLI workflows, Portainer/Nexus direct helpers, image
  build/push helpers, Portainer stack upload, Jenkins/Swagger compose assets,
  and legacy `infra/swarm/**` helpers.
- Added direct README markers for `infra/compose` and `infra/prepare/nexus`.
- Updated README, deployment, installation, usage, and system documentation to
  point to the live-operation catalog.
- Corrected Nexus deployment documentation defaults to match
  `infra/prepare/nexus/setup.py` for endpoint and retry attempts.
- Added architecture tests that require catalog references, key surface
  classifications, and Nexus documented default parity.

## Review Notes

- No live Multipass, Docker Swarm, compose deployment, Docker build, image
  push, netplan, socat, Portainer, Nexus, Jenkins, RabbitMQ, SonarQube,
  Swagger/NGINX bootstrap, or service command was run.
- No scripts were removed or promoted; ADR is not required for this slice.
- Existing hardcoded local defaults in legacy/transitional scripts are
  documented as compatibility surface and must not be copied into new product
  configuration or logs.
- `infra/swarm/**` remains legacy and is not a supported workflow entry point.

## Verification

```text
PYTHONPATH=src python3 -m unittest tests.architecture.test_legacy_surface_documentation
PASS, 6 tests
```

```text
git diff --check
PASS
```

```text
python3 tools/quality_gate.py arch-tests
PASS, 14 tests
```

```text
python3 tools/quality_gate.py test
PASS, 253 tests, 1 skipped
```

```text
/tmp/tsw-quality-venv/bin/python tools/quality_gate.py quality
PASS
```

Gate result details:

```text
lint: PASS
arch-lint: PASS, 3 contracts kept and 0 broken
arch-tests: PASS
typecheck: PASS, no issues found in 249 source files
test: PASS, 253 tests run, 1 skipped
```

## CP_RECORD

```yaml
Slice-ID: "08"
workflowVersion: "system-unification-v1.0.0"
sliceTitle: "Legacy Live-Surface Quarantine"
responsibleRole: "senior_devops"
reviewedRoles:
  - "senior_devops"
  - "senior_system_architect"
  - "senior_security_sandbox_engineer"
  - "senior_tester"
changedFiles:
  - "README.md"
  - "documentation/deployment/system.adoc"
  - "documentation/system/system.adoc"
  - "documentation/system/live-operation-surfaces.adoc"
  - "documentation/user_guide/installation.adoc"
  - "documentation/user_guide/usage.adoc"
  - "infra/compose/README.md"
  - "infra/prepare/nexus/README.md"
  - "infra/prepare/portainer/README.md"
  - "infra/swarm/README.md"
  - "tests/architecture/test_legacy_surface_documentation.py"
  - "documentation/workflow/context-pack.md"
  - "documentation/workflow/context-pack.json"
  - "documentation/workflow/reports/08-legacy-live-surface-quarantine.md"
  - "documentation/workflow/execution-report.md"
qualityGates:
  - command: "PYTHONPATH=src python3 -m unittest tests.architecture.test_legacy_surface_documentation"
    result: "PASS"
  - command: "git diff --check"
    result: "PASS"
  - command: "python3 tools/quality_gate.py arch-tests"
    result: "PASS"
  - command: "python3 tools/quality_gate.py test"
    result: "PASS"
  - command: "/tmp/tsw-quality-venv/bin/python tools/quality_gate.py quality"
    result: "PASS"
rollbackReference: "revert this Slice 08 checkpoint commit on codex/workflow-system-unification-20260524"
arc42Updated: false
adrUpdated: false
checkpointCommit: "14f3f667cbca6e87a48cf1b1bd350386a149bcde"
checkpointPush: "origin/codex/workflow-system-unification-20260524"
```

## Slice 08 Decision

```text
READY_FOR_NEXT_SLICE
```

Slice 09 may proceed to final documentation synchronization and workflow
execution reporting. Live-operation surfaces are classified without executing
them.
