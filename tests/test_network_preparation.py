"""Fresh preparation through real use case/configuration owners, mocked host I/O."""
from __future__ import annotations

import copy
import hashlib
import json
import shlex
import tempfile
import shutil
import subprocess
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import asyncio
from contextlib import ExitStack

from tiny_swarm_world.application.ports.network_preparation import NetworkPreparationFailure
from tiny_swarm_world.application.services.network_preparation import NetworkPreparationService
from tiny_swarm_world.infrastructure.adapters.network_preparation.adapter import LocalNetworkPreparation
from tiny_swarm_world.infrastructure.adapters.network_preparation.files import FileObservation
from tiny_swarm_world.infrastructure.adapters.network_preparation.firewall import Bridge, forwarding_rules, input_rules
from tiny_swarm_world.infrastructure.adapters.network_preparation.firewall_inventory import verify_nft
from tiny_swarm_world.infrastructure.adapters.network_preparation.firewall import exact_present, parse_rules, verify_no_foreign_denies
from tiny_swarm_world.infrastructure.adapters.network_preparation.firewall import equivalent
from tiny_swarm_world.infrastructure.adapters.network_preparation.linux_plan import CONTROLS
from tiny_swarm_world.infrastructure.adapters.network_preparation.windows import WindowsNetworkPreparation
from tiny_swarm_world.infrastructure.adapters.network_preparation.configuration import verify_listeners
from tiny_swarm_world.infrastructure.adapters.network_preparation.source_identity import preparation_asset_hashes
from tiny_swarm_world.infrastructure.adapters.network_preparation.persistence_guard import render_guard
from tiny_swarm_world.infrastructure.adapters.network_preparation.firewall_inventory import ufw_status
from tiny_swarm_world.application.ports.host.port_windows_command_runner import WindowsCommandResult

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "tiny_swarm_world.infrastructure.adapters.network_preparation"
INCUS = "tiny_swarm_world.infrastructure.adapters.incus_preparation.runtime"
BRIDGE = Bridge("incusbr0", "10.231.50.0/24", "10.231.50.1", "eth0")


def nft_fixture():
    subnet = {"prefix": {"addr": "10.231.50.0", "len": 24}}
    entries = [{"chain": {"family": "inet", "table": "incus", "name": prefix + "incusbr0",
                           "type": kind, "hook": hook, "prio": priority, "policy": "accept"}}
               for prefix, kind, hook, priority in (("in.", "filter", "input", 0), ("out.", "filter", "output", 0),
                                                     ("fwd.", "filter", "forward", 0), ("pstrt.", "nat", "postrouting", 100))]
    entries.append({"set": {"family": "inet", "table": "incus", "name": "bridges", "type": "ifname", "elem": ["incusbr0"]}})
    entries.append({"rule": {"family": "inet", "table": "incus", "chain": "pstrt.incusbr0", "expr": [
        {"match": {"op": "==", "left": {"payload": {"protocol": "ip", "field": "saddr"}}, "right": subnet}},
        {"match": {"op": "==", "left": {"meta": {"key": "oifname"}}, "right": "@bridges"}}, {"accept": None}]}})
    entries.append({"rule": {"family": "inet", "table": "incus", "chain": "pstrt.incusbr0", "expr": [
        {"match": {"op": "==", "left": {"payload": {"protocol": "ip", "field": "saddr"}}, "right": subnet}},
        {"match": {"op": "!=", "left": {"payload": {"protocol": "ip", "field": "daddr"}}, "right": subnet}},
        {"masquerade": None}]}})
    return {"nftables": entries}


