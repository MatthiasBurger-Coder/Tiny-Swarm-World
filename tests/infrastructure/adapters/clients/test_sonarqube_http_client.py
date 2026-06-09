import unittest

from tiny_swarm_world.infrastructure.adapters.clients.sonarqube_http_client import (
    SonarqubeHttpClient,
)


class TestSonarqubeHttpClient(unittest.TestCase):
    def test_validates_system_status_and_authentication_without_exposing_values(self):
        session = _FakeSession()
        client = SonarqubeHttpClient("http://localhost:9001", session=session)

        self.assertTrue(client.is_available())
        self.assertTrue(client.can_authenticate("admin", "configured"))
        self.assertFalse(client.can_authenticate("admin", "wrong"))

    def test_posts_change_password_payload(self):
        session = _FakeSession()
        client = SonarqubeHttpClient("http://localhost:9001", session=session)

        client.change_password("admin", "admin", "configured")

        self.assertEqual("/api/users/change_password", session.post_calls[0]["path"])
        self.assertEqual(("admin", "admin"), session.post_calls[0]["auth"])
        self.assertEqual(
            {
                "login": "admin",
                "previousPassword": "admin",
                "password": "configured",
            },
            session.post_calls[0]["data"],
        )

    def test_rejects_secret_bearing_base_url(self):
        with self.assertRaises(ValueError):
            SonarqubeHttpClient("http://admin:secret@localhost:9001")


class _FakeSession:
    def __init__(self):
        self.post_calls: list[dict[str, object]] = []

    def get(self, url: str, **kwargs):
        if url.endswith("/api/system/status"):
            return _FakeResponse(200, {"status": "UP"})
        if url.endswith("/api/authentication/validate"):
            return _FakeResponse(200, {"valid": kwargs["auth"] == ("admin", "configured")})
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
