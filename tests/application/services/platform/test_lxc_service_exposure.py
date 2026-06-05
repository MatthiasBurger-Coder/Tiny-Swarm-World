import unittest

from tiny_swarm_world.application.ports.node_provider import LxcProxyDeviceState
from tiny_swarm_world.application.services.platform import (
    LxcServiceExposureService,
    LxcServiceExposureStep,
)
from tiny_swarm_world.application.services.platform.workflows import PlatformExposeWorkflow
from tiny_swarm_world.domain.deployment import ServiceStackProfile
from tiny_swarm_world.domain.inventory import VerificationStatus
from tiny_swarm_world.domain.network import LxcProxyDevicePlan
from tiny_swarm_world.domain.node_provider import NodeProviderKind, NodeRole, NodeSpec
from tiny_swarm_world.domain.preflight import SetupManifest, default_setup_manifest


class TestLxcServiceExposure(unittest.IsolatedAsyncioTestCase):
    async def test_existing_proxy_devices_are_verified_without_mutation(self):
        runtime = _RecordingProxyRuntime(default_state=LxcProxyDeviceState.PRESENT)
        service = LxcServiceExposureService(
            runtime,
            gateway_node=_manager(),
            setup_manifest=default_setup_manifest(
                service_profile=ServiceStackProfile.SERVICE_ACCESS
            ),
            listen_address="0.0.0.0",
        )

        result = await service.ensure_service_exposure()

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual("10", result.evidence["published_port_count"])
        self.assertEqual("10", result.evidence["existing_count"])
        self.assertEqual("0", result.evidence["created_count"])
        self.assertEqual([], runtime.created)
        self.assertEqual("swarm-manager", result.evidence["gateway_node"])
        self.assertEqual("0.0.0.0", result.evidence["listen_address"])

    async def test_missing_proxy_devices_are_created_on_manager_gateway(self):
        runtime = _RecordingProxyRuntime(default_state=LxcProxyDeviceState.MISSING)
        service = LxcServiceExposureService(
            runtime,
            gateway_node=_manager(),
            setup_manifest=default_setup_manifest(service_profile=ServiceStackProfile.DEFAULT),
            listen_address="127.0.0.1",
        )

        result = await service.ensure_service_exposure()

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual("8", result.evidence["published_port_count"])
        self.assertEqual("8", result.evidence["created_count"])
        self.assertEqual("127.0.0.1", result.evidence["listen_address"])
        self.assertEqual({"swarm-manager"}, {node.name for node, _plan in runtime.created})
        self.assertNotIn("swarm-worker", repr(runtime.created))

    async def test_drifted_proxy_devices_are_updated(self):
        runtime = _RecordingProxyRuntime(default_state=LxcProxyDeviceState.DRIFTED)
        service = LxcServiceExposureService(
            runtime,
            gateway_node=_manager(),
            setup_manifest=default_setup_manifest(service_profile=ServiceStackProfile.DEFAULT),
            listen_address="0.0.0.0",
        )

        result = await service.ensure_service_exposure()

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual("8", result.evidence["updated_count"])
        self.assertEqual({"swarm-manager"}, {node.name for node, _plan in runtime.updated})

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


class _RecordingProxyRuntime:
    def __init__(
        self,
        *,
        states: dict[int, LxcProxyDeviceState] | None = None,
        default_state: LxcProxyDeviceState,
        create_success: bool = True,
        update_success: bool = True,
    ) -> None:
        self.states = dict(states or {})
        self.default_state = default_state
        self.create_success = create_success
        self.update_success = update_success
        self.inspected: list[tuple[NodeSpec, LxcProxyDevicePlan]] = []
        self.created: list[tuple[NodeSpec, LxcProxyDevicePlan]] = []
        self.updated: list[tuple[NodeSpec, LxcProxyDevicePlan]] = []

    async def inspect_proxy_device(
        self,
        node: NodeSpec,
        plan: LxcProxyDevicePlan,
    ) -> LxcProxyDeviceState:
        self.inspected.append((node, plan))
        return self.states.get(plan.listen_port, self.default_state)

    async def create_proxy_device(
        self,
        node: NodeSpec,
        plan: LxcProxyDevicePlan,
    ) -> bool:
        self.created.append((node, plan))
        return self.create_success

    async def update_proxy_device(
        self,
        node: NodeSpec,
        plan: LxcProxyDevicePlan,
    ) -> bool:
        self.updated.append((node, plan))
        return self.update_success


def _manager() -> NodeSpec:
    return NodeSpec("swarm-manager", NodeRole.MANAGER, NodeProviderKind.LXC_NATIVE)
