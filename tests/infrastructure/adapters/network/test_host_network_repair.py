import unittest
from pathlib import Path

from tiny_swarm_world.infrastructure.adapters.network import host_network_repair


class TestHostNetworkRepair(unittest.TestCase):
    def test_set_wsl_networking_mode_updates_existing_wsl2_section(self):
        content = "[wsl2]\nmemory=8GB\nnetworkingMode=mirrored\n[experimental]\nautoMemoryReclaim=gradual\n"

        updated = host_network_repair._set_wsl_networking_mode(content, "nat")

        self.assertIn("[wsl2]\nmemory=8GB\nnetworkingMode=nat\n", updated)
        self.assertIn("[experimental]\nautoMemoryReclaim=gradual", updated)
        self.assertNotIn("networkingMode=mirrored", updated)

    def test_set_wsl_networking_mode_adds_wsl2_section(self):
        updated = host_network_repair._set_wsl_networking_mode("[experimental]\nfoo=bar\n", "nat")

        self.assertTrue(updated.endswith("[wsl2]\nnetworkingMode=nat\n"))

    def test_forwarding_script_contains_scoped_idempotent_rules(self):
        script = host_network_repair._forwarding_script()
        service = host_network_repair._forwarding_service()

        self.assertIn('iptables -C FORWARD -i "$BRIDGE" -j ACCEPT', script)
        self.assertIn('iptables -C FORWARD -o "$BRIDGE" -m conntrack', script)
        self.assertIn("tsw-apply-incus-forwarding.sh", service)
        self.assertIn("RemainAfterExit=yes", service)

    def test_incus_runtime_file_guard_accepts_only_expected_pid_path(self):
        self.assertTrue(
            host_network_repair._inside_incus_network_dir(
                "/var/lib/incus/networks/incusbr0/dnsmasq.pid"
            )
        )
        self.assertFalse(host_network_repair._inside_incus_network_dir("/tmp/dnsmasq.pid"))
        self.assertFalse(
            host_network_repair._inside_incus_network_dir(
                "/var/lib/incus/networks/other/dnsmasq.pid"
            )
        )

    def test_windows_scripts_read_ports_from_registry(self):
        root = Path(__file__).resolve().parents[4]
        repair_script = root / "tools" / "windows" / "repair-wsl-portproxy.ps1"
        doctor_script = root / "tools" / "windows" / "doctor-portproxy.ps1"

        for script in (repair_script, doctor_script):
            text = script.read_text(encoding="utf-8")
            self.assertIn("infra\\config\\ports.yaml", text)
            self.assertIn("Get-TswBridgePorts", text)
            self.assertNotIn("$ports = @(", text)


if __name__ == "__main__":
    unittest.main()
