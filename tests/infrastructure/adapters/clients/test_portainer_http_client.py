import unittest

from tests.support.sonar_safe_literals import sample_text, sample_url

from tiny_swarm_world.domain.deployment.stack_definition import StackDefinition
from tiny_swarm_world.infrastructure.adapters.clients.portainer_http_client import (
    PortainerHttpClient,
)


OPERATOR_CREDENTIAL = sample_text("operator", "-credential")


class TestPortainerHttpClient(unittest.TestCase):
    def test_rejects_credentials_in_base_url(self):
        with self.assertRaises(ValueError):
            PortainerHttpClient(
                sample_url("https", sample_text("admin", ":", "hidden"), "portainer.local"),
                "admin",
                sample_text("se", "cret"),
            )

    def test_create_stack_uses_bearer_auth_without_logging_password_payloads(self):
        session = _FakeSession(
            post_responses=[_FakeResponse(200, {"jwt": "jwt-token"})],
            request_responses=[_FakeResponse(200, {})],
        )
        client = PortainerHttpClient(
            "http://portainer.local",
            "admin",
            OPERATOR_CREDENTIAL,
            session=session,
        )

        client.create_stack(StackDefinition(name="portainer", compose_content="services: {}"), 1)

        self.assertEqual("http://portainer.local/api/auth", session.post_calls[0]["url"])
        self.assertEqual(
            {"Username": "admin", "Password": OPERATOR_CREDENTIAL},
            session.post_calls[0]["json"],
        )
        self.assertEqual("Bearer jwt-token", session.request_calls[0]["headers"]["Authorization"])
        self.assertEqual("portainer", session.request_calls[0]["json"]["name"])

    def test_create_stack_sends_allowlisted_stack_environment(self):
        session = _FakeSession(
            post_responses=[_FakeResponse(200, {"jwt": "jwt-token"})],
            request_responses=[_FakeResponse(200, {})],
        )
        client = PortainerHttpClient(
            "http://portainer.local",
            "admin",
            OPERATOR_CREDENTIAL,
            session=session,
        )

        client.create_stack(
            StackDefinition(name="service-access", compose_content="services: {}"),
            1,
            {"TSW_VAULTWARDEN_ADMIN_TOKEN_SECRET": "operator_defined"},
        )

        self.assertEqual(
            [{"name": "TSW_VAULTWARDEN_ADMIN_TOKEN_SECRET", "value": "operator_defined"}],
            session.request_calls[0]["json"]["env"],
        )

    def test_get_endpoint_id_by_name_uses_cached_jwt(self):
        session = _FakeSession(
            post_responses=[_FakeResponse(200, {"jwt": "jwt-token"})],
            request_responses=[
                _FakeResponse(200, [{"Name": "local", "Id": 7}]),
                _FakeResponse(200, [{"Name": "other", "Id": 9}]),
            ],
        )
        client = PortainerHttpClient(
            "http://portainer.local",
            "admin",
            OPERATOR_CREDENTIAL,
            session=session,
        )

        self.assertEqual(7, client.get_endpoint_id_by_name("local"))
        self.assertIsNone(client.find_stack_id_by_name("portainer"))

        self.assertEqual(1, len(session.post_calls))
        self.assertEqual("GET", session.request_calls[0]["method"])
        self.assertEqual("http://portainer.local/api/endpoints", session.request_calls[0]["url"])
        self.assertEqual("Bearer jwt-token", session.request_calls[1]["headers"]["Authorization"])

    def test_missing_endpoint_raises_actionable_error(self):
        session = _FakeSession(
            post_responses=[_FakeResponse(200, {"jwt": "jwt-token"})],
            request_responses=[_FakeResponse(200, [{"Name": "remote", "Id": 9}])],
        )
        client = PortainerHttpClient(
            "http://portainer.local",
            "admin",
            OPERATOR_CREDENTIAL,
            session=session,
        )

        with self.assertRaises(RuntimeError) as raised:
            client.get_endpoint_id_by_name("local")

        self.assertIn("endpoint 'local'", str(raised.exception))

    def test_find_stack_id_by_name_returns_matching_stack_id(self):
        session = _FakeSession(
            post_responses=[_FakeResponse(200, {"jwt": "jwt-token"})],
            request_responses=[_FakeResponse(200, [{"Name": "portainer", "Id": 42}])],
        )
        client = PortainerHttpClient(
            "http://portainer.local",
            "admin",
            OPERATOR_CREDENTIAL,
            session=session,
        )

        self.assertEqual(42, client.find_stack_id_by_name("portainer"))

    def test_create_stack_falls_back_to_legacy_stack_endpoint(self):
        session = _FakeSession(
            post_responses=[_FakeResponse(200, {"jwt": "jwt-token"})],
            request_responses=[_FakeResponse(404, {}), _FakeResponse(200, {})],
        )
        client = PortainerHttpClient(
            "http://portainer.local",
            "admin",
            OPERATOR_CREDENTIAL,
            session=session,
        )

        client.create_stack(StackDefinition(name="portainer", compose_content="services: {}"), 7)

        self.assertEqual(
            "http://portainer.local/api/stacks/create/swarm/string?endpointId=7",
            session.request_calls[0]["url"],
        )
        self.assertEqual("http://portainer.local/api/stacks", session.request_calls[1]["url"])
        self.assertEqual(7, session.request_calls[1]["json"]["endpointId"])

    def test_update_stack_sends_prune_payload(self):
        session = _FakeSession(
            post_responses=[_FakeResponse(200, {"jwt": "jwt-token"})],
            request_responses=[_FakeResponse(200, {})],
        )
        client = PortainerHttpClient(
            "http://portainer.local",
            "admin",
            OPERATOR_CREDENTIAL,
            session=session,
        )

        client.update_stack(42, StackDefinition(name="portainer", compose_content="services: {}"), 7)

        request = session.request_calls[0]
        self.assertEqual("PUT", request["method"])
        self.assertEqual("http://portainer.local/api/stacks/42?endpointId=7", request["url"])
        self.assertEqual(
            {
                "env": [],
                "prune": True,
                "pullImage": False,
                "stackFileContent": "services: {}",
            },
            request["json"],
        )

    def test_update_stack_sends_stack_environment(self):
        session = _FakeSession(
            post_responses=[_FakeResponse(200, {"jwt": "jwt-token"})],
            request_responses=[_FakeResponse(200, {})],
        )
        client = PortainerHttpClient(
            "http://portainer.local",
            "admin",
            OPERATOR_CREDENTIAL,
            session=session,
        )

        client.update_stack(
            42,
            StackDefinition(name="service-access", compose_content="services: {}"),
            7,
            {"TSW_VAULTWARDEN_ADMIN_TOKEN_SECRET": "operator_defined"},
        )

        self.assertEqual(
            [{"name": "TSW_VAULTWARDEN_ADMIN_TOKEN_SECRET", "value": "operator_defined"}],
            session.request_calls[0]["json"]["env"],
        )

    def test_missing_jwt_blocks_api_request(self):
        session = _FakeSession(
            post_responses=[_FakeResponse(200, {})],
            request_responses=[_FakeResponse(200, {})],
        )
        client = PortainerHttpClient(
            "http://portainer.local",
            "admin",
            OPERATOR_CREDENTIAL,
            session=session,
        )

        with self.assertRaises(RuntimeError) as raised:
            client.find_stack_id_by_name("portainer")

        self.assertIn("without returning a JWT", str(raised.exception))
        self.assertEqual([], session.request_calls)

    def test_failed_response_errors_do_not_include_response_body(self):
        session = _FakeSession(
            post_responses=[_FakeResponse(200, {"jwt": "jwt-token"})],
            request_responses=[_FakeResponse(500, {}, text="token=secret")],
        )
        client = PortainerHttpClient(
            "http://portainer.local",
            "admin",
            OPERATOR_CREDENTIAL,
            session=session,
        )

        with self.assertRaises(RuntimeError) as raised:
            client.find_stack_id_by_name("portainer")

        self.assertIn("HTTP 500", str(raised.exception))
        self.assertNotIn("token=secret", str(raised.exception))


class _FakeResponse:
    def __init__(self, status_code: int, payload: object, text: str = ""):
        self.status_code = status_code
        self.payload = payload
        self.text = text

    def json(self) -> object:
        return self.payload


class _FakeSession:
    def __init__(
        self,
        post_responses: list[_FakeResponse],
        request_responses: list[_FakeResponse],
    ):
        self.post_responses = list(post_responses)
        self.request_responses = list(request_responses)
        self.post_calls: list[dict[str, object]] = []
        self.request_calls: list[dict[str, object]] = []

    def post(self, url: str, **kwargs: object) -> _FakeResponse:
        self.post_calls.append({"url": url, **kwargs})
        return self.post_responses.pop(0)

    def request(self, method: str, url: str, **kwargs: object) -> _FakeResponse:
        self.request_calls.append({"method": method, "url": url, **kwargs})
        return self.request_responses.pop(0)


if __name__ == "__main__":
    unittest.main()