class MockHost:
    def __init__(self, proc, *, ufw=False):
        self.proc = proc
        self.ufw = ufw
        self.files = {"/etc/hosts": (b"127.0.0.1 localhost\n192.0.2.7 keep.example\n", 0o644)}
        self.calls = []
        self.rules = {"FORWARD": [], "INPUT": []}
        self.enabled = False
        self.source = "trusted-source"
        self.nft = nft_fixture()
        self.denied = False
        self.listening = ""
        self.networks = [{"name": "incusbr0", "managed": True, "type": "bridge", "status": "Created",
                          "config": {"ipv4.address": "10.231.50.1/24", "ipv4.nat": "true",
                                     "ipv4.dhcp": "true", "ipv6.address": "none"}}]
        self.routes = [{"dst": "default", "dev": "eth0"}]
        self.links = [{"ifname": "eth0", "addr_info": [{"family": "inet", "local": "172.20.1.2", "prefixlen": 20}]}]

    def observe(self, path):
        content, mode = self.files.get(str(path), (b"", 0o644))
        return FileObservation(str(path) in self.files, content, hashlib.sha256(content).hexdigest(), mode, 0, 0)

    async def install(self, path, before, content, mode, **kwargs):
        self.calls.append(("file", str(path)))
        if self.observe(path) != before:
            raise RuntimeError("target drift")
        self.files[str(path)] = (content, mode)

    async def query(self, path):
        return copy.deepcopy(self.networks if "/networks?" in path else [])

    async def host_json(self, args):
        return copy.deepcopy(self.routes if "route" in args else self.links)

    async def nft_json(self, args, **kwargs):
        result = copy.deepcopy(self.nft)
        for chain, rules in parse_rules(self.saved()).items():
            table, name = ("filter", chain) if ":" not in chain else chain.split(":", 1)
            result["nftables"] += [{"rule": {"family": "ip", "table": table, "chain": name, "expr": []}} for rule in rules]
        return result

    def saved(self):
        lines = ["*filter", ":INPUT " + ("DROP" if self.ufw else "ACCEPT") + " [0:0]", ":OUTPUT ACCEPT [0:0]", ":FORWARD DROP [0:0]"]
        if self.ufw:
            lines += ["-A INPUT -j ufw-before-input", "-A FORWARD -j ufw-before-forward", "-A ufw-before-forward -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT",
                      "-A ufw-before-input -m conntrack --ctstate INVALID -j DROP",
                      "-A ufw-before-input -j ufw-not-local",
                      *["-A ufw-not-local -m addrtype --dst-type " + kind + " -j RETURN" for kind in ("LOCAL", "MULTICAST", "BROADCAST")],
                      "-A ufw-not-local -j DROP", "-A ufw-before-forward -j ufw-user-forward",
                      "-A ufw-before-input -j ufw-user-input"]
        for chain, rules in self.rules.items():
            actual = "ufw-user-forward" if self.ufw and chain == "FORWARD" else "ufw-user-input" if self.ufw else chain
            lines += ["-A " + actual + " " + shlex.join(rule) for rule in rules]
        if self.denied:
            lines += ["-A FORWARD -s 10.231.50.0/24 -j DROP"]
        return "\n".join(lines + ["COMMIT"]) + "\n"

    async def command(self, args, timeout=5, **kwargs):
        if args == ("iptables", "--version"):
            return "iptables v1.8.10 (nf_tables)"
        if args[0] == "systemctl" and "firewalld.service" in args:
            return "ActiveState=inactive\nUnitFileState=disabled\n"
        if args[0] == "systemctl":
            return "UnitFileState=" + ("enabled" if self.enabled else "not-found")
        if args[0] == "ss":
            return self.listening
        if args[0] == "getent":
            name = args[-1]
            hosts = self.files["/etc/hosts"][0].decode()
            return "127.0.0.1 STREAM " + name + "\n" if name in hosts else ""
        if args[0] == "modinfo":
            return "filename: br_netfilter.ko"
        raise AssertionError(args)

    async def privileged(self, args, timeout=5):
        if args[0] == "ss":
            return self.listening
        if args == ("iptables-save",):
            return self.saved()
        if args[:2] == ("ufw", "status"):
            return "Status: active\nDefault: deny (incoming), allow (outgoing), deny (routed)\n" if self.ufw else "Status: inactive\n"
        if args[:3] == ("ufw", "show", "added"):
            return "Existing user configuration preserved\n"
        self.calls.append(args)
        if args[0] == "modprobe":
            for control in CONTROLS:
                path = self.proc / control.replace(".", "/")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("0\n")
        elif args[0] == "sysctl":
            name = args[-1].split("=")[0]
            (self.proc / name.replace(".", "/")).write_text("1\n")
        elif args[0] == "iptables":
            self.rules[args[4]].insert(0, args[6:])
        elif args[0] == "ufw":
            tag = args[-1]
            candidates = (("FORWARD", rule) for rule in forwarding_rules(BRIDGE)[:2])
            candidates = list(candidates) + [("INPUT", rule) for rule in input_rules(BRIDGE)]
            chain, rule = next((chain, rule) for chain, rule in candidates if tag in rule)
            self.rules[chain].append(rule)
        elif args[:2] == ("systemctl", "enable"):
            self.enabled = True
        return ""

    def patches(self):
        stack = ExitStack()
        for target, value in ((PACKAGE + ".runtime.command", self.command),
                              (PACKAGE + ".runtime.privileged", self.privileged),
                              (PACKAGE + ".runtime.json_command", self.nft_json),
                              (PACKAGE + ".files.observe", self.observe),
                              (PACKAGE + ".files.install", self.install),
                              (INCUS + ".query", self.query), (INCUS + ".json_command", self.host_json)):
            stack.enter_context(patch(target, side_effect=value))
        async def ufw_inventory():
            return await self.privileged(("ufw", "status", "verbose"))
        stack.enter_context(patch(PACKAGE + ".firewall_inventory.ufw_status", side_effect=ufw_inventory))
        stack.enter_context(patch(INCUS + ".daemon_state", return_value={"ActiveState": "active"}))
        return stack


