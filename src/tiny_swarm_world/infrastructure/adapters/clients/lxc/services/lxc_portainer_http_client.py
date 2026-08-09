"""Portainer deployment and administration adapter for LXC."""

from __future__ import annotations

import shlex
import subprocess
from collections.abc import Callable, Mapping

import requests

from tiny_swarm_world.application.ports.clients.port_deployment_gateway import (
    DeploymentStackRequest,
    PortDeploymentGateway,
)
from tiny_swarm_world.application.ports.clients.port_portainer_client import PortPortainerClient
from tiny_swarm_world.domain.deployment import StackDefinition
from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
from tiny_swarm_world.infrastructure.adapters.clients.lxc.services.common import (
    lxc_manager_ip,
    local_service_url,
    validate_local_http_scheme,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.backend_cli import backend_cli
from tiny_swarm_world.infrastructure.adapters.clients.lxc.swarm.swarm_stack_runtime import (
    _external_overlay_network_names,
)
from tiny_swarm_world.infrastructure.adapters.clients.portainer_http_client import PortainerHttpClient


class LxcPortainerHttpClient(PortPortainerClient, PortDeploymentGateway):
    """Resolve local Portainer access and retain deployment safeguards."""

    def __init__(
        self,
        *,
        backend: ManagedLxcBackend,
        username: str,
        password: str,
        manager_node: str = "swarm-manager",
        port: int = 10001,
        scheme: str = "http",
        api_url: str | None = None,
        session: requests.Session | None = None,
        timeout_seconds: int = 30,
        stack_request_timeout_seconds: int = 180,
        manager_ip_resolver: Callable[[ManagedLxcBackend, str, int], str] = lxc_manager_ip,
    ) -> None:
        if stack_request_timeout_seconds <= 0:
            raise ValueError("Portainer stack request timeout must be positive.")
        self.backend = backend
        self.username = username
        self.password = password
        self.manager_node = manager_node
        self.port = port
        self.scheme = validate_local_http_scheme(scheme)
        self.api_url = api_url.rstrip("/") if api_url else None
        self.session = session
        self.timeout_seconds = timeout_seconds
        self.stack_request_timeout_seconds = stack_request_timeout_seconds
        self._cached_client: PortainerHttpClient | None = None
        self._manager_ip_resolver = manager_ip_resolver

    def get_endpoint_id_by_name(self, endpoint_name: str) -> int:
        return self._client().get_endpoint_id_by_name(endpoint_name)

    def ensure_local_endpoint(self, endpoint_name: str) -> int:
        return self._client().ensure_local_endpoint(endpoint_name)

    def find_stack_id_by_name(self, stack_name: str) -> int | None:
        return self._client().find_stack_id_by_name(stack_name)

    def create_stack(
        self,
        stack_definition: StackDefinition,
        endpoint_id: int,
        stack_environment: Mapping[str, str] | None = None,
    ) -> None:
        self._ensure_external_overlay_networks(stack_definition)
        self._client().create_stack(stack_definition, endpoint_id, stack_environment)

    def update_stack(
        self,
        stack_id: int,
        stack_definition: StackDefinition,
        endpoint_id: int,
        stack_environment: Mapping[str, str] | None = None,
    ) -> None:
        self._ensure_external_overlay_networks(stack_definition)
        self._client().update_stack(
            stack_id,
            stack_definition,
            endpoint_id,
            stack_environment,
        )

    def apply_stack(self, request: DeploymentStackRequest) -> None:
        endpoint_id = self.get_endpoint_id_by_name("local")
        stack_id = self.find_stack_id_by_name(request.stack_definition.name)
        if stack_id is None:
            self.create_stack(
                request.stack_definition,
                endpoint_id,
                request.stack_environment,
            )
            return
        self.update_stack(
            stack_id,
            request.stack_definition,
            endpoint_id,
            request.stack_environment,
        )

    def stack_registered(self, stack_name: str) -> bool:
        return self.find_stack_id_by_name(stack_name) is not None

    def _ensure_external_overlay_networks(self, stack_definition: StackDefinition) -> None:
        for network_name in _external_overlay_network_names(stack_definition):
            result = self._run_manager_shell(
                f"docker network inspect -- {shlex.quote(network_name)} >/dev/null 2>&1",
                check=False,
            )
            if result.returncode == 0:
                continue
            self._run_manager_shell(
                "docker network create --driver overlay --attachable -- "
                f"{shlex.quote(network_name)} >/dev/null"
            )

    def _run_manager_shell(
        self,
        script: str,
        *,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        try:
            result = subprocess.run(
                [backend_cli(self.backend), "exec", self.manager_node, "--", "sh", "-lc", script],
                capture_output=True,
                text=True,
                check=False,
                shell=False,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("LXC manager Portainer prerequisite operation timed out.") from exc
        if check and result.returncode != 0:
            raise RuntimeError(
                f"LXC manager Portainer prerequisite operation failed with exit code {result.returncode}."
            )
        return result

    def _client(self) -> PortainerHttpClient:
        if self._cached_client is None:
            self._cached_client = PortainerHttpClient(
                self.api_url or self._base_url(),
                self.username,
                self.password,
                session=self.session,
                request_timeout_seconds=self.timeout_seconds,
                stack_request_timeout_seconds=self.stack_request_timeout_seconds,
            )
        return self._cached_client

    def _base_url(self) -> str:
        return local_service_url(
            self.scheme,
            self._manager_ip_resolver(self.backend, self.manager_node, self.timeout_seconds),
            self.port,
        )
