import unittest
from dataclasses import dataclass
from typing import Any

from tiny_swarm_world.application.ports.commands.executable_command import (
    ExecutableCommandEntity,
)
from tiny_swarm_world.application.ports.commands.parameter_type import ParameterType
from tiny_swarm_world.application.ports.commands.port_command_workflow import PortCommandWorkflow
from tiny_swarm_world.application.ports.repositories.port_vm_repository import PortVmRepository
from tiny_swarm_world.application.ports.repositories.port_yaml_repository import PortYamlRepository
from tiny_swarm_world.application.services.multipass.multipass_docker_install import (
    MultipassDockerInstall,
)
from tiny_swarm_world.application.services.multipass.multipass_docker_swarm_init import (
    MultipassDockerSwarmInit,
)
from tiny_swarm_world.application.services.multipass.multipass_init_vms import (
    MultipassInitVms,
)
from tiny_swarm_world.application.services.multipass.multipass_restart_vms import (
    MultipassRestartVMs,
)
from tiny_swarm_world.application.services.network.netplant.network_prepare_netplan import (
    NetworkPrepareNetplan,
)
from tiny_swarm_world.application.services.network.netplant.network_setup_netplan import (
    NetworkSetupNetplan,
)
from tiny_swarm_world.application.services.vm.vm_ip_list import VmIpList
from tiny_swarm_world.domain.command.command_entity import CommandWorkflowId
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus
from tiny_swarm_world.domain.multipass.vm_entity import VmEntity
from tiny_swarm_world.domain.multipass.vm_type import VmType


