from __future__ import annotations

import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import replace
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from tiny_swarm_world import installer
from tiny_swarm_world.application.services.native_preparation import (
    NativePreparationService,
)
from tiny_swarm_world.domain.native_preparation import GIB, NativeHostFacts
from tiny_swarm_world.domain.native_preparation import (
    HOST_PACKAGES_BY_PROFILE,
    HOST_PORTS_BY_PROFILE,
    PROFILE_MINIMUM_CPUS,
    PROFILE_MINIMUM_FREE_DISK_BYTES,
    PROFILE_MINIMUM_MEMORY_BYTES,
)
from tiny_swarm_world.prepare_linux import main, _prepare_python_dependencies, _prepare_remaining
from tiny_swarm_world.infrastructure.adapters.native_preparation_evidence import (
    NativePreparationEvidenceWriter,
)
from tiny_swarm_world.infrastructure.adapters.host.native_preparation import (
    NativePreparationInspector,
    _can_install_packages,
    _conflicting_runtime,
    _kernel_ready,
    _memory_bytes,
    _network_ready,
    _os_release,
    _port_available,
)


QUALIFIED = NativeHostFacts(
    platform="Linux",
    is_wsl=False,
    distribution_id="ubuntu",
    version_id="24.04",
    architecture="x86_64",
    cpu_count=8,
    memory_bytes=20 * GIB,
    free_disk_bytes=150 * GIB,
    can_install_packages=True,
    repository_writable=True,
    kernel_ready=True,
    ports_ready=True,
    conflicting_runtime=False,
    network_ready=True,
)


class NativePreparationInspectorTests(unittest.TestCase):
    def test_inspection_reports_actual_host_facts_without_mutation(self) -> None:
        with (
            patch("tiny_swarm_world.infrastructure.adapters.host.native_preparation._read") as read,
            patch("tiny_swarm_world.infrastructure.adapters.host.native_preparation.platform.system", return_value="Linux"),
            patch("tiny_swarm_world.infrastructure.adapters.host.native_preparation.platform.machine", return_value="x86_64"),
            patch("tiny_swarm_world.infrastructure.adapters.host.native_preparation.os.cpu_count", return_value=8),
            patch("tiny_swarm_world.infrastructure.adapters.host.native_preparation.os.access", return_value=True),
            patch("tiny_swarm_world.infrastructure.adapters.host.native_preparation.shutil.disk_usage", return_value=Mock(free=160 * GIB)) as disk,
            patch("tiny_swarm_world.infrastructure.adapters.host.native_preparation._can_install_packages", return_value=True),
            patch("tiny_swarm_world.infrastructure.adapters.host.native_preparation._port_available", return_value=True) as ports,
            patch("tiny_swarm_world.infrastructure.adapters.host.native_preparation._conflicting_runtime", return_value=False),
            patch("tiny_swarm_world.infrastructure.adapters.host.native_preparation._network_ready", return_value=True),
        ):
            values = {
                "/etc/os-release": 'ID=ubuntu\nVERSION_ID="26.04"\nNAME=Ubuntu\n',
                "/proc/sys/kernel/osrelease": "linux",
                "/proc/version": "Linux version 6",
                "/proc/meminfo": "MemTotal: 25165824 kB\n",
            }
            read.side_effect = lambda path: values.get(str(path), "1")
            facts = NativePreparationInspector(Path("/repo")).inspect()
        self.assertEqual(facts.distribution_id, "ubuntu")
        self.assertEqual(facts.version_id, "26.04")
        self.assertEqual(facts.memory_bytes, 24 * GIB)
        self.assertEqual(facts.free_disk_bytes, 160 * GIB)
        self.assertFalse(facts.is_wsl)
        self.assertTrue(facts.kernel_ready)
        self.assertTrue(facts.ports_ready)
        disk.assert_called_once_with(Path("/repo"))
        self.assertEqual(ports.call_count, len(HOST_PORTS_BY_PROFILE["service-access"]))

    def test_release_and_memory_parsers_fail_closed_on_missing_or_invalid_data(self) -> None:
        with patch("tiny_swarm_world.infrastructure.adapters.host.native_preparation._read", return_value='NAME=Ubuntu\nID=ubuntu\nVERSION_ID="26.04"\n'):
            self.assertEqual(_os_release(), {"ID": "ubuntu", "VERSION_ID": "26.04"})
        with patch("tiny_swarm_world.infrastructure.adapters.host.native_preparation._read", return_value="MemTotal: unknown kB\n"):
            self.assertEqual(_memory_bytes(), 0)
        with patch("tiny_swarm_world.infrastructure.adapters.host.native_preparation._read", return_value=""):
            self.assertEqual(_os_release(), {})
            self.assertEqual(_memory_bytes(), 0)

    def test_kernel_and_network_probes_fail_closed_then_accept_recovered_state(self) -> None:
        with patch("tiny_swarm_world.infrastructure.adapters.host.native_preparation._read", side_effect=("1", "0", "1")):
            self.assertFalse(_kernel_ready())
        with patch("tiny_swarm_world.infrastructure.adapters.host.native_preparation.socket.create_connection", side_effect=(OSError("offline"), MagicMock())) as connect:
            self.assertTrue(_network_ready())
            self.assertEqual(connect.call_count, 2)
        with patch("tiny_swarm_world.infrastructure.adapters.host.native_preparation.socket.create_connection", side_effect=OSError("offline")):
            self.assertFalse(_network_ready())

    def test_privilege_and_runtime_probe_fail_closed_when_tools_cannot_run(self) -> None:
        with (
            patch("tiny_swarm_world.infrastructure.adapters.host.native_preparation.os.geteuid", return_value=0),
            patch("tiny_swarm_world.infrastructure.adapters.host.native_preparation.SubprocessProcessRunner") as runner,
        ):
            self.assertTrue(_can_install_packages())
            runner.assert_not_called()
        with (
            patch("tiny_swarm_world.infrastructure.adapters.host.native_preparation.os.geteuid", return_value=1000),
            patch("tiny_swarm_world.infrastructure.adapters.host.native_preparation.shutil.which", return_value=None),
        ):
            self.assertFalse(_can_install_packages())
        with patch("tiny_swarm_world.infrastructure.adapters.host.native_preparation.shutil.which", side_effect=lambda name: "/usr/bin/lxd" if name == "lxd" else None):
            self.assertTrue(_conflicting_runtime())
        with patch("tiny_swarm_world.infrastructure.adapters.host.native_preparation.shutil.which", return_value=None):
            self.assertFalse(_conflicting_runtime())


