from __future__ import annotations

import argparse
import os
import stat
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from tiny_swarm_world import installer as legacy
from tiny_swarm_world.domain.configuration.internal_test_credentials import (
    validate_internal_test_consumers,
)
from tiny_swarm_world.application.services.credential_resolution import (
    CREDENTIAL_SOURCE_MAP_ENVIRONMENT,
    CredentialResolutionService,
)
from tiny_swarm_world.infrastructure.composition_operator_configuration import (
    load_operator_configuration,
)

DEFAULT_BOOTSTRAP_SECRET_FILE = "bootstrap-secrets.env"
TRAEFIK_GUI_USERS_HTPASSWD_ENVIRONMENT = legacy.TRAEFIK_GUI_USERS_HTPASSWD_ENVIRONMENT


class SimpleInstallerError(RuntimeError):
    pass


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = _parse_args(argv)
        env = _prepare_bootstrap_environment(os.environ, Path.cwd())
        options = legacy.InstallerOptions(
            service_profile=args.service_profile,
            confirm_reset=args.confirm_reset,
            non_interactive_live_approval=args.non_interactive_live_approval,
            headless=args.headless or env.get("TSW_INSTALL_HEADLESS") == "1",
            allow_wsl_windows_filesystem=args.allow_wsl_windows_filesystem,
        )
        exit_code = legacy.run(options, env=env, cwd=Path.cwd())
        if exit_code == 0:
            _print_operator_credentials(env)
        return exit_code
    except (legacy.InstallerError, SimpleInstallerError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tiny Swarm World RC1 installer with automatic secret bootstrap."
    )
    parser.add_argument(
        "--service-profile",
        default=os.environ.get("SERVICE_PROFILE", legacy.DEFAULT_SERVICE_PROFILE),
        choices=("default", "service-access"),
        help="Service profile passed to setup run.",
    )
    parser.add_argument(
        "--confirm-reset",
        action="store_true",
        help="Confirm the governed fresh-install reset without prompting.",
    )
    parser.add_argument(
        "--non-interactive-live-approval",
        action="store_true",
        help="Pass explicit non-interactive live approval to the CLI.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Disable terminal recorder/TUI presentation and capture command output directly.",
    )
    parser.add_argument(
        "--allow-wsl-windows-filesystem",
        action="store_true",
        help=(
            "Allow a confirmed Windows-mounted WSL2 repository and record the "
            "applied override in protected Linux-native evidence."
        ),
    )
    return parser.parse_args(argv)


def _prepare_bootstrap_environment(
    source_env: Mapping[str, str],
    cwd: Path,
) -> dict[str, str]:
    operator_file_values = _load_operator_install_file(source_env, cwd)
    override_values = _load_explicit_bootstrap_override(source_env, cwd)
    env = dict(operator_file_values)
    env.update(override_values)
    env.update(source_env)

    required_entries = legacy._required_installer_secret_entries(
        cwd / legacy.DEFAULT_SECRET_MANIFEST_PATH,
    )
    required_keys = tuple(entry.key for entry in required_entries)
    validate_internal_test_consumers(required_keys)
    resolution_keys = tuple(
        dict.fromkeys((*required_keys, TRAEFIK_GUI_USERS_HTPASSWD_ENVIRONMENT))
    )
    resolutions = CredentialResolutionService().resolve_bootstrap(
        resolution_keys,
        operator_values={key: env.get(key, "") for key in resolution_keys},
    )
    env.update(resolutions.values)
    _ensure_default_secret_names(env)
    # The standard path is catalog-backed and stateless. Explicit operator
    # values remain in `env`; CRED-03 defines their full precedence.
    env[CREDENTIAL_SOURCE_MAP_ENVIRONMENT] = resolutions.source_metadata()
    return env


def _load_operator_install_file(
    source_env: Mapping[str, str],
    cwd: Path,
) -> dict[str, str]:
    configured = source_env.get("TSW_INSTALL_ENV_FILE", "").strip()
    path = Path(configured or legacy.DEFAULT_SECRET_ENV_FILE).expanduser()
    if not path.is_absolute():
        path = cwd / path
    if not path.is_file():
        return {}
    _validate_secure_override_path(path)
    try:
        return load_operator_configuration(path)
    except (OSError, ValueError) as error:
        raise SimpleInstallerError(
            f"Operator credential source is invalid: {path.as_posix()}"
        ) from error


