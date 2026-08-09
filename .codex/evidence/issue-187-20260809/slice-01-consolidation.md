# Issue #187 — S187-01 Consolidation Evidence

- Workflow: `issue-187-20260809` / `issue-187-v1.0.0`
- Slice: `S187-01` — Service/fingerprint behavior inventory
- Execution branch: `feature/preflight-service-probe-registry-solid`
- Decision: `PASS`
- Execution mode: sequential; the shared host-service-probe contract is
  locked for extraction.
- Real subagents used: no callable project-subagent tool was exposed; the
  role-based fallback review was completed in the main thread.

## Inventory result

The current ordered conditional contract is fully recorded in
`responsibility-map-before.md`: Portainer, Docker Registry, Nexus, Jenkins,
Pulsar Admin/Manager/broker, SonarQube, Swagger API/UI, Traefik HTTP/HTTPS,
Service Access and Infisical HTTP/HTTPS, followed by unsupported false.

The inventory preserves exact paths, markers, HTTPS/TCP semantics, first-match
ordering and safe network-failure behavior. Host environment detection,
executable checks, secrets and Git scanning are explicitly out of the registry
scope. No ambiguous fingerprint or missing current test case was found.

## Verification

`git diff --check` passed. The required local quality gate passed:

- verification-policy: PASS
- lint: PASS
- arch-lint: PASS (3 contracts kept, 0 broken)
- arch-tests: PASS
- typecheck: PASS (`Success: no issues found in 595 source files`)
- tests: PASS (`1685` passed, `28` skipped)

This is local verification only; no live host, network, browser or external
quality-system result is claimed.

## Handoff

S187-02 may extract the registry and probe strategies against the frozen
responsibility map.
