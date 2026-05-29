from __future__ import annotations

from tiny_swarm_world.application.ports.node_provider import (
    PortContainerNetworkIdentity,
    PortContainerSwarmBootstrap,
)
from tiny_swarm_world.application.services.platform.docker_swarm_lxc_contract import (
    DockerSwarmInLxcContractService,
)
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus
from tiny_swarm_world.domain.node_provider import NodeSpec


class LxcSwarmBootstrapService:
    def __init__(
        self,
        swarm: PortContainerSwarmBootstrap,
        network_identity: PortContainerNetworkIdentity,
        contract_service: DockerSwarmInLxcContractService | None = None,
    ) -> None:
        self.swarm = swarm
        self.network_identity = network_identity
        self.contract_service = contract_service or DockerSwarmInLxcContractService()

    async def bootstrap_swarm(
        self,
        manager: NodeSpec,
        workers: tuple[NodeSpec, ...],
    ) -> tuple[VerificationResult, ...]:
        results: list[VerificationResult] = []
        manager_outcome = await self.swarm.inspect_manager(manager)
        manager_result = self.contract_service.verify_swarm_manager_bootstrap(
            manager_outcome,
        )
        if manager_result.status != VerificationStatus.VERIFIED:
            advertise_address = await self.network_identity.manager_advertise_address(
                manager,
            )
            manager_outcome = await self.swarm.initialize_manager(
                manager,
                advertise_address,
            )
            manager_result = self.contract_service.verify_swarm_manager_bootstrap(
                manager_outcome,
            )
        results.append(manager_result)
        if manager_result.status != VerificationStatus.VERIFIED:
            return tuple(results)

        advertise_address = await self.network_identity.manager_advertise_address(manager)
        credential = await self.swarm.worker_join_credential(manager)
        for worker in workers:
            worker_outcome = await self.swarm.inspect_worker(worker)
            worker_result = self.contract_service.verify_swarm_worker_join(worker_outcome)
            if worker_result.status != VerificationStatus.VERIFIED:
                worker_outcome = await self.swarm.join_worker(
                    worker,
                    advertise_address,
                    credential,
                )
                worker_result = self.contract_service.verify_swarm_worker_join(
                    worker_outcome,
                )
            results.append(worker_result)
        return tuple(results)
