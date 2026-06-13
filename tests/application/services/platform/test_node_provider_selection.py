import unittest
from collections.abc import Sequence

from tests.support.async_helpers import async_checkpoint

from tiny_swarm_world.application.ports.node_provider import (
    PortManagedNodeTeardown,
    PortNodeLifecycle,
    PortNodeProviderReadiness,
)
from tiny_swarm_world.application.services.platform.node_provider_selection import (
    NodeProviderDestroyManagedNodesStep,
    NodeProviderResetManagedNodesStep,
    NodeProviderSelectionRequest,
    NodeProviderSelectionService,
)
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus
from tiny_swarm_world.domain.node_provider import (
    ManagedLxcBackend,
    ManagedLxcBackendSelection,
    ManagedLxcBackendSelectionStatus,
    NodeProviderKind,
    NodeRole,
    NodeSpec,
    ProviderReadiness,
    ProviderReadinessStatus,
    ProviderSelection,
    ProviderSelectionStatus,
)


class TestNodeProviderSelectionService(unittest.IsolatedAsyncioTestCase):
    async def test_default_lxc_native_selects_single_ready_backend(self):
        readiness = _ReadinessProbe(
            ProviderReadiness(
                provider=NodeProviderKind.LXC_NATIVE,
                status=ProviderReadinessStatus.READY,
                backend_selection=ManagedLxcBackendSelection.for_backend(
                    ManagedLxcBackend.INCUS,
                    evidence={"source": "unit"},
                ),
            )
        )

        selection = await NodeProviderSelectionService(readiness).select_provider()

        self.assertTrue(selection.selected)
        self.assertEqual(NodeProviderKind.LXC_NATIVE, selection.requested_provider)
        self.assertEqual(NodeProviderKind.LXC_NATIVE, selection.selected_provider)
        self.assertEqual(ManagedLxcBackend.INCUS, selection.backend_selection.backend)
        self.assertEqual([(NodeProviderKind.LXC_NATIVE, None)], readiness.calls)

    async def test_explicit_preferred_lxd_backend_is_passed_to_readiness_port(self):
        readiness = _ReadinessProbe(
            ProviderReadiness(
                provider=NodeProviderKind.LXC_NATIVE,
                status=ProviderReadinessStatus.READY,
                backend_selection=ManagedLxcBackendSelection.for_backend(
                    ManagedLxcBackend.LXD,
                    evidence={"source": "unit"},
                ),
            )
        )

        selection = await NodeProviderSelectionService(readiness).select_provider(
            NodeProviderSelectionRequest(
                requested_provider=NodeProviderKind.LXC_NATIVE,
                preferred_backend=ManagedLxcBackend.LXD,
            )
        )

        self.assertTrue(selection.selected)
        self.assertEqual(ManagedLxcBackend.LXD, selection.backend_selection.backend)
        self.assertEqual(
            [(NodeProviderKind.LXC_NATIVE, ManagedLxcBackend.LXD)],
            readiness.calls,
        )

    async def test_ambiguous_incus_and_lxd_blocks_with_remediation(self):
        backend_selection = ManagedLxcBackendSelection.ambiguous(
            candidates=(ManagedLxcBackend.INCUS, ManagedLxcBackend.LXD),
            remediation=("Set a provider backend preference.",),
            evidence={"source": "unit"},
        )
        readiness = _ReadinessProbe(
            ProviderReadiness(
                provider=NodeProviderKind.LXC_NATIVE,
                status=ProviderReadinessStatus.BACKEND_AMBIGUOUS,
                backend_selection=backend_selection,
                remediation=("Both managed LXC backends are usable.",),
            )
        )

        selection = await NodeProviderSelectionService(readiness).select_provider()

        self.assertFalse(selection.selected)
        self.assertTrue(selection.blocks_mutation)
        self.assertEqual(ProviderSelectionStatus.BLOCKED, selection.status)
        self.assertEqual(ManagedLxcBackendSelectionStatus.AMBIGUOUS, selection.backend_selection.status)
        self.assertEqual((ManagedLxcBackend.INCUS, ManagedLxcBackend.LXD), selection.backend_selection.candidates)
        self.assertIn("Set a provider backend preference.", selection.remediation)
        self.assertIn("Both managed LXC backends are usable.", selection.remediation)

    async def test_missing_backend_blocks_without_provider_fallback(self):
        readiness = _ReadinessProbe(
            ProviderReadiness(
                provider=NodeProviderKind.LXC_NATIVE,
                status=ProviderReadinessStatus.BACKEND_MISSING,
                backend_selection=ManagedLxcBackendSelection.missing(
                    remediation=("Install Incus or LXD.",),
                    evidence={"source": "unit"},
                ),
            )
        )

        selection = await NodeProviderSelectionService(readiness).select_provider()

        self.assertFalse(selection.selected)
        self.assertEqual(NodeProviderKind.LXC_NATIVE, selection.requested_provider)
        self.assertEqual(NodeProviderKind.LXC_NATIVE, selection.selected_provider)
        self.assertEqual(ProviderSelectionStatus.BLOCKED, selection.status)
        self.assertEqual(ManagedLxcBackendSelectionStatus.MISSING, selection.backend_selection.status)

    async def test_unsupported_lxc_backend_blocks_without_provider_fallback(self):
        readiness = _ReadinessProbe(
            ProviderReadiness(
                provider=NodeProviderKind.LXC_NATIVE,
                status=ProviderReadinessStatus.BACKEND_UNSUPPORTED,
                backend_selection=ManagedLxcBackendSelection.unsupported(
                    remediation=("Use a supported managed LXC backend.",),
                    evidence={"source": "unit"},
                ),
            )
        )

        selection = await NodeProviderSelectionService(readiness).select_provider()

        self.assertFalse(selection.selected)
        self.assertEqual(NodeProviderKind.LXC_NATIVE, selection.selected_provider)
        self.assertEqual(ManagedLxcBackendSelectionStatus.UNSUPPORTED, selection.backend_selection.status)

    async def test_unsupported_provider_request_blocks_selection(self):
        readiness = _ReadinessProbe(
            ProviderReadiness(
                provider=NodeProviderKind.LXC_NATIVE,
                status=ProviderReadinessStatus.READY,
                backend_selection=ManagedLxcBackendSelection.for_backend(
                    ManagedLxcBackend.INCUS
                ),
            )
        )

        selection = await NodeProviderSelectionService(readiness).select_provider(
            NodeProviderSelectionRequest(requested_provider=NodeProviderKind.UNSUPPORTED)
        )

        self.assertFalse(selection.selected)
        self.assertEqual(ProviderSelectionStatus.UNSUPPORTED, selection.status)
        self.assertEqual([], readiness.calls)

    async def test_blocked_selection_prevents_node_lifecycle_calls(self):
        readiness = _ReadinessProbe(
            ProviderReadiness(
                provider=NodeProviderKind.LXC_NATIVE,
                status=ProviderReadinessStatus.BACKEND_MISSING,
                backend_selection=ManagedLxcBackendSelection.missing(
                    remediation=("Install Incus or LXD.",),
                    evidence={"source": "unit"},
                ),
            )
        )
        lifecycle = _RecordingNodeLifecycle()
        service = NodeProviderSelectionService(readiness, lifecycle)

        result = await service.ensure_node(
            NodeSpec(
                name="swarm-manager",
                role=NodeRole.MANAGER,
                provider=NodeProviderKind.LXC_NATIVE,
            )
        )

        self.assertEqual(VerificationStatus.BLOCKED, result.status)
        self.assertEqual("provider_selection_blocked", result.evidence["reason"])
        self.assertEqual([], lifecycle.ensure_calls)

    async def test_selected_provider_calls_node_lifecycle_port(self):
        readiness = _ReadinessProbe(
            ProviderReadiness(
                provider=NodeProviderKind.LXC_NATIVE,
                status=ProviderReadinessStatus.READY,
                backend_selection=ManagedLxcBackendSelection.for_backend(
                    ManagedLxcBackend.INCUS,
                    evidence={"source": "unit"},
                ),
            )
        )
        lifecycle = _RecordingNodeLifecycle()
        service = NodeProviderSelectionService(readiness, lifecycle)
        node = NodeSpec(
            name="swarm-manager",
            role=NodeRole.MANAGER,
            provider=NodeProviderKind.LXC_NATIVE,
            backend=ManagedLxcBackend.INCUS,
        )

        result = await service.ensure_node(node)

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual(1, len(lifecycle.ensure_calls))
        (ensured_node, selection), = lifecycle.ensure_calls
        self.assertIs(node, ensured_node)
        self.assertEqual(ManagedLxcBackend.INCUS, selection.backend_selection.backend)

    async def test_selected_provider_calls_managed_reset_port(self):
        readiness = _ready_incus_probe()
        teardown = _RecordingManagedNodeTeardown()
        service = NodeProviderSelectionService(
            readiness,
            managed_node_teardown=teardown,
        )
        nodes = (_managed_node("swarm-manager"), _managed_node("swarm-worker-1"))

        result = await service.reset_managed_nodes(nodes)

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual(1, len(teardown.reset_calls))
        (reset_nodes, selection), = teardown.reset_calls
        self.assertEqual(nodes, reset_nodes)
        self.assertEqual(ManagedLxcBackend.INCUS, selection.backend_selection.backend)
        self.assertEqual([], teardown.destroy_calls)

    async def test_destroy_step_calls_managed_destroy_port(self):
        readiness = _ready_incus_probe()
        teardown = _RecordingManagedNodeTeardown()
        service = NodeProviderSelectionService(
            readiness,
            managed_node_teardown=teardown,
        )
        nodes = (_managed_node("swarm-manager"),)
        step = NodeProviderDestroyManagedNodesStep(nodes, service)

        result = await step.run()

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual("platform:destroy:managed-nodes", step.verification_target_id)
        self.assertEqual(1, len(teardown.destroy_calls))
        (destroy_nodes, selection), = teardown.destroy_calls
        self.assertEqual(nodes, destroy_nodes)
        self.assertEqual(ManagedLxcBackend.INCUS, selection.backend_selection.backend)
        self.assertEqual([], teardown.reset_calls)

    async def test_reset_step_calls_managed_reset_port_with_verification_target(self):
        readiness = _ready_incus_probe()
        teardown = _RecordingManagedNodeTeardown()
        service = NodeProviderSelectionService(
            readiness,
            managed_node_teardown=teardown,
        )
        nodes = (_managed_node("swarm-manager"),)
        step = NodeProviderResetManagedNodesStep(nodes, service)

        result = await step.run()

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual("platform:reset:managed-nodes", step.verification_target_id)
        self.assertEqual(1, len(teardown.reset_calls))
        (reset_nodes, selection), = teardown.reset_calls
        self.assertEqual(nodes, reset_nodes)
        self.assertEqual(ManagedLxcBackend.INCUS, selection.backend_selection.backend)
        self.assertEqual([], teardown.destroy_calls)

    async def test_blocked_selection_prevents_managed_reset_port(self):
        readiness = _ReadinessProbe(
            ProviderReadiness(
                provider=NodeProviderKind.LXC_NATIVE,
                status=ProviderReadinessStatus.BACKEND_MISSING,
                backend_selection=ManagedLxcBackendSelection.missing(
                    remediation=("Install Incus or LXD.",),
                    evidence={"source": "unit"},
                ),
            )
        )
        teardown = _RecordingManagedNodeTeardown()
        service = NodeProviderSelectionService(
            readiness,
            managed_node_teardown=teardown,
        )

        result = await service.reset_managed_nodes((_managed_node("swarm-manager"),))

        self.assertEqual(VerificationStatus.BLOCKED, result.status)
        self.assertEqual("provider_selection_blocked", result.evidence["reason"])
        self.assertEqual([], teardown.reset_calls)
        self.assertEqual([], teardown.destroy_calls)

    async def test_missing_teardown_port_blocks_managed_destroy_before_adapter_call(self):
        service = NodeProviderSelectionService(_ready_incus_probe())

        result = await service.destroy_managed_nodes((_managed_node("swarm-manager"),))

        self.assertEqual(VerificationStatus.BLOCKED, result.status)
        self.assertEqual("managed_node_teardown_port_missing", result.evidence["reason"])

    async def test_backend_mismatch_blocks_managed_reset_before_adapter_call(self):
        readiness = _ready_incus_probe()
        teardown = _RecordingManagedNodeTeardown()
        service = NodeProviderSelectionService(
            readiness,
            managed_node_teardown=teardown,
        )
        nodes = (
            _managed_node("swarm-manager"),
            NodeSpec(
                name="swarm-worker-1",
                role=NodeRole.WORKER,
                provider=NodeProviderKind.LXC_NATIVE,
                backend=ManagedLxcBackend.LXD,
            ),
        )

        result = await service.reset_managed_nodes(nodes)

        self.assertEqual(VerificationStatus.BLOCKED, result.status)
        self.assertEqual("reset_node_backend_mismatch", result.evidence["reason"])
        self.assertEqual([], teardown.reset_calls)
        self.assertEqual([], teardown.destroy_calls)

    async def test_reset_step_without_managed_nodes_blocks_before_readiness_probe(self):
        readiness = _ready_incus_probe()
        teardown = _RecordingManagedNodeTeardown()
        service = NodeProviderSelectionService(
            readiness,
            managed_node_teardown=teardown,
        )
        step = NodeProviderResetManagedNodesStep((), service)

        result = await step.run()

        self.assertEqual(VerificationStatus.BLOCKED, result.status)
        self.assertEqual("managed_nodes_missing", result.evidence["reason"])
        self.assertEqual("platform:reset:managed-nodes", result.target_id)
        self.assertEqual([], readiness.calls)
        self.assertEqual([], teardown.reset_calls)


