import unittest
from pathlib import Path
from typing import Any, cast

from tiny_swarm_world.domain.command.command_entity import CommandCatalogValidationError
from tiny_swarm_world.infrastructure.adapters.file_management.file_manager import FileManager
from tiny_swarm_world.infrastructure.adapters.repositories.command_repository_yaml import (
    PortCommandRepositoryYaml,
)
from tiny_swarm_world.infrastructure.project_paths import config_root


class TestCommandRepositoryYamlContract(unittest.TestCase):
    def test_repository_rejects_missing_command_id_from_synthetic_yaml(self):
        yaml_content = _catalog_yaml(
            """
  - index: 1
    description: Test command
    intent: test_command
    execution_mode: shell
    safety_class: safe_read
    scope: host
    allowed_workflows:
      - platform:init
    parameters: []
    effects:
      - read
    verify:
      type: none
      description: Read-only command.
    command: "docker ps"
    runner: "async"
    command_type: "hostos"
    vm_type:
      - "none"
"""
        )

        with self.assertRaises(CommandCatalogValidationError):
            _repository_for(yaml_content).get_all_commands()

    def test_repository_rejects_duplicate_command_ids(self):
        yaml_content = _catalog_yaml(_command_yaml(command_id="duplicate.001", index=1))
        yaml_content = yaml_content + _command_yaml(command_id="duplicate.001", index=2)

        with self.assertRaises(CommandCatalogValidationError):
            _repository_for(yaml_content).get_all_commands()

    def test_repository_rejects_duplicate_indexes(self):
        yaml_content = _catalog_yaml(_command_yaml(command_id="first.001", index=1))
        yaml_content = yaml_content + _command_yaml(command_id="second.001", index=1)

        with self.assertRaises(CommandCatalogValidationError):
            _repository_for(yaml_content).get_all_commands()

    def test_repository_rejects_destructive_shell_string_without_destructive_class(self):
        yaml_content = _catalog_yaml(
            _command_yaml(command_id="unsafe.001", command="docker system prune --all")
        )

        with self.assertRaises(CommandCatalogValidationError):
            _repository_for(yaml_content).get_all_commands()

    def test_repository_rejects_mutating_command_without_verify_spec(self):
        yaml_content = _catalog_yaml(
            _command_yaml(
                command_id="unsafe-mutation.001",
                command="echo mutate",
                safety_class="safe_mutation",
                effects=("modify",),
                verify_type="none",
            )
        )

        with self.assertRaises(CommandCatalogValidationError):
            _repository_for(yaml_content).get_all_commands()

    def test_repository_rejects_credential_output_without_redacted_policy(self):
        yaml_content = _catalog_yaml(
            _command_yaml(
                command_id="unsafe-credential-output.001",
                command="docker swarm join-token -q worker",
                safety_class="credential_mutation",
                effects=("read", "credential_output"),
                verify_type="manual",
            )
        )

        with self.assertRaises(CommandCatalogValidationError):
            _repository_for(yaml_content).get_all_commands()

    def test_repository_loads_all_product_command_yaml_files_with_typed_contract(self):
        command_ids: set[str] = set()

        for config_file in sorted(config_root().rglob("command_*.yaml")):
            with self.subTest(config_file=config_file.name):
                commands = PortCommandRepositoryYaml(config_file.name).get_all_commands()
                self.assertGreaterEqual(len(commands), 1)
                for command in commands.values():
                    self.assertNotIn(command.id, command_ids)
                    command_ids.add(command.id)

    def test_product_command_catalog_is_intentionally_retired(self):
        product_command_files = sorted(config_root().rglob("command_*.yaml"))

        self.assertEqual(product_command_files, [])

    def test_product_runtime_change_commands_are_not_read_classified(self):
        for config_file in sorted(config_root().rglob("command_*.yaml")):
            commands = PortCommandRepositoryYaml(config_file.name).get_all_commands()
            for command in commands.values():
                with self.subTest(command_id=command.id):
                    if "runtime_change" in command.effects:
                        self.assertNotEqual("safe_read", command.safety_class.value)

    def test_product_credential_output_commands_declare_redacted_policy(self):
        credential_output_commands = []

        for config_file in sorted(config_root().rglob("command_*.yaml")):
            commands = PortCommandRepositoryYaml(config_file.name).get_all_commands()
            for command in commands.values():
                if command.produces_sensitive_output:
                    credential_output_commands.append(command.id)
                    with self.subTest(command_id=command.id):
                        self.assertEqual("credential_mutation", command.safety_class.value)
                        self.assertIsNotNone(command.evidence_policy)
                        self.assertTrue(command.evidence_policy.redact_output)
                        self.assertFalse(command.evidence_policy.store_raw_output)

        self.assertEqual(credential_output_commands, [])


