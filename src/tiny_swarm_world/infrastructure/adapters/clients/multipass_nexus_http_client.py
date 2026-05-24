from __future__ import annotations

import subprocess

import requests

from tiny_swarm_world.application.ports.clients.port_nexus_client import PortNexusClient
from tiny_swarm_world.domain.nexus.nexus_user import NexusUser
from tiny_swarm_world.infrastructure.adapters.clients.nexus_http_client import NexusHttpClient


class MultipassNexusHttpClient(PortNexusClient):
    def __init__(
        self,
        manager_vm: str = "swarm-manager",
        port: int = 8081,
        session: requests.Session | None = None,
        timeout_seconds: int = 30,
    ):
        self.manager_vm = manager_vm
        self.port = port
        self.session = session
        self.timeout_seconds = timeout_seconds

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
        self._client().create_docker_hosted_repository(username, password, repository_name, http_port)

    def update_docker_hosted_repository(
        self,
        username: str,
        password: str,
        repository_name: str,
        http_port: int,
    ) -> None:
        self._client().update_docker_hosted_repository(username, password, repository_name, http_port)

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
            f"http://{self._manager_ip()}:{self.port}",
            session=self.session,
        )

    def _manager_ip(self) -> str:
        try:
            result = subprocess.run(
                ["multipass", "exec", self.manager_vm, "--", "hostname", "-I"],
                capture_output=True,
                text=True,
                check=False,
                shell=False,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("Manager IP lookup timed out.") from exc
        if result.returncode != 0:
            raise RuntimeError("Manager IP lookup failed.")
        addresses = [part for part in result.stdout.split() if "." in part]
        if not addresses:
            raise RuntimeError("Manager IP lookup returned no IPv4 address.")
        return addresses[0]
