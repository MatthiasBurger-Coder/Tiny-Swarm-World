import unittest

from tests.support.async_helpers import async_checkpoint

from tiny_swarm_world.application.ports.node_provider import (
    LxcProxyDeviceState,
    LxcProxyDriftRepairOutcome,
)
from tiny_swarm_world.application.services.platform import (
    LxcProxyDriftRepairService,
    LxcProxyDriftRepairStep,
    LxcServiceExposureService,
    LxcServiceExposureStep,
)
from tiny_swarm_world.application.services.platform.workflows import (
    PlatformExposeWorkflow,
    PlatformRepairLxcProxyDriftWorkflow,
)
from tiny_swarm_world.domain.deployment import ServiceStackProfile
from tiny_swarm_world.domain.inventory import VerificationStatus
from tiny_swarm_world.domain.network import LxcProxyDevicePlan
from tiny_swarm_world.domain.node_provider import NodeProviderKind, NodeRole, NodeSpec
from tiny_swarm_world.domain.preflight import default_setup_manifest


class TestLxcServiceExposure(unittest.IsolatedAsyncioTestCase):
    async def test_existing_proxy_devices_are_verified_without_mutation(self):
        runtime = _RecordingProxyRuntime(default_state=LxcProxyDeviceState.PRESENT)
        service = LxcServiceExposureService(
            runtime,
            gateway_node=_manager(),
            manager_profile_name=_manager_profile(),
            setup_manifest=default_setup_manifest(
                service_profile=ServiceStackProfile.SERVICE_ACCESS
            ),
            listen_address="0.0.0.0",
        )

        result = await service.ensure_service_exposure()

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual("2", result.evidence["published_port_count"])
        self.assertEqual("2", result.evidence["existing_count"])
        self.assertEqual("0", result.evidence["created_count"])
        self.assertEqual([], runtime.created)
        self.assertEqual((80, 443), tuple(plan.listen_port for _profile, plan in runtime.inspected))
        self.assertEqual("swarm-manager", result.evidence["gateway_node"])
        self.assertEqual("docker-swarm-manager", result.evidence["manager_profile"])
        self.assertEqual("0.0.0.0", result.evidence["listen_address"])

    async def test_missing_proxy_devices_are_created_on_manager_gateway(self):
        runtime = _RecordingProxyRuntime(default_state=LxcProxyDeviceState.MISSING)
        service = LxcServiceExposureService(
            runtime,
            gateway_node=_manager(),
            manager_profile_name=_manager_profile(),
            setup_manifest=default_setup_manifest(service_profile=ServiceStackProfile.DEFAULT),
            listen_address="127.0.0.1",
        )

        result = await service.ensure_service_exposure()

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual("10", result.evidence["published_port_count"])
        self.assertEqual("10", result.evidence["created_count"])
        self.assertEqual("127.0.0.1", result.evidence["listen_address"])
        self.assertEqual({"docker-swarm-manager"}, {profile for profile, _plan in runtime.created})
        self.assertNotIn("swarm-worker", repr(runtime.created))

    async def test_drifted_proxy_devices_are_updated(self):
        runtime = _RecordingProxyRuntime(default_state=LxcProxyDeviceState.DRIFTED)
        service = LxcServiceExposureService(
            runtime,
            gateway_node=_manager(),
            manager_profile_name=_manager_profile(),
            setup_manifest=default_setup_manifest(service_profile=ServiceStackProfile.DEFAULT),
            listen_address="0.0.0.0",
        )

        result = await service.ensure_service_exposure()

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual("10", result.evidence["updated_count"])
        self.assertEqual({"docker-swarm-manager"}, {profile for profile, _plan in runtime.updated})

    async def test_unknown_or_failed_proxy_device_apply_reports_actionable_counts(self):
        runtime = _RecordingProxyRuntime(
            states={
                9000: LxcProxyDeviceState.UNKNOWN,
                8081: LxcProxyDeviceState.MISSING,
                5000: LxcProxyDeviceState.DRIFTED,
            },
            default_state=LxcProxyDeviceState.PRESENT,
            create_success=False,
            update_success=False,
        )
        service = LxcServiceExposureService(
            runtime,
            gateway_node=_manager(),
            manager_profile_name=_manager_profile(),
            setup_manifest=default_setup_manifest(service_profile=ServiceStackProfile.DEFAULT),
            listen_address="0.0.0.0",
        )

        result = await service.ensure_service_exposure()

        self.assertEqual(VerificationStatus.FAILED_TO_APPLY, result.status)
        self.assertEqual("1", result.evidence["lookup_failure_count"])
        self.assertEqual("1", result.evidence["create_failure_count"])
        self.assertEqual("1", result.evidence["update_failure_count"])
        self.assertEqual("3", result.evidence["failed_apply_count"])
        self.assertIn("published service ports", result.message)

    async def test_platform_expose_workflow_uses_direct_verification_result(self):
        runtime = _RecordingProxyRuntime(default_state=LxcProxyDeviceState.PRESENT)
        step = LxcServiceExposureStep(
            LxcServiceExposureService(
                runtime,
                gateway_node=_manager(),
                manager_profile_name=_manager_profile(),
                setup_manifest=default_setup_manifest(),
                listen_address="0.0.0.0",
            )
        )

        result = await PlatformExposeWorkflow([step]).run()

        self.assertEqual("platform expose", result.workflow_name)
        self.assertEqual(VerificationStatus.VERIFIED, result.verification_results[0].status)
        self.assertEqual(
            "platform:expose:lxc-proxy-devices",
            result.verification_results[0].target_id,
        )

    async def test_repair_reports_removed_stale_direct_proxy_devices(self):
        runtime = _RecordingProxyRuntime(
            default_state=LxcProxyDeviceState.PRESENT,
            repair_outcome=LxcProxyDriftRepairOutcome(
                expected_profile_device_count=8,
                stale_direct_device_count=1,
                removed_count=1,
                removed_devices=("tsw-proxy-8080",),
            ),
        )
        service = LxcProxyDriftRepairService(
            runtime,
            gateway_node=_manager(),
            manager_profile_name=_manager_profile(),
            setup_manifest=default_setup_manifest(service_profile=ServiceStackProfile.DEFAULT),
            listen_address="0.0.0.0",
        )

        result = await service.repair_stale_proxy_devices()

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual("lxc_proxy_drift_repaired", result.evidence["classification"])
        self.assertEqual("1", result.evidence["removed_count"])
        self.assertEqual("tsw-proxy-8080", result.evidence["removed_devices"])
        self.assertEqual("swarm-manager", result.evidence["gateway_node"])
        self.assertEqual("docker-swarm-manager", result.evidence["manager_profile"])
        self.assertEqual({"docker-swarm-manager"}, {profile for profile, _node, _plans in runtime.repaired})

    async def test_repair_blocks_when_profile_equivalent_is_not_verified(self):
        runtime = _RecordingProxyRuntime(
            default_state=LxcProxyDeviceState.PRESENT,
            repair_outcome=LxcProxyDriftRepairOutcome(
                expected_profile_device_count=8,
                stale_direct_device_count=1,
                refused_count=1,
                refused_devices=("tsw-proxy-8080",),
            ),
        )
        service = LxcProxyDriftRepairService(
            runtime,
            gateway_node=_manager(),
            manager_profile_name=_manager_profile(),
            setup_manifest=default_setup_manifest(service_profile=ServiceStackProfile.DEFAULT),
            listen_address="0.0.0.0",
        )

        result = await service.repair_stale_proxy_devices()

        self.assertEqual(VerificationStatus.BLOCKED, result.status)
        self.assertEqual("lxc_proxy_drift_repair_refused", result.evidence["classification"])
        self.assertEqual("1", result.evidence["refused_count"])
        self.assertEqual("tsw-proxy-8080", result.evidence["refused_devices"])

    async def test_repair_workflow_uses_direct_verification_result(self):
        runtime = _RecordingProxyRuntime(
            default_state=LxcProxyDeviceState.PRESENT,
            repair_outcome=LxcProxyDriftRepairOutcome(
                expected_profile_device_count=8,
                stale_direct_device_count=0,
            ),
        )
        step = LxcProxyDriftRepairStep(
            LxcProxyDriftRepairService(
                runtime,
                gateway_node=_manager(),
                manager_profile_name=_manager_profile(),
                setup_manifest=default_setup_manifest(),
                listen_address="0.0.0.0",
            )
        )

        result = await PlatformRepairLxcProxyDriftWorkflow([step]).run()

        self.assertEqual("platform repair-lxc-proxy-drift", result.workflow_name)
        self.assertEqual(VerificationStatus.VERIFIED, result.verification_results[0].status)
        self.assertEqual(
            "platform:repair-lxc-proxy-drift",
            result.verification_results[0].target_id,
        )


