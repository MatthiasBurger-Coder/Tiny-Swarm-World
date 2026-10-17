# EPIC #452 — relevance audit of the ten follow-up slices

Review date: 2026-10-17. Reviewed product baseline: `53ce11fc96da9a9503313cc612eff9ac1af09378`. Workflow after planning correction: version 1.1.

Result: relevance review COMPLETE; EPIC implementation INCOMPLETE. The user explicitly allowed checking whether the ten steps remain relevant. This report fulfills that alternative; it does not mark any execution slice complete. No product code, ADR decision, admission policy or live host state was changed.

## What was actually reviewed

Read-only Requirement, Architecture, Python and Test reviewers inspected current source, accepted ADRs, original #452, closed children #453–#462, the W09 qualification rollup and W10 independent audit. Reviews used an isolated execution worktree on the verified workflow branch. S3 status/branch/scope/classification and S3D metadata/hash/dependency checks passed. All ten steps share contracts and stay sequential for writes; read-only reviews were independent. There was no parallel implementation or worker integration.

The original child work packages and the new completion slices are different lists. All original child issues are CLOSED, and much implementation exists. The W10 audit still says INCOMPLETE; W09's `remaining=[]` is scoped to its operator-amended existing-host campaign. Its `full_original_matrix_fresh_host_or_release_qualification=false` and explicit deferrals preserve the original parent gaps. No parent scope amendment was supplied.

## Ten-slice result

| Slice | Verdict | Already present | Concrete remaining work / verification |
|---|---|---|---|
| S452-01 | Relevant, narrow | Accepted preparation, source-proof and WSL-reconciliation decisions; complete child delivery inventory | Decide only archive-equivalent secret policy, dependency-light handoff and evidence-bound ordinary Windows admission. Do not replace accepted source proof or retroactively accept the whole W01 proposal. |
| S452-02 | Relevant product gap, narrow | Offline Gitless archive membership/hash/ownership verifier and adversarial tests | Installer downstream Git-ignore policy still rejects a Gitless source archive. Establish equivalent protected secret/evidence policy through existing ports; retain the source verifier. |
| S452-03 | Relevant product gap, narrow | Shell missing-Python bootstrap, source verification and guided Linux-native source placement | Windows handoff source probe invokes Python before that bootstrap. Fix dependency-light inventory/delegation. Automatic source copy is optional, not an original mandatory requirement. |
| S452-04 | Relevant verification first | Protected checkpoints, observed resume, fresh consent, Incus/resource/config preservation and many regression tests | Inventory coverage, add full-entrypoint failure/recovery and aggregate preservation cases only where absent; repair defects exposed by tests. No recovery rewrite is justified. |
| S452-05 | Relevant preparation, reuse | W09 scenario matrix and committed-source existing-host results | Extend remaining original scenario matrix, freeze an applicable candidate, identify recoverable clean targets and reviewed commands. No new blanket campaign solely for documentation SHA changes. |
| S452-06 | Relevant live evidence gap | Existing native Ubuntu26 prepare/install/rerun and scoped recovery evidence | Clean native path from trusted source; actual group transition, missing prerequisites, preservation and entrypoint recovery where not already proven at applicable source. |
| S452-07 | Relevant live evidence gap | Existing WSL Ubuntu26 install/rerun/restarts and scoped preservation | Clean Windows/WSL lifecycle, actual address change/bridge recovery and deferred capacity/preservation/fault scenarios. Browser-routing proof is required; Selenium specifically is not. |
| S452-08 | Relevant product gap | Bounded explicit candidate qualification mode | Ordinary Apply is unconditionally qualification-blocked. Add reviewed evidence-bound admission after applicable candidate proof; never simply remove the guard or infer support from local tests. |
| S452-09 | Relevant final integration proof | Historical exact-source walkthroughs for existing hosts | Witness final ordinary preparation/install commands after behavior/admission changes on both families. Rerun scenarios affected by the actual product delta; distinguish source/artifact identity from documentation-only publication changes. |
| S452-10 | Relevant final reconciliation | README, guides, W10 requirement audit already delivered | Update only affected instructions/support states, witness remaining walkthroughs and obtain independent original-EPIC completion audit. Do not rewrite all docs or infer parent completion from child closure. |

No complete follow-up slice is obsolete. Several are substantially narrower than a new implementation task. Three current code paths remain concrete blockers (S02, S03, S08); the rest are prerequisite decisions, coverage work, actual qualification or final documentation/audit.

## Source findings

