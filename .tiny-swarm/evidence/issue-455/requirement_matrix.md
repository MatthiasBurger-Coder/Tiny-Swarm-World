# Issue #455 requirement matrix

Baseline: main at `1a8f237c`. Branch: `feature/incus-preparation-20261004`.
Dependencies #453 and #454 are CLOSED and present. The checked workflow concerns
completed #355; this is independent issue implementation, not workflow execution.
No active matching slice or runtime locks were found; the #355 workflow is preserved.

| ID | Requirement | Type | Implementation evidence | Verification | Status |
|---|---|---|---|---|---|
| R455-01 | Explicit plan/apply and consent for daemon startup, ordinary-user access and first initialization | behavior | preparation service/port/Incus adapter and prepare_linux entrypoint | `test_plan_and_refusal_write_no_evidence_or_resources`, `test_boot_w03_ac1_daemon_group_restart_then_current_user_clean_resource_setup` | VERIFIED locally |
| R455-02 | Resolve storage/network/profile names from existing provider configuration; detect subnet/name/config collisions | behavior | configuration adapter, domain policy | `test_custom_resolved_resource_and_profile_names_used_without_defaults`, `test_subnet_collision_and_host_interface_name_collision_block` | VERIFIED locally |
| R455-03 | Preserve installations, unrelated instances/resources, existing pools/bridges and configuration | safety | create-only resource reconciliation | `test_boot_w03_ac2_compatible_resources_reused_ac4_rerun_preserves_configuration`, `test_drift_during_first_mutation_stops_later_approved_actions` | VERIFIED locally |
| R455-04 | New membership needs explicit shell restart or verified user handoff; verify without sudo | behavior | access adapter/service outcome | `test_boot_w03_ac1_daemon_group_restart_then_current_user_clean_resource_setup`, `test_incus_restart_exit_stops_install_handoff_from_prepare_linux` | VERIFIED locally |
| R455-05 | BOOT-W03-AC1: default clean host reaches Incus readiness without manual initialization/YAML edits | acceptance | prepare_linux integration and default resource creation | `test_boot_w03_ac1_default_initialization_and_ac3_user_verification`, `test_prepare_linux_actual_delegation_read_only_apply_and_ready_rerun` | VERIFIED locally |
| R455-06 | BOOT-W03-AC2: compatible resources reused; incompatible resources block with remediation | acceptance | resource policy/service | `test_boot_w03_ac2_incompatible_storage_network_and_profile_block_all_mutation`, settings-only profile reuse regression | VERIFIED locally |
| R455-07 | BOOT-W03-AC3: current-user version/info and every declared resource verified before handoff | acceptance | readiness adapter/service/entrypoint | `test_final_readiness_failure_never_reports_ready`, current-user/default-project/client-state isolation argv assertions | VERIFIED locally |
| R455-08 | BOOT-W03-AC4: rerun preserves unrelated nodes, identities and configuration | acceptance | create-only service/adapter | `test_boot_w03_ac2_compatible_resources_reused_ac4_rerun_preserves_configuration`, `test_configuration_drift_during_mutation_stops_later_actions` | VERIFIED locally |
| R455-09 | Bounded failures, consent, preservation, interruption/partial outcomes; read-only writes no host/config/state/evidence | safety | bounded process adapter, protected evidence, CLI | timeout/resume, cancellation, protected evidence failure/modes, read-only CLI, address lifetime/topology and target requalification regressions | VERIFIED locally |
| R455-10 | Thin Linux/WSL entrypoints, ports/services, existing provider/profile policy; fixed-profile semantics aligned with #440/#444 | architecture | existing composition and configuration owners | strict root/port/domain architecture tests; independent Architect PASS; canonical configuration and existing profile/launch policy review | VERIFIED locally |
| R455-11 | Acceptance-ID tests, redacted six-file evidence, docs, QUALITY.md and independent completion audit | process | issue evidence and bootstrap guide | local quality PASS (all seven gates, exit 0); independent perspectives and completion_audit.md PASS | VERIFIED locally |
| R455-12 | No live mutation from issue request; truthful live states; no #427/DNS/K3s/Podman/multi-host duplication | safety/scope | local-only implementation and review | source/argv inspection: no incus/init/delete/edit/reset command executed by development; live state explicitly LIVE_CONSENT_MISSING | VERIFIED locally |

Plan: extend the existing preparation boundary with an async Incus capability
service and a port. Read-only systemd checks must avoid socket activation. Missing
daemon/access stages receive their own exact consent and reinventory; group changes
return RESTART_REQUIRED, never root-only READY. First initialization uses explicit
create-only pool, bridge and declared profile operations, leaving the global default
profile and daemon settings untouched. Compatible existing storage drivers are reused.
Choose a deterministic nonoverlapping private subnet from observed routes/networks
for a new bridge, and recheck before every mutation. Load canonical configuration
and reuse existing profile requirements/safety checks through infrastructure.

Applicability: local contract/unit/adapter and installation orchestration
APPLICABLE_LOCAL; actual Incus installation APPLICABLE_LIVE / LIVE_CONSENT_MISSING.
Browser NOT_APPLICABLE. External gates EXTERNAL_GATE_NOT_APPLICABLE to this local
implementation; publication is outside this request.
