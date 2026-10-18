from __future__ import annotations

from collections.abc import Mapping

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
        self._values: Mapping[str, str] | None = None

    def freeze(self) -> None:
        if self._values is None:
            self._values = dict(self.configuration_source.load())

    def validate(self) -> ConfigurationValidationResult:
        return self.contract.validate(
            self._values if self._values is not None else self.configuration_source.load()
        )

    def for_scopes(self, scopes: set[str]) -> ConfigurationValidationService:
        """Reuse frozen inputs while validating only active consumers."""
        selected = ConfigurationValidationService(
            self.configuration_source,
            ConfigurationContract(self.contract.schema_version, tuple(
                item for item in self.contract.requirements if item.scope in scopes
            )),
        )
        selected._values = self._values
        return selected
