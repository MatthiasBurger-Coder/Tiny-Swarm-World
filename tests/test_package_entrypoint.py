import asyncio
import ast
import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from tiny_swarm_world import __main__ as entrypoint
from tiny_swarm_world.application.services.artifacts import (
    ArtifactWorkflowKind,
    ArtifactWorkflowResult,
    ArtifactWorkflowStatus,
)
from tiny_swarm_world.application.services.deployment import (
    DeploymentWorkflowKind,
    DeploymentWorkflowResult,
    DeploymentWorkflowStatus,
)
from tiny_swarm_world.application.services.setup import (
    SetupPhaseResult,
    SetupWorkflowKind,
    SetupWorkflowResult,
    SetupWorkflowStatus,
)
from tiny_swarm_world.application.services.platform.preflight_service import (
    PreflightService,
)
from tiny_swarm_world.application.services.platform.workflow_taxonomy import (
    DESTROY_TINY_SWARM_PLATFORM_CONFIRMATION,
    RESET_TINY_SWARM_PLATFORM_CONFIRMATION,
    PlatformWorkflowKind,
    PlatformWorkflowResult,
    PlatformWorkflowStatus,
)
from tiny_swarm_world.domain.deployment import ServiceStackProfile
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus
from tiny_swarm_world.domain.node_provider import ManagedLxcBackend, NodeProviderKind
from tiny_swarm_world.domain.preflight import (
    HostEnvironmentKind,
    HostEnvironmentReport,
    PreflightCategory,
    PreflightCheck,
    PreflightResult,
    PreflightSeverity,
    PreflightStatus,
    SetupPath,
)
from tiny_swarm_world.domain.project_filesystem import (
    ProjectFilesystemInspection,
    ProjectFilesystemKind,
    assess_project_filesystem,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT_PATH = REPOSITORY_ROOT / "src" / "tiny_swarm_world" / "__main__.py"


class TestPackageEntrypoint(unittest.IsolatedAsyncioTestCase):
    async def test_default_entrypoint_does_not_build_or_run_services(self):
        output = io.StringIO()

        with patch.object(entrypoint, "build_application_services") as build_services:
            with redirect_stdout(output):
                await entrypoint.main([])

        build_services.assert_not_called()
        self.assertIn("No workflow selected", output.getvalue())
        self.assertIn("--list-workflows", output.getvalue())

    async def test_default_entrypoint_normalizes_common_linux_executable_paths(self):
        output = io.StringIO()

        with patch.object(entrypoint, "ensure_common_executable_paths") as normalize_paths:
            with redirect_stdout(output):
                await entrypoint.main([])

        normalize_paths.assert_called_once_with()

    async def test_list_workflows_does_not_build_or_run_services(self):
        output = io.StringIO()

        with patch.object(entrypoint, "build_application_services") as build_services:
            with redirect_stdout(output):
                await entrypoint.main(["--list-workflows"])

        build_services.assert_not_called()
        self.assertIn("platform init", output.getvalue())
        self.assertIn("platform reconcile", output.getvalue())
        self.assertIn("platform expose", output.getvalue())
        self.assertIn("platform repair-lxc-proxy-drift", output.getvalue())
        self.assertIn("platform reset", output.getvalue())
        self.assertIn("deployment bootstrap", output.getvalue())
        self.assertIn("deployment apply", output.getvalue())
        self.assertIn("setup run", output.getvalue())
        self.assertIn("host detect", output.getvalue())
        self.assertNotIn("vm-ip-list", output.getvalue())
        self.assertNotIn("multipass-init-vms", output.getvalue())

    def test_parse_args_accepts_host_detect_as_read_only(self):
        args = entrypoint.parse_args(["host", "detect"])

        self.assertEqual("host detect", args.workflow.name)
        self.assertFalse(args.workflow.mutating)
        self.assertTrue(args.workflow.implemented)

    async def test_host_detect_human_output_is_complete_and_read_only(self):
        output = io.StringIO()
        report = _host_report(HostEnvironmentKind.WSL2, SetupPath.WSL2)
        service = _HostDetectionService(report)

        with (
            patch.object(
                entrypoint,
                "build_host_detection_service",
                return_value=service,
            ),
            patch.object(
                entrypoint,
                "ensure_common_executable_paths",
            ) as ensure_paths,
            patch.object(entrypoint, "build_application_logger") as build_logger,
            patch.object(entrypoint, "build_application_services") as build_services,
            redirect_stdout(output),
        ):
            await entrypoint.main(["host", "detect"])

        rendered = output.getvalue()
        self.assertIn("Host environment", rendered)
        self.assertIn("Type: wsl2", rendered)
        self.assertIn("Distribution: Ubuntu-24.04", rendered)
        self.assertIn("Kernel release: 6.1.21.2-microsoft-standard-WSL2", rendered)
        self.assertIn("Windows interop: unavailable", rendered)
        self.assertIn("Supported: yes", rendered)
        self.assertIn("Setup path: wsl2", rendered)
        self.assertEqual(1, service.calls)
        ensure_paths.assert_not_called()
        build_logger.assert_not_called()
        build_services.assert_not_called()

    async def test_host_detect_json_stdout_is_exact_and_repeatable(self):
        report = _host_report(HostEnvironmentKind.WSL2, SetupPath.WSL2)
        rendered: list[str] = []

        for _ in range(2):
            output = io.StringIO()
            with (
                patch.object(
                    entrypoint,
                    "build_host_detection_service",
                    return_value=_HostDetectionService(report),
                ),
                redirect_stdout(output),
            ):
                await entrypoint.main(["--json", "host", "detect"])
            rendered.append(output.getvalue())

        payload = json.loads(rendered[0])
        self.assertEqual(
            {**report.to_dict(), "live_readiness_verified": False},
            payload,
        )
        self.assertEqual(rendered[0], rendered[1])
        _, end_index = json.JSONDecoder().raw_decode(rendered[0])
        self.assertEqual("", rendered[0][end_index:].strip())

    async def test_unsupported_host_detect_emits_remediation_and_exits_one(self):
        output = io.StringIO()
        report = _host_report(
            HostEnvironmentKind.WSL1_UNSUPPORTED,
            SetupPath.UNSUPPORTED,
        )

        with (
            patch.object(
                entrypoint,
                "build_host_detection_service",
                return_value=_HostDetectionService(report),
            ),
            redirect_stdout(output),
        ):
            with self.assertRaises(SystemExit) as raised:
                await entrypoint.main(["host", "detect"])

        self.assertEqual(1, raised.exception.code)
        self.assertIn("Supported: no", output.getvalue())
        self.assertIn("Upgrade to WSL2", output.getvalue())

    async def test_unsupported_host_detect_json_remains_parseable_before_exit(self):
        output = io.StringIO()
        report = _host_report(
            HostEnvironmentKind.UNKNOWN_UNSUPPORTED,
            SetupPath.UNSUPPORTED,
        )

        with (
            patch.object(
                entrypoint,
                "build_host_detection_service",
                return_value=_HostDetectionService(report),
            ),
            redirect_stdout(output),
        ):
            with self.assertRaises(SystemExit) as raised:
                await entrypoint.main(["--json", "host", "detect"])

        self.assertEqual(1, raised.exception.code)
        self.assertEqual(
            {**report.to_dict(), "live_readiness_verified": False},
            json.loads(output.getvalue()),
        )

    async def test_host_detect_runs_no_process_or_file_mutation(self):
        report = _host_report(HostEnvironmentKind.NATIVE_LINUX, SetupPath.NATIVE_LINUX)

        with (
            patch.object(
                entrypoint,
                "build_host_detection_service",
                return_value=_HostDetectionService(report),
            ),
            patch.object(
                entrypoint,
                "ensure_common_executable_paths",
            ) as ensure_paths,
            patch.object(entrypoint, "build_application_logger") as build_logger,
            patch.object(Path, "mkdir") as mkdir,
            patch(
                "subprocess.run",
                side_effect=AssertionError("host detect must not run a process"),
            ),
            patch(
                "asyncio.create_subprocess_exec",
                side_effect=AssertionError("host detect must not run an async process"),
            ),
            patch(
                "asyncio.create_subprocess_shell",
                side_effect=AssertionError("host detect must not run an async shell"),
            ),
            patch.object(
                Path,
                "write_text",
                side_effect=AssertionError("host detect must not write files"),
            ),
            redirect_stdout(io.StringIO()),
        ):
            await entrypoint.main(["host", "detect"])

        ensure_paths.assert_not_called()
        build_logger.assert_not_called()
        mkdir.assert_not_called()

    async def test_native_host_reports_windows_interop_as_not_applicable(self):
        output = io.StringIO()
        report = _host_report(
            HostEnvironmentKind.NATIVE_LINUX,
            SetupPath.NATIVE_LINUX,
        )

        with (
            patch.object(
                entrypoint,
                "build_host_detection_service",
                return_value=_HostDetectionService(report),
            ),
            redirect_stdout(output),
        ):
            await entrypoint.main(["host", "detect"])

        self.assertIn("Windows interop: not applicable", output.getvalue())
        self.assertIn("Live readiness verified: no", output.getvalue())

    def test_legacy_run_option_is_rejected(self):
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                entrypoint.parse_args(["--run", "vm-ip-list"])

    def test_service_profile_defaults_to_service_access(self):
        args = entrypoint.parse_args([])

        self.assertEqual(ServiceStackProfile.SERVICE_ACCESS.value, args.service_profile)
        self.assertEqual(NodeProviderKind.LXC_NATIVE.value, args.node_provider)
        self.assertIsNone(args.lxc_backend)
        self.assertFalse(args.json)
        self.assertFalse(args.allow_wsl_windows_filesystem)

    def test_parse_args_accepts_exact_wsl_windows_filesystem_override(self):
        args = entrypoint.parse_args(["--allow-wsl-windows-filesystem"])

        self.assertTrue(args.allow_wsl_windows_filesystem)

    def test_json_flag_enables_machine_readable_output(self):
        args = entrypoint.parse_args(["--json"])

        self.assertTrue(args.json)

    def test_lxc_backend_option_is_forwarded_as_provider_preference(self):
        args = entrypoint.parse_args(["--lxc-backend", "incus"])

        self.assertEqual(NodeProviderKind.LXC_NATIVE.value, args.node_provider)
        self.assertEqual(ManagedLxcBackend.INCUS.value, args.lxc_backend)

    def test_multipass_provider_option_is_rejected(self):
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                entrypoint.parse_args(["--node-provider", "multipass_legacy"])

    def test_setup_installation_plan_lists_service_access_landing_page(self):
        output = io.StringIO()

        with redirect_stdout(output):
            entrypoint._print_setup_installation_plan()

        plan = output.getvalue()
        self.assertIn("Default node provider: lxc_native", plan)
        self.assertIn("Managed backend: Incus", plan)
        self.assertIn("Provider readiness: checked before platform mutation", plan)
        self.assertIn("Service profile: service-access", plan)
        self.assertIn("Traefik Ingress: stack traefik", plan)
        self.assertIn("compose service(s) traefik, published port(s) 80, 443", plan)
        self.assertIn("Service Access: stack service-access", plan)
        self.assertIn(
            "compose service(s) service-access-dashboard, service-access-nginx, "
            "published port(s) 10000, 8086",
            plan,
        )
        self.assertIn("Infisical: stack infisical", plan)
        self.assertIn("compose service(s) infisical, infisical-db, infisical-redis", plan)
        self.assertIn("Jenkins: stack jenkins", plan)
        self.assertIn("published port(s) 11080, 11050", plan)
        self.assertNotIn("Target: local Linux/WSL Multipass Docker Swarm", plan)

    async def test_mutating_workflow_requires_live_consent_before_building_services(self):
        output = io.StringIO()

        with patch.object(entrypoint, "build_application_services") as build_services:
            with redirect_stdout(output):
                with self.assertRaises(SystemExit) as raised:
                    await entrypoint.main(["platform", "init"])

        self.assertEqual(2, raised.exception.code)
        build_services.assert_not_called()
        self.assertIn("REFUSED_LIVE_CONSENT_MISSING", output.getvalue())
        self.assertIn("missing --live", output.getvalue())

    async def test_mutating_workflow_refuses_negative_live_confirmation(self):
        output = io.StringIO()

        with patch("builtins.input", return_value="n"):
            with patch.object(entrypoint, "build_application_services") as build_services:
                with redirect_stdout(output):
                    with self.assertRaises(SystemExit) as raised:
                        await entrypoint.main(["platform", "init", "--live"])

        self.assertEqual(2, raised.exception.code)
        build_services.assert_not_called()
        self.assertIn("missing live confirmation", output.getvalue())

    async def test_mutating_workflow_accepts_short_yes_confirmation(self):
        services, workflows = _application_services_with_platform_workflows()
        output = io.StringIO()

        with patch("builtins.input", return_value="y"):
            with patch.object(entrypoint, "build_application_services", return_value=services):
                with redirect_stdout(output):
                    await entrypoint.main(["platform", "init", "--live"])

        workflows.init.run.assert_awaited_once_with()
        self.assertIn("Workflow: platform init", output.getvalue())
        self.assertNotIn('{\n', output.getvalue())

    async def test_mutating_workflow_accepts_explicit_noninteractive_live_approval(self):
        services, workflows = _application_services_with_platform_workflows()
        output = io.StringIO()

        with patch("builtins.input", side_effect=AssertionError("prompt must not run")):
            with patch.object(entrypoint, "build_application_services", return_value=services):
                with redirect_stdout(output):
                    await entrypoint.main(["platform", "init", "--live", "--approve-live"])

        workflows.init.run.assert_awaited_once_with()
        self.assertIn("Workflow: platform init", output.getvalue())
        self.assertNotIn('{\n', output.getvalue())

    async def test_mutating_workflow_refuses_noninteractive_eof(self):
        output = io.StringIO()

        with patch("builtins.input", side_effect=EOFError):
            with patch.object(entrypoint, "build_application_services") as build_services:
                with redirect_stdout(output):
                    with self.assertRaises(SystemExit) as raised:
                        await entrypoint.main(["platform", "init", "--live"])

        self.assertEqual(2, raised.exception.code)
        build_services.assert_not_called()
        self.assertIn("missing live confirmation", output.getvalue())

    async def test_platform_init_dispatches_to_composed_workflow_with_live_consent(self):
        services, workflows = _application_services_with_platform_workflows()
        output = io.StringIO()

        with patch("builtins.input", return_value="y"):
            with patch.object(entrypoint, "build_application_services", return_value=services):
                with redirect_stdout(output):
                    await entrypoint.main(["platform", "init", "--live"])

        workflows.init.run.assert_awaited_once_with()
        workflows.reconcile.run.assert_not_awaited()
        workflows.expose.run.assert_not_awaited()
        self.assertIn("Workflow: platform init", output.getvalue())
        self.assertNotIn('{\n', output.getvalue())

    async def test_workflow_summary_prints_verification_evidence(self):
        services, workflows = _application_services_with_platform_workflows(
            init_result=_blocked_platform_init_result()
        )
        output = io.StringIO()

        with patch.object(entrypoint, "build_application_services", return_value=services):
            with redirect_stdout(output):
                with self.assertRaises(SystemExit) as raised:
                    await entrypoint.main(["platform", "init", "--live", "--approve-live"])

        self.assertEqual(1, raised.exception.code)
        workflows.init.run.assert_awaited_once_with()
        rendered = output.getvalue()
        self.assertIn("Verification summary:", rendered)
        self.assertIn("- platform:init:preflight: blocked", rendered)
        self.assertIn("  Evidence:", rendered)
        self.assertIn("  - failed_check_count: 1", rendered)
        self.assertIn("  - phase: pre_apply", rendered)

    async def test_platform_reconcile_cli_output_reports_converged_outcome(self):
        reconcile_result = PlatformWorkflowResult(
            kind=PlatformWorkflowKind.RECONCILE,
            status=PlatformWorkflowStatus.COMPLETED,
            message="reconcile workflow completed.",
            executed=True,
            verification_results=(
                VerificationResult(
                    target_id="platform:node:swarm-worker-1",
                    status=VerificationStatus.VERIFIED,
                    message="Node was reconciled.",
                    evidence={
                        "phase": "apply",
                        "classification": "started",
                        "applied": "true",
                    },
                ),
            ),
        )
        services, workflows = _application_services_with_platform_workflows(
            reconcile_result=reconcile_result
        )
        output = io.StringIO()

        with patch.object(entrypoint, "build_application_services", return_value=services):
            with redirect_stdout(output):
                await entrypoint.main(
                    ["platform", "reconcile", "--live", "--approve-live", "--json"]
                )

        workflows.reconcile.run.assert_awaited_once_with()
        payload = _json_payload_from_output(output.getvalue())
        self.assertEqual("platform reconcile", payload["workflow"])
        self.assertEqual("converged", payload["outcome"]["mutation"]["result"])
        self.assertEqual("verified", payload["outcome"]["verification"])

    async def test_platform_init_uses_composed_guarded_workflow_result(self):
        services, workflows = _application_services_with_platform_workflows(
            init_result=_blocked_platform_init_result()
        )
        output = io.StringIO()

        with patch("builtins.input", return_value="y"):
            with patch.object(entrypoint, "build_application_services", return_value=services):
                with redirect_stdout(output):
                    with self.assertRaises(SystemExit) as raised:
                        await entrypoint.main(["platform", "init", "--live", "--json"])

        self.assertEqual(1, raised.exception.code)
        services.platform.preflight.run.assert_not_awaited()
        workflows.init.run.assert_awaited_once_with()
        payload = _json_payload_from_output(output.getvalue())
        self.assertEqual("platform init", payload["workflow"])
        self.assertEqual("blocked", payload["status"])
        self.assertFalse(payload["executed"])
        self.assertEqual(
            "1",
            payload["verification_results"][0]["evidence"]["runtime_failure_count"],
        )

    async def test_platform_verify_dispatches_without_live_consent(self):
        services, workflows = _application_services_with_platform_workflows()
        output = io.StringIO()

        with patch.object(entrypoint, "build_application_services", return_value=services) as build_services:
            with redirect_stdout(output):
                await entrypoint.main(["platform", "verify"])

        build_services.assert_called_once_with(
            live_consent=None,
            service_profile=ServiceStackProfile.SERVICE_ACCESS.value,
            node_provider_request=None,
            allow_wsl_windows_filesystem=False,
        )
        workflows.verify.run.assert_awaited_once_with()
        workflows.init.run.assert_not_awaited()
        self.assertIn("Workflow: platform verify", output.getvalue())
        self.assertNotIn('{\n', output.getvalue())

    def test_lxd_backend_option_is_rejected(self):
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                entrypoint.parse_args(["--lxc-backend", "lxd"])

    async def test_explicit_lxc_backend_override_builds_provider_request(self):
        services, workflows = _application_services_with_platform_workflows()
        output = io.StringIO()

        with patch.object(entrypoint, "build_application_services", return_value=services) as build_services:
            with redirect_stdout(output):
                await entrypoint.main(["--lxc-backend", "incus", "platform", "verify"])

        build_services.assert_called_once()
        request = build_services.call_args.kwargs["node_provider_request"]
        self.assertEqual(
            entrypoint.NodeProviderSelectionRequest(
                requested_provider=entrypoint.NodeProviderKind.LXC_NATIVE,
                preferred_backend=entrypoint.ManagedLxcBackend.INCUS,
            ),
            request,
        )
        workflows.verify.run.assert_awaited_once_with()

    async def test_platform_expose_requires_live_consent_and_dispatches(self):
        services, workflows = _application_services_with_platform_workflows()
        output = io.StringIO()

        with patch("builtins.input", return_value="y"):
            with patch.object(entrypoint, "build_application_services", return_value=services):
                with redirect_stdout(output):
                    await entrypoint.main(["platform", "expose", "--live"])

        workflows.expose.run.assert_awaited_once_with()
        workflows.init.run.assert_not_awaited()
        self.assertIn("Workflow: platform expose", output.getvalue())
        self.assertNotIn('{\n', output.getvalue())

    async def test_platform_repair_lxc_proxy_drift_requires_live_consent_and_dispatches(self):
        services, workflows = _application_services_with_platform_workflows()
        output = io.StringIO()

        with patch("builtins.input", return_value="y"):
            with patch.object(entrypoint, "build_application_services", return_value=services):
                with redirect_stdout(output):
                    await entrypoint.main(["platform", "repair-lxc-proxy-drift", "--live"])

        workflows.repair_lxc_proxy_drift.run.assert_awaited_once_with()
        workflows.expose.run.assert_not_awaited()
        self.assertIn("Workflow: platform repair-lxc-proxy-drift", output.getvalue())
        self.assertNotIn('{\n', output.getvalue())

    async def test_reset_refuses_missing_confirmation_before_building_services(self):
        output = io.StringIO()

        with patch.object(entrypoint, "build_application_services") as build_services:
            with redirect_stdout(output):
                with self.assertRaises(SystemExit) as raised:
                    await entrypoint.main(["platform", "reset"])

        self.assertEqual(2, raised.exception.code)
        build_services.assert_not_called()
        self.assertIn("REFUSED_WORKFLOW_CONFIRMATION_MISSING", output.getvalue())
        self.assertIn(RESET_TINY_SWARM_PLATFORM_CONFIRMATION, output.getvalue())

    async def test_destroy_refuses_wrong_confirmation_before_building_services(self):
        output = io.StringIO()

        with patch.object(entrypoint, "build_application_services") as build_services:
            with redirect_stdout(output):
                with self.assertRaises(SystemExit) as raised:
                    await entrypoint.main(["platform", "destroy", "--confirm", "wrong"])

        self.assertEqual(2, raised.exception.code)
        build_services.assert_not_called()
        self.assertIn("REFUSED_WORKFLOW_CONFIRMATION_MISSING", output.getvalue())
        self.assertIn(DESTROY_TINY_SWARM_PLATFORM_CONFIRMATION, output.getvalue())

    async def test_confirmed_reset_dispatches_to_composed_workflow(self):
        services, workflows = _application_services_with_platform_workflows()

        with patch("builtins.input", return_value="y"):
            with patch.object(entrypoint, "build_application_services", return_value=services):
                with redirect_stdout(io.StringIO()):
                    await entrypoint.main(
                        [
                            "platform",
                            "reset",
                            "--confirm",
                            RESET_TINY_SWARM_PLATFORM_CONFIRMATION,
                            "--live",
                        ]
                    )

        workflows.reset.run.assert_awaited_once_with(RESET_TINY_SWARM_PLATFORM_CONFIRMATION)
        workflows.destroy.run.assert_not_awaited()

    async def test_confirmed_destroy_dispatches_to_composed_workflow(self):
        services, workflows = _application_services_with_platform_workflows()

        with patch("builtins.input", return_value="y"):
            with patch.object(entrypoint, "build_application_services", return_value=services):
                with redirect_stdout(io.StringIO()):
                    await entrypoint.main(
                        [
                            "platform",
                            "destroy",
                            "--confirm",
                            DESTROY_TINY_SWARM_PLATFORM_CONFIRMATION,
                            "--live",
                        ]
                    )

        workflows.destroy.run.assert_awaited_once_with(DESTROY_TINY_SWARM_PLATFORM_CONFIRMATION)
        workflows.reset.run.assert_not_awaited()

    async def test_artifact_and_deployment_mutating_workflows_require_live_consent_before_services(
        self,
    ):
        for command in (
            ["artifacts", "prepare"],
            ["deployment", "bootstrap"],
            ["deployment", "apply"],
            ["setup", "run"],
        ):
            with self.subTest(command=command):
                output = io.StringIO()

                with patch.object(entrypoint, "build_application_services") as build_services:
                    with patch.object(
                        entrypoint,
                        "build_artifact_services_for_provider",
                    ) as build_artifact_services:
                        with patch.object(
                            entrypoint,
                            "build_deployment_services_for_provider",
                        ) as build_deployment_services:
                            with patch.object(
                                entrypoint,
                                "run_setup_with_terminal_status",
                            ) as run_setup:
                                with redirect_stdout(output):
                                    with self.assertRaises(SystemExit) as raised:
                                        await entrypoint.main(command)

                self.assertEqual(2, raised.exception.code)
                build_services.assert_not_called()
                build_artifact_services.assert_not_called()
                build_deployment_services.assert_not_called()
                run_setup.assert_not_called()
                self.assertIn("REFUSED_LIVE_CONSENT_MISSING", output.getvalue())
                await asyncio.sleep(0)

    async def test_artifact_and_deployment_workflows_dispatch_to_contract_blocks(self):
        cases = (
            ("artifacts", "prepare", True, "live registry and Nexus contracts"),
            ("artifacts", "verify", False, "observed-state verification"),
            ("deployment", "bootstrap", True, "Portainer and Nexus bootstrap"),
            ("deployment", "apply", True, "Portainer stack changes"),
            ("deployment", "verify", False, "observed-state verification"),
        )

        for namespace, action, requires_live, expected_reason in cases:
            with self.subTest(workflow=f"{namespace} {action}"):
                artifact_services, deployment_services, runs = _boundary_service_bundles()
                output = io.StringIO()
                command = [namespace, action]
                if requires_live:
                    command.append("--live")

                with patch.object(
                    entrypoint,
                    "build_application_services",
                    side_effect=AssertionError("boundary workflow must not build platform services"),
                ) as build_application_services:
                    with patch.object(
                        entrypoint,
                        "build_artifact_services_for_provider",
                        return_value=artifact_services,
                    ) as build_artifact_services:
                        with patch.object(
                            entrypoint,
                            "build_deployment_services_for_provider",
                            return_value=deployment_services,
                        ) as build_deployment_services:
                            with redirect_stdout(output):
                                with self.assertRaises(SystemExit) as raised:
                                    if requires_live:
                                        with patch("builtins.input", return_value="y"):
                                            await entrypoint.main([*command, "--json"])
                                    else:
                                        await entrypoint.main([*command, "--json"])

                self.assertEqual(1, raised.exception.code)
                build_application_services.assert_not_called()
                if namespace == "artifacts":
                    build_artifact_services.assert_called_once_with(
                        node_provider_request=None
                    )
                    build_deployment_services.assert_not_called()
                else:
                    build_artifact_services.assert_not_called()
                    build_deployment_services.assert_called_once_with(
                        service_profile=ServiceStackProfile.SERVICE_ACCESS.value,
                        node_provider_request=None,
                    )
                runs[(namespace, action)].assert_awaited_once_with()
                payload = _json_payload_from_output(output.getvalue())
                self.assertFalse(payload["executed"])
                self.assertEqual("blocked", payload["status"])
                self.assertEqual(f"{namespace} {action}", payload["workflow"])
                self.assertIn(expected_reason, str(payload["reason"]))
                await asyncio.sleep(0)

    async def test_setup_run_dispatches_to_setup_workflow_after_live_consent(self):
        setup_result = SetupWorkflowResult(
            kind=SetupWorkflowKind.RUN,
            status=SetupWorkflowStatus.BLOCKED,
            message="setup run stopped during phase 'platform init'.",
            reason="phase 'platform init' returned blocked",
            executed=True,
        )
        output = io.StringIO()

        with patch("builtins.input", return_value="y"):
            with patch.object(
                entrypoint,
                "run_setup_with_terminal_status",
                return_value=setup_result,
            ) as run_setup:
                with patch.object(
                    entrypoint,
                    "build_application_services",
                    side_effect=AssertionError("setup must use setup services"),
                ):
                    with redirect_stdout(output):
                        with self.assertRaises(SystemExit) as raised:
                            await entrypoint.main(["setup", "run", "--live", "--json"])

        self.assertEqual(1, raised.exception.code)
        run_setup.assert_awaited_once()
        live_consent = run_setup.call_args.args[0]
        self.assertTrue(live_consent.accepted)
        self.assertEqual("run", run_setup.call_args.args[1])
        self.assertEqual(
            {
                "service_profile": ServiceStackProfile.SERVICE_ACCESS.value,
                "node_provider_request": None,
                "allow_wsl_windows_filesystem": False,
            },
            run_setup.call_args.kwargs,
        )
        payload = _json_payload_from_output(output.getvalue())
        self.assertEqual("setup run", payload["workflow"])
        self.assertEqual("blocked", payload["status"])

    async def test_setup_run_propagates_explicit_wsl_filesystem_override(self):
        setup_result = SetupWorkflowResult(
            kind=SetupWorkflowKind.RUN,
            status=SetupWorkflowStatus.BLOCKED,
            message="setup run stopped during phase 'preflight'.",
            reason="phase 'preflight' returned blocked",
            executed=True,
        )

        with patch.object(
            entrypoint,
            "run_setup_with_terminal_status",
            return_value=setup_result,
        ) as run_setup:
            with redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit):
                    await entrypoint.main(
                        [
                            "setup",
                            "run",
                            "--live",
                            "--approve-live",
                            "--allow-wsl-windows-filesystem",
                        ]
                    )

        self.assertTrue(
            run_setup.call_args.kwargs["allow_wsl_windows_filesystem"]
        )

    async def test_setup_run_propagates_composition_lifecycle_failure(self):
        with patch("builtins.input", return_value="y"):
            with patch.object(
                entrypoint,
                "run_setup_with_terminal_status",
                side_effect=RuntimeError("boom"),
            ) as run_setup:
                with redirect_stdout(io.StringIO()):
                    with self.assertRaises(RuntimeError):
                        await entrypoint.main(["setup", "run", "--live"])

        run_setup.assert_awaited_once()

    def test_setup_summary_prints_failed_preflight_checks(self):
        result = SetupWorkflowResult(
            kind=SetupWorkflowKind.RUN,
            status=SetupWorkflowStatus.FAILED,
            message="setup run stopped during phase 'preflight'.",
            reason="phase 'preflight' returned failed",
            executed=True,
            phase_results=(
                SetupPhaseResult(
                    name="preflight",
                    status="failed",
                    result=PreflightResult(
                        (
                            PreflightCheck(
                                check_id="DEPENDENCY-docker",
                                category=PreflightCategory.DEPENDENCY,
                                status=PreflightStatus.FAILED,
                                severity=PreflightSeverity.MANDATORY,
                                message="Dependency 'docker' is missing.",
                                remediation="Install 'docker' or make it available on PATH.",
                            ),
                        )
                    ),
                ),
            ),
        )
        output = io.StringIO()

        with redirect_stdout(output):
            entrypoint._print_setup_installation_summary(result)

        rendered = output.getvalue()
        self.assertIn("- preflight: failed", rendered)
        self.assertIn("Failed preflight checks:", rendered)
        self.assertIn("DEPENDENCY-docker: Dependency 'docker' is missing.", rendered)
        self.assertIn("Action: Install 'docker' or make it available on PATH.", rendered)

    def test_setup_summary_prints_failed_platform_phase_verification(self):
        result = SetupWorkflowResult(
            kind=SetupWorkflowKind.RUN,
            status=SetupWorkflowStatus.FAILED_TO_APPLY,
            message="setup run stopped during phase 'platform init'.",
            reason="phase 'platform init' returned failed_to_apply",
            executed=True,
            phase_results=(
                SetupPhaseResult(
                    name="platform init",
                    status="failed_to_apply",
                    result=PlatformWorkflowResult(
                        kind=PlatformWorkflowKind.INIT,
                        status=PlatformWorkflowStatus.FAILED_TO_APPLY,
                        message="init workflow stopped.",
                        executed=True,
                        verification_results=(
                            VerificationResult(
                                target_id="platform:init:lxc-container-runtime",
                                status=VerificationStatus.FAILED_TO_APPLY,
                                message="Container runtime phase reached a terminal state.",
                                evidence={
                                    "phase": "verify",
                                    "classification": "container_runtime_not_verified",
                                    "first_failure_node": "swarm-manager",
                                    "first_failure_reason": "apt_repository_unreachable",
                                },
                            ),
                        ),
                    ),
                ),
            ),
        )
        output = io.StringIO()

        with redirect_stdout(output):
            entrypoint._print_setup_installation_summary(result)

        rendered = output.getvalue()
        self.assertIn("- platform init: failed_to_apply", rendered)
        self.assertIn("Workflow: platform init", rendered)
        self.assertIn("platform:init:lxc-container-runtime: failed_to_apply", rendered)
        self.assertIn("- first_failure_node: swarm-manager", rendered)
        self.assertIn("- first_failure_reason: apt_repository_unreachable", rendered)

    async def test_static_preflight_runs_without_live_consent(self):
        preflight = SimpleNamespace(run=AsyncMock(return_value=_FakePreflightResult(True)))
        output = io.StringIO()

        with patch.object(entrypoint, "build_preflight_service", return_value=preflight) as build_preflight:
            with patch.object(entrypoint, "build_application_services") as build_services:
                with redirect_stdout(output):
                    await entrypoint.main(["--preflight"])

        build_preflight.assert_called_once_with(
            service_profile=ServiceStackProfile.SERVICE_ACCESS.value,
            node_provider_request=None,
            allow_wsl_windows_filesystem=False,
        )
        build_services.assert_not_called()
        preflight.run.assert_awaited_once_with(None)
        self.assertNotIn('{\n', output.getvalue())
        self.assertIn("Preflight summary: PASSED", output.getvalue())
        self.assertIn("Static checks passed", output.getvalue())
        self.assertIn("does not claim live provider readiness", output.getvalue())

    async def test_preflight_json_mode_emits_structured_payload(self):
        preflight = SimpleNamespace(run=AsyncMock(return_value=_FakePreflightResult(True)))
        output = io.StringIO()

        with patch.object(entrypoint, "build_preflight_service", return_value=preflight):
            with redirect_stdout(output):
                await entrypoint.main(["--preflight", "--json"])

        payload = _json_payload_from_output(output.getvalue())
        self.assertEqual("PASSED", payload["status"])

    async def test_preflight_json_preserves_host_filesystem_order_without_path_leak(self):
        project_path = "/mnt/e/private/project"
        assessment = assess_project_filesystem(
            HostEnvironmentKind.WSL2,
            ProjectFilesystemInspection(
                kind=ProjectFilesystemKind.WINDOWS_MOUNTED,
                resolved_project_path=project_path,
                filesystem_type="9p",
                classification_source="test_fixture",
            ),
            allow_wsl_windows_filesystem=False,
        )
        filesystem_check = PreflightService(
            SimpleNamespace()
        )._project_filesystem_check(assessment)
        result = PreflightResult(
            (
                PreflightCheck(
                    check_id="HOST",
                    category=PreflightCategory.HOST,
                    status=PreflightStatus.PASSED,
                    severity=PreflightSeverity.MANDATORY,
                    message="Host environment supports this setup path.",
                    remediation="None",
                    evidence={"environment": "wsl2"},
                ),
                filesystem_check,
            )
        )
        preflight = SimpleNamespace(run=AsyncMock(return_value=result))
        outputs: list[str] = []

        with patch.object(entrypoint, "build_preflight_service", return_value=preflight):
            for _ in range(2):
                output = io.StringIO()
                with redirect_stdout(output), self.assertRaises(SystemExit):
                    await entrypoint.main(["--preflight", "--json"])
                outputs.append(output.getvalue())

        self.assertEqual(outputs[0], outputs[1])
        payload = _json_payload_from_output(outputs[0])
        self.assertEqual(
            ["HOST", "HOST-FILESYSTEM"],
            [item["check_id"] for item in payload["checks"]],
        )
        self.assertNotIn(project_path, outputs[0])

    async def test_failed_preflight_exits_nonzero(self):
        preflight = SimpleNamespace(run=AsyncMock(return_value=_FakePreflightResult(False)))

        with patch.object(entrypoint, "build_preflight_service", return_value=preflight):
            with redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    await entrypoint.main(["--preflight"])

        self.assertEqual(1, raised.exception.code)

    async def test_doctor_network_dispatches_without_building_workflow_services(self):
        doctor = SimpleNamespace(run=AsyncMock(return_value=_FakeNetworkDoctorReport(True)))
        output = io.StringIO()

        with patch.object(entrypoint, "build_network_doctor_service", return_value=doctor):
            with patch.object(entrypoint, "build_application_services") as build_services:
                with redirect_stdout(output):
                    await entrypoint.main(["doctor", "network"])

        build_services.assert_not_called()
        doctor.run.assert_awaited_once_with()
        self.assertIn("[Runtime]", output.getvalue())

    async def test_failed_doctor_network_exits_nonzero(self):
        doctor = SimpleNamespace(run=AsyncMock(return_value=_FakeNetworkDoctorReport(False)))

        with patch.object(entrypoint, "build_network_doctor_service", return_value=doctor):
            with redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    await entrypoint.main(["doctor", "network"])

        self.assertEqual(1, raised.exception.code)

    async def test_network_repair_dispatches_dry_run_options_without_live_consent(self):
        repair = SimpleNamespace(run=AsyncMock(return_value=_FakeNetworkRepairReport(True)))
        output = io.StringIO()

        with patch.object(entrypoint, "build_network_repair_service", return_value=repair):
            with patch.object(entrypoint, "build_application_services") as build_services:
                with redirect_stdout(output):
                    await entrypoint.main(["network", "repair", "--runtime", "wsl2-nat"])

        build_services.assert_not_called()
        options = repair.run.call_args.args[0]
        self.assertEqual("wsl2-nat", options.runtime)
        self.assertFalse(options.apply)
        self.assertIn("[Network Repair]", output.getvalue())

    async def test_network_repair_apply_dispatches_selected_targets(self):
        repair = SimpleNamespace(run=AsyncMock(return_value=_FakeNetworkRepairReport(True)))

        with patch.object(entrypoint, "build_network_repair_service", return_value=repair):
            with redirect_stdout(io.StringIO()):
                await entrypoint.main(
                    ["network", "repair", "--linux-forwarding", "--incus", "--apply"]
                )

        options = repair.run.call_args.args[0]
        self.assertTrue(options.linux_forwarding)
        self.assertTrue(options.incus)
        self.assertTrue(options.apply)

    def test_network_repair_requires_target(self):
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                entrypoint.parse_args(["network", "repair"])

    def test_network_repair_options_are_rejected_for_other_commands(self):
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                entrypoint.parse_args(["doctor", "network", "--apply"])

    def test_entrypoint_has_no_direct_low_level_infrastructure_imports(self):
        imports = _direct_imports(ENTRYPOINT_PATH)
        forbidden_prefixes = (
            "tiny_swarm_world.infrastructure.adapters.command_runner",
            "tiny_swarm_world.infrastructure.adapters.ui",
            "tiny_swarm_world.infrastructure.adapters.repositories",
            "tiny_swarm_world.infrastructure.adapters.yaml",
            "tiny_swarm_world.infrastructure.adapters.file_management",
            "tiny_swarm_world.infrastructure.logging",
            "tiny_swarm_world.application.ports.method_trace",
            "tiny_swarm_world.application.ports.progress",
            "tiny_swarm_world.application.services.network",
            "tiny_swarm_world.application.services.vm",
        )

        violations = [
            imported
            for imported in imports
            for prefix in forbidden_prefixes
            if imported == prefix or imported.startswith(f"{prefix}.")
        ]

        self.assertEqual([], violations)

    def test_entrypoint_has_no_direct_console_or_logging_lifecycle_identifiers(self):
        forbidden_identifiers = {
            "AGGREGATE_INSTANCE",
            "FactoryUI",
            "LoggerFactory",
            "STATUS_ERROR",
            "build_setup_ui",
            "start_in_thread",
            "ui_thread",
            "update_status",
        }

        violations = sorted(_referenced_identifiers(ENTRYPOINT_PATH) & forbidden_identifiers)

        self.assertEqual([], violations)


