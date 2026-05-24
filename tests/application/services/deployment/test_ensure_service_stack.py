import unittest

from tiny_swarm_world.application.services.deployment.ensure_service_stack import EnsureServiceStack
from tiny_swarm_world.domain.deployment import ServiceStackContract
from tiny_swarm_world.domain.deployment.stack_definition import StackDefinition
from tiny_swarm_world.domain.inventory import VerificationStatus


class TestEnsureServiceStack(unittest.IsolatedAsyncioTestCase):
    async def test_creates_missing_default_service_stack(self):
        stack_definition = StackDefinition(name="jenkins", compose_content="services: {}")
        compose_repository = _FakeComposeRepository(stack_definition)
        portainer_client = _FakePortainerClient(stack_ids=[None])
        service = EnsureServiceStack(
            compose_repository,
            portainer_client,
            ServiceStackContract("jenkins", ("jenkins",)),
            "local",
        )

        await service.run()

        self.assertEqual(["jenkins"], compose_repository.requested_stacks)
        self.assertEqual(["local"], portainer_client.requested_endpoints)
        self.assertEqual([("jenkins", 7)], portainer_client.created_stacks)
        self.assertEqual([], portainer_client.updated_stacks)

    async def test_updates_existing_default_service_stack(self):
        stack_definition = StackDefinition(name="rabbitmq", compose_content="services: {}")
        compose_repository = _FakeComposeRepository(stack_definition)
        portainer_client = _FakePortainerClient(stack_ids=[42])
        service = EnsureServiceStack(
            compose_repository,
            portainer_client,
            ServiceStackContract("rabbitmq", ("rabbitmq",)),
            "local",
        )

        await service.run()

        self.assertEqual([], portainer_client.created_stacks)
        self.assertEqual([(42, "rabbitmq", 7)], portainer_client.updated_stacks)

    async def test_verify_blocks_when_only_stack_presence_is_known(self):
        stack_definition = StackDefinition(name="sonarqube", compose_content="services: {}")
        compose_repository = _FakeComposeRepository(stack_definition)
        portainer_client = _FakePortainerClient(stack_ids=[31])
        service = EnsureServiceStack(
            compose_repository,
            portainer_client,
            ServiceStackContract("sonarqube", ("sonarqube", "sonar_db")),
            "local",
        )

        verification = await service.verify()

        self.assertEqual(VerificationStatus.BLOCKED, verification.status)
        self.assertEqual("deployment:sonarqube-service-readiness", verification.target_id)
        self.assertEqual("service_readiness", verification.evidence["readiness_scope"])
        self.assertEqual("true", verification.evidence["stack_registered"])
        self.assertIn("required services are not observed", verification.message)

    async def test_verify_reports_missing_stack_without_running_compose(self):
        stack_definition = StackDefinition(name="swagger", compose_content="services: {}")
        compose_repository = _FakeComposeRepository(stack_definition)
        portainer_client = _FakePortainerClient(stack_ids=[None])
        service = EnsureServiceStack(
            compose_repository,
            portainer_client,
            ServiceStackContract("swagger", ("swagger-ui",)),
            "local",
        )

        verification = await service.verify()

        self.assertEqual(VerificationStatus.FAILED_TO_VERIFY, verification.status)
        self.assertEqual([], compose_repository.requested_stacks)
        self.assertEqual("false", verification.evidence["stack_registered"])

    async def test_verify_sanitizes_portainer_client_failures(self):
        stack_definition = StackDefinition(name="nexus", compose_content="services: {}")
        compose_repository = _FakeComposeRepository(stack_definition)
        portainer_client = _FakePortainerClient(stack_exception=RuntimeError("secret=leaked"))
        service = EnsureServiceStack(
            compose_repository,
            portainer_client,
            ServiceStackContract("nexus", ("nexus",)),
            "local",
        )

        verification = await service.verify()

        self.assertEqual(VerificationStatus.FAILED_TO_VERIFY, verification.status)
        self.assertIn("RuntimeError", verification.message)
        self.assertNotIn("secret", verification.message)
        self.assertNotIn("secret", str(verification.to_dict()))


class _FakeComposeRepository:
    def __init__(self, stack_definition: StackDefinition):
        self.stack_definition = stack_definition
        self.requested_stacks: list[str] = []

    def get_compose_of(self, stack_name: str) -> StackDefinition:
        self.requested_stacks.append(stack_name)
        return self.stack_definition


class _FakePortainerClient:
    def __init__(
        self,
        stack_ids: list[int | None] | None = None,
        stack_exception: Exception | None = None,
    ):
        self.stack_ids = list(stack_ids or [])
        self.stack_exception = stack_exception
        self.requested_endpoints: list[str] = []
        self.created_stacks: list[tuple[str, int]] = []
        self.updated_stacks: list[tuple[int, str, int]] = []

    def get_endpoint_id_by_name(self, endpoint_name: str) -> int:
        self.requested_endpoints.append(endpoint_name)
        return 7

    def find_stack_id_by_name(self, stack_name: str) -> int | None:
        if self.stack_exception:
            raise self.stack_exception
        if self.stack_ids:
            return self.stack_ids.pop(0)
        return None

    def create_stack(self, stack_definition: StackDefinition, endpoint_id: int) -> None:
        self.created_stacks.append((stack_definition.name, endpoint_id))

    def update_stack(self, stack_id: int, stack_definition: StackDefinition, endpoint_id: int) -> None:
        self.updated_stacks.append((stack_id, stack_definition.name, endpoint_id))
