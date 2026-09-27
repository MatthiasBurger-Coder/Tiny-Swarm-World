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
from unittest.mock import Mock, patch

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
from tiny_swarm_world.prepare_linux import main, _prepare_python_dependencies
from tiny_swarm_world.infrastructure.adapters.native_preparation_evidence import (
    NativePreparationEvidenceWriter,
)
from tiny_swarm_world.infrastructure.adapters.host.native_preparation import (
    _can_install_packages,
    _conflicting_runtime,
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
        facts = replace(QUALIFIED, cpu_count=4, memory_bytes=18 * GIB, free_disk_bytes=100 * GIB)
        packages = Mock(missing=Mock(return_value=("incus",)))
        service = NativePreparationService(Mock(inspect=Mock(return_value=facts)), packages)
        plan = service.plan()
        self.assertFalse(plan.qualified)
        self.assertIn("At least 8 CPU threads", " ".join(plan.failures))
        self.assertIn("At least 20 GiB of RAM", " ".join(plan.failures))
        self.assertIn("At least 150 GiB", " ".join(plan.failures))
        with self.assertRaisesRegex(ValueError, "preflight failed"):
            service.apply(plan)
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
    def test_python_dependencies_are_prepared_only_after_separate_consent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = installer.InstallerPaths(
                Path(directory) / "operator.env", Path(directory) / "install-venv"
            )
            with (
                patch("tiny_swarm_world.installer._paths_from_env", return_value=paths),
                patch("tiny_swarm_world.installer._python_imports_available", side_effect=(False, False, True)),
                patch("tiny_swarm_world.installer.ensure_python_environment", return_value="/prepared/python") as bootstrap,
                patch("tiny_swarm_world.installer.detect_host_runtime") as runtime,
                patch("builtins.input", return_value="yes") as answer,
                redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(_prepare_python_dependencies(read_only=True), 0)
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
                patch("tiny_swarm_world.installer._paths_from_env", return_value=paths),
                patch("tiny_swarm_world.installer._python_imports_available", return_value=False),
                patch("tiny_swarm_world.installer.ensure_python_environment", return_value="python3") as bootstrap,
                patch("tiny_swarm_world.installer.detect_host_runtime"),
                patch("builtins.input", return_value="yes"),
                redirect_stdout(io.StringIO()),
                redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(_prepare_python_dependencies(read_only=False), 1)
            bootstrap.assert_called_once()

    def test_prepared_host_records_noop_only_for_mutating_entrypoint(self) -> None:
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
            writer.assert_not_called()
            self.assertEqual(main(()), 0)
        self.assertEqual(writer.return_value.write.call_args.kwargs["status"], "noop")
        self.assertEqual(writer.return_value.write.call_args.kwargs["platform_release"], "26.04")

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
                    self.assertEqual(main((option,)), 0)
                user_input.assert_not_called()
                writer.assert_not_called()

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
