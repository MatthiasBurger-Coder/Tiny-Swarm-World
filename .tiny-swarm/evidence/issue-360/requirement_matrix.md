# Issue #360 requirement matrix

Source: [ARCH-03.17] Remove Dead and Duplicate Orchestration Paths, parent #313.
Baseline: clean `main` checkout; work branch `issue-360-remove-dead-orchestration`.

| ID | Requirement from issue | Type | Files likely affected | Implementation evidence | Test evidence | Status |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-001 | Inventory obsolete installers, helpers, compatibility wrappers, unused adapters, and duplicated orchestration flows. | Scope | `src/tiny_swarm_world`, entry scripts, tests, docs | `documentation/arc42/05_analysis/arch-03-17-dead-path-audit.md` inventories candidates including V-006/V-008 and duplicate Traefik defaults | `rg` reference audit recorded there | VERIFIED |
| REQ-002 | Prove each removed path unused or superseded. | Acceptance | `installer.py`, `simple_installer.py` | Removed inert `_configure_native_linux_command_group`, superseded by `_run_phase`; removed `_ensure_default_secret_names`, superseded by domain `missing_traefik_secret_name_defaults` | `rg` caller audit, mocked phase test, and absent/custom/empty bootstrap handoff test pass | VERIFIED |
| REQ-003 | Establish canonical ownership before deleting duplicate code. | Acceptance | Installer, CLI, composition, adapters as applicable | Domain configuration contract owns Traefik defaults; audit names `_run_phase`, `installer.run`, `simple_installer.main`, `CredentialResolutionService`, and focused composition owners | Bootstrap handoff tests and architecture gate pass | VERIFIED |
| REQ-004 | Preserve supported CLI and configuration behavior. | Acceptance | Entry scripts, CLI, installer, configuration | Entrypoints remain; simple bootstrap preserves explicit empty names while installer preparation replaces them as before | Installer, simple installer, and domain configuration suites pass | VERIFIED |
| REQ-005 | Cover retained canonical paths with regression tests. | Acceptance | `tests/test_installer.py`, `tests/test_simple_installer.py` | Mocked phase test plus absent/custom/empty Traefik default tests across bootstrap and installer preparation | Focused tests, 109-test suite, and final full quality gate pass | VERIFIED |
| REQ-006 | Explicitly document remaining legacy compatibility code. | Acceptance | `documentation/arc42/05_analysis/arch-03-17-dead-path-audit.md` | Installer, composition, command runner compatibility table | Documentation reference audit and `git diff --check` pass | VERIFIED |
| REQ-007 | Preserve parent #313 safety and architecture constraints during removal. | Inherited constraint | Entrypoints, application, infrastructure, tests | No consent, reset, setup, or composition behavior changed | Targeted suite, architecture gates, and final full quality gate pass | VERIFIED |

Removal candidates were assessed against reference, runtime, and ownership evidence. The inventory distinguishes dead paths from supported compatibility contracts.
