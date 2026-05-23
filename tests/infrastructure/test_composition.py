from dataclasses import fields
import unittest
from unittest.mock import patch

from tiny_swarm_world.application.services.platform.preflight_service import PreflightService
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

    def test_artifact_and_deployment_service_bundles_exist(self):
        self.assertEqual([], list(fields(composition.ArtifactServices)))
        self.assertEqual([], list(fields(composition.DeploymentServices)))

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

    def test_build_application_services_wires_preflight_through_platform_bundle(self):
        with patch.object(composition, "PortVmRepositoryYaml"):
            with patch.object(composition, "PortNetplanRepositoryYaml"):
                services = composition.build_application_services()

        self.assertIsInstance(services.platform.preflight, PreflightService)
        self.assertIs(services.preflight, services.platform.preflight)

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
