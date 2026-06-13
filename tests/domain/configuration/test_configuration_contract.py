import unittest

from tiny_swarm_world.domain.configuration import (
    ConfigurationContract,
    ConfigurationRequirement,
    ConfigurationStatus,
    ConfigurationValueKind,
    default_configuration_contract,
)


class TestConfigurationContract(unittest.TestCase):
    def test_required_secret_missing_fails_without_leaking_value(self):
        contract = ConfigurationContract(
            schema_version="1",
            requirements=(
                ConfigurationRequirement(
                    key="TSW_EXAMPLE_PASSWORD",
                    scope="example",
                    value_kind=ConfigurationValueKind.SECRET_VALUE,
                    required=True,
                    description="Example password.",
                ),
            ),
        )

        result = contract.validate({})

        self.assertFalse(result.passed)
        self.assertEqual("TSW_EXAMPLE_PASSWORD", result.failed_findings[0].key)
        self.assertEqual(ConfigurationStatus.FAILED, result.failed_findings[0].status)
        self.assertNotIn("secret-value", repr(result.to_dict()))

    def test_secret_value_passes_without_exposing_value(self):
        contract = ConfigurationContract(
            schema_version="1",
            requirements=(
                ConfigurationRequirement(
                    key="TSW_EXAMPLE_PASSWORD",
                    scope="example",
                    value_kind=ConfigurationValueKind.SECRET_VALUE,
                    required=True,
                    description="Example password.",
                ),
            ),
        )

        result = contract.validate({"TSW_EXAMPLE_PASSWORD": "secret-value"})

        self.assertTrue(result.passed)
        self.assertNotIn("secret-value", repr(result.to_dict()))

    def test_invalid_url_with_credentials_fails(self):
        contract = ConfigurationContract(
            schema_version="1",
            requirements=(
                ConfigurationRequirement(
                    key="TSW_EXAMPLE",
                    scope="example",
                    value_kind=ConfigurationValueKind.URL,
                    required=True,
                    description="Example URL.",
                ),
            ),
        )

        result = contract.validate({"TSW_EXAMPLE": "https://user:pass@example.test"})

        self.assertFalse(result.passed)
        self.assertIn("credentials", result.failed_findings[0].message)

    def test_optional_default_is_validated_and_reported_as_default_source(self):
        contract = ConfigurationContract(
            schema_version="1",
            requirements=(
                ConfigurationRequirement(
                    key="TSW_EXAMPLE",
                    scope="example",
                    value_kind=ConfigurationValueKind.POSITIVE_INTEGER,
                    required=False,
                    default="5",
                    description="Example integer.",
                ),
            ),
        )

        result = contract.validate({})

        self.assertTrue(result.passed)
        self.assertEqual("default", result.findings[0].evidence["source"])

    def test_invalid_defaults_are_rejected_when_contract_is_created(self):
        with self.assertRaises(ValueError):
            ConfigurationRequirement(
                key="TSW_EXAMPLE",
                scope="example",
                value_kind=ConfigurationValueKind.POSITIVE_INTEGER,
                required=False,
                default="0",
                description="Example integer.",
            )

    def test_default_contract_covers_runtime_required_postgres_and_redis_secrets(self):
        keys = {requirement.key for requirement in default_configuration_contract().requirements}

        self.assertIn("TSW_SONARQUBE_POSTGRES_PASSWORD", keys)
        self.assertIn("TSW_INFISICAL_REDIS_PASSWORD", keys)


if __name__ == "__main__":
    unittest.main()