class NativePreparationServiceTests(unittest.TestCase):
    def test_rejects_wsl_and_unsupported_release_before_package_inventory(self) -> None:
        for facts in (
            replace(QUALIFIED, is_wsl=True),
            replace(QUALIFIED, version_id="25.10"),
            replace(QUALIFIED, architecture="aarch64"),
        ):
            with self.subTest(facts=facts):
                inspector = Mock(inspect=Mock(return_value=facts))
                packages = Mock()
                plan = NativePreparationService(inspector, packages).plan()
                self.assertFalse(plan.qualified)
                packages.missing.assert_not_called()
                packages.install.assert_not_called()

    def test_both_ubuntu_lts_releases_are_qualified(self) -> None:
        for release in ("24.04", "26.04"):
            with self.subTest(release=release):
                facts = replace(QUALIFIED, version_id=release)
                packages = Mock(missing=Mock(return_value=()))
                plan = NativePreparationService(Mock(inspect=Mock(return_value=facts)), packages).plan()
                self.assertTrue(plan.qualified)
                packages.missing.assert_called_once()

    def test_service_access_resources_block_apt_before_mutation(self) -> None:
        facts = replace(QUALIFIED, cpu_count=4, memory_bytes=14 * GIB, free_disk_bytes=100 * GIB)
        packages = Mock(missing=Mock(return_value=("incus",)))
        service = NativePreparationService(Mock(inspect=Mock(return_value=facts)), packages)
        plan = service.plan()
        self.assertFalse(plan.qualified)
        self.assertIn("At least 8 CPU threads", " ".join(plan.failures))
        self.assertIn("At least 15 GiB of RAM", " ".join(plan.failures))
        self.assertIn("At least 150 GiB", " ".join(plan.failures))
        with self.assertRaisesRegex(ValueError, "preflight failed"):
            service.apply(plan)
        packages.install.assert_not_called()

    def test_service_access_memory_boundary(self) -> None:
        for memory, qualified in ((15 * GIB - 1, False), (15 * GIB, True)):
            with self.subTest(memory=memory):
                facts = replace(QUALIFIED, memory_bytes=memory)
                packages = Mock(missing=Mock(return_value=()))
                service = NativePreparationService(Mock(inspect=Mock(return_value=facts)), packages)
                self.assertEqual(qualified, service.plan().qualified)
                packages.install.assert_not_called()

    def test_default_profile_keeps_smaller_resource_floor(self) -> None:
        facts = replace(QUALIFIED, cpu_count=4, free_disk_bytes=60 * GIB)
        packages = Mock(missing=Mock(return_value=()))
        plan = NativePreparationService(
            Mock(inspect=Mock(return_value=facts)), packages, service_profile="default"
        ).plan()
        self.assertTrue(plan.qualified)

    def test_prepared_host_needs_no_sudo_permission(self) -> None:
        facts = replace(QUALIFIED, can_install_packages=False)
        packages = Mock(missing=Mock(return_value=()))
        plan = NativePreparationService(Mock(inspect=Mock(return_value=facts)), packages).plan()
        self.assertTrue(plan.qualified)

    def test_blocks_every_host_resource_and_safety_failure_before_install(self) -> None:
        facts = replace(
            QUALIFIED,
            cpu_count=1,
            memory_bytes=4 * GIB,
            free_disk_bytes=2 * GIB,
            can_install_packages=False,
            repository_writable=False,
            kernel_ready=False,
            ports_ready=False,
            conflicting_runtime=True,
            network_ready=False,
        )
        packages = Mock(missing=Mock(return_value=("incus",)))
        service = NativePreparationService(Mock(inspect=Mock(return_value=facts)), packages)
        plan = service.plan()
        self.assertGreaterEqual(len(plan.failures), 9)
        with self.assertRaisesRegex(ValueError, "preflight failed"):
            service.apply(plan)
        packages.install.assert_not_called()

    def test_installed_packages_are_noop_on_repeated_run(self) -> None:
        packages = Mock(missing=Mock(return_value=()))
        service = NativePreparationService(Mock(inspect=Mock(return_value=QUALIFIED)), packages)
        self.assertEqual(service.apply(service.plan()), ())
        self.assertEqual(service.apply(service.plan()), ())
        packages.install.assert_not_called()

    def test_rechecks_host_before_apt_and_verifies_afterward(self) -> None:
        inspector = Mock(inspect=Mock(side_effect=(QUALIFIED, QUALIFIED)))
        packages = Mock(missing=Mock(side_effect=(("incus",), ("incus",), ())))
        service = NativePreparationService(inspector, packages)
        plan = service.plan()
        self.assertEqual(service.apply(plan), ("incus",))
        packages.install.assert_called_once_with(("incus",))

    def test_host_change_after_confirmation_prevents_mutation(self) -> None:
        inspector = Mock(inspect=Mock(side_effect=(QUALIFIED, replace(QUALIFIED, cpu_count=1))))
        packages = Mock(missing=Mock(return_value=("incus",)))
        service = NativePreparationService(inspector, packages)
        with self.assertRaisesRegex(ValueError, "preflight changed"):
            service.apply(service.plan())
        packages.install.assert_not_called()

    def test_package_plan_drift_requires_new_confirmation(self) -> None:
        packages = Mock(missing=Mock(side_effect=(("incus",), ("incus", "jq"))))
        service = NativePreparationService(Mock(inspect=Mock(return_value=QUALIFIED)), packages)
        with self.assertRaisesRegex(ValueError, "plan changed"):
            service.apply(service.plan())
        packages.install.assert_not_called()

    def test_native_ports_match_setup_manifest(self) -> None:
        from tiny_swarm_world.domain.preflight import default_preflight_configuration

        for profile, ports in HOST_PORTS_BY_PROFILE.items():
            with self.subTest(profile=profile):
                expected = tuple(
                    item.port for item in default_preflight_configuration(service_profile=profile).required_ports
                )
                self.assertEqual(ports, expected)

    def test_service_access_resource_plan_matches_setup_preflight(self) -> None:
        from tiny_swarm_world.domain.preflight.resources import default_resource_profiles

        expected = default_resource_profiles()["service-access"].minimum
        self.assertEqual(PROFILE_MINIMUM_CPUS["service-access"], expected.cpu_threads)
        self.assertEqual(PROFILE_MINIMUM_MEMORY_BYTES["service-access"], expected.memory_bytes)
        self.assertEqual(PROFILE_MINIMUM_FREE_DISK_BYTES["service-access"], expected.free_disk_bytes)

    def test_incus_bridge_dependency_is_in_host_package_plan(self) -> None:
        self.assertIn("dnsmasq-base", HOST_PACKAGES_BY_PROFILE["service-access"])

    def test_occupied_port_is_detected(self) -> None:
        import socket

        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            self.assertFalse(_port_available(listener.getsockname()[1]))

    def test_sudo_capability_requires_actual_allowed_apt_command(self) -> None:
        with (
            patch("tiny_swarm_world.infrastructure.adapters.host.native_preparation.os.geteuid", return_value=1000),
            patch("tiny_swarm_world.infrastructure.adapters.host.native_preparation.shutil.which", return_value="/usr/bin/sudo"),
            patch("tiny_swarm_world.infrastructure.adapters.host.native_preparation.SubprocessProcessRunner") as runner,
        ):
            runner.return_value.run_text.return_value = subprocess.CompletedProcess((), 1, "", "")
            self.assertFalse(_can_install_packages())
            runner.return_value.run_text.return_value = subprocess.CompletedProcess((), 0, "", "")
            self.assertTrue(_can_install_packages())
        command = runner.return_value.run_text.call_args.args[0]
        self.assertEqual(command, ("sudo", "-n", "-l", "/usr/bin/apt-get"))

    def test_inactive_lxd_binary_is_not_treated_as_active_conflict(self) -> None:
        with (
            patch("tiny_swarm_world.infrastructure.adapters.host.native_preparation.shutil.which", return_value="/usr/bin/tool"),
            patch("tiny_swarm_world.infrastructure.adapters.host.native_preparation.SubprocessProcessRunner") as runner,
        ):
            runner.return_value.run_text.return_value = subprocess.CompletedProcess((), 3, "", "")
            self.assertFalse(_conflicting_runtime())
            self.assertEqual(runner.return_value.run_text.call_count, 3)
            runner.return_value.run_text.reset_mock()
            runner.return_value.run_text.side_effect = (
                subprocess.CompletedProcess((), 3, "", ""),
                subprocess.CompletedProcess((), 3, "", ""),
                subprocess.CompletedProcess((), 0, "", ""),
            )
            self.assertTrue(_conflicting_runtime())


