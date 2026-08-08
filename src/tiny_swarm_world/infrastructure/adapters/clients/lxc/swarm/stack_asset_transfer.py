"""Stack-specific asset transfer for the LXC Swarm runtime."""

from __future__ import annotations

import shlex
import subprocess
from collections.abc import Callable

from tiny_swarm_world.infrastructure.project_paths import ProjectPaths


REMOTE_WORKDIR_PREFIX = "$PWD/"
ManagerShell = Callable[..., subprocess.CompletedProcess[str]]


class StackAssetTransfer:
    """Transfer generated or committed stack assets to a remote stack root."""

    def __init__(
        self,
        *,
        project_paths: ProjectPaths,
        run_manager_shell: ManagerShell,
        render_service_access_dashboard: Callable[[], str],
    ) -> None:
        self.project_paths = project_paths
        self._run_manager_shell = run_manager_shell
        self._render_service_access_dashboard = render_service_access_dashboard

    def transfer_stack_assets(self, stack_name: str, remote_dir: str) -> None:
        if stack_name == "traefik":
            tls_config = (
                self.project_paths.infra_root
                / "config"
                / "compose"
                / "traefik"
                / "dynamic"
                / "tls.yml"
            )
            script = (
                f"set -e; mkdir -p {_quote_remote_path(remote_dir + '/dynamic')}; "
                f"cat > {_quote_remote_path(remote_dir + '/dynamic/tls.yml')}"
            )
            self._run_manager_shell(script, input_text=tls_config.read_text(encoding="utf-8"))
            return
        if stack_name == "service-access":
            script = (
                f"set -e; mkdir -p {_quote_remote_path(remote_dir + '/dashboard')}; "
                f"cat > {_quote_remote_path(remote_dir + '/dashboard/index.html')}"
            )
            self._run_manager_shell(
                script,
                input_text=self._render_service_access_dashboard(),
            )
            return
        if stack_name != "swagger":
            return
        openapi_file = (
            self.project_paths.infra_root
            / "config"
            / "compose"
            / "swagger"
            / "swagger"
            / "openapi.json"
        )
        nginx_config = (
            self.project_paths.infra_root
            / "config"
            / "compose"
            / "swagger"
            / "nginx"
            / "default.conf"
        )
        script = (
            f"set -e; mkdir -p {_quote_remote_path(remote_dir + '/swagger')}; "
            f"cat > {_quote_remote_path(remote_dir + '/swagger/openapi.json')}"
        )
        self._run_manager_shell(script, input_text=openapi_file.read_text(encoding="utf-8"))
        script = (
            f"set -e; mkdir -p {_quote_remote_path(remote_dir + '/nginx')}; "
            f"cat > {_quote_remote_path(remote_dir + '/nginx/default.conf')}"
        )
        self._run_manager_shell(script, input_text=nginx_config.read_text(encoding="utf-8"))


def _quote_remote_path(path: str) -> str:
    if path.startswith(REMOTE_WORKDIR_PREFIX):
        return f"{REMOTE_WORKDIR_PREFIX}{shlex.quote(path.removeprefix(REMOTE_WORKDIR_PREFIX))}"
    return shlex.quote(path)
