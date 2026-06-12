import unittest
from tests.support.sonar_safe_literals import sensitive_assignment

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
        self.assertEqual([("jenkins", 7, {})], portainer_client.created_stacks)
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
        self.assertEqual([(42, "rabbitmq", 7, {})], portainer_client.updated_stacks)

    async def test_passes_stack_environment_when_creating_service_access_stack(self):
        stack_definition = StackDefinition(name="service-access", compose_content="services: {}")
        compose_repository = _FakeComposeRepository(stack_definition)
        portainer_client = _FakePortainerClient(stack_ids=[None])
        service = EnsureServiceStack(
            compose_repository,
            portainer_client,
            ServiceStackContract("service-access", ("service-access-dashboard",)),
            "local",
            stack_environment={"TSW_VAULTWARDEN_ADMIN_TOKEN_SECRET": "operator_defined"},
        )

        await service.run()

        self.assertEqual(
            [("service-access", 7, {"TSW_VAULTWARDEN_ADMIN_TOKEN_SECRET": "operator_defined"})],
            portainer_client.created_stacks,
        )

    async def test_treats_create_timeout_as_success_when_stack_registration_is_visible(self):
        stack_definition = StackDefinition(name="swagger", compose_content="services: {}")
        compose_repository = _FakeComposeRepository(stack_definition)
        portainer_client = _FakePortainerClient(
            stack_ids=[None, 52],
            create_exception=TimeoutError("Portainer create timed out"),
        )
        service = EnsureServiceStack(
            compose_repository,
            portainer_client,
            ServiceStackContract("swagger", ("swagger-ui",)),
            "local",
            verify_wait_seconds=0,
        )

        await service.run()

        self.assertEqual([("swagger", 7, {})], portainer_client.created_stacks)

    async def test_treats_update_timeout_as_success_when_stack_registration_is_visible(self):
        stack_definition = StackDefinition(name="swagger", compose_content="services: {}")
        compose_repository = _FakeComposeRepository(stack_definition)
        portainer_client = _FakePortainerClient(
            stack_ids=[52, 52],
            update_exception=TimeoutError("Portainer update timed out"),
        )
        service = EnsureServiceStack(
            compose_repository,
            portainer_client,
            ServiceStackContract("swagger", ("swagger-ui",)),
            "local",
            verify_wait_seconds=0,
        )

        await service.run()

        self.assertEqual([(52, "swagger", 7, {})], portainer_client.updated_stacks)

    async def test_keeps_create_timeout_when_stack_registration_is_missing(self):
        stack_definition = StackDefinition(name="swagger", compose_content="services: {}")
        compose_repository = _FakeComposeRepository(stack_definition)
        portainer_client = _FakePortainerClient(
            stack_ids=[None, None],
            create_exception=TimeoutError("Portainer create timed out"),
        )
        service = EnsureServiceStack(
            compose_repository,
            portainer_client,
            ServiceStackContract("swagger", ("swagger-ui",)),
            "local",
            verify_wait_seconds=0,
        )

        with self.assertRaises(TimeoutError):
            await service.run()

    async def test_verify_reports_registered_stack_without_claiming_readiness(self):
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

        self.assertEqual(VerificationStatus.VERIFIED, verification.status)
        self.assertEqual("deployment:sonarqube-stack", verification.target_id)
        self.assertEqual("portainer_stack", verification.evidence["registration_scope"])
        self.assertEqual("false", verification.evidence["readiness_observed"])
        self.assertEqual("true", verification.evidence["stack_registered"])
        self.assertIn("service readiness remains", verification.message)

    async def test_verify_retries_transient_portainer_stack_lookup_failure(self):
        stack_definition = StackDefinition(name="swagger", compose_content="services: {}")
        compose_repository = _FakeComposeRepository(stack_definition)
        portainer_client = _FakePortainerClient(
            stack_ids=[31],
            stack_exceptions=[RuntimeError("temporary Portainer lookup failure")],
        )
        service = EnsureServiceStack(
            compose_repository,
            portainer_client,
            ServiceStackContract("swagger", ("swagger-ui",)),
            "local",
            verify_wait_seconds=0,
        )

        verification = await service.verify()

        self.assertEqual(VerificationStatus.VERIFIED, verification.status)
        self.assertEqual("true", verification.evidence["stack_registered"])
        self.assertEqual("2", verification.evidence["verify_attempt"])

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
        self.assertEqual("deployment_apply_failed", verification.evidence["classification"])

    async def test_run_rejects_compose_stack_name_mismatch(self):
        stack_definition = StackDefinition(name="wrong-stack", compose_content="services: {}")
        compose_repository = _FakeComposeRepository(stack_definition)
        portainer_client = _FakePortainerClient(stack_ids=[None])
        service = EnsureServiceStack(
            compose_repository,
            portainer_client,
            ServiceStackContract("service-access", ("service-access-dashboard",)),
            "local",
        )

        with self.assertRaises(ValueError):
            await service.run()

        self.assertEqual(["service-access"], compose_repository.requested_stacks)
        self.assertEqual([], portainer_client.requested_endpoints)

    async def test_verify_sanitizes_portainer_client_failures(self):
        stack_definition = StackDefinition(name="nexus", compose_content="services: {}")
        compose_repository = _FakeComposeRepository(stack_definition)
        portainer_client = _FakePortainerClient(stack_exception=RuntimeError(sensitive_assignment()))
        service = EnsureServiceStack(
            compose_repository,
            portainer_client,
            ServiceStackContract("nexus", ("nexus",)),
            "local",
        )

        verification = await service.verify()

        self.assertEqual(VerificationStatus.FAILED_TO_VERIFY, verification.status)
        self.assertIn("RuntimeError", verification.message)
        self.assertEqual("deployment_apply_failed", verification.evidence["classification"])
        self.assertEqual("RuntimeError", verification.evidence["exception_type"])
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
        stack_exceptions: list[Exception] | None = None,
        create_exception: Exception | None = None,
        update_exception: Exception | None = None,
    ):
        self.stack_ids = list(stack_ids or [])
        self.stack_exception = stack_exception
        self.stack_exceptions = list(stack_exceptions or [])
        self.create_exception = create_exception
        self.update_exception = update_exception
        self.requested_endpoints: list[str] = []
        self.created_stacks: list[tuple[str, int, dict[str, str]]] = []
        self.updated_stacks: list[tuple[int, str, int, dict[str, str]]] = []

    def get_endpoint_id_by_name(self, endpoint_name: str) -> int:
        self.requested_endpoints.append(endpoint_name)
        return 7

    def find_stack_id_by_name(self, stack_name: str) -> int | None:
        if self.stack_exceptions:
            raise self.stack_exceptions.pop(0)
        if self.stack_exception:
            raise self.stack_exception
        if self.stack_ids:
            return self.stack_ids.pop(0)
        return None

    def create_stack(
        self,
        stack_definition: StackDefinition,
        endpoint_id: int,
        stack_environment: dict[str, str] | None = None,
    ) -> None:
        self.created_stacks.append((stack_definition.name, endpoint_id, dict(stack_environment or {})))
        if self.create_exception is not None:
            raise self.create_exception

    def update_stack(
        self,
        stack_id: int,
        stack_definition: StackDefinition,
        endpoint_id: int,
        stack_environment: dict[str, str] | None = None,
    ) -> None:
        self.updated_stacks.append((stack_id, stack_definition.name, endpoint_id, dict(stack_environment or {})))
        if self.update_exception is not None:
            raise self.update_exception
