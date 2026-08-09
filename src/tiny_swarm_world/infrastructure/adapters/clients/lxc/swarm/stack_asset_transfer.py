"""Strategy-based stack asset transfer for the LXC Swarm runtime."""

from __future__ import annotations

import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol

from tiny_swarm_world.infrastructure.adapters.clients.lxc.swarm.swarm_stack_runtime import (
    _quote_remote_path,
)
from tiny_swarm_world.infrastructure.project_paths import ProjectPaths


ManagerShell = Callable[..., subprocess.CompletedProcess[str]]
DashboardRenderer = Callable[[], str]


@dataclass(frozen=True, slots=True)
class StackAssetTransferContext:
    stack_name: str
    remote_dir: str
    project_paths: ProjectPaths
    run_manager_shell: ManagerShell
    render_service_access_dashboard: DashboardRenderer


class StackAssetTransferStrategy(Protocol):
    def supports(self, stack_name: str) -> bool:
        pass

    def transfer(self, context: StackAssetTransferContext) -> None:
        pass


@dataclass(frozen=True, slots=True)
class TraefikAssetTransferStrategy:
    def supports(self, stack_name: str) -> bool:
        return stack_name == "traefik"

    def transfer(self, context: StackAssetTransferContext) -> None:
        tls_config = (
            context.project_paths.infra_root
            / "config"
            / "compose"
            / "traefik"
            / "dynamic"
            / "tls.yml"
        )
        script = (
            f"set -e; mkdir -p {_quote_remote_path(context.remote_dir + '/dynamic')}; "
            f"cat > {_quote_remote_path(context.remote_dir + '/dynamic/tls.yml')}"
        )
        context.run_manager_shell(script, input_text=tls_config.read_text(encoding="utf-8"))


@dataclass(frozen=True, slots=True)
class ServiceAccessAssetTransferStrategy:
    def supports(self, stack_name: str) -> bool:
        return stack_name == "service-access"

    def transfer(self, context: StackAssetTransferContext) -> None:
        script = (
            f"set -e; mkdir -p {_quote_remote_path(context.remote_dir + '/dashboard')}; "
            f"cat > {_quote_remote_path(context.remote_dir + '/dashboard/index.html')}"
        )
        context.run_manager_shell(
            script,
            input_text=context.render_service_access_dashboard(),
        )


@dataclass(frozen=True, slots=True)
class SwaggerAssetTransferStrategy:
    def supports(self, stack_name: str) -> bool:
        return stack_name == "swagger"

    def transfer(self, context: StackAssetTransferContext) -> None:
        openapi_file = (
            context.project_paths.infra_root
            / "config"
            / "compose"
            / "swagger"
            / "swagger"
            / "openapi.json"
        )
        nginx_config = (
            context.project_paths.infra_root
            / "config"
            / "compose"
            / "swagger"
            / "nginx"
            / "default.conf"
        )
        script = (
            f"set -e; mkdir -p {_quote_remote_path(context.remote_dir + '/swagger')}; "
            f"cat > {_quote_remote_path(context.remote_dir + '/swagger/openapi.json')}"
        )
        context.run_manager_shell(script, input_text=openapi_file.read_text(encoding="utf-8"))
        script = (
            f"set -e; mkdir -p {_quote_remote_path(context.remote_dir + '/nginx')}; "
            f"cat > {_quote_remote_path(context.remote_dir + '/nginx/default.conf')}"
        )
        context.run_manager_shell(script, input_text=nginx_config.read_text(encoding="utf-8"))


@dataclass(frozen=True, slots=True)
class StackAssetTransferRegistry:
    strategies: tuple[StackAssetTransferStrategy, ...]

    def transfer(self, context: StackAssetTransferContext) -> None:
        for strategy in self.strategies:
            if strategy.supports(context.stack_name):
                strategy.transfer(context)
                return


class StackAssetTransfer:
    """Dispatch stack-specific asset transfer through ordered strategies."""

    def __init__(
        self,
        *,
        project_paths: ProjectPaths,
        run_manager_shell: ManagerShell,
        render_service_access_dashboard: DashboardRenderer,
        strategies: Sequence[StackAssetTransferStrategy] | None = None,
    ) -> None:
        self.project_paths = project_paths
        self._run_manager_shell = run_manager_shell
        self._render_service_access_dashboard = render_service_access_dashboard
        self.registry = StackAssetTransferRegistry(
            tuple(
                strategies
                or (
                    TraefikAssetTransferStrategy(),
                    ServiceAccessAssetTransferStrategy(),
                    SwaggerAssetTransferStrategy(),
                )
            )
        )

    def transfer_stack_assets(self, stack_name: str, remote_dir: str) -> None:
        self.registry.transfer(
            StackAssetTransferContext(
                stack_name=stack_name,
                remote_dir=remote_dir,
                project_paths=self.project_paths,
                run_manager_shell=self._run_manager_shell,
                render_service_access_dashboard=self._render_service_access_dashboard,
            )
        )
