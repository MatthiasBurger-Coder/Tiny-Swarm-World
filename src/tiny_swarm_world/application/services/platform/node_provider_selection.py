from __future__ import annotations

from dataclasses import dataclass

from tiny_swarm_world.application.ports.node_provider import (
    PortNodeLifecycle,
    PortNodeProviderReadiness,
)
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus
from tiny_swarm_world.domain.node_provider import (
    ManagedLxcBackend,
    ManagedLxcBackendSelection,
    ManagedLxcBackendSelectionStatus,
    NodeProviderKind,
    NodeSpec,
    ProviderReadiness,
    ProviderReadinessStatus,
    ProviderSelection,
    ProviderSelectionStatus,
)


@dataclass(frozen=True)
class NodeProviderSelectionRequest:
    requested_provider: NodeProviderKind = NodeProviderKind.LXC_NATIVE
    preferred_backend: ManagedLxcBackend | None = None


class NodeProviderSelectionService:
    def __init__(
        self,
        readiness_probe: PortNodeProviderReadiness,
        node_lifecycle: PortNodeLifecycle | None = None,
    ):
        self.readiness_probe = readiness_probe
        self.node_lifecycle = node_lifecycle

    async def select_provider(
        self,
        request: NodeProviderSelectionRequest | None = None,
    ) -> ProviderSelection:
        selection_request = request or NodeProviderSelectionRequest()
        if selection_request.requested_provider == NodeProviderKind.MULTIPASS_LEGACY:
            return ProviderSelection.explicit_multipass_legacy(
                remediation=(
                    "Multipass is a legacy provider and must be selected explicitly.",
                )
            )
        if selection_request.requested_provider == NodeProviderKind.UNSUPPORTED:
            return ProviderSelection(
                requested_provider=NodeProviderKind.UNSUPPORTED,
                selected_provider=NodeProviderKind.UNSUPPORTED,
                status=ProviderSelectionStatus.UNSUPPORTED,
                remediation=("Select lxc_native or explicit multipass_legacy.",),
            )

        readiness = await self.readiness_probe.provider_readiness(
            selection_request.requested_provider,
            selection_request.preferred_backend,
        )
        return _selection_from_lxc_readiness(readiness)

    async def ensure_node(
        self,
        node: NodeSpec,
        request: NodeProviderSelectionRequest | None = None,
    ) -> VerificationResult:
        selection_request = request or NodeProviderSelectionRequest(
            requested_provider=node.provider,
            preferred_backend=node.backend,
        )
        selection = await self.select_provider(selection_request)
        if selection.blocks_mutation:
            return _blocked_result(
                selection,
                "Provider selection blocked node lifecycle before apply.",
                "provider_selection_blocked",
            )
        if node.provider != selection.selected_provider:
            return _blocked_result(
                selection,
                "Node provider does not match the selected provider.",
                "node_provider_mismatch",
            )
        if self.node_lifecycle is None:
            return _blocked_result(
                selection,
                "Node lifecycle port is not configured.",
                "node_lifecycle_port_missing",
            )
        return await self.node_lifecycle.ensure_node(node, selection)


def _selection_from_lxc_readiness(readiness: ProviderReadiness) -> ProviderSelection:
    if readiness.provider != NodeProviderKind.LXC_NATIVE:
        raise ValueError("LXC-native selection requires LXC-native readiness")
    if readiness.ready:
        backend_selection = readiness.backend_selection
        if backend_selection is None:
            raise ValueError("ready LXC-native readiness requires backend selection")
        return ProviderSelection.from_lxc_backend_selection(backend_selection)

    backend_selection = _blocked_backend_selection(readiness)
    remediation = _merge_remediation(backend_selection.remediation, readiness.remediation)
    return ProviderSelection(
        requested_provider=NodeProviderKind.LXC_NATIVE,
        selected_provider=NodeProviderKind.LXC_NATIVE,
        status=ProviderSelectionStatus.BLOCKED,
        backend_selection=backend_selection,
        remediation=remediation,
    )


def _blocked_backend_selection(readiness: ProviderReadiness) -> ManagedLxcBackendSelection:
    backend_selection = readiness.backend_selection
    if (
        backend_selection is not None
        and backend_selection.status != ManagedLxcBackendSelectionStatus.SELECTED
    ):
        return backend_selection

    evidence = {"readiness_status": readiness.status.value}
    if readiness.status == ProviderReadinessStatus.BACKEND_MISSING:
        return ManagedLxcBackendSelection.missing(
            remediation=readiness.remediation,
            evidence=evidence,
        )
    return ManagedLxcBackendSelection.unsupported(
        remediation=readiness.remediation,
        evidence=evidence,
    )


def _blocked_result(
    selection: ProviderSelection,
    message: str,
    reason: str,
) -> VerificationResult:
    return VerificationResult(
        target_id=f"platform:node-provider:{selection.requested_provider.value}",
        status=VerificationStatus.BLOCKED,
        message=message,
        evidence={
            "phase": "pre_apply",
            "reason": reason,
            "requested_provider": selection.requested_provider.value,
            "selection_status": selection.status.value,
        },
    )


def _merge_remediation(
    backend_remediation: tuple[str, ...],
    readiness_remediation: tuple[str, ...],
) -> tuple[str, ...]:
    merged: list[str] = []
    for item in (*backend_remediation, *readiness_remediation):
        if item not in merged:
            merged.append(item)
    return tuple(merged)
