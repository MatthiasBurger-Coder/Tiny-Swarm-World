# S252-R01 Consolidation Evidence

- Workflow id: `issue-252-classic-public-beta-rc1-remediation-20260823`
- Workflow version: `2026-08-23-remediation-r1`
- Slice: `S252-R01 — Canonical TLS contract and CA lifecycle`
- Branch: `feature/classic-public-beta-rc1-stabilization`
- Rollback baseline: `620fe65a`
- Owner: Senior Python Automation Developer; Codex root retained integration ownership.
- Result: PASS for the bounded R01 scope.

## Consolidated behavior

- Complete external TLS configuration has precedence; incomplete or conflicting
  configuration fails before managed-state mutation.
- Managed CA and separately signed ingress leaf material are generated into
  protected local state and reused byte-for-byte while valid.
- CA/leaf roles, strict server chain, exact SANs, expiry, key pairs, trust
  consistency, regular-file constraints and owner-only private-key modes are
  validated fail-closed.
- Runtime composition injects the TLS resolver through the application port.
- Docker-secret transfer consumes the exact immutable certificate and key byte
  snapshots that were validated; raw material is excluded from object repr,
  commands, logs and evidence.
- Installer compatibility exports resolve to the same canonical managed or
  external trust-bundle path, and conflicting aliases fail closed.

## Verification

- Focused R01 command: PASS, 222 tests.
- `python3 tools/quality_gate.py lint`: PASS.
- `python3 tools/quality_gate.py typecheck`: PASS, 634 files.
- `python3 tools/quality_gate.py quality`: PASS; 1,792 tests, 18 skipped;
  verification policy, lint, three import contracts, 18 architecture tests and
  type checking all passed.
- `git diff --check`: PASS.
- Independent architecture re-review: PASS.
- Independent security re-review: PASS.
- Independent test/acceptance re-review: PASS.
- Live infrastructure commands: not executed in this slice.

Negative regression evidence covers incomplete external configuration,
conflicting trust aliases, wrong CA chains, near-expiry CA and leaf material,
incorrect certificate roles and usages, non-exact SANs, mismatched or shared
keys, trust drift, unsafe permissions, symlinks, incomplete managed state and
source replacement after resolution.

## Explicit deferrals

- `S252-R02` retains atomic certificate/key Docker-secret reconciliation,
  partial-state recovery, rollback and dashboard htpasswd ownership. Existing
  complete pairs only short-circuit in R01; no aggregate atomicity claim is made.
- `S252-R06` retains direct E2E consumption of the resolved trust bundle and the
  remaining E2E portion of `REQ-252-055`. R01 establishes the canonical contract
  and alias consistency but does not claim the live E2E requirement complete.
- Native Linux, live WSL restart, CI, SonarQube and self-hosted-runner evidence
  remain outside R01 and are not inferred from local quality results.
