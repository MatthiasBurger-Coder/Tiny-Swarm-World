from ipaddress import ip_network
import json
import subprocess
import unittest
from unittest.mock import patch

from tiny_swarm_world.application.ports.network_preparation import NetworkPreparationFailure
from tiny_swarm_world.infrastructure.adapters.network_preparation.firewall import (
    Bridge, parse_rules, verify_no_foreign_denies,
)
from tiny_swarm_world.infrastructure.adapters.network_preparation.nat_conflicts import verify
from tiny_swarm_world.infrastructure.adapters.network_preparation.persistence_guard import render_guard
from tiny_swarm_world.infrastructure.adapters.network_preparation.tailscale_policy import (
    compatibility_projection, verify_tailscale,
)
from modules.tsw_core.tests.test_network_preparation import nft_fixture, BRIDGE as BOOT_BRIDGE


BRIDGE = Bridge("incusbr0", "10.10.0.0/24", "10.10.0.1", "eth0")
SAVED = """*filter
:FORWARD ACCEPT [0:0]
-A INPUT -j ts-input
-A FORWARD -j ts-forward
-A ts-forward -i tailscale0 -j MARK --set-xmark 0x40000/0xff0000
-A ts-forward -m mark --mark 0x40000/0xff0000 -j ACCEPT
-A ts-forward -s 100.64.0.0/10 -o tailscale0 -j DROP
-A ts-forward -o tailscale0 -j ACCEPT
-A ts-input -s 100.64.0.2/32 -i lo -j ACCEPT
-A ts-input -i tailscale0 -j ACCEPT
-A ts-input -p udp -m udp --dport 41641 -j ACCEPT
-A ts-input -s 100.115.92.0/23 ! -i tailscale0 -j RETURN
-A ts-input -s 100.64.0.0/10 ! -i tailscale0 -j DROP
COMMIT
*nat
-A POSTROUTING -j ts-postrouting
-A ts-postrouting -m mark --mark 0x40000/0xff0000 -j MASQUERADE
COMMIT
"""
CONNMARK = """*mangle
-A PREROUTING -m conntrack --ctstate RELATED,ESTABLISHED -m connmark ! --mark 0x0/0xff0000 -j CONNMARK --restore-mark --nfmask 0xff0000 --ctmask 0xff0000
-A OUTPUT -m conntrack --ctstate NEW -m mark ! --mark 0x0/0xff0000 -j CONNMARK --save-mark --nfmask 0xff0000 --ctmask 0xff0000
COMMIT
"""


