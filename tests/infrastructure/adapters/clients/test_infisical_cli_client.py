import os
import requests
import unittest
from unittest.mock import patch

from tests.support.sonar_safe_literals import operator_credential, sample_text, token_marker

from tiny_swarm_world.application.ports.clients.port_infisical_cli import InfisicalCliResult
from tiny_swarm_world.infrastructure.adapters.clients.infisical_cli_client import (
    InfisicalCliClient,
    _secret_value,
)


class TestInfisicalCliClient(unittest.TestCase):
    def test_uses_admin_login_token_when_bootstrap_token_is_missing(self):
        calls: list[tuple[str, str]] = []
        session = _FakeSession(calls, self)

        client = InfisicalCliClient(base_url="http://localhost:17080", session=session)

        with patch.dict(
            os.environ,
            {
                "TSW_INFISICAL_LOGIN_EMAIL": "admin@tiny-swarm-world.local",
                "TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD": operator_credential(),
            },
            clear=True,
        ):
            client.ensure_project_environment("tiny-swarm-world", "local")

        self.assertEqual(calls[0], ("POST", "http://localhost:17080/api/v3/auth/login"))

    def test_retries_transient_infisical_request_timeouts(self):
        calls: list[tuple[str, str]] = []
        session = _FakeSession(
            calls,
            self,
            request_failures=[requests.ReadTimeout("slow Infisical response")],
        )
        client = InfisicalCliClient(
            base_url="http://localhost:17080",
            session=session,
            retry_wait_seconds=0,
        )

        with patch.dict(
            os.environ,
            {
                "TSW_INFISICAL_LOGIN_EMAIL": "admin@tiny-swarm-world.local",
                "TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD": operator_credential(),
            },
            clear=True,
        ):
            self.assertFalse(
                client.secret_exists("TSW_EXAMPLE_PASSWORD", project="tiny-swarm-world", environment="local")
            )

        organization_calls = [call for call in calls if call == ("GET", "http://localhost:17080/api/v1/organization")]
        self.assertEqual(len(organization_calls), 2)

    def test_reads_one_managed_value_without_exposing_it_in_client_diagnostics(self):
        calls: list[tuple[str, str]] = []
        session = _FakeSession(
            calls,
            self,
            secret_payload={
                "secrets": [
                    {
                        "secretKey": "TSW_EXAMPLE_PASSWORD",
                        "secretValue": operator_credential(),
                    }
                ]
            },
        )
        client = InfisicalCliClient(base_url="http://localhost:17080", session=session)

        with patch.dict(
            os.environ,
            {
                "TSW_INFISICAL_LOGIN_EMAIL": "admin@tiny-swarm-world.local",
                "TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD": operator_credential(),
            },
            clear=True,
        ):
            value = client.get_secret(
                "TSW_EXAMPLE_PASSWORD",
                project="tiny-swarm-world",
                environment="local",
            )

        self.assertEqual(value, operator_credential())
        self.assertTrue(any("/api/v3/secrets/raw?" in url for _, url in calls))

    def test_missing_managed_value_is_distinct_from_an_authorization_failure(self):
        calls: list[tuple[str, str]] = []
        session = _FakeSession(calls, self, secret_status_code=404)
        client = InfisicalCliClient(base_url="http://localhost:17080", session=session)

        with patch.dict(
            os.environ,
            {
                "TSW_INFISICAL_LOGIN_EMAIL": "admin@tiny-swarm-world.local",
                "TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD": operator_credential(),
            },
            clear=True,
        ):
            self.assertIsNone(
                client.get_secret(
                    "TSW_EXAMPLE_PASSWORD",
                    project="tiny-swarm-world",
                    environment="local",
                )
            )

    def test_authorization_failure_blocks_instead_of_becoming_a_missing_value(self):
        calls: list[tuple[str, str]] = []
        session = _FakeSession(calls, self, secret_status_code=401)
        client = InfisicalCliClient(base_url="http://localhost:17080", session=session)

        with patch.dict(
            os.environ,
            {
                "TSW_INFISICAL_LOGIN_EMAIL": "admin@tiny-swarm-world.local",
                "TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD": operator_credential(),
            },
            clear=True,
        ):
            with self.assertRaisesRegex(RuntimeError, "redacted output"):
                client.get_secret(
                    "TSW_EXAMPLE_PASSWORD",
                    project="tiny-swarm-world",
                    environment="local",
                )

    def test_secret_value_parser_handles_malformed_and_nonmatching_payloads(self):
        self.assertIsNone(_secret_value("not-a-mapping", "TSW_EXAMPLE_PASSWORD"))
        self.assertIsNone(_secret_value({"secrets": "not-a-list"}, "TSW_EXAMPLE_PASSWORD"))
        self.assertIsNone(
            _secret_value(
                {"secrets": [{"secretKey": "OTHER_KEY", "secretValue": "value"}]},
                "TSW_EXAMPLE_PASSWORD",
            )
        )
        self.assertIsNone(
            _secret_value(
                {"secrets": [{"secretKey": "TSW_EXAMPLE_PASSWORD"}]},
                "TSW_EXAMPLE_PASSWORD",
            )
        )

    def test_bootstrap_token_stays_on_client_and_legacy_environment_name_is_ignored(self):
        calls: list[tuple[str, str]] = []
        session = _FakeSession(calls, self)
        client = InfisicalCliClient(base_url="http://localhost:17080", session=session)

        with patch.dict(
            os.environ,
            {"TSW_INFISICAL_BOOTSTRAP_TOKEN": "legacy-token"},
            clear=True,
        ):
            with patch(
                "tiny_swarm_world.infrastructure.adapters.clients.infisical_cli_client._run",
                return_value=InfisicalCliResult(
                    return_code=0,
                    stdout='{"identity":{"credentials":{"token":"client-only-token"}}}',
                ),
            ):
                client.run_bootstrap(("infisical", "bootstrap"))
            self.assertEqual(client._access_token(), "client-only-token")


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
        secret_payload: object | None = None,
        secret_status_code: int = 200,
    ):
        self.calls = calls
        self.test_case = test_case
        self.request_failures = list(request_failures or [])
        self.secret_payload = secret_payload
        self.secret_status_code = secret_status_code

    def post(self, url: str, **kwargs):
        self.calls.append(("POST", url))
        if url.endswith("/api/v3/auth/select-organization"):
            self.test_case.assertEqual(f"Bearer {token_marker()}", kwargs["headers"]["Authorization"])
            return _FakeResponse(200, {"token": sample_text("selected-org-", "value")})
        return _FakeResponse(200, {"accessToken": token_marker()})

    def request(self, method: str, url: str, **kwargs):
        self.calls.append((method, url))
        if self.request_failures:
            raise self.request_failures.pop(0)
        expected_token = token_marker() if url.endswith("/api/v1/organization") else sample_text("selected-org-", "value")
        self.test_case.assertEqual(f"Bearer {expected_token}", kwargs["headers"]["Authorization"])
        if url.endswith("/api/v1/organization"):
            return _FakeResponse(200, {"organizations": [{"id": "org-id"}]})
        if url.endswith("/api/v1/projects"):
            return _FakeResponse(200, {"projects": [{"id": "project-id", "name": "tiny-swarm-world"}]})
        if "/api/v3/secrets/raw?" in url and self.secret_payload is not None:
            return _FakeResponse(self.secret_status_code, self.secret_payload)
        if "/api/v3/secrets/raw?" in url:
            return _FakeResponse(self.secret_status_code, {})
        return _FakeResponse(200, {})

    def get(self, url: str, **kwargs):
        return self.request("GET", url, **kwargs)


if __name__ == "__main__":
    unittest.main()
