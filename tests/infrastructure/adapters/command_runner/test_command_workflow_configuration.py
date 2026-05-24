import unittest

from tiny_swarm_world.application.ports.commands.parameter_type import ParameterType
from tiny_swarm_world.infrastructure.adapters.command_runner.command_workflow import CommandWorkflow
from tiny_swarm_world.infrastructure.adapters.file_management.file_manager import FileManager
from tiny_swarm_world.infrastructure.adapters.file_management.path_strategies.path_factory import PathFactory
from tiny_swarm_world.infrastructure.dependency_injection.infra_core_di_container import infra_core_container
from tiny_swarm_world.infrastructure.project_paths import config_root
from tiny_swarm_world.domain.command.command_entity import (
    CommandCatalogValidationError,
    CommandSafetyClass,
    CommandVerifySpec,
    CommandWorkflowId,
)
from tiny_swarm_world.application.ports.commands.executable_command import (
    ExecutableCommandEntity,
)
from tiny_swarm_world.domain.inventory import VerificationStatus


EXPECTED_COMMAND_COUNTS = {
    "command_multipass_docker_install_yaml.yaml": 30,
    "command_multipass_docker_prepare_repository_yaml.yaml": 6,
    "command_multipass_docker_swarm_join_worker.yaml": 2,
    "command_multipass_docker_swarm_manager_init.yaml": 1,
    "command_multipass_docker_swarm_manager_ip.yaml": 1,
    "command_multipass_docker_swarm_manager_join_token.yaml": 1,
    "command_multipass_docker_swarm_verify_yaml.yaml": 3,
    "command_multipass_docker_verify_yaml.yaml": 3,
    "command_multipass_clean_repository_yaml.yaml": 3,
    "command_multipass_instance_status_yaml.yaml": 3,
    "command_multipass_init_repository_yaml.yaml": 4,
    "command_multipass_prepare_repository_yaml.yaml": 12,
    "command_multipass_restart_repository_yaml.yaml": 1,
    "command_netplant_ip_yaml.yaml": 2,
    "command_netplant_setup_yaml.yaml": 7,
    "command_vm_bridge_list.yaml": 1,
    "command_vm_docker_bridge_list.yaml": 1,
    "command_vm_gateway_yaml.yaml": 1,
    "command_vm_ip_list.yaml": 3,
}

WORKFLOW_BY_COMMAND_FILE = {
    "command_multipass_clean_repository_yaml.yaml": CommandWorkflowId.PLATFORM_RESET.value,
    "command_multipass_init_repository_yaml.yaml": CommandWorkflowId.PLATFORM_INIT.value,
    "command_multipass_prepare_repository_yaml.yaml": CommandWorkflowId.PLATFORM_INIT.value,
    "command_multipass_restart_repository_yaml.yaml": CommandWorkflowId.PLATFORM_INIT.value,
    "command_multipass_docker_install_yaml.yaml": CommandWorkflowId.PLATFORM_INIT.value,
    "command_multipass_docker_prepare_repository_yaml.yaml": CommandWorkflowId.PLATFORM_INIT.value,
    "command_multipass_docker_swarm_join_worker.yaml": CommandWorkflowId.PLATFORM_INIT.value,
    "command_multipass_docker_swarm_manager_init.yaml": CommandWorkflowId.PLATFORM_INIT.value,
    "command_multipass_docker_swarm_manager_ip.yaml": CommandWorkflowId.PLATFORM_INIT.value,
    "command_multipass_docker_swarm_manager_join_token.yaml": CommandWorkflowId.PLATFORM_INIT.value,
    "command_multipass_docker_swarm_verify_yaml.yaml": CommandWorkflowId.PLATFORM_INIT.value,
    "command_multipass_docker_verify_yaml.yaml": CommandWorkflowId.PLATFORM_INIT.value,
    "command_netplant_ip_yaml.yaml": CommandWorkflowId.PLATFORM_INIT.value,
    "command_netplant_setup_yaml.yaml": CommandWorkflowId.PLATFORM_INIT.value,
    "command_multipass_instance_status_yaml.yaml": CommandWorkflowId.PLATFORM_INIT.value,
    "command_vm_bridge_list.yaml": CommandWorkflowId.PLATFORM_RECONCILE.value,
    "command_vm_docker_bridge_list.yaml": CommandWorkflowId.PLATFORM_RECONCILE.value,
    "command_vm_gateway_yaml.yaml": CommandWorkflowId.PLATFORM_RECONCILE.value,
    "command_vm_ip_list.yaml": CommandWorkflowId.PLATFORM_RECONCILE.value,
}


