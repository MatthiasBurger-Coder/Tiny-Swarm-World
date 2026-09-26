# ARCH-03.12 requirement matrix

Source: GitHub #355 goal, scope and five acceptance criteria; parent #313 and accepted ADR.
Every requirement is retained. Product evidence and final S07 quality are verified (2259 tests; 18 exclusions).
Independent completion audit PASS; all requirements are complete. See completion_audit.md in the issue evidence package.
Implementation paths below are relative to src/tiny_swarm_world; service paths
are relative to application/services.

| ID | Requirement from issue | Type | Files / slices | Implementation evidence | Test evidence | Status |
|---|---|---|---|---|---|---|
| R355-01 | Standardize expected lifecycle outcomes through explicit application-level results. | Functional / architecture | S355-02–05; exact paths in workflow metadata | application/ports/operation_result.py and the platform, artifacts, deployment and setup result producers; real provider-blocked wrappers. | CLI::test_operation_context_is_additive_in_json_for_every_result_family; COMP::test_real_blocked_producers_expose_results_through_setup | VERIFIED |
| R355-02 | Represent successful completion explicitly. | Functional | S355-02, 04, 05; exact paths in workflow metadata | OperationResult invariants; verified producer success and no-op handling. | C::test_valid_outcomes_and_origin_failures_serialize_independently; U::test_preview_noop_and_observed_recovery_are_distinct | VERIFIED |
| R355-03 | Represent failure explicitly. | Functional / resilience | S355-02–05; exact paths in workflow metadata | Typed OperationError and existing unexpected_failure fallback; workflow failed outcomes. | I::test_first_failed_attempt_is_uncertain_not_partial; P::test_guard_pass_and_first_timeout_do_not_claim_completed_work | VERIFIED |
| R355-04 | Represent partial completion where applicable. | Functional / resilience | S355-04, 05; exact paths in workflow metadata | shared/operation_results.py aggregation; requested completed/pending/uncertain ledgers and timeout snapshots. | I::test_blocked_after_confirmed_work_preserves_partial_and_stops_mutation; test_timeouts_retain_prior_confirmed_work; test_concurrent_aggregation_uses_plan_order | VERIFIED |
| R355-05 | Represent rolled-back outcome only after completed, verified restoration. | Functional / resilience | S355-02, 04; exact paths in workflow metadata | platform/workflow/update.py observed recovery; nested resolved history retained by setup. | U::test_recovery_requires_convergence_despite_rollback_status; I::test_restored_child_history_is_nested_and_parent_tracks_current_failure; CLI::test_operation_outcome_does_not_replace_legacy_cli_exit_status | VERIFIED |
| R355-06 | Failure details identify the operation. | Observability | S355-02–05; exact paths in workflow metadata | OperationFailure.operation; indexed allowlisted origin propagation and typed companion values. | I::test_artifact_failure_origin_survives_setup_and_stops_dependents; READ::test_indexed_adapter_and_direct_typed_gate_origins_reach_setup | VERIFIED |
| R355-07 | Failure details identify the component. | Observability | S355-02–05; exact paths in workflow metadata | OperationFailure.component; adapters, readiness gates and nested workflow aggregation. | INF::test_cli_failure_origin_reaches_setup_and_failed_run_does_not_poison_success; CONFIG::test_typed_configuration_failure_retains_finding_and_stops_setup | VERIFIED |
| R355-08 | Failure details identify a safe classified cause. | Security / observability | S355-02, 03, 06; exact paths in workflow metadata | Fixed cause/action catalogue; safe adapter translation, suppressed chains and redacted legacy diagnostics. | M::test_process_classification_does_not_expose_technical_payloads; test_gateway_and_http_hide_raw_cause_chains; I::test_untrusted_exception_attributes_are_redacted; ARCH::test_actual_operation_boundaries_contain_no_raw_failures | VERIFIED |
| R355-09 | Failure details express recoverability. | Resilience | S355-02, 03; exact paths in workflow metadata | Recoverability catalogue classifies current causes as unknown/nonrecoverable; no unproven safe-retry promise. | C::test_failures_use_only_catalogue_actions_and_constrained_identifiers; documented applicability below | VERIFIED |
| R355-10 | Failure details provide a recommended action. | UX / resilience | S355-02, 03, 06; exact paths in workflow metadata | OperationFailure.recommended_action validated against fixed catalogue; pure CLI rendering. | C::test_failures_use_only_catalogue_actions_and_constrained_identifiers; CLI::test_operation_renderer_is_pure_and_preserves_legacy_absence | VERIFIED |
| R355-11 | Translate expected infrastructure exceptions at adapter boundaries. | Architecture | S355-02, 03; exact paths in workflow metadata | Accepted lifecycle-failure-inventory.md reconciles reachable adapters, compatible port bridges and documented exclusions. | A::test_process_classifications_preserve_legacy_exception_contract; M::test_state_store_storage_and_parser_errors_are_safe_compatible_bridges; test_http_decoded_schema_errors_and_legacy_cli_timeout_are_classified; inventory source audit | VERIFIED |
| R355-12 | Expected infrastructure failures do not leak arbitrary exceptions through orchestration. | Architecture / resilience | S355-03–05; exact paths in workflow metadata | Typed boundary propagation; Infisical bootstrap plus evidence failure preserved; cancellation and existing programming-error behavior retained. | INF::test_bootstrap_and_evidence_failure_both_reach_deployment_safely; I::test_cancellation_propagates; CLI::test_setup_run_propagates_composition_lifecycle_failure | VERIFIED |
| R355-13 | Preserve existing CLI exit/error behavior unless a correction is explicitly justified. | Compatibility / UX | S355-01, 06; exact paths in workflow metadata | __main__ additive rendering/to_dict; unchanged status dispatch; installer/simple-installer exit behavior retained. | CLI::test_operation_outcome_does_not_replace_legacy_cli_exit_status; INST::test_run_phase_preserves_child_exits_timeout_and_interruption; SIMPLE::test_main_preserves_child_exit_and_only_prints_credentials_on_success | VERIFIED |
| R355-14 | Test representative failure mappings. | Quality | S355-02–07; exact paths in workflow metadata | Contract, adapter, four-family integration, CLI and architecture regressions; final integrated quality gate passed; 2259 tests, 18 exclusions in test_results.md. | All named suites and full gate; INF::test_successful_bootstrap_is_retained_when_final_evidence_write_fails; AUTH::test_authentication_exhaustion_is_expected_without_new_retries | VERIFIED |
| R355-15 | Preserve EPIC architecture, consent, destructive guards, redaction, deterministic evidence and Linux/WSL behavior. | Parent EPIC / governance | S355-01–07; exact paths in workflow metadata | Pure application-port contract, transitive ports import rule, safety/consent tests, architecture docs and independent reviews. | ARCH::test_operation_contract_depends_only_on_standard_library; test_operation_contract_import_probe_rejects_hidden_dependencies; test_operation_boundary_probe_detects_nested_exception_and_traceback; P consent/destructive guard regressions; arch-lint | VERIFIED |

