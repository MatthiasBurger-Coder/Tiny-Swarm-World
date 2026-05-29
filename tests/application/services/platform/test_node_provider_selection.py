import unittest
from tests.support.async_helpers import async_checkpoint

from tiny_swarm_world.application.ports.node_provider import (
    PortNodeLifecycle,
    PortNodeProviderReadiness,
)
from tiny_swarm_world.application.services.platform.node_provider_selection import (
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

    async def test_missing_backend_blocks_without_multipass_fallback(self):
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
        self.assertNotEqual(NodeProviderKind.MULTIPASS_LEGACY, selection.selected_provider)
        self.assertEqual(ProviderSelectionStatus.BLOCKED, selection.status)
        self.assertEqual(ManagedLxcBackendSelectionStatus.MISSING, selection.backend_selection.status)

    async def test_unsupported_lxc_backend_blocks_without_multipass_fallback(self):
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
        self.assertNotEqual(NodeProviderKind.MULTIPASS_LEGACY, selection.selected_provider)
        self.assertEqual(ManagedLxcBackendSelectionStatus.UNSUPPORTED, selection.backend_selection.status)

    async def test_explicit_multipass_legacy_selection_is_operator_visible(self):
        readiness = _ReadinessProbe(
            ProviderReadiness(
                provider=NodeProviderKind.LXC_NATIVE,
                status=ProviderReadinessStatus.BACKEND_MISSING,
                backend_selection=ManagedLxcBackendSelection.missing(),
            )
        )

        selection = await NodeProviderSelectionService(readiness).select_provider(
            NodeProviderSelectionRequest(
                requested_provider=NodeProviderKind.MULTIPASS_LEGACY,
            )
        )

        self.assertTrue(selection.selected)
        self.assertEqual(NodeProviderKind.MULTIPASS_LEGACY, selection.requested_provider)
        self.assertEqual(NodeProviderKind.MULTIPASS_LEGACY, selection.selected_provider)
        self.assertIn("explicitly", " ".join(selection.remediation))
        self.assertEqual([], readiness.calls)

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
        ensure_call, = lifecycle.ensure_calls
        self.assertIs(node, ensure_call[0])
        self.assertEqual(ManagedLxcBackend.INCUS, ensure_call[1].backend_selection.backend)


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


if __name__ == "__main__":
    unittest.main()
