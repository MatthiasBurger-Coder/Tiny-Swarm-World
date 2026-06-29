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
            if readiness_result.status == VerificationStatus.BLOCKED:
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

    async def verify_docker_runtime(
        self,
        nodes: tuple[NodeSpec, ...],
    ) -> tuple[VerificationResult, ...]:
        results: list[VerificationResult] = []
        for node in nodes:
            readiness = await self.runtime.inspect_docker(node)
            results.append(
                self.contract_service.verify_container_docker_readiness(readiness)
            )
        return tuple(results)


class LxcDockerInstallStep:
    returns_verification_result = True
    verification_target_id = "platform:init:lxc-container-runtime"

    def __init__(
        self,
        service: LxcDockerInstallService,
        nodes: tuple[NodeSpec, ...],
    ) -> None:
        self.service = service
        self.nodes = nodes

    async def run(self) -> VerificationResult:
        results = await self.service.ensure_docker_installed(self.nodes)
        return _aggregate_install_results(results)


class LxcDockerVerifyStep:
    returns_verification_result = True
    verification_target_id = "platform:verify:lxc-container-runtime"

    def __init__(
        self,
        service: LxcDockerInstallService,
        nodes: tuple[NodeSpec, ...],
    ) -> None:
        self.service = service
        self.nodes = nodes

    async def run(self) -> VerificationResult:
        results = await self.service.verify_docker_runtime(self.nodes)
        return _aggregate_verify_results(results)


def _aggregate_install_results(
    results: tuple[VerificationResult, ...],
) -> VerificationResult:
    if not results:
        return VerificationResult(
            target_id=LxcDockerInstallStep.verification_target_id,
            status=VerificationStatus.BLOCKED,
            message="Container runtime phase has no node results.",
            evidence={"phase": "verify", "classification": "node_results_missing"},
        )

    status = _aggregate_status(results)
    classification = (
        "container_runtime_verified"
        if status == VerificationStatus.VERIFIED
        else "container_runtime_not_verified"
    )
    return VerificationResult(
        target_id=LxcDockerInstallStep.verification_target_id,
        status=status,
        message="Container runtime phase reached a terminal state.",
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
            "failed_apply_count": str(
                sum(
                    1
                    for result in results
                    if result.status == VerificationStatus.FAILED_TO_APPLY
                )
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


def _aggregate_verify_results(
    results: tuple[VerificationResult, ...],
) -> VerificationResult:
    if not results:
        return VerificationResult(
            target_id=LxcDockerVerifyStep.verification_target_id,
            status=VerificationStatus.BLOCKED,
            message="Container runtime verification has no node results.",
            evidence={
                "phase": "verify",
                "classification": "node_results_missing",
                "expected": "docker_engine_ready_on_each_managed_node",
                "observed": "no_node_results",
                "next_action": "Configure managed LXC nodes before platform verification.",
            },
        )

    status = _aggregate_status(results)
    failed_nodes = _node_names_for_statuses(
        results,
        (VerificationStatus.BLOCKED, VerificationStatus.FAILED_TO_VERIFY),
    )
    classification = (
        "container_runtime_verified"
        if status == VerificationStatus.VERIFIED
        else "container_runtime_not_verified"
    )
    return VerificationResult(
        target_id=LxcDockerVerifyStep.verification_target_id,
        status=status,
        message="Container Docker runtime verification reached a terminal state.",
        evidence={
            "phase": "verify",
            "classification": classification,
            "expected": "docker_engine_ready_on_each_managed_node",
            "observed": (
                "all_nodes_ready"
                if status == VerificationStatus.VERIFIED
                else "one_or_more_nodes_not_ready"
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


def _aggregate_status(results: tuple[VerificationResult, ...]) -> VerificationStatus:
    statuses = tuple(result.status for result in results)
    if all(status == VerificationStatus.VERIFIED for status in statuses):
        return VerificationStatus.VERIFIED
    if VerificationStatus.FAILED_TO_APPLY in statuses:
        return VerificationStatus.FAILED_TO_APPLY
    if VerificationStatus.BLOCKED in statuses:
        return VerificationStatus.BLOCKED
    return VerificationStatus.FAILED_TO_VERIFY