def _repository_for(yaml_content: str) -> PortCommandRepositoryYaml:
    return PortCommandRepositoryYaml(
        "synthetic.yaml",
        file_manager=cast(FileManager, _FakeFileManager(yaml_content)),
    )


def _catalog_yaml(commands: str) -> str:
    return f"commands:\n{commands}"


def _command_yaml(
    *,
    command_id: str,
    index: int = 1,
    command: str = "docker ps",
    safety_class: str = "safe_read",
    effects: tuple[str, ...] = ("read",),
    verify_type: str = "none",
) -> str:
    effect_lines = "\n".join(f"      - {effect}" for effect in effects)
    return f"""
  - id: {command_id}
    index: {index}
    description: Test command
    intent: test_command
    execution_mode: shell
    safety_class: {safety_class}
    scope: host
    allowed_workflows:
      - platform:init
    parameters: []
    effects:
{effect_lines}
    verify:
      type: {verify_type}
      description: Read-only command.
    command: "{command}"
    runner: "async"
    command_type: "hostos"
    vm_type:
      - "none"
"""


class _FakeFileManager:
    def __init__(self, content: str):
        self.content = content

    def load(self, path: Path) -> Any:
        return self.content


class TestCommandParsingBoundary(unittest.TestCase):
    def test_supported_numeric_string_indexes_remain_accepted(self):
        for index in ("1", " 1 ", "+1", "1.0"):
            with self.subTest(index=index):
                text = _catalog_yaml(_command_yaml(command_id="read.001")).replace("index: 1", f"index: '{index}'")
                self.assertEqual(_repository_for(text).get_all_commands()[1].index, 1)

    def test_valid_synthetic_catalog_keeps_typed_command_output(self):
        commands = _repository_for(_catalog_yaml(_command_yaml(command_id="read.001"))).get_all_commands()
        self.assertEqual(commands[1].id, "read.001")
        self.assertEqual(commands[1].command, "docker ps")

    def test_invalid_yaml_and_shapes_have_safe_neutral_diagnostics(self):
        import traceback
        for text in (
            "commands: [boundary-marker-secret",
            "commands: []\ncommands: [boundary-marker-secret]",
            "commands: &loop [*loop]",
            "commands: []\n1: boundary-marker-secret\nother: x",
            _catalog_yaml(_command_yaml(command_id="valid.001").replace("index: 1", "index: true")),
            _catalog_yaml(_command_yaml(command_id="valid.001").replace("index: 1", "index: 1.0")),
            _catalog_yaml(_command_yaml(command_id="valid.001").replace("index: 1", "index: 'boundary-marker-secret'")),
            _catalog_yaml(_command_yaml(command_id="valid.001").replace("intent: test_command", "intent: [boundary-marker-secret]")),
            _catalog_yaml(_command_yaml(command_id="valid.001")) + "    evidence_policy: {redact_output: 'false'}\n",
        ):
            with self.subTest(text=text):
                try:
                    _repository_for(text).get_all_commands()
                except CommandCatalogValidationError as error:
                    self.assertNotIn("boundary-marker-secret", str(error))
                    self.assertNotIn("boundary-marker-secret", "".join(traceback.format_exception(error)))
                else:
                    self.fail("Malformed command configuration accepted")


if __name__ == "__main__":
    unittest.main()