## Test module keys

Each method above belongs to the listed module (subsequent names in a cell use
the same module until another key appears).

- C: `tests/application/ports/test_operation_result.py`
- U: `tests/application/services/platform/test_classic_update_workflow.py`
- P: `tests/application/services/platform/test_platform_workflows.py`
- I: `tests/application/services/setup/test_operation_result_integration.py`
- CLI: `tests/test_package_entrypoint.py`
- COMP: `tests/infrastructure/test_composition.py`
- READ: `tests/infrastructure/adapters/preflight/test_artifact_readiness.py`
- INF: `tests/application/services/deployment/test_infisical_silent_install.py`
- CONFIG: `tests/application/services/artifacts/test_static_contract_preflight.py`
- M: `tests/infrastructure/adapters/exceptions/test_operation_failure_mapping.py`
- A: `tests/infrastructure/adapters/command_runner/test_async_command_runner.py`
- ARCH: `tests/architecture/test_hexagonal_imports.py`
- INST: `tests/test_installer.py`
- SIMPLE: `tests/test_simple_installer.py`
- AUTH: `tests/application/services/deployment/test_ensure_infisical_secret_items.py`

## Applicability and retained boundaries

R355-09 expresses recoverability without inventing a recoverable diagnosis. Current
causes are unknown or nonrecoverable; RECOVERABLE is reserved for future evidenced
cases. No new retry or rollback policy is introduced.

Provider/domain and endpoint status collapse is preserved where the accepted
inventory permits it; detailed endpoint evidence survives. Unreachable optional
repositories, separate diagnostic commands and process-runner internals remain
explicit exclusions. These are reviewed applicability decisions, not omitted
requirements. Local quality is authoritative; live/browser are NOT_APPLICABLE,
and no external verification is claimed for branch checkpoints.
