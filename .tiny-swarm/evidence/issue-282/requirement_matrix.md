# Requirement Matrix: #282 / CRED-04

This matrix is the mandatory dependency/use-case inventory for the cleanup.
It is committed separately before the implementation cleanup. The entries
below describe the baseline consumers first and the intended migration after
those consumers are removed or rewritten.

| Item / requirement | Baseline consumer | Classification | Migration / supported consumer after cleanup | Planned verification | Status |
|---|---|---|---|---|---|
| `.tiny-swarm-world/local/live-installation.env` | `simple_installer` operator override loading | KEEP | One explicit operator override file; no generated values are written to it | override tests; docs | OPEN |
| `.tiny-swarm-world/local/fixed-secrets.env` | legacy installer fixed mode and `FixedEnvSecretSource` | MIGRATE/DELETE | Remove fixed-mode consumer; custom values use the central operator override/process environment contract | source/reference search; rejection tests | OPEN |
| `.tiny-swarm/secrets/bootstrap.local.env` | legacy installer Infisical persistence | MIGRATE/DELETE | Remove bootstrap persistence; explicit operator override remains the only local input | deleted-path search; installer tests | OPEN |
| `.tiny-swarm/secrets/generated.local.env` | generated-mode sync/reuse and recovery tests | MIGRATE/DELETE | Remove generated-default recovery; catalog-backed reruns remain deterministic without a file | no-file rerun tests | OPEN |
| Installer credential generators | `installer._generated_secret_values`, SonarQube regeneration | DELETE | Catalog and explicit operator values are the only standard credential inputs; test nonces/trace IDs are unrelated and remain | source search; deterministic tests | OPEN |
| Sync credential generator | `secret_management._generate_secret` and rotate branch | DELETE | No generated credential is created by sync; rotation remains an explicit provider operation only | sync tests; source search | OPEN |
| Generated-default recovery/persistence helpers | installer export snapshots and generated-file writers | DELETE | No standard recovery state is created or required | fresh-install and rerun tests | OPEN |
| `internal-test` mode | normal `simple_installer` path and catalog resolver | KEEP | Normal path has one fixed catalog-backed behavior, represented only as evidence metadata | installer/integration tests | OPEN |
| `generated`, `fixed`, `infisical` mode selectors | installer CLI/config branches and mode tests | MIGRATE/DELETE | Remove mode selection and dead branches; retain secure Infisical synchronization and operator overrides as lifecycle concerns, not selectable modes | CLI/config rejection and composition tests | OPEN |
| `EnsureInfisicalSilentInstall` / `InfisicalBootstrapStep` | service-access bootstrap workflow | KEEP | Self-hosted Infisical bootstrap remains explicit and service-access scoped | ordering/profile tests | OPEN |
| `InfisicalSecretSyncStep` / `SecretSyncUseCase` | all composed profiles currently build sync | MIGRATE | Keep only post-bootstrap service-access synchronization; default profile must not construct or invoke it | profile tests; call-count tests | OPEN |
| `simple_installer -> installer` | normal wrapper delegates to legacy installer | MIGRATE | Keep the wrapper boundary while legacy implementation accepts the single standard contract only | installer delegation tests | OPEN |
| Secret manifest | `SecretManifestRenderer` and deployment consumers | KEEP | Inventory owns keys/types/consumers; it does not generate or persist values | manifest contract tests | OPEN |
| Installer required-key selection | `_required_installer_secret_entries` and manifest | MIGRATE | Derive required bootstrap keys from the manifest and exclude external Docker-secret references by type/source | manifest/integration tests | OPEN |
| Credential catalog | `CredentialResolutionService` / `CredentialResolver` | KEEP | One value authority for deterministic internal-test defaults and component derivations | catalog/resolver tests | OPEN |
| Configuration contract | `default_configuration_contract()` | MIGRATE | Own non-secret configuration validation; no duplicate secret value authority | architecture/config tests | OPEN |
| Setup manifest | `default_setup_manifest()` | KEEP | Own setup workflow/service inventory, distinct from credential key/value ownership | setup manifest tests | OPEN |
| Secret storage preflight | `SecretStorageProbe` and preflight composition | MIGRATE | Validate only an explicitly supplied operator override when applicable; do not require removed generated/fixed state | absent-file/override preflight tests | OPEN |
| Secret discovery and redaction | `SecretDiscoveryStep`, `SecretRedactor` | KEEP | Preserve tracked-config classification and value redaction | discovery/redaction tests | OPEN |
| Evidence and operational recovery | `SecretEvidenceWriter`, verification/evidence repositories | KEEP | Preserve sanitized evidence and infrastructure recovery; remove only generated credential recovery state | evidence/recovery regression tests | OPEN |
| Current mode docs/tests/examples | legacy mode references across README, guides, contracts, and tests | MIGRATE/DELETE | Rewrite standard instructions and remove obsolete mode/generated-state examples | repository reference search; docs review | OPEN |

## Requirement-to-acceptance mapping

| ID | Issue #282 requirement | Implementation target | Verification | Status |
|---|---|---|---|---|
| CRED-04-REQ-001 | KEEP/MIGRATE/DELETE matrix exists before cleanup. | This file, committed in a preparation-only commit before cleanup edits | branch history and evidence review | UNVERIFIED |
| CRED-04-REQ-002 | Random default-password generation is absent from the standard path. | Standard installer remains catalog-only; obsolete generators removed | deterministic installer tests and source search | OPEN |
| CRED-04-REQ-003 | Recovery state used only for generated test defaults is removed. | Remove generated/bootstrap persistence paths from standard and obsolete modes | no-file rerun tests and deleted-path search | OPEN |
| CRED-04-REQ-004 | Overlapping local credential files are eliminated or have distinct responsibilities. | Retain one explicit operator override file; remove fixed/bootstrap/generated files | docs/config/source search | OPEN |
| CRED-04-REQ-005 | Obsolete modes are removed or isolated as supported advanced paths. | Remove mode selection and dead mode branches; retain secure/operator overrides | CLI and composition tests | OPEN |
| CRED-04-REQ-006 | Catalog, installer, and manifest have no duplicate credential authority. | Catalog owns values; manifest owns inventory; installer derives required keys | manifest/catalog integration tests | OPEN |
| CRED-04-REQ-007 | Preflight does not enforce rules solely for removed state. | Existing explicit-file validation is optional and operator-driven | preflight absent-file/override tests | OPEN |
| CRED-04-REQ-008 | Real override/custom-secret redaction remains intact. | Keep central resolver, protected file checks, and sanitized evidence | redaction/security tests | OPEN |
| CRED-04-REQ-009 | Dead docs/examples/tests are removed or rewritten. | Update README, user guides, contracts, and legacy tests | docs/reference search; full gate | OPEN |
| CRED-04-REQ-010 | Full quality gate passes. | Repository verification | `python3 tools/quality_gate.py quality` | OPEN |
| CRED-04-REQ-011 | Changed code reaches at least 95% coverage. | Changed cleanup paths and compatibility routing | branch-aware diff coverage | OPEN |

## Sequencing gate

This matrix must be committed before the destructive or mode-removal commit.
The implementation may only remove a row's baseline consumer after the row
has a named replacement or an explicit DELETE decision. A missing supported
consumer blocks completion.

## Redaction boundary

Inventory and evidence contain only path names, component names, source
labels, and statuses. They never contain credential values, tokens, raw env
files, authorization headers, or private runtime endpoints.
