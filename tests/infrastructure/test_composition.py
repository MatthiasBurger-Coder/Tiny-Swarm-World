import asyncio
import unittest
from dataclasses import fields
from unittest.mock import patch

from tiny_swarm_world.application.services.deployment.ensure_service_stack import EnsureServiceStack
from tiny_swarm_world.application.services.platform import PlatformWorkflowStatus
from tiny_swarm_world.application.services.platform.preflight_service import PreflightService
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus
from tiny_swarm_world.domain.deployment import ServiceStackProfile
from tiny_swarm_world.domain.preflight import (
    LIVE_CONSENT_ENVIRONMENT_VALUE,
    LIVE_CONSENT_PHRASE,
    LiveConsent,
)
from tiny_swarm_world.infrastructure import composition
from tiny_swarm_world.infrastructure.adapters.preflight import HostPreflightProbe


class TestComposition(unittest.TestCase):
    def test_application_services_separates_service_bundles(self):
        self.assertIsNot(composition.ApplicationServices, composition.PlatformServices)

        field_names = {field.name for field in fields(composition.ApplicationServices)}

        self.assertEqual({"platform", "artifacts", "deployment"}, field_names)

    def test_service_bundle_types_are_distinct_dataclasses(self):
        self.assertNotEqual(composition.PlatformServices, composition.ArtifactServices)
        self.assertNotEqual(composition.PlatformServices, composition.DeploymentServices)
        self.assertNotEqual(composition.ArtifactServices, composition.DeploymentServices)

    def test_build_application_services_aggregates_separate_builders(self):
        platform = object()
        artifacts = object()
        deployment = object()

        with patch.object(
            composition,
            "build_platform_services",
            return_value=platform,
        ) as build_platform_services:
            with patch.object(
                composition,
                "build_artifact_services",
                return_value=artifacts,
            ) as build_artifact_services:
                with patch.object(
                    composition,
                    "build_deployment_services",
                    return_value=deployment,
                ) as build_deployment_services:
                    services = composition.build_application_services()

        self.assertIs(services.platform, platform)
        self.assertIs(services.artifacts, artifacts)
        self.assertIs(services.deployment, deployment)
        build_platform_services.assert_called_once_with()
        build_artifact_services.assert_called_once_with()
        build_deployment_services.assert_called_once_with()

    def test_platform_services_contains_preflight_service(self):
        field_names = {field.name for field in fields(composition.PlatformServices)}

        self.assertIn("preflight", field_names)

    def test_platform_services_contains_workflow_bundle(self):
        platform_field_names = {field.name for field in fields(composition.PlatformServices)}
        workflow_field_names = {field.name for field in fields(composition.PlatformWorkflows)}

        self.assertIn("workflows", platform_field_names)
        self.assertEqual({"init", "reconcile", "reset", "destroy", "verify"}, workflow_field_names)

    def test_artifact_and_deployment_service_bundles_exist(self):
        artifact_field_names = {field.name for field in fields(composition.ArtifactServices)}
        artifact_workflow_names = {field.name for field in fields(composition.ArtifactWorkflows)}
        deployment_field_names = {field.name for field in fields(composition.DeploymentServices)}
        deployment_workflow_names = {field.name for field in fields(composition.DeploymentWorkflows)}
        setup_field_names = {field.name for field in fields(composition.SetupServices)}
        setup_workflow_names = {field.name for field in fields(composition.SetupWorkflows)}

        self.assertEqual({"workflows"}, artifact_field_names)
        self.assertEqual({"prepare", "verify"}, artifact_workflow_names)
        self.assertEqual({"workflows"}, deployment_field_names)
        self.assertEqual({"bootstrap", "apply", "verify"}, deployment_workflow_names)
        self.assertEqual({"workflows"}, setup_field_names)
        self.assertEqual({"run"}, setup_workflow_names)

    def test_build_platform_services_wires_preflight_adapter(self):
        with patch.object(composition, "PortVmRepositoryYaml") as vm_repository_factory:
            with patch.object(
                composition,
                "PortNetplanRepositoryYaml",
            ) as netplan_repository_factory:
                services = composition.build_platform_services()

        vm_repository_factory.assert_called_once_with()
        netplan_repository_factory.assert_called_once_with()
        self.assertIsInstance(services.preflight, PreflightService)
        self.assertIsInstance(services.preflight.host_probe, HostPreflightProbe)

    def test_build_platform_services_wires_workflow_objects(self):
        evidence_repository = _RecordingEvidenceRepository()
        with patch.object(composition, "PortVmRepositoryYaml"):
            with patch.object(composition, "PortNetplanRepositoryYaml"):
                with patch.object(
                    composition,
                    "VerificationEvidenceLocalRepository",
                    return_value=evidence_repository,
                ):
                    services = composition.build_platform_services()

        self.assertIsInstance(services.workflows.init, composition.PlatformInitWorkflow)
        self.assertIsInstance(services.workflows.reconcile, composition.PlatformReconcileWorkflow)
        self.assertIsInstance(services.workflows.reset, composition.PlatformResetWorkflow)
        self.assertIsInstance(services.workflows.destroy, composition.PlatformDestroyWorkflow)
        self.assertIsInstance(services.workflows.verify, composition.PlatformVerifyWorkflow)
        self.assertIs(
            evidence_repository,
            services.workflows.init.verification_evidence_repository,
        )
        self.assertIs(
            evidence_repository,
            services.workflows.reconcile.verification_evidence_repository,
        )

    def test_build_platform_services_wires_workflow_types_without_evidence_patch(self):
        with patch.object(composition, "PortVmRepositoryYaml"):
            with patch.object(composition, "PortNetplanRepositoryYaml"):
                services = composition.build_platform_services()

        self.assertIsInstance(services.workflows.init, composition.PlatformInitWorkflow)
        self.assertIsInstance(services.workflows.reconcile, composition.PlatformReconcileWorkflow)
        self.assertIsInstance(services.workflows.reset, composition.PlatformResetWorkflow)
        self.assertIsInstance(services.workflows.destroy, composition.PlatformDestroyWorkflow)
        self.assertIsInstance(services.workflows.verify, composition.PlatformVerifyWorkflow)

    def test_build_artifact_services_wires_artifact_contracts_without_running_clients(self):
        services = composition.build_artifact_services()

        self.assertIsInstance(services.workflows.prepare, composition.ArtifactPrepareWorkflow)
        self.assertIsInstance(services.workflows.verify, composition.ArtifactVerifyWorkflow)
        self.assertEqual(
            (
                "artifacts:nexus-ready",
                "artifacts:nexus-admin-access",
                "artifacts:nexus-docker-hosted-repository",
                "artifacts:nexus-maven-proxy-repository",
                "artifacts:jenkins-image",
                "artifacts:service-access-dashboard-image",
                "artifacts:service-access-nginx-image",
            ),
            tuple(step.verification_target_id for step in services.workflows.prepare.steps),
        )

    def test_build_artifact_services_does_not_call_live_clients_during_construction(self):
        with patch.object(composition, "MultipassNexusHttpClient") as nexus_client:
            with patch.object(composition, "MultipassContainerRuntime") as container_runtime:
                with patch.object(composition, "MultipassContainerImagePublisher") as image_publisher:
                    services = composition.build_artifact_services()

        nexus_client.assert_called_once_with()
        container_runtime.assert_called_once_with()
        image_publisher.assert_called_once()
        self.assertEqual(7, len(services.workflows.prepare.steps))
        self.assertEqual(7, len(services.workflows.verify.checks))

    def test_build_deployment_services_wires_stack_contracts_without_running_runtime(self):
        with patch.object(composition, "ComposeFileRepositoryYaml"):
            with patch.object(composition, "MultipassSwarmRuntime"):
                with patch.object(composition, "MultipassPortainerAdminClient"):
                    with patch.object(composition, "PortainerHttpClient"):
                        services = composition.build_deployment_services()

        self.assertIsInstance(services.workflows.bootstrap, composition.DeploymentApplyWorkflow)
        self.assertIsInstance(services.workflows.apply, composition.DeploymentApplyWorkflow)
        self.assertIsInstance(services.workflows.verify, composition.DeploymentVerifyWorkflow)
        self.assertEqual(
            (
                "deployment:portainer-stack",
                "deployment:portainer-admin-access",
                "deployment:nexus-stack",
            ),
            tuple(step.verification_target_id for step in services.workflows.bootstrap.steps),
        )
        self.assertEqual(
            (
                "deployment:jenkins-stack",
                "deployment:rabbitmq-stack",
                "deployment:sonarqube-stack",
                "deployment:swagger-stack",
                "deployment:service-access-stack",
            ),
            tuple(step.verification_target_id for step in services.workflows.apply.steps),
        )
        self.assertEqual(
            (
                "deployment:portainer-service-readiness",
                "deployment:nexus-service-readiness",
                "deployment:jenkins-service-readiness",
                "deployment:rabbitmq-service-readiness",
                "deployment:sonarqube-service-readiness",
                "deployment:swagger-service-readiness",
                "deployment:service-access-service-readiness",
            ),
            tuple(check.verification_target_id for check in services.workflows.verify.checks),
        )

    def test_build_deployment_services_does_not_call_runtime_during_construction(self):
        with patch.object(composition, "ComposeFileRepositoryYaml") as compose_repository:
            with patch.object(composition, "MultipassSwarmRuntime") as swarm_runtime:
                with patch.object(composition, "MultipassPortainerAdminClient") as portainer_client:
                    with patch.object(composition, "PortainerHttpClient") as stack_client:
                        services = composition.build_deployment_services()

        compose_repository.assert_called_once_with()
        swarm_runtime.assert_called_once_with()
        portainer_client.assert_called_once_with()
        stack_client.assert_called_once()
        self.assertEqual(3, len(services.workflows.bootstrap.steps))
        self.assertEqual(5, len(services.workflows.apply.steps))
        self.assertEqual(7, len(services.workflows.verify.checks))

    def test_build_deployment_services_can_select_service_access_profile(self):
        with patch.object(composition, "ComposeFileRepositoryYaml"):
            with patch.object(composition, "MultipassSwarmRuntime"):
                with patch.object(composition, "MultipassPortainerAdminClient"):
                    with patch.object(composition, "PortainerHttpClient"):
                        services = composition.build_deployment_services(
                            service_profile=ServiceStackProfile.SERVICE_ACCESS
                        )

        self.assertEqual(
            (
                "deployment:portainer-stack",
                "deployment:portainer-admin-access",
                "deployment:nexus-stack",
            ),
            tuple(step.verification_target_id for step in services.workflows.bootstrap.steps),
        )
        self.assertEqual(
            (
                "deployment:jenkins-stack",
                "deployment:rabbitmq-stack",
                "deployment:sonarqube-stack",
                "deployment:swagger-stack",
                "deployment:service-access-stack",
            ),
            tuple(step.verification_target_id for step in services.workflows.apply.steps),
        )
        self.assertTrue(
            all(isinstance(step, EnsureServiceStack) for step in services.workflows.apply.steps)
        )
        self.assertEqual(
            (
                "deployment:portainer-service-readiness",
                "deployment:nexus-service-readiness",
                "deployment:jenkins-service-readiness",
                "deployment:rabbitmq-service-readiness",
                "deployment:sonarqube-service-readiness",
                "deployment:swagger-service-readiness",
                "deployment:service-access-service-readiness",
            ),
            tuple(check.verification_target_id for check in services.workflows.verify.checks),
        )

    def test_build_artifact_services_uses_static_local_defaults_not_environment_passwords(self):
        with patch.dict("os.environ", {"TSW_NEXUS_ADMIN_PASSWORD": "operator-supplied"}, clear=True):
            services = composition.build_artifact_services()

        image_publisher = services.workflows.prepare.steps[-1].image_publisher
        self.assertEqual(
            "MyAdminPassWord1234-126354654",
            image_publisher.registry_password,
        )

    def test_build_setup_services_wires_phase_orchestrator_without_running_phases(self):
        with patch.object(composition, "build_preflight_service") as build_preflight:
            with patch.object(composition, "build_platform_services") as build_platform:
                with patch.object(composition, "build_artifact_services") as build_artifacts:
                    with patch.object(composition, "build_deployment_services") as build_deployment:
                        build_preflight.return_value = _phase_bundle()
                        build_platform.return_value = _platform_phase_bundle()
                        build_artifacts.return_value = _artifact_phase_bundle()
                        build_deployment.return_value = _deployment_phase_bundle()

                        services = composition.build_setup_services(_accepted_live_consent())

        self.assertIsInstance(services.workflows.run, composition.SetupWorkflow)
        self.assertTrue(services.workflows.run.live_consent.accepted)
        self.assertEqual(
            (
                "preflight",
                "platform init",
                "platform reconcile",
                "deployment bootstrap",
                "artifacts prepare",
                "artifacts verify",
                "deployment apply",
                "deployment verify",
                "platform verify",
            ),
            tuple(phase.name for phase in services.workflows.run.phases),
        )
        build_preflight.assert_called_once_with(service_profile=ServiceStackProfile.SERVICE_ACCESS)
        build_platform.assert_called_once_with(service_profile=ServiceStackProfile.SERVICE_ACCESS)
        build_deployment.assert_called_once_with(service_profile=ServiceStackProfile.SERVICE_ACCESS)
        build_preflight.return_value.run.assert_not_called()
        build_platform.return_value.workflows.init.run.assert_not_called()
        build_artifacts.return_value.workflows.prepare.run.assert_not_called()
        build_deployment.return_value.workflows.apply.run.assert_not_called()

    def test_build_application_services_wires_preflight_through_platform_bundle(self):
        with patch.object(composition, "PortVmRepositoryYaml"):
            with patch.object(composition, "PortNetplanRepositoryYaml"):
                services = composition.build_application_services()

        self.assertIsInstance(services.platform.preflight, PreflightService)
        self.assertIs(services.preflight, services.platform.preflight)
        self.assertIs(services.platform.workflows.verify.steps[0], services.platform.preflight)

    def test_build_application_services_does_not_run_constructed_services(self):
        with patch.object(composition.MultipassInitVms, "run", side_effect=AssertionError):
            with patch.object(composition.MultipassDockerInstall, "run", side_effect=AssertionError):
                with patch.object(
                    composition.MultipassDockerSwarmInit,
                    "run",
                    side_effect=AssertionError,
                ):
                    services = composition.build_application_services()

        self.assertIsInstance(services, composition.ApplicationServices)

    def test_composed_init_workflow_blocks_before_live_step_execution(self):
        evidence_repository = _RecordingEvidenceRepository()
        blocked_result = _blocked_contract_result("platform:init:multipass-vms")
        with patch.object(composition, "PortVmRepositoryYaml"):
            with patch.object(composition, "PortNetplanRepositoryYaml"):
                with patch.object(
                    composition,
                    "VerificationEvidenceLocalRepository",
                    return_value=evidence_repository,
                ):
                    with patch.object(
                        composition.CommandWorkflow,
                        "verify_config_contract",
                        return_value=blocked_result,
                    ):
                        with patch.object(
                            composition.MultipassInitVms,
                            "run",
                            side_effect=AssertionError("init step must not run"),
                        ):
                            services = composition.build_platform_services()
                            result = asyncio.run(services.workflows.init.run())

        self.assertEqual(PlatformWorkflowStatus.BLOCKED, result.status)
        self.assertFalse(result.executed)
        self.assertEqual(
            "platform:init:multipass-vms",
            result.verification_results[0].target_id,
        )
        self.assertEqual(
            "command_backed_verification_missing",
            result.verification_results[0].evidence["reason"],
        )
        self.assertEqual(tuple(result.verification_results), evidence_repository.list_all())

    def test_composed_reconcile_workflow_blocks_before_live_step_execution(self):
        evidence_repository = _RecordingEvidenceRepository()
        blocked_result = _blocked_contract_result("platform:reconcile:vm-ip-list")
        with patch.object(composition, "PortVmRepositoryYaml"):
            with patch.object(composition, "PortNetplanRepositoryYaml"):
                with patch.object(
                    composition,
                    "VerificationEvidenceLocalRepository",
                    return_value=evidence_repository,
                ):
                    with patch.object(
                        composition.CommandWorkflow,
                        "verify_config_contract",
                        return_value=blocked_result,
                    ):
                        with patch.object(
                            composition.VmIpList,
                            "run",
                            side_effect=AssertionError("reconcile step must not run"),
                        ):
                            services = composition.build_platform_services()
                            result = asyncio.run(services.workflows.reconcile.run())

        self.assertEqual(PlatformWorkflowStatus.BLOCKED, result.status)
        self.assertFalse(result.executed)
        self.assertEqual(
            "platform:reconcile:vm-ip-list",
            result.verification_results[0].target_id,
        )
        self.assertEqual(
            "command_backed_verification_missing",
            result.verification_results[0].evidence["reason"],
        )
        self.assertEqual(tuple(result.verification_results), evidence_repository.list_all())


