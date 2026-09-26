import subprocess
import unittest

import requests

from tiny_swarm_world.application.ports.operation_result import OperationError
from tiny_swarm_world.infrastructure.adapters.exceptions.operation_failure_mapping import (
    process_failure, request_failure, process_result_failure,
)
from tiny_swarm_world.infrastructure.process import ProcessLaunchError, ProcessTimeoutError


class TestFailureMapping(unittest.TestCase):
    def test_process_classification_does_not_expose_technical_payloads(self):
        for error, cause in (
            (FileNotFoundError("private"), "launch_executable_missing"),
            (PermissionError("private"), "launch_permission_denied"),
            (OSError("private"), "launch_os_error"),
            (ProcessLaunchError(), "launch_os_error"),
            (ProcessTimeoutError(), "process_timeout"),
            (subprocess.TimeoutExpired("private", 1), "process_timeout"),
            (subprocess.CalledProcessError(1, "private"), "process_exit_failed"),
        ):
            with self.subTest(cause=cause):
                failure = process_failure(error, "execute", "runtime")
                self.assertEqual(cause, failure.cause)
                self.assertNotIn("private", str(failure.to_dict()))

    def test_request_classification_and_unknown_programming_errors(self):
        for error, cause in (
            (requests.Timeout("private"), "request_timeout"),
            (requests.ConnectionError("private"), "dependency_unavailable"),
            (requests.HTTPError("private"), "request_failed"),
        ):
            self.assertEqual(cause, request_failure(error, "bootstrap", "http").cause)
        with self.assertRaises(TypeError):
            process_failure(RuntimeError("bug"), "execute", "runtime")
        with self.assertRaises(TypeError):
            request_failure(RuntimeError("bug"), "bootstrap", "http")

    def test_process_result_and_nested_origin(self):
        failure = process_result_failure("execute", "runtime", failure_hint="launch_executable_missing")
        self.assertEqual("launch_executable_missing", failure.cause)
        self.assertEqual("process_timeout", process_result_failure("execute", "runtime", timed_out=True).cause)
        self.assertIs(failure, process_failure(OperationError(failure), "outer", "wrapper"))


