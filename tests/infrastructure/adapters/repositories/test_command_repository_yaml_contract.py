import unittest
from pathlib import Path
from typing import Any, cast

from tiny_swarm_world.domain.command.command_entity import CommandCatalogValidationError
from tiny_swarm_world.infrastructure.adapters.file_management.file_manager import FileManager
from tiny_swarm_world.infrastructure.adapters.file_management.path_strategies.path_factory import PathFactory
from tiny_swarm_world.infrastructure.adapters.repositories.command_repository_yaml import (
    PortCommandRepositoryYaml,
)
from tiny_swarm_world.infrastructure.dependency_injection.infra_core_di_container import (
    infra_core_container,
)
from tiny_swarm_world.infrastructure.project_paths import config_root


class TestCommandRepositoryYamlContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        infra_core_container.register(PathFactory)
        infra_core_container.register(FileManager)

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

        self.assertEqual([], credential_output_commands)


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


if __name__ == "__main__":
    unittest.main()
