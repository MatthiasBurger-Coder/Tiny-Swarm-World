"""Protected credential source loading for the operator bootstrap boundary."""

from __future__ import annotations
import os
import stat
from collections.abc import Mapping
from pathlib import Path
from tiny_swarm_world.application.ports import installation as values
from tiny_swarm_world.infrastructure.adapters.installation import credentials
from tiny_swarm_world.domain.configuration.internal_test_credentials import (
    validate_internal_test_consumers,
)
from tiny_swarm_world.application.services.credential_resolution import (
    CREDENTIAL_SOURCE_MAP_ENVIRONMENT,
    CredentialResolutionService,
)
from tiny_swarm_world.domain.configuration.configuration_contract import (
    missing_traefik_secret_name_defaults,
)
from tiny_swarm_world.infrastructure.composition_operator_configuration import (
    load_operator_configuration,
)

DEFAULT_BOOTSTRAP_SECRET_FILE = "bootstrap-secrets.env"
TRAEFIK_GUI_USERS_HTPASSWD_ENVIRONMENT = values.TRAEFIK_GUI_USERS_HTPASSWD_ENVIRONMENT


class SimpleInstallerError(RuntimeError):
    pass


def _prepare_bootstrap_environment(
    source_env: Mapping[str, str],
    cwd: Path,
) -> dict[str, str]:
    operator_file_values = _load_operator_install_file(source_env, cwd)
    override_values = _load_explicit_bootstrap_override(source_env, cwd)
    env = dict(operator_file_values)
    env.update(override_values)
    env.update(source_env)

    required_entries = credentials._required_installer_secret_entries(
        cwd / values.DEFAULT_SECRET_MANIFEST_PATH,
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
    env.update(missing_traefik_secret_name_defaults(env, empty_is_missing=False))
    # The standard path is catalog-backed and stateless. Explicit operator
    # values remain in `env`; CRED-03 defines their full precedence.
    env[CREDENTIAL_SOURCE_MAP_ENVIRONMENT] = resolutions.source_metadata()
    return env


def _load_operator_install_file(
    source_env: Mapping[str, str],
    cwd: Path,
) -> dict[str, str]:
    configured = source_env.get("TSW_INSTALL_ENV_FILE", "").strip()
    path = Path(configured or values.DEFAULT_SECRET_ENV_FILE).expanduser()
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