class NetworkPreparationTests(unittest.IsolatedAsyncioTestCase):
    async def test_stopped_daemon_does_not_query_or_activate_in_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            host = MockHost(Path(directory))
            adapter = LocalNetworkPreparation(ROOT, ROOT / "infra/config", release="24.04", profile="service-access",
                        proc_root=host.proc, target_snapshot=lambda: (host.source,), evidence=Mock())
            with host.patches(), patch(INCUS + ".daemon_state", return_value={"ActiveState": "inactive"}), patch(INCUS + ".query") as query:
                self.assertTrue((await adapter.inspect()).blockers)
                query.assert_not_called()
                self.assertEqual(host.calls, [])

    async def test_network_cli_read_only_and_eof_leave_state_evidence_untouched(self):
        from tiny_swarm_world.prepare_network import prepare
        with tempfile.TemporaryDirectory() as directory:
            host = MockHost(Path(directory))
            evidence = Mock()
            adapter = LocalNetworkPreparation(ROOT, ROOT / "infra/config", release="24.04", profile="service-access",
                        proc_root=host.proc, target_snapshot=lambda: (host.source,), evidence=evidence)
            with host.patches(), patch("tiny_swarm_world.prepare_network.build_network_preparation_service", return_value=NetworkPreparationService(adapter)), patch("builtins.input", side_effect=EOFError):
                self.assertEqual(await prepare(read_only=True, service_profile="service-access"), 2)
                self.assertEqual(await prepare(read_only=False, service_profile="service-access"), 2)
                self.assertEqual(host.calls, [])
                evidence.write.assert_not_called()

    async def test_missing_ufw_supported_only_when_config_service_rules_are_absent(self):
        path = Mock()
        path.is_file.return_value = False
        path.exists.return_value = False
        with patch(PACKAGE + ".firewall_inventory.Path", return_value=path), patch(PACKAGE + ".runtime.command", return_value="ActiveState=inactive\nUnitFileState=not-found\n"):
            self.assertEqual(await ufw_status(), "Status: absent")
            path.exists.return_value = True
            with self.assertRaises(NetworkPreparationFailure):
                await ufw_status()

    async def test_owned_proxy_requires_observed_incus_executable_provenance(self):
        instances = [{"name": "swarm-manager", "expanded_devices": {"tsw-proxy-443":
                     {"type": "proxy", "listen": "tcp:0.0.0.0:443", "connect": "tcp:127.0.0.1:443"}}}]
        output = 'LISTEN 0 128 0.0.0.0:443 0.0.0.0:* users:(("forkproxy",pid=99,fd=4))\n'
        with patch(PACKAGE + ".trusted_process.verify", return_value=(99, "/trusted/incus", 1, 2, "start")) as proof:
            self.assertEqual(await verify_listeners(output, (443,), instances, "0.0.0.0"), ((99, "/trusted/incus", 1, 2, "start"),))
            proof.assert_awaited_once_with(99)
        with patch(PACKAGE + ".trusted_process.verify", side_effect=NetworkPreparationFailure("exe differs")):
            with self.assertRaises(NetworkPreparationFailure):
                await verify_listeners(output, (443,), instances, "0.0.0.0")
        with self.assertRaises(NetworkPreparationFailure):
            await verify_listeners(output.replace("pid=99,", ""), (443,), instances, "0.0.0.0")

    async def exercise(self, *, ufw=False, wsl=False):
        with tempfile.TemporaryDirectory() as directory:
            host = MockHost(Path(directory) / "proc", ufw=ufw)
            evidence = Mock()
            runner = Mock()
            state = {"schema_version": 1, "distro": "Ubuntu-24.04", "observed_address": "172.20.1.2",
                     "ownership": "absent", "routing_ready": False, "agent_ready": False, "bridge_ready": False,
                     "action": "install", "blockers": [], "fingerprint": "absent", "endpoint_state": "UNVERIFIED", "login_state": "UNVERIFIED"}
            def windows_run(action, **kwargs):
                if action != "inventory":
                    host.calls.append(("windows", action))
                    state.update(ownership="owned", routing_ready=True, agent_ready=True, bridge_ready=True, action=None, fingerprint="ready")
                return WindowsCommandResult(0, stdout=json.dumps(state))
            runner.run.side_effect = windows_run
            windows = WindowsNetworkPreparation(runner, ROOT, ROOT / "infra/config") if wsl else None
            adapter = LocalNetworkPreparation(ROOT, ROOT / "infra/config", release="24.04", profile="service-access",
                        proc_root=host.proc, target_snapshot=lambda: (host.source,), evidence=evidence, windows=windows)
            with host.patches(), patch.dict("os.environ", WSL_DISTRO_NAME="Ubuntu-24.04"):
                service = NetworkPreparationService(adapter)
                plan = await service.plan()
                self.assertFalse(plan.blockers, plan.blockers)
                self.assertFalse(plan.verified)
                self.assertEqual(host.calls, [])
                evidence.write.assert_not_called()
                declined = await service.apply(plan, approved=False)
                self.assertEqual(declined.status, "BLOCKED")
                self.assertEqual(host.calls, [])
                result = await service.apply(plan, approved=True)
                self.assertEqual(result.status, "READY", result)
                self.assertFalse(result.services_verified)
                self.assertEqual(result.login_state, "UNVERIFIED")
                self.assertEqual(result.endpoint_state, "UNVERIFIED")
                self.assertIn(b"192.0.2.7 keep.example\n", host.files["/etc/hosts"][0])
                before = copy.deepcopy(host.calls)
                second = await service.plan()
                self.assertTrue(second.verified, second)
                self.assertEqual((await service.apply(second, approved=True)).status, "READY")
                self.assertEqual(host.calls, before)
                self.assertFalse(any("MASQUERADE" in call or "--system" in call or "reload" in call for call in host.calls))
                if wsl:
                    self.assertIn(("windows", "install"), host.calls)
                    self.assertTrue(all(call.kwargs["distro"] == "Ubuntu-24.04" for call in runner.run.call_args_list))
                else:
                    runner.run.assert_not_called()

    async def test_fresh_native_reconciliation_and_zero_mutation_rerun(self):
        await self.exercise()

    async def test_active_ufw_adds_scoped_dhcp_dns_routes_preserves_policy_and_rerun(self):
        await self.exercise(ufw=True)

    async def test_fresh_wsl_delegates_existing_owner_and_readiness_stays_separate(self):
        await self.exercise(wsl=True)

    async def test_source_drift_and_foreign_port_block_before_any_effect(self):
        with tempfile.TemporaryDirectory() as directory:
            host = MockHost(Path(directory))
            adapter = LocalNetworkPreparation(ROOT, ROOT / "infra/config", release="24.04", profile="service-access",
                        proc_root=host.proc, target_snapshot=lambda: (host.source,), evidence=Mock())
            with host.patches():
                service = NetworkPreparationService(adapter)
                plan = await service.plan()
                host.source = "tampered"
                self.assertEqual((await service.apply(plan, approved=True)).status, "BLOCKED")
                host.listening = 'LISTEN 0 128 0.0.0.0:443 0.0.0.0:* users:(("foreign",pid=99,fd=4))\n'
                self.assertTrue((await service.plan()).blockers)
                self.assertEqual(host.calls, [])

    async def test_evidence_failure_prevents_first_effect_and_post_failure_reports_partial(self):
        for failure_at in (1, 3):
            with self.subTest(failure_at=failure_at), tempfile.TemporaryDirectory() as directory:
                host = MockHost(Path(directory))
                evidence = Mock()
                count = 0
                def record(**kwargs):
                    nonlocal count
                    count += 1
                    if count >= failure_at:
                        raise OSError("private state denied")
                    return "/redacted/evidence"
                evidence.write.side_effect = record
                adapter = LocalNetworkPreparation(ROOT, ROOT / "infra/config", release="24.04", profile="service-access",
                            proc_root=host.proc, target_snapshot=lambda: (host.source,), evidence=evidence)
                with host.patches():
                    service = NetworkPreparationService(adapter)
                    result = await service.apply(await service.plan(), approved=True)
                    self.assertEqual(result.status, "FAILED" if failure_at == 1 else "PARTIAL")
                    self.assertEqual(bool(host.calls), failure_at > 1)

    async def test_foreign_deny_missing_nat_overlap_and_file_collision_fail_closed(self):
        mutations = (lambda host: setattr(host, "denied", True),
                     lambda host: host.nft["nftables"].pop(),
                     lambda host: host.routes.append({"dst": "10.231.50.0/24", "dev": "vpn0"}),
                     lambda host: host.files.update({"/etc/sysctl.d/90-tiny-swarm-world.conf": (b"foreign\n", 0o644)}))
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                host = MockHost(Path(directory))
                mutation(host)
                adapter = LocalNetworkPreparation(ROOT, ROOT / "infra/config", release="24.04", profile="service-access",
                            proc_root=host.proc, target_snapshot=lambda: (host.source,), evidence=Mock())
                with host.patches():
                    plan = await adapter.inspect()
                    self.assertTrue(plan.blockers)
                    self.assertEqual(host.calls, [])

    async def test_unrelated_permissive_rule_and_hosts_drift_halts_after_attempt(self):
        for target in ("rule", "hosts"):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as directory:
                host = MockHost(Path(directory))
                original = host.privileged
                async def mutate(args, timeout=5):
                    output = await original(args, timeout)
                    if args[0] == "modprobe":
                        if target == "rule":
                            host.rules["INPUT"].append(("-s", "192.0.2.7/32", "-j", "ACCEPT"))
                        else:
                            host.files["/etc/hosts"] = (b"127.0.0.1 localhost\n192.0.2.8 changed.example\n", 0o644)
                    return output
                adapter = LocalNetworkPreparation(ROOT, ROOT / "infra/config", release="24.04", profile="service-access",
                            proc_root=host.proc, target_snapshot=lambda: (host.source,), evidence=Mock())
                with host.patches(), patch(PACKAGE + ".runtime.privileged", side_effect=mutate):
                    service = NetworkPreparationService(adapter)
                    result = await service.apply(await service.plan(), approved=True)
                    self.assertEqual(result.status, "PARTIAL")
                    self.assertEqual(result.completed, ("module:br_netfilter",))
                    self.assertEqual(host.calls, [("modprobe", "br_netfilter")])

    async def test_packet_counter_variation_is_stable_but_policy_drift_is_not(self):
        with tempfile.TemporaryDirectory() as directory:
            host = MockHost(Path(directory))
            host.nft["nftables"][-1]["rule"]["expr"].append({"counter": {"packets": 1, "bytes": 64}})
            adapter = LocalNetworkPreparation(ROOT, ROOT / "infra/config", release="24.04", profile="service-access",
                        proc_root=host.proc, target_snapshot=lambda: (host.source,), evidence=Mock())
            with host.patches():
                before = await adapter.inspect()
                host.nft["nftables"][-1]["rule"]["expr"][-1]["counter"].update(packets=1000, bytes=99999)
                self.assertEqual(await adapter.inspect(), before)
                host.nft["nftables"][0]["chain"]["policy"] = "drop"
                self.assertTrue((await adapter.inspect()).blockers)

    async def test_timeout_and_failed_postcheck_retain_uncertain_pending_effect(self):
        for error in (NetworkPreparationFailure("timeout", exit_code=124), None):
            with self.subTest(error=error), tempfile.TemporaryDirectory() as directory:
                host = MockHost(Path(directory))
                adapter = LocalNetworkPreparation(ROOT, ROOT / "infra/config", release="24.04", profile="service-access",
                            proc_root=host.proc, target_snapshot=lambda: (host.source,), evidence=Mock())
                with host.patches(), patch.object(adapter, "execute", side_effect=error), patch.object(adapter, "action_verified", return_value=False):
                    service = NetworkPreparationService(adapter)
                    result = await service.apply(await service.plan(), approved=True)
                    self.assertEqual(result.status, "PARTIAL")
                    self.assertEqual(result.uncertain, ("module:br_netfilter",))
                    self.assertEqual(result.completed, ())
                    self.assertEqual(host.calls, [])

    async def test_cancelled_mutation_records_uncertain_effect_and_propagates(self):
        with tempfile.TemporaryDirectory() as directory:
            host = MockHost(Path(directory))
            evidence = Mock()
            adapter = LocalNetworkPreparation(ROOT, ROOT / "infra/config", release="24.04", profile="service-access",
                        proc_root=host.proc, target_snapshot=lambda: (host.source,), evidence=evidence)
            with host.patches(), patch.object(adapter, "execute", side_effect=asyncio.CancelledError):
                service = NetworkPreparationService(adapter)
                with self.assertRaises(asyncio.CancelledError):
                    await service.apply(await service.plan(), approved=True)
                self.assertEqual(evidence.write.call_args.kwargs["uncertain"], ("module:br_netfilter",))
                self.assertEqual(host.calls, [])


