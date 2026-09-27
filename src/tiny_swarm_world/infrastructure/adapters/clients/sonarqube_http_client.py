from __future__ import annotations

from tiny_swarm_world.application.ports.clients.port_sonarqube_client import SonarqubeClientError
from tiny_swarm_world.application.ports.operation_result import OperationFailure
from tiny_swarm_world.infrastructure.adapters.exceptions.operation_failure_mapping import request_failure

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

    def _request(self, method: str, *args, **kwargs) -> requests.Response:
        try:
            return getattr(self.session, method)(*args, **kwargs)
        except requests.RequestException as exc:
            raise SonarqubeClientError(request_failure(exc, "service.request", "sonarqube")) from None

    def is_available(self) -> bool:
        try:
            response = self.session.get(f"{self.base_url}/api/system/status", timeout=30)
        except requests.RequestException:
            return False
        if response.status_code != 200:
            return False
        payload = _response_payload(response)
        return isinstance(payload, dict) and payload.get("status") == "UP"

    def can_authenticate(self, username: str, password: str) -> bool:
        response = self._request("get",
            f"{self.base_url}/api/authentication/validate",
            auth=(username, password),
            timeout=30,
        )
        if response.status_code != 200:
            return False
        payload = _response_payload(response)
        return isinstance(payload, dict) and payload.get("valid") is True

    def change_password(
        self,
        username: str,
        current_password: str,
        new_password: str,
    ) -> None:
        response = self._request("post",
            f"{self.base_url}/api/users/change_password",
            auth=(username, current_password),
            data={
                "login": username,
                "previousPassword": current_password,
                "password": new_password,
            },
            timeout=30,
        )
        if response.status_code >= 400:
            raise SonarqubeClientError(OperationFailure.for_cause("service.request", "sonarqube", "request_failed")) from None


def _response_payload(response: requests.Response):
    try:
        return response.json()
    except ValueError:
        raise SonarqubeClientError(OperationFailure.for_cause("service.decode", "sonarqube", "request_failed")) from None
