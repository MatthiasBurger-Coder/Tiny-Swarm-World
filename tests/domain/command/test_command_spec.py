import unittest

from pydantic import ValidationError

from tiny_swarm_world.domain.command.command_entity import (
    CommandCatalogValidationError,
    CommandEntity,
    CommandSafetyClass,
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

    def test_command_backed_verify_requires_command(self):
        spec = _command_spec(
            safety_class="safe_mutation",
            verify={"type": "command", "description": "verify with command"},
        )

        with self.assertRaises(ValidationError):
            CommandEntity(**spec)

    def test_manual_verify_is_metadata_only(self):
        command = CommandEntity(
            **_command_spec(
                safety_class="safe_mutation",
                verify={"type": "manual", "description": "operator check required"},
            )
        )

        self.assertTrue(command.is_manual_only_verification)
        self.assertFalse(command.is_command_backed_verification)

    def test_all_mutating_safety_classes_require_verify_spec(self):
        mutating_classes = (
            CommandSafetyClass.SAFE_MUTATION.value,
            CommandSafetyClass.CREDENTIAL_MUTATION.value,
            CommandSafetyClass.NETWORK_MUTATION.value,
            CommandSafetyClass.DESTRUCTIVE.value,
        )

        for safety_class in mutating_classes:
            with self.subTest(safety_class=safety_class):
                spec = _command_spec(
                    safety_class=safety_class,
                    allowed_workflows=[CommandWorkflowId.PLATFORM_RESET.value]
                    if safety_class == CommandSafetyClass.DESTRUCTIVE.value
                    else [CommandWorkflowId.PLATFORM_INIT.value],
                    command="multipass delete --all"
                    if safety_class == CommandSafetyClass.DESTRUCTIVE.value
                    else "echo ok",
                )
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

    def test_runtime_change_command_cannot_be_safe_read(self):
        spec = _command_spec(effects=["read", "runtime_change"])

        with self.assertRaises(ValidationError):
            CommandEntity(**spec)

    def test_credential_output_requires_credential_safety_and_redacted_policy(self):
        missing_policy = _command_spec(
            safety_class="credential_mutation",
            effects=["read", "credential_output"],
            verify={"type": "manual", "description": "operator check required"},
        )

        with self.assertRaises(ValidationError):
            CommandEntity(**missing_policy)

        read_classified = _command_spec(
            safety_class="safe_read",
            effects=["read", "credential_output"],
            verify={"type": "none", "description": "read only"},
            evidence_policy={"redact_output": True, "store_raw_output": False},
        )

        with self.assertRaises(ValidationError):
            CommandEntity(**read_classified)

        command = CommandEntity(
            **_command_spec(
                safety_class="credential_mutation",
                effects=["read", "credential_output"],
                verify={"type": "manual", "description": "operator check required"},
                evidence_policy={"redact_output": True, "store_raw_output": False},
            )
        )

        self.assertTrue(command.produces_sensitive_output)

    def test_command_evidence_policy_rejects_raw_output_storage(self):
        spec = _command_spec(evidence_policy={"redact_output": False, "store_raw_output": True})

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
