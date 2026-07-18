import unittest

from tiny_swarm_world.application.ports.network import (
    CommandObservation,
    ForwardingObservation,
    IncusObservation,
    LxcNodeObservation,
    NetworkRepairMutationResult,
    RuntimeObservation,
    ServicePortObservation,
    WslHostObservation,
)
from tiny_swarm_world.application.services.network import (
    NetworkDoctorService,
    NetworkRepairOptions,
    NetworkRepairService,
)
from tiny_swarm_world.domain.network import (
    PortExposureClass,
    PortRange,
    PortRegistry,
    ServicePortMapping,
)


class TestNetworkDoctorService(unittest.IsolatedAsyncioTestCase):
    async def test_wsl2_nat_happy_path_reports_expected_acceptance_lines(self):
        report = await NetworkDoctorService(
            _HealthyProbe(),
            _sample_port_registry(),
        ).run()

        rendered = report.render()

        self.assertTrue(report.passed)
        self.assertIn("Runtime: wsl2", rendered)
        self.assertIn("Networking mode: nat", rendered)
        self.assertIn("WSL egress: OK", rendered)
        self.assertIn("Incus network incusbr0: OK", rendered)
        self.assertIn("LXC swarm-manager gateway: OK", rendered)
        self.assertIn("LXC swarm-manager DNS: OK", rendered)
        self.assertIn("LXC swarm-manager HTTP egress: OK", rendered)
        self.assertIn("Docker/Incus forwarding: OK", rendered)

    async def test_lxc_http_blocked_with_docker_forward_drop_suggests_forwarding_repair(self):
        report = await NetworkDoctorService(
            _ForwardingBlockedProbe(),
            _sample_port_registry(),
        ).run()

        rendered = report.render()

        self.assertFalse(report.passed)
        self.assertIn("LXC_HTTP_BLOCKED", rendered)
        self.assertIn("INCUS_FORWARDING_BLOCKED_BY_DOCKER", rendered)
        self.assertIn("./tsw network repair --linux-forwarding --apply", rendered)

    async def test_historical_incus_journal_dnsmasq_failure_does_not_fail_available_bridge(self):
        report = await NetworkDoctorService(
            _HistoricalIncusJournalFailureProbe(),
            _sample_port_registry(),
        ).run()

        rendered = report.render()

        self.assertTrue(report.passed)
        self.assertIn("INCUSBR0_OK", rendered)
        self.assertNotIn("INCUS_DNSMASQ_FAILED", rendered)

    async def test_native_linux_skips_windows_and_wsl_sections(self):
        report = await NetworkDoctorService(
            _NativeLinuxProbe(),
            _sample_port_registry(),
        ).run()

        rendered = report.render()

        self.assertTrue(report.passed)
        self.assertIn("Runtime: native-linux", rendered)
        self.assertIn("WINDOWS_WSL_NOT_APPLICABLE", rendered)
        self.assertIn("WINDOWS_PORTPROXY_NOT_APPLICABLE", rendered)

    async def test_unsupported_host_stops_before_network_or_incus_probes(self):
        probe = _UnsupportedHostProbe()

        report = await NetworkDoctorService(
            probe,
            _sample_port_registry(),
        ).run()

        rendered = report.render()
        self.assertFalse(report.passed)
        self.assertIn("Runtime: wsl1_unsupported", rendered)
        self.assertIn("RUNTIME_HOST_UNSUPPORTED", rendered)
        self.assertIn("Upgrade to WSL2", rendered)
        self.assertEqual(probe.non_runtime_calls, [])

    async def test_wsl_mirrored_runtime_reports_runtime_repair_hint(self):
        report = await NetworkDoctorService(
            _MirroredRuntimeProbe(),
            _sample_port_registry(),
        ).run()

        rendered = report.render()

        self.assertTrue(report.passed)
        self.assertIn("WSL2_MIRRORED", rendered)

    async def test_wsl_host_dns_failure_blocks_final_diagnosis(self):
        report = await NetworkDoctorService(
            _WslDnsBrokenProbe(),
            _sample_port_registry(),
        ).run()

        rendered = report.render()

        self.assertFalse(report.passed)
        self.assertIn("WSL_DNS_BROKEN", rendered)
        self.assertIn("Final diagnosis: FAILED", rendered)

    async def test_unavailable_incus_bridge_suggests_incus_repair(self):
        report = await NetworkDoctorService(
            _UnavailableIncusBridgeProbe(),
            _sample_port_registry(),
        ).run()

        rendered = report.render()

        self.assertFalse(report.passed)
        self.assertIn("INCUSBR0_UNAVAILABLE", rendered)
        self.assertIn("./tsw network repair --incus --apply", rendered)

    async def test_missing_incus_command_skips_lxc_nodes(self):
        report = await NetworkDoctorService(
            _IncusMissingProbe(),
            _sample_port_registry(),
        ).run()

        rendered = report.render()

        self.assertFalse(report.passed)
        self.assertIn("INCUS_NOT_INSTALLED", rendered)
        self.assertIn("LXC_SKIPPED", rendered)


