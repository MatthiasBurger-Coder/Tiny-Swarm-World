import unittest
from tests.support.async_helpers import async_checkpoint
from tests.support.sonar_safe_literals import sample_text, sensitive_assignment

from tiny_swarm_world.application.services.nexus.ensure_nexus_repository import (
    EnsureNexusDockerHostedRepository,
    EnsureNexusMavenProxyRepository,
    NexusDockerHostedRepositoryConfiguration,
    NexusMavenProxyRepositoryConfiguration,
)
from tiny_swarm_world.domain.inventory import VerificationStatus


class TestEnsureNexusDockerHostedRepository(unittest.IsolatedAsyncioTestCase):
    async def test_creates_missing_docker_hosted_repository_then_verifies(self):
        nexus_client = _FakeNexusClient(repository_exists_results=[False, True])
        operator_value = sample_text("operator", "-supplied")
        configuration = NexusDockerHostedRepositoryConfiguration(
            repository_name="docker-hosted",
            http_port=5000,
            admin_username="admin",
            admin_password=operator_value,
        )
        service = EnsureNexusDockerHostedRepository(nexus_client, configuration)

        await service.run()
        verification = await service.verify()

        self.assertEqual(
            [("admin", operator_value, "docker-hosted", 5000)],
            nexus_client.created_docker_repositories,
        )
        self.assertEqual(VerificationStatus.VERIFIED, verification.status)
        self.assertEqual("docker-hosted", verification.evidence["repository_name"])
        self.assertNotIn(operator_value, str(verification.to_dict()))

    async def test_updates_existing_docker_hosted_repository(self):
        nexus_client = _FakeNexusClient(repository_exists_results=[True])
        operator_value = sample_text("operator", "-supplied")
        configuration = NexusDockerHostedRepositoryConfiguration(
            repository_name="docker-hosted",
            http_port=5000,
            admin_username="admin",
            admin_password=operator_value,
        )
        service = EnsureNexusDockerHostedRepository(nexus_client, configuration)

        await service.run()

        self.assertEqual([], nexus_client.created_docker_repositories)
        self.assertEqual(
            [("admin", operator_value, "docker-hosted", 5000)],
            nexus_client.updated_docker_repositories,
        )

    async def test_verification_failure_is_sanitized(self):
        nexus_client = _FakeNexusClient(repository_exists_exception=RuntimeError(sensitive_assignment()))
        operator_value = sample_text("operator", "-supplied")
        configuration = NexusDockerHostedRepositoryConfiguration(
            repository_name="docker-hosted",
            http_port=5000,
            admin_username="admin",
            admin_password=operator_value,
        )
        service = EnsureNexusDockerHostedRepository(nexus_client, configuration)

        verification = await service.verify()

        self.assertEqual(VerificationStatus.FAILED_TO_VERIFY, verification.status)
        self.assertIn("RuntimeError", verification.message)
        self.assertNotIn("secret", verification.message)
        self.assertNotIn(operator_value, str(verification.to_dict()))


class TestEnsureNexusMavenProxyRepository(unittest.IsolatedAsyncioTestCase):
    async def test_creates_missing_maven_proxy_repository_then_verifies(self):
        nexus_client = _FakeNexusClient(repository_exists_results=[False, True])
        operator_value = sample_text("operator", "-supplied")
        configuration = NexusMavenProxyRepositoryConfiguration(
            repository_name="maven-central",
            remote_url="https://repo.maven.apache.org/maven2/",
            admin_username="admin",
            admin_password=operator_value,
        )
        service = EnsureNexusMavenProxyRepository(nexus_client, configuration)

        await service.run()
        verification = await service.verify()

        self.assertEqual(
            [
                (
                    "admin",
                    operator_value,
                    "maven-central",
                    "https://repo.maven.apache.org/maven2/",
                )
            ],
            nexus_client.created_maven_repositories,
        )
        self.assertEqual(VerificationStatus.VERIFIED, verification.status)
        self.assertEqual("maven_proxy", verification.evidence["repository_type"])

    async def test_rejects_missing_operator_supplied_password(self):
        await async_checkpoint()
        with self.assertRaises(ValueError):
            NexusMavenProxyRepositoryConfiguration(
                repository_name="maven-central",
                remote_url="https://repo.maven.apache.org/maven2/",
                admin_username="admin",
                admin_password="",
            )


class _FakeNexusClient:
    def __init__(
        self,
        repository_exists_results: list[bool] | None = None,
        repository_exists_exception: Exception | None = None,
    ):
        self.repository_exists_results = list(repository_exists_results or [])
        self.repository_exists_exception = repository_exists_exception
        self.created_docker_repositories: list[tuple[str, str, str, int]] = []
        self.updated_docker_repositories: list[tuple[str, str, str, int]] = []
        self.created_maven_repositories: list[tuple[str, str, str, str]] = []

    def repository_exists(self, username: str, password: str, repository_name: str) -> bool:
        if self.repository_exists_exception:
            raise self.repository_exists_exception
        if self.repository_exists_results:
            return self.repository_exists_results.pop(0)
        return False

    def create_docker_hosted_repository(
        self,
        username: str,
        password: str,
        repository_name: str,
        http_port: int,
    ) -> None:
        self.created_docker_repositories.append((username, password, repository_name, http_port))

    def update_docker_hosted_repository(
        self,
        username: str,
        password: str,
        repository_name: str,
        http_port: int,
    ) -> None:
        self.updated_docker_repositories.append((username, password, repository_name, http_port))

    def create_maven_proxy_repository(
        self,
        username: str,
        password: str,
        repository_name: str,
        remote_url: str,
    ) -> None:
        self.created_maven_repositories.append((username, password, repository_name, remote_url))
