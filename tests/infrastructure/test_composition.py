from dataclasses import fields
import unittest
from unittest.mock import patch

from tiny_swarm_world.application.services.platform.preflight_service import PreflightService
from tiny_swarm_world.infrastructure import composition
from tiny_swarm_world.infrastructure.adapters.preflight import HostPreflightProbe


class TestComposition(unittest.TestCase):
    def test_application_services_aliases_platform_services(self):
        self.assertIs(composition.ApplicationServices, composition.PlatformServices)

    def test_build_application_services_delegates_to_platform_builder(self):
        expected_services = object()

        with patch.object(
            composition,
            "build_platform_services",
            return_value=expected_services,
        ) as build_platform_services:
            services = composition.build_application_services()

        self.assertIs(services, expected_services)
        build_platform_services.assert_called_once_with()

    def test_platform_services_contains_preflight_service(self):
        field_names = {field.name for field in fields(composition.PlatformServices)}

        self.assertIn("preflight", field_names)

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
