# Issue 449 code-only consolidation amendment — v1.42

The user's publication instruction excludes live evidence for this consolidation. Requirement review accepted a narrowly scoped code-only amendment for the existing 86-file candidate and ordinary existing execution paths, with exact offline quality as publication authority and #449 INCOMPLETE. This supersedes the earlier refusal to publish any downstream work solely because S02 live fixture evidence is missing. It does not waive S02 for future scoped capabilities, admit any component candidate, prove ownership or mark S03–S09 done.

Requirement clarification: preserve and integrate all task-owned candidate files into PR #499, use logical one-slice commits and serialize overlapping composition responsibility. No new scoped Incus profile, internal Swagger mode or optional-stack ownership implementation is present in this candidate; no artificial dormant gate is needed. Existing consented product/setup flows remain the execution boundary. Future capabilities remain governed by S02 and their existing S03–S09 contracts. New or resumed live work is excluded from this amendment. Issue #449 and AC1–AC5/W10 remain INCOMPLETE pending their real evidence and independent completion audit.

The exact file groups below define write scopes and locks. Each candidate file appears once. The first slice also owns these six amendment documents. Root may split a whole-file mixed documentation change by hunks only if both resulting slices retain explicit ownership and no final change is lost. Preserve unrelated governance edits and the old dirty checkout until root verifies they are merged, superseded or explicitly retained. No new worktree, cleanup or discard is authorized by this document alone.

The final integrated exact-byte PC WSL quality result is aggregate integration evidence. Do not claim it proves every intermediate commit independently passed full quality or any live scenario. Before publication, run relevant focused checks and the mandatory final full gate from the approved PC WSL checkout after byte verification; use the final integration evidence plus reviewed dependency ordering for the logical commits. Required CI and SonarQube when configured still govern merge; failed or unavailable mandatory checks remain blockers. The publication is a code integration PR, not an issue-completion PR; do not close #449 by keyword or status.

Requirement mapping is implementation/test contribution only. C01 contributes prepared-product authority/recovery for R449-06/07/08/10/35; its live upgrade/recovery attribution remains open. C02 contributes exact pinned metadata and refusal/recovery policy for R449-04/08/10/23–26; candidate transitions stay non-executable before exact-source qualification. C03 contributes ordinary selection/observation/source-image propagation, foundation-only Apply and cancellation for R449-02/03/09/17/19/29–31/36–38; cross-host preservation and interrupted live behavior remain open. C04 preserves historical attribution, non-pass rows and draft AC5/W10 handoff for R449-01/15/18/21/22/27; it does not count a draft as acceptance.

Review and execution status has one authority: root-owned consolidation evidence. This static design records the requirement GO and closed scope only; it invents no final Architecture/Security/Quality review or execution result.

## S449-C01 — Bind prepared-product effective configuration source and recovery

Requirements contributed: R449-06, R449-07, R449-08, R449-10, R449-35. Dependencies: .

Exact files / locks:

- documentation/contracts/lifecycle.md
- documentation/user_guide/product-upgrades.md
- src/tiny_swarm_world/application/ports/lifecycle/product_upgrade.py
- src/tiny_swarm_world/application/services/product_upgrade.py
- src/tiny_swarm_world/domain/lifecycle/product_upgrade.py
- src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_admission.py
- src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_configuration_capture.py
- src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_configuration_source.py
- src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_configuration_validation.py
- src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_environment.py
- src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_installation.py
- src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_journal.py
- src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_migration.py
- src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_paths.py
- src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_runtime.py
- src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_verification.py
- src/tiny_swarm_world/infrastructure/composition_product.py
- tests/application/services/test_product_upgrade.py
- tests/infrastructure/adapters/lifecycle/test_product_configuration_source.py
- tests/infrastructure/adapters/lifecycle/test_product_upgrade.py
- tests/tools/test_secure_runtime_paths.py
- documentation/workflow/issues/issue-449/workflow.md
- documentation/workflow/issues/issue-449/context-pack.md
- documentation/workflow/issues/issue-449/context-pack.json
- documentation/workflow/workflow.index.md
- .codex/evidence/issue-449-code-consolidation-design.md
- .codex/evidence/issue-449-code-consolidation-distribution.md

Targeted modules: tests.application.services.test_product_upgrade, tests.infrastructure.adapters.lifecycle.test_product_configuration_source, tests.infrastructure.adapters.lifecycle.test_product_upgrade, tests.tools.test_secure_runtime_paths.


## S449-C02 — Retain immutable component candidates with fail-closed update admission

Requirements contributed: R449-04, R449-08, R449-10, R449-23, R449-24, R449-25, R449-26. Dependencies: S449-C01.

Exact files / locks:

