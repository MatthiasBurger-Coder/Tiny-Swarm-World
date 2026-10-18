# Issue #442 / LCM-W02 requirement matrix

Baseline: `4ddc2d7d50e371922f04cd59b8340070a76dc8f1` (see test_results.md for full SHA). Scope: Classic,
native Linux/WSL2, prepared Git checkout. W01 #441 is merged; its accepted
lifecycle ADR is design authority. The active workflow describes historical
#355 and is not executed or modified. This issue owns lifecycle domain, ports,
service, local state/catalog adapters, read-only CLI, tests and documentation.
No overlapping work or locks existed; initial working tree was clean. This
matrix was created before implementation; rows below now map delivered evidence.

| ID | Requirement from issue | Type | Files affected / implementation evidence | Test evidence | Status |
|---|---|---|---|---|---|
| REQ-01 | Versioned installation identity, release/revision/model/lock/config schema; requested/resolved selection and reasons; component desired/observed upstream/tag/digest/build identities; credential references only | domain/security | domain/lifecycle/models.py: InstallationManifest, ProductIdentity, VersionIdentity, CredentialReference; symbolic configuration and operation/checkpoint provenance | ManifestContractTests current roundtrip, invalid/secret-field rejection, selection/provenance invariants, identity/drift tests | VERIFIED_LOCAL |
| REQ-02 | Canonical versioned service catalog; schema, dependency/resource/profile/capability support, compatibility/migration ownership and #318 integration | architecture | models.py ComponentCatalog/ServiceDefinition; NativeComponentCatalog projects existing deployment/image/Compose authorities; installation-manifest.md Schema and ownership | NativeCatalogTests bundle coverage, foundations, policies, missing/malformed/mismatched assets; LifecycleServiceTests dependency/preset rejection | VERIFIED_LOCAL |
| REQ-03 / LCM-W02-AC1 | Validate current/existing, unknown and corrupt state; explicit migration policy and tests | functional | decode_manifest: identity migration for only admitted v1; legacy/future migration rejection; domain strict schema fields | ManifestContractTests lossless roundtrip, catalog exact-int checks and unknown/legacy/future/corrupt/duplicate JSON cases; repository preservation test | VERIFIED_LOCAL |
| REQ-04 / LCM-W02-AC2 | Non-mutating reads/preview, atomic writes, interruption handling, no-op and preservation of unrelated operator configuration | persistence | JsonManifestRepository token/CAS+flock, private temporary file/fsync/replace/directory fsync, orphan diagnostics; InstallationLifecycleService preview | JsonManifestRepositoryTests missing read, atomic/no-op/unrelated YAML, stale token, pre/post-replace failures, fsync, orphan and symlink tests; CLI no-write test | VERIFIED_LOCAL |
| REQ-05 / LCM-W02-AC3 | Explicit installed/desired version drift including resolved image identity and absent observations; redacted inspection | observability | ComponentState.drift; inspect; product version/services list read-only CLI, per-service installation state | ManifestContractTests versions/resolved digest drift; catalog digest-only/local-build separation; LifecycleServiceTests missing-observation output; LifecycleCliTests sanitized failure/no runtime wiring | VERIFIED_LOCAL |
| REQ-06 / LCM-W02-AC4 | Safe adoption of existing installations or actionable refusal of ambiguous state | functional/security | adopt: explicit inventory/preview/approval, exact component membership/foundations/dependencies/preset, existing identity/orphan refusal; documentation's blocked legacy operator path | LifecycleServiceTests preview, approval, repeat no-op, incomplete inventory, identity conflict, interrupted adoption and persistence failure | VERIFIED_LOCAL |
| REQ-07 | Follow #313/#314 architecture and existing lifecycle boundaries; keep #297 unchanged, foundations mandatory, Classic only; no parallel logical schema/engine, no implicit reset/deletion/rotation or unqualified profiles | architecture/safety | inward-only ports/service, native catalog references, composition facade and early read-only CLI routing; lifecycle ADR/contract preserved; no infrastructure commands added | Existing architecture gates and full gate (test_results.md); catalog foundation/ownership tests; CLI mutation flag refusal; independent System Architect approval | VERIFIED_LOCAL |
| REQ-08 | Meaningful targeted invalid-input/read-only/no-op/failure coverage; CLI help/validation and existing live-consent behavior; applicable QUALITY.md gates | quality | 30 new tests plus existing CLI/update/installer regressions; no new mutating CLI | Exact targeted and full prepared-environment quality commands/results in test_results.md; all seven gates PASS, 2661 tests / 18 skipped | VERIFIED_LOCAL |
| REQ-09 | Operator docs, AC-to-contract/tests/evidence mapping, required evidence and independent requirements/architecture/test review; W09 owns cross-host live matrix and exact live evidence, missing/skipped/stale/inconclusive checks stay non-pass | documentation/quality | README; lifecycle.md; installation-manifest.md; six mandatory issue evidence files; tracked completion audit | Independent final completion audit PASS; no open requirements; W09 evidence fields documented | VERIFIED_LOCAL |

Applicability: deterministic state, catalog, CLI and architecture checks are
APPLICABLE_LOCAL. W02 introduces local persistence/inspection and no live mutation
entrypoint. Live install/upgrade/browser qualification belongs to W09 and is
NOT_APPLICABLE / LIVE_NOT_APPLICABLE here; no live success claimed.
External checks EXTERNAL_GATE_NOT_APPLICABLE to local implementation completion.
Current CLI help/argument validation and existing consent regressions are covered
by the local suite; a library adoption approval is not infrastructure live consent.