class FirewallNegativeTests(unittest.TestCase):
    def test_early_ufw_policy_drop_cannot_be_hidden_by_present_exact_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            host = MockHost(Path(directory), ufw=True)
            host.rules["FORWARD"] = list(forwarding_rules(BRIDGE))
            rules = parse_rules(host.saved())
            rules["ufw-skip-to-policy-forward"] = [("-j", "DROP")]
            for chain in ("FORWARD", "ufw-before-forward"):
                broken = copy.deepcopy(rules)
                broken[chain].insert(0, ("-j", "ufw-skip-to-policy-forward"))
                with self.assertRaises(NetworkPreparationFailure):
                    verify_no_foreign_denies(broken, ufw=True)

    def test_nested_logging_policy_and_conntrack_disabling_block(self):
        with tempfile.TemporaryDirectory() as directory:
            rules = parse_rules(MockHost(Path(directory), ufw=True).saved())
            rules["FORWARD"].insert(0, ("-j", "ufw-before-logging-forward"))
            rules["ufw-before-logging-forward"] = [("-j", "ufw-skip-to-policy-forward")]
            rules["ufw-skip-to-policy-forward"] = [("-j", "DROP")]
            with self.assertRaises(NetworkPreparationFailure):
                verify_no_foreign_denies(rules, ufw=True)
            for rule in (("-j", "CT", "--notrack"), ("-m", "conntrack", "--ctstate", "INVALID,NEW", "-j", "DROP")):
                with self.assertRaises(NetworkPreparationFailure):
                    verify_no_foreign_denies({"raw:PREROUTING": [rule]}, ufw=False)

    def test_competing_nat_and_published_reserved_port_block_disjoint_docker_survives(self):
        from tiny_swarm_world.infrastructure.adapters.network_preparation.nat_conflicts import verify
        allowed = "*filter\n:INPUT ACCEPT [0:0]\n:OUTPUT ACCEPT [0:0]\n:FORWARD DROP [0:0]\nCOMMIT\n*nat\n-A POSTROUTING -s 172.18.0.0/16 ! -o br-123 -j MASQUERADE\n-A PREROUTING -m addrtype --dst-type LOCAL -j DOCKER\n-A DOCKER -p tcp --dport 8080 -j DNAT --to-destination 172.18.0.2:80\nCOMMIT\n"
        verify(allowed, (BRIDGE,), (80, 443))
        for source in ("10.231.50.0/24", "0.0.0.0/0", "! 172.18.0.0/16"):
            with self.assertRaises(NetworkPreparationFailure):
                verify(allowed.replace("172.18.0.0/16", source), (BRIDGE,), (80, 443))
        with self.assertRaises(NetworkPreparationFailure):
            verify(allowed.replace("--dport 8080", "--dport 443"), (BRIDGE,), (80, 443))
        with self.assertRaises(NetworkPreparationFailure):
            verify(allowed.replace("-j DOCKER", "-j custom-nat"), (BRIDGE,), (80, 443))
        with self.assertRaises(NetworkPreparationFailure):
            verify(allowed.replace("-m addrtype --dst-type LOCAL -j DOCKER", "-j DOCKER"), (BRIDGE,), (80, 443))

    def test_restricted_ufw_established_return_does_not_prove_bridge_readiness(self):
        with tempfile.TemporaryDirectory() as directory:
            rules = parse_rules(MockHost(Path(directory), ufw=True).saved())
            rules["ufw-before-forward"][0] = ("-i", "unrelated0", *rules["ufw-before-forward"][0])
            with self.assertRaises(NetworkPreparationFailure):
                verify_no_foreign_denies(rules, ufw=True)

    def test_ufw_narrowing_conntrack_rule_is_not_an_equivalent_new_flow_allow(self):
        desired = forwarding_rules(BRIDGE)[1]
        for state in ("INVALID", "ESTABLISHED", "RELATED,ESTABLISHED"):
            observed = tuple(state if item == "NEW,ESTABLISHED,RELATED" else item for item in desired)
            self.assertFalse(equivalent(desired, observed, ufw=True))

    def test_embedded_boot_guard_executes_complete_isolated_closure_with_mock_commands(self):
        guard = render_guard((BRIDGE,), False)
        self.assertIn("python3 -I -B -", guard)
        source = guard.split("\n", 1)[1].rsplit("\nTSW_GUARD", 1)[0]
        saved = "*filter\n:INPUT ACCEPT [0:0]\n:OUTPUT ACCEPT [0:0]\n:FORWARD DROP [0:0]\nCOMMIT\n"
        def run(args, **kwargs):
            outputs = {"iptables": "iptables v1.8 (nf_tables)", "systemctl": "ActiveState=inactive\nUnitFileState=disabled\n",
                       "ufw": "Status: inactive\n", "iptables-save": saved, "nft": json.dumps(nft_fixture()),
                       "ip": '[{"dst":"default","dev":"eth0"}]'}
            if args[:3] == ["ip", "-j", "address"]:
                return subprocess.CompletedProcess(args, 0, '[{"ifname":"incusbr0","addr_info":[{"family":"inet","local":"10.231.50.1","prefixlen":24}]}]', "")
            return subprocess.CompletedProcess(args, 0, outputs[args[0]], "")
        with patch("subprocess.run", side_effect=run) as runner:
            exec(compile(source, "root-owned-forwarding-guard", "exec"), {})
            self.assertTrue(all(call.kwargs["timeout"] == 5 for call in runner.call_args_list))

    def test_source_digest_binds_all_helpers_configs_and_rejects_linked_ancestor(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "src", root / "src", ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copytree(ROOT / "infra/config", root / "infra/config")
            for name in ("requirements.lock", "requirements.build.lock", "pyproject.toml"):
                shutil.copyfile(ROOT / name, root / name)
            before = preparation_asset_hashes(root, is_wsl=False)
            helper = root / "src/tiny_swarm_world/infrastructure/adapters/network_preparation/trusted_process.py"
            helper.write_text(helper.read_text() + "\n# source drift\n")
            self.assertNotEqual(preparation_asset_hashes(root, is_wsl=False), before)
            original = root / "infra/config/host"
            protected = root / "outside-host"
            original.rename(protected)
            original.symlink_to(protected, target_is_directory=True)
            with self.assertRaises(RuntimeError):
                preparation_asset_hashes(root, is_wsl=False)

    def test_real_iptables_save_expansions_preserve_exact_scope_and_states(self):
        desired = forwarding_rules(BRIDGE)[0]
        observed = ("-s", "10.231.50.0/24", "-d", "10.231.50.0/24", "-i", "incusbr0", "-o", "incusbr0",
                    "-m", "conntrack", "--ctstate", "RELATED,ESTABLISHED,NEW", "-m", "comment", "--comment", "tsw:incusbr0:internal", "-j", "ACCEPT")
        self.assertTrue(exact_present(desired, [observed]))
        extra = observed[:-2] + ("--sport", "22", *observed[-2:])
        with self.assertRaises(NetworkPreparationFailure):
            exact_present(desired, [extra])

    def test_custom_deny_jump_and_nonfilter_rule_cannot_hide_behind_filter(self):
        for saved in ("*filter\n:FORWARD DROP [0:0]\n-A FORWARD -j custom\n-A custom -j DROP\nCOMMIT\n",
                      "*raw\n:PREROUTING ACCEPT [0:0]\n-A PREROUTING -j DROP\nCOMMIT\n*filter\n:FORWARD DROP [0:0]\nCOMMIT\n"):
            with self.assertRaises(NetworkPreparationFailure):
                verify_no_foreign_denies(parse_rules(saved), ufw=False)

    def test_native_incus_queue_jump_and_unknown_chain_block(self):
        for expression in ({"queue": None}, {"jump": {"target": "foreign"}}, {"mangle": {"key": {"meta": {"key": "mark"}}, "value": 1}}):
            value = nft_fixture()
            value["nftables"].append({"rule": {"family": "inet", "table": "incus", "chain": "fwd.incusbr0", "expr": [expression]}})
            with self.assertRaises(NetworkPreparationFailure):
                verify_nft(value, (BRIDGE,))
        value = nft_fixture()
        value["nftables"].append({"chain": {"family": "inet", "table": "incus", "name": "foreign"}})
        with self.assertRaises(NetworkPreparationFailure):
            verify_nft(value, (BRIDGE,))

    def test_native_hook_policy_priority_and_nat_predicates_cannot_be_guessed(self):
        mutations = (lambda value: value["nftables"][0]["chain"].update(policy="drop"),
                     lambda value: value["nftables"][0]["chain"].update(prio=-200),
                     lambda value: value["nftables"][0]["chain"].update(table="foreign"),
                     lambda value: value["nftables"][-1]["rule"]["expr"].insert(0, {"match": {"op": "==", "left": {"meta": {"key": "oifname"}}, "right": "other0"}}))
        for mutation in mutations:
            value = nft_fixture()
            mutation(value)
            with self.assertRaises(NetworkPreparationFailure):
                verify_nft(value, (BRIDGE,))
