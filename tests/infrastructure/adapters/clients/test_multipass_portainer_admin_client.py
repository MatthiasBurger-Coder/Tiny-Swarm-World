import unittest
from unittest.mock import patch

from tiny_swarm_world.infrastructure.adapters.clients.multipass_portainer_admin_client import (
    MultipassPortainerAdminClient,
)


class TestMultipassPortainerAdminClient(unittest.TestCase):
    def test_can_authenticate_returns_false_for_non_json_success_response(self):
        session = _FakeSession([_FakeResponse(200, ValueError("html response"))])
        client = MultipassPortainerAdminClient(session=session)

        with patch.object(client, "_manager_ip", return_value="10.157.2.182"):
            self.assertFalse(client.can_authenticate("admin", "operator-password"))

        self.assertEqual("http://10.157.2.182:9000/api/auth", session.post_calls[0]["url"])

    def test_can_authenticate_keeps_portainer_login_requests_stateless(self):
        session = _PortainerCookieSession()
        client = MultipassPortainerAdminClient(session=session)

        with patch.object(client, "_manager_ip", return_value="10.157.2.182"):
            self.assertTrue(client.can_authenticate("admin", "operator-password"))
            self.assertTrue(client.can_authenticate("admin", "operator-password"))

        self.assertEqual(2, len(session.post_calls))
        self.assertEqual(4, session.cookies.clear_calls)

    def test_initialize_admin_user_sanitizes_failed_init_with_malformed_auth_fallback(self):
        session = _FakeSession(
            [
                _FakeResponse(409, {"message": "secret=leaked"}),
                _FakeResponse(200, ValueError("secret=leaked")),
            ]
        )
        client = MultipassPortainerAdminClient(session=session)

        with patch.object(client, "_manager_ip", return_value="10.157.2.182"):
            with self.assertRaises(RuntimeError) as raised:
                client.initialize_admin_user("admin", "operator-password")

        self.assertIn("HTTP 409", str(raised.exception))
        self.assertNotIn("secret=leaked", str(raised.exception))


class _FakeResponse:
    def __init__(self, status_code: int, payload: object):
        self.status_code = status_code
        self.payload = payload

    def json(self) -> object:
        if isinstance(self.payload, ValueError):
            raise self.payload
        return self.payload


class _FakeSession:
    def __init__(self, post_responses: list[_FakeResponse]):
        self.post_responses = list(post_responses)
        self.post_calls: list[dict[str, object]] = []

    def post(self, url: str, **kwargs: object) -> _FakeResponse:
        self.post_calls.append({"url": url, **kwargs})
        return self.post_responses.pop(0)


class _FakeCookies(dict[str, str]):
    def __init__(self):
        super().__init__()
        self.clear_calls = 0

    def clear(self) -> None:
        self.clear_calls += 1
        super().clear()


class _PortainerCookieSession:
    def __init__(self):
        self.cookies = _FakeCookies()
        self.post_calls: list[dict[str, object]] = []

    def post(self, url: str, **kwargs: object) -> _FakeResponse:
        self.post_calls.append({"url": url, **kwargs, "cookies": dict(self.cookies)})
        if self.cookies:
            return _FakeResponse(403, ValueError("Forbidden - CSRF token not found in request"))
        self.cookies["portainer_api_key"] = "jwt-cookie"
        return _FakeResponse(200, {"jwt": "jwt-token"})


if __name__ == "__main__":
    unittest.main()
