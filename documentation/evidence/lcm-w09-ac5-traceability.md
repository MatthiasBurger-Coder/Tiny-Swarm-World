# LCM-W09 AC5 traceability handoff — draft

Status: **DRAFT FOR REVIEW — AC5 OPEN; no W10 owner acceptance recorded.**

Prepared 2026-10-26 from the repository lifecycle contract, the local #440
requirement matrix and the current #449 acceptance crosswalk. This document
makes the parent-to-evidence mapping reviewable. It does not update GitHub #440,
#449 or #450, reconcile the parent's native checklist, accept the W10 handoff,
or claim that a mapped scenario passed in full.

## Parent tracker snapshot

On 2026-10-26, GitHub #440 reported 8/10 work packages complete. Its linked
child issue pages showed the following statuses on that date:

| Work package | Issue | Status |
| --- | --- | --- |
| LCM-W01 | [#441](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/441) | Closed |
| LCM-W02 | [#442](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/442) | Closed |
| LCM-W03 | [#443](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/443) | Closed |
| LCM-W04 | [#444](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/444) | Closed |
| LCM-W05 | [#445](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/445) | Closed |
| LCM-W06 | [#446](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/446) | Closed |
| LCM-W07 | [#447](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/447) | Closed |
| LCM-W08 | [#448](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/448) | Closed |
| LCM-W09 | [#449](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/449) | Open |
| LCM-W10 | [#450](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/450) | Open |

This dated child snapshot supplements but does not reconcile or accept the
parent acceptance checklist. This W09 evidence does not complete the parent
requirements; the parent checklist and W10 owner acceptance remain open. The
external issues were not edited, and no parent acceptance item was marked
complete by this document.

## Trace obligations

Every parent acceptance row carries the shared W01 obligations: W01-REQ06
(trace acceptance to contract, tests and evidence), W01-REQ09 (distinguish
mock/local from live qualification), W01-REQ11 (retain missing, skipped, stale
and inconclusive outcomes as non-passes), and LCM-W01-AC4 (planned evidence for
parent requirements). W01-REQ10 applies whenever a live result is claimed.
Additional row-specific W01 identifiers are listed below. Scenario names are
defined by [lifecycle contract §7](../contracts/lifecycle.md#7-acceptance-scenarios-and-evidence-ownership).

The source requirement identifiers and parent acceptance numbers follow
[`issue-441-requirement-matrix.md`](issue-441-requirement-matrix.md). The
fuller local artifact crosswalk and hash indexes remain in the ignored,
workspace-private `.tiny-swarm/evidence/issue-449/` tree; they are not published
by this handoff. The documentation paths below are repository-local references;
in the current worktree these drafts are untracked and their hashes identify
local bytes, not committed files. A public summary is not a substitute for
protected raw live records.

## Parent acceptance mapping

| Parent row | Requirement summary | LCM sub-requirements | Additional W01 IDs | LCM-W01 scenarios | W09 evidence and current disposition |
|---|---|---|---|---|---|
| P01 / PARENT-AC01 | Upgrade a supported TSW release and distinguish product, dependencies, configuration and service images. | LCM-01-01–11 | LCM-W01-AC2 | LCM-S01–S03 | Q14–Q15 provide bounded native and WSL product transition/recovery/repeat evidence. WSL R35 remains a non-pass because its later completion state is not linked to a unique invocation or actor. See [qualification Q14–Q15](lcm-w09-qualification.md). |
| P02 / PARENT-AC02 | Discover installed/supported component versions and converge/persist single and selected-batch updates. | LCM-02-01–11 | LCM-W01-AC2 | LCM-S04–S06 | Q07–Q10 provide bounded Swagger/Traefik transition evidence. Exact WSL operation attribution and applicable Q16 source/task variants remain open. See [transition proposal](lcm-w09-transition-proposal.md) and [qualification Q07–Q10](lcm-w09-qualification.md). |
| P03 / PARENT-AC03 | Qualify a Portainer upgrade while retaining access/endpoints and proving managed deployment. | LCM-03-01–07 | LCM-W01-AC1/AC3 | LCM-S07 | Native LIVE-4 is bounded verified. WSL Q12 candidate attribution is insufficient; Q13 remains partial; WSL LIVE-4 is open. R53 limits the accepted `RemoteAddress=Any` consent to the existing port 10001 route and records Q12 NO-GO pending product design. See [qualification Q12–Q13](lcm-w09-qualification.md), the [Q12 design proposal](lcm-w09-q12-design-proposal.md), and private `three-amigos-r53-q12-route-consent-gate.md`. |
| P04 / PARENT-AC04 | Verify fresh minimal Classic installation and two distinct optional selections. | LCM-04-01–08 | LCM-W01-AC3 | LCM-S08 | Native minimal/optional selections and WSL Q02–Q04 are bounded evidence. WSL Q02 uses a synthetic source identity; protected raw Q03/Q04 records are not reproduced here. The bounded results do not imply every S08 clause. See [qualification Q02–Q04](lcm-w09-qualification.md). |
| P05 / PARENT-AC05 | Reject disabling mandatory foundations and unsupported combinations before mutation. | LCM-04-03–07, LCM-04-12; LCM-02-11 for downgrade/migration negatives | W01-REQ08; LCM-W01-AC3 | LCM-S08, LCM-S10 | Q17/Q18 contain representative refusal/control evidence. Optional-service removal and remaining unsupported combinations are open. See [qualification Q17–Q18](lcm-w09-qualification.md). |
| P06 / PARENT-AC06 | Add optional services while retaining existing identities, data and effective credentials. | LCM-01-07, LCM-03-04, LCM-04-08–09, LCM-04-11 | LCM-W01-AC3 | LCM-S09 | Native add/preservation and WSL Q05–Q06 are bounded for recorded fixtures. Direct WSL Q05/Q06 artifact attribution remains incomplete; disposed former WSL instances are not claimed preserved. See [qualification Q05–Q06](lcm-w09-qualification.md). |
| P07 / PARENT-AC07 | Ensure routes, access output and verification follow persisted selection and omit unselected services. | LCM-04-02, LCM-04-08, LCM-04-11–12 | LCM-W01-AC3 | LCM-S08–S09 | Q02–Q06 provide bounded results for recorded selections. Full cross-host selection/status applicability reconciliation remains open. See [qualification Q02–Q06](lcm-w09-qualification.md). |
| P08 / PARENT-AC08 | Test help, argument validation, preview and explicit consent for mutating entry points. | LCM-05-01–06 | W01-REQ08 | LCM-S11 | Q17/Q18 provide representative controls. Checkpoint-specific consent and broader entrypoint, input and failure variants remain open. See [qualification Q17–Q18](lcm-w09-qualification.md). |
| P09 / PARENT-AC09 | Verify no-op repeats, interruption, partial-batch failure and supported recovery. | LCM-01-10–11, LCM-02-07–10, LCM-05-04–06 | LCM-W01-AC4 | LCM-S03, LCM-S05–S06, LCM-S11 | Q06/Q09–Q11/Q15/Q19 provide bounded evidence for some applicable cases; Q19 is setup retry evidence, and R35 is not a recovery pass. Remaining Q11/Q19 variants and Q16/Q18 cross-requirement cases remain open. Portainer API-loss recovery under LCM-03-06/AC03 is adjacent evidence, not a direct PARENT-AC09 scenario; WSL Q12/Q13 attribution remains partial. See [qualification](lcm-w09-qualification.md). |
| P10 / PARENT-AC10 | Reject unsupported stateful downgrade/data migration and distinguish image rollback from data restoration. | LCM-02-11; LCM-04-10 is adjacent deselection/removal-preview coverage, not the direct downgrade requirement | W01-REQ08; LCM-W01-AC4 | LCM-S10 | Q16–Q18 contain representative refusal evidence. Remaining downgrade, source and entrypoint combinations plus cross-host trace are open. No image rollback is represented as data restoration. See [qualification Q16–Q18](lcm-w09-qualification.md). |
| P11 / PARENT-AC11 | Make configuration/runtime drift visible and prevent false success. | LCM-01-01, LCM-01-04, LCM-01-11, LCM-02-07, LCM-02-09 | LCM-W01-AC2/AC4 | LCM-S01, LCM-S05, LCM-S11 | Dirty-checkout and unofficial-origin source refusals have bounded native preview evidence. WSL R52 adds dirty+official-origin and clean+unofficial-origin preview refusals. R54 is a relocated-checkout characterization consistent with source admission before a missing-adoption-manifest block, but omitted root-value/runner evidence prevents independent path binding. Moved-source semantics, other source variants, live runtime drift and old/mixed task cases remain open. See [R52](lcm-w09-q16-wsl-r52.md), [R54](lcm-w09-q16-wsl-r54.md), and private R54 review/archive. |
| P12 / PARENT-AC12 | Record exact native Linux/WSL2 versions, host/profile, selection, hashes, commands and redacted evidence. | W01-REQ10 is the direct version/host/profile/selection/command/evidence authority; LCM-01-01/03 and LCM-01-08 cover installed identity and redaction; LCM-05-06 covers failure/recovery evidence | W01-REQ10 | LCM-S12 | Many rows have exact identity/hash evidence, but a complete cross-host per-scenario ledger, Q16–Q20 applicability, R35 attribution and cleanup mapping remain outstanding. R54 raw output and fixture are retained, but command-root binding is not independently proven. See [qualification Q01–Q20](lcm-w09-qualification.md) and the private R54 archive/review. |
| P13 / PARENT-AC13 | Pass architecture, targeted tests and applicable quality/security gates; separate live from mock/local evidence. | Cross-cutting W01 quality/evidence requirements | W01-REQ06/07/09/11; LCM-W01-AC1 | LCM-S12 | Current-candidate local quality and bounded independent reviews are recorded; aggregate live coverage is incomplete. External CI/SonarQube status is unavailable or unverified and is not claimed successful. See [qualification](lcm-w09-qualification.md). |
| P14 / PARENT-AC14 | Document lifecycle commands, foundations, backups and recovery. | LCM-01-10, LCM-02-11, LCM-03-03/06, LCM-04-10, LCM-05-06 | LCM-W01-AC1–AC4 | LCM-S12 | CLI syntax, supported-scope wording, backup and recovery boundaries have bounded documentation review. Parent checklist reconciliation and final W10 audit remain open. See [lifecycle contract](../contracts/lifecycle.md), [component updates](../user_guide/component-updates.md), [product upgrades](../user_guide/product-upgrades.md), and [selective setup](../user_guide/selective-setup.md). |
| P15 / PARENT-AC15 | Complete independent requirement, architecture and test/evidence review before closure. | Cross-cutting completion gate | W01-REQ06/11; LCM-W01-AC4 | LCM-S12 | Independent audit is INCOMPLETE. Q13, WSL LIVE-4, remaining Q16–Q18 variants, WSL R35 attribution, AC1–AC4, AC5 and W10 remain incomplete/open. Do not close #449 until all applicable requirements are verified and the independent auditor returns PASS. See [qualification](lcm-w09-qualification.md). |

## Regression and verification trace

These paths identify relevant regression suites in the current candidate. The
latest exact-worktree WSL gate included the repository test suite and passed
seven gates with 2,978 tests passed and 36 skipped on Python 3.12.15; its source
identity and log hash are recorded in the [qualification report](lcm-w09-qualification.md).
Per-suite test names/counts were not captured, so the mapping below is suite
ownership, not a claim that each case proves the corresponding live scenario.
Bounded live results and remaining gaps are listed in the parent table above.

| Parent row | Relevant regression suites | Verification limit |
|---|---|---|
| P01 | `tests/application/services/test_product_upgrade.py`; `tests/infrastructure/adapters/lifecycle/test_product_upgrade.py`; `tests/domain/lifecycle/test_update_planning.py`; `tests/test_product_upgrade_cli.py` | Local gate only; Q14–Q15 provide bounded live evidence and R35 remains a non-pass. |
| P02 | `tests/domain/update/test_classic_update.py`; `tests/application/services/test_component_updates.py`; `tests/infrastructure/adapters/lifecycle/test_native_component_transitions.py`; `tests/test_component_updates_cli.py` | Local gate only; WSL Q07–Q10 attribution and Q16 variants remain open. |
| P03 | `tests/application/services/test_portainer_upgrade.py`; `tests/infrastructure/adapters/lifecycle/test_portainer_runtime.py`; `tests/infrastructure/adapters/clients/test_portainer_http_client.py`; `tests/application/services/deployment/test_ensure_portainer_endpoint.py`; `tests/application/services/deployment/test_deployment_workflows.py`; `tests/test_portainer_upgrade_cli.py` | Local gate only; native LIVE-4 is bounded, while WSL Q12/Q13 and LIVE-4 remain partial/open. |
| P04 | `tests/domain/lifecycle/test_selection.py`; `tests/application/services/test_service_selection.py`; `tests/infrastructure/test_selective_setup.py`; `tests/test_selective_setup_cli.py`; `tests/test_service_selection_cli.py` | Local gate only; WSL Q02 uses synthetic source and Q03/Q04 raw evidence is protected. |
| P05 | Selection suites in P04; `tests/test_portainer_upgrade_cli.py`; `tests/test_product_upgrade_cli.py`; `tests/test_component_updates_cli.py` | Local gate only; live Q17/Q18 cover representative refusals. |
| P06 | Selection suites in P04; `tests/application/services/deployment/test_ensure_service_stack.py`; `tests/application/services/deployment/test_deployment_workflows.py` | Local gate only; direct WSL Q05/Q06 attribution remains incomplete. |
| P07 | `tests/integration/test_portainer_routing.py`; `tests/integration/test_nexus_routing.py`; `tests/application/services/deployment/test_write_effective_access_model_evidence.py`; `tests/infrastructure/adapters/lifecycle/test_setup_state.py` | Local routing/selection contracts do not prove complete cross-host route/status applicability. |
| P08 | `tests/test_lifecycle_cli.py`; `tests/test_component_updates_cli.py`; `tests/test_portainer_upgrade_cli.py`; `tests/test_product_upgrade_cli.py`; `tests/test_selective_setup_cli.py`; `tests/test_service_selection_cli.py` | Local gate only; live Q17/Q18 remain representative, with broader consent/input variants open. |
| P09 | `tests/infrastructure/adapters/clients/lxc/services/test_recovery_semantics.py`; `tests/application/services/test_product_upgrade.py`; `tests/application/services/test_component_updates.py`; `tests/application/services/deployment/test_deployment_workflows.py` | Local gate only; Q12/Q13 attribution is partial and R35 is not a recovery pass. |
| P10 | `tests/domain/lifecycle/test_update_planning.py`; `tests/application/services/test_product_upgrade.py`; `tests/infrastructure/adapters/lifecycle/test_product_upgrade.py`; `tests/application/services/test_component_updates.py` | Local refusal regressions do not close remaining source, entrypoint or cross-host cases. |
| P11 | `tests/infrastructure/adapters/lifecycle/test_product_admission.py`; `tests/infrastructure/adapters/lifecycle/test_product_upgrade.py`; `tests/test_classic_update_cli.py` | Local gate only; live runtime drift and old/mixed task cases remain open. |
| P12 | `tests/infrastructure/adapters/host/test_preflight_evidence_writer.py`; `tests/tools/test_secure_runtime_paths.py` | Local provenance tests do not satisfy the complete per-scenario cross-host ledger. |
| P13 | `python3 tools/quality_gate.py quality`; `tests/architecture/test_hexagonal_imports.py`; `tests/architecture/test_explicit_composition_bindings.py` | Latest full gate is verified local evidence; it does not replace live qualification or unverified external CI/SonarQube checks. |
| P14 | `tests/architecture/test_legacy_surface_documentation.py`; `tests/e2e/classic/test_lifecycle_contract.py`; `tests/tools/test_check_verification_policy_consistency.py` | Local docs/contracts checks do not replace parent checklist reconciliation or W10 review. |
| P15 | No test suite can replace the independent completion review. | Current completion audit is INCOMPLETE; independent PASS is still required. |

## Handoff disposition

This repository-path trace is prepared for review only. It does not make AC5 PASS:
the external parent checklist was not changed, W10 has no owner acceptance, and
protected/private raw evidence and operation attribution still have gaps. AC1–
AC4 also remain partial or open, so the overall issue remains **INCOMPLETE**.
The next handoff review must validate every parent row against its canonical
source, inspect protected indexes where authorized, reconcile checklist states,
and record owner acceptance or rejection. A fresh independent issue-completion
audit is required before any closure claim.
