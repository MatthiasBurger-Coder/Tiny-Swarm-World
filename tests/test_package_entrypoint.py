import ast
import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from tiny_swarm_world import __main__ as entrypoint
from tiny_swarm_world.application.services.platform.workflow_taxonomy import (
    DESTROY_TINY_SWARM_PLATFORM_CONFIRMATION,
    RESET_TINY_SWARM_PLATFORM_CONFIRMATION,
    PlatformWorkflowKind,
    PlatformWorkflowResult,
    PlatformWorkflowStatus,
)
from tiny_swarm_world.domain.preflight import (
    LIVE_CONSENT_ENVIRONMENT_VALUE,
    LIVE_CONSENT_PHRASE,
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

    async def test_list_workflows_does_not_build_or_run_services(self):
        output = io.StringIO()

        with patch.object(entrypoint, "build_application_services") as build_services:
            with redirect_stdout(output):
                await entrypoint.main(["--list-workflows"])

        build_services.assert_not_called()
        self.assertIn("platform init", output.getvalue())
        self.assertIn("platform reconcile", output.getvalue())
        self.assertIn("platform reset", output.getvalue())
        self.assertIn("deployment apply", output.getvalue())
        self.assertNotIn("vm-ip-list", output.getvalue())
        self.assertNotIn("multipass-init-vms", output.getvalue())

    def test_legacy_run_option_is_rejected(self):
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                entrypoint.parse_args(["--run", "vm-ip-list"])

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

    async def test_mutating_workflow_refuses_missing_consent_environment(self):
        output = io.StringIO()

        with patch("builtins.input", return_value=LIVE_CONSENT_PHRASE):
            with patch.object(entrypoint, "build_application_services") as build_services:
                with redirect_stdout(output):
                    with self.assertRaises(SystemExit) as raised:
                        await entrypoint.main(["platform", "init", "--live"])

        self.assertEqual(2, raised.exception.code)
        build_services.assert_not_called()
        self.assertIn("missing TSW_LIVE_INFRASTRUCTURE_CONSENT", output.getvalue())

    async def test_mutating_workflow_refuses_wrong_typed_phrase(self):
        output = io.StringIO()

        with patch.dict(
            "os.environ",
            {entrypoint.LIVE_CONSENT_ENVIRONMENT_VARIABLE: LIVE_CONSENT_ENVIRONMENT_VALUE},
        ):
            with patch("builtins.input", return_value="wrong phrase"):
                with patch.object(entrypoint, "build_application_services") as build_services:
                    with redirect_stdout(output):
                        with self.assertRaises(SystemExit) as raised:
                            await entrypoint.main(["platform", "init", "--live"])

        self.assertEqual(2, raised.exception.code)
        build_services.assert_not_called()
        self.assertIn("missing typed live confirmation phrase", output.getvalue())

    async def test_mutating_workflow_refuses_noninteractive_eof(self):
        output = io.StringIO()

        with patch.dict(
            "os.environ",
            {entrypoint.LIVE_CONSENT_ENVIRONMENT_VARIABLE: LIVE_CONSENT_ENVIRONMENT_VALUE},
        ):
            with patch("builtins.input", side_effect=EOFError):
                with patch.object(entrypoint, "build_application_services") as build_services:
                    with redirect_stdout(output):
                        with self.assertRaises(SystemExit) as raised:
                            await entrypoint.main(["platform", "init", "--live"])

        self.assertEqual(2, raised.exception.code)
        build_services.assert_not_called()
        self.assertIn("missing typed live confirmation phrase", output.getvalue())

    async def test_platform_init_dispatches_to_composed_workflow_with_live_consent(self):
        services, workflows = _application_services_with_platform_workflows()
        output = io.StringIO()

        with patch.dict(
            "os.environ",
            {entrypoint.LIVE_CONSENT_ENVIRONMENT_VARIABLE: LIVE_CONSENT_ENVIRONMENT_VALUE},
        ):
            with patch("builtins.input", return_value=LIVE_CONSENT_PHRASE):
                with patch.object(entrypoint, "build_application_services", return_value=services):
                    with redirect_stdout(output):
                        await entrypoint.main(["platform", "init", "--live"])

        workflows.init.run.assert_awaited_once_with()
        workflows.reconcile.run.assert_not_awaited()
        self.assertIn('"workflow": "platform init"', output.getvalue())

    async def test_platform_verify_dispatches_without_live_consent(self):
        services, workflows = _application_services_with_platform_workflows()
        output = io.StringIO()

        with patch.object(entrypoint, "build_application_services", return_value=services) as build_services:
            with redirect_stdout(output):
                await entrypoint.main(["platform", "verify"])

        build_services.assert_called_once_with()
        workflows.verify.run.assert_awaited_once_with()
        workflows.init.run.assert_not_awaited()
        self.assertIn('"workflow": "platform verify"', output.getvalue())

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

        with patch.dict(
            "os.environ",
            {entrypoint.LIVE_CONSENT_ENVIRONMENT_VARIABLE: LIVE_CONSENT_ENVIRONMENT_VALUE},
        ):
            with patch("builtins.input", return_value=LIVE_CONSENT_PHRASE):
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

        with patch.dict(
            "os.environ",
            {entrypoint.LIVE_CONSENT_ENVIRONMENT_VARIABLE: LIVE_CONSENT_ENVIRONMENT_VALUE},
        ):
            with patch("builtins.input", return_value=LIVE_CONSENT_PHRASE):
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

    async def test_declared_unwired_workflow_is_blocked_without_building_services(self):
        output = io.StringIO()

        with patch.object(entrypoint, "build_application_services") as build_services:
            with redirect_stdout(output):
                with self.assertRaises(SystemExit) as raised:
                    await entrypoint.main(["deployment", "apply"])

        self.assertEqual(1, raised.exception.code)
        build_services.assert_not_called()
        self.assertIn('"status": "blocked"', output.getvalue())

    async def test_static_preflight_runs_without_live_consent(self):
        preflight = SimpleNamespace(run=AsyncMock(return_value=_FakePreflightResult(True)))
        output = io.StringIO()

        with patch.object(entrypoint, "build_preflight_service", return_value=preflight) as build_preflight:
            with patch.object(entrypoint, "build_application_services") as build_services:
                with redirect_stdout(output):
                    await entrypoint.main(["--preflight"])

        build_preflight.assert_called_once_with()
        build_services.assert_not_called()
        preflight.run.assert_awaited_once_with(None)
        self.assertIn('"status": "PASSED"', output.getvalue())

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
            "tiny_swarm_world.infrastructure.adapters.repositories",
            "tiny_swarm_world.infrastructure.adapters.yaml",
            "tiny_swarm_world.infrastructure.adapters.file_management",
            "tiny_swarm_world.application.services.multipass",
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


def _direct_imports(source_file: Path) -> list[str]:
    tree = ast.parse(source_file.read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


class _FakePreflightResult:
    def __init__(self, passed: bool):
        self.passed = passed

    def to_dict(self) -> dict[str, object]:
        return {"status": "PASSED" if self.passed else "FAILED", "checks": []}


def _application_services_with_platform_workflows():
    workflows = SimpleNamespace(
        init=SimpleNamespace(run=AsyncMock(return_value=_workflow_result(PlatformWorkflowKind.INIT))),
        reconcile=SimpleNamespace(
            run=AsyncMock(return_value=_workflow_result(PlatformWorkflowKind.RECONCILE))
        ),
        verify=SimpleNamespace(run=AsyncMock(return_value=_workflow_result(PlatformWorkflowKind.VERIFY))),
        reset=SimpleNamespace(run=AsyncMock(return_value=_workflow_result(PlatformWorkflowKind.RESET))),
        destroy=SimpleNamespace(run=AsyncMock(return_value=_workflow_result(PlatformWorkflowKind.DESTROY))),
    )
    low_level_services = {
        "multipass_init_vms": SimpleNamespace(run=AsyncMock(side_effect=AssertionError)),
        "network_setup_netplan": SimpleNamespace(run=AsyncMock(side_effect=AssertionError)),
        "vm_ip_list": SimpleNamespace(run=AsyncMock(side_effect=AssertionError)),
    }
    return SimpleNamespace(platform=SimpleNamespace(workflows=workflows, **low_level_services)), workflows


def _workflow_result(kind: PlatformWorkflowKind) -> PlatformWorkflowResult:
    return PlatformWorkflowResult(
        kind=kind,
        status=PlatformWorkflowStatus.COMPLETED,
        message=f"{kind.value} workflow completed.",
        executed=True,
    )
