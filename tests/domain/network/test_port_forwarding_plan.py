import unittest

from tests.support.sonar_safe_literals import sample_http_url, sample_text, sample_url
from tiny_swarm_world.domain.network.port_forwarding_plan import (
    ForwardingStrategy,
    PortExposureClass,
    PortForwardingPlan,
    PortRange,
    PortRegistry,
    ServicePortMapping,
)


class TestPortForwardingPlan(unittest.TestCase):
    def test_wsl2_socat_plan_describes_ports_without_addresses(self):
        plan = PortForwardingPlan(
            strategy=ForwardingStrategy.WSL2_SOCAT,
            service="Portainer",
            listen_port=9000,
            target_port=9000,
            remediation=("Start forwarding only after operator approval.",),
        )

        self.assertTrue(plan.requires_operator_action)
        self.assertFalse(plan.supported_without_operator_action)
        payload = plan.to_dict()
        self.assertEqual("wsl2_socat", payload["strategy"])
        self.assertNotIn("host_ip", payload)
        self.assertNotIn("vm_ip", payload)

    def test_native_linux_direct_plan_is_supported_without_operator_action(self):
        plan = PortForwardingPlan(
            strategy=ForwardingStrategy.NATIVE_LINUX_DIRECT,
            service="Nexus",
            listen_port=8081,
            target_port=8081,
            remediation=("Use the published service port.",),
        )

        self.assertFalse(plan.requires_operator_action)
        self.assertTrue(plan.supported_without_operator_action)

    def test_unsupported_plan_is_blocked(self):
        plan = PortForwardingPlan(
            strategy=ForwardingStrategy.UNSUPPORTED,
            service="Unknown host",
            listen_port=9000,
            target_port=9000,
            remediation=("Use native Linux or WSL2.",),
        )

        self.assertFalse(plan.requires_operator_action)
        self.assertFalse(plan.supported_without_operator_action)

    def test_rejects_invalid_ports_and_empty_service_names(self):
        with self.assertRaises(ValueError):
            PortForwardingPlan(
                strategy=ForwardingStrategy.WSL2_SOCAT,
                service="Portainer",
                listen_port=0,
                target_port=9000,
                remediation=("Fix the port.",),
            )

        with self.assertRaises(ValueError):
            PortForwardingPlan(
                strategy=ForwardingStrategy.WSL2_SOCAT,
                service=" ",
                listen_port=9000,
                target_port=9000,
                remediation=("Fix the service name.",),
            )


