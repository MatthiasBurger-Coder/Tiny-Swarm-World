# ARCH-03.17 — Dead and duplicate orchestration path audit

Issue: #360. Parent architecture direction: #313. This audit uses repository
callers, configuration, tests, and accepted decisions as the removal boundary.

## Canonical owners and disposition

| Candidate | Reference and ownership evidence | Disposition |
| --- | --- | --- |
| `installer._configure_native_linux_command_group` | Its only product call was in `installer._run_prepared`; the helper returned without changing state. The actual group choice and `sg` command are in `installer._run_phase`. | Removed the dead call and helper. The phase runner remains the sole owner of explicit group switching. |
| Traefik secret-name defaults in both installers | `simple_installer._ensure_default_secret_names` and `installer._ensure_default_config_exports` inserted the same three names before successive lifecycle stages. `default_configuration_contract` declared the same defaults a third time. | One domain configuration map and `missing_traefik_secret_name_defaults` now own the values and selection rule. Simple bootstrap preserves explicit empty values; the lifecycle preparation replaces them, as before. The simple helper was removed. |
| `simple_installer.py` and `installer.py` | `install.sh` invokes `simple_installer.main`; it prepares bootstrap credentials and delegates to `installer.run`. The latter owns reset/setup order, phase results, and installation evidence. `prepare_linux.py`, installer tests, and live acceptance runners use installer utilities or the simple bootstrap. | Retained. These are distinct bootstrap and lifecycle responsibilities, with supported callers. The direct `installer.main` and `parse_args` path remains a compatibility entrypoint; its external use cannot be disproved by an internal reference search. |
| Bootstrap credential resolution in both installers (baseline V-006) | `simple_installer._prepare_bootstrap_environment` merges protected operator sources and resolves catalog values. `installer._resolve_internal_test_installer_values` re-evaluates source metadata against the prepared environment before the live lifecycle. Both call `CredentialResolutionService`, which owns the resolution policy. | Retained the two stage calls; they handle different inputs and share one policy owner. The secret-name default duplication within this boundary is consolidated above. Removing a resolution stage would change credential precedence and requires a separate contract change. |
| CLI and installer presentation (baseline V-008) | `__main__.py` renders individual workflow results; `installer.py` renders the higher-level reset/setup lifecycle, evidence location, and recovery guidance. | Retained distinct presentation scopes. The installer remains responsible for its combined lifecycle status, while CLI presentation remains at the workflow command boundary. A common renderer would blur these result contracts. |
| `composition.py` facade and `composition_runtime.py` wrappers | The CLI and tests use public `composition.build_*` symbols, including patch seams. Focused `composition_*` modules own capability assembly, while the facade synchronizes legacy patch points. Architecture and composition tests assert the surface. | Retained compatibility delegation. Removing it requires consumer and patch-seam migration. New builder ownership remains in focused composition modules. |
| Ansible and REST command runner placeholder adapters | The factory selects only `async`. The placeholder classes have no product construction sites; tests instantiate them directly. The accepted `command-runner-responsibility.adoc` decision explicitly requires direct instantiation to fail closed. The enum values also remain legacy configuration compatibility values. | Retained under the accepted decision. They cannot execute commands or report success. Deleting them would change that decision and direct import compatibility. |

The reference audit searched `src`, `tests`, `infra/config`, entry scripts,
`tools`, and documentation. Internal absence alone cannot prove that a public
Python import path has no external consumer, so this change removes the inert
private group helper and the private secret-name helper superseded by the
domain-owned selector.

## Supported behavior and checks

`install.sh` continues to use the simple installer. The CLI, installer
arguments, configuration keys, reset/setup ordering, live consent, and evidence
files are unchanged. The explicit `TSW_INSTALL_COMMAND_GROUP` input is still
interpreted only by `_run_phase`; the regression test checks the generated
command and unchanged environment with process execution mocked. Bootstrap to
lifecycle tests cover absent, custom, and empty Traefik secret names without
running live infrastructure.

Live installation, external services, and browser checks are outside this local
dead-code audit. Their result state is `LIVE_NOT_APPLICABLE`; the local quality
gate is the applicable verification authority.
