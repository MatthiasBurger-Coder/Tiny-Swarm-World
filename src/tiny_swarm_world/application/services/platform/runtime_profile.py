from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from tiny_swarm_world.application.services.platform.node_provider_selection import (
    NodeProviderSelectionRequest,
)
from tiny_swarm_world.domain.deployment import ServiceStackProfile
from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
from tiny_swarm_world.domain.node_provider import ManagedLxcBackend, NodeProviderKind


class RuntimeProfileResolutionStatus(str, Enum):
    RESOLVED = "resolved"
    UNSUPPORTED = "unsupported"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class RuntimeProfileResolutionRequest:
    """Validated intent and observed platform capabilities for resolution."""

    service_profile: ServiceStackProfile | str
    provider_request: NodeProviderSelectionRequest
    host_environment: HostEnvironmentKind | None = None
    available_backends: tuple[ManagedLxcBackend, ...] = ()
    supported_backends: tuple[ManagedLxcBackend, ...] = (
        ManagedLxcBackend.INCUS,
        ManagedLxcBackend.LXD,
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "available_backends", tuple(self.available_backends))
        object.__setattr__(self, "supported_backends", tuple(self.supported_backends))


@dataclass(frozen=True)
class ResolvedRuntimeProfile:
    """The canonical runtime/profile decision consumed by composition."""

    service_profile: ServiceStackProfile
    requested_provider: NodeProviderKind
    backend: ManagedLxcBackend | None
    host_environment: HostEnvironmentKind | None
    available_backends: tuple[ManagedLxcBackend, ...]
    status: RuntimeProfileResolutionStatus
    remediation: tuple[str, ...] = ()

    @property
    def resolved(self) -> bool:
        return self.status is RuntimeProfileResolutionStatus.RESOLVED


class RuntimeProfileResolver:
    """Own deterministic service-profile and runtime capability resolution."""

    def resolve(
        self,
        request: RuntimeProfileResolutionRequest,
    ) -> ResolvedRuntimeProfile:
        service_profile = ServiceStackProfile(request.service_profile)
        provider = request.provider_request.requested_provider
        available_backends = tuple(
            backend
            for backend in request.available_backends
            if backend in request.supported_backends
        )

        if provider is not NodeProviderKind.LXC_NATIVE:
            return ResolvedRuntimeProfile(
                service_profile,
                provider,
                None,
                request.host_environment,
                available_backends,
                RuntimeProfileResolutionStatus.UNSUPPORTED,
                ("Select lxc_native.",),
            )

        preferred = request.provider_request.preferred_backend
        if preferred is not None:
            if preferred not in request.supported_backends:
                return self._unavailable(
                    service_profile,
                    provider,
                    request,
                    available_backends,
                    "The preferred managed LXC backend is unsupported.",
                )
            return self._resolved(
                service_profile,
                provider,
                preferred,
                request,
                available_backends,
            )

        for candidate in request.provider_request.backend_candidates:
            if candidate in available_backends:
                return self._resolved(
                    service_profile,
                    provider,
                    candidate,
                    request,
                    available_backends,
                )

        return self._unavailable(
            service_profile,
            provider,
            request,
            available_backends,
            "No configured managed LXC backend is available.",
        )

    @staticmethod
    def _resolved(
        service_profile: ServiceStackProfile,
        provider: NodeProviderKind,
        backend: ManagedLxcBackend,
        request: RuntimeProfileResolutionRequest,
        available_backends: tuple[ManagedLxcBackend, ...],
    ) -> ResolvedRuntimeProfile:
        return ResolvedRuntimeProfile(
            service_profile,
            provider,
            backend,
            request.host_environment,
            available_backends,
            RuntimeProfileResolutionStatus.RESOLVED,
        )

    @staticmethod
    def _unavailable(
        service_profile: ServiceStackProfile,
        provider: NodeProviderKind,
        request: RuntimeProfileResolutionRequest,
        available_backends: tuple[ManagedLxcBackend, ...],
        remediation: str,
    ) -> ResolvedRuntimeProfile:
        return ResolvedRuntimeProfile(
            service_profile,
            provider,
            None,
            request.host_environment,
            available_backends,
            RuntimeProfileResolutionStatus.UNAVAILABLE,
            (remediation,),
        )