- Archive blocker: `src/tiny_swarm_world/infrastructure/adapters/preflight/host_preflight_probe.py:200` invokes `git check-ignore`; failure/unavailable Git returns false. `src/tiny_swarm_world/application/services/platform/preflight_service.py:946` turns that result into failed mandatory ignore-policy checks. Installer metadata warnings are not this blocker.
- Existing archive proof: `tools/windows/preparation/linux-handoff.sh:47` and `:83` verify archive identity/membership/ownership and reject tampered/unsafe executable source; `tests/test_install_handoff.py:69` covers archive proof. Accepted Windows lifecycle ADR's extracted-release amendment already defines offline proof without Windows Git/Python.
- Missing-Python ordering: `tools/windows/preparation/linux-handoff.sh:20` unconditionally invokes `/usr/bin/python3`; `prepare_linux.sh:7` and `tools/ubuntu_python_prerequisites.sh:43` already own shell-first prerequisite bootstrap.
- Optional source copying: `documentation/contracts/bootstrap.md:155` requires an existing owned Linux-native checkout/release and explicitly says W04/W07 **may copy** after plan/approval. The parent forbids manual pip/venv, Incus YAML and undocumented networking; it does not impose a particular automatic copy mechanism.
- Ordinary Apply: `tools/windows/preparation/Application.ps1:41` sets `unqualified_target` without QualificationRun; `tools/windows/preparation/Policy.ps1:143` emits `qualified=false`. No ordinary-release admission mechanism is demonstrated.
- Delivered resilience: `src/tiny_swarm_world/infrastructure/adapters/bootstrap_state.py:20` binds identity and `:39` protects state paths; `tests/test_bootstrap_recovery.py:148` exercises observed resume/fresh consent. Missing live full-entrypoint recovery does not imply absent checkpoint implementation.
- Evidence authority: `documentation/evidence/issue-462-bootstrap-completion-audit.md`, `.tiny-swarm/evidence/issue-462/completion_audit.md`, and `.tiny-swarm/evidence/issue-461/combined_qualification_20261017.json`. GitHub #462 is closed although its retained independent audit says INCOMPLETE for original walkthrough acceptance; preserve that discrepancy rather than claiming all criteria verified or automatically reopening children.

## Removed scope inflation

The workflow now explicitly reuses accepted source proof and existing preparers. Automatic Linux source copy is optional; the supported source starting location must be clear. Existing checkpoints/preservation owners need coverage-first follow-up, not presumptive reimplementation. Browser routing must be proved, with Selenium separately classified. Existing reset-isolation evidence must be evaluated before requesting destructive testing; no new live reset or whole-OS/external-volume restoration is implied. Candidate Ubuntu24/26 rows retain truthful individual states; an unclaimed version is not silently treated as qualified.

## Verification

Product files were unchanged during this relevance-only planning correction.

1. `PYTHONPATH=src python3 -m unittest tests.test_prepare_linux tests.test_prepare_windows tests.test_ubuntu_bootstrap_integration tests.test_install_handoff tests.test_incus_preparation tests.test_bootstrap_recovery tests.test_network_preparation tests.test_network_preparation_compatibility tests.test_network_preparation_files tests.test_wsl_resource_projection tests.test_installer tests.test_simple_installer`: 270 tests in 141.696s; 267 passed, three failed, zero skips.
2. `PYTHONPATH=src python3 -m unittest tests.test_windows_source_proof tests.test_preparation_login_session tests.infrastructure.adapters.test_native_package_manager tests.domain.preflight.test_resources tests.domain.preflight.test_host_environment tests.domain.preflight.test_project_filesystem tests.infrastructure.adapters.preflight.test_windows_wsl_bridge_state`: 72 tests in 67.825s; all passed, zero skips.
3. Prepared-environment rerun: `PYTHONPATH=src /mnt/d/Projects/Tiny-Swarm-World/.venv/bin/python -m unittest tests.test_simple_installer.TestSimpleInstallerSecretBootstrap.test_main_passes_single_credential_contract_to_legacy_execution tests.test_simple_installer.TestSimpleInstallerSecretBootstrap.test_main_preserves_child_exit_and_only_prints_credentials_on_success tests.test_simple_installer.TestSimpleInstallerSecretBootstrap.test_main_reports_installer_error_without_exposing_values`: 3 tests in 8.105s, all passed unchanged. The absolute interpreter is local verification provenance, not a product configuration/example requirement.

The original 342-test run remains 339 passed / three failed; it is not rewritten as green and the whole suite was not rerun in the venv. The failing fixtures clear environment and use a temporary HOME while leaving a real dependency subprocess probe active. System Python user-site dependencies disappear with that HOME; the already prepared project venv provides them independently. The successful focused rerun needs no code, mock or dependency-install change. Independent Tester confirmed environment sensitivity; these three failures do not demonstrate a product defect.

Executable Windows PowerShell fixtures ran through the available Windows PowerShell executable; no tests were skipped in these runs. Runtime Python 3.14.4 does not establish Python3.12 qualification.

Documentation checks: `git diff --check` and `python3 tools/quality_gate.py verification-policy` passed; static checks passed for version1.1, all ten metadata blocks, concrete topology/locks, governing hashes, links and synchronized matrix copies. Full quality intentionally omitted for documentation-only changes; no full-gate, live, browser/Selenium or external SonarQube result is claimed. No real provider/package/network/bootstrap/install or host mutation command was run.

## Completion boundary

No original EPIC acceptance row was waived. S452-01 remains uncompleted until its decisions are independently accepted. Missing live consent/recoverable targets are execution prerequisites; they do not invalidate the relevance review. Leave #452 OPEN, and retain the workflow branch. This review does not authorize PR merge, branch deletion, live reset or host preparation. An independent reviewer checks this report and the narrowed plan before publication.

## Independent review

Senior Requirement Engineer and Senior System Architect: PASS for the relevance audit and narrowed planning correction; no acceptance criterion waived. Senior Python review confirms narrow source/probe gaps and optional copy. Senior Tester confirms concrete coverage limits and the environment-sensitive fixture rerun. EPIC completion remains INCOMPLETE.
