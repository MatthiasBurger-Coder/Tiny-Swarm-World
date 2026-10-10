"""BOOT-W03 acceptance through actual service/adapter owners and mocked host I/O."""
from __future__ import annotations

import asyncio
import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from tiny_swarm_world.application.ports.incus_preparation import IncusPreparationFailure
from tiny_swarm_world.application.services.incus_preparation import IncusPreparationService
from tiny_swarm_world.domain.incus_preparation import IncusAction, IncusSnapshot
from tiny_swarm_world.infrastructure.adapters.incus_preparation.adapter import LocalIncusPreparation
from tiny_swarm_world.infrastructure.adapters.incus_preparation.resources import choose_subnet, ipv4_subnet
from tiny_swarm_world.infrastructure.adapters.incus_preparation import runtime
from tiny_swarm_world.infrastructure.adapters.native_preparation_evidence import NativePreparationEvidenceWriter
from tiny_swarm_world.infrastructure.process.async_runner import AsyncProcessResult
from tiny_swarm_world.prepare_incus import prepare

CONFIG = Path(__file__).resolve().parents[1] / "infra/config/node-providers/provider_config.yaml"
RUNTIME = "tiny_swarm_world.infrastructure.adapters.incus_preparation.runtime"


class FakeHost:
    def __init__(self):
        self.daemon = True
        self.active_group = True
        self.persisted_group = True
        self.calls = []
        self.routes = [{"dst": "10.231.50.0/24", "dev": "vpn0"}]
        self.links = []
        self.server = {"environment": {"server_clustered": False}, "config": {"user.keep": "unchanged"}}
        self.inventory = {"storage-pools": [], "networks": [],
                          "profiles": [{"name": "default", "config": {}, "devices": {}}],
                          "instances": [{"name": "unrelated-node", "status": "Running", "config": {"user.keep": "unchanged"}}]}
        self.failure_kind = None

    def account(self):
        return "operator", self.active_group, self.persisted_group

    async def daemon_state(self):
        return {"LoadState": "loaded", "ActiveState": "active" if self.daemon else "inactive", "UnitFileState": "enabled"}

    async def command(self, args, timeout=5):
        self.calls.append(tuple(args))
        return AsyncProcessResult(0 if self.active_group else 1, "safe")

    async def checked(self, args, timeout=5):
        self.calls.append(tuple(args))
        if "start" in args:
            self.daemon = True
        elif "usermod" in " ".join(args):
            self.persisted_group = True
        elif "POST" in args:
            kind = args[args.index("query") + 1].split("/")[-1].split("?")[0]
            if self.failure_kind == kind:
                raise IncusPreparationFailure("sensitive-output-is-not-propagated", exit_code=124)
            data = json.loads(args[args.index("--data") + 1])
            if any(item["name"] == data["name"] for item in self.inventory[kind]):
                raise IncusPreparationFailure("name_claimed")
            data["status"] = "Created"
            if kind == "networks":
                data["managed"] = True
            self.inventory[kind].append(data)
        return "safe"

    async def query(self, path):
        self.calls.append(("query", path))
        if path == "/1.0":
            return copy.deepcopy(self.server)
        kind = path.split("/")[-1].split("?")[0]
        return copy.deepcopy(self.inventory[kind])

    async def networking(self, args):
        return copy.deepcopy(self.routes if "route" in args else self.links)


