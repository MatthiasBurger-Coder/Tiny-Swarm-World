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
    SetupWorkflowKind,
    SetupWorkflowResult,
    SetupWorkflowStatus,
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

    async def test_entrypoint_normalizes_common_linux_executable_paths(self):
        output = io.StringIO()

        with patch.object(entrypoint, "ensure_common_executable_paths") as normalize_paths:
            with redirect_stdout(output):
                await entrypoint.main(["--list-workflows"])

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
        self.assertIn("platform reset", output.getvalue())
        self.assertIn("deployment bootstrap", output.getvalue())
        self.assertIn("deployment apply", output.getvalue())
        self.assertIn("setup run", output.getvalue())
        self.assertNotIn("vm-ip-list", output.getvalue())
        self.assertNotIn("multipass-init-vms", output.getvalue())

    def test_legacy_run_option_is_rejected(self):
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                entrypoint.parse_args(["--run", "vm-ip-list"])

    def test_service_profile_defaults_to_service_access(self):
        args = entrypoint.parse_args([])

        self.assertEqual(ServiceStackProfile.SERVICE_ACCESS.value, args.service_profile)
        self.assertEqual(NodeProviderKind.LXC_NATIVE.value, args.node_provider)
        self.assertIsNone(args.lxc_backend)

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
        self.assertIn("Managed backend: auto-detect Incus or LXD", plan)
        self.assertIn("Provider readiness: checked before platform mutation", plan)
        self.assertIn("Service profile: service-access", plan)
        self.assertIn("Service Access: stack service-access", plan)
        self.assertIn("published port(s) 80, 8086", plan)
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
        self.assertIn('"workflow": "platform init"', output.getvalue())

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
        self.assertIn('"workflow": "platform init"', output.getvalue())

    async def test_platform_init_uses_composed_guarded_workflow_result(self):
        services, workflows = _application_services_with_platform_workflows(
            init_result=_blocked_platform_init_result()
        )
        output = io.StringIO()

        with patch("builtins.input", return_value="y"):
            with patch.object(entrypoint, "build_application_services", return_value=services):
                with redirect_stdout(output):
                    with self.assertRaises(SystemExit) as raised:
                        await entrypoint.main(["platform", "init", "--live"])

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
            node_provider_request=entrypoint.NodeProviderSelectionRequest(),
        )
        workflows.verify.run.assert_awaited_once_with()
        workflows.init.run.assert_not_awaited()
        self.assertIn('"workflow": "platform verify"', output.getvalue())

    async def test_platform_expose_requires_live_consent_and_dispatches(self):
        services, workflows = _application_services_with_platform_workflows()
        output = io.StringIO()

        with patch("builtins.input", return_value="y"):
            with patch.object(entrypoint, "build_application_services", return_value=services):
                with redirect_stdout(output):
                    await entrypoint.main(["platform", "expose", "--live"])

        workflows.expose.run.assert_awaited_once_with()
        workflows.init.run.assert_not_awaited()
        self.assertIn('"workflow": "platform expose"', output.getvalue())

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
                                            await entrypoint.main(command)
                                    else:
                                        await entrypoint.main(command)

                self.assertEqual(1, raised.exception.code)
                build_application_services.assert_not_called()
                if namespace == "artifacts":
                    build_artifact_services.assert_called_once_with(
                        node_provider_request=entrypoint.NodeProviderSelectionRequest()
                    )
                    build_deployment_services.assert_not_called()
                else:
                    build_artifact_services.assert_not_called()
                    build_deployment_services.assert_called_once_with(
                        service_profile=ServiceStackProfile.SERVICE_ACCESS.value,
                        node_provider_request=entrypoint.NodeProviderSelectionRequest(),
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
                            await entrypoint.main(["setup", "run", "--live"])

        self.assertEqual(1, raised.exception.code)
        run_setup.assert_awaited_once()
        live_consent = run_setup.call_args.args[0]
        self.assertTrue(live_consent.accepted)
        self.assertEqual("run", run_setup.call_args.args[1])
        self.assertEqual(
            {
                "service_profile": ServiceStackProfile.SERVICE_ACCESS.value,
                "node_provider_request": entrypoint.NodeProviderSelectionRequest(),
            },
            run_setup.call_args.kwargs,
        )
        payload = _json_payload_from_output(output.getvalue())
        self.assertEqual("setup run", payload["workflow"])
        self.assertEqual("blocked", payload["status"])

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

    async def test_static_preflight_runs_without_live_consent(self):
        preflight = SimpleNamespace(run=AsyncMock(return_value=_FakePreflightResult(True)))
        output = io.StringIO()

        with patch.object(entrypoint, "build_preflight_service", return_value=preflight) as build_preflight:
            with patch.object(entrypoint, "build_application_services") as build_services:
                with redirect_stdout(output):
                    await entrypoint.main(["--preflight"])

        build_preflight.assert_called_once_with(
            service_profile=ServiceStackProfile.SERVICE_ACCESS.value,
            node_provider_request=entrypoint.NodeProviderSelectionRequest(),
        )
        build_services.assert_not_called()
        preflight.run.assert_awaited_once_with(None)
        self.assertIn('"status": "PASSED"', output.getvalue())
        self.assertIn("Static checks passed", output.getvalue())
        self.assertIn("does not claim live provider readiness", output.getvalue())

    async def test_failed_preflight_exits_nonzero(self):
        preflight = SimpleNamespace(run=AsyncMock(return_value=_FakePreflightResult(False)))

        with patch.object(entrypoint, "build_preflight_service", return_value=preflight):
            with redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    await entrypoint.main(["--preflight"])

        self.assertEqual(1, raised.exception.code)

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


def _application_services_with_platform_workflows(
    preflight_result: _FakePreflightResult | None = None,
    init_result: PlatformWorkflowResult | None = None,
):
    workflows = SimpleNamespace(
        init=SimpleNamespace(
            run=AsyncMock(return_value=init_result or _workflow_result(PlatformWorkflowKind.INIT))
        ),
        reconcile=SimpleNamespace(
            run=AsyncMock(return_value=_workflow_result(PlatformWorkflowKind.RECONCILE))
        ),
        expose=SimpleNamespace(
            run=AsyncMock(return_value=_workflow_result(PlatformWorkflowKind.EXPOSE))
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
