"""Dependency-light installation wiring and outward compatibility exports."""

from collections.abc import Mapping, Sequence
from pathlib import Path
from tiny_swarm_world.application.ports.installation import InstallerError as InstallerError
from tiny_swarm_world.application.services.installation import InstallationService

from tiny_swarm_world.infrastructure.adapters.installation.host import (
    HostPreparationAdapter,
)

from tiny_swarm_world.infrastructure.adapters.installation.configuration import (
    ConfigurationPreparationAdapter,
)

from tiny_swarm_world.infrastructure.adapters.installation.credentials import (
    CredentialsPreparationAdapter,
)

from tiny_swarm_world.infrastructure.adapters.installation.process import (
    PhaseRunnerAdapter,
)

from tiny_swarm_world.infrastructure.adapters.installation.evidence import (
    InstallationEvidenceAdapter,
)

from tiny_swarm_world.infrastructure.adapters.installation.presentation import (
    InstallationPresentationAdapter,
)

from tiny_swarm_world.infrastructure.adapters.installation.presentation import (
    main as main,
)

from tiny_swarm_world.infrastructure.adapters.installation.configuration import (
    _configuration_snapshot as _configuration_snapshot,
    _copy_configuration_directory as _copy_configuration_directory,
    _copy_configuration_file as _copy_configuration_file,
    _copy_configuration_tree as _copy_configuration_tree,
    _open_configuration_source as _open_configuration_source,
    _paths_from_env as _paths_from_env,
    _validate_native_installation_read_only as _validate_native_installation_read_only,
    _validate_snapshot_storage as _validate_snapshot_storage,
)

from tiny_swarm_world.infrastructure.adapters.installation.credentials import (
    _ensure_default_config_exports as _ensure_default_config_exports,
    _normalize_infisical_login_email as _normalize_infisical_login_email,
    _normalized_email_value as _normalized_email_value,
    _require_operator_provisioned_traefik_gui_users as _require_operator_provisioned_traefik_gui_users,
    _required_installer_secret_entries as _required_installer_secret_entries,
    _resolve_internal_test_installer_values as _resolve_internal_test_installer_values,
)

from tiny_swarm_world.infrastructure.adapters.installation.evidence import (
    _append_context as _append_context,
    _collect_evidence_probe_snapshot as _collect_evidence_probe_snapshot,
    _git_revision_metadata as _git_revision_metadata,
    _installation_evidence_directory as _installation_evidence_directory,
    _probe_git_ignore as _probe_git_ignore,
    _read_text as _read_text,
    _safe_credential_source_metadata as _safe_credential_source_metadata,
    _utc_timestamp as _utc_timestamp,
    _windows_wsl_bridge_context as _windows_wsl_bridge_context,
    _write_context as _write_context,
    _write_text as _write_text,
)

from tiny_swarm_world.infrastructure.adapters.installation.host import (
    _require_repository as _require_repository,
    _windows_exposure_required as _windows_exposure_required,
    _windows_wsl_bridge_expected_ports as _windows_wsl_bridge_expected_ports,
    _windows_wsl_bridge_guard as _windows_wsl_bridge_guard,
    authorize_project_filesystem as authorize_project_filesystem,
    detect_host_runtime as detect_host_runtime,
)

from tiny_swarm_world.infrastructure.adapters.installation.presentation import (
    _FallbackInstallReporter as _FallbackInstallReporter,
    _confirm_reset as _confirm_reset,
    _default_install_reporter as _default_install_reporter,
    _format_ints as _format_ints,
    _has_setup_network_failure as _has_setup_network_failure,
    _live_approval as _live_approval,
    _phase_event as _phase_event,
    _print_install_completion_summary as _print_install_completion_summary,
    _print_install_plan as _print_install_plan,
    _print_reset_failure_guidance as _print_reset_failure_guidance,
    _print_setup_failure_guidance as _print_setup_failure_guidance,
    _print_tail as _print_tail,
    _print_windows_wsl_bridge_failure as _print_windows_wsl_bridge_failure,
    _relative_display_path as _relative_display_path,
    _render_fallback_install_event as _render_fallback_install_event,
    _reset_failure_guidance_lines as _reset_failure_guidance_lines,
    _reset_log_mentions as _reset_log_mentions,
    _safe_installer_line_value as _safe_installer_line_value,
    _safe_log_tail_lines as _safe_log_tail_lines,
    _setup_failure_guidance_lines as _setup_failure_guidance_lines,
    _starts_structured_log_value as _starts_structured_log_value,
    _structured_delimiter_delta as _structured_delimiter_delta,
    _suggested_checks_for_phase as _suggested_checks_for_phase,
    _windows_wsl_bridge_suggested_commands as _windows_wsl_bridge_suggested_commands,
    parse_args as parse_args,
)

from tiny_swarm_world.infrastructure.adapters.installation.process import (
    _filesystem_override_argument as _filesystem_override_argument,
    _installer_subprocess_timeout_seconds as _installer_subprocess_timeout_seconds,
    _python_imports_available as _python_imports_available,
    _run_installer_subprocess as _run_installer_subprocess,
    _run_optional_text as _run_optional_text,
    _run_phase as _run_phase,
    _run_text as _run_text,
    _workflow_command as _workflow_command,
    _write_test_venv_python as _write_test_venv_python,
    ensure_python_environment as ensure_python_environment,
)

from tiny_swarm_world.infrastructure.adapters.host import (
    ProjectFilesystemInspector as ProjectFilesystemInspector,
)


def build_installation_service() -> InstallationService:
    return InstallationService(
        HostPreparationAdapter(),
        ConfigurationPreparationAdapter(),
        CredentialsPreparationAdapter(),
        PhaseRunnerAdapter(),
        InstallationEvidenceAdapter(),
        InstallationPresentationAdapter(),
    )


def simple_install_main(argv: Sequence[str] | None = None) -> int:
    from tiny_swarm_world.infrastructure.adapters.installation.bootstrap import main

    return main(argv)


def prepare_bootstrap_environment(source_env: Mapping[str, str], cwd: Path) -> dict[str, str]:
    from tiny_swarm_world.infrastructure.adapters.installation.bootstrap import (
        _prepare_bootstrap_environment,
    )

    return _prepare_bootstrap_environment(source_env, cwd)