class IncusCliTransportTests(unittest.IsolatedAsyncioTestCase):
    async def test_query_is_local_isolated_and_uses_api_project_scope(self):
        for path in ("/1.0", "/1.0/profiles?recursion=1&project=default"):
            with patch(f"{RUNTIME}.run_async_process", return_value=AsyncProcessResult(0, "{}")) as runner:
                self.assertEqual(await runtime.query(path), {})
                runner.assert_awaited_once_with(
                    ("/usr/bin/env", "INCUS_CONF=/proc/self", "incus", "--force-local", "query", path),
                    timeout=5.0,
                )

    async def test_resource_create_retains_approved_payload_project_and_deadline(self):
        adapter = LocalIncusPreparation(CONFIG, release="26.04", evidence=Mock())
        payload = json.dumps({"name": "docker-swarm", "config": {}, "devices": {}})
        action = IncusAction("profile:create", "profiles", "docker-swarm", payload=payload)
        adapter._actions = (action,)
        with patch(f"{RUNTIME}.run_async_process", return_value=AsyncProcessResult(0, "{}")) as runner:
            await adapter.execute(action)
            runner.assert_awaited_once_with(
                ("/usr/bin/env", "INCUS_CONF=/proc/self", "incus", "--force-local", "query",
                 "/1.0/profiles?project=default", "-X", "POST", "--wait", "--data", payload),
                timeout=action.timeout_seconds,
            )


class IncusAcceptanceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.host = FakeHost()
        self.evidence = Mock(write=Mock(return_value=Path("/private/redacted-evidence")))
        self.adapter = LocalIncusPreparation(CONFIG, release="24.04", evidence=self.evidence)
        self.service = IncusPreparationService(self.adapter)
        replacements = {"account": self.host.account, "daemon_state": self.host.daemon_state,
                        "command": self.host.command, "checked_command": self.host.checked,
                        "query": self.host.query, "json_command": self.host.networking}
        for name, replacement in replacements.items():
            handle = patch(f"{RUNTIME}.{name}", side_effect=replacement)
            handle.start()
            self.addCleanup(handle.stop)

    async def test_boot_w03_ac1_default_initialization_and_ac3_user_verification(self):
        original = copy.deepcopy(self.host.inventory["instances"])
        plan = await self.service.plan()
        self.assertEqual([action.kind for action in plan.actions], ["storage-pools", "networks", "profiles", "profiles"])
        network = json.loads(plan.actions[1].payload)
        self.assertEqual(network["name"], "incusbr0")
        self.assertEqual(network["config"]["ipv4.address"], "10.231.51.1/24")
        result = await self.service.apply(plan, approved=True)
        self.assertEqual(result.status, "READY")
        self.assertEqual(len(result.completed), 4)
        self.assertFalse(result.services_verified)
        self.assertEqual(self.host.inventory["instances"], original)
        self.assertEqual(self.host.inventory["profiles"][0], {"name": "default", "config": {}, "devices": {}})
        commands = [call for call in self.host.calls if "incus" in call]
        self.assertTrue(any("version" in call for call in commands))
        self.assertTrue(any("info" in call for call in commands))
        self.assertTrue(all("sudo" not in call and "--force-local" in call for call in commands))
        self.assertTrue(all("--project" in call for call in commands if "query" not in call))
        self.assertTrue(all("--project" not in call for call in commands if "query" in call))
        self.assertTrue(all("INCUS_CONF=/proc/self" in call for call in commands))
        self.assertTrue((await self.service.plan()).verified)

    async def test_boot_w03_ac2_compatible_resources_reused_ac4_rerun_preserves_configuration(self):
        await self.service.apply(await self.service.plan(), approved=True)
        self.host.inventory["storage-pools"][0]["driver"] = "zfs"
        self.host.inventory["storage-pools"][0]["config"] = {"source": "operator-owned-pool"}
        self.host.inventory["networks"][0]["config"]["ipv4.address"] = "192.168.240.1/24"
        self.host.inventory["profiles"][1]["config"]["user.keep"] = "same"
        before = copy.deepcopy(self.host.inventory)
        self.host.calls.clear()
        self.evidence.reset_mock()
        result = await self.service.apply(await self.service.plan(), approved=True)
        self.assertEqual(result.status, "READY")
        self.assertEqual(self.host.inventory, before)
        self.assertFalse(any("POST" in call or "sudo" in call for call in self.host.calls))
        self.evidence.write.assert_not_called()

    async def test_boot_w03_ac2_incompatible_storage_network_and_profile_block_all_mutation(self):
        await self.service.apply(await self.service.plan(), approved=True)
        baseline = copy.deepcopy(self.host.inventory)
        for kind, key, value in (("storage-pools", "driver", "cephobject"),
                                  ("networks", "type", "physical"), ("profiles", "config", {"security.privileged": "true"})):
            self.host.inventory = copy.deepcopy(baseline)
            self.host.inventory[kind][-1][key] = value
            self.host.calls.clear()
            plan = await self.service.plan()
            self.assertTrue(plan.blockers, kind)
            result = await self.service.apply(plan, approved=True)
            self.assertEqual(result.status, "BLOCKED")
            self.assertFalse(any("POST" in call for call in self.host.calls))
            self.assertIn("preserve", plan.blockers[0])

    async def test_boot_w03_ac1_daemon_group_restart_then_current_user_clean_resource_setup(self):
        self.host.daemon = False
        self.host.active_group = self.host.persisted_group = False
        plan = await self.service.plan()
        self.assertEqual([item.id for item in plan.actions], ["daemon:start"])
        self.assertEqual(self.host.calls, [])  # no socket activation by inventory
        await self.service.apply(plan, approved=True)
        access = await self.service.plan()
        self.assertEqual([item.id for item in access.actions], ["access:add-group"])
        result = await self.service.apply(access, approved=True)
        self.assertEqual(result.status, "RESTART_REQUIRED")
        self.assertEqual(self.host.inventory["storage-pools"], [])
        self.assertTrue((await self.service.plan()).restart_required)
        self.host.active_group = True  # new ordinary-user login, not sudo
        self.assertEqual((await self.service.apply(await self.service.plan(), approved=True)).status, "READY")

    async def test_existing_settings_only_profiles_are_compatible_with_explicit_launch_devices(self):
        await self.service.apply(await self.service.plan(), approved=True)
        for profile in self.host.inventory["profiles"]:
            profile["devices"] = {}
        before = copy.deepcopy(self.host.inventory)
        self.assertTrue((await self.service.plan()).verified)
        self.assertEqual(self.host.inventory, before)

    async def test_drift_during_first_mutation_stops_later_approved_actions(self):
        checked = self.host.checked
        async def mutate(args, timeout=5):
            output = await checked(args, timeout)
            if "POST" in args:
                self.host.inventory["instances"][0]["config"]["user.keep"] = "external-change"
            return output
        with patch(f"{RUNTIME}.checked_command", side_effect=mutate):
            result = await self.service.apply(await self.service.plan(), approved=True)
        self.assertEqual(result.status, "PARTIAL")
        self.assertEqual(self.host.inventory["networks"], [])
        self.assertEqual(len(self.host.inventory["storage-pools"]), 1)
        self.assertEqual(result.uncertain, ("create:storage-pools:default",))

    async def test_configuration_drift_during_mutation_stops_later_actions(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "provider_config.yaml"
            target.write_text(CONFIG.read_text())
            self.adapter.path = target
            checked = self.host.checked
            async def mutate(args, timeout=5):
                output = await checked(args, timeout)
                if "POST" in args:
                    target.write_text(CONFIG.read_text() + "\n# changed after approval\n")
                return output
            with patch(f"{RUNTIME}.checked_command", side_effect=mutate):
                result = await self.service.apply(await self.service.plan(), approved=True)
        self.assertEqual(result.status, "PARTIAL")
        self.assertEqual(self.host.inventory["networks"], [])

    async def test_custom_resolved_resource_and_profile_names_used_without_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "provider_config.yaml"
            target.write_text(CONFIG.read_text().replace("incusbr0", "tsw-control")
                              .replace("storage_pool: default", "storage_pool: tsw-pool")
                              .replace("docker-swarm", "tsw-swarm"))
            self.adapter.path = target
            plan = await self.service.plan()
            self.assertEqual([item.name for item in plan.actions],
                             ["tsw-pool", "tsw-control", "tsw-swarm", "tsw-swarm-manager"])
            self.assertEqual((await self.service.apply(plan, approved=True)).status, "READY")
        self.assertEqual(self.host.inventory["profiles"][0]["name"], "default")

    async def test_cli_daemon_stage_followed_by_separate_resource_consent(self):
        self.host.daemon = False
        with patch("tiny_swarm_world.prepare_incus.build_incus_preparation_service", return_value=self.service), patch("builtins.input", side_effect=["yes", "yes"]) as prompt, redirect_stdout(io.StringIO()):
            self.assertEqual(await prepare(read_only=False, service_profile="default"), 0)
        self.assertEqual(prompt.call_count, 2)
        self.assertTrue((await self.service.plan()).verified)

    async def test_cli_declining_second_stage_reports_partial_prior_daemon_change(self):
        self.host.daemon = False
        with patch("tiny_swarm_world.prepare_incus.build_incus_preparation_service", return_value=self.service), patch("builtins.input", side_effect=["yes", "no"]), redirect_stdout(io.StringIO()):
            self.assertEqual(await prepare(read_only=False, service_profile="default"), 4)
        self.assertTrue(self.host.daemon)
        self.assertEqual(self.host.inventory["storage-pools"], [])

    async def test_address_lifetime_countdown_does_not_invalidate_approved_topology(self):
        self.host.links = [{"ifname": "eth0", "addr_info": [{"family": "inet", "local": "192.168.10.20", "prefixlen": 24,
                          "valid_life_time": 3600, "preferred_life_time": 3600}]}]
        plan = await self.service.plan()
        self.host.links[0]["addr_info"][0]["valid_life_time"] = 3599
        self.host.links[0]["addr_info"][0]["preferred_life_time"] = 3599
        checked = self.host.checked
        async def mutate(args, timeout=5):
            self.host.links[0]["addr_info"][0]["preferred_life_time"] -= 1
            return await checked(args, timeout)
        with patch(f"{RUNTIME}.checked_command", side_effect=mutate):
            result = await self.service.apply(plan, approved=True)
        self.assertEqual(result.status, "READY")

    async def test_real_address_or_route_drift_during_apply_stops_dependents(self):
        self.host.links = [{"ifname": "eth0", "addr_info": [{"family": "inet", "local": "192.168.10.20", "prefixlen": 24}]}]
        checked = self.host.checked
        async def mutate(args, timeout=5):
            output = await checked(args, timeout)
            if "POST" in args:
                self.host.links[0]["addr_info"][0]["local"] = "192.168.11.20"
            return output
        with patch(f"{RUNTIME}.checked_command", side_effect=mutate):
            result = await self.service.apply(await self.service.plan(), approved=True)
        self.assertEqual(result.status, "PARTIAL")
        self.assertEqual(self.host.inventory["networks"], [])

    async def test_failed_host_requalification_after_mutation_reports_partial(self):
        self.adapter._target_snapshot = Mock(return_value=("qualified",))
        checked = self.host.checked
        async def mutate(args, timeout=5):
            output = await checked(args, timeout)
            if "POST" in args:
                self.adapter._target_snapshot = Mock(side_effect=RuntimeError("host path secret"))
            return output
        with patch(f"{RUNTIME}.checked_command", side_effect=mutate):
            result = await self.service.apply(await self.service.plan(), approved=True)
        self.assertEqual(result.status, "PARTIAL")
        self.assertEqual(self.host.inventory["networks"], [])
        self.assertNotIn("secret", result.message)

    async def test_plan_and_refusal_write_no_evidence_or_resources(self):
        before = copy.deepcopy(self.host.inventory)
        plan = await self.service.plan()
        result = await self.service.apply(plan, approved=False)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(self.host.inventory, before)
        self.evidence.write.assert_not_called()
        self.assertFalse(any("POST" in call for call in self.host.calls))

    async def test_configuration_or_inventory_drift_invalidates_consent(self):
        plan = await self.service.plan()
        self.host.inventory["instances"].append({"name": "another-node"})
        result = await self.service.apply(plan, approved=True)
        self.assertEqual(result.status, "BLOCKED")
        self.evidence.write.assert_not_called()
        self.assertFalse(any("POST" in call for call in self.host.calls))

    async def test_subnet_collision_and_host_interface_name_collision_block(self):
        await self.service.apply(await self.service.plan(), approved=True)
        self.host.routes.append({"dst": "10.231.51.0/24", "dev": "vpn1"})
        self.assertIn("collides", (await self.service.plan()).blockers[0])
        self.host.inventory["networks"] = []
        self.host.links = [{"ifname": "incusbr0"}]
        self.assertIn("host interface", (await self.service.plan()).blockers[0])

    async def test_timeout_preserves_observed_pool_and_stops_profiles_with_uncertain_network(self):
        plan = await self.service.plan()
        self.host.failure_kind = "networks"
        result = await self.service.apply(plan, approved=True)
        self.assertEqual(result.status, "PARTIAL")
        self.assertEqual(result.exit_code, 124)
        self.assertEqual(result.completed, ("create:storage-pools:default",))
        self.assertEqual(result.uncertain, ("create:networks:incusbr0",))
        self.assertEqual(len(self.host.inventory["profiles"]), 1)
        last = self.evidence.write.call_args.kwargs
        self.assertEqual(last["uncertain"], result.uncertain)
        self.assertNotIn("sensitive-output", result.message)
        # Safe resume uses observed pool; no delete/reset.
        self.host.failure_kind = None
        resume = await self.service.plan()
        self.assertFalse(any(action.kind == "storage-pools" for action in resume.actions))
        self.assertEqual((await self.service.apply(resume, approved=True)).status, "READY")

    async def test_final_readiness_failure_never_reports_ready(self):
        original = self.host.query
        async def query(path):
            if path == "/1.0" and len(self.host.inventory["profiles"]) == 3:
                raise IncusPreparationFailure("final_info_failed")
            return await original(path)
        with patch(f"{RUNTIME}.query", side_effect=query):
            result = await self.service.apply(await self.service.plan(), approved=True)
        self.assertEqual(result.status, "PARTIAL")
        self.assertNotEqual(result.exit_code, 0)

    async def test_read_only_cli_no_prompt_or_evidence_and_exact_plan(self):
        output = io.StringIO()
        with patch("tiny_swarm_world.prepare_incus.build_incus_preparation_service", return_value=self.service), patch("builtins.input") as prompt, redirect_stdout(output):
            self.assertEqual(await prepare(read_only=True, service_profile="default"), 2)
        self.assertIn("incusbr0", output.getvalue())
        self.assertIn("10.231.51.1/24", output.getvalue())
        self.assertIn("retries=0", output.getvalue())
        prompt.assert_not_called()
        self.evidence.write.assert_not_called()

    async def test_clustered_unknown_server_and_unknown_inventory_block(self):
        self.host.server["environment"]["server_clustered"] = True
        self.assertIn("Clustered", (await self.service.plan()).blockers[0])
        self.host.server["environment"]["server_clustered"] = False
        with patch(f"{RUNTIME}.query", return_value={"environment": {"server_clustered": False}}):
            self.assertTrue((await self.service.plan()).blockers)

    async def test_interruption_records_uncertain_action_and_propagates(self):
        plan = await self.service.plan()
        with patch.object(self.adapter, "execute", side_effect=asyncio.CancelledError):
            with self.assertRaises(asyncio.CancelledError):
                await self.service.apply(plan, approved=True)
        self.assertEqual(self.evidence.write.call_args.kwargs["status"], "interrupted")
        self.assertEqual(self.evidence.write.call_args.kwargs["uncertain"], ("create:storage-pools:default",))


class IncusBoundaryTests(unittest.IsolatedAsyncioTestCase):
    async def test_consent_prompt_keeps_event_loop_responsive(self):
        import threading
        from tiny_swarm_world.prepare_incus import request_consent
        released = threading.Event()
        loop = asyncio.get_running_loop()
        handle = loop.call_later(0.01, released.set)
        def blocking_prompt(_prompt):
            return "yes" if released.wait(1) else "no"
        try:
            with patch("builtins.input", side_effect=blocking_prompt):
                self.assertTrue(await request_consent())
        finally:
            released.set()
            handle.cancel()

    def test_cancelled_consent_does_not_delay_runner_shutdown(self):
        import threading
        from tiny_swarm_world.prepare_incus import request_consent
        started = threading.Event()
        release = threading.Event()
        returned = threading.Event()
        def blocking_prompt(_prompt):
            started.set()
            release.wait(2)
            return "yes"
        async def cancel_prompt():
            task = asyncio.create_task(request_consent())
            while not started.is_set():
                await asyncio.sleep(0.001)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
        def runner():
            asyncio.run(cancel_prompt())
            returned.set()
        worker = threading.Thread(target=runner, daemon=True)
        try:
            with patch("builtins.input", side_effect=blocking_prompt):
                worker.start()
                self.assertTrue(returned.wait(0.5), "Runner must finish before unanswered input returns")
                self.assertFalse(release.is_set())
        finally:
            release.set()
            worker.join(3)

    async def test_positive_bounded_commands_and_safe_error_output(self):
        with patch(f"{RUNTIME}.run_async_process", return_value=AsyncProcessResult(1, "secret", "secret")) as runner:
            with self.assertRaises(IncusPreparationFailure) as error:
                await runtime.checked_command(("incus", "info"))
            self.assertNotIn("secret", str(error.exception))
            self.assertEqual(runner.call_args.kwargs["timeout"], 5.0)
        with patch(f"{RUNTIME}.run_async_process", return_value=AsyncProcessResult(124, timed_out=True)):
            with self.assertRaises(IncusPreparationFailure) as error:
                await runtime.command(("incus", "info"), 60)
            self.assertEqual(error.exception.exit_code, 124)

    async def test_missing_group_root_and_unsafe_identity_block(self):
        with patch(f"{RUNTIME}.os.geteuid", return_value=0):
            with self.assertRaisesRegex(IncusPreparationFailure, "ordinary"):
                runtime.account()
        with patch(f"{RUNTIME}.os.geteuid", return_value=1000), patch(f"{RUNTIME}.grp.getgrnam", side_effect=KeyError):
            with self.assertRaisesRegex(IncusPreparationFailure, "missing"):
                runtime.account()

    async def test_unknown_or_failed_daemon_never_starts_automatically(self):
        for state in ("failed", "activating", "deactivating", "unknown"):
            with patch(f"{RUNTIME}.checked_command", return_value=f"LoadState=loaded\nActiveState={state}\nUnitFileState=enabled"):
                with self.assertRaises(IncusPreparationFailure):
                    await runtime.daemon_state()

    def test_subnet_exhaustion_is_bounded(self):
        occupied = [("vpn", ipv4_subnet("10.0.0.0/8"))]
        with self.assertRaisesRegex(IncusPreparationFailure, "No collision-free"):
            choose_subnet(occupied)

    def test_protected_redacted_action_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            writer = NativePreparationEvidenceWriter(Path(directory))
            target = writer.write(platform_release="24.04", status="PARTIAL", planned=("daemon:start",),
                                  added=(), uncertain=("daemon:start",), stage="incus_preparation", capability="incus")
            payload = json.loads(target.read_text())
            self.assertEqual(payload["schema"], "incus-preparation-v1")
            self.assertEqual(payload["uncertain_actions"], ["daemon:start"])
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
            self.assertEqual(target.parent.stat().st_mode & 0o777, 0o700)
            self.assertNotIn("stdout", payload)

    async def test_evidence_failure_before_mutation_and_failed_verification(self):
        action = IncusAction("daemon:start", "daemon", "incus.service")
        plan = IncusSnapshot("same", (action,))
        port = Mock(inspect=AsyncMock(return_value=plan), execute=AsyncMock(), action_verified=AsyncMock(return_value=False))
        port.record.side_effect = OSError("secret")
        service = IncusPreparationService(port)
        with self.assertRaises(OSError):
            await service.apply(plan, approved=True)
        port.execute.assert_not_called()
        port.record.side_effect = None
        port.record.return_value = "/private/evidence"
        result = await IncusPreparationService(port).apply(plan, approved=True)
        self.assertEqual(result.status, "PARTIAL")
        self.assertEqual(result.uncertain, ("daemon:start",))


class IncusHandoffTests(unittest.TestCase):
    def setUp(self):
        from tests.test_prepare_linux import QUALIFIED
        self.host = FakeHost()
        self.evidence = Mock(write=Mock(return_value=Path("/private/evidence")))
        self.service = IncusPreparationService(LocalIncusPreparation(CONFIG, release="24.04", evidence=self.evidence))
        self.native = Mock(plan=Mock(return_value=Mock(facts=QUALIFIED, failures=(), missing_packages=())))
        replacements = {"account": self.host.account, "daemon_state": self.host.daemon_state,
                        "command": self.host.command, "checked_command": self.host.checked,
                        "query": self.host.query, "json_command": self.host.networking}
        for name, replacement in replacements.items():
            handle = patch(f"{RUNTIME}.{name}", side_effect=replacement)
            handle.start()
            self.addCleanup(handle.stop)

    def test_prepare_linux_actual_delegation_read_only_apply_and_ready_rerun(self):
        from tiny_swarm_world.prepare_linux import main
        from tiny_swarm_world.prepare_incus import main as incus_main
        import subprocess
        calls = []
        def child(args, **kwargs):
            calls.append((args, kwargs))
            return subprocess.CompletedProcess(args, incus_main(args[args.index("--service-profile"):]))
        with (patch("tiny_swarm_world.prepare_linux.build_native_preparation_service", return_value=self.native),
              patch("tiny_swarm_world.prepare_linux._validate_mutation_paths", return_value=("same",)),
              patch("tiny_swarm_world.infrastructure.composition_installation._python_imports_available", return_value=True),
              patch("tiny_swarm_world.infrastructure.composition_installation._paths_from_env", return_value=Mock(native_linux_venv=Path("/venv"))),
              patch("tiny_swarm_world.prepare_incus.build_incus_preparation_service", return_value=self.service),
              patch("tiny_swarm_world.infrastructure.process.SubprocessProcessRunner.run_text", side_effect=child),
              patch("builtins.input", return_value="yes"), redirect_stdout(io.StringIO())):
            self.assertEqual(main(("--preflight",)), 2)
            self.evidence.write.assert_not_called()
            self.assertEqual(main(()), 0)
            self.evidence.reset_mock()
            self.assertEqual(main(("--dry-run",)), 0)
            self.evidence.write.assert_not_called()
        self.assertIn("-B", calls[0][0])
        self.assertIn("--dry-run", calls[0][0])
        self.assertEqual(calls[0][1]["env"]["PYTHONDONTWRITEBYTECODE"], "1")
        self.assertEqual(calls[0][1]["timeout"], 1800)

    def test_incus_restart_exit_stops_install_handoff_from_prepare_linux(self):
        from tiny_swarm_world.prepare_linux import main
        from tiny_swarm_world.prepare_incus import main as incus_main
        import subprocess
        self.host.active_group = False
        self.host.persisted_group = True
        def child(args, **kwargs):
            return subprocess.CompletedProcess(args, incus_main(()))
        with (patch("tiny_swarm_world.prepare_linux.build_native_preparation_service", return_value=self.native),
              patch("tiny_swarm_world.prepare_linux._validate_mutation_paths", return_value=("same",)),
              patch("tiny_swarm_world.infrastructure.composition_installation._python_imports_available", return_value=True),
              patch("tiny_swarm_world.infrastructure.composition_installation._paths_from_env", return_value=Mock(native_linux_venv=Path("/venv"))),
              patch("tiny_swarm_world.prepare_incus.build_incus_preparation_service", return_value=self.service),
              patch("tiny_swarm_world.infrastructure.process.SubprocessProcessRunner.run_text", side_effect=child),
              patch("builtins.input") as prompt, redirect_stdout(io.StringIO())):
            self.assertEqual(main(()), 3)
        prompt.assert_not_called()
        self.evidence.write.assert_not_called()
        self.assertEqual(self.host.inventory["storage-pools"], [])
