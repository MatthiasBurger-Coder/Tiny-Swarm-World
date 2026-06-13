from __future__ import annotations

from tiny_swarm_world.application.ports.configuration import PortConfigurationSource
from tiny_swarm_world.domain.configuration import (
    ConfigurationContract,
    ConfigurationValidationResult,
    default_configuration_contract,
)


class ConfigurationValidationService:
    def __init__(
        self,
        configuration_source: PortConfigurationSource,
        contract: ConfigurationContract | None = None,
    ) -> None:
        self.configuration_source = configuration_source
        self.contract = contract or default_configuration_contract()

    def validate(self) -> ConfigurationValidationResult:
        return self.contract.validate(self.configuration_source.load())
