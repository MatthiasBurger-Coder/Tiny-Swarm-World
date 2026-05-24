import logging

from tiny_swarm_world.application.ports.commands.port_command_workflow import PortCommandWorkflow
from tiny_swarm_world.application.ports.repositories.port_vm_repository import PortVmRepository
from tiny_swarm_world.application.ports.repositories.port_yaml_repository import PortYamlRepository
from tiny_swarm_world.domain.command.command_entity import CommandWorkflowId
from tiny_swarm_world.domain.multipass.vm_type import VmType
from tiny_swarm_world.domain.network.ip_extractor.ip_extractor_builder import IpExtractorBuilder
from tiny_swarm_world.domain.network.ip_extractor.strategies.ip_extstractor_types import IpExtractorTypes
from tiny_swarm_world.domain.network.network import Network


class NetworkPrepareNetplan:
    verification_target_id = "platform:init:network-prepare-netplan"
    operator_block_reason = "post-apply verification is not implemented"

    def __init__(
        self,
        command_workflow: PortCommandWorkflow,
        vm_repository: PortVmRepository,
        netplan_repository: PortYamlRepository,
        ip_extractor_builder: IpExtractorBuilder | None = None,
    ):
        self.command_workflow = command_workflow
        self.vm_repository = vm_repository
        self.netplan_repository = netplan_repository
        self.ip_extractor_builder = ip_extractor_builder or IpExtractorBuilder()
        self.logger = logging.getLogger(self.__class__.__name__)

    async def run(self):
        self.logger.info("Setup cloud-init-manager.yaml")

        result = await self.command_workflow.run_async(
            "command_netplant_ip_yaml.yaml",
            workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
        )
        self.logger.info("network IP discovery completed")

        # getting the necessary IPs
        gateway_ip = self.ip_extractor_builder.build(result=result, ip_extractor_types=IpExtractorTypes.GATEWAY)
        self.logger.info("gateway address extracted")
        ip = self.ip_extractor_builder.build(result=result, ip_extractor_types=IpExtractorTypes.SWAM_MANAGER)
        self.logger.info("swarm manager address extracted")

        vm_instance_names = self.vm_repository.find_vm_instances_by_type(VmType.MANAGER)
        network_data = Network(vm_instance=vm_instance_names[0], ip_address=ip, gateway=gateway_ip)
        self.logger.info("creating network data")

        data = self.netplan_repository
        data.create(network_data)
        self.logger.info("saving network data")
        data.save()

    def verify_pre_apply(self):
        from tiny_swarm_world.application.services.platform.command_verification import (
            verify_command_configs,
        )

        return verify_command_configs(
            self.command_workflow,
            target_id=self.verification_target_id,
            workflow_id=CommandWorkflowId.PLATFORM_INIT.value,
            config_files=("command_netplant_ip_yaml.yaml",),
        )
