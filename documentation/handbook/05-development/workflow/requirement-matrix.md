# #440 remaining requirement crosswalk

Source: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/440; issue updated 2026-11-08T14:31:54Z.
Committed planning baseline c40d87ed81101dd582a112fe8b427d84372f36e2; verified repair is owner-retained and
absent from this docs-only branch until S440O-01. This is not parent acceptance.

## Parent acceptance crosswalk

| ID | Requirement | Accepted bounded baseline | Owning slices | Remaining evidence |
|---|---|---|---|---|
| P01 | Historical product release 0.4.0 → 0.5.0 | VERIFIED (historical bounded scope) | S440O-03, S440O-11, S440O-12, S440O-14 | Retain accepted Q14/Q15; only remaining current-candidate variants need qualification. |
| P02 | Single and selected-batch component updates | OPEN | S440O-05, S440O-10, S440O-12, S440O-14 | Current Swagger/Traefik targets are candidates; live convergence and persisted desired pins required. |
| P03 | Real Portainer upgrade and subsequent managed deployment | OPEN | S440O-02, S440O-04, S440O-06, S440O-07, S440O-08, S440O-09, S440O-12, S440O-14 | Native history retained; attributable WSL upgrade, cold backup and API-down recovery required. |
| P04 | Minimal and two distinct optional resolved selections | PARTIAL | S440O-02, S440O-06, S440O-07, S440O-08, S440O-11, S440O-12, S440O-14 | Reconcile historical cases; qualify missing exact-current-source selections. |
| P05 | Mandatory foundation and unsupported-combination refusal | PARTIAL | S440O-11, S440O-12, S440O-14 | W03 regression acceptance retained; remaining entrypoint/host cases required. |
| P06 | Optional-service add preserves identity, data and credentials | PARTIAL | S440O-11, S440O-12, S440O-14 | Exact WSL preservation and retention evidence remains incomplete. |
| P07 | Routes, access output and verification match persisted selection | PARTIAL | S440O-11, S440O-12, S440O-14 | Full-service browser checks are bounded evidence; omitted-service cases remain. |
| P08 | Every mutating entrypoint help, syntax, preview and consent | PARTIAL | S440O-01, S440O-03, S440O-04, S440O-05, S440O-09, S440O-10, S440O-11, S440O-12, S440O-14 | Complete public CLI/recovery/checkpoint matrix; no direct-adapter substitute. |
| P09 | No-op, interruption, partial failure and recovery | PARTIAL | S440O-01, S440O-02, S440O-03, S440O-04, S440O-06, S440O-07, S440O-09, S440O-10, S440O-11, S440O-12, S440O-14 | Historical product Q15 retained; component and attributable WSL Portainer gaps remain. |
| P10 | Explicit unsupported downgrade/migration rejection | PARTIAL | S440O-03, S440O-09, S440O-10, S440O-11, S440O-12, S440O-14 | No image rollback presented as data restore. |
| P11 | Visible configuration/runtime drift; no false success | PARTIAL | S440O-01, S440O-02, S440O-03, S440O-04, S440O-09, S440O-10, S440O-11, S440O-12, S440O-14 | Wrong/mixed tasks, dirty/moved/unknown sources and stale checkpoints require attributable results. |
| P12 | Exact cross-host versions, source, selection and redacted evidence | PARTIAL | S440O-01, S440O-02, S440O-03, S440O-04, S440O-05, S440O-06, S440O-07, S440O-08, S440O-09, S440O-10, S440O-11, S440O-12, S440O-13, S440O-14 | Native and WSL deployments remain separate; historical source bindings preserved. |
| P13 | Architecture, targeted tests and applicable quality/security gates | LOCAL repair PASS, owner-retained; EXTERNAL OPEN | S440O-01, S440O-02, S440O-03, S440O-04, S440O-05, S440O-08, S440O-12, S440O-13, S440O-14 | Historical local repair results apply only to recorded source; actual final PR CI/Sonar required in S440O-13 and independent audit S440O-14. |
| P14 | Verified operator documentation and truthful support limits | PARTIAL | S440O-05, S440O-10, S440O-12, S440O-13, S440O-14 | Candidate wording corrected in #518; complete example verification/reconciliation pending. |
| P15 | Independent final requirement/architecture/evidence review | OPEN | S440O-14 | No independent parent PASS; authoring role reviews do not close the Epic. |

## All 47 LCM obligations

