import unittest
from collections.abc import Mapping

from tiny_swarm_world.application.ports.configuration import PortConfigurationSource
from tiny_swarm_world.application.services.configuration import ConfigurationValidationService
from tiny_swarm_world.domain.configuration import (
    ConfigurationContract,
    ConfigurationRequirement,
    ConfigurationValueKind,
)


class TestConfigurationValidationService(unittest.TestCase):
    def test_service_validates_values_loaded_from_port(self):
        source = _FakeConfigurationSource({"TSW_EXAMPLE": "1"})
        contract = ConfigurationContract(
            schema_version="1",
            requirements=(
                ConfigurationRequirement(
                    key="TSW_EXAMPLE",
                    scope="example",
                    value_kind=ConfigurationValueKind.POSITIVE_INTEGER,
                    required=True,
                    description="Example integer.",
                ),
            ),
        )

        result = ConfigurationValidationService(source, contract).validate()

        self.assertTrue(result.passed)
        self.assertEqual("environment", result.findings[0].evidence["source"])


class _FakeConfigurationSource(PortConfigurationSource):
    def __init__(self, values: Mapping[str, str]) -> None:
        self.values = dict(values)

    def load(self) -> Mapping[str, str]:
        return dict(self.values)


if __name__ == "__main__":
    unittest.main()
