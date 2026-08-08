"""Portainer admin bootstrap adapter for an LXC-hosted service."""

from __future__ import annotations

from collections.abc import Callable

import requests

from tiny_swarm_world.application.ports.clients.port_portainer_admin_client import (
    PortainerAdminInitializationRejected,
    PortPortainerAdminClient,
)
from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
from tiny_swarm_world.infrastructure.adapters.clients.lxc.services.common import (
    lxc_manager_ip,
    local_service_url,
    validate_local_http_scheme,
)


class LxcPortainerAdminClient(PortPortainerAdminClient):
    """Initialize and authenticate the Portainer administrator."""

    def __init__(
        self,
        *,
        backend: ManagedLxcBackend,
        manager_node: str = "swarm-manager",
        port: int = 10001,
        scheme: str = "http",
        session: requests.Session | None = None,
        timeout_seconds: int = 30,
        manager_ip_resolver: Callable[[ManagedLxcBackend, str, int], str] = lxc_manager_ip,
    ) -> None:
        self.backend = backend
        self.manager_node = manager_node
        self.port = port
        self.scheme = validate_local_http_scheme(scheme)
        self.session = session or requests.Session()
        self.timeout_seconds = timeout_seconds
        self._manager_ip_resolver = manager_ip_resolver

    def can_authenticate(self, username: str, password: str) -> bool:
        try:
            self._clear_session_cookies()
            response = self.session.post(
                f"{self._base_url()}/api/auth",
                json={"Username": username, "Password": password},
                timeout=self.timeout_seconds,
            )
            self._clear_session_cookies()
        except requests.RequestException:
            return False
        if response.status_code != 200:
            return False
        return bool(self._json_object(response).get("jwt"))

    def initialize_admin_user(self, username: str, password: str) -> None:
        try:
            self._clear_session_cookies()
            response = self.session.post(
                f"{self._base_url()}/api/users/admin/init",
                json={"username": username, "password": password},
                timeout=self.timeout_seconds,
            )
            self._clear_session_cookies()
        except requests.RequestException as exc:
            raise RuntimeError("Failed to initialize Portainer admin user.") from exc
        if response.status_code >= 400 and not self.can_authenticate(username, password):
            raise PortainerAdminInitializationRejected(
                f"Failed to initialize Portainer admin user. HTTP {response.status_code}.",
                status_code=response.status_code,
            )

    def _base_url(self) -> str:
        return local_service_url(
            self.scheme,
            self._manager_ip_resolver(self.backend, self.manager_node, self.timeout_seconds),
            self.port,
        )

    def _clear_session_cookies(self) -> None:
        cookies = getattr(self.session, "cookies", None)
        clear = getattr(cookies, "clear", None)
        if callable(clear):
            clear()

    @staticmethod
    def _json_object(response: requests.Response) -> dict[str, object]:
        try:
            payload = response.json()
        except ValueError:
            return {}
        if isinstance(payload, dict):
            return payload
        return {}