class _RecordingProxyRuntime:
    def __init__(
        self,
        *,
        states: dict[int, LxcProxyDeviceState] | None = None,
        default_state: LxcProxyDeviceState,
        create_success: bool = True,
        update_success: bool = True,
        repair_outcome: LxcProxyDriftRepairOutcome | None = None,
    ) -> None:
        self.states = dict(states or {})
        self.default_state = default_state
        self.create_success = create_success
        self.update_success = update_success
        self.repair_outcome = repair_outcome or LxcProxyDriftRepairOutcome(
            expected_profile_device_count=0
        )
        self.inspected: list[tuple[str, LxcProxyDevicePlan]] = []
        self.created: list[tuple[str, LxcProxyDevicePlan]] = []
        self.updated: list[tuple[str, LxcProxyDevicePlan]] = []
        self.repaired: list[tuple[str, NodeSpec, tuple[LxcProxyDevicePlan, ...]]] = []

    async def inspect_proxy_device(
        self,
        profile_name: str,
        plan: LxcProxyDevicePlan,
    ) -> LxcProxyDeviceState:
        await async_checkpoint()
        self.inspected.append((profile_name, plan))
        return self.states.get(plan.listen_port, self.default_state)

    async def create_proxy_device(
        self,
        profile_name: str,
        plan: LxcProxyDevicePlan,
    ) -> bool:
        await async_checkpoint()
        self.created.append((profile_name, plan))
        return self.create_success

    async def update_proxy_device(
        self,
        profile_name: str,
        plan: LxcProxyDevicePlan,
    ) -> bool:
        await async_checkpoint()
        self.updated.append((profile_name, plan))
        return self.update_success

    async def repair_stale_proxy_devices(
        self,
        profile_name: str,
        gateway_node: NodeSpec,
        plans: tuple[LxcProxyDevicePlan, ...],
    ) -> LxcProxyDriftRepairOutcome:
        await async_checkpoint()
        self.repaired.append((profile_name, gateway_node, plans))
        return self.repair_outcome


def _manager() -> NodeSpec:
    return NodeSpec("swarm-manager", NodeRole.MANAGER, NodeProviderKind.LXC_NATIVE)


def _manager_profile() -> str:
    return "docker-swarm-manager"