class TailscaleOwnershipTests(unittest.TestCase):
    def test_exact_disjoint_rules_are_preserved(self):
        rules = parse_rules(SAVED)
        self.assertTrue(verify_tailscale(rules, (BRIDGE,)))
        projected = compatibility_projection(SAVED, (BRIDGE,))
        verify(projected, (BRIDGE,), (80, 443))
        verify_no_foreign_denies(parse_rules(projected), ufw=False, bridges=(BRIDGE,))

    def test_other_masquerade_still_blocks(self):
        competing = SAVED.removesuffix("COMMIT\n") + (
            "-A POSTROUTING -s 10.10.0.0/24 ! -o incusbr0 -j MASQUERADE\nCOMMIT\n"
        )
        self.assertTrue(verify_tailscale(parse_rules(competing), (BRIDGE,)))
        with self.assertRaisesRegex(NetworkPreparationFailure, "Competing existing NAT"):
            verify(compatibility_projection(competing, (BRIDGE,)), (BRIDGE,), (80, 443))

    def test_exact_connection_mark_pair_is_preserved(self):
        self.assertTrue(verify_tailscale(parse_rules(SAVED + CONNMARK), (BRIDGE,)))
        for bad in (
            CONNMARK.replace("--ctstate RELATED,ESTABLISHED", "--ctstate NEW"),
            CONNMARK.replace("--ctmask 0xff0000", "--ctmask 0xffffffff"),
            "\n".join(line for line in CONNMARK.splitlines() if not line.startswith("-A OUTPUT")),
        ):
            with self.subTest(bad=bad), self.assertRaises(NetworkPreparationFailure):
                verify_tailscale(parse_rules(SAVED + bad), (BRIDGE,))

    def test_unknown_rules_and_mark_sources_block(self):
        for before, after in (
            ("-i tailscale0 -j MARK", "-i incusbr0 -j MARK"),
            ("-A POSTROUTING -j ts-postrouting", "-A OUTPUT -j ts-postrouting"),
            ("--mark 0x40000/0xff0000 -j MASQUERADE", "--mark 0x40000/0xffff00 -j MASQUERADE"),
            ("-A FORWARD -j ts-forward", "-A FORWARD -j ts-forward\n-A FORWARD -j ts-forward"),
            ("-A FORWARD -j ts-forward", "-A FORWARD -j ts-forward\n-A FORWARD -j CONNMARK --restore-mark"),
            ("-s 100.64.0.2/32 -i lo", "-s 0.0.0.0/0 -i lo"),
            ("-o tailscale0 -j DROP", "-o eth0 -j DROP"),
        ):
            with self.subTest(before=before), self.assertRaises(NetworkPreparationFailure):
                verify_tailscale(parse_rules(SAVED.replace(before, after)), (BRIDGE,))

    def test_managed_subnet_and_egress_must_be_disjoint(self):
        for bridge in (
            Bridge("incusbr0", BRIDGE.subnet, BRIDGE.gateway, "tailscale0"),
            Bridge("incusbr0", str(ip_network("100.64.0.0/24")), "100.64.0.1", BRIDGE.egress),
        ):
            with self.subTest(bridge=bridge), self.assertRaisesRegex(NetworkPreparationFailure, "overlaps"):
                verify_tailscale(parse_rules(SAVED), (bridge,))


    def test_only_exact_disjoint_docker_raw_denies_are_projected(self):
        raw = "-A PREROUTING -d 172.18.0.2/32 ! -i docker0 -j DROP"
        saved = (SAVED.replace("-A INPUT -j ts-input", "-A INPUT -j ts-input\n"
                 "-A DOCKER-BRIDGE -o docker0 -j DOCKER\n"
                 "-A DOCKER -d 172.18.0.2/32 ! -i docker0 -o docker0 "
                 "-p tcp -m tcp --dport 8081 -j ACCEPT") + f"*raw\n{raw}\nCOMMIT\n")
        self.assertNotIn(raw, compatibility_projection(saved, (BRIDGE,)))
        for broken, bridge in (
            (saved.replace("-A DOCKER-BRIDGE -o docker0 -j DOCKER", ""), BRIDGE),
            (saved.replace("--dport 8081", "--dport 8081 !"), BRIDGE),
            (saved, Bridge("incusbr0", "172.18.0.0/16", "172.18.0.1", "eth0")),
        ):
            with self.subTest(bridge=bridge):
                self.assertIn(raw, compatibility_projection(broken, (bridge,)))

    def test_existing_strict_guard_keeps_its_original_path(self):
        self.assertNotIn("compatibility_projection", render_guard((BOOT_BRIDGE,), False))

    def test_embedded_guard_revalidates_exact_compatibility(self):
        nft = nft_fixture()
        saved = SAVED.replace(":FORWARD ACCEPT [0:0]", ":FORWARD ACCEPT [0:0]\n:OUTPUT ACCEPT [0:0]") + CONNMARK
        for chain, entries in parse_rules(saved).items():
            table, _, name = chain.partition(":")
            if not name:
                table, name = "filter", table
            nft["nftables"].extend(
                {"rule": {"family": "ip", "table": table, "chain": name}}
                for _ in entries
            )
        guard = render_guard((BOOT_BRIDGE,), False, compatibility=True)
        source = guard.split("\n", 1)[1].rsplit("\nTSW_GUARD", 1)[0]

        def run(args, **kwargs):
            outputs = {
                "iptables": "iptables v1.8 (nf_tables)",
                "systemctl": "ActiveState=inactive\nUnitFileState=disabled\n",
                "ufw": "Status: inactive\n", "iptables-save": saved,
                "nft": json.dumps(nft), "ip": '[{"dst":"default","dev":"eth0"}]',
            }
            if args[:3] == ["ip", "-j", "address"]:
                return subprocess.CompletedProcess(args, 0, json.dumps([{
                    "ifname": BOOT_BRIDGE.name,
                    "addr_info": [{"family": "inet", "local": BOOT_BRIDGE.gateway, "prefixlen": 24}],
                }]), "")
            return subprocess.CompletedProcess(args, 0, outputs[args[0]], "")

        with patch("subprocess.run", side_effect=run):
            exec(compile(source, "<forwarding-compatibility-guard>", "exec"), {})
            saved = saved.replace("-i tailscale0 -j MARK", "-i incusbr0 -j MARK")
            with self.assertRaisesRegex(RuntimeError, "Unrecognized Tailscale"):
                exec(compile(source, "<forwarding-compatibility-guard>", "exec"), {})
