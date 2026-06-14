from __future__ import annotations

from dataclasses import dataclass

from tiny_swarm_world.application.ports.node_provider import (
    LxcProxyDriftRepairOutcome,
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


@dataclass(frozen=True)
class LxcServiceExposureVerificationSummary:
    plans: tuple[LxcProxyDevicePlan, ...]
    present_count: int = 0
    missing_count: int = 0
    drifted_count: int = 0
    unknown_count: int = 0


class LxcServiceExposureService:
    def __init__(
        self,
        runtime: PortLxcProxyDeviceRuntime,
        *,
        gateway_node: NodeSpec,
        manager_profile_name: str,
        setup_manifest: SetupManifest,
        listen_address: str,
    ) -> None:
        self.runtime = runtime
        self.gateway_node = gateway_node
        self.manager_profile_name = manager_profile_name
        self.setup_manifest = setup_manifest
        self.listen_address = listen_address

    async def ensure_service_exposure(self) -> VerificationResult:
        plans = _plans_from_manifest(
            self.setup_manifest,
            gateway_node=self.gateway_node.name,
            listen_address=self.listen_address,
        )
        summary = await self._apply_plans(plans)
        return _summary_result(
            summary,
            self.gateway_node.name,
            self.manager_profile_name,
            self.listen_address,
        )

    async def verify_service_exposure(self) -> VerificationResult:
        plans = _plans_from_manifest(
            self.setup_manifest,
            gateway_node=self.gateway_node.name,
            listen_address=self.listen_address,
        )
        summary = await self._verify_plans(plans)
        return _verify_summary_result(
            summary,
            self.gateway_node.name,
            self.manager_profile_name,
            self.listen_address,
        )

    async def _verify_plans(
        self,
        plans: tuple[LxcProxyDevicePlan, ...],
    ) -> LxcServiceExposureVerificationSummary:
        present_count = 0
        missing_count = 0
        drifted_count = 0
        unknown_count = 0
        for plan in plans:
            state = await self.runtime.inspect_proxy_device(self.manager_profile_name, plan)
            if state == LxcProxyDeviceState.PRESENT:
                present_count += 1
            elif state == LxcProxyDeviceState.MISSING:
                missing_count += 1
            elif state == LxcProxyDeviceState.DRIFTED:
                drifted_count += 1
            else:
                unknown_count += 1
        return LxcServiceExposureVerificationSummary(
            plans=plans,
            present_count=present_count,
            missing_count=missing_count,
            drifted_count=drifted_count,
            unknown_count=unknown_count,
        )

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
            state = await self.runtime.inspect_proxy_device(self.manager_profile_name, plan)
            if state == LxcProxyDeviceState.PRESENT:
                existing_count += 1
                continue
            if state == LxcProxyDeviceState.UNKNOWN:
                lookup_failure_count += 1
                continue
            if state == LxcProxyDeviceState.DRIFTED:
                if await self.runtime.update_proxy_device(self.manager_profile_name, plan):
                    updated_count += 1
                else:
                    update_failure_count += 1
                continue
            if await self.runtime.create_proxy_device(self.manager_profile_name, plan):
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


class LxcServiceExposureVerifyStep:
    returns_verification_result = True
    verification_target_id = "platform:verify:lxc-proxy-devices"

    def __init__(self, service: LxcServiceExposureService) -> None:
        self.service = service

    async def run(self) -> VerificationResult:
        return await self.service.verify_service_exposure()


class LxcProxyDriftRepairService:
    def __init__(
        self,
        runtime: PortLxcProxyDeviceRuntime,
        *,
        gateway_node: NodeSpec,
        manager_profile_name: str,
        setup_manifest: SetupManifest,
        listen_address: str,
    ) -> None:
        self.runtime = runtime
        self.gateway_node = gateway_node
        self.manager_profile_name = manager_profile_name
        self.setup_manifest = setup_manifest
        self.listen_address = listen_address

    async def repair_stale_proxy_devices(self) -> VerificationResult:
        plans = _plans_from_manifest(
            self.setup_manifest,
            gateway_node=self.gateway_node.name,
            listen_address=self.listen_address,
        )
        outcome = await self.runtime.repair_stale_proxy_devices(
            self.manager_profile_name,
            self.gateway_node,
            plans,
        )
        return _repair_result(
            outcome,
            self.gateway_node.name,
            self.manager_profile_name,
            self.listen_address,
        )


class LxcProxyDriftRepairStep:
    returns_verification_result = True
    verification_target_id = "platform:repair-lxc-proxy-drift"

    def __init__(self, service: LxcProxyDriftRepairService) -> None:
        self.service = service

    async def run(self) -> VerificationResult:
        return await self.service.repair_stale_proxy_devices()


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


def _repair_result(
    outcome: LxcProxyDriftRepairOutcome,
    gateway_node: str,
    manager_profile_name: str,
    listen_address: str,
) -> VerificationResult:
    if outcome.expected_profile_device_count == 0:
        return VerificationResult(
            target_id=LxcProxyDriftRepairStep.verification_target_id,
            status=VerificationStatus.BLOCKED,
            message="LXC proxy drift repair has no published service ports to validate.",
            evidence={"phase": "pre_apply", "classification": "published_ports_missing"},
        )

    status = _repair_status(outcome)
    classification = _repair_classification(outcome, status)
    message = _repair_message(outcome, status)
    return VerificationResult(
        target_id=LxcProxyDriftRepairStep.verification_target_id,
        status=status,
        message=message,
        evidence={
            "phase": "apply",
            "classification": classification,
            "gateway_node": gateway_node,
            "manager_profile": manager_profile_name,
            "listen_address": listen_address,
            "expected_profile_device_count": str(outcome.expected_profile_device_count),
            "stale_direct_device_count": str(outcome.stale_direct_device_count),
            "removed_count": str(outcome.removed_count),
            "refused_count": str(outcome.refused_count),
            "lookup_failure_count": str(outcome.lookup_failure_count),
            "remove_failure_count": str(outcome.remove_failure_count),
            "mutation_allowed": str(outcome.mutation_allowed).lower(),
            "removed_devices": ",".join(outcome.removed_devices),
            "refused_devices": ",".join(outcome.refused_devices),
            "failed_devices": ",".join(outcome.failed_devices),
        },
    )


def _repair_status(outcome: LxcProxyDriftRepairOutcome) -> VerificationStatus:
    if not outcome.mutation_allowed or outcome.blocked_count > 0:
        return VerificationStatus.BLOCKED
    if outcome.remove_failure_count > 0:
        return VerificationStatus.FAILED_TO_APPLY
    return VerificationStatus.VERIFIED


def _repair_classification(
    outcome: LxcProxyDriftRepairOutcome,
    status: VerificationStatus,
) -> str:
    if status == VerificationStatus.BLOCKED:
        if not outcome.mutation_allowed:
            return "live_mutation_required"
        return "lxc_proxy_drift_repair_refused"
    if status == VerificationStatus.FAILED_TO_APPLY:
        return "lxc_proxy_drift_repair_failed"
    if outcome.removed_count > 0:
        return "lxc_proxy_drift_repaired"
    return "lxc_proxy_drift_absent"


def _repair_message(
    outcome: LxcProxyDriftRepairOutcome,
    status: VerificationStatus,
) -> str:
    if status == VerificationStatus.BLOCKED:
        if not outcome.mutation_allowed:
            return "LXC proxy drift repair requires accepted live infrastructure consent."
        return (
            "LXC proxy drift repair was refused for one or more devices because the "
            "manager profile equivalent was not verified."
        )
    if status == VerificationStatus.FAILED_TO_APPLY:
        return "LXC proxy drift repair failed while removing one or more stale devices."
    if outcome.removed_count > 0:
        return "LXC proxy drift repair removed stale direct proxy devices."
    return "LXC proxy drift repair found no stale direct proxy devices."


def _summary_result(
    summary: LxcServiceExposureSummary,
    gateway_node: str,
    manager_profile_name: str,
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
            "manager_profile": manager_profile_name,
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


def _verify_summary_result(
    summary: LxcServiceExposureVerificationSummary,
    gateway_node: str,
    manager_profile_name: str,
    listen_address: str,
) -> VerificationResult:
    if not summary.plans:
        return VerificationResult(
            target_id=LxcServiceExposureVerifyStep.verification_target_id,
            status=VerificationStatus.BLOCKED,
            message="LXC proxy verification has no published service ports to validate.",
            evidence={
                "phase": "verify",
                "classification": "published_ports_missing",
                "expected": "published_lxc_proxy_devices",
                "observed": "no_published_ports",
                "next_action": "Select a service profile with published ports.",
            },
        )

    failed_verify_count = (
        summary.missing_count + summary.drifted_count + summary.unknown_count
    )
    status = (
        VerificationStatus.VERIFIED
        if failed_verify_count == 0
        else VerificationStatus.FAILED_TO_VERIFY
    )
    classification = (
        "lxc_proxy_devices_verified"
        if status == VerificationStatus.VERIFIED
        else "lxc_proxy_devices_not_verified"
    )
    return VerificationResult(
        target_id=LxcServiceExposureVerifyStep.verification_target_id,
        status=status,
        message="LXC proxy device verification reached a terminal state.",
        evidence={
            "phase": "verify",
            "classification": classification,
            "expected": "published_lxc_proxy_devices_on_manager_profile",
            "observed": (
                "all_proxy_devices_present"
                if status == VerificationStatus.VERIFIED
                else "one_or_more_proxy_devices_missing_or_drifted"
            ),
            "next_action": (
                "No action required."
                if status == VerificationStatus.VERIFIED
                else "Run platform expose or inspect the manager profile proxy devices."
            ),
            "gateway_node": gateway_node,
            "manager_profile": manager_profile_name,
            "listen_address": listen_address,
            "target_address": "127.0.0.1",
            "published_port_count": str(len(summary.plans)),
            "present_count": str(summary.present_count),
            "missing_count": str(summary.missing_count),
            "drifted_count": str(summary.drifted_count),
            "unknown_count": str(summary.unknown_count),
            "failed_verify_count": str(failed_verify_count),
            "published_ports": ",".join(
                str(plan.listen_port)
                for plan in sorted(summary.plans, key=lambda item: item.listen_port)
            ),
        },
    )
