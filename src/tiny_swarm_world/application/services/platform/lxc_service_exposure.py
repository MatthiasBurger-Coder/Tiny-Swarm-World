from __future__ import annotations

from dataclasses import dataclass

from tiny_swarm_world.application.ports.node_provider import (
    LxcProxyDeviceState,
    PortLxcProxyDeviceRuntime,
)
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus
from tiny_swarm_world.domain.network import LxcProxyDevicePlan
from tiny_swarm_world.domain.node_provider import NodeSpec
from tiny_swarm_world.domain.preflight import SetupManifest


@dataclass(frozen=True)
class LxcServiceExposureSummary:
    plans: tuple[LxcProxyDevicePlan, ...]
    existing_count: int = 0
    created_count: int = 0
    updated_count: int = 0
    lookup_failure_count: int = 0
    create_failure_count: int = 0
    update_failure_count: int = 0

    @property
    def failed_apply_count(self) -> int:
        return (
            self.lookup_failure_count
            + self.create_failure_count
            + self.update_failure_count
        )


class LxcServiceExposureService:
    def __init__(
        self,
        runtime: PortLxcProxyDeviceRuntime,
        *,
        gateway_node: NodeSpec,
        setup_manifest: SetupManifest,
        listen_address: str,
    ) -> None:
        self.runtime = runtime
        self.gateway_node = gateway_node
        self.setup_manifest = setup_manifest
        self.listen_address = listen_address

    async def ensure_service_exposure(self) -> VerificationResult:
        plans = _plans_from_manifest(
            self.setup_manifest,
            gateway_node=self.gateway_node.name,
            listen_address=self.listen_address,
        )
        summary = await self._apply_plans(plans)
        return _summary_result(summary, self.gateway_node.name, self.listen_address)

    async def _apply_plans(
        self,
        plans: tuple[LxcProxyDevicePlan, ...],
    ) -> LxcServiceExposureSummary:
        existing_count = 0
        created_count = 0
        updated_count = 0
        lookup_failure_count = 0
        create_failure_count = 0
        update_failure_count = 0

        for plan in plans:
            state = await self.runtime.inspect_proxy_device(self.gateway_node, plan)
            if state == LxcProxyDeviceState.PRESENT:
                existing_count += 1
                continue
            if state == LxcProxyDeviceState.UNKNOWN:
                lookup_failure_count += 1
                continue
            if state == LxcProxyDeviceState.DRIFTED:
                if await self.runtime.update_proxy_device(self.gateway_node, plan):
                    updated_count += 1
                else:
                    update_failure_count += 1
                continue
            if await self.runtime.create_proxy_device(self.gateway_node, plan):
                created_count += 1
            else:
                create_failure_count += 1

        return LxcServiceExposureSummary(
            plans=plans,
            existing_count=existing_count,
            created_count=created_count,
            updated_count=updated_count,
            lookup_failure_count=lookup_failure_count,
            create_failure_count=create_failure_count,
            update_failure_count=update_failure_count,
        )


class LxcServiceExposureStep:
    returns_verification_result = True
    verification_target_id = "platform:expose:lxc-proxy-devices"

    def __init__(self, service: LxcServiceExposureService) -> None:
        self.service = service

    async def run(self) -> VerificationResult:
        return await self.service.ensure_service_exposure()


def _plans_from_manifest(
    setup_manifest: SetupManifest,
    *,
    gateway_node: str,
    listen_address: str,
) -> tuple[LxcProxyDevicePlan, ...]:
    return tuple(
        LxcProxyDevicePlan(
            service=requirement.service,
            listen_port=requirement.port,
            target_port=requirement.port,
            listen_address=listen_address,
            gateway_node=gateway_node,
        )
        for requirement in setup_manifest.required_ports
    )


def _summary_result(
    summary: LxcServiceExposureSummary,
    gateway_node: str,
    listen_address: str,
) -> VerificationResult:
    if not summary.plans:
        return VerificationResult(
            target_id=LxcServiceExposureStep.verification_target_id,
            status=VerificationStatus.BLOCKED,
            message="LXC proxy exposure has no published service ports to configure.",
            evidence={"phase": "pre_apply", "classification": "published_ports_missing"},
        )

    failed_apply_count = summary.failed_apply_count
    status = (
        VerificationStatus.VERIFIED
        if failed_apply_count == 0
        else VerificationStatus.FAILED_TO_APPLY
    )
    classification = (
        "lxc_proxy_exposure_verified"
        if status == VerificationStatus.VERIFIED
        else "lxc_proxy_exposure_not_verified"
    )
    message = (
        "LXC proxy exposure is configured on the Swarm manager gateway."
        if status == VerificationStatus.VERIFIED
        else "LXC proxy exposure failed for one or more published service ports."
    )
    return VerificationResult(
        target_id=LxcServiceExposureStep.verification_target_id,
        status=status,
        message=message,
        evidence={
            "phase": "apply",
            "classification": classification,
            "gateway_node": gateway_node,
            "listen_address": listen_address,
            "target_address": "127.0.0.1",
            "published_port_count": str(len(summary.plans)),
            "existing_count": str(summary.existing_count),
            "created_count": str(summary.created_count),
            "updated_count": str(summary.updated_count),
            "lookup_failure_count": str(summary.lookup_failure_count),
            "create_failure_count": str(summary.create_failure_count),
            "update_failure_count": str(summary.update_failure_count),
            "failed_apply_count": str(failed_apply_count),
            "published_ports": ",".join(
                str(plan.listen_port)
                for plan in sorted(summary.plans, key=lambda item: item.listen_port)
            ),
        },
    )
