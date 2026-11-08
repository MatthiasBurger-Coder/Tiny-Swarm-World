"""Regression coverage for fresh nft hosts and Incus 6.0 LTS rules."""
import copy
import tempfile
import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from modules.tsw_core.tests.test_network_preparation import BRIDGE, MockHost, PACKAGE, ROOT, nft_fixture
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


# Authoritative preserved owners are deliberately separate from configured targets.
OTHER = Bridge("qualbr447", "10.231.51.0/24", "10.231.51.1", "eth0")


def two_bridge_fixture(*, legacy=False):
    original = legacy_fixture() if legacy else nft_fixture()
    value = copy.deepcopy(original)
    extra = copy.deepcopy(original)
    def substitute(item):
        if isinstance(item, dict):
            return {key: substitute(child) for key, child in item.items()}
        if isinstance(item, list):
            return [substitute(child) for child in item]
        if isinstance(item, str):
            return item.replace("incusbr0", "qualbr447").replace("10.231.50.", "10.231.51.")
        return item
    extra = substitute(extra)
    value["nftables"].extend(entry for entry in extra["nftables"] if "set" not in entry)
    if not legacy:
        next(entry["set"] for entry in value["nftables"] if "set" in entry)["elem"] = ["incusbr0", "qualbr447"]
    return value


def owner_observations():
    networks = [{"name": bridge.name, "managed": True, "project": "default", "type": "bridge", "status": "Created",
                 "config": {"ipv4.address": bridge.gateway + "/24", "ipv4.nat": "true", "ipv4.dhcp": "true", "ipv6.address": "none"}}
                for bridge in (BRIDGE, OTHER)]
    links = [{"ifname": bridge.name, "linkinfo": {"info_kind": "bridge"},
              "addr_info": [{"family": "inet", "local": bridge.gateway, "prefixlen": 24}]}
             for bridge in (BRIDGE, OTHER)]
    return networks, links