def _load_explicit_bootstrap_override(
    source_env: Mapping[str, str],
    cwd: Path,
) -> dict[str, str]:
    configured_file = source_env.get("TSW_BOOTSTRAP_SECRET_ENV_FILE", "").strip()
    configured_state_dir = source_env.get("TSW_BOOTSTRAP_STATE_DIR", "").strip()
    if configured_file and configured_state_dir:
        raise SimpleInstallerError(
            "TSW_BOOTSTRAP_SECRET_ENV_FILE and TSW_BOOTSTRAP_STATE_DIR are mutually exclusive."
        )
    if not configured_file and not configured_state_dir:
        return {}
    if configured_file:
        path = Path(configured_file).expanduser()
        if not path.is_absolute():
            path = cwd / path
    else:
        path = Path(configured_state_dir).expanduser() / DEFAULT_BOOTSTRAP_SECRET_FILE
        if not path.is_absolute():
            path = cwd / path
    if not path.is_file():
        raise SimpleInstallerError(
            f"Explicit bootstrap credential override is missing: {path.as_posix()}"
        )
    _validate_secure_override_path(path)
    try:
        return load_operator_configuration(path)
    except (OSError, ValueError) as error:
        raise SimpleInstallerError(
            f"Explicit bootstrap credential override is invalid: {path.as_posix()}"
        ) from error


def _validate_secure_override_path(path: Path) -> None:
    """Reject credential files whose POSIX ownership boundary is unverified."""
    resolved = path.resolve()
    if _is_windows_mounted_path(resolved):
        raise SimpleInstallerError(
            "Credential override files must be stored on a WSL-native Linux filesystem."
        )
    if path.is_symlink() or path.parent.is_symlink():
        raise SimpleInstallerError(
            "Credential override files must not use symbolic links."
        )
    try:
        file_stat = path.stat()
        parent_stat = path.parent.stat()
    except OSError as error:
        raise SimpleInstallerError(
            "Credential override file metadata could not be verified."
        ) from error
    if (
        not stat.S_ISREG(file_stat.st_mode)
        or file_stat.st_uid != os.geteuid()
        or file_stat.st_gid != os.getegid()
        or stat.S_IMODE(file_stat.st_mode) != 0o600
        or not stat.S_ISDIR(parent_stat.st_mode)
        or parent_stat.st_uid != os.geteuid()
        or parent_stat.st_gid != os.getegid()
        or stat.S_IMODE(parent_stat.st_mode) != 0o700
    ):
        raise SimpleInstallerError(
            "Credential override file must be a user-owned 0600 file in a user-owned 0700 directory."
        )


def _is_windows_mounted_path(path: Path) -> bool:
    parts = path.parts
    return (
        len(parts) >= 3
        and parts[0] == "/"
        and parts[1] == "mnt"
        and len(parts[2]) == 1
        and parts[2].isalpha()
    )


def _ensure_default_secret_names(env: dict[str, str]) -> None:
    env.setdefault("TSW_TRAEFIK_TLS_CERT_SECRET_NAME", "tsw_traefik_tls_cert")
    env.setdefault("TSW_TRAEFIK_TLS_KEY_SECRET_NAME", "tsw_traefik_tls_key")
    env.setdefault("TSW_TRAEFIK_GUI_USERS_SECRET_NAME", "tsw_traefik_gui_users")


def _print_operator_credentials(env: Mapping[str, str]) -> None:
    portainer_url = env.get("TSW_PORTAINER_URL", "http://localhost:10001")
    infisical_url = env.get("TSW_INFISICAL_URL", "http://localhost:17080")
    print("\nTiny Swarm World access targets")
    print("--------------------------------")
    print("Credential convention: INTERNAL/TEST ONLY catalog defaults")
    print("  Password values are intentionally not printed; see the credential catalog.")
    print("Portainer")
    print(f"  URL:      {portainer_url}")
    print("  User:     admin")
    print("  Password: catalog default or protected operator override")
    print("\nInfisical")
    print(f"  URL:      {infisical_url}")
    print(f"  User:     {env['TSW_INFISICAL_LOGIN_EMAIL']}")
    print("  Password: catalog default or protected operator override")
    print("See: documentation/arc42/08_configuration/internal-test-credential-catalog.md")
    print("\nAll other catalog-managed secrets are internal and are not printed.")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