| ID | Original requirement | Owner slices | Implementation / verification rule | State |
|---|---|---|---|---|
| LCM-01-01 | Inspect the installed TSW release/revision, effective configuration and managed runtime state. | S440O-01, S440O-03, S440O-05, S440O-11, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-01-02 | Resolve an explicit target release using a defined release source and supported upgrade matrix. | S440O-01, S440O-03, S440O-05, S440O-11, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-01-03 | Distinguish the TSW product version from upstream component versions and locally built image versions. | S440O-01, S440O-03, S440O-05, S440O-11, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-01-04 | Validate source and target state, dependency compatibility, host support and required resources before mutation. | S440O-01, S440O-03, S440O-05, S440O-11, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-01-05 | Upgrade product code/package and locked Python dependencies through the supported installation model. | S440O-01, S440O-03, S440O-05, S440O-11, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-01-06 | Apply versioned configuration/state migrations in an explicit order. | S440O-01, S440O-03, S440O-05, S440O-11, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-01-07 | Preserve local overrides, credential-source references, installation identity and persistent service data. | S440O-01, S440O-03, S440O-05, S440O-11, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-01-08 | Keep runtime credentials out of source-control operations, logs and upgrade evidence. | S440O-01, S440O-03, S440O-05, S440O-11, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-01-09 | Use a controlled checkout/package switch; do not overwrite an operator's uncommitted changes or perform an implicit reset. | S440O-01, S440O-03, S440O-05, S440O-11, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-01-10 | Define interruption handling, resumability and recovery for each supported transition. | S440O-01, S440O-03, S440O-05, S440O-11, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-01-11 | Record the actual resulting version and verify the complete installed service selection. | S440O-01, S440O-03, S440O-05, S440O-11, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-02-01 | Report installed and desired component versions, available supported targets and compatibility restrictions. | S440O-04, S440O-05, S440O-10, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-02-02 | Separate upstream versions, image tags and resolved image digests. | S440O-04, S440O-05, S440O-10, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-02-03 | Support one selected service and an explicitly selected batch of installed services. | S440O-04, S440O-05, S440O-10, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-02-04 | Resolve updates through an authoritative component catalog and profile support policy. | S440O-04, S440O-05, S440O-10, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-02-05 | Preview the exact changes, dependency order, restart/availability impact and required migrations. | S440O-04, S440O-05, S440O-10, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-02-06 | Reuse #297 for supported stack-service image transitions. | S440O-04, S440O-05, S440O-10, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-02-07 | Verify deployed task-image convergence and authenticated service behavior after an update. | S440O-04, S440O-05, S440O-10, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-02-08 | Update the persisted desired configuration after a successfully verified transition so later setup/deployment does not silently restore the old image. | S440O-04, S440O-05, S440O-10, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-02-09 | Represent no-op, unsupported, blocked, failed, partial and recovered outcomes explicitly. | S440O-04, S440O-05, S440O-10, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-02-10 | Do not update uninstalled or unselected services implicitly. | S440O-04, S440O-05, S440O-10, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-02-11 | Document stateful-service migration, backup and downgrade restrictions; an image rollback is not a persistent-data restore. | S440O-04, S440O-05, S440O-10, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-03-01 | Inspect the current Portainer version, deployment mode, persistent state and endpoint connectivity. | S440O-02, S440O-04, S440O-06, S440O-07, S440O-08, S440O-09, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-03-02 | Define and test at least one supported source-to-target upgrade. | S440O-02, S440O-04, S440O-06, S440O-07, S440O-08, S440O-09, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-03-03 | Back up the required Portainer state and document compatible recovery boundaries. | S440O-02, S440O-04, S440O-06, S440O-07, S440O-08, S440O-09, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-03-04 | Preserve administrative access, endpoint registration and managed stack ownership. | S440O-02, S440O-04, S440O-06, S440O-07, S440O-08, S440O-09, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-03-05 | Verify the Portainer API and authenticated access, then prove that a managed deployment/update still works. | S440O-02, S440O-04, S440O-06, S440O-07, S440O-08, S440O-09, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-03-06 | Recover without depending exclusively on an unavailable Portainer API. | S440O-02, S440O-04, S440O-06, S440O-07, S440O-08, S440O-09, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-03-07 | Keep Incus host-package upgrades separate from service-image updates; define their ownership and reject unsupported requests explicitly. | S440O-02, S440O-04, S440O-06, S440O-07, S440O-08, S440O-09, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-04-01 | Provide a canonical catalog of service IDs with versions, dependencies, resource requirements and profile support. | S440O-02, S440O-06, S440O-07, S440O-08, S440O-11, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-04-02 | Let operators select optional services through CLI/configuration and persist the resolved selection. | S440O-02, S440O-06, S440O-07, S440O-08, S440O-11, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-04-03 | Keep **Incus/LXC and Portainer mandatory for Classic**; attempts to disable either must fail before mutation with an actionable explanation. | S440O-02, S440O-06, S440O-07, S440O-08, S440O-11, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-04-04 | Treat Incus as a host/provider prerequisite and Portainer as a managed foundation; mandatory status does not imply that the installer already provisions the host Incus daemon. | S440O-02, S440O-06, S440O-07, S440O-08, S440O-11, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-04-05 | Resolve transitive dependencies deterministically. Show dependencies added to the requested selection and the reason for each. | S440O-02, S440O-06, S440O-07, S440O-08, S440O-11, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-04-06 | Document any additional unavoidable dependencies in the current implementation rather than claiming that every remaining service can already be omitted. | S440O-02, S440O-06, S440O-07, S440O-08, S440O-11, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-04-07 | Preflight only the resources, credentials, artifacts and capabilities needed for the resolved service set and mandatory foundations. | S440O-02, S440O-06, S440O-07, S440O-08, S440O-11, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-04-08 | Install, route, display and verify only the resolved services. | S440O-02, S440O-06, S440O-07, S440O-08, S440O-11, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-04-09 | Support a subsequent request to add optional services to an existing installation. | S440O-02, S440O-06, S440O-07, S440O-08, S440O-11, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-04-10 | Preview removals separately; deselection must not silently delete deployed services or persistent data. | S440O-02, S440O-06, S440O-07, S440O-08, S440O-11, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-04-11 | Use the same persisted selection for setup, reconcile, update and verification. | S440O-02, S440O-06, S440O-07, S440O-08, S440O-11, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-04-12 | Do not conflate service selection with runtime/orchestrator selection. | S440O-02, S440O-06, S440O-07, S440O-08, S440O-11, S440O-12, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-05-01 | Current-state inspection and supported-transition validation. | S440O-01, S440O-02, S440O-03, S440O-04, S440O-06, S440O-09, S440O-10, S440O-11, S440O-12, S440O-13, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-05-02 | A read-only preview with exact targets and planned changes. | S440O-01, S440O-02, S440O-03, S440O-04, S440O-06, S440O-09, S440O-10, S440O-11, S440O-12, S440O-13, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-05-03 | Explicit live-operation intent through existing consent boundaries. | S440O-01, S440O-02, S440O-03, S440O-04, S440O-06, S440O-09, S440O-10, S440O-11, S440O-12, S440O-13, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-05-04 | Ordered execution with bounded waits and per-stage results. | S440O-01, S440O-02, S440O-03, S440O-04, S440O-06, S440O-09, S440O-10, S440O-11, S440O-12, S440O-13, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-05-05 | Post-operation verification tied to the actual deployed state. | S440O-01, S440O-02, S440O-03, S440O-04, S440O-06, S440O-09, S440O-10, S440O-11, S440O-12, S440O-13, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |
| LCM-05-06 | A documented failure/recovery path and redacted evidence. | S440O-01, S440O-02, S440O-03, S440O-04, S440O-06, S440O-09, S440O-10, S440O-11, S440O-12, S440O-13, S440O-14 | Existing canonical implementation; precise public CLI, regression and required host cell reconciled at01/12/14 | REVALIDATE; live gaps OPEN |

