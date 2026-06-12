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
            request_responses=[_swarm_info_response(), _FakeResponse(200, {})],
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
        self.assertEqual(
            "http://portainer.local/api/endpoints/1/docker/info",
            session.request_calls[0]["url"],
        )
        self.assertEqual("portainer", session.request_calls[1]["json"]["name"])
        self.assertEqual("swarm-cluster-id", session.request_calls[1]["json"]["SwarmID"])

    def test_create_stack_sends_allowlisted_stack_environment(self):
        session = _FakeSession(
            post_responses=[_FakeResponse(200, {"jwt": "jwt-token"})],
            request_responses=[_swarm_info_response(), _FakeResponse(200, {})],
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
            session.request_calls[1]["json"]["env"],
        )

    def test_create_stack_uses_extended_stack_request_timeout(self):
        session = _FakeSession(
            post_responses=[_FakeResponse(200, {"jwt": "jwt-token"})],
            request_responses=[_swarm_info_response(), _FakeResponse(200, {})],
        )
        client = PortainerHttpClient(
            "http://portainer.local",
            "admin",
            OPERATOR_CREDENTIAL,
            session=session,
            request_timeout_seconds=11,
            stack_request_timeout_seconds=181,
        )

        client.create_stack(StackDefinition(name="swagger", compose_content="services: {}"), 1)

        self.assertEqual(11, session.post_calls[0]["timeout"])
        self.assertEqual(11, session.request_calls[0]["timeout"])
        self.assertEqual(181, session.request_calls[1]["timeout"])

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
        self.assertEqual(1, session.cookies.clear_count)

    def test_api_request_reauthenticates_once_after_unauthorized_response(self):
        session = _FakeSession(
            post_responses=[
                _FakeResponse(200, {"jwt": "expired-token"}),
                _FakeResponse(200, {"jwt": "fresh-token"}),
            ],
            request_responses=[
                _FakeResponse(401, {}),
                _FakeResponse(200, [{"Name": "local", "Id": 7}]),
            ],
        )
        client = PortainerHttpClient(
            "http://portainer.local",
            "admin",
            OPERATOR_CREDENTIAL,
            session=session,
        )

        self.assertEqual(7, client.get_endpoint_id_by_name("local"))

        self.assertEqual(2, len(session.post_calls))
        self.assertEqual(
            "Bearer expired-token",
            session.request_calls[0]["headers"]["Authorization"],
        )
        self.assertEqual(
            "Bearer fresh-token",
            session.request_calls[1]["headers"]["Authorization"],
        )

    def test_authentication_clears_cookie_auth_before_endpoint_creation(self):
        session = _FakeSession(
            post_responses=[_FakeResponse(200, {"jwt": "jwt-token"})],
            request_responses=[
                _FakeResponse(200, []),
                _FakeResponse(200, {}),
                _FakeResponse(200, [{"Name": "local", "Id": 7}]),
            ],
        )
        client = PortainerHttpClient(
            "http://portainer.local",
            "admin",
            OPERATOR_CREDENTIAL,
            session=session,
        )

        self.assertEqual(7, client.ensure_local_endpoint("local"))

        self.assertEqual(1, session.cookies.clear_count)
        self.assertEqual("POST", session.request_calls[1]["method"])
        self.assertEqual("Bearer jwt-token", session.request_calls[1]["headers"]["Authorization"])

    def test_local_endpoint_request_accepts_primary_portainer_endpoint_alias(self):
        session = _FakeSession(
            post_responses=[_FakeResponse(200, {"jwt": "jwt-token"})],
            request_responses=[_FakeResponse(200, [{"Name": "primary", "Id": 11}])],
        )
        client = PortainerHttpClient(
            "http://portainer.local",
            "admin",
            OPERATOR_CREDENTIAL,
            session=session,
        )

        self.assertEqual(11, client.get_endpoint_id_by_name("local"))

    def test_local_endpoint_request_accepts_single_socket_backed_endpoint(self):
        session = _FakeSession(
            post_responses=[_FakeResponse(200, {"jwt": "jwt-token"})],
            request_responses=[
                _FakeResponse(
                    200,
                    [{"Name": "docker-env", "Id": 12, "URL": "unix:///var/run/docker.sock"}],
                )
            ],
        )
        client = PortainerHttpClient(
            "http://portainer.local",
            "admin",
            OPERATOR_CREDENTIAL,
            session=session,
        )

        self.assertEqual(12, client.get_endpoint_id_by_name("local"))

    def test_ensure_local_endpoint_returns_existing_endpoint(self):
        session = _FakeSession(
            post_responses=[_FakeResponse(200, {"jwt": "jwt-token"})],
            request_responses=[_FakeResponse(200, [{"Name": "local", "Id": 7}])],
        )
        client = PortainerHttpClient(
            "http://portainer.local",
            "admin",
            OPERATOR_CREDENTIAL,
            session=session,
        )

        self.assertEqual(7, client.ensure_local_endpoint("local"))
        self.assertEqual(1, len(session.request_calls))

    def test_ensure_local_endpoint_creates_socket_endpoint_when_missing(self):
        session = _FakeSession(
            post_responses=[_FakeResponse(200, {"jwt": "jwt-token"})],
            request_responses=[
                _FakeResponse(200, []),
                _FakeResponse(200, {}),
                _FakeResponse(
                    200,
                    [{"Name": "local", "Id": 17, "URL": "unix:///var/run/docker.sock"}],
                ),
            ],
        )
        client = PortainerHttpClient(
            "http://portainer.local",
            "admin",
            OPERATOR_CREDENTIAL,
            session=session,
        )

        self.assertEqual(17, client.ensure_local_endpoint("local"))
        create_call = session.request_calls[1]
        self.assertEqual("POST", create_call["method"])
        self.assertEqual("http://portainer.local/api/endpoints", create_call["url"])
        self.assertEqual(
            {
                "Name": (None, "local"),
                "EndpointCreationType": (None, "1"),
                "ContainerEngine": (None, "docker"),
                "URL": (None, "unix:///var/run/docker.sock"),
            },
            create_call["files"],
        )

    def test_ensure_local_endpoint_reports_creation_failure_without_response_body(self):
        session = _FakeSession(
            post_responses=[_FakeResponse(200, {"jwt": "jwt-token"})],
            request_responses=[
                _FakeResponse(200, []),
                _FakeResponse(500, {"message": "token=secret"}),
            ],
        )
        client = PortainerHttpClient(
            "http://portainer.local",
            "admin",
            OPERATOR_CREDENTIAL,
            session=session,
        )

        with self.assertRaises(RuntimeError) as raised:
            client.ensure_local_endpoint("local")

        self.assertIn("HTTP 500", str(raised.exception))
        self.assertNotIn("token=secret", str(raised.exception))

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
        self.assertIn("Available endpoints: remote", str(raised.exception))

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
            request_responses=[
                _swarm_info_response(),
                _FakeResponse(404, {}),
                _FakeResponse(200, {}),
            ],
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
            session.request_calls[1]["url"],
        )
        self.assertEqual("http://portainer.local/api/stacks", session.request_calls[2]["url"])
        self.assertEqual(7, session.request_calls[2]["json"]["endpointId"])
        self.assertEqual("swarm-cluster-id", session.request_calls[2]["json"]["SwarmID"])

    def test_create_stack_requires_swarm_identity(self):
        session = _FakeSession(
            post_responses=[_FakeResponse(200, {"jwt": "jwt-token"})],
            request_responses=[_FakeResponse(200, {"Swarm": {"Cluster": {}}})],
        )
        client = PortainerHttpClient(
            "http://portainer.local",
            "admin",
            OPERATOR_CREDENTIAL,
            session=session,
        )

        with self.assertRaises(RuntimeError) as raised:
            client.create_stack(StackDefinition(name="jenkins", compose_content="services: {}"), 7)

        self.assertIn("Swarm cluster ID", str(raised.exception))
        self.assertEqual(1, len(session.request_calls))

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

    def test_update_stack_uses_extended_stack_request_timeout(self):
        session = _FakeSession(
            post_responses=[_FakeResponse(200, {"jwt": "jwt-token"})],
            request_responses=[_FakeResponse(200, {})],
        )
        client = PortainerHttpClient(
            "http://portainer.local",
            "admin",
            OPERATOR_CREDENTIAL,
            session=session,
            stack_request_timeout_seconds=181,
        )

        client.update_stack(42, StackDefinition(name="swagger", compose_content="services: {}"), 7)

        self.assertEqual(181, session.request_calls[0]["timeout"])

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


def _swarm_info_response() -> _FakeResponse:
    return _FakeResponse(200, {"Swarm": {"Cluster": {"ID": "swarm-cluster-id"}}})


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
        self.cookies = _FakeCookies()

    def post(self, url: str, **kwargs: object) -> _FakeResponse:
        self.post_calls.append({"url": url, **kwargs})
        return self.post_responses.pop(0)

    def request(self, method: str, url: str, **kwargs: object) -> _FakeResponse:
        self.request_calls.append({"method": method, "url": url, **kwargs})
        return self.request_responses.pop(0)


class _FakeCookies:
    def __init__(self) -> None:
        self.clear_count = 0

    def clear(self) -> None:
        self.clear_count += 1


if __name__ == "__main__":
    unittest.main()