class TestPortRegistry(unittest.TestCase):
    def test_accepts_ranges_and_service_mappings_without_parser_dependency(self):
        registry = _sample_registry()

        self.assertEqual(
            ("public-ingress", "direct-diagnostic"),
            tuple(port_range.range_id for port_range in registry.ranges),
        )
        self.assertEqual((80, 443, 18081), registry.external_ports)
        self.assertEqual(
            (80, 443, 8081),
            tuple(mapping.internal_port for mapping in registry.mappings),
        )
        self.assertEqual(
            PortExposureClass.PUBLIC_INGRESS,
            registry.mapping_for_port_id("traefik-http").exposure,
        )
        self.assertEqual(
            PortExposureClass.DIAGNOSTIC,
            registry.mapping_for_port_id("nexus-ui").exposure,
        )
        payload = registry.to_dict()
        self.assertNotIn("host_ip", repr(payload))
        self.assertNotIn("vm_ip", repr(payload))

    def test_rejects_duplicate_external_ports(self):
        with self.assertRaisesRegex(ValueError, "duplicate external ports"):
            PortRegistry(
                ranges=(_direct_range(),),
                mappings=(
                    _mapping("nexus-ui", external_port=18081),
                    _mapping("sonarqube-ui", external_port=18081),
                ),
            )

    def test_rejects_invalid_port_ranges(self):
        with self.assertRaisesRegex(ValueError, "start must be a TCP port"):
            PortRange("bad-low", 0, 1024)

        with self.assertRaisesRegex(ValueError, "end must be a TCP port"):
            PortRange("bad-high", 1024, 65536)

        with self.assertRaisesRegex(ValueError, "start must be less than or equal"):
            PortRange("bad-order", 9000, 8000)

    def test_rejects_overlapping_ranges(self):
        with self.assertRaisesRegex(ValueError, "ranges must not overlap"):
            PortRegistry(
                ranges=(
                    PortRange("first", 10000, 10999),
                    PortRange("second", 10999, 11999),
                ),
                mappings=(),
            )

    def test_rejects_service_ports_outside_declared_range(self):
        with self.assertRaisesRegex(ValueError, "external_port must belong"):
            PortRegistry(
                ranges=(_direct_range(),),
                mappings=(
                    _mapping("nexus-registry", external_port=5000),
                ),
            )

    def test_rejects_invalid_service_ids(self):
        for service_id in (
            "",
            "Nexus",
            "nexus admin",
            "nexus_admin",
            "../nexus",
            sample_http_url("nexus"),
        ):
            with self.subTest(service_id=service_id):
                with self.assertRaisesRegex(ValueError, "service_id"):
                    _mapping(service_id, external_port=18081)

    def test_rejects_invalid_internal_and_external_ports(self):
        for kwargs in (
            {"internal_port": 0},
            {"internal_port": 65536},
            {"external_port": 0},
            {"external_port": 65536},
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaisesRegex(ValueError, "port"):
                    _mapping("nexus-ui", **kwargs)

    def test_rejects_host_specific_addresses_and_credential_metadata(self):
        unsafe_metadata = (
            {"host_ip": "192.168.1.10"},
            {"listen_address": "10.0.0.5"},
            {
                "endpoint": sample_url(
                    "http",
                    sample_text("sample", "-", "name", ":", "sample", "-", "value"),
                    "localhost:9000",
                ),
            },
            {
                "dashboard_url": sample_url(
                    "https",
                    sample_text("fixture", "-", "name", ":", "fixture", "-", "value"),
                    "example.test",
                ),
            },
            {"secret": "plain-value"},
            {"token": "plain-value"},
        )
        for metadata in unsafe_metadata:
            with self.subTest(metadata=metadata):
                with self.assertRaisesRegex(
                    ValueError,
                    "host-specific|credential|secret",
                ):
                    _mapping("unsafe-service", metadata=metadata)

    def test_rejects_host_specific_route_hosts_and_urls(self):
        for route_host in (
            "192.168.1.10",
            sample_url(
                "http",
                sample_text("sample", "-", "name", ":", "sample", "-", "value"),
                "localhost:9000",
            ),
        ):
            with self.subTest(route_host=route_host):
                with self.assertRaisesRegex(
                    ValueError,
                    "host-specific|URL",
                ):
                    _mapping("unsafe-service", route_host=route_host)

    def test_rejects_non_traefik_public_ingress(self):
        with self.assertRaisesRegex(ValueError, "Traefik-owned 80 or 443"):
            _mapping(
                "gateway",
                internal_port=80,
                external_port=10080,
                exposure=PortExposureClass.PUBLIC_INGRESS,
                range_id="direct-diagnostic",
            )

    def test_preserves_internal_external_semantics(self):
        registry = _sample_registry()

        nexus = registry.mapping_for_port_id("nexus-ui")

        self.assertEqual(8081, nexus.internal_port)
        self.assertEqual(18081, nexus.external_port)
        self.assertFalse(nexus.required_for_preflight)
        payload = registry.to_dict()
        self.assertEqual(8081, payload["ports"][2]["internal_port"])
        self.assertEqual(18081, payload["ports"][2]["external_port"])
        self.assertNotEqual(nexus.internal_port, nexus.external_port)


def _direct_range() -> PortRange:
    return PortRange("direct-diagnostic", 10000, 19999)


def _mapping(
    service_id: str,
    *,
    port_id: str | None = None,
    internal_port: int = 8081,
    external_port: int | None = 18081,
    exposure: PortExposureClass = PortExposureClass.DIAGNOSTIC,
    range_id: str | None = "direct-diagnostic",
    route_host: str | None = None,
    metadata: dict[str, str] | None = None,
) -> ServicePortMapping:
    return ServicePortMapping(
        service_id=service_id,
        port_id=port_id or service_id,
        internal_port=internal_port,
        external_port=external_port,
        exposure=exposure,
        range_id=range_id,
        route_host=route_host,
        required_for_preflight=False,
        metadata=metadata,
    )


def _sample_registry() -> PortRegistry:
    return PortRegistry(
        ranges=(
            PortRange("public-ingress", 80, 443),
            _direct_range(),
        ),
        mappings=(
            ServicePortMapping(
                service_id="traefik",
                port_id="traefik-http",
                internal_port=80,
                external_port=80,
                exposure=PortExposureClass.PUBLIC_INGRESS,
                range_id="public-ingress",
                route_host="tsw.local",
            ),
            ServicePortMapping(
                service_id="traefik",
                port_id="traefik-https",
                internal_port=443,
                external_port=443,
                exposure=PortExposureClass.PUBLIC_INGRESS,
                range_id="public-ingress",
                route_host="tsw.local",
            ),
            _mapping("nexus", port_id="nexus-ui"),
        ),
    )
