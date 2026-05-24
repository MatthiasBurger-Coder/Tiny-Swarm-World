import unittest

from tiny_swarm_world.application.ports.clients.port_swarm_stack_runtime import (
    SwarmServiceStatus,
)
from tiny_swarm_world.application.services.deployment.ensure_swarm_stack import (
    EnsureSwarmStack,
)
from tiny_swarm_world.domain.deployment import ServiceStackContract
from tiny_swarm_world.domain.deployment.stack_definition import StackDefinition
from tiny_swarm_world.domain.inventory import VerificationStatus


class TestEnsureSwarmStack(unittest.IsolatedAsyncioTestCase):
    async def test_deploys_loaded_compose_definition_through_runtime_port(self):
        stack_definition = StackDefinition(name="jenkins", compose_content="services: {}")
        repository = _FakeComposeRepository(stack_definition)
        runtime = _FakeSwarmRuntime(stack_exists=True)
        contract = ServiceStackContract("jenkins", ("jenkins",))
        service = EnsureSwarmStack(repository, runtime, contract)

        await service.run()

        self.assertEqual(["jenkins"], repository.requested_stacks)
        self.assertEqual([stack_definition], runtime.deployed_stacks)

    async def test_verify_confirms_stack_registration_and_expected_services(self):
        repository = _FakeComposeRepository(StackDefinition(name="rabbitmq", compose_content="services: {}"))
        runtime = _FakeSwarmRuntime(
            stack_exists=True,
            services=(SwarmServiceStatus("rabbitmq_rabbitmq", 1, 1),),
        )
        service = EnsureSwarmStack(
            repository,
            runtime,
            ServiceStackContract("rabbitmq", ("rabbitmq",)),
        )

        verification = await service.verify()

        self.assertEqual(VerificationStatus.VERIFIED, verification.status)
        self.assertEqual("deployment:rabbitmq-stack", verification.target_id)
        self.assertEqual("true", verification.evidence["stack_registered"])


class _FakeComposeRepository:
    def __init__(self, stack_definition: StackDefinition):
        self.stack_definition = stack_definition
        self.requested_stacks: list[str] = []

    def get_compose_of(self, stack_name: str) -> StackDefinition:
        self.requested_stacks.append(stack_name)
        return self.stack_definition


class _FakeSwarmRuntime:
    def __init__(
        self,
        *,
        stack_exists: bool,
        services: tuple[SwarmServiceStatus, ...] = (),
    ):
        self._stack_exists = stack_exists
        self._services = services
        self.deployed_stacks: list[StackDefinition] = []

    def deploy_stack(self, stack_definition: StackDefinition) -> None:
        self.deployed_stacks.append(stack_definition)

    def stack_exists(self, stack_name: str) -> bool:
        return self._stack_exists

    def list_stack_services(self, stack_name: str) -> tuple[SwarmServiceStatus, ...]:
        return self._services
