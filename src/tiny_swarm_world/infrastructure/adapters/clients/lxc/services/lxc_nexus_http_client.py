"""Nexus HTTP client adapter for a Nexus service hosted in LXC."""

from __future__ import annotations

from collections.abc import Callable

import requests

from tiny_swarm_world.application.ports.clients.port_nexus_client import PortNexusClient
from tiny_swarm_world.domain.nexus.nexus_user import NexusUser
from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
from tiny_swarm_world.infrastructure.adapters.clients.lxc.services.common import (
    lxc_manager_ip,
    local_service_url,
    validate_local_http_scheme,
)
from tiny_swarm_world.infrastructure.adapters.clients.nexus_http_client import NexusHttpClient


class LxcNexusHttpClient(PortNexusClient):
    """Resolve the LXC manager address and delegate Nexus operations."""

    def __init__(
        self,
        *,
        backend: ManagedLxcBackend,
        manager_node: str = "swarm-manager",
        port: int = 13081,
        scheme: str = "http",
        session: requests.Session | None = None,
        timeout_seconds: int = 30,
        manager_ip_resolver: Callable[[ManagedLxcBackend, str, int], str] = lxc_manager_ip,
    ) -> None:
        self.backend = backend
        self.manager_node = manager_node
        self.port = port
        self.scheme = validate_local_http_scheme(scheme)
        self.session = session
        self.timeout_seconds = timeout_seconds
        self._manager_ip_resolver = manager_ip_resolver

    def is_available(self) -> bool:
        return self._client().is_available()

    def can_authenticate(self, username: str, password: str) -> bool:
        return self._client().can_authenticate(username, password)

    def get_user(self, username: str, password: str, target_user_id: str) -> NexusUser:
        return self._client().get_user(username, password, target_user_id)

    def update_user(self, username: str, password: str, user: NexusUser) -> None:
        self._client().update_user(username, password, user)

    def change_password(self, username: str, password: str, target_user_id: str, new_password: str) -> None:
        self._client().change_password(username, password, target_user_id, new_password)

    def set_anonymous_access(self, username: str, password: str, enabled: bool) -> None:
        self._client().set_anonymous_access(username, password, enabled)

    def repository_exists(self, username: str, password: str, repository_name: str) -> bool:
        return self._client().repository_exists(username, password, repository_name)

    def create_docker_hosted_repository(
        self,
        username: str,
        password: str,
        repository_name: str,
        http_port: int,
    ) -> None:
        self._client().create_docker_hosted_repository(
            username,
            password,
            repository_name,
            http_port,
        )

    def update_docker_hosted_repository(
        self,
        username: str,
        password: str,
        repository_name: str,
        http_port: int,
    ) -> None:
        self._client().update_docker_hosted_repository(
            username,
            password,
            repository_name,
            http_port,
        )

    def create_docker_proxy_repository(
        self,
        username: str,
        password: str,
        repository_name: str,
        http_port: int,
        remote_url: str,
    ) -> None:
        self._client().create_docker_proxy_repository(
            username,
            password,
            repository_name,
            http_port,
            remote_url,
        )

    def create_maven_proxy_repository(
        self,
        username: str,
        password: str,
        repository_name: str,
        remote_url: str,
    ) -> None:
        self._client().create_maven_proxy_repository(username, password, repository_name, remote_url)

    def _client(self) -> NexusHttpClient:
        return NexusHttpClient(
            self._base_url(),
            session=self.session,
        )

    def _base_url(self) -> str:
        return local_service_url(
            self.scheme,
            self._manager_ip_resolver(self.backend, self.manager_node, self.timeout_seconds),
            self.port,
        )