class _ReadinessProbe(PortNodeProviderReadiness):
    def __init__(self, readiness: ProviderReadiness):
        self.readiness = readiness
        self.calls: list[tuple[NodeProviderKind, ManagedLxcBackend | None]] = []

    async def provider_readiness(
        self,
        provider: NodeProviderKind,
        preferred_backend: ManagedLxcBackend | None = None,
    ) -> ProviderReadiness:
        await async_checkpoint()
        self.calls.append((provider, preferred_backend))
        return self.readiness


class _RecordingNodeLifecycle(PortNodeLifecycle):
    def __init__(self):
        self.ensure_calls: list[tuple[NodeSpec, ProviderSelection]] = []

    async def ensure_node(
        self,
        node: NodeSpec,
        selection: ProviderSelection,
    ) -> VerificationResult:
        await async_checkpoint()
        self.ensure_calls.append((node, selection))
        return VerificationResult(
            target_id=f"platform:node:{node.name}",
            status=VerificationStatus.VERIFIED,
            message="Node lifecycle port was called.",
            evidence={"phase": "apply"},
        )


class _RecordingManagedNodeTeardown(PortManagedNodeTeardown):
    def __init__(self):
        self.reset_calls: list[tuple[tuple[NodeSpec, ...], ProviderSelection]] = []
        self.destroy_calls: list[tuple[tuple[NodeSpec, ...], ProviderSelection]] = []

    async def reset_nodes(
        self,
        nodes: Sequence[NodeSpec],
        selection: ProviderSelection,
    ) -> VerificationResult:
        await async_checkpoint()
        self.reset_calls.append((tuple(nodes), selection))
        return VerificationResult(
            target_id="platform:reset:managed-nodes",
            status=VerificationStatus.VERIFIED,
            message="Managed nodes were reset.",
            evidence={"phase": "verify", "classification": "managed_nodes_reset"},
        )

    async def destroy_nodes(
        self,
        nodes: Sequence[NodeSpec],
        selection: ProviderSelection,
    ) -> VerificationResult:
        await async_checkpoint()
        self.destroy_calls.append((tuple(nodes), selection))
        return VerificationResult(
            target_id="platform:destroy:managed-nodes",
            status=VerificationStatus.VERIFIED,
            message="Managed nodes were destroyed.",
            evidence={"phase": "verify", "classification": "managed_nodes_destroyed"},
        )


def _ready_incus_probe() -> _ReadinessProbe:
    return _ReadinessProbe(
        ProviderReadiness(
            provider=NodeProviderKind.LXC_NATIVE,
            status=ProviderReadinessStatus.READY,
            backend_selection=ManagedLxcBackendSelection.for_backend(
                ManagedLxcBackend.INCUS,
                evidence={"source": "unit"},
            ),
        )
    )


def _managed_node(name: str) -> NodeSpec:
    return NodeSpec(
        name=name,
        role=NodeRole.MANAGER if name == "swarm-manager" else NodeRole.WORKER,
        provider=NodeProviderKind.LXC_NATIVE,
        backend=ManagedLxcBackend.INCUS,
    )


if __name__ == "__main__":
    unittest.main()
