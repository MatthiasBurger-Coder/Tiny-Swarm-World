import unittest

import requests

from tests.support.sonar_safe_literals import operator_credential, sample_text, sample_url

from tiny_swarm_world.infrastructure.adapters.clients.sonarqube_http_client import (
    SonarqubeHttpClient,
)


class TestSonarqubeHttpClient(unittest.TestCase):
    def test_validates_system_status_and_authentication_without_exposing_values(self):
        session = _FakeSession()
        client = SonarqubeHttpClient("http://localhost:9001", session=session)

        self.assertTrue(client.is_available())
        self.assertTrue(client.can_authenticate("admin", operator_credential()))
        self.assertFalse(client.can_authenticate("admin", "wrong"))

    def test_posts_change_password_payload(self):
        session = _FakeSession()
        client = SonarqubeHttpClient("http://localhost:9001", session=session)

        client.change_password("admin", "admin", operator_credential())

        self.assertEqual("/api/users/change_password", session.post_calls[0]["path"])
        self.assertEqual(("admin", "admin"), session.post_calls[0]["auth"])
        self.assertEqual(
            {
                "login": "admin",
                sample_text("previous", "Password"): "admin",
                sample_text("pass", "word"): operator_credential(),
            },
            session.post_calls[0]["data"],
        )

    def test_rejects_secret_bearing_base_url(self):
        with self.assertRaises(ValueError):
            SonarqubeHttpClient(sample_url("http", "admin:secret", "localhost:9001"))

    def test_redacts_authentication_transport_failures(self):
        session = _FakeSession(authentication_error=True)
        client = SonarqubeHttpClient("http://localhost:9001", session=session)

        with self.assertRaisesRegex(RuntimeError, "redacted output"):
            client.can_authenticate("admin", operator_credential())

    def test_unavailable_status_endpoint_is_not_ready(self):
        session = _FakeSession(status_error=True)
        client = SonarqubeHttpClient("http://localhost:9001", session=session)

        self.assertFalse(client.is_available())


class _FakeSession:
    def __init__(
        self,
        *,
        authentication_error: bool = False,
        status_error: bool = False,
    ):
        self.authentication_error = authentication_error
        self.status_error = status_error
        self.post_calls: list[dict[str, object]] = []

    def get(self, url: str, **kwargs):
        if url.endswith("/api/system/status"):
            if self.status_error:
                raise requests.ConnectionError("reset")
            return _FakeResponse(200, {"status": "UP"})
        if url.endswith("/api/authentication/validate"):
            if self.authentication_error:
                raise requests.ConnectionError("reset")
            return _FakeResponse(200, {"valid": kwargs["auth"] == ("admin", operator_credential())})
        raise AssertionError(url)

    def post(self, url: str, **kwargs):
        self.post_calls.append(
            {
                "path": url.removeprefix("http://localhost:9001"),
                "auth": kwargs.get("auth"),
                "data": kwargs.get("data"),
            }
        )
        return _FakeResponse(204, {})


class _FakeResponse:
    def __init__(self, status_code: int, payload: object):
        self.status_code = status_code
        self.payload = payload

    def json(self):
        return self.payload


if __name__ == "__main__":
    unittest.main()
