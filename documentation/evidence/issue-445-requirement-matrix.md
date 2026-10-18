# Issue #445 — LCM-W05 requirement matrix

Scope: Classic on native Linux and WSL2; read-only discovery and update preview.
Baseline: `3200347b`; branch `feat/445-component-discovery-planning`.
The active workflow describes completed #355 and has no applicable executable
slice or locks for #445. This issue is the bounded implementation authority.

| ID | Requirement | Type | Architecture / likely files | Implementation evidence | Verification evidence | Status |
| --- | --- | --- | --- | --- | --- | --- |
| R445-01 / AC1 | Read-only discovery and preview, no state/runtime mutation; canonical help and input validation | Behavior | lifecycle service, CLI | CLI registry/parser/component_updates; ComponentUpdateService | ComponentUpdateCliTests read-only/help/argument tests; ComponentUpdateServiceTests.test_discover_and_preview_preserve_all_state | VERIFIED_LOCAL |
| R445-02 | Report installed (recorded observations), desired and supported available versions; separate upstream, build, tag and digest; disclose offline/unavailable metadata and drift | Behavior | lifecycle models/catalog/service | ComponentUpdateService.discover; VersionIdentity/ComponentState; native targets | ComponentUpdateServiceTests identity/unknown/native/offline cases | VERIFIED_LOCAL |
| R445-03 / AC2 | Reject unsupported transitions, downgrades, invalid/unknown and uninstalled selections clearly | Safety | domain planner, CLI | selected_services and _admission; CLI exit mapping | UpdatePlanningTests invalid/uninstalled/downgrade/compatibility cases; CLI failures | VERIFIED_LOCAL |
| R445-04 / AC3 | Single and explicit selected-batch plans, deterministic dependency order, exact identities, compatibility, availability impact, migrations, backups and recovery limits; no implicit updates | Behavior | domain planner, service, CLI | ComponentUpdateTarget/Transition, ComponentChange/ServiceUpdatePlan; plan_component_updates | UpdatePlanningTests batch_order_exact_images_migrations_and_no_implicit_updates; single_bundle_and_explicit_target | VERIFIED_LOCAL |
| R445-05 | Portainer uses dedicated upgrade path; generic Incus package upgrades rejected with host-owner guidance | Ownership | catalog and planner | ServiceDefinition.lifecycle_owner; _admission; discovery restrictions | UpdatePlanningTests.test_portainer_dedicated_and_incus_host_owner; CLI dedicated failure | VERIFIED_LOCAL |
| R445-06 / AC4 | Only authoritative catalog targets and explicit profile/host/source-target policy; never qualify upstream latest automatically | Policy | existing native catalog, target/transition contracts | ServiceDefinition.coherent_update_policy; native-baseline classification | UpdatePlanningTests policy/native baseline tests; ComponentUpdateServiceTests native catalog target tests | VERIFIED_LOCAL |
| R445-07 | No-op and failure paths; reuse existing #297 boundary without reopening execution; preserve hexagonal/#318 models and mandatory foundations; Classic only | Architecture | domain/application/CLI | Pure planner, existing manifest/catalog ports, early read-only CLI dispatch; legacy update untouched | No-op/drift regressions; legacy CLI/lifecycle/selection regression suite; independent architecture PASS | VERIFIED_LOCAL |
| R445-08 | Operator documentation, targeted tests, full local gate, evidence and independent completion review; separate W09/live/external states | Verification | docs/tests/evidence | README; lifecycle contract; component-updates guide; this evidence package and reviewable documentation mirror | Targeted suite PASS (40); full gate PASS (2747 tests, 18 opt-in skips); independent completion audit recorded separately | VERIFIED_LOCAL |

Local deterministic checks: APPLICABLE_LOCAL. Installation/browser/live:
NOT_APPLICABLE / LIVE_NOT_APPLICABLE (no runtime execution changed; W09 owns
host qualification). External checks: EXTERNAL_GATE_NOT_APPLICABLE for local
completion. No live infrastructure consent is supplied or required by this scope.
