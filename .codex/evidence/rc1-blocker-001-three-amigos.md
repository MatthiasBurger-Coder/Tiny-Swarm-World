# RC1_BLOCKER-001 — Three-Amigos Decision

## Scope

- Issue: #252 Classic Profile Stabilization / Public Beta RC1
- Scenario: RC1-01 WSL2 CLEAN FRESH INSTALL
- Observed blocker: after platform reset, the Traefik stack could not converge
  because the external Docker secret named by `TSW_TRAEFIK_GUI_USERS_SECRET_NAME`
  was absent.
- Classification: `RC1_BLOCKER`
- Current decision: `PROCEED_WITH_FIX`; RC1 remains blocked until a clean real
  re-run passes.

## Three-Amigos review

### Requirement lead

The required behavior is explicit: a fresh install must make the
operator-provisioned Traefik htpasswd material available after reset, before
Traefik stack deployment, and must verify the external Docker secret before
the stack is applied. A missing operator value must fail closed; it must not be
generated, mocked, skipped, or treated as a pass.

### System architect

Use the existing `PortSwarmStackRuntime.ensure_external_secret` port and the
existing `DeploymentApplyWorkflow` pre-apply step/check boundary. Keep the
public `composition.py` facade unchanged. The secret value remains in the
operator environment and is passed only as process input to the existing
Docker-secret adapter. No domain dependency on Docker, shell, or filesystem is
introduced.

### Python automation lead

Implement one serial slice in the existing composition path:

1. define `TSW_TRAEFIK_GUI_USERS_HTPASSWD` as an operator-only input;
2. add an idempotent pre-apply ensure step when the value is present;
3. add a pre-apply existence check for the named external Docker secret;
4. require the operator input during installer preparation so a clean reset
   is not started without the required material.

The existing generic secret ensure/verify services and the existing LXC Swarm
runtime are reused. No new CI, framework, mock-based release claim, or
unrelated refactor is in scope.

### Senior tester

Regression coverage must prove: supplied material is wired into the
pre-apply lifecycle, an existing secret is not recreated, a missing secret is
blocked before stack apply, and the raw value is absent from commands and
verification evidence. Tests remain local/unit-level; RC1 qualification still
requires the real WSL2 E2E re-run.

### Security and dependency review

- The htpasswd value is operator-owned and must be supplied through the ignored
  local installation environment or process environment.
- No default, generated value, manifest value, log, or evidence payload may
  contain the material.
- This is one ordered slice because composition, installer, and test wiring
  share execution order and state. Parallel edits would create overlapping
  lifecycle decisions.
- No callable subagent stream was exposed in this session; the required role
  review is recorded here as an explicit fallback and remains subject to the
  final integration review.

## Accepted assumption

The operator input key is `TSW_TRAEFIK_GUI_USERS_HTPASSWD`. Its value is the
complete htpasswd file content expected by Traefik, not a clear-text password.
The repository will not invent or derive that content.

## Handoff / completion condition

The implementation slice is complete only after local gates pass and RC1-01
is repeated from a clean WSL2 state with the resulting evidence showing the
secret was present before Traefik deployment and the complete scenario passed.
