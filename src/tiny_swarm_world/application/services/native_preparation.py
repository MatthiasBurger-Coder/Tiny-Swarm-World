"""Reconcile qualified host packages without owning APT or host probes."""

from __future__ import annotations

from dataclasses import dataclass

from tiny_swarm_world.application.ports.native_preparation import (
    HostPackageManager,
    NativeHostInspector,
)
from tiny_swarm_world.domain.native_preparation import (
    HOST_PACKAGES_BY_PROFILE,
    SUPPORTED_UBUNTU_RELEASES,
    NativeHostFacts,
    qualification_failures,
)


@dataclass(frozen=True)
class NativePreparationPlan:
    facts: NativeHostFacts
    missing_packages: tuple[str, ...]
    failures: tuple[str, ...]

    @property
    def qualified(self) -> bool:
        return not self.failures


class NativePreparationService:
    def __init__(
        self,
        inspector: NativeHostInspector,
        packages: HostPackageManager,
        *,
        service_profile: str = "service-access",
    ) -> None:
        if service_profile not in HOST_PACKAGES_BY_PROFILE:
            raise ValueError("Unsupported native service profile.")
        self._inspector = inspector
        self._packages = packages
        self._service_profile = service_profile
        self._host_packages = HOST_PACKAGES_BY_PROFILE[service_profile]

    def plan(self) -> NativePreparationPlan:
        facts = self._inspector.inspect()
        # Avoid invoking a platform package manager on unsupported hosts.
        supported = (
            facts.platform == "Linux"
            and not facts.is_wsl
            and facts.distribution_id == "ubuntu"
            and facts.version_id in SUPPORTED_UBUNTU_RELEASES
            and facts.architecture == "x86_64"
        )
        missing = self._packages.missing(self._host_packages) if supported else ()
        failures = qualification_failures(
            facts, needs_network=bool(missing), needs_ports=bool(missing),
            needs_privilege=bool(missing), service_profile=self._service_profile,
        )
        return NativePreparationPlan(facts, missing, failures)

    def apply(self, plan: NativePreparationPlan) -> tuple[str, ...]:
        if not plan.qualified:
            raise ValueError("Native Linux preflight failed; package installation was not started.")
        if not plan.missing_packages:
            return ()
        # Recheck observed state after operator confirmation. A changed host
        # must pass the full qualification again before APT is called.
        current = self.plan()
        if not current.qualified:
            raise ValueError("Native Linux preflight changed; package installation was not started.")
        if current.missing_packages != plan.missing_packages:
            raise ValueError("Host package plan changed; review and confirm again.")
        if not current.missing_packages:
            return ()
        self._packages.install(current.missing_packages)
        remaining = self._packages.missing(current.missing_packages)
        if remaining:
            raise RuntimeError("Host package verification failed after installation.")
        return current.missing_packages
