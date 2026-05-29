from __future__ import annotations

from tiny_swarm_world.application.ports.node_provider import PortContainerDockerRuntime
from tiny_swarm_world.application.services.platform.docker_swarm_lxc_contract import (
    DockerSwarmInLxcContractService,
)
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus
from tiny_swarm_world.domain.node_provider import NodeSpec


class LxcDockerInstallService:
    def __init__(
        self,
        runtime: PortContainerDockerRuntime,
        contract_service: DockerSwarmInLxcContractService | None = None,
    ) -> None:
        self.runtime = runtime
        self.contract_service = contract_service or DockerSwarmInLxcContractService()

    async def ensure_docker_installed(
        self,
        nodes: tuple[NodeSpec, ...],
    ) -> tuple[VerificationResult, ...]:
        results: list[VerificationResult] = []
        for node in nodes:
            readiness = await self.runtime.inspect_docker(node)
            readiness_result = self.contract_service.verify_container_docker_readiness(readiness)
            if readiness_result.status == VerificationStatus.VERIFIED:
                results.append(readiness_result)
                continue

            install_outcome = await self.runtime.install_docker(node)
            install_result = self.contract_service.verify_container_docker_install(
                install_outcome,
            )
            results.append(install_result)
            if install_result.status != VerificationStatus.VERIFIED:
                continue

            verified_readiness = await self.runtime.verify_docker(node)
            results.append(
                self.contract_service.verify_container_docker_readiness(
                    verified_readiness,
                )
            )
        return tuple(results)
