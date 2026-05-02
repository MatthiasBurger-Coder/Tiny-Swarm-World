import unittest
from unittest.mock import patch

from tiny_swarm_world.infrastructure import composition


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
