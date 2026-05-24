from __future__ import annotations

import subprocess

import requests

from tiny_swarm_world.application.ports.clients.port_portainer_admin_client import (
    PortPortainerAdminClient,
)


class MultipassPortainerAdminClient(PortPortainerAdminClient):
    def __init__(
        self,
        manager_vm: str = "swarm-manager",
        port: int = 9000,
        session: requests.Session | None = None,
        timeout_seconds: int = 30,
    ):
        self.manager_vm = manager_vm
        self.port = port
        self.session = session or requests.Session()
        self.timeout_seconds = timeout_seconds

    def can_authenticate(self, username: str, password: str) -> bool:
        try:
            response = self.session.post(
                f"{self._base_url()}/api/auth",
                json={"Username": username, "Password": password},
                timeout=self.timeout_seconds,
            )
        except requests.RequestException:
            return False
        if response.status_code != 200:
            return False
        return bool(self._json_object(response).get("jwt"))

    def initialize_admin_user(self, username: str, password: str) -> None:
        try:
            response = self.session.post(
                f"{self._base_url()}/api/users/admin/init",
                json={"username": username, "password": password},
                timeout=self.timeout_seconds,
            )
        except requests.RequestException as exc:
            raise RuntimeError("Failed to initialize Portainer admin user.") from exc
        if response.status_code >= 400 and not self.can_authenticate(username, password):
            raise RuntimeError(f"Failed to initialize Portainer admin user. HTTP {response.status_code}.")

    def _base_url(self) -> str:
        return f"http://{self._manager_ip()}:{self.port}"

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

    @staticmethod
    def _json_object(response: requests.Response) -> dict[str, object]:
        try:
            payload = response.json()
        except ValueError:
            return {}
        if isinstance(payload, dict):
            return payload
        return {}
