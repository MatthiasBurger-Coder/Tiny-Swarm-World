import unittest
from tests.support.sonar_safe_literals import sensitive_assignment

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
        self.assertEqual(runtime.deployed_stacks, [(stack_definition, {})])

    async def test_deploys_stack_with_environment_through_runtime_port(self):
        stack_definition = StackDefinition(name="service-access", compose_content="services: {}")
        repository = _FakeComposeRepository(stack_definition)
        runtime = _FakeSwarmRuntime(stack_exists=True)
        service = EnsureSwarmStack(
            repository,
            runtime,
            ServiceStackContract("service-access", ("service-access-dashboard",)),
            stack_environment={"TSW_VAULTWARDEN_ADMIN_TOKEN_SECRET": "operator_defined"},
        )

        await service.run()

        self.assertEqual(
            runtime.deployed_stacks,
            [(stack_definition, {"TSW_VAULTWARDEN_ADMIN_TOKEN_SECRET": "operator_defined"})],
        )

    async def test_verify_confirms_stack_registration_and_expected_services(self):
        repository = _FakeComposeRepository(StackDefinition(name="pulsar", compose_content="services: {}"))
        runtime = _FakeSwarmRuntime(
            stack_exists=True,
            services=(SwarmServiceStatus("pulsar_pulsar", 1, 1),),
        )
        service = EnsureSwarmStack(
            repository,
            runtime,
            ServiceStackContract("pulsar", ("pulsar",)),
        )

        verification = await service.verify()

        self.assertEqual(VerificationStatus.VERIFIED, verification.status)
        self.assertEqual(verification.target_id, "deployment:pulsar-stack")
        self.assertEqual("true", verification.evidence["stack_registered"])

    async def test_verify_fails_when_stack_is_missing(self):
        service = EnsureSwarmStack(
            _FakeComposeRepository(StackDefinition(name="pulsar", compose_content="services: {}")),
            _FakeSwarmRuntime(
                stack_exists=False,
                services=(SwarmServiceStatus("pulsar_pulsar", 1, 1),),
            ),
            ServiceStackContract("pulsar", ("pulsar",)),
        )

        verification = await service.verify()

        self.assertEqual(VerificationStatus.FAILED_TO_VERIFY, verification.status)
        self.assertEqual(verification.evidence["stack_registered"], "false")

    async def test_verify_fails_when_required_service_is_missing(self):
        service = EnsureSwarmStack(
            _FakeComposeRepository(StackDefinition(name="pulsar", compose_content="services: {}")),
            _FakeSwarmRuntime(stack_exists=True, services=()),
            ServiceStackContract("pulsar", ("pulsar",)),
        )

        verification = await service.verify()

        self.assertEqual(VerificationStatus.FAILED_TO_VERIFY, verification.status)
        self.assertEqual(verification.evidence["missing_services"], "pulsar")

    async def test_verify_sanitizes_runtime_failure_and_does_not_deploy(self):
        runtime = _FakeSwarmRuntime(
            stack_exists=True,
            stack_exception=RuntimeError(sensitive_assignment()),
        )
        service = EnsureSwarmStack(
            _FakeComposeRepository(StackDefinition(name="pulsar", compose_content="services: {}")),
            runtime,
            ServiceStackContract("pulsar", ("pulsar",)),
        )

        verification = await service.verify()

        self.assertEqual(VerificationStatus.FAILED_TO_VERIFY, verification.status)
        self.assertEqual(runtime.deployed_stacks, [])
        self.assertNotIn("secret", str(verification.to_dict()).casefold())


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
        stack_exception: Exception | None = None,
    ):
        self._stack_exists = stack_exists
        self._services = services
        self.stack_exception = stack_exception
        self.deployed_stacks: list[tuple[StackDefinition, dict[str, str]]] = []

    def deploy_stack(
        self,
        stack_definition: StackDefinition,
        stack_environment: dict[str, str] | None = None,
    ) -> None:
        self.deployed_stacks.append((stack_definition, dict(stack_environment or {})))

    def stack_exists(self, stack_name: str) -> bool:
        if self.stack_exception is not None:
            raise self.stack_exception
        return self._stack_exists

    def list_stack_services(self, stack_name: str) -> tuple[SwarmServiceStatus, ...]:
        if self.stack_exception is not None:
            raise self.stack_exception
        return self._services

    def external_secret_exists(self, name: str) -> bool:
        return True

    def ensure_external_secret(self, name: str, value: str) -> None:
        return None