## Previously inspected delivery maps — revalidate source at Slice01

### LCM-01 delivery map

- Public command: `product version / product upgrade`.
- Production path: cli/product_upgrade.run_product_upgrade → composition_product.build_product_upgrade → ProductUpgradeService.preview/run/_execute → PreparedProductInstallation/OfficialProductSource/JsonProductJournal/ClassicProductRuntime.
- Core source: `application/services/product_upgrade.py; infrastructure/adapters/lifecycle/product_{admission,source,environment,migration,installation,journal,runtime}.py` (brace notation is a source map, not a shell command).
- Relevant existing suites: `test_product_upgrade_cli; application.services.test_product_upgrade; infrastructure.adapters.lifecycle.test_product_admission/test_product_upgrade/test_product_layout/test_product_configuration_source`.
- Evidence level: source trace + deterministic CONTRACT/COMPONENT suites; separately bounded historical SYSTEM records.
- Remaining gap: Q14/Q15 historical accepted source/environment/migration/real interruption/recovery/no_op; v2→legacy reader-v1 target is intentionally refused, not a missing positive upgrade.

### LCM-02 delivery map

- Public command: `services updates / services update`.
- Production path: cli/component_updates.run_component_updates → ComponentUpdateService.discover/preview → domain plan_component_updates/_admission → ComponentUpdateExecution.run/_admit → ClassicComponentRuntime or ManagedComponentRuntime → #297/Portainer; JsonUpdateJournal and manifest desired-state commit.
- Core source: `application/services/component_updates.py; application/services/component_execution.py; domain/lifecycle/update_planning.py; infrastructure/adapters/lifecycle/{component_runtime,managed_component_runtime,component_transitions}.py` (brace notation is a source map, not a shell command).
- Relevant existing suites: `test_component_updates_cli; application.services.test_component_updates/test_component_execution; infrastructure.adapters.lifecycle.test_native_component_transitions`.
- Evidence level: source trace + deterministic CONTRACT/COMPONENT suites; separately bounded historical SYSTEM records.
- Remaining gap: Q07-Q11 historical bounded cases; exact-current-runner single/two-changing-member batch, desired pins/later setup, no_op, interruption/recovery and drift remain unqualified; production candidates are blocked.

