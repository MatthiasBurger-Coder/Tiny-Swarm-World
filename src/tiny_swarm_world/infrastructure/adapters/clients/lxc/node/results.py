"""Shared LXC node result serialization for lifecycle and qualification."""

from __future__ import annotations

from collections.abc import Mapping

from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus
from tiny_swarm_world.domain.node_provider import (
    ManagedLxcBackend,
    NodeProviderKind,
    NodeSpec,
    ProviderSelection,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc.node.evidence import (
    EvidenceBuilder,
)


def blocked(
    node: NodeSpec,
    selection: ProviderSelection,
    reason: str,
    *,
    backend: ManagedLxcBackend | None = None,
    return_code: int | None = None,
    timed_out: bool = False,
    extra_evidence: Mapping[str, str] | None = None,
) -> VerificationResult:
    evidence = node_evidence(
        "pre_apply",
        reason,
        node,
        backend,
        return_code=return_code,
        timed_out=timed_out,
        selection_status=selection.status.value,
    )
    if extra_evidence:
        evidence.update(extra_evidence)
    return VerificationResult(
        target_id=node_target_id(node),
        status=VerificationStatus.BLOCKED,
        message="LXC node lifecycle is blocked before mutation.",
        evidence=evidence,
    )


def node_evidence(
    phase: str,
    classification: str,
    node: NodeSpec,
    backend: ManagedLxcBackend | None,
    *,
    lifecycle_outcome: str | None = None,
    return_code: int | None = None,
    timed_out: bool = False,
    selection_status: str | None = None,
    applied: bool = False,
) -> dict[str, str]:
    return (
        EvidenceBuilder()
        .add("phase", phase)
        .add("classification", classification)
        .add("provider", NodeProviderKind.LXC_NATIVE.value)
        .add("node", node.name)
        .add("node_name", node.name)
        .add("backend", backend.value if backend is not None else None)
        .add("lifecycle_outcome", lifecycle_outcome)
        .add("return_code", return_code)
        .add("timed_out", timed_out if timed_out else None)
        .add("selection_status", selection_status)
        .add("applied", applied if applied else None)
        .build()
    )


def node_target_id(node: NodeSpec) -> str:
    return f"platform:node:{node.name}"