class TestRealBoundaryFailureMapping(unittest.IsolatedAsyncioTestCase):
    async def test_observer_retains_origin_and_distinguishes_programmer_errors(self):
        import traceback
        from unittest.mock import Mock
        from tiny_swarm_world.application.ports.clients.port_swarm_stack_runtime import SwarmRuntimeError
        from tiny_swarm_world.infrastructure.adapters.update.lxc_runtime_observer import LxcUpdateRuntimeObserver
        marker = "sensitive-observer-payload"
        origin = process_result_failure("swarm.execute", "lxc_gateway", timed_out=True)
        for error, cause in (
            (SwarmRuntimeError(origin), "process_timeout"),
            (TypeError(marker), "unexpected_failure"),
            (KeyError(marker), "unexpected_failure"),
            (RuntimeError(marker), "unexpected_failure"),
        ):
            gateway = Mock()
            gateway.run_manager_shell.side_effect = error
            try:
                await LxcUpdateRuntimeObserver(gateway).observe("stack", "service")
            except OperationError as caught:
                self.assertIsInstance(caught, RuntimeError)
                self.assertEqual(cause, caught.failure.cause)
                self.assertNotIn(marker, "".join(traceback.format_exception(caught)))
                if cause == "process_timeout":
                    self.assertIs(origin, caught.failure)
            else:
                self.fail("Expected an observer failure")

    async def test_observer_invalid_payload_is_expected_and_redacted(self):
        import traceback
        from unittest.mock import Mock
        from tiny_swarm_world.infrastructure.adapters.update.lxc_runtime_observer import LxcUpdateRuntimeObserver
        marker = "sensitive-parser-payload"
        gateway = Mock()
        gateway.run_manager_shell.return_value = subprocess.CompletedProcess([], 0, marker, "")
        try:
            await LxcUpdateRuntimeObserver(gateway).observe("stack", "service")
        except OperationError as caught:
            self.assertEqual("observation_unavailable", caught.failure.cause)
            self.assertNotIn(marker, "".join(traceback.format_exception(caught)))
        else:
            self.fail("Expected invalid observation data")

    def test_state_store_storage_and_parser_errors_are_safe_compatible_bridges(self):
        import traceback
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from tiny_swarm_world.domain.update import ClassicUpdatePlan
        from tiny_swarm_world.infrastructure.adapters.update.json_state_store import JsonUpdateStateStore
        marker = "sensitive-state-payload"
        with TemporaryDirectory() as directory:
            root = Path(directory)
            store = JsonUpdateStateStore(root)
            (root / "stack__service.json").write_text(marker, encoding="utf-8")
            try:
                store.load("stack", "service")
            except OperationError as error:
                self.assertIsInstance(error, ValueError)
                self.assertEqual("state_invalid", error.failure.cause)
                self.assertNotIn(marker, "".join(traceback.format_exception(error)))
            else:
                self.fail("Expected invalid state")
            plan = ClassicUpdatePlan("stack", "service", "old:1", "new:1")
            for method in ("mkdir", "chmod", "unlink"):
                with self.subTest(method=method), patch.object(Path, method, side_effect=OSError(marker)):
                    try:
                        store.save(plan)
                    except OperationError as error:
                        self.assertIsInstance(error, OSError)
                        self.assertEqual("filesystem_error", error.failure.cause)
                        self.assertNotIn(marker, "".join(traceback.format_exception(error)))
                    else:
                        self.fail("Expected storage failure")

    def test_gateway_and_http_hide_raw_cause_chains(self):
        import traceback
        from unittest.mock import Mock
        from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
        from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.manager_shell_gateway import LxcManagerShellGateway
        from tiny_swarm_world.infrastructure.adapters.clients.nexus_http_client import NexusHttpClient
        marker = "sensitive-technical-payload"
        process_error = ProcessTimeoutError()
        process_error.__cause__ = OSError(marker)
        runner = Mock()
        runner.run_text.side_effect = process_error
        gateway = LxcManagerShellGateway(backend=ManagedLxcBackend.INCUS, manager_node="manager", timeout_seconds=1, logger=Mock(), process_runner=runner)
        session = Mock()
        session.get.side_effect = requests.ConnectionError(marker)
        client = NexusHttpClient("http://localhost", session=session)
        for action, cause in (
            (lambda: gateway.run_manager_shell(marker), "process_timeout"),
            (lambda: client.get_user("user", "password", "target"), "dependency_unavailable"),
        ):
            try:
                action()
            except OperationError as error:
                self.assertEqual(cause, error.failure.cause)
                public = str(error) + repr(error) + str(error.failure.to_dict()) + "".join(traceback.format_exception(error))
                self.assertNotIn(marker, public)
                self.assertTrue(error.__suppress_context__)
            else:
                self.fail("Expected classified technical failure")

    async def test_socat_absence_launch_and_timeout_are_distinct(self):
        from unittest.mock import AsyncMock, patch
        from tiny_swarm_world.infrastructure.adapters.network.wsl_socat_exposure import WslSocatExposureAdapter
        from tiny_swarm_world.infrastructure.process.async_runner import AsyncProcessResult
        target = "tiny_swarm_world.infrastructure.adapters.network.wsl_socat_exposure.run_async_process"
        with patch(target, new=AsyncMock(return_value=AsyncProcessResult(1))):
            self.assertFalse(await WslSocatExposureAdapter().process_exists("unused"))
        for process_result, cause in (
            (AsyncProcessResult(127, failure_hint="launch_executable_missing"), "launch_executable_missing"),
            (AsyncProcessResult(124, timed_out=True), "process_timeout"),
        ):
            with patch(target, new=AsyncMock(return_value=process_result)):
                with self.assertRaises(OperationError) as caught:
                    await WslSocatExposureAdapter().start("unused")
                self.assertEqual(cause, caught.exception.failure.cause)

    def test_state_cleanup_preserves_control_flow(self):
        import asyncio
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from tiny_swarm_world.domain.update import ClassicUpdatePlan
        from tiny_swarm_world.infrastructure.adapters.update.json_state_store import JsonUpdateStateStore
        for primary in (asyncio.CancelledError(), KeyboardInterrupt(), SystemExit()):
            with self.subTest(primary=type(primary)), TemporaryDirectory() as directory:
                store = JsonUpdateStateStore(Path(directory))
                with patch("tiny_swarm_world.infrastructure.adapters.update.json_state_store.os.replace", side_effect=primary), patch.object(Path, "unlink", side_effect=OSError("cleanup-private")):
                    with self.assertRaises(type(primary)) as caught:
                        store.save(ClassicUpdatePlan("stack", "service", "old:1", "new:1"))
                self.assertIs(primary, caught.exception)

    def test_http_decoded_schema_errors_and_legacy_cli_timeout_are_classified(self):
        import traceback
        from unittest.mock import Mock, patch
        from tiny_swarm_world.infrastructure.adapters.clients.portainer_http_client import PortainerHttpClient
        from tiny_swarm_world.infrastructure.adapters.clients.nexus_http_client import NexusHttpClient
        from tiny_swarm_world.infrastructure.adapters.clients.infisical_cli_client import InfisicalCliClient
        marker = "sensitive-schema-payload"
        session = Mock()
        response = Mock(status_code=200)
        session.get.return_value = response
        session.post.return_value = response
        session.request.return_value = response
        nexus = NexusHttpClient("http://localhost", session=session)
        portainer = PortainerHttpClient("http://localhost", "user", "value", session=session)
        for payload, action in (
            (None, lambda: portainer._get_jwt_token()),
            ([marker], lambda: portainer._get_jwt_token()),
            ([marker], lambda: nexus.get_user("user", "value", "target")),
            ([{"userId": "target", "roles": marker}], lambda: nexus.get_user("user", "value", "target")),
            ([{"Name": "target", "Id": marker}], lambda: portainer.find_stack_id_by_name("target")),
            ([{"Name": "target", "Id": "9" * 5000}], lambda: portainer.find_stack_id_by_name("target")),
        ):
            response.json.return_value = payload
            if isinstance(payload, list) and payload and isinstance(payload[0], dict) and "Name" in payload[0]:
                portainer._jwt_token = "test-session"
            try:
                action()
            except OperationError as error:
                self.assertEqual("request_failed", error.failure.cause)
                self.assertNotIn(marker, "".join(traceback.format_exception(error)))
            else:
                self.fail("Expected safe schema failure")
        with patch("tiny_swarm_world.infrastructure.adapters.clients.infisical_cli_client.run_process", side_effect=subprocess.TimeoutExpired(marker, 1)):
            try:
                InfisicalCliClient(session=session).run_bootstrap(("unused",))
            except OperationError as error:
                self.assertEqual("process_timeout", error.failure.cause)
                self.assertNotIn(marker, "".join(traceback.format_exception(error)))
            else:
                self.fail("Expected classified legacy timeout")

    def test_playwright_library_errors_are_expected_and_generic_defects_are_distinct(self):
        import sys
        from types import ModuleType
        from unittest.mock import Mock, patch
        from tiny_swarm_world.infrastructure.adapters.clients.infisical_playwright_client import _fill_first, _click_first
        class BrowserFailure(Exception):
            pass
        module = ModuleType("playwright.sync_api")
        module.Error = BrowserFailure
        for failure, cause in ((BrowserFailure("private"), "request_failed"), (TypeError("private"), "unexpected_failure")):
            page = Mock()
            page.get_by_label.return_value.fill.side_effect = failure
            page.get_by_placeholder.return_value.fill.side_effect = failure
            page.get_by_role.return_value.first.click.side_effect = failure
            with patch.dict(sys.modules, {"playwright.sync_api": module}):
                for action in (lambda: _fill_first(page, ("Name",), "value"), lambda: _click_first(page, ("Save",))):
                    with self.assertRaises(OperationError) as caught:
                        action()
                    self.assertEqual(cause, caught.exception.failure.cause)

    def test_malformed_memory_observation_is_safe(self):
        import traceback
        from pathlib import Path
        from unittest.mock import patch
        from tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe import HostPreflightProbe
        marker = "sensitive-memory-payload"
        with patch.object(Path, "exists", return_value=True), patch.object(Path, "read_text", return_value="MemTotal: " + marker):
            try:
                HostPreflightProbe().memory_bytes()
            except OperationError as error:
                self.assertEqual("observation_unavailable", error.failure.cause)
                self.assertNotIn(marker, "".join(traceback.format_exception(error)))
            else:
                self.fail("Expected invalid observed memory")

    def test_evidence_invalid_decoded_status_and_bytes_are_preserved(self):
        import json
        import traceback
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus
        from tiny_swarm_world.infrastructure.adapters.repositories.verification_evidence_local_repository import VerificationEvidenceLocalRepository
        marker = "sensitive-status-payload"
        for content in (json.dumps({"results": [{"target_id": "test", "status": marker}]}).encode(), b"\xff"):
            with TemporaryDirectory() as directory:
                path = Path(directory) / "evidence.json"
                path.write_bytes(content)
                repository = object.__new__(VerificationEvidenceLocalRepository)
                repository.path = path
                try:
                    repository.append(VerificationResult("test", VerificationStatus.VERIFIED))
                except OperationError as error:
                    self.assertIsInstance(error, ValueError)
                    self.assertEqual("configuration_invalid", error.failure.cause)
                    self.assertNotIn(marker, "".join(traceback.format_exception(error)))
                else:
                    self.fail("Expected invalid evidence")
                self.assertEqual(content, path.read_bytes())

    def test_missing_compose_and_invalid_context_do_not_expose_paths(self):
        import traceback
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from tiny_swarm_world.infrastructure.adapters.repositories.compose_file_repository_yaml import ComposeFileRepositoryYaml
        marker = "sensitive-context-payload"
        with TemporaryDirectory() as directory:
            repository = object.__new__(ComposeFileRepositoryYaml)
            repository.base_directories = [Path(directory)]
            repository._validated_stacks = {}
            for action, catch_type in (
                (lambda: repository.get_compose_of("missing"), FileNotFoundError),
            ):
                try:
                    action()
                except OperationError as error:
                    self.assertIsInstance(error, catch_type)
                    self.assertNotIn(directory, "".join(traceback.format_exception(error)))
                    self.assertEqual("configuration_invalid", error.failure.cause)
                else:
                    self.fail("Expected missing selected configuration")
            from tiny_swarm_world.infrastructure.project_paths import default_project_paths
            repository.project_paths = default_project_paths()
            try:
                repository.get_build_context_path(marker)
            except OperationError as error:
                self.assertIsInstance(error, ValueError)
                self.assertNotIn(marker, "".join(traceback.format_exception(error)))
            else:
                self.fail("Expected invalid build context")
