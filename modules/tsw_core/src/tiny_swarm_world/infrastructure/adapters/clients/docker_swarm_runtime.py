"""Docker Swarm runtime adapter exposed to application deployment services."""

from __future__ import annotations

from collections.abc import Mapping

from tiny_swarm_world.application.ports.clients.port_swarm_stack_runtime import (
    PortSwarmStackRuntime,
    SwarmServiceStatus,
)
from tiny_swarm_world.domain.deployment import StackDefinition


class DockerSwarmRuntime(PortSwarmStackRuntime):
    """Adapt the configured Docker Swarm transport to the application port.

    The delegate owns transport-specific concerns such as managed-LXC shell
    execution. This adapter keeps the application-facing runtime boundary
    independent from that concrete transport.
    """

    def __init__(self, delegate: PortSwarmStackRuntime) -> None:
        self._delegate = delegate

    def deploy_stack(
        self,
        stack_definition: StackDefinition,
        stack_environment: Mapping[str, str] | None = None,
    ) -> None:
        self._delegate.deploy_stack(stack_definition, stack_environment)

    def stack_exists(self, stack_name: str) -> bool:
        return self._delegate.stack_exists(stack_name)

    def list_stack_services(self, stack_name: str) -> tuple[SwarmServiceStatus, ...]:
        return self._delegate.list_stack_services(stack_name)

    def external_secret_exists(self, name: str) -> bool:
        return self._delegate.external_secret_exists(name)

    def ensure_external_secret(self, name: str, value: str) -> None:
        self._delegate.ensure_external_secret(name, value)

    def recover_infisical_migration_lock(self) -> bool:
        """Preserve the existing recovery hook used by composition bootstrap."""
        recovery = getattr(self._delegate, "recover_infisical_migration_lock")
        return recovery()
