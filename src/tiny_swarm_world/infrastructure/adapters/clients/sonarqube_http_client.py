from __future__ import annotations

from urllib.parse import urlparse

import requests

from tiny_swarm_world.application.ports.clients.port_sonarqube_client import (
    PortSonarqubeClient,
)


class SonarqubeHttpClient(PortSonarqubeClient):
    def __init__(self, base_url: str, session: requests.Session | None = None) -> None:
        parsed_url = urlparse(base_url)
        if parsed_url.username or parsed_url.password:
            raise ValueError("SonarQube base URL must not contain credentials.")
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()

    def is_available(self) -> bool:
        try:
            response = self.session.get(f"{self.base_url}/api/system/status", timeout=30)
        except requests.RequestException:
            return False
        if response.status_code != 200:
            return False
        payload = response.json()
        return isinstance(payload, dict) and payload.get("status") == "UP"

    def can_authenticate(self, username: str, password: str) -> bool:
        try:
            response = self.session.get(
                f"{self.base_url}/api/authentication/validate",
                auth=(username, password),
                timeout=30,
            )
        except requests.RequestException as exc:
            raise RuntimeError(
                "SonarQube authentication check failed with redacted output."
            ) from exc
        if response.status_code != 200:
            return False
        payload = response.json()
        return isinstance(payload, dict) and payload.get("valid") is True

    def change_password(
        self,
        username: str,
        current_password: str,
        new_password: str,
    ) -> None:
        try:
            response = self.session.post(
                f"{self.base_url}/api/users/change_password",
                auth=(username, current_password),
                data={
                    "login": username,
                    "previousPassword": current_password,
                    "password": new_password,
                },
                timeout=30,
            )
        except requests.RequestException as exc:
            raise RuntimeError(
                "SonarQube admin password rotation failed with redacted output."
            ) from exc
        if response.status_code >= 400:
            raise RuntimeError("SonarQube admin password rotation failed with redacted output.")
