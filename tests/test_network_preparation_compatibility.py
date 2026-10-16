"""Regression coverage for fresh nft hosts and Incus 6.0 LTS rules."""
import copy
import tempfile
import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.test_network_preparation import BRIDGE, MockHost, PACKAGE, nft_fixture
from tiny_swarm_world.application.ports.network_preparation import NetworkPreparationFailure
from tiny_swarm_world.infrastructure.adapters.network_preparation.firewall import Bridge
from tiny_swarm_world.infrastructure.adapters.network_preparation.persistence_guard import render_guard
from tiny_swarm_world.infrastructure.adapters.network_preparation.firewall_inventory import inventory, verify_nft


def legacy_fixture():
    value = nft_fixture()
    value["nftables"] = [entry for entry in value["nftables"]
                         if "set" not in entry and not any(
                             "accept" in expression for expression in entry.get("rule", {}).get("expr", []))]
    return value


class FirewallCompatibilityTests(unittest.IsolatedAsyncioTestCase):
    async def test_fresh_nft_host_uses_explicit_filter_without_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            host = MockHost(Path(directory))
            host.nft = legacy_fixture()
            reads = []

            async def privileged(args, timeout=5):
                reads.append(args)
                if args == ("iptables-save",):
                    return ""
                if args == ("iptables-save", "-t", "filter"):
                    return host.saved()
                return await host.privileged(args, timeout)

            with host.patches(), patch(PACKAGE + ".runtime.privileged", side_effect=privileged):
                result = await inventory((BRIDGE,))
            self.assertIn(("iptables-save", "-t", "filter"), reads)
            self.assertEqual(len(result["missing"]), 3)
            self.assertEqual(host.calls, [])

    async def test_partial_dump_is_rejected_without_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            host = MockHost(Path(directory))
            reads = []

            async def privileged(args, timeout=5):
                reads.append(args)
                return "*filter\n:INPUT DROP [0:0]\n" if args == ("iptables-save",) else await host.privileged(args, timeout)

            with host.patches(), patch(PACKAGE + ".runtime.privileged", side_effect=privileged):
                with self.assertRaisesRegex(NetworkPreparationFailure, "Incomplete iptables"):
                    await inventory((BRIDGE,))
            self.assertNotIn(("iptables-save", "-t", "filter"), reads)

    def test_exact_legacy_nat_and_current_pair_are_supported(self):
        verify_nft(legacy_fixture(), (BRIDGE,))
        verify_nft(nft_fixture(), (BRIDGE,))

    def test_legacy_nat_must_not_broaden_or_add_effects(self):
        for mutation in ("source", "destination", "verdict", "extra", "duplicate", "missing"):
            with self.subTest(mutation=mutation):
                value = legacy_fixture()
                expressions = value["nftables"][-1]["rule"]["expr"]
                if mutation == "source":
                    expressions[0]["match"]["right"]["prefix"]["len"] = 0
                elif mutation == "destination":
                    expressions[1]["match"]["op"] = "=="
                elif mutation == "verdict":
                    expressions[-1] = {"snat": {"addr": "192.0.2.1"}}
                elif mutation == "extra":
                    expressions.append({"accept": None})
                elif mutation == "duplicate":
                    value["nftables"].append(copy.deepcopy(value["nftables"][-1]))
                else:
                    value["nftables"].pop()
                with self.assertRaises(NetworkPreparationFailure):
                    verify_nft(value, (BRIDGE,))

    def test_legacy_nat_is_not_assumed_safe_for_multiple_bridges(self):
        other = Bridge("incusbr1", "10.231.51.0/24", "10.231.51.1", "eth0")
        with self.assertRaises(NetworkPreparationFailure):
            verify_nft(legacy_fixture(), (BRIDGE, other))

    def test_persisted_guard_handles_fresh_filter_and_legacy_nat(self):
        guard = render_guard((BRIDGE,), False, absent=True)
        source = guard.split("\n", 1)[1].rsplit("\nTSW_GUARD", 1)[0]
        saved = "*filter\n:INPUT ACCEPT [0:0]\n:OUTPUT ACCEPT [0:0]\n:FORWARD ACCEPT [0:0]\nCOMMIT\n"

        def run(args, **kwargs):
            if args == ["iptables-save"]:
                output = ""
            elif args == ["iptables-save", "-t", "filter"]:
                output = saved
            elif args[0] == "iptables":
                output = "iptables v1.8.11 (nf_tables)"
            elif args[0] == "systemctl":
                output = "ActiveState=inactive\nUnitFileState=disabled\n"
            elif args[0] == "nft":
                output = json.dumps(legacy_fixture())
            elif args[:3] == ["ip", "-j", "address"]:
                output = json.dumps([{"addr_info": [{"family": "inet", "local": BRIDGE.gateway, "prefixlen": 24}]}])
            elif args[0] == "ip":
                output = '[{"dst":"default","dev":"eth0"}]'
            else:
                raise AssertionError(args)
            return subprocess.CompletedProcess(args, 0, output, "")

        with patch("subprocess.run", side_effect=run), patch("pathlib.Path.exists", return_value=False):
            exec(compile(source, "<root-owned-forwarding-guard>", "exec"), {})
