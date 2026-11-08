from __future__ import annotations

from tiny_swarm_world.application.ports.clients.port_swarm_stack_runtime import (
    PortSwarmStackRuntime,
)


class EnsureExternalSwarmSecret:
    verification_target_id = "deployment:service-access-external-input"

    def __init__(
        self,
        swarm_runtime: PortSwarmStackRuntime,
        resource_name: str,
        resource_value: str,
        verification_target_id: str | None = None,
    ):
        if not resource_name:
            raise ValueError("external Swarm input name must not be empty")
        if not resource_value:
            raise ValueError("external Swarm input value must not be empty")
        self.swarm_runtime = swarm_runtime
        self.resource_name = resource_name
        self.resource_value = resource_value
        self.verification_target_id = verification_target_id or type(self).verification_target_id
        self.deployment_target_id = self.verification_target_id

    def run(self) -> None:
        self.swarm_runtime.ensure_external_secret(self.resource_name, self.resource_value)
