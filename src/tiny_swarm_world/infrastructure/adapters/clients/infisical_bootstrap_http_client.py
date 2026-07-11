from __future__ import annotations

import time
import warnings
from collections.abc import Callable
from collections.abc import Mapping
from collections.abc import Iterator
from contextlib import contextmanager
from urllib.parse import urlparse

import requests
from urllib3.exceptions import InsecureRequestWarning

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
        verify_tls: bool = True,
        readiness_attempts: int = 60,
        readiness_interval_seconds: float = 5.0,
        readiness_recovery: Callable[[], bool] | None = None,
    ):
        parsed_base_url = urlparse(base_url)
        if parsed_base_url.username or parsed_base_url.password:
            raise ValueError("Infisical base URL must not contain credentials.")
        if readiness_attempts < 1:
            raise ValueError("Infisical readiness attempts must be at least one.")
        if readiness_interval_seconds < 0:
            raise ValueError("Infisical readiness interval must not be negative.")
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.timeout_seconds = timeout_seconds
        self.verify_tls = verify_tls
        self.readiness_attempts = readiness_attempts
        self.readiness_interval_seconds = readiness_interval_seconds
        self.readiness_recovery = readiness_recovery

    def bootstrap_instance(
        self,
        *,
        email: str,
        password: str,
        organization: str,
    ) -> InfisicalBootstrapResult:
        self._wait_until_ready()
        with _local_tls_warning_context(self.verify_tls):
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

    def _wait_until_ready(self) -> None:
        recovery_attempted = False
        while True:
            unavailable = self._readiness_unavailable()
            if unavailable is None:
                return
            if self.readiness_recovery is None or recovery_attempted:
                raise unavailable
            recovery_attempted = True
            if not self.readiness_recovery():
                raise unavailable

    def _readiness_unavailable(self) -> "InfisicalBootstrapUnavailable | None":
        last_status_code: int | None = None
        last_failure: Exception | None = None
        for attempt in range(1, self.readiness_attempts + 1):
            try:
                with _local_tls_warning_context(self.verify_tls):
                    response = self.session.get(
                        f"{self.base_url}/api/status",
                        timeout=self.timeout_seconds,
                        verify=self.verify_tls,
                    )
            except requests.RequestException as exc:
                last_failure = exc
            else:
                last_status_code = response.status_code
                if response.status_code < 500:
                    return None
            if attempt < self.readiness_attempts:
                time.sleep(self.readiness_interval_seconds)

        if last_status_code is not None:
            return InfisicalBootstrapUnavailable(last_status_code)
        if last_failure is not None:
            return InfisicalBootstrapUnavailable.from_exception(last_failure)
        return InfisicalBootstrapUnavailable()


class InfisicalBootstrapUnavailable(RuntimeError):
    def __init__(self, status_code: int | None = None, reason: str = "not_ready"):
        super().__init__("Infisical bootstrap API is not ready.")
        self.status_code = status_code
        self.reason = reason

    @classmethod
    def from_exception(cls, exc: Exception) -> "InfisicalBootstrapUnavailable":
        return cls(reason=exc.__class__.__name__)


@contextmanager
def _local_tls_warning_context(verify_tls: bool) -> Iterator[None]:
    if verify_tls:
        yield
        return
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", InsecureRequestWarning)
        yield


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