class PreservedManagedBridgeTests(unittest.IsolatedAsyncioTestCase):
    def test_two_explicit_owners_allow_exact_legacy_and_full_modern_sets(self):
        from tiny_swarm_world.infrastructure.adapters.network_preparation.configuration import managed_bridge_owners
        networks, links = owner_observations()
        owners = managed_bridge_owners(networks, links, "eth0")
        self.assertEqual(owners, (BRIDGE, OTHER))
        for legacy in (False, True):
            value = two_bridge_fixture(legacy=legacy)
            verify_nft(value, (BRIDGE,), owners=owners)
            with self.assertRaises(NetworkPreparationFailure):
                verify_nft(value, (BRIDGE,))  # A name/table alone never grants owner scope.
        self.assertEqual(networks[1]["name"], "qualbr447")
        networks[1]["config"]["ipv4.dhcp"] = "false"
        self.assertEqual(managed_bridge_owners(networks, links, "eth0"), owners)
        # The unselected owner does not inherit the target's DHCP configuration contract.

    async def test_real_plan_never_generates_forwarding_or_nat_for_unselected_owner(self):
        from tiny_swarm_world.infrastructure.adapters.network_preparation.adapter import LocalNetworkPreparation
        from tiny_swarm_world.infrastructure.adapters.network_preparation.firewall import forwarding_rules
        from tiny_swarm_world.infrastructure.adapters.network_preparation.forwarding import render_script
        with tempfile.TemporaryDirectory() as directory:
            host = MockHost(Path(directory))
            host.networks, host.links = owner_observations()
            host.links.append({"ifname": "eth0", "addr_info": [{"family": "inet", "local": "172.20.1.2", "prefixlen": 20}]})
            host.nft = two_bridge_fixture(legacy=True)
            adapter = LocalNetworkPreparation(ROOT, ROOT / "infra/config", release="24.04", profile="service-access",
                        proc_root=host.proc, target_snapshot=lambda: (host.source,), evidence=Mock())
            with host.patches():
                plan = await adapter.inspect()
                self.assertFalse(plan.blockers)
                targets, firewall = adapter._payloads["forwarding:rules"]
                self.assertEqual(targets, (BRIDGE,))
            firewall["desired_rules"] = tuple(("FORWARD", rule) for rule in forwarding_rules(BRIDGE))
            script = render_script((BRIDGE,), firewall).decode()
            effect_lines = [line for line in script.splitlines() if line.startswith("timeout 5 iptables")]
            self.assertEqual(len(effect_lines), 3)
            self.assertTrue(all("incusbr0" in line and "qualbr447" not in line for line in effect_lines))
            self.assertTrue(all("MASQUERADE" not in line and "SNAT" not in line for line in effect_lines))
            self.assertTrue(all("qualbr447" not in rule for _chain, rule in firewall["missing"]))
            self.assertEqual(firewall["managed_bridge_owners"], (BRIDGE, OTHER))
            self.assertEqual(host.calls, [])

    def test_unknown_owner_kernel_ipv4_ipv6_or_overlap_is_refused(self):
        from tiny_swarm_world.infrastructure.adapters.network_preparation.configuration import managed_bridge_owners
        cases = ("managed", "project", "status", "type", "missing_link", "link_kind", "duplicate", "ipv4", "prefix", "ipv6", "overlap", "acl", "snat")
        for case in cases:
            networks, links = owner_observations()
            if case in {"managed", "project", "status", "type"}:
                networks[1][case] = {"managed": False, "project": "foreign", "status": "Pending", "type": "physical"}[case]
            elif case == "missing_link":
                links.pop()
            elif case == "link_kind":
                links[1]["linkinfo"]["info_kind"] = "dummy"
            elif case == "duplicate":
                networks.append(copy.deepcopy(networks[1]))
            elif case == "ipv4":
                links[1]["addr_info"][0]["local"] = "10.231.52.1"
            elif case == "prefix":
                links[1]["addr_info"][0]["prefixlen"] = True
            elif case == "ipv6":
                links[1]["addr_info"].append({"family": "inet6", "scope": "global", "local": "fd00::1", "prefixlen": 64})
            elif case == "overlap":
                networks[1]["config"]["ipv4.address"] = "10.231.50.2/24"
                links[1]["addr_info"][0]["local"] = "10.231.50.2"
            elif case == "acl":
                networks[1]["config"]["security.acls"] = "foreign"
            else:
                networks[1]["config"]["ipv4.nat.address"] = "192.0.2.1"
            with self.subTest(case=case):
                if case in {"managed", "type"}:
                    # Unmanaged/non-bridge visibility is not an owner. Its chains still fail.
                    owners = managed_bridge_owners(networks, links, "eth0")
                    with self.assertRaises(NetworkPreparationFailure):
                        verify_nft(two_bridge_fixture(legacy=True), (BRIDGE,), owners=owners)
                else:
                    with self.assertRaises(NetworkPreparationFailure):
                        managed_bridge_owners(networks, links, "eth0")

    def test_peer_chains_nat_and_counter_effects_are_fully_checked(self):
        for case in ("hook", "priority", "policy", "unknown", "missing", "extra_nat", "mixed_counter", "broad_source", "unknown_set"):
            value = two_bridge_fixture(legacy=True)
            peer = next(entry["chain"] for entry in value["nftables"] if entry.get("chain", {}).get("name") == "fwd.qualbr447")
            nat = next(entry["rule"] for entry in value["nftables"] if entry.get("rule", {}).get("chain") == "pstrt.qualbr447")
            if case in {"hook", "priority", "policy"}:
                peer[{"priority": "prio"}.get(case, case)] = {"hook": "prerouting", "priority": -100, "policy": "drop"}[case]
            elif case == "unknown":
                peer["name"] = "fwd.spoofed"
            elif case == "missing":
                value["nftables"] = [entry for entry in value["nftables"] if entry.get("chain", {}).get("name") != "in.qualbr447"]
            elif case == "extra_nat":
                nat["expr"].append({"accept": None})
            elif case == "mixed_counter":
                nat["expr"].append({"counter": {"packets": 0, "bytes": 0}, "mangle": {"key": "mark", "value": 1}})
            elif case == "broad_source":
                nat["expr"][0]["match"]["right"]["prefix"]["len"] = 0
            else:
                value["nftables"].append({"set": {"family": "inet", "table": "incus", "name": "foreign", "type": "ifname", "elem": []}})
            with self.subTest(case=case), self.assertRaises(NetworkPreparationFailure):
                verify_nft(value, (BRIDGE,), owners=(BRIDGE, OTHER))

    def test_preserved_filter_checksum_requires_exact_owner_and_udp_scope(self):
        checksum = {"mangle": {"key": {"payload": {"protocol": "udp", "field": "checksum"}}, "value": 0}}
        owner = {"match": {"op": "==", "left": {"meta": {"key": "iifname"}}, "right": "qualbr447"}}
        udp = {"match": {"op": "==", "left": {"payload": {"protocol": "ip", "field": "protocol"}}, "right": "udp"}}
        for expressions, valid in (([owner, udp, checksum], True), ([checksum], False), ([owner, checksum], False),
                                   ([owner, udp, checksum, {"accept": None}], False),
                                   ([owner, udp, {"counter": {"packets": 0, "bytes": 0}, "drop": None}], False)):
            value = two_bridge_fixture(legacy=True)
            value["nftables"].append({"rule": {"family": "inet", "table": "incus", "chain": "in.qualbr447", "expr": expressions}})
            if valid:
                verify_nft(value, (BRIDGE,), owners=(BRIDGE, OTHER))
            else:
                with self.assertRaises(NetworkPreparationFailure):
                    verify_nft(value, (BRIDGE,), owners=(BRIDGE, OTHER))

    def test_generated_guard_rechecks_complete_live_owner_set_before_target_writes(self):
        guard = render_guard((BRIDGE,), False, owners=(BRIDGE, OTHER))
        source = guard.split("\n", 1)[1].rsplit("\nTSW_GUARD", 1)[0]
        saved = "*filter\n:INPUT ACCEPT [0:0]\n:OUTPUT ACCEPT [0:0]\n:FORWARD DROP [0:0]\nCOMMIT\n"
        for drift in (None, "missing", "kernel", "pid", "new_owner"):
            networks, links = owner_observations()
            if drift == "missing":
                networks.pop()
            elif drift == "kernel":
                links[1]["linkinfo"]["info_kind"] = "dummy"
            elif drift == "new_owner":
                extra = copy.deepcopy(networks[1])
                extra.update(name="qualbr448")
                extra["config"]["ipv4.address"] = "10.231.52.1/24"
                networks.append(extra)
                links.append({"ifname": "qualbr448", "linkinfo": {"info_kind": "bridge"},
                              "addr_info": [{"family": "inet", "local": "10.231.52.1", "prefixlen": 24}]})
            observations = []
            def run(args, **kwargs):
                observations.append(args)
                if args[:3] == ["systemctl", "show", "incus.service"]:
                    count = sum(call[:3] == args[:3] for call in observations)
                    pid = 2 if drift == "pid" and count == 2 else 1
                    output = f"LoadState=loaded\nActiveState=active\nUnitFileState=enabled\nMainPID={pid}\n"
                elif args[0] == "/usr/bin/env":
                    self.assertIn("INCUS_CONF=/proc/self", args)
                    self.assertEqual(args[-1], "/1.0/networks?recursion=1&project=default")
                    output = json.dumps(networks)
                elif args[:4] == ["ip", "-j", "-d", "address"]:
                    output = json.dumps(links)
                elif args[:3] == ["ip", "-j", "address"]:
                    output = json.dumps([links[0]])
                else:
                    output = {"iptables": "iptables v1.8 (nf_tables)", "systemctl": "ActiveState=inactive\nUnitFileState=disabled\n",
                              "ufw": "Status: inactive\n", "iptables-save": saved, "nft": json.dumps(two_bridge_fixture(legacy=True)),
                              "ip": '[{"dst":"default","dev":"eth0"}]'}[args[0]]
                return subprocess.CompletedProcess(args, 0, output, "")
            with self.subTest(drift=drift), patch("subprocess.run", side_effect=run):
                if drift is None:
                    exec(compile(source, "<preserving-owner-guard>", "exec"), {})
                else:
                    with self.assertRaises(RuntimeError):
                        exec(compile(source, "<preserving-owner-guard>", "exec"), {})
            self.assertFalse(any(args[0] in {"iptables", "nft"} and any(flag in args for flag in ("-I", "-A", "-f")) for args in observations))