class TestCommandVerificationContracts(unittest.TestCase):
    def test_platform_services_check_declared_pre_apply_catalogs(self):
        cases = (
            (
                lambda workflow: MultipassInitVms(workflow),
                "platform:init:multipass-vms",
                CommandWorkflowId.PLATFORM_INIT.value,
                ("command_multipass_init_repository_yaml.yaml",),
            ),
            (
                lambda workflow: MultipassDockerInstall(workflow),
                "platform:init:multipass-docker-install",
                CommandWorkflowId.PLATFORM_INIT.value,
                (
                    "command_multipass_docker_install_yaml.yaml",
                    "command_multipass_docker_prepare_repository_yaml.yaml",
                ),
            ),
            (
                lambda workflow: MultipassRestartVMs(workflow),
                "platform:init:multipass-restart-vms",
                CommandWorkflowId.PLATFORM_INIT.value,
                ("command_multipass_restart_repository_yaml.yaml",),
            ),
            (
                lambda workflow: NetworkSetupNetplan(workflow),
                "platform:init:network-setup-netplan",
                CommandWorkflowId.PLATFORM_INIT.value,
                ("command_netplant_setup_yaml.yaml",),
            ),
            (
                lambda workflow: _network_prepare_netplan(workflow),
                "platform:init:network-prepare-netplan",
                CommandWorkflowId.PLATFORM_INIT.value,
                ("command_netplant_ip_yaml.yaml",),
            ),
            (
                lambda workflow: _vm_ip_list(workflow),
                "platform:reconcile:vm-ip-list",
                CommandWorkflowId.PLATFORM_RECONCILE.value,
                (
                    "command_vm_bridge_list.yaml",
                    "command_vm_docker_bridge_list.yaml",
                    "command_multipass_docker_swarm_manager_ip.yaml",
                    "command_vm_ip_list.yaml",
                    "command_vm_gateway_yaml.yaml",
                ),
            ),
        )

        for factory, target_id, workflow_id, expected_configs in cases:
            with self.subTest(target_id=target_id):
                command_workflow = _RecordingCommandWorkflow()
                result = factory(command_workflow).verify_pre_apply()

                self.assertEqual(VerificationStatus.VERIFIED, result.status)
                self.assertEqual(target_id, result.target_id)
                self.assertEqual(
                    list(expected_configs),
                    [call.config_file for call in command_workflow.verify_calls],
                )
                self.assertEqual(
                    [workflow_id] * len(expected_configs),
                    [call.workflow_id for call in command_workflow.verify_calls],
                )
                self.assertEqual(
                    [None] * len(expected_configs),
                    [call.parameter for call in command_workflow.verify_calls],
                )

    def test_platform_services_return_first_blocked_pre_apply_result(self):
        command_workflow = _RecordingCommandWorkflow(blocked_at="command_netplant_setup_yaml.yaml")

        result = NetworkSetupNetplan(command_workflow).verify_pre_apply()

        self.assertEqual(VerificationStatus.BLOCKED, result.status)
        self.assertEqual("command_backed_verification_missing", result.evidence["reason"])
        self.assertEqual(
            ["command_netplant_setup_yaml.yaml"],
            [call.config_file for call in command_workflow.verify_calls],
        )

    def test_swarm_pre_apply_contract_does_not_substitute_join_token(self):
        command_workflow = _RecordingCommandWorkflow()
        service = MultipassDockerSwarmInit(command_workflow)
        service.parameter[ParameterType.SWARM_TOKEN] = "raw-token"
        service.parameter[ParameterType.SWARM_MANAGER_IP] = "10.0.0.1"

        service.verify_pre_apply()

        self.assertEqual(
            [None, None, None, None],
            [call.parameter for call in command_workflow.verify_calls],
        )

    def test_swarm_run_clears_join_token_after_worker_join(self):
        command_workflow = _RecordingCommandWorkflow(
            sync_results={
                "command_multipass_docker_swarm_manager_ip.yaml": [{"swarm-manager": "10.0.0.1"}],
                "command_multipass_docker_swarm_manager_join_token.yaml": [(1, "raw-token")],
            }
        )
        service = MultipassDockerSwarmInit(command_workflow)

        self.loop_run(service.run())

        self.assertNotIn(ParameterType.SWARM_TOKEN, service.parameter)
        join_call = command_workflow.sync_calls[-1]
        self.assertEqual("command_multipass_docker_swarm_join_worker.yaml", join_call.config_file)
        self.assertEqual("raw-token", join_call.parameter[ParameterType.SWARM_TOKEN])

    def test_swarm_run_clears_join_token_when_worker_join_fails(self):
        command_workflow = _RecordingCommandWorkflow(
            sync_results={
                "command_multipass_docker_swarm_manager_ip.yaml": [{"swarm-manager": "10.0.0.1"}],
                "command_multipass_docker_swarm_manager_join_token.yaml": [(1, "raw-token")],
            },
            raise_at="command_multipass_docker_swarm_join_worker.yaml",
        )
        service = MultipassDockerSwarmInit(command_workflow)

        with self.assertRaises(RuntimeError):
            self.loop_run(service.run())

        self.assertNotIn(ParameterType.SWARM_TOKEN, service.parameter)

    def test_platform_steps_do_not_claim_post_apply_verification_from_metadata(self):
        cases = (
            MultipassInitVms,
            MultipassDockerInstall,
            MultipassDockerSwarmInit,
            MultipassRestartVMs,
            NetworkSetupNetplan,
        )

        for service_type in cases:
            with self.subTest(service_type=service_type.__name__):
                service = service_type(_RecordingCommandWorkflow())
                self.assertFalse(callable(getattr(service, "verify", None)))

        self.assertFalse(callable(getattr(_network_prepare_netplan(_RecordingCommandWorkflow()), "verify", None)))
        self.assertFalse(callable(getattr(_vm_ip_list(_RecordingCommandWorkflow()), "verify", None)))

    @staticmethod
    def loop_run(coro: Any) -> Any:
        import asyncio

        return asyncio.run(coro)


def _network_prepare_netplan(command_workflow: PortCommandWorkflow) -> NetworkPrepareNetplan:
    return NetworkPrepareNetplan(
        command_workflow=command_workflow,
        vm_repository=_VmRepository(),
        netplan_repository=_NetplanRepository(),
    )


