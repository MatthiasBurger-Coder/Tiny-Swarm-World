from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from tiny_swarm_world import installer as legacy
from tiny_swarm_world.domain.configuration.internal_test_credentials import (
    INTERNAL_TEST_LOGIN_EMAIL,
    INTERNAL_TEST_PROFILE,
    internal_test_credential,
    validate_internal_test_consumers,
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
            generate_secrets=False,
            secrets_mode=INTERNAL_TEST_PROFILE,
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
    override_values = _load_explicit_bootstrap_override(source_env, cwd)
    env = dict(override_values)
    env.update(source_env)

    required_entries = legacy._required_installer_secret_entries(
        cwd / legacy.DEFAULT_SECRET_MANIFEST_PATH,
        sources=legacy.INSTALLER_REQUIRED_SOURCES,
    )
    required_keys = tuple(entry.key for entry in required_entries)
    validate_internal_test_consumers(required_keys)
    for key in required_keys:
        env.setdefault(key, internal_test_credential(key))

    env.setdefault("TSW_INFISICAL_LOGIN_EMAIL", INTERNAL_TEST_LOGIN_EMAIL)
    env.setdefault(
        TRAEFIK_GUI_USERS_HTPASSWD_ENVIRONMENT,
        internal_test_credential(TRAEFIK_GUI_USERS_HTPASSWD_ENVIRONMENT),
    )
    _ensure_default_secret_names(env)
    # The standard internal-test path is catalog-backed and stateless. Explicit
    # operator values remain in `env`; CRED-03 defines their full precedence.
    env["TSW_SECRETS_MODE"] = INTERNAL_TEST_PROFILE
    return env


def _load_explicit_bootstrap_override(
    source_env: Mapping[str, str],
    cwd: Path,
) -> dict[str, str]:
    configured_file = source_env.get("TSW_BOOTSTRAP_SECRET_ENV_FILE", "").strip()
    configured_state_dir = source_env.get("TSW_BOOTSTRAP_STATE_DIR", "").strip()
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
    return legacy._load_export_file(path)


def _ensure_default_secret_names(env: dict[str, str]) -> None:
    env.setdefault("TSW_TRAEFIK_TLS_CERT_SECRET_NAME", "tsw_traefik_tls_cert")
    env.setdefault("TSW_TRAEFIK_TLS_KEY_SECRET_NAME", "tsw_traefik_tls_key")
    env.setdefault("TSW_TRAEFIK_GUI_USERS_SECRET_NAME", "tsw_traefik_gui_users")


def _print_operator_credentials(env: Mapping[str, str]) -> None:
    portainer_url = env.get("TSW_PORTAINER_URL", "http://localhost:10001")
    infisical_url = env.get("TSW_INFISICAL_URL", "http://localhost:17080")
    print("\nTiny Swarm World access credentials")
    print("-----------------------------------")
    print("Portainer")
    print(f"  URL:      {portainer_url}")
    print("  User:     admin")
    print(f"  Password: {env['TSW_PORTAINER_ADMIN_PASSWORD']}")
    print("\nInfisical")
    print(f"  URL:      {infisical_url}")
    print(f"  User:     {env['TSW_INFISICAL_LOGIN_EMAIL']}")
    print(f"  Password: {env['TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD']}")
    print("\nAll other generated secrets are internal and are not printed.")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
