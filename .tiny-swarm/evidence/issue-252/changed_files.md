# Issue #252 Remediation Changed Files

Implementation baseline: `60d5d09f`

The exact product/test changes are the committed R01-R06 diffs:

- `b88255f1` — canonical TLS domain, port, resolver, installer/runtime wiring and tests.
- `70eef782` — atomic Traefik secret-pair and dashboard htpasswd pre-apply behavior and tests.
- `2f107bf8` — bounded Incus provider readiness and tests.
- `6da94de6` — managed-manager artifact readiness and tests.
- `aad6ab53` — read-only Native Linux kernel prerequisite verification, tests and installation guidance.
- `60d5d09f` — bounded canonical Classic E2E readiness and composition integration tests.

R07 changes only the workflow-authorized Arc42, configuration, requirement and
evidence surfaces. `git diff --name-only aad6ab53..60d5d09f` and the preceding
slice commit diffs remain the authoritative file-level product record.