def _direct_imports(source_file: Path) -> list[str]:
    tree = ast.parse(source_file.read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def _referenced_identifiers(source_file: Path) -> set[str]:
    tree = ast.parse(source_file.read_text(encoding="utf-8"))
    identifiers: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            identifiers.add(node.id)
        if isinstance(node, ast.Attribute):
            identifiers.add(node.attr)
    return identifiers


class _FakePreflightResult:
    def __init__(
        self,
        passed: bool,
        failed_checks: tuple[object, ...] = (),
    ):
        self.passed = passed
        self.status = "PASSED" if passed else "FAILED"
        self.resource_gated = False
        self.failed_checks = failed_checks

    def to_dict(self) -> dict[str, object]:
        return {"status": self.status, "checks": []}


class _FakeNetworkDoctorReport:
    def __init__(self, passed: bool):
        self.passed = passed

    def render(self) -> str:
        return "[Runtime]\nRuntime: wsl2"

    def to_dict(self) -> dict[str, object]:
        return {"passed": self.passed, "sections": []}


class _FakeNetworkRepairReport:
    def __init__(self, succeeded: bool):
        self.succeeded = succeeded

    def render(self) -> str:
        return "[Network Repair]\nMode: dry-run"

    def to_dict(self) -> dict[str, object]:
        return {"succeeded": self.succeeded, "steps": []}


def _application_services_with_platform_workflows(
    preflight_result: _FakePreflightResult | None = None,
    init_result: PlatformWorkflowResult | None = None,
    reconcile_result: PlatformWorkflowResult | None = None,
):
    workflows = SimpleNamespace(
        init=SimpleNamespace(
            run=AsyncMock(return_value=init_result or _workflow_result(PlatformWorkflowKind.INIT))
        ),
        reconcile=SimpleNamespace(
            run=AsyncMock(
                return_value=reconcile_result
                or _workflow_result(PlatformWorkflowKind.RECONCILE)
            )
        ),
        expose=SimpleNamespace(
            run=AsyncMock(return_value=_workflow_result(PlatformWorkflowKind.EXPOSE))
        ),
        repair_lxc_proxy_drift=SimpleNamespace(
            run=AsyncMock(
                return_value=_workflow_result(PlatformWorkflowKind.REPAIR_LXC_PROXY_DRIFT)
            )
        ),
        verify=SimpleNamespace(run=AsyncMock(return_value=_workflow_result(PlatformWorkflowKind.VERIFY))),
        reset=SimpleNamespace(run=AsyncMock(return_value=_workflow_result(PlatformWorkflowKind.RESET))),
        destroy=SimpleNamespace(run=AsyncMock(return_value=_workflow_result(PlatformWorkflowKind.DESTROY))),
    )
    preflight = SimpleNamespace(
        run=AsyncMock(return_value=preflight_result or _FakePreflightResult(True))
    )
    return SimpleNamespace(
        platform=SimpleNamespace(
            workflows=workflows,
            preflight=preflight,
        )
    ), workflows


def _blocked_platform_init_result() -> PlatformWorkflowResult:
    return PlatformWorkflowResult(
        kind=PlatformWorkflowKind.INIT,
        status=PlatformWorkflowStatus.BLOCKED,
        message="init workflow blocked by live preflight before mutation.",
        executed=False,
        verification_results=(
            VerificationResult(
                target_id="platform:init:preflight",
                status=VerificationStatus.BLOCKED,
                message="Live preflight blocked platform init before mutation.",
                evidence={
                    "phase": "pre_apply",
                    "failed_check_count": "1",
                    "runtime_failure_count": "1",
                },
            ),
        ),
    )


def _workflow_result(kind: PlatformWorkflowKind) -> PlatformWorkflowResult:
    return PlatformWorkflowResult(
        kind=kind,
        status=PlatformWorkflowStatus.COMPLETED,
        message=f"{kind.value} workflow completed.",
        executed=True,
    )


def _boundary_service_bundles():
    artifact_runs = {
        "prepare": AsyncMock(
            return_value=ArtifactWorkflowResult(
                kind=ArtifactWorkflowKind.PREPARE,
                status=ArtifactWorkflowStatus.BLOCKED,
                message="artifacts prepare is blocked.",
                reason="live registry and Nexus contracts are not wired",
            )
        ),
        "verify": AsyncMock(
            return_value=ArtifactWorkflowResult(
                kind=ArtifactWorkflowKind.VERIFY,
                status=ArtifactWorkflowStatus.BLOCKED,
                message="artifacts verify is blocked.",
                reason="observed-state verification is not implemented",
            )
        ),
    }
    deployment_runs = {
        "bootstrap": AsyncMock(
            return_value=DeploymentWorkflowResult(
                kind=DeploymentWorkflowKind.BOOTSTRAP,
                status=DeploymentWorkflowStatus.BLOCKED,
                message="deployment bootstrap is blocked.",
                reason="Portainer and Nexus bootstrap require contracts",
            )
        ),
        "apply": AsyncMock(
            return_value=DeploymentWorkflowResult(
                kind=DeploymentWorkflowKind.APPLY,
                status=DeploymentWorkflowStatus.BLOCKED,
                message="deployment apply is blocked.",
                reason="Portainer stack changes require contracts",
            )
        ),
        "verify": AsyncMock(
            return_value=DeploymentWorkflowResult(
                kind=DeploymentWorkflowKind.VERIFY,
                status=DeploymentWorkflowStatus.BLOCKED,
                message="deployment verify is blocked.",
                reason="observed-state verification is not implemented",
            )
        ),
    }
    artifact_services = SimpleNamespace(
        workflows=SimpleNamespace(
            prepare=SimpleNamespace(run=artifact_runs["prepare"]),
            verify=SimpleNamespace(run=artifact_runs["verify"]),
        )
    )
    deployment_services = SimpleNamespace(
        workflows=SimpleNamespace(
            bootstrap=SimpleNamespace(run=deployment_runs["bootstrap"]),
            apply=SimpleNamespace(run=deployment_runs["apply"]),
            verify=SimpleNamespace(run=deployment_runs["verify"]),
        )
    )
    return artifact_services, deployment_services, {
        ("artifacts", "prepare"): artifact_runs["prepare"],
        ("artifacts", "verify"): artifact_runs["verify"],
        ("deployment", "bootstrap"): deployment_runs["bootstrap"],
        ("deployment", "apply"): deployment_runs["apply"],
        ("deployment", "verify"): deployment_runs["verify"],
    }


def _json_payload_from_output(text: str) -> dict[str, object]:
    return json.loads(text[text.index("{") :])


class _HostDetectionService:
    def __init__(self, report: HostEnvironmentReport) -> None:
        self.report = report
        self.calls = 0

    def run(self) -> HostEnvironmentReport:
        self.calls += 1
        return self.report


def _host_report(
    environment: HostEnvironmentKind,
    setup_path: SetupPath,
) -> HostEnvironmentReport:
    remediation = (
        ("Upgrade to WSL2 or use native Linux.",)
        if environment is HostEnvironmentKind.WSL1_UNSUPPORTED
        else ("Verify the host classification.",)
    )
    return HostEnvironmentReport(
        environment=environment,
        setup_path=setup_path,
        distribution="Ubuntu-24.04",
        kernel_release="6.1.21.2-microsoft-standard-WSL2",
        windows_interop_available=False,
        platform_family="linux",
        remediation=remediation,
        evidence={"classification": environment.value},
    )
