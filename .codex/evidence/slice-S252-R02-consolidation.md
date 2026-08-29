# S252-R02 Consolidation Evidence

- Workflow id: `issue-252-classic-public-beta-rc1-remediation-20260823`
- Workflow version: `2026-08-23-remediation-r1`
- Slice: `S252-R02 — Atomic Traefik secret reconciliation and GUI input recovery`
- Branch: `feature/classic-public-beta-rc1-stabilization`
- Rollback baseline: `1f00e4e0`
- Result: PASS for the bounded local R02 scope.

## Consolidated behavior

- TLS certificate and key secret names must be distinct. Existing pairs are
  accepted only when both carry Tiny Swarm World ownership and the exact same
  resolved TLS lifecycle fingerprint.
- Unknown, unlabeled or mismatched existing state fails closed without deletion.
  A verified owned orphan can be reconciled. Every create captures its opaque
  Docker secret id, and failures during second create or post-create existence
  and label verification roll back only ids created by that invocation.
- Retrying after rollback converges, and stack application remains gated behind
  successful external-input verification.
- Complete operator-provided Traefik dashboard htpasswd material is validated
  before installer or deployment mutation. Placeholder, control-character,
  blank, malformed and unsupported-hash input fails with content-free errors.
- The htpasswd value is transported through the secret port and never appears
  in command text, result serialization, error messages, logs or evidence.

## Verification

- Exact focused R02 command: PASS, 249 tests.
- `python3 tools/quality_gate.py lint`: PASS.
- `python3 tools/quality_gate.py typecheck`: PASS, 634 files.
- `python3 tools/quality_gate.py quality`: PASS; 1,804 tests, 18 skipped;
  verification policy, lint, three import contracts, 18 architecture tests and
  type checking all passed.
- `git diff --check`: PASS.
- Independent architecture review: PASS.
- Independent security review: PASS after post-verification rollback hardening.
- Independent test/acceptance review: PASS.
- Live Docker, Incus and Swarm commands: not executed.

Deterministic regressions cover none/both/certificate-only/key-only states,
unknown and mismatched labels, duplicate names, second-create rollback and
retry, post-create existence and ownership failures, positive htpasswd
provisioning, preparation-before-verification-before-apply ordering, blocked
stack execution and redaction.

## Scope notes and deferrals

- `tests/test_install_script.py` includes the ingress package files introduced
  by R01 because the installer source manifest must close over imports before
  the R02 installer path can execute. This is an inherited R01 bootstrap-closure
  correction inside the explicitly authorized R02 installer-test lock.
- The accepted Traefik htpasswd formats retain compatibility with bcrypt and
  recognized legacy formats. R07 must document bcrypt as the recommended
  operator choice and record the legacy-algorithm hardening consideration.
- Live secret-store reconciliation remains a serialized live-validation item;
  no local unit or quality result is reported as live evidence.
