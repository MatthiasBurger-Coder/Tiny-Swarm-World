import unittest

from tiny_swarm_world.domain.nexus.nexus_user import NexusUser
from tiny_swarm_world.infrastructure.adapters.clients.nexus_http_client import NexusHttpClient


class TestNexusHttpClient(unittest.TestCase):
    def test_rejects_credentials_in_base_url(self):
        with self.assertRaises(ValueError):
            NexusHttpClient("https://admin:secret@nexus.local")

    def test_status_and_authentication_use_nexus_rest_api(self):
        session = _FakeSession(
            get_responses=[
                _FakeResponse(200, {}),
                _FakeResponse(200, []),
            ],
        )
        client = NexusHttpClient("http://nexus.local", session=session)

        self.assertTrue(client.is_available())
        self.assertTrue(client.can_authenticate("admin", "operator-password"))

        self.assertEqual("http://nexus.local/service/rest/v1/status", session.get_calls[0]["url"])
        self.assertEqual(
            "http://nexus.local/service/rest/v1/security/users",
            session.get_calls[1]["url"],
        )
        self.assertEqual(("admin", "operator-password"), session.get_calls[1]["auth"])

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

        user = client.get_user("admin", "initial-password", "admin")
        client.update_user("admin", "initial-password", user.model_copy(update={"status": "active"}))
        client.change_password("admin", "initial-password", "admin", "operator-password")
        client.set_anonymous_access("admin", "operator-password", enabled=False)

        self.assertIsInstance(user, NexusUser)
        self.assertEqual("active", session.put_calls[0]["json"]["status"])
        self.assertEqual("operator-password", session.put_calls[1]["data"])
        self.assertEqual({"enabled": False}, session.put_calls[2]["json"])

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

        self.assertTrue(client.repository_exists("admin", "operator-password", "docker-hosted"))

        self.assertEqual(
            "http://nexus.local/service/rest/v1/repositories",
            session.get_calls[0]["url"],
        )

    def test_create_docker_hosted_repository_uses_repository_contract_payload(self):
        session = _FakeSession(post_responses=[_FakeResponse(201, {})])
        client = NexusHttpClient("http://nexus.local", session=session)

        client.create_docker_hosted_repository("admin", "operator-password", "docker-hosted", 5000)

        request = session.post_calls[0]
        self.assertEqual(
            "http://nexus.local/service/rest/v1/repositories/docker/hosted",
            request["url"],
        )
        self.assertEqual("docker-hosted", request["json"]["name"])
        self.assertEqual(5000, request["json"]["docker"]["httpPort"])
        self.assertTrue(request["json"]["docker"]["forceBasicAuth"])

    def test_create_maven_proxy_repository_uses_repository_contract_payload(self):
        session = _FakeSession(post_responses=[_FakeResponse(201, {})])
        client = NexusHttpClient("http://nexus.local", session=session)

        client.create_maven_proxy_repository(
            "admin",
            "operator-password",
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
            client.repository_exists("admin", "operator-password", "docker-hosted")

        self.assertIn("HTTP 500", str(raised.exception))
        self.assertNotIn("token=secret", str(raised.exception))
        self.assertNotIn("operator-password", str(raised.exception))


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
        get_responses: list[_FakeResponse] | None = None,
        put_responses: list[_FakeResponse] | None = None,
        post_responses: list[_FakeResponse] | None = None,
    ):
        self.get_responses = list(get_responses or [])
        self.put_responses = list(put_responses or [])
        self.post_responses = list(post_responses or [])
        self.get_calls: list[dict[str, object]] = []
        self.put_calls: list[dict[str, object]] = []
        self.post_calls: list[dict[str, object]] = []

    def get(self, url: str, **kwargs: object) -> _FakeResponse:
        self.get_calls.append({"url": url, **kwargs})
        return self.get_responses.pop(0)

    def put(self, url: str, **kwargs: object) -> _FakeResponse:
        self.put_calls.append({"url": url, **kwargs})
        return self.put_responses.pop(0)

    def post(self, url: str, **kwargs: object) -> _FakeResponse:
        self.post_calls.append({"url": url, **kwargs})
        return self.post_responses.pop(0)
