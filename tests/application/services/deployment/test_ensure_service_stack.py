import unittest
from tests.support.sonar_safe_literals import sensitive_assignment

from tiny_swarm_world.application.ports.clients.port_deployment_gateway import (
    DeploymentStackRequest,
)
from tiny_swarm_world.application.services.deployment.ensure_service_stack import EnsureServiceStack
from tiny_swarm_world.domain.deployment import ServiceStackContract
from tiny_swarm_world.domain.deployment.stack_definition import StackDefinition
from tiny_swarm_world.domain.inventory import VerificationStatus


class TestEnsureServiceStack(unittest.IsolatedAsyncioTestCase):
    async def test_creates_missing_default_service_stack(self):
        stack_definition = StackDefinition(name="jenkins", compose_content="services: {}")
        compose_repository = _FakeComposeRepository(stack_definition)
        deployment_gateway = _FakeDeploymentGateway(registered_values=[False])
        service = EnsureServiceStack(
            compose_repository,
            deployment_gateway,
            ServiceStackContract("jenkins", ("jenkins",)),
        )

        await service.run()

        self.assertEqual(["jenkins"], compose_repository.requested_stacks)
        self.assertEqual(1, len(deployment_gateway.applied_requests))
        request = deployment_gateway.applied_requests[0]
        self.assertEqual("jenkins", request.target_stack)
        self.assertEqual(stack_definition, request.stack_definition)
        self.assertEqual({}, dict(request.stack_environment))

    async def test_updates_existing_default_service_stack(self):
        stack_definition = StackDefinition(name="rabbitmq", compose_content="services: {}")
        compose_repository = _FakeComposeRepository(stack_definition)
        deployment_gateway = _FakeDeploymentGateway(registered_values=[True])
        service = EnsureServiceStack(
            compose_repository,
            deployment_gateway,
            ServiceStackContract("rabbitmq", ("rabbitmq",)),
        )

        await service.run()

        self.assertEqual(1, len(deployment_gateway.applied_requests))
        self.assertEqual("rabbitmq", deployment_gateway.applied_requests[0].target_stack)

    async def test_passes_stack_environment_when_creating_service_access_stack(self):
        stack_definition = StackDefinition(name="service-access", compose_content="services: {}")
        compose_repository = _FakeComposeRepository(stack_definition)
        deployment_gateway = _FakeDeploymentGateway(registered_values=[False])
        service = EnsureServiceStack(
            compose_repository,
            deployment_gateway,
            ServiceStackContract("service-access", ("service-access-dashboard",)),
            stack_environment={"TSW_VAULTWARDEN_ADMIN_TOKEN_SECRET": "operator_defined"},
        )

        await service.run()

        self.assertEqual(
            {"TSW_VAULTWARDEN_ADMIN_TOKEN_SECRET": "operator_defined"},
            dict(deployment_gateway.applied_requests[0].stack_environment),
        )

    async def test_treats_create_timeout_as_success_when_stack_registration_is_visible(self):
        stack_definition = StackDefinition(name="swagger", compose_content="services: {}")
        compose_repository = _FakeComposeRepository(stack_definition)
        deployment_gateway = _FakeDeploymentGateway(
            registered_values=[True],
            apply_exception=TimeoutError("Deployment gateway timed out"),
        )
        service = EnsureServiceStack(
            compose_repository,
            deployment_gateway,
            ServiceStackContract("swagger", ("swagger-ui",)),
            verify_wait_seconds=0,
        )

        await service.run()

        self.assertEqual(["swagger"], deployment_gateway.registration_checks)

    async def test_treats_update_timeout_as_success_when_stack_registration_is_visible(self):
        stack_definition = StackDefinition(name="swagger", compose_content="services: {}")
        compose_repository = _FakeComposeRepository(stack_definition)
        deployment_gateway = _FakeDeploymentGateway(
            registered_values=[True],
            apply_exception=TimeoutError("Deployment gateway timed out"),
        )
        service = EnsureServiceStack(
            compose_repository,
            deployment_gateway,
            ServiceStackContract("swagger", ("swagger-ui",)),
            verify_wait_seconds=0,
        )

        await service.run()

        self.assertEqual(["swagger"], deployment_gateway.registration_checks)

    async def test_keeps_create_timeout_when_stack_registration_is_missing(self):
        stack_definition = StackDefinition(name="swagger", compose_content="services: {}")
        compose_repository = _FakeComposeRepository(stack_definition)
        deployment_gateway = _FakeDeploymentGateway(
            registered_values=[False],
            apply_exception=TimeoutError("Deployment gateway timed out"),
        )
        service = EnsureServiceStack(
            compose_repository,
            deployment_gateway,
            ServiceStackContract("swagger", ("swagger-ui",)),
            verify_wait_seconds=0,
        )

        with self.assertRaises(TimeoutError):
            await service.run()

    async def test_verify_reports_registered_stack_without_claiming_readiness(self):
        stack_definition = StackDefinition(name="sonarqube", compose_content="services: {}")
        compose_repository = _FakeComposeRepository(stack_definition)
        deployment_gateway = _FakeDeploymentGateway(registered_values=[True])
        service = EnsureServiceStack(
            compose_repository,
            deployment_gateway,
            ServiceStackContract("sonarqube", ("sonarqube", "sonar_db")),
        )

        verification = await service.verify()

        self.assertEqual(VerificationStatus.VERIFIED, verification.status)
        self.assertEqual("deployment:sonarqube-stack", verification.target_id)
        self.assertEqual("deployment_gateway_stack", verification.evidence["registration_scope"])
        self.assertEqual("false", verification.evidence["readiness_observed"])
        self.assertEqual("true", verification.evidence["stack_registered"])
        self.assertIn("service readiness remains", verification.message)

    async def test_verify_retries_transient_portainer_stack_lookup_failure(self):
        stack_definition = StackDefinition(name="swagger", compose_content="services: {}")
        compose_repository = _FakeComposeRepository(stack_definition)
        deployment_gateway = _FakeDeploymentGateway(
            registered_values=[True],
            stack_exceptions=[RuntimeError("temporary gateway lookup failure")],
        )
        service = EnsureServiceStack(
            compose_repository,
            deployment_gateway,
            ServiceStackContract("swagger", ("swagger-ui",)),
            verify_wait_seconds=0,
        )

        verification = await service.verify()

        self.assertEqual(VerificationStatus.VERIFIED, verification.status)
        self.assertEqual("true", verification.evidence["stack_registered"])
        self.assertEqual("2", verification.evidence["verify_attempt"])

    async def test_verify_reports_missing_stack_without_running_compose(self):
        stack_definition = StackDefinition(name="swagger", compose_content="services: {}")
        compose_repository = _FakeComposeRepository(stack_definition)
        deployment_gateway = _FakeDeploymentGateway(registered_values=[False])
        service = EnsureServiceStack(
            compose_repository,
            deployment_gateway,
            ServiceStackContract("swagger", ("swagger-ui",)),
        )

        verification = await service.verify()

        self.assertEqual(VerificationStatus.FAILED_TO_VERIFY, verification.status)
        self.assertEqual([], compose_repository.requested_stacks)
        self.assertEqual("false", verification.evidence["stack_registered"])
        self.assertEqual("deployment_apply_failed", verification.evidence["classification"])

    async def test_run_rejects_compose_stack_name_mismatch(self):
        stack_definition = StackDefinition(name="wrong-stack", compose_content="services: {}")
        compose_repository = _FakeComposeRepository(stack_definition)
        deployment_gateway = _FakeDeploymentGateway(registered_values=[False])
        service = EnsureServiceStack(
            compose_repository,
            deployment_gateway,
            ServiceStackContract("service-access", ("service-access-dashboard",)),
        )

        with self.assertRaises(ValueError):
            await service.run()

        self.assertEqual(["service-access"], compose_repository.requested_stacks)
        self.assertEqual([], deployment_gateway.applied_requests)

    async def test_verify_sanitizes_portainer_client_failures(self):
        stack_definition = StackDefinition(name="nexus", compose_content="services: {}")
        compose_repository = _FakeComposeRepository(stack_definition)
        deployment_gateway = _FakeDeploymentGateway(
            stack_exception=RuntimeError(sensitive_assignment())
        )
        service = EnsureServiceStack(
            compose_repository,
            deployment_gateway,
            ServiceStackContract("nexus", ("nexus",)),
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


class _FakeDeploymentGateway:
    def __init__(
        self,
        registered_values: list[bool] | None = None,
        stack_exception: Exception | None = None,
        stack_exceptions: list[Exception] | None = None,
        apply_exception: Exception | None = None,
    ):
        self.registered_values = list(registered_values or [])
        self.stack_exception = stack_exception
        self.stack_exceptions = list(stack_exceptions or [])
        self.apply_exception = apply_exception
        self.applied_requests: list[DeploymentStackRequest] = []
        self.registration_checks: list[str] = []

    def apply_stack(self, request: DeploymentStackRequest) -> None:
        self.applied_requests.append(request)
        if self.apply_exception is not None:
            raise self.apply_exception

    def stack_registered(self, stack_name: str) -> bool:
        self.registration_checks.append(stack_name)
        if self.stack_exceptions:
            raise self.stack_exceptions.pop(0)
        if self.stack_exception:
            raise self.stack_exception
        if self.registered_values:
            return self.registered_values.pop(0)
        return False
