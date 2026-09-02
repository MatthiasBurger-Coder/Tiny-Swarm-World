# Requirement Matrix: #280 / CRED-02

Issue: `[EPIC 02 / CRED-02] Make deterministic credentials the standard internal-test installation path`

Parent: #277 — Simplify Credentials for the Internal-Test Profile
Dependency: #279 — canonical deterministic credential catalog

| ID | Requirement from issue | Type | Files likely affected | Implementation evidence | Test/evidence proof | Status |
|---|---|---|---|---|---|---|
| CRED-02-REQ-001 | The normal Classic/internal-test installation path resolves standard credentials from the canonical CRED-01 catalog. | functional / architecture | `src/tiny_swarm_world/simple_installer.py`, `src/tiny_swarm_world/installer.py` | `simple_installer.main` pins `InstallerOptions` to `internal-test`; `_prepare_bootstrap_environment` resolves through catalog APIs | `test_main_passes_internal_test_options_to_legacy_execution`; `test_populates_every_required_manifest_key_from_catalog` | VERIFIED |
| CRED-02-REQ-002 | A fresh internal-test checkout needs no manually created ordinary-password file or generated-password recovery state. | functional | `simple_installer.py`, installer docs | Standard resolver is stateless and creates no bootstrap/recovery file | `test_resolves_catalog_defaults_without_creating_recovery_state` | VERIFIED |
| CRED-02-REQ-003 | Portainer receives the canonical internal-test credential. | functional | installer resolution path, tests | `TSW_PORTAINER_ADMIN_PASSWORD` is resolved from the catalog | `test_resolves_catalog_defaults_without_creating_recovery_state`; `test_populates_every_required_manifest_key_from_catalog` | VERIFIED |
| CRED-02-REQ-004 | Infisical bootstrap receives its deterministic test credentials without an existing Infisical dependency. | functional / bootstrap | installer resolution path, tests | Infisical keys are resolved locally before the legacy execution call | `test_main_passes_internal_test_options_to_legacy_execution`; required-key catalog test; no service/network call in resolver | VERIFIED |
| CRED-02-REQ-005 | Other active Classic services receive the catalog values consistently, including documented special-format values. | functional | installer resolution path, manifest/catalog integration | Every required manifest key is resolved via the catalog; Traefik `htpasswd` uses its catalog exception | `test_populates_every_required_manifest_key_from_catalog`; `test_resolves_catalog_traefik_htpasswd_without_random_generation`; CRED-01 catalog tests | VERIFIED |
| CRED-02-REQ-006 | The standard internal-test path does not invoke random password generation for catalog-managed defaults. | safety / functional | `simple_installer.py`, tests | Random-generation helper was removed from the standard resolver | patched `_generated_secret_values` regression in `test_resolves_catalog_traefik_htpasswd_without_random_generation`; static search | VERIFIED |
| CRED-02-REQ-007 | Reinstall/reconcile resolves exactly the same defaults without reading a generated-password recovery file. | functional / lifecycle | `simple_installer.py`, tests | Two independent resolver calls use the immutable catalog and no default file | `test_resolves_catalog_defaults_without_creating_recovery_state` | VERIFIED |
| CRED-02-REQ-008 | Credential resolution does not add raw credentials to diagnostics or evidence output. | security | installer context/reporting, tests | Resolver only prepares process values; existing operator output remains limited to intentional login material and internal values remain hidden | `test_completion_output_exposes_only_operator_credentials`; context/reporting static review | VERIFIED |
| CRED-02-REQ-009 | Existing explicit overrides are preserved; unsupported legacy modes are identified for CRED-03/CRED-04 rather than silently discarded. | compatibility | installer resolution and issue evidence | Environment values and explicitly named compatibility files win over catalog defaults; old modes remain behind legacy layer | `test_preserves_explicit_environment_override`; `test_loads_only_explicit_bootstrap_override_file`; risk note | VERIFIED |
| CRED-02-REQ-010 | Unit/integration tests cover fresh resolution, rerun equality, component exceptions, and missing/invalid catalog definitions. | quality | `tests/test_simple_installer.py`, catalog tests | Focused installer and catalog regression tests cover all requested local cases | 12 simple-installer tests + 10 CRED-01 catalog tests passed | VERIFIED |
| CRED-02-REQ-011 | Introduced or materially changed code reaches at least 95% test coverage. | quality-gate | changed Python modules | `simple_installer.py` is covered by the focused branch-aware run | 79 statements, 99% coverage | VERIFIED |
| CRED-02-REQ-012 | No-override, reconcile, and unsupported-component scenarios behave as specified by the issue. | acceptance / BDD | installer and tests | Catalog default, rerun equality, explicit override, and Traefik exception paths are executable | focused scenario tests passed | VERIFIED |
| CRED-02-REQ-013 | The resolver behavior and configuration contract are documented, with key names only in traces/evidence. | documentation / evidence | `documentation/arc42/08_configuration/rc1-simple-secret-bootstrap.md`, issue evidence | Documentation describes catalog authority, stateless default path, override boundary, and test-only safety | `git diff --check`; documentation review; this evidence package | VERIFIED |

## Applicability

| Gate | State | Rationale |
|---|---|---|
| Local unit/integration verification | `APPLICABLE_LOCAL` | Credential resolution and installer wiring change without requiring infrastructure. |
| Full local quality gate | `APPLICABLE_LOCAL` | Python installer behavior and tests are materially changed. |
| Live installation/browser/API verification | `NOT_APPLICABLE` for CRED-02 | Live proof belongs to CRED-07; no live infrastructure mutation is part of this issue. |
| SonarQube/external gate | `NOT_APPLICABLE` for local issue completion | No accessible external result is required to verify this local resolver slice. |
