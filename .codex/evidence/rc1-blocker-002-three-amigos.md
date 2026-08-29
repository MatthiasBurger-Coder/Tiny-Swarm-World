# RC1_BLOCKER-002 — Three-Amigos Decision

## Scope

- Issue: #252 Classic Profile Stabilization / Public Beta RC1
- Scenario: RC1-02 WSL2 POST-INSTALL ACCEPTANCE
- Classification: RC1_BLOCKER
- Observed failure: browser-relevant HTTPS routes could not be verified with
  the configured local CA bundle after a clean install.
- Current decision: PROCEED_WITH_FIX; RC1 remains blocked until RC1-01 and
  RC1-02 pass again from a clean state.

## Three-Amigos review

### Requirement lead

After a clean install, all mandatory HTTPS routes must be reachable and
verifiable from the supported Windows-to-WSL operator path. A stale, missing,
or mismatched CA bundle is not a valid acceptance result and cannot be
replaced with curl -k, a mock, or an internal-only check.

### System architect

The existing Traefik prerequisite lifecycle remains the single owner for
fresh TLS material. The certificate and private key are generated once on the
local operator host, transferred to the manager only as process input, and
created as the two existing external Docker secrets. The public certificate
is atomically written to the ignored local CA-bundle path used by live
acceptance. The private key is never written to the repository or evidence.
Existing complete secret pairs remain idempotent; a partial pair fails closed.

### Python automation lead

Implement one serial blocker slice in the existing
StackPrerequisiteRegistry, LxcSwarmRuntime, and installer configuration path.
Reuse the existing shell gateway and ProjectPaths; do not introduce a new
transport, framework, or live-test substitute.

### Senior tester

Regression coverage must prove local certificate synchronization, safe
certificate/key input handling, partial-pair rejection, runtime path wiring,
and deterministic TSW_LIVE_TLS_CA_BUNDLE configuration. The real evidence
requirement remains separate: RC1-01 must be repeated cleanly and RC1-02 must
then pass with the synchronized certificate.

### Security review

Only redacted state and presence metadata may enter evidence. The htpasswd
value, generated private key, and secret input payload must not be logged or
persisted in repository evidence. The generated public certificate is local
ignored runtime state only.

### Coordination result

The slice is not safely parallelizable because it changes one ordered
installation lifecycle across runtime wiring, installer defaults, and
regression tests. No callable subagent stream was exposed in this session;
the Three-Amigos role review is therefore recorded as an explicit fallback
and remains subject to the final integration and live E2E review.

## Handoff / completion condition

Run local quality gates, then execute RC1-01 from a freshly reset WSL2
environment. Only after RC1-01 passes may RC1-02 be rerun. Both must pass
before the RC1 progression can continue.