### LCM-03 delivery map

- Public command: `services update --services portainer`.
- Production path: cli/component_updates._run_portainer → portainer_preview → consent → require_no_component_batch → build_portainer_upgrade → PortainerUpgradeService.run → ClassicPortainerUpgradeRuntime; JsonPortainerJournal.
- Core source: `application/services/portainer_upgrade.py; application/ports/lifecycle/portainer_upgrade.py; infrastructure/adapters/lifecycle/portainer_{runtime,backup,manager,api,journal}.py` (brace notation is a source map, not a shell command).
- Relevant existing suites: `test_portainer_upgrade_cli; application.services.test_portainer_upgrade; infrastructure.adapters.lifecycle.test_portainer_runtime`.
- Evidence level: source trace + deterministic CONTRACT/COMPONENT suites; separately bounded historical SYSTEM records.
- Remaining gap: Native bounded Q12/Q13 retained; WSL source/time/exit/process/checkpoint attribution and managed-stack/API-down recovery incomplete; cold backup and actual Portainer stack ownership required.

### LCM-04 delivery map

- Public command: `setup run --minimal/--services; services add/remove`.
- Production path: cli selective_setup/selection → ServiceSelectionService.preview → domain plan_selection → SetupSelectionState.admit → composition_profile.prepare_profile_state → existing setup/profile services → observations → complete_setup_selection_state/persist/manifest CAS.
- Core source: `application/services/service_selection.py; domain/lifecycle/selection.py; infrastructure/composition_selection.py; infrastructure/composition_profile.py; infrastructure/adapters/lifecycle/setup_state.py; infrastructure/adapters/cli/selective_setup.py` (brace notation is a source map, not a shell command).
- Relevant existing suites: `domain.lifecycle.test_selection; application.services.test_service_selection; test_selective_setup_cli; infrastructure.test_selective_setup/test_selective_followups; test_profile_route_preview; infrastructure.adapters.lifecycle.test_setup_state`.
- Evidence level: source trace + deterministic CONTRACT/COMPONENT suites; separately bounded historical SYSTEM records.
- Remaining gap: Historical Q02-Q06 selections/addition exist; exact-source minimal/two distinct resolved optional selections, WSL override/data/credential preservation, omitted-service outputs/routes and retention need reconciliation; runtime scoped capability asset is empty.

### LCM-05 delivery map

- Public command: `all mutating public entrypoints incl. --recover`.
- Production path: parser/dispatcher and existing consent → installation lease → operation-specific service/journal → owned adapter effects/readback → confirmed verification and persist; uncertain effects retain checkpoint.
- Core source: `infrastructure/adapters/cli/{parser,dispatcher,consent}.py; application/services/installation_profile.py; infrastructure/adapters/lifecycle/installation_operation_lock.py; operation-specific services/journals` (brace notation is a source map, not a shell command).
- Relevant existing suites: `test_package_entrypoint; test_selective_setup_cli; test_portainer_upgrade_cli; test_component_updates_cli; test_product_upgrade_cli; test_profile_recovery_cli; application.services.test_installation_profile`.
- Evidence level: source trace + deterministic CONTRACT/COMPONENT suites; separately bounded historical SYSTEM records.
- Remaining gap: Q16/Q17/Q18 and recovery variants remain partial. No exit/login/healthy old task alone establishes success; unsupported removal/downgrade/source/consent/drift cases remain explicit non-pass checks.