class TestCommandWorkflowConfiguration(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        infra_core_container.register(PathFactory)
        infra_core_container.register(FileManager)

    def test_all_command_yaml_files_build_command_lists(self):
        workflow = CommandWorkflow()
        config_files = sorted(config_root().rglob("command_*.yaml"))

        self.assertEqual(sorted(EXPECTED_COMMAND_COUNTS), sorted(path.name for path in config_files))

        for config_file in config_files:
            with self.subTest(config_file=config_file.name):
                command_list = workflow.build_command_list(
                    config_file.name,
                    _smoke_parameters(),
                    workflow_id=WORKFLOW_BY_COMMAND_FILE[config_file.name],
                )
                command_count = sum(len(commands) for commands in command_list.values())

                self.assertEqual(EXPECTED_COMMAND_COUNTS[config_file.name], command_count)
                self.assertGreaterEqual(len(command_list), 1)

    def test_netplan_transfer_command_uses_infra_config_path(self):
        workflow = CommandWorkflow()
        command_list = workflow.build_command_list(
            "command_netplant_setup_yaml.yaml",
            _smoke_parameters(),
            workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
        )

        transfer_command = command_list["swarm-manager"][3].command

        self.assertEqual(
            "multipass transfer infra/config/cloud-init-manager.yaml swarm-manager:/tmp/netplan.yaml",
            transfer_command,
        )

    def test_package_install_commands_are_bounded_and_noninteractive(self):
        workflow = CommandWorkflow()
        netplan_commands = workflow.build_command_list(
            "command_netplant_setup_yaml.yaml",
            _smoke_parameters(),
            workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
        )
        docker_commands = workflow.build_command_list(
            "command_multipass_docker_install_yaml.yaml",
            _smoke_parameters(),
            workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
        )

        install_socat = netplan_commands["hostos"][1].command
        self.assertIn("command -v socat", install_socat)
        self.assertIn("timeout 300", install_socat)
        self.assertIn("sudo -n env DEBIAN_FRONTEND=noninteractive apt-get", install_socat)

        for index in (1, 2, 7, 8):
            docker_command = docker_commands["swarm-manager"][index].command
            self.assertIn("DEBIAN_FRONTEND=noninteractive", docker_command)
            self.assertIn("timeout 300", docker_command)

    def test_built_commands_preserve_verification_metadata(self):
        workflow = CommandWorkflow()
        command_list = workflow.build_command_list(
            "command_multipass_init_repository_yaml.yaml",
            _smoke_parameters(),
            workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
        )

        launch_command = command_list["swarm-manager"][1]

        self.assertEqual("multipass_init_repository.001", launch_command.command_id)
        self.assertTrue(launch_command.mutating)
        self.assertIsNotNone(launch_command.verify)
        self.assertEqual("command", launch_command.verify.type.value)
        self.assertEqual("probe:platform:vm-created", launch_command.verify.command)
        self.assertIn("multipass launch 24.04", launch_command.command)

    def test_built_sensitive_output_commands_preserve_evidence_policy(self):
        workflow = CommandWorkflow()
        command_list = workflow.build_command_list(
            "command_multipass_docker_swarm_manager_join_token.yaml",
            _smoke_parameters(),
            workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
        )

        join_token_command = command_list["swarm-manager"][1]

        self.assertEqual(
            "multipass_docker_swarm_manager_join_token.001",
            join_token_command.command_id,
        )
        self.assertTrue(join_token_command.mutating)
        self.assertEqual("credential_mutation", join_token_command.safety_class.value)
        self.assertIsNotNone(join_token_command.evidence_policy)
        self.assertTrue(join_token_command.evidence_policy.redact_output)
        self.assertFalse(join_token_command.evidence_policy.store_raw_output)

    def test_destructive_cleanup_commands_are_not_allowed_for_init(self):
        workflow = CommandWorkflow()

        with self.assertRaises(CommandCatalogValidationError):
            workflow.build_command_list(
                "command_multipass_clean_repository_yaml.yaml",
                _smoke_parameters(),
                workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
            )

    def test_manual_mutating_catalog_blocks_pre_apply_verification(self):
        workflow = CommandWorkflow()

        result = workflow.verify_config_contract(
            "command_multipass_clean_repository_yaml.yaml",
            _smoke_parameters(),
            workflow_id=CommandWorkflowId.PLATFORM_RESET.value,
            target_id="platform:reset:multipass-clean",
        )

        self.assertEqual(VerificationStatus.BLOCKED, result.status)
        self.assertEqual("command_backed_verification_missing", result.evidence["reason"])
        self.assertEqual("2", result.evidence["manual_verify_count"])

    def test_read_only_catalog_verifies_without_running_commands(self):
        workflow = CommandWorkflow()

        result = workflow.verify_config_contract(
            "command_vm_gateway_yaml.yaml",
            _smoke_parameters(),
            workflow_id=CommandWorkflowId.PLATFORM_RECONCILE.value,
            target_id="platform:reconcile:vm-ip-list",
        )

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual("0", result.evidence["mutating_count"])

    def test_command_backed_mutating_catalog_verifies_contract(self):
        workflow = _StaticCommandWorkflow(
            {
                "local": {
                    1: ExecutableCommandEntity(
                        index=1,
                        command_id="probe.ready",
                        safety_class=CommandSafetyClass.SAFE_MUTATION,
                        verify=CommandVerifySpec(
                            type="command",
                            description="safe probe",
                            command="probe:platform:vm-created",
                        ),
                    )
                }
            }
        )

        result = workflow.verify_config_contract(
            "synthetic.yaml",
            workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
            target_id="platform:init:synthetic",
        )

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual("1", result.evidence["command_backed_verify_count"])

    def test_unknown_command_backed_probe_blocks_contract(self):
        workflow = _StaticCommandWorkflow(
            {
                "local": {
                    1: ExecutableCommandEntity(
                        index=1,
                        command_id="probe.unknown",
                        safety_class=CommandSafetyClass.SAFE_MUTATION,
                        verify=CommandVerifySpec(
                            type="command",
                            description="unknown probe",
                            command="probe:unknown",
                        ),
                    )
                }
            }
        )

        result = workflow.verify_config_contract(
            "synthetic.yaml",
            workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
            target_id="platform:init:synthetic",
        )

        self.assertEqual(VerificationStatus.BLOCKED, result.status)
        self.assertEqual("verification_probe_not_registered", result.evidence["reason"])
        self.assertEqual("1", result.evidence["unknown_probe_count"])

    def test_invalid_catalog_blocks_pre_apply_verification(self):
        workflow = _StaticCommandWorkflow(error=CommandCatalogValidationError("invalid"))

        result = workflow.verify_config_contract(
            "synthetic.yaml",
            workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
            target_id="platform:init:synthetic",
        )

        self.assertEqual(VerificationStatus.BLOCKED, result.status)
        self.assertEqual("catalog_validation_failed", result.evidence["reason"])


def _smoke_parameters() -> dict[ParameterType, str]:
    return {
        ParameterType.SWARM_MANAGER_IP: "10.0.0.1",
        ParameterType.SWARM_MANAGER_PORT: "2377",
        ParameterType.SWARM_TOKEN: "dummy-token",
        ParameterType.DOCKER_BRIDGE: "bridge",
    }


class _StaticCommandWorkflow(CommandWorkflow):
    def __init__(
        self,
        command_list: dict[str, dict[int, ExecutableCommandEntity]] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.command_list = command_list or {}
        self.error = error

    def build_command_list(
        self,
        config_file: str,
        parameter: dict[ParameterType, str] | None = None,
        *,
        workflow_id: str,
    ) -> dict[str, dict[int, ExecutableCommandEntity]]:
        if self.error is not None:
            raise self.error
        return self.command_list