def _blocked_contract_result(target_id: str) -> VerificationResult:
    return VerificationResult(
        target_id=target_id,
        status=VerificationStatus.BLOCKED,
        message="Command-backed verification is not configured.",
        evidence={
            "phase": "pre_apply",
            "reason": "command_backed_verification_missing",
        },
    )


def _accepted_live_consent() -> LiveConsent:
    return LiveConsent(
        live_flag=True,
        environment_value=LIVE_CONSENT_ENVIRONMENT_VALUE,
        typed_phrase=LIVE_CONSENT_PHRASE,
    )


class _RecordingEvidenceRepository:
    def __init__(self) -> None:
        self.results: list[VerificationResult] = []

    def append(self, result: VerificationResult) -> None:
        self.results.append(result)

    def list_all(self) -> tuple[VerificationResult, ...]:
        return tuple(self.results)


def _phase_bundle():
    from unittest.mock import AsyncMock

    return type("PhaseBundle", (), {"run": AsyncMock()})()


def _workflow_bundle(*names: str):
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    return SimpleNamespace(
        workflows=SimpleNamespace(
            **{name: SimpleNamespace(run=AsyncMock()) for name in names}
        )
    )


def _platform_phase_bundle():
    return _workflow_bundle("init", "reconcile", "verify")


def _artifact_phase_bundle():
    return _workflow_bundle("prepare", "verify")


def _deployment_phase_bundle():
    return _workflow_bundle("bootstrap", "apply", "verify")
