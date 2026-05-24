from __future__ import annotations

from dataclasses import dataclass, field

from tiny_swarm_world.application.ports.clients.port_nexus_client import PortNexusClient
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus


@dataclass(frozen=True)
class NexusDockerHostedRepositoryConfiguration:
    repository_name: str
    http_port: int
    admin_username: str
    admin_password: str = field(repr=False)

    def __post_init__(self) -> None:
        _validate_repository_name(self.repository_name)
        if self.http_port <= 0 or self.http_port > 65535:
            raise ValueError("Nexus Docker hosted repository port must be a valid TCP port.")
        if not self.admin_username:
            raise ValueError("Nexus admin username must not be empty.")
        if not self.admin_password:
            raise ValueError("Nexus admin password must be supplied by the operator.")


@dataclass(frozen=True)
class NexusMavenProxyRepositoryConfiguration:
    repository_name: str
    remote_url: str
    admin_username: str
    admin_password: str = field(repr=False)

    def __post_init__(self) -> None:
        _validate_repository_name(self.repository_name)
        if not self.remote_url.startswith(("http://", "https://")):
            raise ValueError("Nexus Maven proxy remote URL must be HTTP or HTTPS.")
        if not self.admin_username:
            raise ValueError("Nexus admin username must not be empty.")
        if not self.admin_password:
            raise ValueError("Nexus admin password must be supplied by the operator.")


class EnsureNexusDockerHostedRepository:
    verification_target_id = "artifacts:nexus-docker-hosted-repository"

    def __init__(
        self,
        nexus_client: PortNexusClient,
        configuration: NexusDockerHostedRepositoryConfiguration,
    ):
        self.nexus_client = nexus_client
        self.configuration = configuration

    async def run(self) -> None:
        if self._repository_exists():
            return
        self.nexus_client.create_docker_hosted_repository(
            self.configuration.admin_username,
            self.configuration.admin_password,
            self.configuration.repository_name,
            self.configuration.http_port,
        )

    async def verify(self) -> VerificationResult:
        try:
            repository_exists = self._repository_exists()
        except Exception as exc:
            return VerificationResult(
                target_id=self.verification_target_id,
                status=VerificationStatus.FAILED_TO_VERIFY,
                message=f"Nexus Docker hosted repository verification failed: {exc.__class__.__name__}",
                evidence=_docker_repository_evidence(self.configuration, exists="unknown"),
            )

        if repository_exists:
            return VerificationResult(
                target_id=self.verification_target_id,
                status=VerificationStatus.VERIFIED,
                message="Nexus Docker hosted repository is available.",
                evidence=_docker_repository_evidence(self.configuration, exists="true"),
            )
        return VerificationResult(
            target_id=self.verification_target_id,
            status=VerificationStatus.FAILED_TO_VERIFY,
            message="Nexus Docker hosted repository is missing.",
            evidence=_docker_repository_evidence(self.configuration, exists="false"),
        )

    def _repository_exists(self) -> bool:
        return self.nexus_client.repository_exists(
            self.configuration.admin_username,
            self.configuration.admin_password,
            self.configuration.repository_name,
        )


class EnsureNexusMavenProxyRepository:
    verification_target_id = "artifacts:nexus-maven-proxy-repository"

    def __init__(
        self,
        nexus_client: PortNexusClient,
        configuration: NexusMavenProxyRepositoryConfiguration,
    ):
        self.nexus_client = nexus_client
        self.configuration = configuration

    async def run(self) -> None:
        if self._repository_exists():
            return
        self.nexus_client.create_maven_proxy_repository(
            self.configuration.admin_username,
            self.configuration.admin_password,
            self.configuration.repository_name,
            self.configuration.remote_url,
        )

    async def verify(self) -> VerificationResult:
        try:
            repository_exists = self._repository_exists()
        except Exception as exc:
            return VerificationResult(
                target_id=self.verification_target_id,
                status=VerificationStatus.FAILED_TO_VERIFY,
                message=f"Nexus Maven proxy repository verification failed: {exc.__class__.__name__}",
                evidence=_maven_repository_evidence(self.configuration, exists="unknown"),
            )

        if repository_exists:
            return VerificationResult(
                target_id=self.verification_target_id,
                status=VerificationStatus.VERIFIED,
                message="Nexus Maven proxy repository is available.",
                evidence=_maven_repository_evidence(self.configuration, exists="true"),
            )
        return VerificationResult(
            target_id=self.verification_target_id,
            status=VerificationStatus.FAILED_TO_VERIFY,
            message="Nexus Maven proxy repository is missing.",
            evidence=_maven_repository_evidence(self.configuration, exists="false"),
        )

    def _repository_exists(self) -> bool:
        return self.nexus_client.repository_exists(
            self.configuration.admin_username,
            self.configuration.admin_password,
            self.configuration.repository_name,
        )


def _validate_repository_name(repository_name: str) -> None:
    if not repository_name or any(character.isspace() for character in repository_name):
        raise ValueError("Nexus repository name must be a non-empty token.")


def _docker_repository_evidence(
    configuration: NexusDockerHostedRepositoryConfiguration,
    *,
    exists: str,
) -> dict[str, str]:
    return {
        "exists": exists,
        "phase": "verify",
        "repository_name": configuration.repository_name,
        "repository_type": "docker_hosted",
        "registry_port": str(configuration.http_port),
    }


def _maven_repository_evidence(
    configuration: NexusMavenProxyRepositoryConfiguration,
    *,
    exists: str,
) -> dict[str, str]:
    return {
        "exists": exists,
        "phase": "verify",
        "repository_name": configuration.repository_name,
        "repository_type": "maven_proxy",
        "remote_url": configuration.remote_url,
    }
