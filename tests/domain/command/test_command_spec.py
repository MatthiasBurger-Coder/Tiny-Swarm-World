import unittest

from pydantic import ValidationError

from tiny_swarm_world.domain.command.command_entity import (
    CommandCatalogValidationError,
    CommandEntity,
    CommandWorkflowId,
)


class TestCommandSpec(unittest.TestCase):
    def test_valid_typed_command_spec_parses(self):
        command = CommandEntity(**_command_spec())

        self.assertEqual("test.command.001", command.id)
        self.assertEqual(["platform:init"], command.allowed_workflows)

    def test_command_spec_rejects_missing_id(self):
        spec = _command_spec()
        del spec["id"]

        with self.assertRaises(ValidationError):
            CommandEntity(**spec)

    def test_command_spec_rejects_missing_safety_class(self):
        spec = _command_spec()
        del spec["safety_class"]

        with self.assertRaises(ValidationError):
            CommandEntity(**spec)

    def test_command_spec_rejects_unknown_safety_class(self):
        spec = _command_spec()
        spec["safety_class"] = "unknown"

        with self.assertRaises(ValidationError):
            CommandEntity(**spec)

    def test_mutating_command_requires_verify_spec(self):
        spec = _command_spec(safety_class="safe_mutation")
        spec["verify"] = {"type": "none", "description": "not verified"}

        with self.assertRaises(ValidationError):
            CommandEntity(**spec)

    def test_destructive_shell_pattern_requires_destructive_safety_class(self):
        spec = _command_spec(
            command="multipass delete --all",
            safety_class="safe_mutation",
            verify={"type": "manual", "description": "verify deletion"},
        )

        with self.assertRaises(ValidationError):
            CommandEntity(**spec)

    def test_destructive_commands_are_limited_to_reset_or_destroy(self):
        spec = _command_spec(
            command="multipass purge",
            safety_class="destructive",
            allowed_workflows=[CommandWorkflowId.PLATFORM_INIT.value],
            verify={"type": "manual", "description": "verify purge"},
        )

        with self.assertRaises(ValidationError):
            CommandEntity(**spec)

    def test_command_usage_requires_allowed_workflow(self):
        command = CommandEntity(**_command_spec())

        with self.assertRaises(CommandCatalogValidationError):
            command.ensure_allowed_for_workflow(CommandWorkflowId.PLATFORM_RECONCILE.value)


def _command_spec(**overrides: object) -> dict[str, object]:
    spec: dict[str, object] = {
        "id": "test.command.001",
        "index": 1,
        "description": "Test command",
        "intent": "test_command",
        "execution_mode": "shell",
        "safety_class": "safe_read",
        "scope": "host",
        "allowed_workflows": [CommandWorkflowId.PLATFORM_INIT.value],
        "parameters": [],
        "effects": ["read"],
        "verify": {"type": "none", "description": "Read-only command."},
        "command": "multipass list",
        "runner": "async",
        "command_type": "hostos",
        "vm_type": ["none"],
    }
    spec.update(overrides)
    return spec


if __name__ == "__main__":
    unittest.main()