class NativePreparationCliTests(unittest.TestCase):
    def setUp(self):
        paths = patch("tiny_swarm_world.prepare_linux._validate_mutation_paths", return_value=("mock-trusted-source",))
        paths.start()
        self.addCleanup(paths.stop)
        boundary = patch("tiny_swarm_world.prepare_linux.run_incus_preparation", return_value=0)
        self.incus_boundary = boundary.start()
        self.addCleanup(boundary.stop)
        network = patch("tiny_swarm_world.prepare_linux.run_network_preparation", return_value=0)
        self.network_boundary = network.start()
        self.addCleanup(network.stop)
        evidence = patch("tiny_swarm_world.prepare_linux.record_python_preparation", return_value=Path("/redacted/python-evidence"))
        evidence.start()
        self.addCleanup(evidence.stop)

    def test_handoff_requires_every_stage_and_preserves_failure_exit(self):
        for stage in ("python", "incus", "network"):
            for code in (2, 3, 4, 17, 124, 130):
                with (
                    self.subTest(stage=stage, code=code),
                    patch("tiny_swarm_world.prepare_linux._prepare_python_dependencies", return_value=code if stage == "python" else 0),
                    patch("tiny_swarm_world.prepare_linux.run_incus_preparation", return_value=code if stage == "incus" else 0) as incus,
                    patch("tiny_swarm_world.prepare_linux.run_network_preparation", return_value=code if stage == "network" else 0) as network,
                    redirect_stdout(io.StringIO()) as output,
                ):
                    self.assertEqual(_prepare_remaining(read_only=False, service_profile="default"), code)
                    self.assertNotIn("./install.sh", output.getvalue())
                    if stage == "python":
                        incus.assert_not_called()
                    if stage != "network":
                        network.assert_not_called()

    def test_successful_handoff_quotes_checkout_and_keeps_profile(self):
        with (
            patch("tiny_swarm_world.prepare_linux._prepare_python_dependencies", return_value=0),
            patch("tiny_swarm_world.prepare_linux.Path.cwd", return_value=Path("/home/operator/TSW checkout")),
            redirect_stdout(io.StringIO()) as output,
        ):
            self.assertEqual(_prepare_remaining(read_only=True, service_profile="default"), 0)
        self.assertIn("cd -- '/home/operator/TSW checkout' && ./install.sh --service-profile default", output.getvalue())
        self.assertIn("services are not verified", output.getvalue())

    def test_python_dependencies_are_prepared_only_after_separate_consent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = installer.InstallerPaths(
                Path(directory) / "operator.env", Path(directory) / "install-venv"
            )
            with (
                patch("tiny_swarm_world.infrastructure.composition_installation._paths_from_env", return_value=paths),
                patch("tiny_swarm_world.infrastructure.composition_installation._python_imports_available", side_effect=(False, False, True)),
                patch("tiny_swarm_world.infrastructure.composition_installation.ensure_python_environment", return_value="/prepared/python") as bootstrap,
                patch("tiny_swarm_world.infrastructure.composition_installation.detect_host_runtime") as runtime,
                patch("builtins.input", return_value="yes") as answer,
                redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(_prepare_python_dependencies(read_only=True), 2)
                bootstrap.assert_not_called()
                answer.assert_not_called()
                self.assertEqual(_prepare_python_dependencies(read_only=False), 0)
            bootstrap.assert_called_once_with(runtime.return_value, paths, os.environ)
            answer.assert_called_once()

    def test_skipped_python_bootstrap_never_reports_prepared_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = installer.InstallerPaths(
                Path(directory) / "operator.env", Path(directory) / "install-venv"
            )
            with (
                patch("tiny_swarm_world.infrastructure.composition_installation._paths_from_env", return_value=paths),
                patch("tiny_swarm_world.infrastructure.composition_installation._python_imports_available", return_value=False),
                patch("tiny_swarm_world.infrastructure.composition_installation.ensure_python_environment", return_value="python3") as bootstrap,
                patch("tiny_swarm_world.infrastructure.composition_installation.detect_host_runtime"),
                patch("builtins.input", return_value="yes"),
                redirect_stdout(io.StringIO()),
                redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(_prepare_python_dependencies(read_only=False), 1)
            bootstrap.assert_called_once()

    def test_prepared_host_has_no_unapproved_evidence_writes(self) -> None:
        facts = replace(QUALIFIED, version_id="26.04", can_install_packages=False)
        service = NativePreparationService(
            Mock(inspect=Mock(return_value=facts)), Mock(missing=Mock(return_value=()))
        )
        with (
            patch("tiny_swarm_world.prepare_linux.build_native_preparation_service", return_value=service),
            patch("tiny_swarm_world.prepare_linux.build_native_preparation_evidence_writer") as writer,
            redirect_stdout(io.StringIO()),
        ):
            writer.return_value.write.return_value = Path("/safe/evidence.json")
            self.assertEqual(main(("--preflight",)), 0)
            self.assertEqual(main(()), 0)
        writer.return_value.write.assert_not_called()
        self.assertEqual(writer.return_value.validate.call_count, 8)

    def test_entrypoint_imports_without_third_party_dependencies(self) -> None:
        result = subprocess.run(
            [sys.executable, "-S", "-c", "import tiny_swarm_world.prepare_linux"],
            env={**os.environ, "PYTHONPATH": "src"},
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_read_only_modes_never_apply_or_write_evidence(self) -> None:
        for option in ("--preflight", "--dry-run"):
            with self.subTest(option=option):
                service = NativePreparationService(
                    Mock(inspect=Mock(return_value=QUALIFIED)),
                    Mock(missing=Mock(return_value=("incus",))),
                )
                with (
                    patch("tiny_swarm_world.prepare_linux.build_native_preparation_service", return_value=service),
                    patch("tiny_swarm_world.prepare_linux.build_native_preparation_evidence_writer") as writer,
                    patch("builtins.input") as user_input,
                    redirect_stdout(io.StringIO()),
                ):
                    self.assertEqual(main((option,)), 2)
                user_input.assert_not_called()
                writer.return_value.write.assert_not_called()
                self.assertEqual(writer.return_value.validate.call_count, 4)

    def test_failure_prints_no_secret_or_apt_output(self) -> None:
        service = Mock()
        service.plan.return_value = NativePreparationService(
            Mock(inspect=Mock(return_value=QUALIFIED)),
            Mock(missing=Mock(return_value=("incus",))),
        ).plan()
        service.apply.side_effect = RuntimeError("secret-from-external-command")
        output = io.StringIO()
        with (
            patch("tiny_swarm_world.prepare_linux.build_native_preparation_service", return_value=service),
            patch("tiny_swarm_world.prepare_linux.build_native_preparation_evidence_writer") as writer,
            patch("builtins.input", return_value="yes"),
            redirect_stdout(io.StringIO()),
            redirect_stderr(output),
        ):
            writer.return_value.write.return_value = "/safe/evidence.json"
            self.assertEqual(main(()), 1)
        self.assertNotIn("secret-from-external-command", output.getvalue())
        self.assertIn("Package preparation stopped", output.getvalue())

    def test_evidence_failure_blocks_apt_and_interruption_records_partial_state(self) -> None:
        plan = NativePreparationService(
            Mock(inspect=Mock(return_value=QUALIFIED)),
            Mock(missing=Mock(return_value=("incus",))),
        ).plan()
        service = Mock()
        service.plan.return_value = plan
        evidence = Mock()
        evidence.write.side_effect = OSError("unwritable")
        with (
            patch("tiny_swarm_world.prepare_linux.build_native_preparation_service", return_value=service),
            patch("tiny_swarm_world.prepare_linux.build_native_preparation_evidence_writer", return_value=evidence),
            patch("builtins.input", return_value="yes"),
            redirect_stdout(io.StringIO()),
            redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(main(()), 1)
        service.apply.assert_not_called()

        evidence.write.side_effect = None
        evidence.write.return_value = Path("/safe/evidence.json")
        service.apply.side_effect = KeyboardInterrupt()
        with (
            patch("tiny_swarm_world.prepare_linux.build_native_preparation_service", return_value=service),
            patch("tiny_swarm_world.prepare_linux.build_native_preparation_evidence_writer", return_value=evidence),
            patch("builtins.input", return_value="yes"),
            redirect_stdout(io.StringIO()),
            redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(main(()), 130)
        self.assertEqual(evidence.write.call_args.kwargs["status"], "interrupted")

    def test_evidence_is_owner_only_and_contains_no_external_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = NativePreparationEvidenceWriter(Path(directory)).write(
                platform_release="26.04",
                status="failed",
                planned=("incus",),
                added=(),
                uncertain=("incus",),
                stage="package_install_or_verify",
            )
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(path.parent.stat().st_mode & 0o777, 0o700)
            self.assertEqual(path.parent.parent.stat().st_mode & 0o777, 0o700)
            self.assertEqual(path.parent.parent.parent.stat().st_mode & 0o777, 0o700)
            content = path.read_text()
            self.assertIn('"uncertain_packages": ["incus"]', content)
            self.assertIn('"platform": "ubuntu-26.04-x86_64"', content)
            self.assertNotIn("stdout", content)

    def test_evidence_rejects_insecure_existing_project_parent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "tiny-swarm-world"
            project.mkdir(mode=0o755)
            with self.assertRaisesRegex(OSError, "not private"):
                NativePreparationEvidenceWriter(Path(directory)).write(
                    platform_release="26.04", status="started", planned=("incus",),
                    added=(), uncertain=("incus",), stage="package_install_pending",
                )


if __name__ == "__main__":
    unittest.main()