class TestNetworkRepairService(unittest.IsolatedAsyncioTestCase):
    async def test_no_repair_target_blocks_without_mutation(self):
        repair = _RecordingRepair()
        report = await NetworkRepairService(
            _HealthyProbe(),
            repair,
        ).run(NetworkRepairOptions())

        self.assertFalse(report.succeeded)
        self.assertEqual(repair.calls, [])
        self.assertIn("No repair target was selected.", report.render())

    async def test_unsupported_runtime_repair_blocks(self):
        report = await NetworkRepairService(
            _HealthyProbe(),
            _RecordingRepair(),
        ).run(NetworkRepairOptions(runtime="native-linux"))

        self.assertFalse(report.succeeded)
        self.assertIn("Unsupported repair runtime", report.render())

    async def test_runtime_repair_skips_on_native_linux(self):
        report = await NetworkRepairService(
            _NativeLinuxProbe(),
            _RecordingRepair(),
        ).run(NetworkRepairOptions(runtime="wsl2-nat"))

        self.assertTrue(report.succeeded)
        self.assertIn("Runtime repair is only applicable inside WSL2.", report.render())

    async def test_runtime_repair_apply_calls_repair_adapter(self):
        repair = _RecordingRepair()
        report = await NetworkRepairService(
            _MirroredRuntimeProbe(),
            repair,
        ).run(NetworkRepairOptions(runtime="wsl2-nat", apply=True))

        self.assertTrue(report.succeeded)
        self.assertEqual(repair.calls, ["runtime"])

    async def test_runtime_repair_without_apply_only_reports_planned_wsl_nat_change(self):
        repair = _RecordingRepair()
        report = await NetworkRepairService(
            _MirroredRuntimeProbe(),
            repair,
        ).run(NetworkRepairOptions(runtime="wsl2-nat"))

        rendered = report.render()

        self.assertTrue(report.succeeded)
        self.assertEqual(repair.calls, [])
        self.assertIn("- runtime: planned", rendered)
        self.assertIn("WSL is running in mirrored networking mode.", rendered)
        self.assertIn("./tsw network repair --runtime wsl2-nat --apply", rendered)

    async def test_incus_and_forwarding_dry_run_report_planned_steps(self):
        repair = _RecordingRepair()
        report = await NetworkRepairService(
            _HealthyProbe(),
            repair,
        ).run(NetworkRepairOptions(incus=True, linux_forwarding=True))

        rendered = report.render()

        self.assertTrue(report.succeeded)
        self.assertEqual(repair.calls, [])
        self.assertIn("- incus: planned", rendered)
        self.assertIn("- linux-forwarding: planned", rendered)

    async def test_linux_forwarding_apply_calls_repair_adapter(self):
        repair = _RecordingRepair()
        report = await NetworkRepairService(
            _HealthyProbe(),
            repair,
        ).run(NetworkRepairOptions(linux_forwarding=True, apply=True))

        self.assertTrue(report.succeeded)
        self.assertEqual(repair.calls, ["linux-forwarding:incusbr0:swarm-manager"])
        self.assertIn("- linux-forwarding: applied", report.render())


