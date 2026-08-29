from __future__ import annotations

import argparse
import base64
import hashlib
import os
import secrets
import shlex
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from tiny_swarm_world import installer as legacy

DEFAULT_BOOTSTRAP_STATE_DIR = "tiny-swarm-world"
DEFAULT_BOOTSTRAP_SECRET_FILE = "bootstrap-secrets.env"
DEFAULT_INFISICAL_RUNTIME_FILE = "infisical-bootstrap.env"
TRAEFIK_GUI_USERS_HTPASSWD_ENVIRONMENT = "TSW_TRAEFIK_GUI_USERS_HTPASSWD"


class SimpleInstallerError(RuntimeError):
    pass


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = _parse_args(argv)
        env = _prepare_bootstrap_environment(os.environ, Path.cwd())
        options = legacy.InstallerOptions(
            service_profile=args.service_profile,
            generate_secrets=True,
            secrets_mode="generated",
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
    env = dict(source_env)
    state_dir = _state_dir(env)
    secret_file = _resolve_override(
        env.get("TSW_BOOTSTRAP_SECRET_ENV_FILE"),
        state_dir / DEFAULT_BOOTSTRAP_SECRET_FILE,
        cwd,
    )
    infisical_runtime_file = _resolve_override(
        env.get("TSW_INFISICAL_SECRET_ENV_FILE"),
        state_dir / DEFAULT_INFISICAL_RUNTIME_FILE,
        cwd,
    )

    _ensure_linux_private_parent(state_dir)
    existing = legacy._load_export_file(secret_file)
    env.update(existing)

    required_entries = legacy._required_installer_secret_entries(
        cwd / legacy.DEFAULT_SECRET_MANIFEST_PATH,
        sources=legacy.INSTALLER_REQUIRED_SOURCES,
    )
    missing = [entry for entry in required_entries if not env.get(entry.key)]
    generated = legacy._generated_secret_values(missing, env) if missing else {}
    env.update(generated)

    env.setdefault("TSW_INFISICAL_LOGIN_EMAIL", legacy.DEFAULT_INFISICAL_LOGIN_EMAIL)
    _ensure_traefik_dashboard_secret(env)
    _ensure_default_secret_names(env)

    persisted = {
        entry.key: env[entry.key]
        for entry in required_entries
        if env.get(entry.key)
    }
    persisted[TRAEFIK_GUI_USERS_HTPASSWD_ENVIRONMENT] = env[
        TRAEFIK_GUI_USERS_HTPASSWD_ENVIRONMENT
    ]
    for name in (
        "TSW_TRAEFIK_TLS_CERT_SECRET_NAME",
        "TSW_TRAEFIK_TLS_KEY_SECRET_NAME",
        "TSW_TRAEFIK_GUI_USERS_SECRET_NAME",
    ):
        persisted[name] = env[name]
    _write_private_exports(secret_file, persisted)

    # The old installer is retained only as an execution compatibility layer.
    # All persistent secret inputs now point at one canonical Linux-native store.
    env["TSW_INSTALL_ENV_FILE"] = secret_file.as_posix()
    env["TSW_GENERATED_SECRET_ENV_FILE"] = secret_file.as_posix()
    env["TSW_FIXED_SECRET_ENV_FILE"] = secret_file.as_posix()
    env["TSW_INFISICAL_SECRET_ENV_FILE"] = infisical_runtime_file.as_posix()
    env["TSW_SECRETS_MODE"] = "generated"
    return env


def _state_dir(env: Mapping[str, str]) -> Path:
    configured = env.get("TSW_BOOTSTRAP_STATE_DIR", "").strip()
    if configured:
        return Path(configured).expanduser()
    xdg_state_home = env.get("XDG_STATE_HOME", "").strip()
    root = Path(xdg_state_home).expanduser() if xdg_state_home else Path.home() / ".local" / "state"
    return root / DEFAULT_BOOTSTRAP_STATE_DIR


def _resolve_override(value: str | None, default: Path, cwd: Path) -> Path:
    if not value:
        return default
    path = Path(value).expanduser()
    return path if path.is_absolute() else cwd / path


def _ensure_linux_private_parent(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    try:
        path.chmod(0o700)
    except OSError as error:
        raise SimpleInstallerError(
            f"Bootstrap state directory must support POSIX owner-only permissions: {path}"
        ) from error


def _write_private_exports(path: Path, values: Mapping[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    lines = ["# Tiny Swarm World bootstrap secrets. Generated once; reused on reruns."]
    lines.extend(
        f"export {name}={shlex.quote(value)}"
        for name, value in sorted(values.items())
    )
    lines.append("")
    try:
        temporary.write_text("\n".join(lines), encoding="utf-8")
        temporary.chmod(0o600)
        temporary.replace(path)
        path.chmod(0o600)
    finally:
        if temporary.exists():
            temporary.unlink()


def _ensure_traefik_dashboard_secret(env: dict[str, str]) -> None:
    current = env.get(TRAEFIK_GUI_USERS_HTPASSWD_ENVIRONMENT, "").strip()
    if current:
        return
    password = secrets.token_urlsafe(32)
    digest = base64.b64encode(hashlib.sha1(password.encode("utf-8")).digest()).decode("ascii")
    env[TRAEFIK_GUI_USERS_HTPASSWD_ENVIRONMENT] = f"admin:{{SHA}}{digest}"


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


if __name__ == "__main__":
    raise SystemExit(main())