def _vm_ip_list(command_workflow: PortCommandWorkflow) -> VmIpList:
    return VmIpList(command_workflow=command_workflow, vm_repository=_VmRepository())


class _RecordingCommandWorkflow(PortCommandWorkflow):
    def __init__(
        self,
        blocked_at: str | None = None,
        sync_results: dict[str, object] | None = None,
        raise_at: str | None = None,
    ) -> None:
        self.blocked_at = blocked_at
        self.sync_results = sync_results or {}
        self.raise_at = raise_at
        self.async_calls: list[_WorkflowCall] = []
        self.sync_calls: list[_WorkflowCall] = []
        self.build_calls: list[_WorkflowCall] = []
        self.verify_calls: list[_WorkflowCall] = []

    def build_command_list(
        self,
        config_file: str,
        parameter: dict[ParameterType, str] | None = None,
        *,
        workflow_id: str,
    ) -> dict[str, dict[int, ExecutableCommandEntity]]:
        self.build_calls.append(_WorkflowCall.from_values(config_file, parameter, workflow_id))
        return {}

    async def run_async(
        self,
        config_file: str,
        parameter: dict[ParameterType, str] | None = None,
        *,
        workflow_id: str,
    ) -> Any:
        self.async_calls.append(_WorkflowCall.from_values(config_file, parameter, workflow_id))
        return self.sync_results.get(config_file, [])

    async def run_sync(
        self,
        config_file: str,
        parameter: dict[ParameterType, str] | None = None,
        *,
        workflow_id: str,
    ) -> Any:
        self.sync_calls.append(_WorkflowCall.from_values(config_file, parameter, workflow_id))
        if config_file == self.raise_at:
            raise RuntimeError("join failed")
        return self.sync_results.get(config_file, [])

    def verify_config_contract(
        self,
        config_file: str,
        parameter: dict[ParameterType, str] | None = None,
        *,
        workflow_id: str,
        target_id: str,
    ) -> VerificationResult:
        self.verify_calls.append(_WorkflowCall.from_values(config_file, parameter, workflow_id))
        if config_file == self.blocked_at:
            return VerificationResult(
                target_id=target_id,
                status=VerificationStatus.BLOCKED,
                message="Command-backed verification is not configured.",
                evidence={
                    "phase": "pre_apply",
                    "reason": "command_backed_verification_missing",
                },
            )
        return VerificationResult(
            target_id=target_id,
            status=VerificationStatus.VERIFIED,
            message="Command-backed verification contract is configured.",
            evidence={"phase": "pre_apply"},
        )


class _VmRepository(PortVmRepository):
    def get_all_vms(self) -> list[VmEntity]:
        return []

    def get_vm_by_name(self, name: str) -> VmEntity | None:
        return None

    def add_vm(self, vm: VmEntity) -> None:
        return None

    def remove_vm(self, name: str) -> None:
        return None

    def update_vm(self, vm: VmEntity) -> None:
        return None

    def find_all_vms(self) -> list[VmEntity]:
        return []

    def find_vm_instances_by_type(self, vm_type: VmType) -> list[str]:
        return ["swarm-manager"]


class _NetplanRepository(PortYamlRepository):
    def create(self, data: object) -> object:
        return data

    def load(self) -> object:
        return None

    def save(self) -> None:
        return None


@dataclass(frozen=True)
class _WorkflowCall:
    config_file: str
    parameter: dict[ParameterType, str] | None
    workflow_id: str

    @classmethod
    def from_values(
        cls,
        config_file: str,
        parameter: dict[ParameterType, str] | None,
        workflow_id: str,
    ) -> "_WorkflowCall":
        return cls(config_file, dict(parameter) if parameter is not None else None, workflow_id)


if __name__ == "__main__":
    unittest.main()
