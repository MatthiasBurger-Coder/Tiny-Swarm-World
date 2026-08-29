# RC1_BLOCKER-002 — Fix Loop Status

- Issue: #252
- Scenario owner: RC1-02 WSL2 POST-INSTALL ACCEPTANCE
- Classification: RC1_BLOCKER
- Branch: feature/classic-public-beta-rc1-stabilization
- Diagnosis run: 2026-08-23
- Pre-fix result: FAIL
- Post-fix real re-run: PASS

## Observed

The clean WSL2 install completed and the Traefik service was running, but
all browser-relevant HTTPS routes failed TLS verification with the configured
local CA bundle. curl -k reached the routes, while verification with the
configured CA failed.

## Root cause

The Traefik prerequisite generated a new self-signed certificate and private
key remotely inside the manager node, then created the two Docker secrets.
The installer retained an older local CA-bundle path. The Windows-to-WSL
acceptance runner therefore trusted a certificate different from the one
served by the freshly installed Traefik instance.

## Fix implemented

- Generate the Traefik certificate pair locally with the existing OpenSSL
  contract and the required tsw.local SANs.
- Transfer the certificate and private key to the manager only through
  process input encoded for the remote shell; create the existing Docker
  secrets from temporary files and remove those files on exit.
- Atomically write only the public certificate to
  .tiny-swarm-world/local/traefik-live-ca-current.pem.
- Export that path as the installer default
  TSW_LIVE_TLS_CA_BUNDLE when the operator has not configured another CA.
- Reject a partial Traefik TLS secret pair instead of silently creating an
  inconsistent state.

## Local verification

- Focused regression tests: PASS — 108 tests.
- git diff --check: PASS.
- First real RC1 re-run after the initial fix: FAIL — RC1-01
  deployment:traefik-stack returned FAILED_TO_APPLY because the local OpenSSL
  SAN value contained a malformed DNS entry. The same run recorded
  deployment:traefik-service-readiness as FAILED_TO_VERIFY; no workaround or
  partial pass was accepted.
- Corrective iteration: fixed the malformed SAN entry to use
  DNS:localhost, confirmed local material generation, reran focused tests, and
  reran the full quality gate successfully.
- Real RC1-01 re-run after the corrective iteration: PASS — clean WSL2 reset,
  platform and Swarm verification, artifact readiness, all stack applies, and
  platform verification completed successfully. The evidence directory is
  .tiny-swarm-world/evidence/installation-tests/wsl2/20260823T125749Z.
- Real RC1-02 post-install acceptance: PASS — 28 tests; all HTTPS route
  records report https_reachable_verified using the synchronized local CA.

## Closure

The TLS CA synchronization blocker is closed for the affected scenarios.
RC1 progression is released to RC1-03 WSL2 RECONCILE. This does not waive any
later RC1 scenario.

## Required next action

Clean the WSL2 managed state, rerun RC1-01 WSL2 CLEAN FRESH INSTALL, verify
that the generated local CA matches the served Traefik certificate, and only
then rerun RC1-02 WSL2 POST-INSTALL ACCEPTANCE. No later RC1 scenario is
released by the pre-fix acceptance failure.