class _HealthyProbe:
    async def runtime(self) -> RuntimeObservation:
        return RuntimeObservation("wsl2", "nat", "172.22.1.20", "")

    async def wsl_host(self) -> WslHostObservation:
        return WslHostObservation(
            ip_addr=_ok("ip addr"),
            ip_route=_ok("ip route", "default via 172.22.0.1 dev eth0"),
            resolv_conf=_ok("cat /etc/resolv.conf", "nameserver 172.22.0.1"),
            ping_egress=_ok("ping"),
            dns_lookup=_ok("getent", "archive.ubuntu.com 91.189.91.82"),
            http_probe=_ok("curl", "HTTP/1.1 200 OK"),
        )

    async def incus(self) -> IncusObservation:
        return IncusObservation(
            version=_ok("incus version", "6.0"),
            network_list=_ok("incus network list", "incusbr0"),
            network_show=_ok("incus network show incusbr0", "ipv4.address: 10.1.2.1/24"),
            network_info=_ok("incus network info incusbr0", "State: Created"),
            bridge_addr=_ok("ip addr show incusbr0", "inet 10.1.2.1/24"),
            journal=_ok("journalctl"),
            dnsmasq_log=_ok("cat dnsmasq"),
            gateway_ipv4="10.1.2.1",
        )

    async def lxc_node(self, node_name: str, gateway_ipv4: str) -> LxcNodeObservation:
        return LxcNodeObservation(
            node_name=node_name,
            incus_list=_ok("incus list", node_name),
            ip_addr=_ok("ip addr"),
            ip_route=_ok("ip route", "default via 10.1.2.1 dev eth0"),
            resolv_conf=_ok("cat /etc/resolv.conf"),
            ping_gateway=_ok("ping gateway"),
            ping_egress=_ok("ping egress"),
            dns_lookup=_ok("getent"),
            http_probe=_ok("curl", "HTTP/1.1 200 OK"),
        )

    async def forwarding(self) -> ForwardingObservation:
        return ForwardingObservation(
            ip_forward=_ok("sysctl", "net.ipv4.ip_forward = 1"),
            iptables_forward=_ok(
                "iptables",
                "\n".join(
                    (
                        "-P FORWARD ACCEPT",
                        "-A FORWARD -i incusbr0 -j ACCEPT",
                        "-A FORWARD -o incusbr0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT",
                    )
                ),
            ),
            iptables_nat=_ok("iptables nat", "-A POSTROUTING -s 10.1.2.0/24 -o eth0 -j MASQUERADE"),
            nft_rules=_ok("nft"),
        )

    async def service_ports(self) -> ServicePortObservation:
        return ServicePortObservation(_ok("ss", "LISTEN 0 4096 127.0.0.1:10000 0.0.0.0:*"))


class _NativeLinuxProbe(_HealthyProbe):
    async def runtime(self) -> RuntimeObservation:
        return RuntimeObservation("native-linux", "not-applicable", "", "192.168.1.20")


class _UnsupportedHostProbe(_HealthyProbe):
    def __init__(self) -> None:
        self.non_runtime_calls: list[str] = []

    async def runtime(self) -> RuntimeObservation:
        return RuntimeObservation(
            "wsl1_unsupported",
            "not-applicable",
            "",
            "",
            remediation=("Upgrade to WSL2 or use native Linux.",),
        )

    async def wsl_host(self) -> WslHostObservation:
        self.non_runtime_calls.append("wsl_host")
        raise AssertionError("unsupported host must stop before WSL probes")

    async def incus(self) -> IncusObservation:
        self.non_runtime_calls.append("incus")
        raise AssertionError("unsupported host must stop before Incus probes")

    async def forwarding(self) -> ForwardingObservation:
        self.non_runtime_calls.append("forwarding")
        raise AssertionError("unsupported host must stop before forwarding probes")

    async def service_ports(self) -> ServicePortObservation:
        self.non_runtime_calls.append("service_ports")
        raise AssertionError("unsupported host must stop before service probes")


class _WslDnsBrokenProbe(_HealthyProbe):
    async def wsl_host(self) -> WslHostObservation:
        healthy = await super().wsl_host()
        return WslHostObservation(
            ip_addr=healthy.ip_addr,
            ip_route=healthy.ip_route,
            resolv_conf=healthy.resolv_conf,
            ping_egress=healthy.ping_egress,
            dns_lookup=_failed("getent", "not found"),
            http_probe=healthy.http_probe,
        )


class _IncusMissingProbe(_HealthyProbe):
    async def incus(self) -> IncusObservation:
        failed = _failed("incus version", "command not found")
        return IncusObservation(
            version=failed,
            network_list=_failed("skipped"),
            network_show=_failed("skipped"),
            network_info=_failed("skipped"),
            bridge_addr=_failed("skipped"),
            journal=_failed("skipped"),
            dnsmasq_log=_failed("skipped"),
        )


