from __future__ import annotations

from tiny_swarm_world.application.ports.node_provider import (
    PortContainerNetworkIdentity,
    PortContainerSwarmBootstrap,
)
from tiny_swarm_world.application.services.platform.docker_swarm_lxc_contract import (
    DockerSwarmInLxcContractService,
)
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus
from tiny_swarm_world.domain.node_provider import NodeRole, NodeSpec


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
        credential = None
        for worker in workers:
            worker_outcome = await self.swarm.inspect_worker(worker)
            worker_result = self.contract_service.verify_swarm_worker_join(worker_outcome)
            if worker_result.status != VerificationStatus.VERIFIED:
                if credential is None:
                    credential = await self.swarm.worker_join_credential(manager)
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

    async def verify_swarm_membership(
        self,
        manager: NodeSpec,
        workers: tuple[NodeSpec, ...],
    ) -> tuple[VerificationResult, ...]:
        results: list[VerificationResult] = []
        manager_outcome = await self.swarm.inspect_manager(manager)
        results.append(
            self.contract_service.verify_swarm_manager_bootstrap(manager_outcome)
        )
        for worker in workers:
            worker_outcome = await self.swarm.inspect_worker(worker)
            results.append(self.contract_service.verify_swarm_worker_join(worker_outcome))
        return tuple(results)


class LxcSwarmBootstrapStep:
    returns_verification_result = True
    verification_target_id = "platform:init:lxc-swarm-bootstrap"

    def __init__(
        self,
        service: LxcSwarmBootstrapService,
        nodes: tuple[NodeSpec, ...],
    ) -> None:
        self.service = service
        self.nodes = nodes

    async def run(self) -> VerificationResult:
        manager = next((node for node in self.nodes if node.role == NodeRole.MANAGER), None)
        workers = tuple(node for node in self.nodes if node.role == NodeRole.WORKER)
        if manager is None:
            return VerificationResult(
                target_id=self.verification_target_id,
                status=VerificationStatus.BLOCKED,
                message="Swarm bootstrap phase has no manager node.",
                evidence={"phase": "pre_apply", "classification": "manager_node_missing"},
            )
        results = await self.service.bootstrap_swarm(manager, workers)
        return _aggregate_swarm_results(results, self.nodes)


class LxcSwarmVerifyStep:
    returns_verification_result = True
    verification_target_id = "platform:verify:lxc-swarm-membership"

    def __init__(
        self,
        service: LxcSwarmBootstrapService,
        nodes: tuple[NodeSpec, ...],
    ) -> None:
        self.service = service
        self.nodes = nodes

    async def run(self) -> VerificationResult:
        manager = next((node for node in self.nodes if node.role == NodeRole.MANAGER), None)
        workers = tuple(node for node in self.nodes if node.role == NodeRole.WORKER)
        if manager is None:
            return VerificationResult(
                target_id=self.verification_target_id,
                status=VerificationStatus.BLOCKED,
                message="Swarm verification has no manager node.",
                evidence={
                    "phase": "verify",
                    "classification": "manager_node_missing",
                    "expected": "one_swarm_manager_node",
                    "observed": "no_manager_node",
                    "next_action": "Configure a managed LXC manager node.",
                },
            )
        results = await self.service.verify_swarm_membership(manager, workers)
        return _aggregate_swarm_verify_results(results, self.nodes)


def _aggregate_swarm_results(
    results: tuple[VerificationResult, ...],
    expected_nodes: tuple[NodeSpec, ...],
) -> VerificationResult:
    if not results:
        return VerificationResult(
            target_id=LxcSwarmBootstrapStep.verification_target_id,
            status=VerificationStatus.BLOCKED,
            message="Swarm bootstrap phase has no node results.",
            evidence={"phase": "verify", "classification": "node_results_missing"},
        )

    missing_nodes = _missing_node_names(results, expected_nodes)
    if missing_nodes:
        return VerificationResult(
            target_id=LxcSwarmBootstrapStep.verification_target_id,
            status=VerificationStatus.FAILED_TO_VERIFY,
            message="Swarm bootstrap phase is missing expected node results.",
            evidence={
                "phase": "verify",
                "classification": "expected_node_results_missing",
                "expected_count": str(len(expected_nodes)),
                "observed_count": str(len(expected_nodes) - len(missing_nodes)),
                "missing_count": str(len(missing_nodes)),
            },
        )

    status = _aggregate_status(results)
    classification = (
        "swarm_bootstrap_verified"
        if status == VerificationStatus.VERIFIED
        else "swarm_bootstrap_not_verified"
    )
    return VerificationResult(
        target_id=LxcSwarmBootstrapStep.verification_target_id,
        status=status,
        message="Swarm bootstrap phase reached a terminal state.",
        evidence={
            "phase": "verify",
            "classification": classification,
            "result_count": str(len(results)),
            "verified_count": str(
                sum(1 for result in results if result.status == VerificationStatus.VERIFIED)
            ),
            "blocked_count": str(
                sum(1 for result in results if result.status == VerificationStatus.BLOCKED)
            ),
            "failed_verify_count": str(
                sum(
                    1
                    for result in results
                    if result.status == VerificationStatus.FAILED_TO_VERIFY
                )
            ),
        },
    )


