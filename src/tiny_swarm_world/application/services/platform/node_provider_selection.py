from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from tiny_swarm_world.application.ports.node_provider import (
    PortManagedNodeTeardown,
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
    backend_candidates: tuple[ManagedLxcBackend, ...] = (
        ManagedLxcBackend.INCUS,
        ManagedLxcBackend.LXD,
    )


class NodeProviderSelectionService:
    def __init__(
        self,
        readiness_probe: PortNodeProviderReadiness,
        node_lifecycle: PortNodeLifecycle | None = None,
        managed_node_teardown: PortManagedNodeTeardown | None = None,
    ):
        self.readiness_probe = readiness_probe
        self.node_lifecycle = node_lifecycle
        self.managed_node_teardown = managed_node_teardown

    async def select_provider(
        self,
        request: NodeProviderSelectionRequest | None = None,
    ) -> ProviderSelection:
        selection_request = request or NodeProviderSelectionRequest()
        if selection_request.requested_provider == NodeProviderKind.UNSUPPORTED:
            return ProviderSelection(
                requested_provider=NodeProviderKind.UNSUPPORTED,
                selected_provider=NodeProviderKind.UNSUPPORTED,
                status=ProviderSelectionStatus.UNSUPPORTED,
                remediation=("Select lxc_native.",),
            )

        readiness = await self.readiness_probe.provider_readiness(
            selection_request.requested_provider,
            selection_request.preferred_backend,
            selection_request.backend_candidates,
        )
        return _selection_from_lxc_readiness(readiness)

    async def verify_provider_selection(
        self,
        request: NodeProviderSelectionRequest | None = None,
    ) -> VerificationResult:
        selection = await self.select_provider(request)
        if selection.blocks_mutation:
            return _blocked_result(
                selection,
                "Provider selection blocked platform mutation.",
                "provider_selection_blocked",
            )
        return VerificationResult(
            target_id=f"platform:node-provider:{selection.requested_provider.value}",
            status=VerificationStatus.VERIFIED,
            message="Provider selection is ready for platform mutation.",
            evidence=_selection_evidence(selection, "provider_selected"),
        )

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

    async def verify_node(
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
                "Provider selection blocked managed node verification.",
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
        return await self.node_lifecycle.verify_node(node, selection)

    async def reset_managed_nodes(
        self,
        nodes: tuple[NodeSpec, ...],
        request: NodeProviderSelectionRequest | None = None,
    ) -> VerificationResult:
        selection_result = await self._selection_for_managed_node_teardown(
            "reset",
            nodes,
            request,
        )
        if isinstance(selection_result, VerificationResult):
            return selection_result
        assert self.managed_node_teardown is not None
        return await self.managed_node_teardown.reset_nodes(nodes, selection_result)

    async def destroy_managed_nodes(
        self,
        nodes: tuple[NodeSpec, ...],
        request: NodeProviderSelectionRequest | None = None,
    ) -> VerificationResult:
        selection_result = await self._selection_for_managed_node_teardown(
            "destroy",
            nodes,
            request,
        )
        if isinstance(selection_result, VerificationResult):
            return selection_result
        assert self.managed_node_teardown is not None
        return await self.managed_node_teardown.destroy_nodes(nodes, selection_result)

    async def _selection_for_managed_node_teardown(
        self,
        operation: Literal["reset", "destroy"],
        nodes: tuple[NodeSpec, ...],
        request: NodeProviderSelectionRequest | None,
    ) -> ProviderSelection | VerificationResult:
        if not nodes:
            return VerificationResult(
                target_id=f"platform:{operation}:managed-nodes",
                status=VerificationStatus.BLOCKED,
                message=f"No managed nodes are configured for platform {operation}.",
                evidence={"phase": "pre_apply", "reason": "managed_nodes_missing"},
            )

        selection_request = request or NodeProviderSelectionRequest(
            requested_provider=nodes[0].provider,
            preferred_backend=nodes[0].backend,
        )
        selection = await self.select_provider(selection_request)
        if selection.blocks_mutation:
            return _blocked_result(
                selection,
                f"Provider selection blocked managed node {operation} before apply.",
                "provider_selection_blocked",
            )

        mismatched_node = next(
            (node for node in nodes if node.provider != selection.selected_provider),
            None,
        )
        if mismatched_node is not None:
            return _blocked_result(
                selection,
                f"Managed node {operation} provider does not match the selected provider.",
                f"{operation}_node_provider_mismatch",
            )
        backend_mismatched_node = _first_backend_mismatch(nodes, selection)
        if backend_mismatched_node is not None:
            return _blocked_result(
                selection,
                f"Managed node {operation} backend does not match the selected backend.",
                f"{operation}_node_backend_mismatch",
            )
        if self.managed_node_teardown is None:
            return _blocked_result(
                selection,
                "Managed node teardown port is not configured.",
                "managed_node_teardown_port_missing",
            )
        return selection


class NodeProviderEnsureNodeStep:
    returns_verification_result = True

    def __init__(
        self,
        node: NodeSpec,
        provider_selection: NodeProviderSelectionService,
        request: NodeProviderSelectionRequest | None = None,
    ):
        self.node = node
        self.provider_selection = provider_selection
        self.request = request
        self.verification_target_id = f"platform:node:{node.name}"

    async def run(self) -> VerificationResult:
        return await self.provider_selection.ensure_node(self.node, self.request)


class NodeProviderVerifyNodeStep:
    returns_verification_result = True

    def __init__(
        self,
        node: NodeSpec,
        provider_selection: NodeProviderSelectionService,
        request: NodeProviderSelectionRequest | None = None,
    ):
        self.node = node
        self.provider_selection = provider_selection
        self.request = request
        self.verification_target_id = f"platform:node:{node.name}"

    async def run(self) -> VerificationResult:
        return await self.provider_selection.verify_node(self.node, self.request)


class NodeProviderResetManagedNodesStep:
    returns_verification_result = True
    verification_target_id = "platform:reset:managed-nodes"

    def __init__(
        self,
        nodes: tuple[NodeSpec, ...],
        provider_selection: NodeProviderSelectionService,
        request: NodeProviderSelectionRequest | None = None,
    ):
        self.nodes = tuple(nodes)
        self.provider_selection = provider_selection
        self.request = request

    async def run(self) -> VerificationResult:
        return await self.provider_selection.reset_managed_nodes(self.nodes, self.request)


class NodeProviderDestroyManagedNodesStep:
    returns_verification_result = True
    verification_target_id = "platform:destroy:managed-nodes"

    def __init__(
        self,
        nodes: tuple[NodeSpec, ...],
        provider_selection: NodeProviderSelectionService,
        request: NodeProviderSelectionRequest | None = None,
    ):
        self.nodes = tuple(nodes)
        self.provider_selection = provider_selection
        self.request = request

    async def run(self) -> VerificationResult:
        return await self.provider_selection.destroy_managed_nodes(self.nodes, self.request)


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


def _first_backend_mismatch(
    nodes: tuple[NodeSpec, ...],
    selection: ProviderSelection,
) -> NodeSpec | None:
    backend_selection = selection.backend_selection
    if backend_selection is None or backend_selection.backend is None:
        return None
    return next(
        (
            node
            for node in nodes
            if node.backend is not None and node.backend != backend_selection.backend
        ),
        None,
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
        evidence=_selection_evidence(selection, reason),
    )


def _selection_evidence(
    selection: ProviderSelection,
    reason: str,
) -> dict[str, str]:
    evidence = {
        "phase": "pre_apply",
        "reason": reason,
        "requested_provider": selection.requested_provider.value,
        "selected_provider": selection.selected_provider.value,
        "selection_status": selection.status.value,
        "remediation_count": str(len(selection.remediation)),
    }
    backend_selection = selection.backend_selection
    if backend_selection is None:
        return evidence

    evidence["backend_status"] = backend_selection.status.value
    evidence["backend_candidate_count"] = str(len(backend_selection.candidates))
    if backend_selection.backend is not None:
        evidence["selected_backend"] = backend_selection.backend.value
    if backend_selection.candidates:
        evidence["backend_candidates"] = ",".join(
            candidate.value for candidate in backend_selection.candidates
        )
    for key, value in backend_selection.evidence.items():
        if key.startswith(("selected_", "skipped_")):
            evidence[key] = value
    return evidence


def _merge_remediation(
    backend_remediation: tuple[str, ...],
    readiness_remediation: tuple[str, ...],
) -> tuple[str, ...]:
    merged: list[str] = []
    for item in (*backend_remediation, *readiness_remediation):
        if item not in merged:
            merged.append(item)
    return tuple(merged)
