# Issue #187 — S187-02 Consolidation Evidence

- Workflow: `issue-187-20260809` / `issue-187-v1.0.0`
- Slice: `S187-02` — Registry and probe extraction
- Execution branch: `feature/preflight-service-probe-registry-solid`
- Decision: `PASS`
- Execution mode: sequential under the host-service-probe contract lock.
- Real subagents used: no callable project-subagent tool was exposed; role-
  based architecture, Python, tester and security fallback review completed.

## Implementation result

Added the `preflight/service_probes` package with `ServiceProbe`, typed HTTP
and callback strategies, `ServiceProbeRegistry` and the compatibility-ordered
default registry. `HostPreflightProbe.port_matches_expected_service` keeps its
public signature and delegates to the registry. Low-level response parsing,
TLS validation, TCP connection behavior and unrelated host checks remain
outside the strategy registry.

## Verification

- focused Ruff: PASS
- focused registry and HostPreflightProbe tests: PASS (`44` tests)
- `git diff --check`: PASS
- local quality gate: PASS
  - verification-policy: PASS
  - lint: PASS
  - arch-lint: PASS (3 contracts kept, 0 broken)
  - arch-tests: PASS
  - typecheck: PASS (`Success: no issues found in 599 source files`)
  - tests: PASS (`1689` passed, `28` skipped)

No live network, browser, infrastructure or external quality-system result is
claimed.

## Handoff

S187-03 may run the independent compatibility and completion audit.