def _aggregate_swarm_verify_results(
    results: tuple[VerificationResult, ...],
    expected_nodes: tuple[NodeSpec, ...],
) -> VerificationResult:
    if not results:
        return VerificationResult(
            target_id=LxcSwarmVerifyStep.verification_target_id,
            status=VerificationStatus.BLOCKED,
            message="Swarm membership verification has no node results.",
            evidence={
                "phase": "verify",
                "classification": "node_results_missing",
                "expected": "swarm_membership_on_each_managed_node",
                "observed": "no_node_results",
                "next_action": "Configure managed LXC nodes before platform verification.",
            },
        )

    missing_nodes = _missing_node_names(results, expected_nodes)
    if missing_nodes:
        return VerificationResult(
            target_id=LxcSwarmVerifyStep.verification_target_id,
            status=VerificationStatus.FAILED_TO_VERIFY,
            message="Swarm membership verification is missing expected node results.",
            evidence={
                "phase": "verify",
                "classification": "expected_node_results_missing",
                "expected": "swarm_membership_on_each_managed_node",
                "observed": "missing_expected_node_result",
                "next_action": "Inspect managed node inventory and Swarm membership.",
                "expected_count": str(len(expected_nodes)),
                "observed_count": str(len(expected_nodes) - len(missing_nodes)),
                "missing_count": str(len(missing_nodes)),
                "missing_nodes": ",".join(missing_nodes),
            },
        )

    status = _aggregate_status(results)
    failed_nodes = _node_names_for_statuses(
        results,
        (VerificationStatus.BLOCKED, VerificationStatus.FAILED_TO_VERIFY),
    )
    classification = (
        "swarm_membership_verified"
        if status == VerificationStatus.VERIFIED
        else "swarm_membership_not_verified"
    )
    return VerificationResult(
        target_id=LxcSwarmVerifyStep.verification_target_id,
        status=status,
        message="Swarm membership verification reached a terminal state.",
        evidence={
            "phase": "verify",
            "classification": classification,
            "expected": "swarm_membership_on_each_managed_node",
            "observed": (
                "all_nodes_joined"
                if status == VerificationStatus.VERIFIED
                else "one_or_more_nodes_not_joined"
            ),
            "next_action": (
                "No action required."
                if status == VerificationStatus.VERIFIED
                else "Run platform init or inspect the listed managed nodes."
            ),
            "result_count": str(len(results)),
            "verified_count": str(
                sum(1 for result in results if result.status == VerificationStatus.VERIFIED)
            ),
            "blocked_count": str(
                sum(1 for result in results if result.status == VerificationStatus.BLOCKED)
            ),
            "failed_verify_count": str(
                sum(
                    1
                    for result in results
                    if result.status == VerificationStatus.FAILED_TO_VERIFY
                )
            ),
            "failed_nodes": ",".join(failed_nodes),
        },
    )


def _node_names_for_statuses(
    results: tuple[VerificationResult, ...],
    statuses: tuple[VerificationStatus, ...],
) -> tuple[str, ...]:
    return tuple(
        str(result.evidence["node"])
        for result in results
        if result.status in statuses and "node" in result.evidence
    )


def _missing_node_names(
    results: tuple[VerificationResult, ...],
    expected_nodes: tuple[NodeSpec, ...],
) -> tuple[str, ...]:
    observed_nodes = {
        str(result.evidence["node"])
        for result in results
        if "node" in result.evidence
    }
    return tuple(node.name for node in expected_nodes if node.name not in observed_nodes)


def _aggregate_status(results: tuple[VerificationResult, ...]) -> VerificationStatus:
    statuses = tuple(result.status for result in results)
    if all(status == VerificationStatus.VERIFIED for status in statuses):
        return VerificationStatus.VERIFIED
    if VerificationStatus.FAILED_TO_APPLY in statuses:
        return VerificationStatus.FAILED_TO_APPLY
    if VerificationStatus.BLOCKED in statuses:
        return VerificationStatus.BLOCKED
    return VerificationStatus.FAILED_TO_VERIFY
