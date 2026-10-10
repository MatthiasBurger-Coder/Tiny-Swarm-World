from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from tiny_swarm_world.application.ports import installation as values
from tiny_swarm_world.infrastructure.adapters.installation import (
    host,
    configuration,
    process,
)
from tiny_swarm_world.infrastructure.composition_installation import (
    build_installation_service,
)

from tiny_swarm_world.infrastructure.adapters.installation.bootstrap_configuration import (
    SimpleInstallerError,
    _prepare_bootstrap_environment,
)

DEFAULT_BOOTSTRAP_SECRET_FILE = "bootstrap-secrets.env"
TRAEFIK_GUI_USERS_HTPASSWD_ENVIRONMENT = values.TRAEFIK_GUI_USERS_HTPASSWD_ENVIRONMENT


def main(argv: Sequence[str] | None = None) -> int:
    try:
        entrypoint_args = tuple(sys.argv[1:] if argv is None else argv)
        args = _parse_args(entrypoint_args)
        runtime = host.detect_host_runtime(os.environ)
        native = runtime.name == "native_linux"
        if native and args.confirm_reset:
            raise SimpleInstallerError(
                "Native installation is non-destructive. Use a separately confirmed platform reset."
            )
        if args.confirm_reset:
            if args.preflight or args.dry_run:
                raise SimpleInstallerError("Read-only installation cannot request reset.")
            print("DEPRECATED: --confirm-reset requests destructive WSL fresh-reset. Prefer a separately confirmed platform reset, then ./install.sh.", file=sys.stderr)
        if runtime.name == "wsl2" and not args.confirm_reset:
            host.authorize_project_filesystem(
                runtime, Path.cwd(), allow_wsl_windows_filesystem=False, env=os.environ
            )
        _ensure_native_python(True, entrypoint_args, is_wsl=runtime.name == "wsl2")
        env = _prepare_bootstrap_environment(os.environ, Path.cwd())
        options = values.InstallerOptions(
            service_profile="default"
            if args.profile == "classic"
            else args.service_profile,
            confirm_reset=args.confirm_reset,
            non_interactive_live_approval=args.non_interactive_live_approval,
            headless=args.headless or env.get("TSW_INSTALL_HEADLESS") == "1",
            allow_wsl_windows_filesystem=args.allow_wsl_windows_filesystem,
            native_reconcile=not args.confirm_reset,
            preflight_only=args.preflight,
            dry_run=args.dry_run,
        )
        exit_code = build_installation_service().run(options, env=env, cwd=Path.cwd())
        if exit_code == 0 and not (args.preflight or args.dry_run):
            _print_operator_credentials(env)
        return exit_code
    except (values.InstallerError, SimpleInstallerError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tiny Swarm World RC1 installer with automatic secret bootstrap."
    )
    parser.add_argument(
        "--service-profile",
        default=os.environ.get("SERVICE_PROFILE", values.DEFAULT_SERVICE_PROFILE),
        choices=("default", "service-access"),
        help="Service profile passed to setup run.",
    )
    parser.add_argument(
        "--profile",
        choices=("classic",),
        help="Native Classic alias for the supported default service profile.",
    )
    read_only = parser.add_mutually_exclusive_group()
    read_only.add_argument(
        "--preflight",
        action="store_true",
        help="Check Linux/WSL host readiness without mutation.",
    )
    read_only.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview Linux/WSL reconciliation without mutation.",
    )
    parser.add_argument(
        "--confirm-reset",
        action="store_true",
        help="Explicitly request and confirm deprecated destructive WSL fresh-reset.",
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


def _print_operator_credentials(env: Mapping[str, str]) -> None:
    portainer_url = env.get("TSW_PORTAINER_URL", "http://localhost:10001")
    infisical_url = env.get("TSW_INFISICAL_URL", "http://localhost:17080")
    print("\nTiny Swarm World access targets")
    print("--------------------------------")
    print("Credential convention: INTERNAL/TEST ONLY catalog defaults")
    print(
        "  Password values are intentionally not printed; see the credential catalog."
    )
    print("Portainer")
    print(f"  URL:      {portainer_url}")
    print("  User:     admin")
    print("  Password: catalog default or protected operator override")
    print("\nInfisical")
    print(f"  URL:      {infisical_url}")
    print(f"  User:     {env['TSW_INFISICAL_LOGIN_EMAIL']}")
    print("  Password: catalog default or protected operator override")
    print(
        "See: documentation/arc42/08_configuration/internal-test-credential-catalog.md"
    )
    print("\nAll other catalog-managed secrets are internal and are not printed.")


def _ensure_native_python(native: bool, entrypoint_args: tuple[str, ...], *, is_wsl: bool = False) -> None:
    if native and not process._python_imports_available(sys.executable, os.environ):
        python_bin = (
            configuration._paths_from_env(os.environ, Path.cwd()).native_linux_venv
            / "bin"
            / "python"
        )
        if is_wsl and python_bin.is_file():
            from tiny_swarm_world.infrastructure.adapters.installation.prerequisites import validate_user_paths

            validate_user_paths(Path.cwd(), python_bin.parent.parent, is_wsl=True)
        if not python_bin.is_file() or not process._python_imports_available(
            python_bin.as_posix(), os.environ
        ):
            raise SimpleInstallerError(
                "Native Python dependencies are missing. Run ./prepare_linux.sh separately, then retry ./install.sh."
            )
        try:
            os.execvpe(
                python_bin.as_posix(),
                (
                    python_bin.as_posix(),
                    "-m",
                    "tiny_swarm_world.simple_installer",
                    *entrypoint_args,
                ),
                dict(os.environ),
            )
        except OSError as error:
            raise SimpleInstallerError(
                "Prepared native Python could not be started."
            ) from error
