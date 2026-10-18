"""Local composition regressions; all credentials below are synthetic fixtures."""

import os
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from tiny_swarm_world.domain.deployment import ServiceStackProfile
from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
from tiny_swarm_world.domain.lifecycle.selection import plan_selection
from tiny_swarm_world.domain.preflight import LiveConsent
from tiny_swarm_world.infrastructure import composition
from tiny_swarm_world.infrastructure.adapters.lifecycle.catalog import NativeComponentCatalog


ROOT = Path(__file__).resolve().parents[2]


class SelectiveSetupCompositionTests(unittest.TestCase):
    def setUp(self):
        self.catalog = NativeComponentCatalog(ROOT).load()
        self.environment = {
            "TSW_PORTAINER_ADMIN_PASSWORD": "synthetic-portainer-value",
        }

    def test_setup_forwards_resolved_selection_to_every_builder(self):
        plan = plan_selection(self.catalog, ("swagger", "sonarqube"))
        builders = (
            "_build_preflight_service_for_request",
            "_build_artifact_readiness_gate",
            "_build_platform_services_for_request",
            "build_artifact_services_for_provider",
            "_build_deployment_services_for_request",
            "ComposeFileRepositoryYaml",
        )
        with ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ, self.environment, clear=True))
            mocks = {
                name: stack.enter_context(patch.object(composition, name))
                for name in builders
            }
            stack.enter_context(patch.object(composition, "build_host_preparation_service"))
            services = composition.build_setup_services(
                LiveConsent(live_flag=False), selection_plan=plan,
            )

        self.assertTrue(services.workflows.run.phases)
        for name, builder in mocks.items():
            with self.subTest(builder=name):
                builder.assert_called_once()
                self.assertEqual(
                    plan.resolved_services,
                    builder.call_args.kwargs["resolved_services"],
                )
        mocks["ComposeFileRepositoryYaml"].return_value.validate_and_snapshot.assert_called_once_with(
            ("portainer", "sonarqube", "swagger"),
        )

    def test_selective_preflight_requires_only_selected_ports_and_secrets(self):
        plan = plan_selection(self.catalog, minimal=True)
        configuration = composition._preflight_configuration_for_provider(
            ServiceStackProfile.SERVICE_ACCESS, None,
            host_environment=HostEnvironmentKind.NATIVE_LINUX,
            resolved_services=plan.resolved_services,
        )

        self.assertEqual(("Portainer",), configuration.setup_manifest.service_names)
        self.assertEqual((10001,), tuple(item.port for item in configuration.required_ports))
        self.assertEqual(
            ("TSW_PORTAINER_ADMIN_PASSWORD",),
            tuple(item.name for item in configuration.required_secrets),
        )

    def _build_deployment(self, selected, extra_environment=None):
        environment = {**self.environment, **(extra_environment or {})}
        with (
            patch.dict(os.environ, environment, clear=True),
            patch.object(composition, "LxcSwarmRuntime") as runtime,
            patch.object(composition, "InfisicalCliClient") as infisical,
            patch.object(composition, "HostEnvironmentDetector") as detector,
        ):
            detector.return_value.detect.return_value.environment = HostEnvironmentKind.NATIVE_LINUX
            services = composition.build_lxc_deployment_services(
                backend=composition.ManagedLxcBackend.INCUS,
                service_profile=ServiceStackProfile.SERVICE_ACCESS,
                resolved_services=selected,
            )
            for workflow in (services.workflows.bootstrap, services.workflows.apply):
                workflow.configuration_preparation()
            runtime.return_value.prepare_stack_assets.assert_not_called()
            runtime.return_value.apply_stack.assert_not_called()
            infisical.assert_not_called()
        return services

    def test_minimal_deployment_needs_no_nexus_or_optional_credentials(self):
        plan = plan_selection(self.catalog, minimal=True)
        services = self._build_deployment(plan.resolved_services)

        self.assertEqual(
            ("deployment:portainer-stack", "deployment:portainer-admin-access",
             "deployment:portainer-local-endpoint"),
            tuple(step.verification_target_id for step in services.workflows.bootstrap.steps),
        )
        self.assertEqual((), services.workflows.apply.steps)
        self.assertEqual((), services.workflows.apply.pre_apply_checks)
        self.assertEqual(
            (), tuple(step.stack_name for step in services.workflows.apply.pre_apply_steps
                      if hasattr(step, "stack_name")),
        )
        self.assertEqual(
            ("deployment:portainer-service-readiness",),
            tuple(check.verification_target_id for check in services.workflows.verify.checks),
        )

    def test_minimal_artifacts_exclude_nexus_auth_and_unselected_images(self):
        plan = plan_selection(self.catalog, minimal=True)
        with (
            patch.dict(os.environ, self.environment, clear=True),
            patch.object(composition, "build_process_runner") as runner,
        ):
            services = composition.build_lxc_artifact_services(
                backend=composition.ManagedLxcBackend.INCUS,
                resolved_services=plan.resolved_services,
            )
            runner.return_value.run_text.assert_not_called()

        self.assertEqual((), services.workflows.prepare.bootstrap_steps)
        self.assertFalse(services.workflows.prepare.requires_bootstrap)
        expected = {"artifacts:portainer-image", "artifacts:portainer-agent-image"}
        self.assertEqual(
            expected,
            {step.verification_target_id for step in services.workflows.prepare.steps},
        )
        self.assertEqual(
            expected,
            {check.verification_target_id for check in services.workflows.verify.checks},
        )

    def test_swagger_sonarqube_prepare_and_verify_only_selected_stacks(self):
        plan = plan_selection(self.catalog, ("swagger", "sonarqube"))
        services = self._build_deployment(plan.resolved_services, {
            "TSW_SONARQUBE_ADMIN_PASSWORD": "synthetic-sonar-admin-value!",
            "TSW_POSTGRES_PASSWORD": "synthetic-sonar-postgres-value",
            "TSW_SONARQUBE_POSTGRES_PASSWORD": "synthetic-sonar-postgres-value",
        })

        self.assertEqual(
            ("deployment:sonarqube-stack", "deployment:sonarqube-admin-access",
             "deployment:swagger-stack"),
            tuple(step.verification_target_id for step in services.workflows.apply.steps),
        )
        self.assertEqual(
            ("swagger",),
            tuple(step.stack_name for step in services.workflows.apply.pre_apply_steps
                  if hasattr(step, "stack_name")),
        )
        self.assertEqual(
            ("deployment:portainer-service-readiness", "deployment:sonarqube-service-readiness",
             "deployment:swagger-service-readiness"),
            tuple(check.verification_target_id for check in services.workflows.verify.checks),
        )

    def test_jenkins_selection_keeps_transitive_nexus_bootstrap_and_readiness(self):
        plan = plan_selection(self.catalog, ("jenkins",))
        services = self._build_deployment(plan.resolved_services, {
            "TSW_NEXUS_ADMIN_PASSWORD": "synthetic-nexus-value",
            "TSW_JENKINS_ADMIN_PASSWORD": "synthetic-jenkins-value",
        })

        self.assertEqual(
            "deployment:nexus-stack",
            services.workflows.bootstrap.steps[-1].verification_target_id,
        )
        self.assertEqual(
            ("deployment:jenkins-stack",),
            tuple(step.verification_target_id for step in services.workflows.apply.steps),
        )
        self.assertEqual(
            ("deployment:portainer-service-readiness", "deployment:nexus-service-readiness",
             "deployment:jenkins-service-readiness"),
            tuple(check.verification_target_id for check in services.workflows.verify.checks),
        )