class _UnavailableIncusBridgeProbe(_HealthyProbe):
    async def incus(self) -> IncusObservation:
        return IncusObservation(
            version=_ok("incus version", "6.0"),
            network_list=_ok("incus network list", "incusbr0"),
            network_show=_ok("incus network show incusbr0", "incusbr0"),
            network_info=_ok("incus network info incusbr0", "State: unavailable"),
            bridge_addr=_failed("ip addr show incusbr0"),
            journal=_ok("journalctl", "dnsmasq failed"),
            dnsmasq_log=_ok("cat dnsmasq", "failed to bind DHCP socket"),
            gateway_ipv4="",
        )


class _HistoricalIncusJournalFailureProbe(_HealthyProbe):
    async def incus(self) -> IncusObservation:
        return IncusObservation(
            version=_ok("incus version", "6.0"),
            network_list=_ok("incus network list", "incusbr0 CREATED"),
            network_show=_ok("incus network show incusbr0", "ipv4.address: 10.1.2.1/24"),
            network_info=_ok("incus network info incusbr0", "State: up"),
            bridge_addr=_ok("ip addr show incusbr0", "inet 10.1.2.1/24"),
            journal=_ok("journalctl", "dnsmasq failed during an earlier restart"),
            dnsmasq_log=_ok("cat dnsmasq", ""),
            gateway_ipv4="10.1.2.1",
        )


class _ForwardingBlockedProbe(_HealthyProbe):
    async def lxc_node(self, node_name: str, gateway_ipv4: str) -> LxcNodeObservation:
        healthy = await super().lxc_node(node_name, gateway_ipv4)
        return LxcNodeObservation(
            node_name=healthy.node_name,
            incus_list=healthy.incus_list,
            ip_addr=healthy.ip_addr,
            ip_route=healthy.ip_route,
            resolv_conf=healthy.resolv_conf,
            ping_gateway=healthy.ping_gateway,
            ping_egress=healthy.ping_egress,
            dns_lookup=healthy.dns_lookup,
            http_probe=_failed("curl", "connect timed out"),
        )

    async def forwarding(self) -> ForwardingObservation:
        return ForwardingObservation(
            ip_forward=_ok("sysctl", "net.ipv4.ip_forward = 1"),
            iptables_forward=_ok(
                "iptables",
                "\n".join(("-P FORWARD DROP", "-A FORWARD -j DOCKER-USER")),
            ),
            iptables_nat=_ok("iptables nat", "-A POSTROUTING -s 10.1.2.0/24 -o eth0 -j MASQUERADE"),
            nft_rules=_ok("nft"),
        )


class _MirroredRuntimeProbe(_HealthyProbe):
    async def runtime(self) -> RuntimeObservation:
        return RuntimeObservation("wsl2", "mirrored", "172.22.1.20", "")


class _RecordingRepair:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def apply_wsl2_nat_runtime(self) -> NetworkRepairMutationResult:
        self.calls.append("runtime")
        return NetworkRepairMutationResult(
            "runtime",
            applied=True,
            success=True,
            message="runtime applied",
        )

    async def apply_incus_repair(self) -> NetworkRepairMutationResult:
        self.calls.append("incus")
        return NetworkRepairMutationResult(
            "incus",
            applied=True,
            success=True,
            message="incus applied",
        )

    async def apply_linux_forwarding(self, bridge: str, node_name: str) -> NetworkRepairMutationResult:
        self.calls.append(f"linux-forwarding:{bridge}:{node_name}")
        return NetworkRepairMutationResult(
            "linux-forwarding",
            applied=True,
            success=True,
            message="forwarding applied",
        )


def _sample_port_registry() -> PortRegistry:
    return PortRegistry(
        ranges=(PortRange("diagnostic", 10000, 19999),),
        mappings=(
            ServicePortMapping(
                service_id="service-access",
                port_id="service-access-http",
                internal_port=80,
                external_port=10000,
                exposure=PortExposureClass.DIAGNOSTIC,
                range_id="diagnostic",
            ),
        ),
    )


def _ok(command: str, stdout: str = "") -> CommandObservation:
    return CommandObservation(command, 0, stdout=stdout)


def _failed(command: str, stderr: str = "") -> CommandObservation:
    return CommandObservation(command, 1, stderr=stderr)


if __name__ == "__main__":
    unittest.main()