### Supported product-reader boundary

The only admitted product transition, official 0.4.0→0.5.0, explicitly supports
manifest reader v1. `domain/lifecycle/product_upgrade.py` rejects manifest-v2 or
scoped-profile source intent for that legacy target. Existing application tests
`test_legacy_target_keeps_v1_and_v2_source_cannot_reach_runtime` and
`test_forged_or_unknown_target_reader_blocks_before_runtime_or_stage` protect this.
Do not force-enable v2→0.5.0 to fill an acceptance cell. Retain P01/Q14/Q15 historical
acceptance; current-v2 variants require supported refusal/preservation evidence
unless a separately approved release/reader contract changes scope.


## Child acceptance crosswalk — original IDs preserved

All 45 child AC IDs are mapped below. Closed is issue state, not acceptance proof.
#449 is closed/not_planned; the remaining children are closed/completed. Newer
parent acceptance of bounded P01 governs over the dated W10 snapshot's OPEN label.

| Child / AC | Original acceptance text | Delivery and verification owner | Current evidence boundary |
|---|---|---|---|
| [#441](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/441) / LCM-W01-AC1 | An ADR identifies canonical commands, authoritative models and ownership without adding a second orchestration engine. | LCM-05 map + parent P01-P15 crosswalk | Accepted lifecycle ADR/inventory; historical W01 independent audit; full parent trace remains separately required |
| [#441](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/441) / LCM-W01-AC2 | Product releases, upstream versions, image tags and digests have distinct meanings. | LCM-05 map + parent P01-P15 crosswalk | Accepted lifecycle ADR/inventory; historical W01 independent audit; full parent trace remains separately required |
| [#441](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/441) / LCM-W01-AC3 | Service dependency inventory names Incus and Portainer as mandatory Classic foundations and explains all other current dependencies. | LCM-05 map + parent P01-P15 crosswalk | Accepted lifecycle ADR/inventory; historical W01 independent audit; full parent trace remains separately required |
| [#441](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/441) / LCM-W01-AC4 | Requirement IDs and planned unit/integration/live evidence cover all parent requirements. | LCM-05 map + parent P01-P15 crosswalk | Accepted lifecycle ADR/inventory; historical W01 independent audit; full parent trace remains separately required |
| [#442](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/442) / LCM-W02-AC1 | Schema validation and migration tests cover existing, unknown and corrupt state. | LCM-01 map + parent P01-P15 crosswalk | Existing manifest/catalog/schema/identity tests and W02 audit; current install identity and runtime facts remain separately bound |
| [#442](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/442) / LCM-W02-AC2 | Manifest reads are non-mutating; writes are atomic and preserve unrelated operator configuration. | LCM-01 map + parent P01-P15 crosswalk | Existing manifest/catalog/schema/identity tests and W02 audit; current install identity and runtime facts remain separately bound |
| [#442](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/442) / LCM-W02-AC3 | Installed/desired version drift is explicit, including resolved image identity. | LCM-01 map + parent P01-P15 crosswalk | Existing manifest/catalog/schema/identity tests and W02 audit; current install identity and runtime facts remain separately bound |
| [#442](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/442) / LCM-W02-AC4 | Existing installations can be adopted through a documented supported path or blocked with actionable diagnostics. | LCM-01 map + parent P01-P15 crosswalk | Existing manifest/catalog/schema/identity tests and W02 audit; current install identity and runtime facts remain separately bound |
| [#443](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/443) / LCM-W03-AC1 | Unknown services, cycles and attempted removal of mandatory foundations fail before mutation. | LCM-04 map + parent P01-P15 crosswalk | Existing planner tests and W03 independent audit; downstream actual setup not inferred |
| [#443](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/443) / LCM-W03-AC2 | Equivalent selections yield equivalent ordered plans. | LCM-04 map + parent P01-P15 crosswalk | Existing planner tests and W03 independent audit; downstream actual setup not inferred |
| [#443](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/443) / LCM-W03-AC3 | Dependency additions are explained and resource totals match the resolved set. | LCM-04 map + parent P01-P15 crosswalk | Existing planner tests and W03 independent audit; downstream actual setup not inferred |
| [#443](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/443) / LCM-W03-AC4 | Deselection never implicitly deletes deployed services or persistent data. | LCM-04 map + parent P01-P15 crosswalk | Existing planner tests and W03 independent audit; downstream actual setup not inferred |
| [#444](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/444) / LCM-W04-AC1 | A minimal selection and two distinct optional selections have meaningful integration coverage. | LCM-04 map + parent P01-P15 crosswalk | Selection/setup/followup/route suites; W09 Q02-Q06 bounded history, exact-source remaining cases open |
| [#444](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/444) / LCM-W04-AC2 | Unselected services are neither deployed nor reported as failed/installed. | LCM-04 map + parent P01-P15 crosswalk | Selection/setup/followup/route suites; W09 Q02-Q06 bounded history, exact-source remaining cases open |
| [#444](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/444) / LCM-W04-AC3 | Routes, access output, resource budgets and verification match the persisted selection. | LCM-04 map + parent P01-P15 crosswalk | Selection/setup/followup/route suites; W09 Q02-Q06 bounded history, exact-source remaining cases open |
| [#444](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/444) / LCM-W04-AC4 | Adding a service preserves existing identities, data and effective credentials; live proof is coordinated with W09. | LCM-04 map + parent P01-P15 crosswalk | Selection/setup/followup/route suites; W09 Q02-Q06 bounded history, exact-source remaining cases open |
| [#445](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/445) / LCM-W05-AC1 | Read-only discovery and preview cause no runtime mutation. | LCM-02 map + parent P01-P15 crosswalk | Existing discovery/planning tests and W05 audit; production candidate admission remains blocked |
| [#445](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/445) / LCM-W05-AC2 | Unsupported transitions and uninstalled service requests fail clearly. | LCM-02 map + parent P01-P15 crosswalk | Existing discovery/planning tests and W05 audit; production candidate admission remains blocked |
| [#445](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/445) / LCM-W05-AC3 | Batch plans are deterministic and expose image identities, compatibility and migration requirements. | LCM-02 map + parent P01-P15 crosswalk | Existing discovery/planning tests and W05 audit; production candidate admission remains blocked |
| [#445](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/445) / LCM-W05-AC4 | Upstream latest is not automatically advertised as a qualified supported target. | LCM-02 map + parent P01-P15 crosswalk | Existing discovery/planning tests and W05 audit; production candidate admission remains blocked |
| [#446](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/446) / LCM-W06-AC1 | Single-service and batch updates verify actual task-image convergence. | LCM-02 map + parent P01-P15 crosswalk | Component execution/native policy suites; exact-source Q07-Q11 system qualification open |
| [#446](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/446) / LCM-W06-AC2 | Partial failure cannot be reported as complete success; retry/resume behavior is tested. | LCM-02 map + parent P01-P15 crosswalk | Component execution/native policy suites; exact-source Q07-Q11 system qualification open |
| [#446](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/446) / LCM-W06-AC3 | Verified desired configuration survives subsequent setup/deployment. | LCM-02 map + parent P01-P15 crosswalk | Component execution/native policy suites; exact-source Q07-Q11 system qualification open |
| [#446](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/446) / LCM-W06-AC4 | Recovery preserves original transition metadata; repeated apply/recovery is a verified no-op. | LCM-02 map + parent P01-P15 crosswalk | Component execution/native policy suites; exact-source Q07-Q11 system qualification open |
| [#446](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/446) / LCM-W06-AC5 | Unrelated services, data and credentials remain intact; live qualification belongs to W09. | LCM-02 map + parent P01-P15 crosswalk | Component execution/native policy suites; exact-source Q07-Q11 system qualification open |
| [#447](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/447) / LCM-W07-AC1 | A supported upgrade and failure/recovery path have adapter and integration coverage. | LCM-03 map + parent P01-P15 crosswalk | Dedicated Portainer suites; native bounded history retained, WSL Q12/Q13 attribution/recovery open |
| [#447](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/447) / LCM-W07-AC2 | Missing backup/preconditions or unsupported migrations block before mutation. | LCM-03 map + parent P01-P15 crosswalk | Dedicated Portainer suites; native bounded history retained, WSL Q12/Q13 attribution/recovery open |
| [#447](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/447) / LCM-W07-AC3 | Portainer access, endpoints and ownership are verified after upgrade. | LCM-03 map + parent P01-P15 crosswalk | Dedicated Portainer suites; native bounded history retained, WSL Q12/Q13 attribution/recovery open |
| [#447](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/447) / LCM-W07-AC4 | A post-upgrade managed deployment/update proves gateway functionality; actual native/WSL evidence is retained under W09. | LCM-03 map + parent P01-P15 crosswalk | Dedicated Portainer suites; native bounded history retained, WSL Q12/Q13 attribution/recovery open |
| [#447](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/447) / LCM-W07-AC5 | No generic Incus host upgrade is introduced. | LCM-03 map + parent P01-P15 crosswalk | Dedicated Portainer suites; native bounded history retained, WSL Q12/Q13 attribution/recovery open |
| [#448](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/448) / LCM-W08-AC1 | At least one real product release transition is defined and executable, beyond a service-image change. | LCM-01 map + parent P01-P15 crosswalk | Product suites plus accepted historical Q14/Q15; reader-v2 refusal preserved |
| [#448](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/448) / LCM-W08-AC2 | Preview lists product/dependency/configuration/component changes separately. | LCM-01 map + parent P01-P15 crosswalk | Product suites plus accepted historical Q14/Q15; reader-v2 refusal preserved |
| [#448](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/448) / LCM-W08-AC3 | Dirty operator work and unrelated state are preserved or block safely. | LCM-01 map + parent P01-P15 crosswalk | Product suites plus accepted historical Q14/Q15; reader-v2 refusal preserved |
| [#448](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/448) / LCM-W08-AC4 | Interrupted upgrade resumes or recovers deterministically; unsupported downgrade fails before mutation. | LCM-01 map + parent P01-P15 crosswalk | Product suites plus accepted historical Q14/Q15; reader-v2 refusal preserved |
| [#448](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/448) / LCM-W08-AC5 | Resulting product version and selected runtime services are verified; live evidence is delivered with W09. | LCM-01 map + parent P01-P15 crosswalk | Product suites plus accepted historical Q14/Q15; reader-v2 refusal preserved |
| [#449](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/449) / LCM-W09-AC1 | Every claimed host/transition has actual current evidence with commands, versions, timestamps and outcomes. | LCM-05 map + parent P01-P15 crosswalk | W09 Q01-Q20 source/host ledger; aggregate system qualification incomplete, issue is not planned |
| [#449](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/449) / LCM-W09-AC2 | Data, service identities, endpoints and credentials are verified before/after operations. | LCM-05 map + parent P01-P15 crosswalk | W09 Q01-Q20 source/host ledger; aggregate system qualification incomplete, issue is not planned |
| [#449](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/449) / LCM-W09-AC3 | Required checks cannot be silently skipped or replaced by mocks/login-page reachability. | LCM-05 map + parent P01-P15 crosswalk | W09 Q01-Q20 source/host ledger; aggregate system qualification incomplete, issue is not planned |
| [#449](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/449) / LCM-W09-AC4 | Cleanup/restoration and unsupported combinations are explicit; failure remains non-pass. | LCM-05 map + parent P01-P15 crosswalk | W09 Q01-Q20 source/host ledger; aggregate system qualification incomplete, issue is not planned |
| [#449](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/449) / LCM-W09-AC5 | Results trace to every parent requirement and feed W10 completion review. | LCM-05 map + parent P01-P15 crosswalk | W09 Q01-Q20 source/host ledger; aggregate system qualification incomplete, issue is not planned |
| [#450](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/450) / LCM-W10-AC1 | Documented commands match implemented help and tested behavior. | LCM-05 map + parent P01-P15 crosswalk | W10/user guides/traceability; independent parent P15 PASS absent |
| [#450](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/450) / LCM-W10-AC2 | New-user journeys cover selective install, adding services and both update types. | LCM-05 map + parent P01-P15 crosswalk | W10/user guides/traceability; independent parent P15 PASS absent |
| [#450](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/450) / LCM-W10-AC3 | Portainer-specific recovery and image-rollback/data-restore differences are explicit. | LCM-05 map + parent P01-P15 crosswalk | W10/user guides/traceability; independent parent P15 PASS absent |
| [#450](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/450) / LCM-W10-AC4 | Final audit identifies exact supported scope, evidence and outstanding limits without invented success. | LCM-05 map + parent P01-P15 crosswalk | W10/user guides/traceability; independent parent P15 PASS absent |
| [#450](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/450) / LCM-W10-AC5 | Parent acceptance checklist is reconciled only from verified results. | LCM-05 map + parent P01-P15 crosswalk | W10/user guides/traceability; independent parent P15 PASS absent |

### Operator outcome and preservation

The parent promises inspect→preview→explicit apply→verify without recreating the
complete environment. Setup full-install/reset smoke does not establish that
journey. Component/Portainer/product journals and selection add preserve existing
manifest/installation/service/data/credential identities; exact before/after and
repeat/recovery evidence is required in the corresponding Q rows.

## Late additions and overarching obligations

| ID | Requirement/source | Owner and sequencing | Baseline state / gate |
|---|---|---|---|
| A440-01 | Parent final-acceptance order 1: exact Incus 6.0.5 listener fixture, independent support decision, recoverable WSL Portainer Server/Agent 2.45.0→2.45.1 with cold backup, managed update, no-op and API-down recovery | S440O-02, S440O-04, S440O-05, S440O-06, S440O-07, S440O-08, S440O-09, S440O-12, S440O-14 | OPEN; native fixture history is bounded, WSL attribution and capability admission remain separate |
| A440-02 | Parent order 2: real current-runner single/two-service changes, persistence, no-op, partial failure, recovery and drift; promotion follows evidence | S440O-05, S440O-10, S440O-12, S440O-14 | OPEN; production targets remain candidates at baseline |
| A440-03 | Parent order 3: retain P01 history, reconcile remaining selection/product/source cases, preserve WSL overrides/data/credentials and retention; run only actual gaps | S440O-01, S440O-03, S440O-11, S440O-12, S440O-14 | PARTIAL; exact-source and variant reconciliation required |
| A440-04 | Parent order 4: exact source/host/selection/commands/exits before/after evidence, applicable gates, examples, consistent admission wording and independent review | S440O-01, S440O-05, S440O-12, S440O-13, S440O-14 | PARTIAL; wording fixed, actual Sonar findings/final review remain |
| G440-01 | Preserve config, local overrides, credential references, installation/service identities and persistent data; no implicit reset, removal, data deletion or secret rotation | S440O-01, S440O-02, S440O-03, S440O-04, S440O-05, S440O-06, S440O-07, S440O-08, S440O-09, S440O-10, S440O-11, S440O-12, S440O-13, S440O-14 | Non-negotiable preservation and negative-case checks |
| G440-02 | Initial Classic only; #297 reuse, existing #313/#314/#318 ownership and contracts; no competing catalog/orchestration model or unrelated runtime expansion | S440O-01, S440O-02, S440O-03, S440O-04, S440O-05, S440O-08, S440O-12, S440O-14 | Architecture boundary and owner review |
| G440-03 | Product/package, upstream version, local image/tag and resolved digest remain distinct; real task/authenticated service state establishes success | S440O-09, S440O-10, S440O-11, S440O-12 | Exact source-to-target and observed-state evidence |
| G440-04 | Proposed one-token commands in the parent are not shipped promises; use accepted two-token CLI and preserve platform update compatibility | S440O-01, S440O-12 | Inspect actual parser/entrypoint/tests; no invented command claims |
| G440-05 | Scenario-specific live authorization, qualified recoverable targets, source-bound results; missing/stale/simulated evidence must never count as verified | S440O-05, S440O-06, S440O-07, S440O-08, S440O-09, S440O-10, S440O-11, S440O-12, S440O-13, S440O-14 | Separate consent, prerequisite, result and retention states |


## Evidence admission and remaining work

Original child-AC IDs and late/global obligations are preserved above; existing
local/child audits remain bounded. The historical Sonar baseline was not green;
no fresh Sonar success is asserted. Reconcile source facts in01/12 and actual
PR external results in13. Current recipe/recovery gaps are explicit02/03/04
implementation work, not supposedly completed evidence-only execution.

Each row needs exact code/CLI, test/check, source/host, actual scenario and
reviewer evidence before14. Local verification, LIVE_CONSENT_MISSING,
LIVE_PREREQUISITE_MISSING, LIVE_VERIFIED and external states remain separate.
No required negative case passes by skipping; no historical case loses its
accepted bounded scope or silently becomes current-candidate evidence.
