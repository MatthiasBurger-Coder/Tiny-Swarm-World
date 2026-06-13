import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tiny_swarm_world.application.services.configuration import ConfigurationValidationService
from tiny_swarm_world.domain.configuration import (
    ConfigurationContract,
    ConfigurationRequirement,
    ConfigurationValueKind,
)
from tiny_swarm_world.infrastructure.adapters.configuration import (
    CombinedConfigurationSource,
    ConfigurationSourceError,
    EnvironmentConfigurationSource,
    ShellEnvFileConfigurationSource,
)


class TestConfigurationSources(unittest.TestCase):
    def test_environment_source_filters_tsw_keys(self):
        source = EnvironmentConfigurationSource(
            {
                "TSW_EXAMPLE": "value",
                "PATH": "/usr/bin",
            }
        )

        self.assertEqual({"TSW_EXAMPLE": "value"}, source.load())

    def test_missing_env_file_returns_empty_mapping(self):
        with TemporaryDirectory() as temporary_directory:
            source = ShellEnvFileConfigurationSource(Path(temporary_directory) / "missing.env")

            self.assertEqual({}, source.load())

    def test_shell_env_file_parses_comments_export_and_quotes(self):
        with TemporaryDirectory() as temporary_directory:
            env_file = Path(temporary_directory) / "operator.env"
            env_file.write_text(
                "\n".join(
                    (
                        "# local operator values",
                        "export TSW_EXAMPLE='quoted value'",
                        "TSW_OTHER=plain",
                        "PATH=/ignored",
                    )
                )
                + "\n",
                encoding="utf-8",
            )

            values = ShellEnvFileConfigurationSource(env_file).load()

            self.assertEqual(
                {
                    "TSW_EXAMPLE": "quoted value",
                    "TSW_OTHER": "plain",
                },
                values,
            )

    def test_shell_env_file_duplicate_key_fails_without_value(self):
        with TemporaryDirectory() as temporary_directory:
            env_file = Path(temporary_directory) / "operator.env"
            env_file.write_text(
                "TSW_EXAMPLE='first-secret'\nTSW_EXAMPLE='second-secret'\n",
                encoding="utf-8",
            )

            with self.assertRaises(ConfigurationSourceError) as failure:
                ShellEnvFileConfigurationSource(env_file).load()

        message = str(failure.exception)
        self.assertIn("TSW_EXAMPLE", message)
        self.assertIn("lines 1 and 2", message)
        self.assertNotIn("first-secret", message)
        self.assertNotIn("second-secret", message)

    def test_shell_env_file_rejects_command_substitution_without_execution(self):
        with TemporaryDirectory() as temporary_directory:
            env_file = Path(temporary_directory) / "operator.env"
            marker = Path(temporary_directory) / "marker"
            env_file.write_text(
                f"TSW_EXAMPLE=$(touch {marker})\n",
                encoding="utf-8",
            )

            with self.assertRaises(ConfigurationSourceError):
                ShellEnvFileConfigurationSource(env_file).load()

            self.assertFalse(marker.exists())

    def test_combined_source_lets_later_sources_override_earlier_sources(self):
        combined = CombinedConfigurationSource(
            (
                EnvironmentConfigurationSource({"TSW_EXAMPLE": "from-file"}),
                EnvironmentConfigurationSource({"TSW_EXAMPLE": "from-env"}),
            )
        )

        self.assertEqual({"TSW_EXAMPLE": "from-env"}, combined.load())

    def test_loaded_values_validate_through_application_service_without_value_leak(self):
        with TemporaryDirectory() as temporary_directory:
            env_file = Path(temporary_directory) / "operator.env"
            env_file.write_text("TSW_EXAMPLE_PASSWORD='secret-value'\n", encoding="utf-8")
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

            result = ConfigurationValidationService(
                ShellEnvFileConfigurationSource(env_file),
                contract,
            ).validate()

        self.assertTrue(result.passed)
        self.assertNotIn("secret-value", repr(result.to_dict()))


if __name__ == "__main__":
    unittest.main()
