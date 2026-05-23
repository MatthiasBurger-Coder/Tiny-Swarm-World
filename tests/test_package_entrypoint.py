import ast
import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from tiny_swarm_world import __main__ as entrypoint
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
        self.assertIn("No automation service selected", output.getvalue())

    async def test_list_services_does_not_build_or_run_services(self):
        output = io.StringIO()

        with patch.object(entrypoint, "build_application_services") as build_services:
            with redirect_stdout(output):
                await entrypoint.main(["--list-services"])

        build_services.assert_not_called()
        self.assertIn("vm-ip-list", output.getvalue())
        self.assertIn("multipass-init-vms", output.getvalue())

    async def test_explicit_service_selection_requires_live_consent_before_building_services(self):
        output = io.StringIO()

        with patch.object(entrypoint, "build_application_services") as build_services:
            with redirect_stdout(output):
                with self.assertRaises(SystemExit) as raised:
                    await entrypoint.main(["--run", "vm-ip-list"])

        self.assertEqual(2, raised.exception.code)
        build_services.assert_not_called()
        self.assertIn("REFUSED_LIVE_CONSENT_MISSING", output.getvalue())
        self.assertIn("missing --live", output.getvalue())

    async def test_explicit_service_selection_refuses_missing_consent_environment(self):
        output = io.StringIO()

        with patch("builtins.input", return_value=LIVE_CONSENT_PHRASE):
            with patch.object(entrypoint, "build_application_services") as build_services:
                with redirect_stdout(output):
                    with self.assertRaises(SystemExit) as raised:
                        await entrypoint.main(["--run", "vm-ip-list", "--live"])

        self.assertEqual(2, raised.exception.code)
        build_services.assert_not_called()
        self.assertIn("missing TSW_LIVE_INFRASTRUCTURE_CONSENT", output.getvalue())

    async def test_explicit_service_selection_refuses_wrong_typed_phrase(self):
        output = io.StringIO()

        with patch.dict(
            "os.environ",
            {entrypoint.LIVE_CONSENT_ENVIRONMENT_VARIABLE: LIVE_CONSENT_ENVIRONMENT_VALUE},
        ):
            with patch("builtins.input", return_value="wrong phrase"):
                with patch.object(entrypoint, "build_application_services") as build_services:
                    with redirect_stdout(output):
                        with self.assertRaises(SystemExit) as raised:
                            await entrypoint.main(["--run", "vm-ip-list", "--live"])

        self.assertEqual(2, raised.exception.code)
        build_services.assert_not_called()
        self.assertIn("missing typed live confirmation phrase", output.getvalue())

    async def test_explicit_service_selection_refuses_noninteractive_eof(self):
        output = io.StringIO()

        with patch.dict(
            "os.environ",
            {entrypoint.LIVE_CONSENT_ENVIRONMENT_VARIABLE: LIVE_CONSENT_ENVIRONMENT_VALUE},
        ):
            with patch("builtins.input", side_effect=EOFError):
                with patch.object(entrypoint, "build_application_services") as build_services:
                    with redirect_stdout(output):
                        with self.assertRaises(SystemExit) as raised:
                            await entrypoint.main(["--run", "vm-ip-list", "--live"])

        self.assertEqual(2, raised.exception.code)
        build_services.assert_not_called()
        self.assertIn("missing typed live confirmation phrase", output.getvalue())

    async def test_explicit_service_selection_runs_selected_service_with_live_consent(self):
        vm_ip_list = SimpleNamespace(run=AsyncMock())
        services = SimpleNamespace(vm_ip_list=vm_ip_list)
        output = io.StringIO()

        with patch.dict(
            "os.environ",
            {entrypoint.LIVE_CONSENT_ENVIRONMENT_VARIABLE: LIVE_CONSENT_ENVIRONMENT_VALUE},
        ):
            with patch("builtins.input", return_value=LIVE_CONSENT_PHRASE):
                with patch.object(entrypoint, "build_application_services", return_value=services):
                    with redirect_stdout(output):
                        await entrypoint.main(["--run", "vm-ip-list", "--live"])

        vm_ip_list.run.assert_awaited_once_with()
        self.assertIn("Done", output.getvalue())

    async def test_static_preflight_runs_without_live_consent(self):
        preflight = SimpleNamespace(run=AsyncMock(return_value=_FakePreflightResult(True)))
        services = SimpleNamespace(preflight=preflight)
        output = io.StringIO()

        with patch.object(entrypoint, "build_application_services", return_value=services):
            with redirect_stdout(output):
                await entrypoint.main(["--preflight"])

        preflight.run.assert_awaited_once_with(None)
        self.assertIn('"status": "PASSED"', output.getvalue())

    async def test_failed_preflight_exits_nonzero(self):
        preflight = SimpleNamespace(run=AsyncMock(return_value=_FakePreflightResult(False)))
        services = SimpleNamespace(preflight=preflight)

        with patch.object(entrypoint, "build_application_services", return_value=services):
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
