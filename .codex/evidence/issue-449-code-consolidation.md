# Issue 449 code consolidation — v1.42

This is the root-owned execution record for S449-C01 through S449-C04. It records an implementation contribution, not issue completion. Issue #449, AC1–AC5, current-source native/WSL qualification and W10 acceptance remain INCOMPLETE. The user excluded new live evidence as a publication prerequisite for this consolidation; historical bounded observations retain their attribution and non-pass rows.

## Scope and ownership

The independent v1.42 code-publication amendment maps all 86 candidate paths once, plus six authoring documents and this record. The serial order is C01 effective product configuration source/recovery; C02 immutable candidate transitions and fail-closed updates; C03 selected setup/runtime observation and foundation-only Apply; C04 historical evidence and incomplete traceability. Final aggregate verification does not establish separate full-gate results for every intermediate commit.

Requirement, Architecture and Tester reviewers approved the concrete existing-path contribution. Security/Privacy approved publication after hostname redaction, and independently verified the production private-path validation precedes configuration preparation. The issue-completion auditor independently permits publication as incomplete after quality/CI/Sonar checks; it explicitly does not permit closing #449. DevOps/S3D returned EXECUTION_PLAN for the exact v1.42 locks and serial integration.

No installation-scoped Incus profile, internal-only Swagger mode or new optional-stack ownership/removal capability is implemented by this contribution. Their future prerequisites remain open. Existing consent and capacity guards remain authoritative; candidate component transitions remain non-executable before qualification.

## Integration

All 86 frozen candidate files were copied into the prescribed PR #499 branch from its committed b9ed689142f062568196cf5461736172aa6a0322 baseline. Every candidate source and destination hash matched before the three reviewed corrections: README historical qualification wording; matching README governing hash in the skill registry; generic native Linux test-host label in the historical qualification ledger. The other 83 candidate files stayed byte-identical. Six authoring files were preserved, with no unexpected paths. Existing canonical ADR owner-only permission text was retained; the original dirty checkout's stale variant was not substituted.

Original dirty files and unique refs are preserved outside the repository before cleanup. They are not evidence of current live qualification.

## Initial integration verification

Tests and quality were executed only via SSH on the approved PC host, inside Ubuntu WSL on an ext4 verification tree. The separate native host was not used for tests. This code-publication path executed no additional live installation, upgrade, capture or service mutation.

Candidate archive SHA-256: 5f0cef98d8a3e902f06df56a279a0d087f16834fc49b28659395f1a99f8418be.
Manifest SHA-256: d4deaa2552bbc182173a960bcaf8af352407adac508a6bcfd06f5ff52a8c2847.
All 2,654 archived file hashes were verified before commands ran.
Verification driver SHA-256: 07bc0825bcb0d65f40b7d76905c4887f092be0ccf0a641973d60dcc2cbe876ca.

Focused command: PYTHONPATH=src python -m unittest tests.infrastructure.adapters.lifecycle.test_product_configuration_source tests.infrastructure.adapters.lifecycle.test_native_component_transitions tests.infrastructure.test_selective_setup tests.tools.test_native_runtime_inventory tests.tools.test_native_lxd_snap_provenance.
Result: PASS, 174 tests in 2.853 seconds.

Full command: python tools/quality_gate.py quality.

Result: PASS, all seven mandatory gates (verification-policy, complexity, lint, arch-lint, arch-tests, typecheck and test). Architecture tests: 43 passed in 3.107 seconds. Full suite: 3,219 tests in 190.249 seconds, 36 skipped. Skipped cases are not reported as executed live/browser success.

Focused log SHA-256: 7d3ab55ff6be50ce696025fc331562264d5c4455f44d954ee2465ccbe1148a2c.
Full quality log SHA-256: 0c5093fbe0a4a1d27cfd67554b31967fcaf354358d88a806f5b9ba4e89981749.
The verification process exited 0. The local archive manifest was rechecked unchanged after the transfer. WSL git diff --check passed.

This documentation-only result record was added after the tested archive. Its facts are independently reviewed with the final diff; it introduces no product behavior or additional claimed test execution.

## Publication boundary

This record authorizes the reviewed serial commit sequence and guarded PR #499 publication after commit readiness. The final head must still pass configured GitHub CI, Python compatibility and SonarCloud checks before merge. Merge verification and branch/worktree cleanup are operator actions reported after execution; this pre-publication record does not invent those results. The user explicitly authorized cleanup to main after preserving older files and unique histories. No issue-closing keyword or DONE claim is authorized.

## Corrective checkpoint after the first SonarCloud analysis

The first final-head analysis for 73bae31dd20c96676e268b53c02778bd59a45d28 failed its security gate: Python S4790 identified the direct SHA-1 calculation used for Git blob identity. The other gate metrics passed (reliability A, maintainability A, coverage 86.6%, duplication 0%, reviewed hotspots 100%). The failed result was retained; no merge or gate override occurred.

Requirement, Architecture, Security and Tester review resolved the correction within C01's existing locks. Configuration identity is now computed by fixed read-only argv `git hash-object --no-filters --stdin` through the existing byte process-runner port. There is no shell or object write. Input retains the existing per-file byte bound; every object check shares one 30-second monotonic budget. Exit status, empty stderr, exact one-line lowercase Git OID and agreement with the tracked OID are validated. Errors remain sanitized refusals. SHA-256 configuration bindings and the existing path/mode/tree/admission guards remain intact. This records consistency with the trusted prepared Git checkout, not a new authenticity guarantee.

Only C01's configuration-source module and its nearest regression tests changed. Security and Tester independently reviewed frozen source SHA-256 45c6d7cee6c3a409b71f31912cf90dad367238c93c79616be133eacdc7208fef and test SHA-256 03db0b8890425a54216c69b88ff58e0873826e68e661af216b561ca91c53c247. Tests cover binary transport, fixed read-only arguments, output/error rejection, aggregate deadline and source-byte/mode drift.

Corrected archive SHA-256: f737f1c9b16468f9c8f155cb8399da316f0fcc192bd1a2df5cc278841dd5b3d7.
All 2,655 file hashes were verified on the approved PC Ubuntu WSL ext4 tree before execution.
The same focused unittest modules passed: 179 tests in 3.772 seconds.

The mandatory full quality gate passed all seven stages: 43 architecture tests in 3.155 seconds and 3,224 full-suite tests in 188.164 seconds, with 36 skipped. The verification process exited 0. The local file manifest was rechecked unchanged before this documentation-only update.

Corrected manifest SHA-256: a3c5b1dd1efbe989da7a9bebe2dd6ca8ff6a2c1b18037ffbe7ea69a0041fc601.
Focused log SHA-256: c6cffb93c5a82f791c54f088b6940085e6b32103504f8ebf1ef2406b8970d9c2.
Full quality log SHA-256: 8d574b8dc8bc8cfe1803ecdaab7956deead7eecca45d5687f00e49eca0523af6.

The source/test correction is a C01 checkpoint; this result update is a separate C04 checkpoint. Publication must run final-head CI and SonarCloud again and merge only when they pass. No new live qualification was performed, and #449 remains INCOMPLETE.
