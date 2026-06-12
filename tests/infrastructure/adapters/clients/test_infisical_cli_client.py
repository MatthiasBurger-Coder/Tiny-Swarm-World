import os
import requests
import unittest
from unittest.mock import patch

from tiny_swarm_world.infrastructure.adapters.clients.infisical_cli_client import InfisicalCliClient


class TestInfisicalCliClient(unittest.TestCase):
    def test_uses_admin_login_token_when_bootstrap_token_is_missing(self):
        client = InfisicalCliClient(base_url="http://localhost:8086")
        calls: list[tuple[str, str]] = []
        session = _FakeSession(calls, self)

        client = InfisicalCliClient(base_url="http://localhost:8086", session=session)

        with patch.dict(
            os.environ,
            {
                "TSW_INFISICAL_LOGIN_EMAIL": "admin@tiny-swarm-world.local",
                "TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD": "password",
            },
            clear=True,
        ):
            client.ensure_project_environment("tiny-swarm-world", "local")

        self.assertEqual(("POST", "http://localhost:8086/api/v3/auth/login"), calls[0])

    def test_retries_transient_infisical_request_timeouts(self):
        calls: list[tuple[str, str]] = []
        session = _FakeSession(
            calls,
            self,
            request_failures=[requests.ReadTimeout("slow Infisical response")],
        )
        client = InfisicalCliClient(
            base_url="http://localhost:8086",
            session=session,
            retry_wait_seconds=0,
        )

        with patch.dict(
            os.environ,
            {
                "TSW_INFISICAL_LOGIN_EMAIL": "admin@tiny-swarm-world.local",
                "TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD": "password",
            },
            clear=True,
        ):
            self.assertFalse(
                client.secret_exists("TSW_EXAMPLE_PASSWORD", project="tiny-swarm-world", environment="local")
            )

        organization_calls = [call for call in calls if call == ("GET", "http://localhost:8086/api/v1/organization")]
        self.assertEqual(2, len(organization_calls))


class _FakeResponse:
    def __init__(self, status_code: int, payload: object):
        self.status_code = status_code
        self.payload = payload

    def json(self):
        return self.payload


class _FakeSession:
    def __init__(
        self,
        calls: list[tuple[str, str]],
        test_case: unittest.TestCase,
        request_failures: list[requests.RequestException] | None = None,
    ):
        self.calls = calls
        self.test_case = test_case
        self.request_failures = list(request_failures or [])

    def post(self, url: str, **kwargs):
        self.calls.append(("POST", url))
        if url.endswith("/api/v3/auth/select-organization"):
            self.test_case.assertEqual("Bearer session-token", kwargs["headers"]["Authorization"])
            return _FakeResponse(200, {"token": "selected-org-token"})
        return _FakeResponse(200, {"accessToken": "session-token"})

    def request(self, method: str, url: str, **kwargs):
        self.calls.append((method, url))
        if self.request_failures:
            raise self.request_failures.pop(0)
        expected_token = "session-token" if url.endswith("/api/v1/organization") else "selected-org-token"
        self.test_case.assertEqual(f"Bearer {expected_token}", kwargs["headers"]["Authorization"])
        if url.endswith("/api/v1/organization"):
            return _FakeResponse(200, {"organizations": [{"id": "org-id"}]})
        if url.endswith("/api/v1/projects"):
            return _FakeResponse(200, {"projects": [{"id": "project-id", "name": "tiny-swarm-world"}]})
        return _FakeResponse(200, {})

    def get(self, url: str, **kwargs):
        return self.request("GET", url, **kwargs)


if __name__ == "__main__":
    unittest.main()