- README.md
- documentation/process/skills/audit/skill-registry.json
- documentation/user_guide/component-updates.md
- infra/config/compose/swagger/docker-compose.yml
- src/tiny_swarm_world/application/services/component_execution.py
- src/tiny_swarm_world/application/services/component_updates.py
- src/tiny_swarm_world/domain/lifecycle/models.py
- src/tiny_swarm_world/domain/lifecycle/update_planning.py
- src/tiny_swarm_world/domain/update/classic_update.py
- src/tiny_swarm_world/infrastructure/adapters/lifecycle/catalog.py
- src/tiny_swarm_world/infrastructure/adapters/lifecycle/component_transitions.py
- src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py
- tests/application/services/test_component_updates.py
- tests/architecture/test_legacy_surface_documentation.py
- tests/domain/lifecycle/test_update_planning.py
- tests/domain/update/test_classic_update.py
- tests/infrastructure/adapters/lifecycle/test_catalog.py
- tests/infrastructure/adapters/lifecycle/test_native_component_transitions.py
- tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py
- tests/test_classic_update_cli.py

Targeted modules: tests.application.services.test_component_updates, tests.domain.lifecycle.test_update_planning, tests.infrastructure.adapters.lifecycle.test_catalog, tests.infrastructure.adapters.lifecycle.test_native_component_transitions, tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml, tests.test_classic_update_cli.


## S449-C03 — Repair existing selective setup runtime observations and cancellation

Requirements contributed: R449-02, R449-03, R449-09, R449-17, R449-19, R449-29, R449-30, R449-31, R449-36, R449-37, R449-38. Dependencies: S449-C02.

Exact files / locks:

- documentation/user_guide/selective-setup.md
- src/tiny_swarm_world/application/services/deployment/empty_apply.py
- src/tiny_swarm_world/application/services/deployment/ensure_portainer_endpoint.py
- src/tiny_swarm_world/application/services/deployment/workflows.py
- src/tiny_swarm_world/infrastructure/adapters/cli/dispatcher.py
- src/tiny_swarm_world/infrastructure/adapters/cli/selective_setup.py
- src/tiny_swarm_world/infrastructure/adapters/clients/lxc/command/args.py
- src/tiny_swarm_world/infrastructure/adapters/clients/lxc/command/diagnostics.py
- src/tiny_swarm_world/infrastructure/adapters/clients/lxc_container_docker_runtime.py
- src/tiny_swarm_world/infrastructure/adapters/clients/lxc_node_provider.py
- src/tiny_swarm_world/infrastructure/adapters/lifecycle/setup_observations.py
- src/tiny_swarm_world/infrastructure/adapters/lifecycle/setup_state.py
- src/tiny_swarm_world/infrastructure/composition.py
- src/tiny_swarm_world/infrastructure/composition_cli.py
- src/tiny_swarm_world/infrastructure/composition_deployment.py
- src/tiny_swarm_world/infrastructure/composition_deployment_selection.py
- src/tiny_swarm_world/infrastructure/composition_lifecycle.py
- src/tiny_swarm_world/infrastructure/composition_runtime.py
- src/tiny_swarm_world/infrastructure/composition_setup.py
- tests/application/services/deployment/test_deployment_workflows.py
- tests/application/services/deployment/test_ensure_portainer_endpoint.py
- tests/application/services/deployment/test_ensure_swarm_stack.py
- tests/e2e/classic/test_browser_evidence_paths.py
- tests/infrastructure/adapters/clients/lxc/swarm/test_swarm_stack_runtime.py
- tests/infrastructure/adapters/clients/test_lxc_container_docker_runtime.py
- tests/infrastructure/adapters/clients/test_lxc_node_provider.py
- tests/infrastructure/adapters/host/test_preflight_evidence_writer.py
- tests/infrastructure/adapters/lifecycle/test_setup_state.py
- tests/infrastructure/adapters/repositories/test_native_resource_budget.py
- tests/infrastructure/test_composition.py
- tests/infrastructure/test_selective_setup.py
- tests/infrastructure/test_setup_status_cancellation.py
- tests/test_incus_preparation.py
- tests/test_package_entrypoint.py
- tests/test_prepare_linux.py
- tests/test_selective_setup_cli.py
- tests/test_service_selection_cli.py
- tests/test_simple_installer.py
- tests/tools/test_r46_ports_policy.py

Targeted modules: tests.infrastructure.test_selective_setup, tests.infrastructure.test_setup_status_cancellation, tests.infrastructure.adapters.lifecycle.test_setup_state, tests.infrastructure.adapters.clients.test_lxc_node_provider, tests.infrastructure.adapters.clients.test_lxc_container_docker_runtime, tests.application.services.deployment.test_deployment_workflows.


## S449-C04 — Publish historical qualification ledger and incomplete AC5 traceability

Requirements contributed: R449-01, R449-15, R449-18, R449-21, R449-22, R449-27. Dependencies: S449-C03.

Exact files / locks:

- documentation/evidence/lcm-w09-ac5-traceability.md
- documentation/evidence/lcm-w09-blocker-refinement.md
- documentation/evidence/lcm-w09-q16-wsl-r52.md
- documentation/evidence/lcm-w09-q16-wsl-r54.md
- documentation/evidence/lcm-w09-qualification.md
- documentation/evidence/lcm-w09-transition-proposal.md

Targeted modules: .

Root-owned final audit/verification record for S449-C04: `.codex/evidence/issue-449-code-consolidation.md`. This additional file is explicitly within C04 affected_files/file_locks and is created/updated by root after actual verification; it is not part of the original86candidate and this authoring worker does not write its results.
