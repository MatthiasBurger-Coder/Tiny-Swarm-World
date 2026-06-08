import importlib.util
import sys
import types
import unittest
from pathlib import Path

from tiny_swarm_world.application.ports.clients.port_infisical_bootstrap_client import (
    InfisicalBootstrapState,
)

MODULE_PATH = (
    Path(__file__).resolve().parents[4]
    / "src"
    / "tiny_swarm_world"
    / "infrastructure"
    / "adapters"
    / "clients"
    / "infisical_bootstrap_http_client.py"
)


def _load_client_module():
    requests_module = types.ModuleType("requests")
    requests_module.Session = object
    requests_module.Response = object
    requests_module.RequestException = Exception
    sys.modules["requests"] = requests_module
    spec = importlib.util.spec_from_file_location("infisical_bootstrap_http_client", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load Infisical bootstrap HTTP client module.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CLIENT_MODULE = _load_client_module()
InfisicalBootstrapHttpClient = CLIENT_MODULE.InfisicalBootstrapHttpClient
InfisicalBootstrapUnavailable = CLIENT_MODULE.InfisicalBootstrapUnavailable


class TestInfisicalBootstrapHttpClient(unittest.TestCase):
    def test_posts_documented_bootstrap_payload_and_redacts_token_to_boolean(self):
        session = _FakeSession(
            _FakeResponse(
                200,
                {
                    "identity": {"credentials": {"token": "root-token"}},
                    "organization": {"name": "Tiny Swarm World"},
                    "user": {"email": "admin@tiny-swarm-world.local"},
                },
            )
        )
        client = InfisicalBootstrapHttpClient(
            base_url="https://localhost",
            session=session,
            readiness_interval_seconds=0,
        )

        result = client.bootstrap_instance(
            email="admin@tiny-swarm-world.local",
            password="infisical-password",
            organization="Tiny Swarm World",
        )

        self.assertEqual(InfisicalBootstrapState.CREATED, result.state)
        self.assertTrue(result.token_returned)
        self.assertEqual(
            "https://localhost/api/v1/admin/bootstrap",
            session.post_calls[0]["url"],
        )
        self.assertEqual(
            {
                "email": "admin@tiny-swarm-world.local",
                "password": "infisical-password",
                "organization": "Tiny Swarm World",
            },
            session.post_calls[0]["json"],
        )
        self.assertFalse(session.post_calls[0]["verify"])
        self.assertEqual("https://localhost/api/status", session.get_calls[0]["url"])

    def test_waits_for_infisical_api_before_bootstrap(self):
        session = _FakeSession(
            _FakeResponse(
                200,
                {
                    "identity": {"credentials": {"token": "root-token"}},
                    "organization": {"name": "Tiny Swarm World"},
                    "user": {"email": "admin@tiny-swarm-world.local"},
                },
            ),
            readiness_responses=(
                _FakeResponse(502, {}),
                _FakeResponse(200, {"status": "ok"}),
            ),
        )
        client = InfisicalBootstrapHttpClient(
            base_url="https://localhost",
            session=session,
            readiness_interval_seconds=0,
        )

        result = client.bootstrap_instance(
            email="admin@tiny-swarm-world.local",
            password="infisical-password",
            organization="Tiny Swarm World",
        )

        self.assertEqual(InfisicalBootstrapState.CREATED, result.state)
        self.assertEqual(2, len(session.get_calls))

    def test_raises_redacted_unavailable_when_infisical_api_never_ready(self):
        client = InfisicalBootstrapHttpClient(
            base_url="https://localhost",
            session=_FakeSession(
                _FakeResponse(200, {}),
                readiness_responses=(
                    _FakeResponse(502, {}),
                    _FakeResponse(502, {}),
                ),
            ),
            readiness_attempts=2,
            readiness_interval_seconds=0,
        )

        with self.assertRaises(InfisicalBootstrapUnavailable) as raised:
            client.bootstrap_instance(
                email="admin@tiny-swarm-world.local",
                password="infisical-password",
                organization="Tiny Swarm World",
            )

        self.assertEqual(502, raised.exception.status_code)

    def test_treats_conflict_as_already_initialized_for_idempotent_reruns(self):
        client = InfisicalBootstrapHttpClient(
            base_url="https://localhost",
            session=_FakeSession(_FakeResponse(409, {})),
            readiness_interval_seconds=0,
        )

        result = client.bootstrap_instance(
            email="admin@tiny-swarm-world.local",
            password="infisical-password",
            organization="Tiny Swarm World",
        )

        self.assertEqual(InfisicalBootstrapState.ALREADY_INITIALIZED, result.state)
        self.assertFalse(result.token_returned)

    def test_rejects_secret_bearing_base_url(self):
        with self.assertRaises(ValueError):
            InfisicalBootstrapHttpClient(base_url="https://admin:secret@localhost")


class _FakeSession:
    def __init__(
        self,
        response: "_FakeResponse",
        readiness_responses: tuple["_FakeResponse", ...] | None = None,
    ):
        self.response = response
        self.readiness_responses = list(readiness_responses or (_FakeResponse(200, {}),))
        self.get_calls: list[dict[str, object]] = []
        self.post_calls: list[dict[str, object]] = []

    def get(self, url: str, **kwargs):
        self.get_calls.append({"url": url, **kwargs})
        if self.readiness_responses:
            return self.readiness_responses.pop(0)
        return _FakeResponse(200, {})

    def post(self, url: str, **kwargs):
        self.post_calls.append({"url": url, **kwargs})
        return self.response


class _FakeResponse:
    def __init__(self, status_code: int, payload: object):
        self.status_code = status_code
        self.payload = payload

    def json(self):
        return self.payload


if __name__ == "__main__":
    unittest.main()
