# Issue #192 — S192-01 Consolidation Evidence

- Workflow: `issue-192-20260809` / `issue-192-v1.0.0`
- Slice: `S192-01` — Wrapper/API responsibility inventory
- Execution branch: `feature/separate-lxc-service-wrappers-solid`
- Decision: `PASS`
- Execution mode: sequential under the LXC service HTTP contract lock.
- Real subagents used: no callable project-subagent tool was exposed; the
  role-based fallback review was completed in the main thread.

## Inventory result

The #238 service modules already own manager-IP resolution, local URL
construction and Portainer/Nexus HTTP delegation. Composition imports the
concrete modules; the legacy Swarm runtime contains compatibility facades and
the patch seam required by existing callers/tests.

URL precedence is unambiguous: Portainer `api_url` is selected before manager
IP resolution; absent `api_url` resolves the manager IP and constructs the
validated local URL. Admin cookie clearing, injected sessions and credential
redaction are existing contracts to protect with focused tests. No duplicate
wrapper or unknown consumer was found.

## Verification

`git diff --check` passed. The required local quality gate passed:

- verification-policy: PASS
- lint: PASS
- arch-lint: PASS (3 contracts kept, 0 broken)
- arch-tests: PASS
- typecheck: PASS (`Success: no issues found in 599 source files`)
- tests: PASS (`1691` passed, `28` skipped)

The local gate is authoritative; no live Portainer/Nexus, browser or external
quality-system result is claimed.

## Handoff

S192-02 may close residual contract-test/architecture gaps without relocating
HTTP policy into the Swarm runtime.
