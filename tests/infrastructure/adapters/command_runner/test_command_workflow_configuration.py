import unittest

from tiny_swarm_world.application.ports.commands.parameter_type import ParameterType
from tiny_swarm_world.infrastructure.adapters.command_runner.command_workflow import CommandWorkflow
from tiny_swarm_world.infrastructure.adapters.file_management.file_manager import FileManager
from tiny_swarm_world.infrastructure.adapters.file_management.path_strategies.path_factory import PathFactory
from tiny_swarm_world.infrastructure.dependency_injection.infra_core_di_container import infra_core_container
from tiny_swarm_world.infrastructure.project_paths import config_root
from tiny_swarm_world.domain.command.command_entity import (
    CommandCatalogValidationError,
    CommandWorkflowId,
)


EXPECTED_COMMAND_COUNTS = {
    "command_multipass_docker_install_yaml.yaml": 30,
    "command_multipass_docker_prepare_repository_yaml.yaml": 6,
    "command_multipass_docker_swarm_join_worker.yaml": 2,
    "command_multipass_docker_swarm_manager_init.yaml": 1,
    "command_multipass_docker_swarm_manager_ip.yaml": 1,
    "command_multipass_docker_swarm_manager_join_token.yaml": 1,
    "command_multipass_clean_repository_yaml.yaml": 3,
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
    "command_netplant_ip_yaml.yaml": CommandWorkflowId.PLATFORM_INIT.value,
    "command_netplant_setup_yaml.yaml": CommandWorkflowId.PLATFORM_INIT.value,
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

    def test_destructive_cleanup_commands_are_not_allowed_for_init(self):
        workflow = CommandWorkflow()

        with self.assertRaises(CommandCatalogValidationError):
            workflow.build_command_list(
                "command_multipass_clean_repository_yaml.yaml",
                _smoke_parameters(),
                workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
            )


def _smoke_parameters() -> dict[ParameterType, str]:
    return {
        ParameterType.SWARM_MANAGER_IP: "10.0.0.1",
        ParameterType.SWARM_MANAGER_PORT: "2377",
        ParameterType.SWARM_TOKEN: "dummy-token",
        ParameterType.DOCKER_BRIDGE: "bridge",
    }
