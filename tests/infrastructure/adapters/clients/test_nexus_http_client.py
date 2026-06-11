import unittest

import requests

from tests.support.sonar_safe_literals import sample_text, sample_url

from tiny_swarm_world.domain.nexus.nexus_user import NexusUser
from tiny_swarm_world.infrastructure.adapters.clients.nexus_http_client import NexusHttpClient


OPERATOR_CREDENTIAL = sample_text("operator", "-credential")
INITIAL_CREDENTIAL = sample_text("initial", "-credential")


class TestNexusHttpClient(unittest.TestCase):
    def test_rejects_credentials_in_base_url(self):
        with self.assertRaises(ValueError):
            NexusHttpClient(
                sample_url("https", sample_text("admin", ":", "hidden"), "nexus.local")
            )

    def test_status_and_authentication_use_nexus_rest_api(self):
        session = _FakeSession(
            get_responses=[
                _FakeResponse(200, {}),
                _FakeResponse(200, []),
            ],
        )
        client = NexusHttpClient("http://nexus.local", session=session)

        self.assertTrue(client.is_available())
        self.assertTrue(client.can_authenticate("admin", OPERATOR_CREDENTIAL))

        self.assertEqual("http://nexus.local/service/rest/v1/status", session.get_calls[0]["url"])
        self.assertEqual(
            "http://nexus.local/service/rest/v1/security/users",
            session.get_calls[1]["url"],
        )
        self.assertEqual(("admin", OPERATOR_CREDENTIAL), session.get_calls[1]["auth"])

    def test_status_and_authentication_handle_transport_failures(self):
        session = _FakeSession(
            get_responses=[
                requests.ConnectionError("connection reset"),
                requests.Timeout("timeout"),
            ],
        )
        client = NexusHttpClient("http://nexus.local", session=session)

        self.assertFalse(client.is_available())
        self.assertFalse(client.can_authenticate("admin", OPERATOR_CREDENTIAL))

    def test_user_and_password_operations_are_sanitized_http_calls(self):
        session = _FakeSession(
            get_responses=[
                _FakeResponse(
                    200,
                    [
                        {
                            "userId": "admin",
                            "status": "disabled",
                            "roles": ["nx-admin"],
                        }
                    ],
                )
            ],
            put_responses=[
                _FakeResponse(204, {}),
                _FakeResponse(204, {}),
                _FakeResponse(204, {}),
            ],
        )
        client = NexusHttpClient("http://nexus.local", session=session)

        user = client.get_user("admin", INITIAL_CREDENTIAL, "admin")
        client.update_user("admin", INITIAL_CREDENTIAL, user.model_copy(update={"status": "active"}))
        client.change_password("admin", INITIAL_CREDENTIAL, "admin", OPERATOR_CREDENTIAL)
        client.set_anonymous_access("admin", OPERATOR_CREDENTIAL, enabled=False)

        self.assertIsInstance(user, NexusUser)
        self.assertEqual("active", session.put_calls[0]["json"]["status"])
        self.assertEqual(OPERATOR_CREDENTIAL, session.put_calls[1]["data"])
        self.assertEqual({"enabled": False}, session.put_calls[2]["json"])

    def test_user_operations_redact_transport_failure_details(self):
        leaked_value = sample_text("token", "=hidden")
        session = _FakeSession(get_responses=[requests.ConnectionError(leaked_value)])
        client = NexusHttpClient("http://nexus.local", session=session)

        with self.assertRaises(RuntimeError) as raised:
            client.get_user("admin", INITIAL_CREDENTIAL, "admin")

        self.assertNotIn(leaked_value, str(raised.exception))
        self.assertNotIn(INITIAL_CREDENTIAL, str(raised.exception))

    def test_repository_exists_reads_repository_listing(self):
        session = _FakeSession(
            get_responses=[
                _FakeResponse(
                    200,
                    [
                        {"name": "maven-central", "type": "proxy"},
                        {"name": "docker-hosted", "type": "hosted"},
                    ],
                )
            ],
        )
        client = NexusHttpClient("http://nexus.local", session=session)

        self.assertTrue(client.repository_exists("admin", OPERATOR_CREDENTIAL, "docker-hosted"))

        self.assertEqual(
            "http://nexus.local/service/rest/v1/repositories",
            session.get_calls[0]["url"],
        )

    def test_create_docker_hosted_repository_uses_repository_contract_payload(self):
        session = _FakeSession(post_responses=[_FakeResponse(201, {})])
        client = NexusHttpClient("http://nexus.local", session=session)

        client.create_docker_hosted_repository("admin", OPERATOR_CREDENTIAL, "docker-hosted", 5000)

        request = session.post_calls[0]
        self.assertEqual(
            "http://nexus.local/service/rest/v1/repositories/docker/hosted",
            request["url"],
        )
        self.assertEqual("docker-hosted", request["json"]["name"])
        self.assertEqual(5000, request["json"]["docker"]["httpPort"])
        self.assertTrue(request["json"]["docker"]["forceBasicAuth"])
        self.assertEqual("ALLOW", request["json"]["storage"]["writePolicy"])

    def test_update_docker_hosted_repository_uses_repository_contract_payload(self):
        session = _FakeSession(put_responses=[_FakeResponse(204, {})])
        client = NexusHttpClient("http://nexus.local", session=session)

        client.update_docker_hosted_repository("admin", OPERATOR_CREDENTIAL, "docker-hosted", 5000)

        request = session.put_calls[0]
        self.assertEqual(
            "http://nexus.local/service/rest/v1/repositories/docker/hosted/docker-hosted",
            request["url"],
        )
        self.assertEqual("docker-hosted", request["json"]["name"])
        self.assertEqual(5000, request["json"]["docker"]["httpPort"])
        self.assertEqual("ALLOW", request["json"]["storage"]["writePolicy"])

    def test_create_docker_proxy_repository_uses_repository_contract_payload(self):
        session = _FakeSession(post_responses=[_FakeResponse(201, {})])
        client = NexusHttpClient("http://nexus.local", session=session)

        client.create_docker_proxy_repository(
            "admin",
            OPERATOR_CREDENTIAL,
            "docker-hub-proxy",
            5001,
            "https://registry-1.docker.io",
        )

        request = session.post_calls[0]
        self.assertEqual(
            "http://nexus.local/service/rest/v1/repositories/docker/proxy",
            request["url"],
        )
        self.assertEqual("docker-hub-proxy", request["json"]["name"])
        self.assertEqual(5001, request["json"]["docker"]["httpPort"])
        self.assertFalse(request["json"]["docker"]["forceBasicAuth"])
        self.assertEqual(
            "https://registry-1.docker.io",
            request["json"]["proxy"]["remoteUrl"],
        )
        self.assertEqual("HUB", request["json"]["dockerProxy"]["indexType"])

    def test_create_maven_proxy_repository_uses_repository_contract_payload(self):
        session = _FakeSession(post_responses=[_FakeResponse(201, {})])
        client = NexusHttpClient("http://nexus.local", session=session)

        client.create_maven_proxy_repository(
            "admin",
            OPERATOR_CREDENTIAL,
            "maven-central",
            "https://repo.maven.apache.org/maven2/",
        )

        request = session.post_calls[0]
        self.assertEqual(
            "http://nexus.local/service/rest/v1/repositories/maven/proxy",
            request["url"],
        )
        self.assertEqual("maven-central", request["json"]["name"])
        self.assertEqual(
            "https://repo.maven.apache.org/maven2/",
            request["json"]["proxy"]["remoteUrl"],
        )

    def test_failed_response_errors_do_not_include_response_body(self):
        session = _FakeSession(
            get_responses=[_FakeResponse(500, {}, text="token=secret")],
        )
        client = NexusHttpClient("http://nexus.local", session=session)

        with self.assertRaises(RuntimeError) as raised:
            client.repository_exists("admin", OPERATOR_CREDENTIAL, "docker-hosted")

        self.assertIn("HTTP 500", str(raised.exception))
        self.assertNotIn("token=secret", str(raised.exception))
        self.assertNotIn(OPERATOR_CREDENTIAL, str(raised.exception))


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
        get_responses: list[_FakeResponse | requests.RequestException] | None = None,
        put_responses: list[_FakeResponse | requests.RequestException] | None = None,
        post_responses: list[_FakeResponse | requests.RequestException] | None = None,
    ):
        self.get_responses = list(get_responses or [])
        self.put_responses = list(put_responses or [])
        self.post_responses = list(post_responses or [])
        self.get_calls: list[dict[str, object]] = []
        self.put_calls: list[dict[str, object]] = []
        self.post_calls: list[dict[str, object]] = []

    def get(self, url: str, **kwargs: object) -> _FakeResponse:
        self.get_calls.append({"url": url, **kwargs})
        return _response_or_raise(self.get_responses.pop(0))

    def put(self, url: str, **kwargs: object) -> _FakeResponse:
        self.put_calls.append({"url": url, **kwargs})
        return _response_or_raise(self.put_responses.pop(0))

    def post(self, url: str, **kwargs: object) -> _FakeResponse:
        self.post_calls.append({"url": url, **kwargs})
        return _response_or_raise(self.post_responses.pop(0))


def _response_or_raise(response: _FakeResponse | requests.RequestException) -> _FakeResponse:
    if isinstance(response, requests.RequestException):
        raise response
    return response
