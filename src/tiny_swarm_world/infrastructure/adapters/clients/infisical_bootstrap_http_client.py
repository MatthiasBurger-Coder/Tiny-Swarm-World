from __future__ import annotations

from collections.abc import Mapping
from urllib.parse import urlparse

import requests

from tiny_swarm_world.application.ports.clients.port_infisical_bootstrap_client import (
    InfisicalBootstrapResult,
    InfisicalBootstrapState,
    PortInfisicalBootstrapClient,
)


class InfisicalBootstrapHttpClient(PortInfisicalBootstrapClient):
    def __init__(
        self,
        *,
        base_url: str = "https://localhost",
        session: requests.Session | None = None,
        timeout_seconds: float = 30.0,
        verify_tls: bool = False,
    ):
        parsed_base_url = urlparse(base_url)
        if parsed_base_url.username or parsed_base_url.password:
            raise ValueError("Infisical base URL must not contain credentials.")
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.timeout_seconds = timeout_seconds
        self.verify_tls = verify_tls

    def bootstrap_instance(
        self,
        *,
        email: str,
        password: str,
        organization: str,
    ) -> InfisicalBootstrapResult:
        response = self.session.post(
            f"{self.base_url}/api/v1/admin/bootstrap",
            headers={"Content-Type": "application/json"},
            json={
                "email": email,
                "password": password,
                "organization": organization,
            },
            timeout=self.timeout_seconds,
            verify=self.verify_tls,
        )
        if response.status_code in {400, 409}:
            return InfisicalBootstrapResult(
                state=InfisicalBootstrapState.ALREADY_INITIALIZED,
                organization=organization,
                admin_email=email,
            )
        if response.status_code >= 400:
            raise RuntimeError(f"Failed to bootstrap Infisical. HTTP {response.status_code}.")

        payload = _json_mapping(response)
        return InfisicalBootstrapResult(
            state=InfisicalBootstrapState.CREATED,
            token_returned=_token_returned(payload),
            organization=_organization_name(payload) or organization,
            admin_email=_admin_email(payload) or email,
        )


def _json_mapping(response: requests.Response) -> Mapping[str, object]:
    payload = response.json()
    if not isinstance(payload, Mapping):
        raise RuntimeError("Infisical bootstrap returned an unexpected payload.")
    return payload


def _token_returned(payload: Mapping[str, object]) -> bool:
    identity = payload.get("identity")
    if not isinstance(identity, Mapping):
        return False
    credentials = identity.get("credentials")
    if not isinstance(credentials, Mapping):
        return False
    token = credentials.get("token")
    return isinstance(token, str) and bool(token.strip())


def _organization_name(payload: Mapping[str, object]) -> str:
    organization = payload.get("organization")
    if not isinstance(organization, Mapping):
        return ""
    name = organization.get("name")
    return name if isinstance(name, str) else ""


def _admin_email(payload: Mapping[str, object]) -> str:
    user = payload.get("user")
    if not isinstance(user, Mapping):
        return ""
    email = user.get("email")
    return email if isinstance(email, str) else ""
