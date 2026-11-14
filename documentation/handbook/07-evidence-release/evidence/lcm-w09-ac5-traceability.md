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

## Current S440O-07 C7 native/WSL listener pair (2026-11-14)

The actual bounded C7 listener pair is **PASS**, independently accepted: native
qualification plus independent preservation preceded the WSL fixture and its
independent Linux preservation check. Both actual client/server pairs were
6.0.5 and bind C7 `c976ed379f73b6fc4f29226f1516d8e7c9f781cd` with identical
runner/test/qualification-workflow hashes. See the
[current C7 result, identity and artifact hashes](lcm-w09-qualification.md#current-c7-nativewsl-listener-pair--s440o-07-2026-11-14).

| Independent acceptance | SHA-256 |
|---|---|
| Native final | `6113e712db651c8da9155ef770ac8887368b8c98675bee453ee99c6b3647e5b0` |
| WSL final | `03fbc95f3858ee2c5f6c463c062f7b020d1cb3354c2779fb16172607174ac821` |
| Paired receipt | `0662db998bc718549545b38ec81c84bd1f3c18d1577eb8e9140e9c922332680e` |

Native evidence preserves four original UUID/semantic configurations/states,
eight prior snapshot full-metadata hashes and the retained owned ninth, nineteen
full service IDs/Specs and prior replica floors, captured Docker identity,
profiles/pool/listeners and admitted complete routes/boot. It does not establish
universal service health, node membership or a data-recovery scenario. WSL
postchecks preserve zero original instances, the default plus two pre-existing
profiles and owned cleanup. Windows/kernel preservation remains scoped to the
raw fixture's protected before/after route/rule/certificate evidence, not an
independent Windows/kernel query by the Linux postcheck.

| Parent row | C7 pair closes | Still open / separate |
|---|---|---|
| P03 | Listener qualification prerequisite on both hosts | Portainer endpoint/upgrade and remaining product acceptance |
| P04 | Same-runner listener prerequisite and bounded owned cleanup | Complete fresh/minimal/optional product-installation criteria |
| P09 | Listener/manager preservation prerequisite | Remaining interruption, product recovery and data-recovery variants |
| P12 | Exact paired source/runner/test/workflow/version evidence and independent listener acceptance | Complete per-scenario ledger, remaining traceability and owner acceptance |

This replaces the earlier current native-pending/WSL-only listener status; it
preserves earlier attempts in their original dispositions. Accepted C6/K6
evidence remains historical and is not retargeted to C7.
Qualification applies to C7, not the differing whole current public tree.
Product health is NOT_VERIFIED; no endpoint/product/data-recovery PASS, complete
parent checkbox or EPIC completion is claimed. K7 remains a separate S08
admission/write. This report's designated SSH/WSL documentation gate and
independent completion review are pending; S07 DONE is not yet claimed.

## S440O-07 bounded WSL listener result (2026-11-12)

Historical TA04 checkpoint: the accepted C7 pair above supersedes the
native-pending/WSL-only state here. The following status and gate statements
retain their original 2026-11-12 scope.

At TA04, the exact-C WSL standalone listener subcell was **PASS**, independently
accepted after the actual TA04 fixture: exit0, 155 commands all exit0,
nonce-bound HTTP, PID/effective-device/timing attribution, exact owned cleanup
and eight preservation equalities. The admitted default-profile baseline
includes its prepared root disk. Independent post-run readback found zero
instances/volumes, default-profile consumers0 and DNS-only TCP listeners.
See the [actual qualification result and artifact hashes](lcm-w09-qualification.md#current-wsl-listener-qualification--s440o-07--ta04-2026-11-12).

Root ran the actual unchanged C fixture serially in the qualified runtime clone;
this later isolated S07 worktree records evidence only. All1811source files/tree
matched C; standalone Python3.14.4 and actual Incus client/server6.0.5 are the
recorded versions. Raw ownership/command/result/GO/archive and the independent
audit remain private; no host identifiers are published here.

This advances only the WSL listener prerequisite within P03/P04/P09/P12. Those
parent rows, global S06/S07 and the EPIC remained OPEN/PARTIAL at that
checkpoint. Native pause/restore admission was then pending with no native
mutation recorded. The later C7 pair above supplies the two-host listener
evidence; K7 admission remains separate. Actual component/product/public-CLI cases follow
legitimate K and their full operator preservation/recovery evidence; the private
harness's identity rule is not imposed on the public CLI. No new source or
orchestrator is required merely to record this listener result.

Current designated-host documentation gate: PASS; checkpoint publication pending. Full
quality NOT_RUN_DOC_ONLY. No aggregate checkbox, product/recovery, external-gate
or parent PASS is claimed.

## S440O-06 admission progress (2026-11-12)

The following is the earlier complete-reset preparation checkpoint; current
bounded WSL listener evidence is recorded above.

TA440-20261112-02 has a resolved complete-reset target and an actual
`TSW_INSTALLATION_RESET_COMPLETE` preparation result at
2026-11-12T06:06:40.626653+00:00. Four TSW instances with data, two installation
profiles and the owned network/project were deleted. Independent after-checks
found zero instances, only an unused default profile, no default-pool volumes
and no application listeners; ports 80/443/10001/16080/16081 were free.
Provider, WSL distribution, source and evidence were retained. Exact resource
identities and the journal remain private; the
[qualification progress](lcm-w09-qualification.md#current-source-freeze-and-host-admission--s440o-06-2026-11-12)
records the operational-script digest and bounded result.

This completes clean-test preparation only. Old target-question, occupied-port
and preservation-only stops are historical for the explicitly deleted workload.
Root is preparing a source-identical root-owned runtime clone for direct fixture
admission without changing frozen C. Real supported product identity/coordinator,
update/preservation/recovery cases and independent acceptance remain required.

P03/P04/P09/P12 remain OPEN/PARTIAL; S440O-06 is
`ADMISSION_IN_PROGRESS / LIVE_PREREQUISITE_MISSING`, not DONE. The designated
SSH/WSL `git diff --check` passed for this exact changed snapshot. No fixture, K, product,
recovery, external-gate or parent completion follows from resetting the fixture.

## S440O-05 source handoff under review (2026-11-12)

The current common I05 changes address P02/P08/P12/P13/P14 source and evidence
preconditions; they do not complete those parent rows or W09/W10. Shipping
component candidates and the empty capability asset remain unchanged. The
[qualification source/budget contract](lcm-w09-qualification.md#new-campaign-source-contract--s440o-05-2026-11-12)
separates I05, the independently gated private C, the sole capability-only child
K, and later actual scenario admission. No C/K, image availability, new live run
or I05 gate pass is asserted here.

| Obligation | I05 verification design | Remaining evidence |
|---|---|---|
| P02 exact single/batch policy | Fixed candidate refusal/no state change for both hosts; separate exact private positives for Swagger/Traefik and retained images | Exact private policy delta review and both private-C quality gates; actual later component scenarios |
| P08/P12 source and fault provenance | Actual Git C-empty/K-populated fixtures reject merge, intervening/extra/mode/dirty/untracked/replacement and substituted-source cases; paired receipt/fixture/preparation identities bind C | Frozen clean C, actual paired host receipts, sole reviewed K and fresh scenario GO |
| P13 evidence authority | Common tests preserve historical readers, refusal/unavailable shapes and the clean equal-source context sentinel without treating it as runtime admission | Source-matched prescribed-host targeted/full results and independent owner acceptance |
| P14 repeatability | Existing argv, package/source/workflow/runner/test/policy/input hashes and numeric budget capture; exact K tree/parent checks | Immutable C/K and external private evidence, registry byte/platform proof, actual exercise and restoration |

Historical Q01–Q20 and product schema1 evidence below retain their original
sources and limits. Current schema2 negative/helper fixtures are not a historical
release-reader compatibility result; unavailable helpers remain unexecuted with
no product result. Local synthetic resources/Git histories do not qualify a live
host, change the admitted matrix, or close an open acceptance row.

## Trace obligations

Every parent acceptance row carries the shared W01 obligations: W01-REQ06
(trace acceptance to contract, tests and evidence), W01-REQ09 (distinguish
mock/local from live qualification), W01-REQ11 (retain missing, skipped, stale
and inconclusive outcomes as non-passes), and LCM-W01-AC4 (planned evidence for
parent requirements). W01-REQ10 applies whenever a live result is claimed.
Additional row-specific W01 identifiers are listed below. Scenario names are
defined by [lifecycle contract §7](../../01-product/contracts/lifecycle.md#7-acceptance-scenarios-and-evidence-ownership).

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
| P03 / PARENT-AC03 | Qualify a Portainer upgrade while retaining access/endpoints and proving managed deployment. | LCM-03-01–07 | LCM-W01-AC1/AC3 | LCM-S07 | C7 paired listener prerequisite PASS; complete parent row remains OPEN/PARTIAL. Native LIVE-4 is bounded verified. WSL Q12 candidate attribution is insufficient; Q13 remains partial; WSL LIVE-4 is open. R53 limits the accepted `RemoteAddress=Any` consent to the existing port 10001 route and records Q12 NO-GO pending product design. See [qualification Q12–Q13](lcm-w09-qualification.md), the [Q12 design proposal](lcm-w09-q12-design-proposal.md), and private `three-amigos-r53-q12-route-consent-gate.md`. |
| P04 / PARENT-AC04 | Verify fresh minimal Classic installation and two distinct optional selections. | LCM-04-01–08 | LCM-W01-AC3 | LCM-S08 | C7 paired listener prerequisite PASS; complete parent row remains OPEN/PARTIAL. Native minimal/optional selections and WSL Q02–Q04 are bounded evidence. WSL Q02 uses a synthetic source identity; protected raw Q03/Q04 records are not reproduced here. The bounded results do not imply every S08 clause. See [qualification Q02–Q04](lcm-w09-qualification.md). |
| P05 / PARENT-AC05 | Reject disabling mandatory foundations and unsupported combinations before mutation. | LCM-04-03–07, LCM-04-12; LCM-02-11 for downgrade/migration negatives | W01-REQ08; LCM-W01-AC3 | LCM-S08, LCM-S10 | Q17/Q18 contain representative refusal/control evidence. Optional-service removal and remaining unsupported combinations are open. See [qualification Q17–Q18](lcm-w09-qualification.md). |
| P06 / PARENT-AC06 | Add optional services while retaining existing identities, data and effective credentials. | LCM-01-07, LCM-03-04, LCM-04-08–09, LCM-04-11 | LCM-W01-AC3 | LCM-S09 | Native add/preservation and WSL Q05–Q06 are bounded for recorded fixtures. Direct WSL Q05/Q06 artifact attribution remains incomplete; disposed former WSL instances are not claimed preserved. See [qualification Q05–Q06](lcm-w09-qualification.md). |
| P07 / PARENT-AC07 | Ensure routes, access output and verification follow persisted selection and omit unselected services. | LCM-04-02, LCM-04-08, LCM-04-11–12 | LCM-W01-AC3 | LCM-S08–S09 | Q02–Q06 provide bounded results for recorded selections. Full cross-host selection/status applicability reconciliation remains open. See [qualification Q02–Q06](lcm-w09-qualification.md). |
| P08 / PARENT-AC08 | Test help, argument validation, preview and explicit consent for mutating entry points. | LCM-05-01–06 | W01-REQ08 | LCM-S11 | Q17/Q18 provide representative controls. Checkpoint-specific consent and broader entrypoint, input and failure variants remain open. See [qualification Q17–Q18](lcm-w09-qualification.md). |
| P09 / PARENT-AC09 | Verify no-op repeats, interruption, partial-batch failure and supported recovery. | LCM-01-10–11, LCM-02-07–10, LCM-05-04–06 | LCM-W01-AC4 | LCM-S03, LCM-S05–S06, LCM-S11 | C7 paired listener prerequisite PASS; complete parent row remains OPEN/PARTIAL. Q06/Q09–Q11/Q15/Q19 provide bounded evidence for some applicable cases; Q19 is setup retry evidence, and R35 is not a recovery pass. Remaining Q11/Q19 variants and Q16/Q18 cross-requirement cases remain open. Portainer API-loss recovery under LCM-03-06/AC03 is adjacent evidence, not a direct PARENT-AC09 scenario; WSL Q12/Q13 attribution remains partial. See [qualification](lcm-w09-qualification.md). |
| P10 / PARENT-AC10 | Reject unsupported stateful downgrade/data migration and distinguish image rollback from data restoration. | LCM-02-11; LCM-04-10 is adjacent deselection/removal-preview coverage, not the direct downgrade requirement | W01-REQ08; LCM-W01-AC4 | LCM-S10 | Q16–Q18 contain representative refusal evidence. Remaining downgrade, source and entrypoint combinations plus cross-host trace are open. No image rollback is represented as data restoration. See [qualification Q16–Q18](lcm-w09-qualification.md). |
| P11 / PARENT-AC11 | Make configuration/runtime drift visible and prevent false success. | LCM-01-01, LCM-01-04, LCM-01-11, LCM-02-07, LCM-02-09 | LCM-W01-AC2/AC4 | LCM-S01, LCM-S05, LCM-S11 | Dirty-checkout and unofficial-origin source refusals have bounded native preview evidence. WSL R52 adds dirty+official-origin and clean+unofficial-origin preview refusals. R54 is a relocated-checkout characterization consistent with source admission before a missing-adoption-manifest block, but omitted root-value/runner evidence prevents independent path binding. Moved-source semantics, other source variants, live runtime drift and old/mixed task cases remain open. See [R52](lcm-w09-q16-wsl-r52.md), [R54](lcm-w09-q16-wsl-r54.md), and private R54 review/archive. |
| P12 / PARENT-AC12 | Record exact native Linux/WSL2 versions, host/profile, selection, hashes, commands and redacted evidence. | W01-REQ10 is the direct version/host/profile/selection/command/evidence authority; LCM-01-01/03 and LCM-01-08 cover installed identity and redaction; LCM-05-06 covers failure/recovery evidence | W01-REQ10 | LCM-S12 | C7 paired listener prerequisite PASS; complete parent row remains OPEN/PARTIAL. Many rows have exact identity/hash evidence, but a complete cross-host per-scenario ledger, Q16–Q20 applicability, R35 attribution and cleanup mapping remain outstanding. R54 raw output and fixture are retained, but command-root binding is not independently proven. See [qualification Q01–Q20](lcm-w09-qualification.md) and the private R54 archive/review. |
| P13 / PARENT-AC13 | Pass architecture, targeted tests and applicable quality/security gates; separate live from mock/local evidence. | Cross-cutting W01 quality/evidence requirements | W01-REQ06/07/09/11; LCM-W01-AC1 | LCM-S12 | Current-candidate local quality and bounded independent reviews are recorded; aggregate live coverage is incomplete. External CI/SonarQube status is unavailable or unverified and is not claimed successful. See [qualification](lcm-w09-qualification.md). |
| P14 / PARENT-AC14 | Document lifecycle commands, foundations, backups and recovery. | LCM-01-10, LCM-02-11, LCM-03-03/06, LCM-04-10, LCM-05-06 | LCM-W01-AC1–AC4 | LCM-S12 | CLI syntax, supported-scope wording, backup and recovery boundaries have bounded documentation review. Parent checklist reconciliation and final W10 audit remain open. See [lifecycle contract](../../01-product/contracts/lifecycle.md), [component updates](../../03-user-guide/user_guide/component-updates.md), [product upgrades](../../03-user-guide/user_guide/product-upgrades.md), and [selective setup](../../03-user-guide/user_guide/selective-setup.md). |
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
| P01 | `modules/tsw_core/tests/application/services/test_product_upgrade.py`; `modules/tsw_core/tests/infrastructure/adapters/lifecycle/test_product_upgrade.py`; `modules/tsw_core/tests/domain/lifecycle/test_update_planning.py`; `modules/tsw_core/tests/test_product_upgrade_cli.py` | Local gate only; Q14–Q15 provide bounded live evidence and R35 remains a non-pass. |
| P02 | `modules/tsw_core/tests/domain/update/test_classic_update.py`; `modules/tsw_core/tests/application/services/test_component_updates.py`; `modules/tsw_core/tests/infrastructure/adapters/lifecycle/test_native_component_transitions.py`; `modules/tsw_core/tests/test_component_updates_cli.py` | Local gate only; WSL Q07–Q10 attribution and Q16 variants remain open. |
| P03 | `modules/tsw_core/tests/application/services/test_portainer_upgrade.py`; `modules/tsw_core/tests/infrastructure/adapters/lifecycle/test_portainer_runtime.py`; `modules/tsw_core/tests/infrastructure/adapters/clients/test_portainer_http_client.py`; `modules/tsw_core/tests/application/services/deployment/test_ensure_portainer_endpoint.py`; `modules/tsw_core/tests/application/services/deployment/test_deployment_workflows.py`; `modules/tsw_core/tests/test_portainer_upgrade_cli.py` | Local gate only; native LIVE-4 is bounded, while WSL Q12/Q13 and LIVE-4 remain partial/open. |
| P04 | `modules/tsw_core/tests/domain/lifecycle/test_selection.py`; `modules/tsw_core/tests/application/services/test_service_selection.py`; `modules/tsw_core/tests/infrastructure/test_selective_setup.py`; `modules/tsw_core/tests/test_selective_setup_cli.py`; `modules/tsw_core/tests/test_service_selection_cli.py` | Local gate only; WSL Q02 uses synthetic source and Q03/Q04 raw evidence is protected. |
| P05 | Selection suites in P04; `modules/tsw_core/tests/test_portainer_upgrade_cli.py`; `modules/tsw_core/tests/test_product_upgrade_cli.py`; `modules/tsw_core/tests/test_component_updates_cli.py` | Local gate only; live Q17/Q18 cover representative refusals. |
| P06 | Selection suites in P04; `modules/tsw_core/tests/application/services/deployment/test_ensure_service_stack.py`; `modules/tsw_core/tests/application/services/deployment/test_deployment_workflows.py` | Local gate only; direct WSL Q05/Q06 attribution remains incomplete. |
| P07 | `modules/tsw_core/tests/integration/test_portainer_routing.py`; `modules/tsw_core/tests/integration/test_nexus_routing.py`; `modules/tsw_core/tests/application/services/deployment/test_write_effective_access_model_evidence.py`; `modules/tsw_core/tests/infrastructure/adapters/lifecycle/test_setup_state.py` | Local routing/selection contracts do not prove complete cross-host route/status applicability. |
| P08 | `modules/tsw_core/tests/test_lifecycle_cli.py`; `modules/tsw_core/tests/test_component_updates_cli.py`; `modules/tsw_core/tests/test_portainer_upgrade_cli.py`; `modules/tsw_core/tests/test_product_upgrade_cli.py`; `modules/tsw_core/tests/test_selective_setup_cli.py`; `modules/tsw_core/tests/test_service_selection_cli.py` | Local gate only; live Q17/Q18 remain representative, with broader consent/input variants open. |
| P09 | `modules/tsw_core/tests/infrastructure/adapters/clients/lxc/services/test_recovery_semantics.py`; `modules/tsw_core/tests/application/services/test_product_upgrade.py`; `modules/tsw_core/tests/application/services/test_component_updates.py`; `modules/tsw_core/tests/application/services/deployment/test_deployment_workflows.py` | Local gate only; Q12/Q13 attribution is partial and R35 is not a recovery pass. |
| P10 | `modules/tsw_core/tests/domain/lifecycle/test_update_planning.py`; `modules/tsw_core/tests/application/services/test_product_upgrade.py`; `modules/tsw_core/tests/infrastructure/adapters/lifecycle/test_product_upgrade.py`; `modules/tsw_core/tests/application/services/test_component_updates.py` | Local refusal regressions do not close remaining source, entrypoint or cross-host cases. |
| P11 | `modules/tsw_core/tests/infrastructure/adapters/lifecycle/test_product_admission.py`; `modules/tsw_core/tests/infrastructure/adapters/lifecycle/test_product_upgrade.py`; `modules/tsw_core/tests/test_classic_update_cli.py` | Local gate only; live runtime drift and old/mixed task cases remain open. |
| P12 | `modules/tsw_core/tests/infrastructure/adapters/host/test_preflight_evidence_writer.py`; `modules/tsw_core/tests/tools/test_secure_runtime_paths.py` | Local provenance tests do not satisfy the complete per-scenario cross-host ledger. |
| P13 | `python3 tools/quality_gate.py quality`; `modules/tsw_core/tests/architecture/test_hexagonal_imports.py`; `modules/tsw_core/tests/architecture/test_explicit_composition_bindings.py` | Latest full gate is verified local evidence; it does not replace live qualification or unverified external CI/SonarQube checks. |
| P14 | `modules/tsw_core/tests/architecture/test_legacy_surface_documentation.py`; `modules/tsw_core/tests/e2e/classic/test_lifecycle_contract.py`; `modules/tsw_core/tests/tools/test_check_verification_policy_consistency.py` | Local docs/contracts checks do not replace parent checklist reconciliation or W10 review. |
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
