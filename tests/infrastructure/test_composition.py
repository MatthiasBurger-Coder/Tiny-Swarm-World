import asyncio
import os
import unittest
from dataclasses import fields
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import cast
from unittest.mock import patch
from tests.support.async_helpers import async_checkpoint
from tests.support.sonar_safe_literals import ipv4_address, sample_text

from tiny_swarm_world.application.services.deployment.ensure_service_stack import EnsureServiceStack
from tiny_swarm_world.application.ports.ui.port_ui import (
    AGGREGATE_INSTANCE,
    STATUS_ERROR,
    STATUS_SUCCESS,
    PortUI,
)
from tiny_swarm_world.application.services.platform import PlatformWorkflowStatus
from tiny_swarm_world.application.services.platform.preflight_service import PreflightService
from tiny_swarm_world.application.services.setup import (
    SetupWorkflowKind,
    SetupWorkflowResult,
    SetupWorkflowStatus,
)
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus
from tiny_swarm_world.domain.deployment import ServiceStackProfile
from tiny_swarm_world.domain.preflight import (
    LIVE_CONSENT_ENVIRONMENT_VALUE,
    LIVE_CONSENT_PHRASE,
    LiveConsent,
)
from tiny_swarm_world.infrastructure import composition
from tiny_swarm_world.infrastructure.adapters.preflight import HostPreflightProbe


def _required_infisical_bootstrap_env() -> dict[str, str]:
    return {
        "TSW_INFISICAL_LOGIN_EMAIL": "admin@example.com",
        "TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD": sample_text("master", "-value"),
        "TSW_INFISICAL_ENCRYPTION_KEY": "0123456789abcdef0123456789abcdef",
        "TSW_INFISICAL_AUTH_SECRET": sample_text("auth", "-secret"),
        "TSW_INFISICAL_POSTGRES_PASSWORD": sample_text("pg", "-secret"),
        "TSW_INFISICAL_REDIS_PASSWORD": sample_text("redis", "-secret"),
        "TSW_PORTAINER_ADMIN_PASSWORD": sample_text("portainer", "-value"),
        "TSW_JENKINS_ADMIN_PASSWORD": sample_text("jenkins", "-value"),
        "TSW_PULSAR_TOKEN_SECRET_KEY": "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=",
        "TSW_PULSAR_ADMIN_TOKEN": "header.payload.signature",
        "TSW_PULSAR_MANAGER_ADMIN_PASSWORD": sample_text("pulsar-manager", "-value"),
        "TSW_POSTGRES_PASSWORD": sample_text("postgres", "-value"),
        "TSW_SONARQUBE_POSTGRES_PASSWORD": sample_text("sonar-pg", "-value"),
    }


