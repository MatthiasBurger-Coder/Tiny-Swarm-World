import unittest

from tiny_swarm_world.infrastructure.adapters.preflight.service_probes.registry import (
    default_service_probe_registry,
)


class TestServiceProbeRegistry(unittest.TestCase):
    def test_default_registry_preserves_ordered_service_patterns(self):
        registry = default_service_probe_registry(
            http_probe=lambda port, paths, markers, *, scheme="http": True,
            service_access_probe=lambda port: True,
            tcp_probe=lambda port: True,
            api_status_path="/api/status",
            service_access_text="service access",
        )

        self.assertEqual(
            [
                "portainer",
                "docker registry",
                "nexus",
                "jenkins",
                "pulsar admin",
                "pulsar manager",
                "pulsar broker",
                "sonarqube",
                "swagger api",
                "swagger",
                "traefik http ingress",
                "traefik https ingress",
                "service access",
                "infisical https",
                "infisical",
            ],
            [probe.service_pattern for probe in registry.probes],
        )

    def test_specific_patterns_win_before_generic_patterns(self):
        calls = []

        def http_probe(port, paths, markers, *, scheme="http"):
            calls.append((paths, markers, scheme))
            return True

        registry = default_service_probe_registry(
            http_probe=http_probe,
            service_access_probe=lambda port: True,
            tcp_probe=lambda port: True,
            api_status_path="/api/status",
            service_access_text="service access",
        )

        self.assertTrue(registry.matches(8084, "Swagger API"))
        self.assertEqual(
            [(("/",), ("access-control-allow-origin: *",), "http")],
            calls,
        )

    def test_unsupported_service_fails_closed_without_probe(self):
        calls = []
        registry = default_service_probe_registry(
            http_probe=lambda *args, **kwargs: calls.append("http") or True,
            service_access_probe=lambda port: calls.append("service") or True,
            tcp_probe=lambda port: calls.append("tcp") or True,
            api_status_path="/api/status",
            service_access_text="service access",
        )

        self.assertFalse(registry.matches(1234, "Unknown Service"))
        self.assertEqual([], calls)