class TestComposition(unittest.TestCase):
    def setUp(self):
        self._infisical_env_patcher = patch.dict(
            os.environ,
            _required_infisical_bootstrap_env(),
        )
        self._infisical_env_patcher.start()
        self.addCleanup(self._infisical_env_patcher.stop)

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
                "build_artifact_services_for_provider",
                return_value=artifacts,
            ) as build_artifact_services:
                with patch.object(
                    composition,
                    "build_deployment_services_for_provider",
                    return_value=deployment,
                ) as build_deployment_services:
                    services = composition.build_application_services()

        self.assertIs(services.platform, platform)
        self.assertIs(services.artifacts, artifacts)
        self.assertIs(services.deployment, deployment)
        build_platform_services.assert_called_once_with(
            service_profile=ServiceStackProfile.SERVICE_ACCESS,
            live_consent=None,
        )
        build_artifact_services.assert_called_once_with(node_provider_request=None)
        build_deployment_services.assert_called_once_with(
            service_profile=ServiceStackProfile.SERVICE_ACCESS,
            node_provider_request=None,
        )

    def test_platform_services_contains_preflight_service(self):
        field_names = {field.name for field in fields(composition.PlatformServices)}

        self.assertIn("preflight", field_names)
        self.assertIn("lxc_node_provider", field_names)
        self.assertIn("node_provider_selection", field_names)
        self.assertIn("lxc_docker_install", field_names)
        self.assertIn("lxc_proxy_drift_repair", field_names)
        self.assertIn("lxc_service_exposure", field_names)
        self.assertIn("lxc_swarm_bootstrap", field_names)

    def test_platform_services_contains_workflow_bundle(self):
        platform_field_names = {field.name for field in fields(composition.PlatformServices)}
        workflow_field_names = {field.name for field in fields(composition.PlatformWorkflows)}

        self.assertIn("workflows", platform_field_names)
        self.assertEqual(
            {
                "init",
                "reconcile",
                "expose",
                "repair_lxc_proxy_drift",
                "reset",
                "destroy",
                "verify",
            },
            workflow_field_names,
        )

    def test_build_configuration_validation_service_uses_env_file_and_process_environment(self):
        with TemporaryDirectory() as temporary_directory:
            env_file = Path(temporary_directory) / "operator.env"
            env_file.write_text(
                "\n".join(
                    (
                        "TSW_PORTAINER_STACK_REQUEST_TIMEOUT_SECONDS=0",
                        "TSW_NEXUS_ADMIN_PASSWORD='file-secret'",
                        "TSW_SONARQUBE_ADMIN_PASSWORD='file-secret'",
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            environment = {
                **_required_infisical_bootstrap_env(),
                "TSW_NEXUS_ADMIN_PASSWORD": sample_text("nexus", "-value"),
                "TSW_SONARQUBE_ADMIN_PASSWORD": sample_text("sonar", "-value"),
                "TSW_PORTAINER_STACK_REQUEST_TIMEOUT_SECONDS": "30",
            }

            with patch.dict(os.environ, environment, clear=True):
                result = composition.build_configuration_validation_service(env_file).validate()

        self.assertTrue(result.passed)
        self.assertNotIn("file-secret", repr(result.to_dict()))
        self.assertNotIn(environment["TSW_NEXUS_ADMIN_PASSWORD"], repr(result.to_dict()))

    def test_build_configuration_validation_service_uses_install_env_file_override(self):
        with TemporaryDirectory() as temporary_directory:
            env_file = Path(temporary_directory) / "operator.env"
            env_file.write_text(
                "\n".join(
                    f"{key}='{value}'"
                    for key, value in {
                        **_required_infisical_bootstrap_env(),
                        "TSW_NEXUS_ADMIN_PASSWORD": sample_text("nexus", "-value"),
                        "TSW_SONARQUBE_ADMIN_PASSWORD": sample_text("sonar", "-value"),
                    }.items()
                )
                + "\n",
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"TSW_INSTALL_ENV_FILE": str(env_file)}, clear=True):
                result = composition.build_configuration_validation_service().validate()

        self.assertTrue(result.passed)

    def test_wsl_lxc_user_namespace_gate_allows_missing_kernel_flag(self):
        with patch.object(
            composition,
            "_linux_text_file_equals",
            side_effect=AssertionError("missing WSL kernel flag must not be read"),
        ):
            self.assertTrue(
                composition._wsl_unprivileged_userns_clone_available(
                    _ExistingPath(exists=False)
                )
            )

    def test_wsl_lxc_user_namespace_gate_honors_present_kernel_flag(self):
        with patch.object(
            composition,
            "_linux_text_file_equals",
            return_value=True,
        ) as text_file_equals:
            self.assertTrue(
                composition._wsl_unprivileged_userns_clone_available(
                    _ExistingPath(exists=True)
                )
            )

        text_file_equals.assert_called_once()

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
        with patch.object(
            composition,
            "NodeProviderConfigYamlRepository",
        ) as node_config_repository_factory:
            with patch.object(
                composition,
                "AsyncLxcNodeCommandRunner",
            ) as lxc_runner_factory:
                with patch.object(
                    composition,
                    "_wsl_lxc_lifecycle_capability_available",
                    return_value=True,
                ) as wsl_capability_probe:
                    services = composition.build_platform_services()

        node_config_repository_factory.assert_called_once_with()
        lxc_runner_factory.assert_called_once_with()
        self.assertIsInstance(services.preflight, PreflightService)
        self.assertIsInstance(services.preflight.host_probe, HostPreflightProbe)
        self.assertIsInstance(services.lxc_node_provider, composition.LxcNodeProvider)
        self.assertIs(
            node_config_repository_factory.return_value,
            services.lxc_node_provider.config_repository,
        )
        self.assertIs(
            lxc_runner_factory.return_value,
            services.lxc_node_provider.runner,
        )
        self.assertIsInstance(
            services.node_provider_selection,
            composition.NodeProviderSelectionService,
        )
        self.assertIs(
            services.lxc_node_provider,
            services.node_provider_selection.node_lifecycle,
        )
        self.assertIs(
            services.lxc_node_provider,
            services.node_provider_selection.managed_node_teardown,
        )
        self.assertIs(
            wsl_capability_probe,
            services.node_provider_selection.readiness_probe.wsl_lxc_capability_available,
        )
        self.assertFalse(services.lxc_node_provider.allow_live_mutation)

    def test_build_platform_services_wires_workflow_objects(self):
        evidence_repository = _RecordingEvidenceRepository()
        with patch.object(
            composition,
            "VerificationEvidenceLocalRepository",
            return_value=evidence_repository,
        ):
            services = composition.build_platform_services(
                trace_correlation_id="trace-test"
            )

        self.assertIsInstance(services.workflows.init, composition.PlatformInitWorkflow)
        self.assertIsInstance(services.workflows.reconcile, composition.PlatformReconcileWorkflow)
        self.assertIsInstance(services.workflows.expose, composition.PlatformExposeWorkflow)
        self.assertIsInstance(
            services.workflows.repair_lxc_proxy_drift,
            composition.PlatformRepairLxcProxyDriftWorkflow,
        )
        self.assertIsInstance(services.workflows.reset, composition.PlatformResetWorkflow)
        self.assertIsInstance(services.workflows.destroy, composition.PlatformDestroyWorkflow)
        self.assertIsInstance(services.workflows.verify, composition.PlatformVerifyWorkflow)
        self.assertIs(
            evidence_repository,
            services.workflows.init.verification_evidence_repository,
        )
        self.assertIsNone(services.workflows.init.pre_apply_guard)
        self.assertIs(
            evidence_repository,
            services.workflows.reconcile.verification_evidence_repository,
        )
        self.assertIs(
            evidence_repository,
            services.workflows.expose.verification_evidence_repository,
        )
        self.assertIs(
            evidence_repository,
            services.workflows.repair_lxc_proxy_drift.verification_evidence_repository,
        )
        self.assertIsInstance(
            services.workflows.init.progress,
            composition.CompositeWorkflowProgress,
        )
        self.assertIsInstance(
            services.workflows.init.method_trace,
            composition.CompositeMethodTrace,
        )
        self.assertIs(
            services.workflows.init.progress,
            services.workflows.reconcile.progress,
        )
        self.assertIs(
            services.workflows.init.progress,
            services.workflows.expose.progress,
        )
        self.assertIs(
            services.workflows.init.progress,
            services.workflows.repair_lxc_proxy_drift.progress,
        )
        self.assertIs(
            services.workflows.init.method_trace,
            services.workflows.reconcile.method_trace,
        )
        self.assertIs(
            services.workflows.init.method_trace,
            services.workflows.expose.method_trace,
        )
        self.assertIs(
            services.workflows.init.method_trace,
            services.workflows.repair_lxc_proxy_drift.method_trace,
        )
        self.assertEqual("trace-test", services.workflows.init.trace_correlation_id)
        self.assertEqual(
            "trace-test",
            services.workflows.reconcile.trace_correlation_id,
        )
        self.assertEqual("trace-test", services.workflows.expose.trace_correlation_id)
        self.assertEqual(
            "trace-test",
            services.workflows.repair_lxc_proxy_drift.trace_correlation_id,
        )
        self.assertEqual("trace-test", services.workflows.reset.trace_correlation_id)
        self.assertEqual("trace-test", services.workflows.destroy.trace_correlation_id)
        self.assertEqual("trace-test", services.workflows.verify.trace_correlation_id)

    def test_build_platform_services_wires_read_only_platform_verify_steps(self):
        services = composition.build_platform_services()

        verify_preflight = services.workflows.verify.steps[0]
        verify_steps = services.workflows.verify.steps

        self.assertIsInstance(verify_preflight, PreflightService)
        self.assertIsNot(services.preflight, verify_preflight)
        self.assertGreater(len(services.preflight.configuration.required_ports), 0)
        self.assertEqual((), verify_preflight.configuration.required_ports)
        self.assertEqual(8, len(verify_steps))
        self.assertTrue(
            all(
                isinstance(step, composition.NodeProviderVerifyNodeStep)
                for step in verify_steps[1:4]
            )
        )
        self.assertIsInstance(verify_steps[4], composition.LxcDockerVerifyStep)
        self.assertIsInstance(verify_steps[5], composition.LxcSwarmVerifyStep)
        self.assertIsInstance(verify_steps[6], composition.LxcServiceExposureVerifyStep)
        self.assertEqual(
            composition.PortainerEndpointVerifyStep.verification_target_id,
            verify_steps[7].verification_target_id,
        )

    def test_build_platform_services_wires_reset_destroy_managed_node_steps(self):
        services = composition.build_platform_services()

        self.assertEqual(1, len(services.workflows.reset.steps))
        self.assertEqual(1, len(services.workflows.destroy.steps))
        reset_step = services.workflows.reset.steps[0]
        destroy_step = services.workflows.destroy.steps[0]

        self.assertIsInstance(reset_step, composition.NodeProviderResetManagedNodesStep)
        self.assertIsInstance(destroy_step, composition.NodeProviderDestroyManagedNodesStep)
        self.assertEqual(composition.DEFAULT_LXC_PLATFORM_NODES, reset_step.nodes)
        self.assertEqual(composition.DEFAULT_LXC_PLATFORM_NODES, destroy_step.nodes)
        self.assertIs(services.node_provider_selection, reset_step.provider_selection)
        self.assertIs(services.node_provider_selection, destroy_step.provider_selection)

    def test_build_platform_services_does_not_run_lxc_commands_during_wiring(self):
        async def fail_if_called(*_args, **_kwargs):
            raise AssertionError("composition must not run LXC commands during wiring")

        with patch.object(composition, "AsyncLxcNodeCommandRunner") as runner_factory:
            runner_factory.return_value.run.side_effect = fail_if_called

            services = composition.build_platform_services()

        runner_factory.assert_called_once_with()
        self.assertIsInstance(services.lxc_node_provider, composition.LxcNodeProvider)

    def test_build_platform_services_wires_workflow_types_without_evidence_patch(self):
        services = composition.build_platform_services()

        self.assertIsInstance(services.workflows.init, composition.PlatformInitWorkflow)
        self.assertIsInstance(services.workflows.reconcile, composition.PlatformReconcileWorkflow)
        self.assertIsInstance(services.workflows.expose, composition.PlatformExposeWorkflow)
        self.assertIsInstance(
            services.workflows.repair_lxc_proxy_drift,
            composition.PlatformRepairLxcProxyDriftWorkflow,
        )
        self.assertIsInstance(services.workflows.reset, composition.PlatformResetWorkflow)
        self.assertIsInstance(services.workflows.destroy, composition.PlatformDestroyWorkflow)
        self.assertIsInstance(services.workflows.verify, composition.PlatformVerifyWorkflow)

    def test_build_platform_services_adds_terminal_sinks_when_ui_is_supplied(self):
        ui = _RecordingUI()

        services = composition.build_platform_services(ui=ui)

        progress_sink = services.workflows.init.progress
        method_trace_sink = services.workflows.init.method_trace
        self.assertIsInstance(progress_sink, composition.CompositeWorkflowProgress)
        self.assertIsInstance(method_trace_sink, composition.CompositeMethodTrace)

        progress_sinks = cast(composition.CompositeWorkflowProgress, progress_sink).sinks
        method_trace_sinks = cast(composition.CompositeMethodTrace, method_trace_sink).sinks

        self.assertTrue(
            any(
                isinstance(sink, composition.TerminalWorkflowProgress)
                and sink.ui is ui
                for sink in progress_sinks
            )
        )
        self.assertTrue(
            any(
                isinstance(sink, composition.TerminalMethodTrace)
                and sink.ui is ui
                for sink in method_trace_sinks
            )
        )

    def test_build_setup_ui_uses_ui_factory_without_starting_thread(self):
        ui = _RecordingUI()

        with patch.object(composition, "FactoryUI") as factory:
            factory.return_value.get_ui.return_value = ui

            result = composition.build_setup_ui(test_mode=True)

        self.assertIs(ui, result)
        factory.return_value.get_ui.assert_called_once_with(
            instances=(),
            test_mode=True,
        )
        self.assertIsNone(ui.ui_thread)

    def test_run_setup_with_terminal_status_runs_composed_lifecycle_after_consent(self):
        calls: list[str] = []
        live_consent = _accepted_live_consent()
        recording_ui = _LifecycleRecordingUI(calls)
        result = _setup_result(SetupWorkflowStatus.COMPLETED)

        def build_setup_ui():
            calls.append("ui built")
            return recording_ui

        def build_setup_services(
            consent,
            *,
            service_profile,
            node_provider_request,
            ui,
            configuration_validation,
        ):
            calls.append("services built")
            self.assertIs(live_consent, consent)
            self.assertEqual(ServiceStackProfile.SERVICE_ACCESS, service_profile)
            self.assertEqual(composition.NodeProviderSelectionRequest(), node_provider_request)
            self.assertIs(recording_ui, ui)
            self.assertIsNotNone(configuration_validation)
            return _setup_lifecycle_bundle(calls, result)

        with patch.object(composition, "build_setup_ui", side_effect=build_setup_ui):
            with patch.object(
                composition,
                "build_setup_services",
                side_effect=build_setup_services,
            ):
                actual = asyncio.run(
                    composition.run_setup_with_terminal_status(
                        live_consent,
                        "run",
                        service_profile=ServiceStackProfile.SERVICE_ACCESS,
                        node_provider_request=composition.NodeProviderSelectionRequest(),
                    )
                )

        self.assertIs(result, actual)
        self.assertEqual(
            [
                "ui built",
                "ui started",
                "services built",
                "workflow run",
                "ui update completed",
                "ui awaited",
            ],
            calls,
        )
        self.assertEqual(
            SetupWorkflowStatus.COMPLETED.value,
            recording_ui.aggregate_status["result"],
        )

    def test_run_setup_with_terminal_status_rejects_missing_consent_before_ui(self):
        live_consent = LiveConsent(live_flag=False)

        with patch.object(composition, "build_setup_ui") as build_setup_ui:
            with self.assertRaises(ValueError):
                asyncio.run(
                    composition.run_setup_with_terminal_status(
                        live_consent,
                        "run",
                    )
                )

        build_setup_ui.assert_not_called()

    def test_run_setup_with_terminal_status_marks_ui_error_when_workflow_raises(self):
        calls: list[str] = []
        ui = _LifecycleRecordingUI(calls)

        with patch.object(composition, "build_setup_ui", return_value=ui):
            with patch.object(
                composition,
                "build_setup_services",
                return_value=_setup_lifecycle_bundle(
                    calls,
                    RuntimeError("boom"),
                ),
            ):
                with self.assertRaises(RuntimeError):
                    asyncio.run(
                        composition.run_setup_with_terminal_status(
                            _accepted_live_consent(),
                            "run",
                        )
                    )

        self.assertIn(
            (AGGREGATE_INSTANCE, "setup run", "exception", STATUS_ERROR),
            ui.updates,
        )
        self.assertEqual(STATUS_ERROR, ui.aggregate_status["result"])
        self.assertIn("ui awaited", calls)

    def test_run_setup_with_terminal_status_preserves_aggregate_failure(self):
        calls: list[str] = []
        ui = _LifecycleRecordingUI(calls)
        result = _setup_result(SetupWorkflowStatus.COMPLETED)

        with patch.object(composition, "build_setup_ui", return_value=ui):
            with patch.object(
                composition,
                "build_setup_services",
                return_value=_setup_lifecycle_bundle(
                    calls,
                    result,
                    ui=ui,
                    status_updates=(
                        SetupWorkflowStatus.BLOCKED.value,
                        STATUS_SUCCESS,
                    ),
                ),
            ):
                actual = asyncio.run(
                    composition.run_setup_with_terminal_status(
                        _accepted_live_consent(),
                        "run",
                    )
                )

        self.assertIs(result, actual)
        self.assertEqual(STATUS_ERROR, ui.aggregate_status["result"])

    def test_build_artifact_services_wires_artifact_contracts_without_running_clients(self):
        services = composition.build_lxc_artifact_services(
            backend=composition.ManagedLxcBackend.INCUS,
        )

        self.assertIsInstance(services.workflows.prepare, composition.ArtifactPrepareWorkflow)
        self.assertIsInstance(services.workflows.verify, composition.ArtifactVerifyWorkflow)
        self.assertEqual(
            (
                "artifacts:nexus-ready",
                "artifacts:nexus-admin-access",
                "artifacts:nexus-docker-hosted-repository",
                "artifacts:nexus-docker-hub-proxy-repository",
                "artifacts:nexus-maven-proxy-repository",
                "artifacts:jenkins-image",
                "artifacts:service-access-dashboard-image",
                "artifacts:service-access-nginx-image",
                "artifacts:infisical-image",
                "artifacts:infisical-postgres-image",
                "artifacts:infisical-redis-image",
            ),
            tuple(step.verification_target_id for step in services.workflows.prepare.steps),
        )

    def test_build_artifact_services_uses_infisical_image_overrides(self):
        with patch.dict(
            "os.environ",
            {
                **_required_infisical_bootstrap_env(),
                "TSW_NEXUS_ADMIN_PASSWORD": sample_text("nexus", "-value"),
                "TSW_INFISICAL_IMAGE": "registry.local:5000/infisical:cached",
                "TSW_INFISICAL_POSTGRES_IMAGE": "registry.local:5000/postgres:14-alpine",
                "TSW_INFISICAL_REDIS_IMAGE": "registry.local:5000/redis:7-alpine",
            },
            clear=True,
        ):
            services = composition.build_lxc_artifact_services(
                backend=composition.ManagedLxcBackend.INCUS,
            )

        image_refs = {
            step.contract.build_context: step.contract.image_ref
            for step in services.workflows.prepare.steps
            if hasattr(step, "contract")
        }

        self.assertEqual("registry.local:5000/infisical:cached", image_refs["infisical"])
        self.assertEqual(
            "registry.local:5000/postgres:14-alpine",
            image_refs["infisical-postgres"],
        )
        self.assertEqual("registry.local:5000/redis:7-alpine", image_refs["infisical-redis"])

    def test_build_artifact_services_keeps_docker_hub_image_refs_for_mirror_defaults(self):
        with patch.dict(
            "os.environ",
            {
                **_required_infisical_bootstrap_env(),
                "TSW_NEXUS_ADMIN_PASSWORD": sample_text("nexus", "-value"),
            },
            clear=True,
        ):
            services = composition.build_lxc_artifact_services(
                backend=composition.ManagedLxcBackend.INCUS,
            )

        image_refs = {
            step.contract.build_context: step.contract.image_ref
            for step in services.workflows.prepare.steps
            if hasattr(step, "contract")
        }

        self.assertEqual("infisical/infisical:latest", image_refs["infisical"])
        self.assertEqual("postgres:14-alpine", image_refs["infisical-postgres"])
        self.assertEqual("redis:7-alpine", image_refs["infisical-redis"])

    def test_build_artifact_services_does_not_call_live_clients_during_construction(self):
        services = composition.build_lxc_artifact_services(
            backend=composition.ManagedLxcBackend.INCUS,
        )

        self.assertEqual(11, len(services.workflows.prepare.steps))
        self.assertEqual(11, len(services.workflows.verify.checks))

    def test_build_deployment_services_wires_stack_contracts_without_running_runtime(self):
        with patch.dict("os.environ", _required_infisical_bootstrap_env(), clear=True):
            with patch.object(composition, "ComposeFileRepositoryYaml"):
                services = composition.build_lxc_deployment_services(
                    backend=composition.ManagedLxcBackend.INCUS,
                )

        self.assertIsInstance(services.workflows.bootstrap, composition.DeploymentApplyWorkflow)
        self.assertIsInstance(services.workflows.apply, composition.DeploymentApplyWorkflow)
        self.assertIsInstance(services.workflows.verify, composition.DeploymentVerifyWorkflow)
        self.assertEqual(
            (
                "deployment:portainer-stack",
                "deployment:portainer-admin-access",
                "deployment:portainer-local-endpoint",
                "deployment:nexus-stack",
            ),
            tuple(step.verification_target_id for step in services.workflows.bootstrap.steps),
        )
        self.assertEqual(
            (
                "deployment:jenkins-stack",
                "deployment:pulsar-stack",
                "deployment:sonarqube-stack",
                "deployment:sonarqube-admin-access",
                "deployment:swagger-stack",
                "deployment:infisical-stack",
                "deployment:service-access-stack",
                "deployment:infisical-bootstrap-service-readiness",
                "deployment:infisical-bootstrap-access-readiness",
                "deployment:managed-config-inventory",
                "deployment:infisical-silent-install",
                "deployment:infisical-sync",
                "deployment:managed-config-consumption",
                "deployment:managed-config-evidence",
            ),
            tuple(step.verification_target_id for step in services.workflows.apply.steps),
        )
        self.assertTrue(
            all(
                step.deployment_gateway is services.workflows.bootstrap.steps[2].portainer_client
                for step in services.workflows.apply.steps
                if step.verification_target_id.endswith("-stack")
            )
        )
        jenkins_step = next(
            step
            for step in services.workflows.apply.steps
            if step.service_stack.stack_name == "jenkins"
        )
        nexus_step = next(
            step
            for step in services.workflows.bootstrap.steps
            if hasattr(step, "service_stack") and step.service_stack.stack_name == "nexus"
        )
        self.assertEqual(
            {"TSW_NEXUS_IMAGE": "sonatype/nexus3:3.75.1"},
            nexus_step.stack_environment,
        )
        self.assertEqual(
            {
                "TSW_JENKINS_ADMIN_PASSWORD": sample_text("jenkins", "-value"),
                "TSW_JENKINS_IMAGE": "127.0.0.1:5000/jenkins:latest",
            },
            jenkins_step.stack_environment,
        )
        self.assertEqual(
            (
                "deployment:portainer-service-readiness",
                "deployment:nexus-service-readiness",
                "deployment:jenkins-service-readiness",
                "deployment:pulsar-service-readiness",
                "deployment:sonarqube-service-readiness",
                "deployment:swagger-service-readiness",
                "deployment:infisical-service-readiness",
                "deployment:service-access-service-readiness",
            ),
            tuple(check.verification_target_id for check in services.workflows.verify.checks),
        )
        self.assertEqual((), services.workflows.apply.pre_apply_checks)
        self.assertEqual(
            ("deployment:swagger-stack-assets",),
            tuple(step.deployment_target_id for step in services.workflows.apply.pre_apply_steps),
        )

    def test_build_deployment_services_does_not_call_runtime_during_construction(self):
        with patch.object(composition, "ComposeFileRepositoryYaml") as compose_repository:
            services = composition.build_lxc_deployment_services(
                backend=composition.ManagedLxcBackend.INCUS,
            )

        compose_repository.assert_called_once_with()
        self.assertEqual(4, len(services.workflows.bootstrap.steps))
        self.assertEqual(14, len(services.workflows.apply.steps))
        self.assertEqual(8, len(services.workflows.verify.checks))

    def test_default_provider_artifact_services_use_lxc_clients_when_backend_is_available(self):
        with patch.object(composition.shutil, "which", return_value="/usr/bin/lxc"):
            services = composition.build_artifact_services_for_provider()

        self.assertIsInstance(services.workflows.prepare, composition.ArtifactPrepareWorkflow)
        self.assertEqual(11, len(services.workflows.prepare.steps))

    def test_default_provider_deployment_services_use_lxc_clients_when_backend_is_available(self):
        with patch.object(composition.shutil, "which", return_value="/usr/bin/lxc"):
            services = composition.build_deployment_services_for_provider()

        self.assertIsInstance(services.workflows.bootstrap, composition.DeploymentApplyWorkflow)
        self.assertEqual(
            (
                "deployment:portainer-stack",
                "deployment:portainer-admin-access",
                "deployment:portainer-local-endpoint",
                "deployment:nexus-stack",
            ),
            tuple(step.verification_target_id for step in services.workflows.bootstrap.steps),
        )

    def test_default_provider_deployment_services_fail_closed_without_lxc_backend(self):
        with patch.object(composition.shutil, "which", return_value=None):
            services = composition.build_deployment_services_for_provider()

        result = asyncio.run(services.workflows.apply.run())

        self.assertEqual("blocked", result.status.value)

    def test_build_deployment_services_uses_named_portainer_api_default(self):
        services = composition.build_lxc_deployment_services(
            backend=composition.ManagedLxcBackend.INCUS,
        )
        self.assertIsInstance(services.workflows.apply, composition.DeploymentApplyWorkflow)

    def test_build_deployment_services_can_select_service_access_profile(self):
        with patch.object(composition, "ComposeFileRepositoryYaml"):
            services = composition.build_lxc_deployment_services(
                backend=composition.ManagedLxcBackend.INCUS,
                service_profile=ServiceStackProfile.SERVICE_ACCESS,
            )

        self.assertEqual(
            (
                "deployment:portainer-stack",
                "deployment:portainer-admin-access",
                "deployment:portainer-local-endpoint",
                "deployment:nexus-stack",
            ),
            tuple(step.verification_target_id for step in services.workflows.bootstrap.steps),
        )
        self.assertEqual(
            (
                "deployment:jenkins-stack",
                "deployment:pulsar-stack",
                "deployment:sonarqube-stack",
                "deployment:sonarqube-admin-access",
                "deployment:swagger-stack",
                "deployment:infisical-stack",
                "deployment:service-access-stack",
                "deployment:infisical-bootstrap-service-readiness",
                "deployment:infisical-bootstrap-access-readiness",
                "deployment:managed-config-inventory",
                "deployment:infisical-silent-install",
                "deployment:infisical-sync",
                "deployment:managed-config-consumption",
                "deployment:managed-config-evidence",
            ),
            tuple(step.verification_target_id for step in services.workflows.apply.steps),
        )
        self.assertTrue(
            all(
                isinstance(step, EnsureServiceStack)
                for step in services.workflows.apply.steps
                if step.verification_target_id.endswith("-stack")
            )
        )
        self.assertEqual(
            (
                "deployment:portainer-service-readiness",
                "deployment:nexus-service-readiness",
                "deployment:jenkins-service-readiness",
                "deployment:pulsar-service-readiness",
                "deployment:sonarqube-service-readiness",
                "deployment:swagger-service-readiness",
                "deployment:infisical-service-readiness",
                "deployment:service-access-service-readiness",
            ),
            tuple(check.verification_target_id for check in services.workflows.verify.checks),
        )

    def test_build_deployment_services_wires_service_access_infisical_environment(self):
        stack_env = {
            **_required_infisical_bootstrap_env(),
            "TSW_INFISICAL_ENCRYPTION_KEY": "0123456789abcdef0123456789abcdef",
            "TSW_INFISICAL_AUTH_SECRET": sample_text("auth", "-secret"),
            "TSW_INFISICAL_POSTGRES_PASSWORD": sample_text("pg", "-secret"),
        }
        with patch.dict(
            "os.environ",
            stack_env,
            clear=True,
        ):
            with patch.object(composition, "ComposeFileRepositoryYaml"):
                services = composition.build_lxc_deployment_services(
                    backend=composition.ManagedLxcBackend.INCUS,
                )

        service_access_step = next(
            step
            for step in services.workflows.apply.steps
            if step.service_stack.stack_name == "service-access"
        )
        infisical_step = next(
            step
            for step in services.workflows.apply.steps
            if step.service_stack.stack_name == "infisical"
        )

        self.assertEqual(
            {
                "TSW_SERVICE_ACCESS_DASHBOARD_IMAGE": (
                    "127.0.0.1:5000/service-access-dashboard:latest"
                ),
                "TSW_SERVICE_ACCESS_NGINX_IMAGE": (
                    "127.0.0.1:5000/service-access-nginx:latest"
                ),
            },
            service_access_step.stack_environment,
        )
        self.assertEqual(
            {
                "TSW_INFISICAL_ENCRYPTION_KEY": "0123456789abcdef0123456789abcdef",
                "TSW_INFISICAL_AUTH_SECRET": sample_text("auth", "-secret"),
                "TSW_INFISICAL_LOGIN_EMAIL": "admin@example.com",
                "TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD": sample_text("master", "-value"),
                "TSW_INFISICAL_ADMIN_FIRST_NAME": "Tiny",
                "TSW_INFISICAL_ADMIN_LAST_NAME": "Admin",
                "TSW_INFISICAL_POSTGRES_PASSWORD": sample_text("pg", "-secret"),
                "TSW_INFISICAL_REDIS_PASSWORD": sample_text("redis", "-secret"),
            },
            infisical_step.stack_environment,
        )
        self.assertEqual((), services.workflows.apply.pre_apply_checks)
        self.assertEqual(
            ("deployment:swagger-stack-assets",),
            tuple(step.deployment_target_id for step in services.workflows.apply.pre_apply_steps),
        )

    def test_build_deployment_services_uses_operator_swarm_registry_endpoint_for_local_images(self):
        with patch.dict(
            "os.environ",
            {
                **_required_infisical_bootstrap_env(),
                "TSW_SWARM_REGISTRY_ENDPOINT": "registry.local:5000",
            },
            clear=True,
        ):
            with patch.object(composition, "ComposeFileRepositoryYaml"):
                services = composition.build_lxc_deployment_services(
                    backend=composition.ManagedLxcBackend.INCUS,
                )

        environments = {
            step.service_stack.stack_name: step.stack_environment
            for step in services.workflows.apply.steps
            if hasattr(step, "service_stack")
        }

        self.assertEqual(
            "registry.local:5000/jenkins:latest",
            environments["jenkins"]["TSW_JENKINS_IMAGE"],
        )
        self.assertEqual(
            "registry.local:5000/service-access-dashboard:latest",
            environments["service-access"]["TSW_SERVICE_ACCESS_DASHBOARD_IMAGE"],
        )
        self.assertEqual(
            "registry.local:5000/service-access-nginx:latest",
            environments["service-access"]["TSW_SERVICE_ACCESS_NGINX_IMAGE"],
        )

    def test_build_deployment_services_uses_operator_nexus_image_override(self):
        with patch.dict(
            "os.environ",
            {
                **_required_infisical_bootstrap_env(),
                "TSW_NEXUS_IMAGE": "registry.local:5000/sonatype/nexus3:3.75.1",
            },
            clear=True,
        ):
            with patch.object(composition, "ComposeFileRepositoryYaml"):
                services = composition.build_lxc_deployment_services(
                    backend=composition.ManagedLxcBackend.INCUS,
                )

        nexus_step = next(
            step
            for step in services.workflows.bootstrap.steps
            if hasattr(step, "service_stack") and step.service_stack.stack_name == "nexus"
        )

        self.assertEqual(
            "registry.local:5000/sonatype/nexus3:3.75.1",
            nexus_step.stack_environment["TSW_NEXUS_IMAGE"],
        )

    def test_build_artifact_services_uses_operator_environment_credentials(self):
        operator_value = sample_text("operator", "-supplied")
        with patch.dict(
            "os.environ",
            {
                **_required_infisical_bootstrap_env(),
                "TSW_NEXUS_ADMIN_PASSWORD": operator_value,
            },
            clear=True,
        ):
            services = composition.build_lxc_artifact_services(
                backend=composition.ManagedLxcBackend.INCUS,
            )

        image_publisher = services.workflows.prepare.steps[-1].image_publisher
        self.assertEqual(
            operator_value,
            image_publisher.registry_password,
        )

    def test_build_deployment_services_uses_operator_portainer_credential(self):
        operator_value = sample_text("operator", "-portainer")
        with patch.dict(
            "os.environ",
            {
                **_required_infisical_bootstrap_env(),
                "TSW_PORTAINER_ADMIN_PASSWORD": operator_value,
            },
            clear=True,
        ):
            with patch.object(composition, "ComposeFileRepositoryYaml"):
                services = composition.build_lxc_deployment_services(
                    backend=composition.ManagedLxcBackend.INCUS,
                )

        self.assertEqual(operator_value, services.workflows.bootstrap.steps[1].password)

    def test_build_deployment_services_uses_operator_portainer_stack_timeout(self):
        with patch.dict(
            "os.environ",
            {
                **_required_infisical_bootstrap_env(),
                "TSW_PORTAINER_ADMIN_PASSWORD": sample_text("portainer", "-value"),
                "TSW_PORTAINER_STACK_REQUEST_TIMEOUT_SECONDS": "181",
            },
            clear=True,
        ):
            with patch.object(composition, "ComposeFileRepositoryYaml"):
                services = composition.build_lxc_deployment_services(
                    backend=composition.ManagedLxcBackend.INCUS,
                )

        endpoint_step = services.workflows.bootstrap.steps[2]
        self.assertEqual(181, endpoint_step.portainer_client.stack_request_timeout_seconds)

    def test_build_deployment_services_can_seed_infisical_items_when_enabled(self):
        env = {
            **_required_infisical_bootstrap_env(),
            "TSW_SEED_INFISICAL_ITEMS": "1",
            "TSW_JENKINS_ADMIN_PASSWORD": sample_text("jenkins", "-value"),
            "TSW_NEXUS_ADMIN_PASSWORD": sample_text("nexus", "-value"),
            "TSW_PORTAINER_ADMIN_PASSWORD": sample_text("portainer", "-value"),
            "TSW_SONARQUBE_ADMIN_PASSWORD": sample_text("sonarqube", "-value"),
        }
        with patch.dict("os.environ", env, clear=True):
            with patch.object(composition, "ComposeFileRepositoryYaml"):
                services = composition.build_lxc_deployment_services(
                    backend=composition.ManagedLxcBackend.INCUS,
                    service_profile=ServiceStackProfile.SERVICE_ACCESS,
                )

        bootstrap_step = next(
            step
            for step in services.workflows.apply.steps
            if step.verification_target_id == "deployment:infisical-silent-install"
        )
        seed_step = next(
            step
            for step in services.workflows.apply.steps
            if step.verification_target_id == "deployment:infisical-items"
        )
        self.assertEqual("deployment:infisical-silent-install", bootstrap_step.verification_target_id)
        self.assertEqual(
            (
                "platform/jenkins",
                "platform/nexus",
                "platform/portainer",
                "platform/pulsar",
                "platform/pulsar-manager",
                "platform/sonarqube",
            ),
            tuple(item.item_name for item in seed_step.items),
        )

    def test_build_deployment_services_waits_for_infisical_before_silent_install(self):
        env = _required_infisical_bootstrap_env()
        with patch.dict("os.environ", env, clear=True):
            with patch.object(composition, "ComposeFileRepositoryYaml"):
                services = composition.build_lxc_deployment_services(
                    backend=composition.ManagedLxcBackend.INCUS,
                    service_profile=ServiceStackProfile.SERVICE_ACCESS,
                )

        target_ids = tuple(step.verification_target_id for step in services.workflows.apply.steps)
        service_guard_index = target_ids.index("deployment:infisical-bootstrap-service-readiness")
        access_guard_index = target_ids.index("deployment:infisical-bootstrap-access-readiness")
        bootstrap_index = target_ids.index("deployment:infisical-silent-install")

        self.assertLess(service_guard_index, bootstrap_index)
        self.assertLess(access_guard_index, bootstrap_index)
        self.assertIsInstance(
            services.workflows.apply.steps[service_guard_index],
            composition.EnsureSwarmServiceReadiness,
        )

    def test_build_deployment_services_uses_configurable_infisical_readiness_window(self):
        env = {
            **_required_infisical_bootstrap_env(),
            "TSW_INFISICAL_READINESS_ATTEMPTS": "240",
            "TSW_INFISICAL_READINESS_INTERVAL_SECONDS": "2.5",
        }
        with patch.dict("os.environ", env, clear=True):
            with patch.object(composition, "ComposeFileRepositoryYaml"):
                services = composition.build_lxc_deployment_services(
                    backend=composition.ManagedLxcBackend.INCUS,
                    service_profile=ServiceStackProfile.SERVICE_ACCESS,
                )

        bootstrap_step = next(
            step
            for step in services.workflows.apply.steps
            if step.verification_target_id == "deployment:infisical-silent-install"
        )
        self.assertEqual("deployment:infisical-silent-install", bootstrap_step.verification_target_id)
        self.assertEqual(240, bootstrap_step.bootstrap_client.readiness_attempts)
        self.assertEqual(2.5, bootstrap_step.bootstrap_client.readiness_interval_seconds)

    def test_build_deployment_services_uses_extended_infisical_readiness_default(self):
        env = _required_infisical_bootstrap_env()
        with patch.dict("os.environ", env, clear=True):
            with patch.object(composition, "ComposeFileRepositoryYaml"):
                services = composition.build_lxc_deployment_services(
                    backend=composition.ManagedLxcBackend.INCUS,
                    service_profile=ServiceStackProfile.SERVICE_ACCESS,
                )

        bootstrap_step = next(
            step
            for step in services.workflows.apply.steps
            if step.verification_target_id == "deployment:infisical-silent-install"
        )
        self.assertEqual("deployment:infisical-silent-install", bootstrap_step.verification_target_id)
        self.assertEqual(
            composition.DEFAULT_INFISICAL_READINESS_ATTEMPTS,
            bootstrap_step.bootstrap_client.readiness_attempts,
        )
        self.assertEqual(
            composition.DEFAULT_INFISICAL_READINESS_INTERVAL_SECONDS,
            bootstrap_step.bootstrap_client.readiness_interval_seconds,
        )

    def test_build_deployment_services_rejects_invalid_infisical_readiness_window(self):
        env = {
            **_required_infisical_bootstrap_env(),
            "TSW_INFISICAL_READINESS_ATTEMPTS": "0",
        }
        with patch.dict("os.environ", env, clear=True):
            with patch.object(composition, "ComposeFileRepositoryYaml"):
                with self.assertRaises(ValueError):
                    composition.build_lxc_deployment_services(
                        backend=composition.ManagedLxcBackend.INCUS,
                        service_profile=ServiceStackProfile.SERVICE_ACCESS,
                    )

    def test_build_deployment_services_rejects_enabled_infisical_seed_without_passwords(self):
        with patch.dict(
            "os.environ",
            {
                "TSW_SEED_INFISICAL_ITEMS": "1",
                "TSW_INFISICAL_LOGIN_EMAIL": "admin@example.com",
                "TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD": sample_text("master", "-value"),
        "TSW_INFISICAL_ENCRYPTION_KEY": "0123456789abcdef0123456789abcdef",
        "TSW_INFISICAL_AUTH_SECRET": sample_text("auth", "-secret"),
        "TSW_INFISICAL_POSTGRES_PASSWORD": sample_text("pg", "-secret"),
        "TSW_INFISICAL_REDIS_PASSWORD": sample_text("redis", "-secret"),
        "TSW_PORTAINER_ADMIN_PASSWORD": sample_text("portainer", "-value"),
        "TSW_JENKINS_ADMIN_PASSWORD": sample_text("jenkins", "-value"),
        "TSW_POSTGRES_PASSWORD": sample_text("postgres", "-value"),
        "TSW_SONARQUBE_POSTGRES_PASSWORD": sample_text("sonar-pg", "-value"),
            },
            clear=True,
        ):
            with patch.object(composition, "ComposeFileRepositoryYaml"):
                with self.assertRaisesRegex(
                    ValueError,
                    "Required operator secret is missing: TSW_NEXUS_ADMIN_PASSWORD",
                ):
                    composition.build_lxc_deployment_services(
                        backend=composition.ManagedLxcBackend.INCUS,
                        service_profile=ServiceStackProfile.SERVICE_ACCESS,
                    )

    def test_build_setup_services_wires_phase_orchestrator_without_running_phases(self):
        with patch.object(composition, "build_preflight_service") as build_preflight:
            with patch.object(composition, "build_platform_services") as build_platform:
                with patch.object(
                    composition,
                    "build_artifact_services_for_provider",
                ) as build_artifacts:
                    with patch.object(
                        composition,
                        "build_deployment_services_for_provider",
                    ) as build_deployment:
                        build_preflight.return_value = _phase_bundle()
                        build_platform.return_value = _platform_phase_bundle()
                        build_artifacts.return_value = _artifact_phase_bundle()
                        build_deployment.return_value = _deployment_phase_bundle()

                        with patch.object(
                            composition,
                            "_new_installation_trace_correlation_id",
                            return_value="trace-test",
                        ):
                            services = composition.build_setup_services(
                                _accepted_live_consent()
                            )

        self.assertIsInstance(services.workflows.run, composition.SetupWorkflow)
        self.assertTrue(services.workflows.run.live_consent.accepted)
        self.assertIsInstance(
            services.workflows.run.progress,
            composition.CompositeWorkflowProgress,
        )
        self.assertIsInstance(
            services.workflows.run.method_trace,
            composition.CompositeMethodTrace,
        )
        self.assertEqual("trace-test", services.workflows.run.trace_correlation_id)
        self.assertTrue(
            all(
                phase.method_trace is services.workflows.run.method_trace
                for phase in services.workflows.run.phases
            )
        )
        self.assertTrue(
            all(
                phase.trace_correlation_id == services.workflows.run.trace_correlation_id
                for phase in services.workflows.run.phases
            )
        )
        self.assertEqual(
            (
                "preflight",
                "platform init",
                "platform reconcile",
                "platform expose",
                "deployment bootstrap",
                "artifacts prepare",
                "artifacts verify",
                "deployment apply",
                "deployment verify",
                "platform verify",
            ),
            tuple(phase.name for phase in services.workflows.run.phases),
        )
        build_preflight.assert_called_once_with(
            service_profile=ServiceStackProfile.SERVICE_ACCESS,
            configuration_validation=None,
        )
        build_platform.assert_called_once_with(
            service_profile=ServiceStackProfile.SERVICE_ACCESS,
            live_consent=services.workflows.run.live_consent,
            ui=None,
            trace_correlation_id=services.workflows.run.trace_correlation_id,
        )
        build_artifacts.assert_called_once_with(node_provider_request=None, ui=None)
        build_deployment.assert_called_once_with(
            service_profile=ServiceStackProfile.SERVICE_ACCESS,
            node_provider_request=None,
        )
        build_preflight.return_value.run.assert_not_called()
        build_platform.return_value.workflows.init.run.assert_not_called()
        build_platform.return_value.workflows.expose.run.assert_not_called()
        build_artifacts.return_value.workflows.prepare.run.assert_not_called()
        build_deployment.return_value.workflows.apply.run.assert_not_called()

    def test_build_setup_services_passes_ui_to_platform_and_setup_terminal_sinks(self):
        live_consent = _accepted_live_consent()
        ui = _RecordingUI()
        captured: dict[str, object] = {}

        def build_platform(
            *,
            service_profile: object,
            live_consent: LiveConsent | None = None,
            ui: object | None = None,
            trace_correlation_id: str | None = None,
        ):
            captured["service_profile"] = service_profile
            captured["live_consent"] = live_consent
            captured["ui"] = ui
            captured["trace_correlation_id"] = trace_correlation_id
            return _platform_phase_bundle()

        def build_deployment(
            *,
            service_profile: object,
            node_provider_request: object | None = None,
            ui: object | None = None,
        ):
            captured["deployment_service_profile"] = service_profile
            captured["deployment_node_provider_request"] = node_provider_request
            captured["deployment_ui"] = ui
            return _deployment_phase_bundle()

        with patch.object(composition, "build_preflight_service", return_value=_phase_bundle()):
            with patch.object(composition, "build_platform_services", side_effect=build_platform):
                with patch.object(
                    composition,
                    "build_artifact_services_for_provider",
                    return_value=_artifact_phase_bundle(),
                ):
                    with patch.object(
                        composition,
                        "build_deployment_services_for_provider",
                        side_effect=build_deployment,
                    ):
                        services = composition.build_setup_services(live_consent, ui=ui)

        progress_sink = services.workflows.run.progress
        method_trace_sink = services.workflows.run.method_trace
        self.assertIsInstance(progress_sink, composition.CompositeWorkflowProgress)
        self.assertIsInstance(method_trace_sink, composition.CompositeMethodTrace)
        progress_sinks = cast(composition.CompositeWorkflowProgress, progress_sink).sinks
        method_trace_sinks = cast(composition.CompositeMethodTrace, method_trace_sink).sinks

        self.assertIs(ui, captured["ui"])
        self.assertIs(ui, captured["deployment_ui"])
        self.assertIs(live_consent, captured["live_consent"])
        self.assertEqual(ServiceStackProfile.SERVICE_ACCESS, captured["deployment_service_profile"])
        self.assertIsNone(captured["deployment_node_provider_request"])
        self.assertEqual(
            services.workflows.run.trace_correlation_id,
            captured["trace_correlation_id"],
        )
        self.assertTrue(
            any(
                isinstance(sink, composition.TerminalWorkflowProgress)
                and sink.ui is ui
                for sink in progress_sinks
            )
        )
        self.assertTrue(
            any(
                isinstance(sink, composition.TerminalMethodTrace)
                and sink.ui is ui
                for sink in method_trace_sinks
            )
        )

    def test_build_application_services_wires_preflight_through_platform_bundle(self):
        services = composition.build_application_services()

        self.assertIsInstance(services.platform.preflight, PreflightService)
        self.assertIs(services.preflight, services.platform.preflight)
        self.assertIsNot(
            services.platform.workflows.verify.steps[0],
            services.platform.preflight,
        )
        self.assertEqual(
            (),
            services.platform.workflows.verify.steps[0].configuration.required_ports,
        )

    def test_build_platform_services_wires_init_guard_when_live_consent_is_available(self):
        live_consent = _accepted_live_consent()
        services = composition.build_platform_services(live_consent=live_consent)

        self.assertIsNotNone(services.workflows.init.pre_apply_guard)
        self.assertTrue(services.lxc_node_provider.allow_live_mutation)
        self.assertTrue(services.lxc_docker_install.runtime.allow_live_mutation)
        self.assertTrue(services.lxc_proxy_drift_repair.runtime.allow_live_mutation)
        self.assertTrue(services.lxc_service_exposure.runtime.allow_live_mutation)
        self.assertTrue(services.lxc_swarm_bootstrap.swarm.allow_live_mutation)

    def test_lxc_docker_registry_mirror_configuration_uses_operator_environment(self):
        with patch.dict(
            os.environ,
            {"TSW_LXC_DOCKER_REGISTRY_MIRROR": f"http://{ipv4_address(10, 0, 3, 1)}:5001"},
            clear=True,
        ):
            with patch(
                "tiny_swarm_world.infrastructure.composition._auto_detect_nexus_cache_registry_mirror",
                return_value=f"http://{ipv4_address(10, 0, 3, 99)}:5001",
            ) as auto_detect:
                mirror = composition._lxc_docker_registry_mirror_configuration()

        self.assertIsNotNone(mirror)
        assert mirror is not None
        self.assertEqual(f"http://{ipv4_address(10, 0, 3, 1)}:5001", mirror.mirror_url)
        self.assertEqual(f"{ipv4_address(10, 0, 3, 1)}:5001", mirror.registry_authority)
        auto_detect.assert_not_called()

    def test_lxc_docker_registry_mirror_rejects_localhost_operator_value(self):
        with patch.dict(
            os.environ,
            {"TSW_LXC_DOCKER_REGISTRY_MIRROR": "http://127.0.0.1:5001"},
            clear=True,
        ):
            with self.assertRaises(ValueError):
                composition._lxc_docker_registry_mirror_configuration()

    def test_lxc_docker_registry_mirror_auto_detects_local_nexus_cache(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch(
                "tiny_swarm_world.infrastructure.composition._local_docker_container_running",
                return_value=True,
            ) as container_running:
                with patch(
                    "tiny_swarm_world.infrastructure.composition._lxc_reachable_host_ip",
                    return_value=ipv4_address(10, 0, 3, 1),
                ) as host_ip:
                    mirror = composition._lxc_docker_registry_mirror_configuration()

        self.assertIsNotNone(mirror)
        assert mirror is not None
        self.assertEqual(f"http://{ipv4_address(10, 0, 3, 1)}:5001", mirror.mirror_url)
        container_running.assert_called_once_with("tiny-swarm-nexus-cache")
        host_ip.assert_called_once()

    def test_lxc_docker_registry_mirror_returns_none_without_local_nexus_cache(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch(
                "tiny_swarm_world.infrastructure.composition._local_docker_container_running",
                return_value=False,
            ):
                mirror = composition._lxc_docker_registry_mirror_configuration()

        self.assertIsNone(mirror)

    def test_lxc_backend_for_provider_request_honors_candidate_order(self):
        def which(name: str):
            return f"/usr/bin/{name}" if name in {"incus", "lxc"} else None

        request = composition.NodeProviderSelectionRequest(
            backend_candidates=(
                composition.ManagedLxcBackend.INCUS,
                composition.ManagedLxcBackend.LXD,
            )
        )

        with patch.object(composition.shutil, "which", side_effect=which):
            backend = composition._lxc_backend_for_provider_request(request)

        self.assertEqual(composition.ManagedLxcBackend.INCUS, backend)

    def test_lxc_backend_for_provider_request_supports_lxd_first_order(self):
        def which(name: str):
            return f"/usr/bin/{name}" if name in {"incus", "lxc"} else None

        request = composition.NodeProviderSelectionRequest(
            backend_candidates=(
                composition.ManagedLxcBackend.LXD,
                composition.ManagedLxcBackend.INCUS,
            )
        )

        with patch.object(composition.shutil, "which", side_effect=which):
            backend = composition._lxc_backend_for_provider_request(request)

        self.assertEqual(composition.ManagedLxcBackend.LXD, backend)

    def test_preflight_configuration_for_incus_requires_incus_cli(self):
        request = composition.NodeProviderSelectionRequest(
            preferred_backend=composition.ManagedLxcBackend.INCUS,
        )

        configuration = composition._preflight_configuration_for_provider(
            composition.ServiceStackProfile.SERVICE_ACCESS,
            request,
        )

        dependency_names = {item.name for item in configuration.required_dependencies}
        self.assertIn("incus", dependency_names)
        self.assertNotIn("lxc", dependency_names)
        self.assertEqual("lxc_native", configuration.provider_metadata.provider)
        self.assertEqual("incus", configuration.provider_metadata.backend)
        self.assertIn(
            "selected-backend-control-network",
            configuration.provider_metadata.network_checks,
        )

    def test_preflight_configuration_for_lxd_requires_lxc_cli(self):
        request = composition.NodeProviderSelectionRequest(
            preferred_backend=composition.ManagedLxcBackend.LXD,
        )

        configuration = composition._preflight_configuration_for_provider(
            composition.ServiceStackProfile.SERVICE_ACCESS,
            request,
        )

        dependency_names = {item.name for item in configuration.required_dependencies}
        self.assertIn("lxc", dependency_names)
        self.assertNotIn("incus", dependency_names)
        self.assertEqual("lxd", configuration.provider_metadata.backend)
        self.assertEqual(
            ("backend-cli:lxc",),
            configuration.provider_metadata.provider_checks,
        )

    def test_preflight_configuration_honors_backend_candidate_order(self):
        def which(name: str):
            return f"/usr/bin/{name}" if name in {"incus", "lxc"} else None

        request = composition.NodeProviderSelectionRequest(
            backend_candidates=(
                composition.ManagedLxcBackend.LXD,
                composition.ManagedLxcBackend.INCUS,
            )
        )

        with patch.object(composition.shutil, "which", side_effect=which):
            configuration = composition._preflight_configuration_for_provider(
                composition.ServiceStackProfile.SERVICE_ACCESS,
                request,
            )

        dependency_names = {item.name for item in configuration.required_dependencies}
        self.assertIn("lxc", dependency_names)
        self.assertNotIn("incus", dependency_names)
        self.assertEqual("lxd", configuration.provider_metadata.backend)

    def test_preflight_configuration_blocks_missing_lxc_backend_candidates(self):
        request = composition.NodeProviderSelectionRequest(backend_candidates=())

        with patch.object(composition.shutil, "which", return_value=None):
            with self.assertRaisesRegex(ValueError, "requires at least one"):
                composition._preflight_configuration_for_provider(
                    composition.ServiceStackProfile.SERVICE_ACCESS,
                    request,
                )

    def test_default_node_provider_request_uses_committed_candidate_order(self):
        request = composition._default_node_provider_request()

        self.assertIsNone(request.preferred_backend)
        self.assertEqual(
            (
                composition.ManagedLxcBackend.INCUS,
                composition.ManagedLxcBackend.LXD,
            ),
            request.backend_candidates,
        )

    def test_build_setup_services_wires_live_consent_into_platform_init_guard(self):
        live_consent = _accepted_live_consent()
        captured: dict[str, object] = {}

        def build_platform(
            *,
            service_profile: object,
            live_consent: LiveConsent | None = None,
            ui: object | None = None,
            trace_correlation_id: str | None = None,
        ):
            captured["service_profile"] = service_profile
            captured["live_consent"] = live_consent
            captured["ui"] = ui
            captured["trace_correlation_id"] = trace_correlation_id
            return _platform_phase_bundle()

        with patch.object(composition, "build_preflight_service", return_value=_phase_bundle()):
            with patch.object(composition, "build_platform_services", side_effect=build_platform):
                with patch.object(
                    composition,
                    "build_artifact_services_for_provider",
                    return_value=_artifact_phase_bundle(),
                ):
                    with patch.object(
                        composition,
                        "build_deployment_services_for_provider",
                        return_value=_deployment_phase_bundle(),
                    ):
                        composition.build_setup_services(live_consent)

        self.assertIs(live_consent, captured["live_consent"])
        self.assertEqual(ServiceStackProfile.SERVICE_ACCESS, captured["service_profile"])
        self.assertIsNone(captured["ui"])
        self.assertTrue(
            str(captured["trace_correlation_id"]).startswith("trace-installation-")
        )

    def test_build_application_services_does_not_run_constructed_services(self):
        services = composition.build_application_services()

        self.assertIsInstance(services, composition.ApplicationServices)

    def test_composed_default_lxc_init_workflow_blocks_before_live_step_execution(self):
        evidence_repository = _RecordingEvidenceRepository()
        blocked_result = VerificationResult(
            target_id="platform:node-provider:lxc_native",
            status=VerificationStatus.BLOCKED,
            message="Provider selection blocked node lifecycle before apply.",
            evidence={
                "phase": "pre_apply",
                "reason": "provider_selection_blocked",
            },
        )
        with patch.object(
            composition,
            "VerificationEvidenceLocalRepository",
            return_value=evidence_repository,
        ):
            with patch.object(
                composition.NodeProviderSelectionService,
                "ensure_node",
                return_value=blocked_result,
            ):
                services = composition.build_platform_services()
                result = asyncio.run(services.workflows.init.run())

        self.assertEqual(PlatformWorkflowStatus.BLOCKED, result.status)
        self.assertFalse(result.executed)
        self.assertEqual(
            "platform:node-provider:lxc_native",
            result.verification_results[0].target_id,
        )
        self.assertEqual(
            "provider_selection_blocked",
            result.verification_results[0].evidence["reason"],
        )
        self.assertEqual(tuple(result.verification_results), evidence_repository.list_all())

    def test_composed_default_lxc_init_runs_container_runtime_and_swarm_steps(self):
        evidence_repository = _RecordingEvidenceRepository()

        async def verified_node(node, request=None):
            await async_checkpoint()
            return VerificationResult(
                target_id=f"platform:node:{node.name}",
                status=VerificationStatus.VERIFIED,
                message="Node lifecycle is verified.",
                evidence={"phase": "verify", "classification": "node_verified"},
            )

        async def verified_runtime(_service, _nodes):
            await async_checkpoint()
            return (
                VerificationResult(
                    target_id="container-runtime:swarm-manager",
                    status=VerificationStatus.VERIFIED,
                    message="Container runtime is verified.",
                    evidence={"phase": "verify"},
                ),
            )

        async def verified_swarm(_service, _manager, _workers):
            await async_checkpoint()
            return (
                VerificationResult(
                    target_id="swarm:swarm-manager",
                    status=VerificationStatus.VERIFIED,
                    message="Swarm manager is verified.",
                    evidence={"phase": "verify", "node": "swarm-manager"},
                ),
                VerificationResult(
                    target_id="swarm:swarm-worker-1",
                    status=VerificationStatus.VERIFIED,
                    message="Swarm worker is verified.",
                    evidence={"phase": "verify", "node": "swarm-worker-1"},
                ),
                VerificationResult(
                    target_id="swarm:swarm-worker-2",
                    status=VerificationStatus.VERIFIED,
                    message="Swarm worker is verified.",
                    evidence={"phase": "verify", "node": "swarm-worker-2"},
                ),
            )

        with patch.object(
            composition,
            "VerificationEvidenceLocalRepository",
            return_value=evidence_repository,
        ):
            with patch.object(
                composition.NodeProviderSelectionService,
                "ensure_node",
                side_effect=verified_node,
            ):
                with patch.object(
                    composition.LxcDockerInstallService,
                    "ensure_docker_installed",
                    autospec=True,
                    side_effect=verified_runtime,
                ) as ensure_runtime:
                    with patch.object(
                        composition.LxcSwarmBootstrapService,
                        "bootstrap_swarm",
                        autospec=True,
                        side_effect=verified_swarm,
                    ) as bootstrap_swarm:
                        services = composition.build_platform_services()
                        result = asyncio.run(services.workflows.init.run())

        self.assertEqual(PlatformWorkflowStatus.COMPLETED, result.status)
        self.assertTrue(result.executed)
        self.assertEqual(
            (
                "platform:node:swarm-manager",
                "platform:node:swarm-worker-1",
                "platform:node:swarm-worker-2",
                "platform:init:lxc-container-runtime",
                "platform:init:lxc-swarm-bootstrap",
            ),
            tuple(item.target_id for item in result.verification_results),
        )
        ensure_runtime.assert_called_once()
        bootstrap_swarm.assert_called_once()
        self.assertEqual(
            composition.DEFAULT_LXC_PLATFORM_NODES,
            ensure_runtime.call_args.args[1],
        )
        self.assertEqual("swarm-manager", bootstrap_swarm.call_args.args[1].name)
        self.assertEqual(
            ("swarm-worker-1", "swarm-worker-2"),
            tuple(worker.name for worker in bootstrap_swarm.call_args.args[2]),
        )
        self.assertEqual(tuple(result.verification_results), evidence_repository.list_all())

    def test_composed_default_lxc_init_without_live_consent_fails_closed_before_runtime_probe(self):
        evidence_repository = _RecordingEvidenceRepository()

        async def verified_node(node, request=None):
            await async_checkpoint()
            return VerificationResult(
                target_id=f"platform:node:{node.name}",
                status=VerificationStatus.VERIFIED,
                message="Node lifecycle is verified.",
                evidence={"phase": "verify", "classification": "node_verified"},
            )

        with patch.object(
            composition,
            "VerificationEvidenceLocalRepository",
            return_value=evidence_repository,
        ):
            with patch.object(
                composition.NodeProviderSelectionService,
                "ensure_node",
                side_effect=verified_node,
            ):
                with patch.object(
                    composition,
                    "LxcContainerDockerRuntime",
                    side_effect=AssertionError(
                        "runtime adapter must not be constructed without consent"
                    ),
                ):
                    services = composition.build_platform_services()
                    result = asyncio.run(services.workflows.init.run())

        self.assertEqual(PlatformWorkflowStatus.BLOCKED, result.status)
        self.assertFalse(result.executed)
        self.assertEqual(
            "platform:init:lxc-container-runtime",
            result.verification_results[-1].target_id,
        )
        self.assertEqual(
            "container_runtime_not_verified",
            result.verification_results[-1].evidence["classification"],
        )
        self.assertEqual(tuple(result.verification_results), evidence_repository.list_all())

    def test_composed_default_lxc_reconcile_verifies_configured_nodes_without_provider_fallback(self):
        evidence_repository = _RecordingEvidenceRepository()

        async def verified_node(node, request=None):
            await async_checkpoint()
            return VerificationResult(
                target_id=f"platform:node:{node.name}",
                status=VerificationStatus.VERIFIED,
                message="Node already matches configured state.",
                evidence={
                    "phase": "verify",
                    "classification": "already_present",
                    "node": node.name,
                },
            )

        with patch.object(
            composition,
            "VerificationEvidenceLocalRepository",
            return_value=evidence_repository,
        ):
            with patch.object(
                composition.NodeProviderSelectionService,
                "ensure_node",
                side_effect=verified_node,
            ) as ensure_node:
                with patch.object(
                    composition.CommandWorkflow,
                    "verify_config_contract",
                    side_effect=AssertionError(
                        "default reconcile must not inspect command contracts"
                    ),
                ) as verify_config_contract:
                    services = composition.build_platform_services()
                    result = asyncio.run(services.workflows.reconcile.run())

        self.assertEqual(PlatformWorkflowStatus.COMPLETED, result.status)
        self.assertTrue(result.executed)
        verify_config_contract.assert_not_called()
        self.assertEqual(
            tuple(
                f"platform:node:{node.name}"
                for node in composition.DEFAULT_LXC_PLATFORM_NODES
            ),
            tuple(item.target_id for item in result.verification_results),
        )
        self.assertEqual(
            ["swarm-manager", "swarm-worker-1", "swarm-worker-2"],
            [call.args[0].name for call in ensure_node.call_args_list],
        )
        self.assertEqual(tuple(result.verification_results), evidence_repository.list_all())

    def test_composed_default_lxc_reconcile_reports_converged_node_drift(self):
        evidence_repository = _RecordingEvidenceRepository()

        async def reconcile_node(node, request=None):
            await async_checkpoint()
            applied = node.name == "swarm-worker-1"
            evidence = {
                "phase": "apply" if applied else "verify",
                "classification": "started" if applied else "already_present",
                "node": node.name,
            }
            if applied:
                evidence["applied"] = "true"
            return VerificationResult(
                target_id=f"platform:node:{node.name}",
                status=VerificationStatus.VERIFIED,
                message="Node lifecycle is reconciled.",
                evidence=evidence,
            )

        with patch.object(
            composition,
            "VerificationEvidenceLocalRepository",
            return_value=evidence_repository,
        ):
            with patch.object(
                composition.NodeProviderSelectionService,
                "ensure_node",
                side_effect=reconcile_node,
            ):
                services = composition.build_platform_services()
                result = asyncio.run(services.workflows.reconcile.run())

        self.assertEqual(PlatformWorkflowStatus.COMPLETED, result.status)
        self.assertEqual(
            "converged",
            result.to_dict()["outcome"]["mutation"]["result"],
        )
        self.assertEqual(
            "platform:node:swarm-worker-1",
            next(
                item
                for item in result.verification_results
                if item.evidence.get("applied") == "true"
            ).target_id,
        )
        self.assertEqual(tuple(result.verification_results), evidence_repository.list_all())

    def test_composed_default_lxc_reconcile_blocks_before_unapproved_mutation(self):
        evidence_repository = _RecordingEvidenceRepository()

        async def blocked_node(node, request=None):
            await async_checkpoint()
            return VerificationResult(
                target_id=f"platform:node:{node.name}",
                status=VerificationStatus.BLOCKED,
                message="Live mutation is required to reconcile node drift.",
                evidence={
                    "phase": "pre_apply",
                    "reason": "live_mutation_required",
                    "node": node.name,
                },
            )

        with patch.object(
            composition,
            "VerificationEvidenceLocalRepository",
            return_value=evidence_repository,
        ):
            with patch.object(
                composition.NodeProviderSelectionService,
                "ensure_node",
                side_effect=blocked_node,
            ):
                services = composition.build_platform_services()
                result = asyncio.run(services.workflows.reconcile.run())

        self.assertEqual(PlatformWorkflowStatus.BLOCKED, result.status)
        self.assertFalse(result.executed)
        self.assertEqual(
            "blocked",
            result.to_dict()["outcome"]["mutation"]["result"],
        )
        self.assertEqual(
            "platform:node:swarm-manager",
            result.verification_results[0].target_id,
        )
        self.assertEqual(tuple(result.verification_results), evidence_repository.list_all())

    def test_composed_default_lxc_expose_uses_manager_gateway_and_setup_ports(self):
        services = composition.build_platform_services()

        self.assertEqual(2, len(services.workflows.expose.steps))
        step = services.workflows.expose.steps[0]
        socat_step = services.workflows.expose.steps[1]

        self.assertIsInstance(step, composition.LxcServiceExposureStep)
        self.assertIsInstance(socat_step, composition._WslSocatExposeStep)
        self.assertIs(step.service, services.lxc_service_exposure)
        self.assertIs(socat_step.socat_manager, services.socat_manager)
        self.assertEqual("swarm-manager", step.service.gateway_node.name)
        self.assertEqual(
            composition.DEFAULT_LXC_MANAGER_PROXY_PROFILE,
            step.service.manager_profile_name,
        )
        self.assertEqual(
            composition.DEFAULT_LXC_PROXY_LISTEN_ADDRESS,
            step.service.listen_address,
        )
        self.assertEqual(2, len(step.service.setup_manifest.required_ports))
        self.assertEqual("Infisical", step.service.setup_manifest.services[-1].name)

    def test_composed_wsl_socat_expose_verifies_not_required_on_native_linux(self):
        services = composition.build_platform_services()
        socat_step = services.workflows.expose.steps[1]
        socat_step.os_type = composition.OsTypes.LINUX

        result = asyncio.run(socat_step.run())

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual("not_required", result.evidence["classification"])

    def test_composed_lxc_proxy_drift_repair_uses_manager_profile_scope(self):
        services = composition.build_platform_services()

        self.assertEqual(1, len(services.workflows.repair_lxc_proxy_drift.steps))
        step = services.workflows.repair_lxc_proxy_drift.steps[0]

        self.assertIsInstance(step, composition.LxcProxyDriftRepairStep)
        self.assertIs(step.service, services.lxc_proxy_drift_repair)
        self.assertEqual("swarm-manager", step.service.gateway_node.name)
        self.assertEqual(
            composition.DEFAULT_LXC_MANAGER_PROXY_PROFILE,
            step.service.manager_profile_name,
        )
        self.assertEqual(
            composition.DEFAULT_LXC_PROXY_LISTEN_ADDRESS,
            step.service.listen_address,
        )
        self.assertEqual(2, len(step.service.setup_manifest.required_ports))

    def test_composed_default_lxc_expose_without_live_consent_fails_closed(self):
        with patch.object(
            composition,
            "LxcProxyDeviceRuntime",
            side_effect=AssertionError("proxy runtime must not run without consent"),
        ):
            services = composition.build_platform_services()
            result = asyncio.run(services.workflows.expose.run())

        self.assertEqual(PlatformWorkflowStatus.FAILED_TO_APPLY, result.status)
        self.assertEqual(
            "platform:expose:lxc-proxy-devices",
            result.verification_results[0].target_id,
        )
        self.assertEqual(
            "2",
            result.verification_results[0].evidence["lookup_failure_count"],
        )



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


class _ExistingPath:
    def __init__(self, *, exists: bool):
        self._exists = exists

    def exists(self):
        return self._exists


class _RecordingUI(PortUI):
    def __init__(self):
        super().__init__(instances=(), test_mode=True)

    def start(self):
        return None


class _LifecycleRecordingUI(PortUI):
    def __init__(self, calls: list[str]):
        super().__init__(instances=(), test_mode=True)
        self.calls = calls
        self.updates: list[tuple[str, str, str, str | None]] = []

    def start_in_thread(self):
        self.calls.append("ui started")
        self.ui_thread = _record_ui_awaited(self.calls)

    def update_status(self, instance, task, step, result=None):
        super().update_status(instance, task, step, result)
        status = self._status_for_instance(instance)
        self.updates.append((instance, task, step, status["result"]))
        if instance == AGGREGATE_INSTANCE and step in {"finished", "exception"}:
            self.calls.append(f"ui update {status['result']}")

    def start(self):
        return None


async def _record_ui_awaited(calls: list[str]):
    await async_checkpoint()
    calls.append("ui awaited")


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
    return _workflow_bundle("init", "reconcile", "expose", "verify")


def _artifact_phase_bundle():
    return _workflow_bundle("prepare", "verify")


def _deployment_phase_bundle():
    return _workflow_bundle("bootstrap", "apply", "verify")


def _setup_lifecycle_bundle(
    calls: list[str],
    result: SetupWorkflowResult | Exception,
    *,
    ui: PortUI | None = None,
    status_updates: tuple[str, ...] = (),
):
    from types import SimpleNamespace

    class SetupRun:
        async def run(self):
            await async_checkpoint()
            calls.append("workflow run")
            if ui is not None:
                for status in status_updates:
                    ui.update_status(
                        AGGREGATE_INSTANCE,
                        task="setup run",
                        step="workflow progress",
                        result=status,
                    )
            if isinstance(result, Exception):
                raise result
            return result

    return SimpleNamespace(workflows=SimpleNamespace(run=SetupRun()))


def _setup_result(status: SetupWorkflowStatus) -> SetupWorkflowResult:
    return SetupWorkflowResult(
        kind=SetupWorkflowKind.RUN,
        status=status,
        message=f"setup run {status.value}.",
        reason=status.value,
        executed=True,
    )
