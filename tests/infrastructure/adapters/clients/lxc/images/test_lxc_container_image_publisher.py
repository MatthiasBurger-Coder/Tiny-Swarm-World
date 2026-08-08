import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from tiny_swarm_world.domain.artifacts import ContainerImageContract
from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
from tiny_swarm_world.infrastructure.adapters.clients.lxc.images.errors import (
    ImagePublisherOperationRejected,
    PublicImagePullRejected,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc.images.lxc_container_image_publisher import (
    LxcContainerImagePublisher,
)
class TestLxcContainerImagePublisher(unittest.TestCase):
    def setUp(self):
        self.publisher = LxcContainerImagePublisher(
            backend=ManagedLxcBackend.LXD,
            registry_username="admin",
            registry_password="secret",
            timeout_seconds=30,
        )

    def test_rate_limited_public_pull_uses_typed_redacted_error(self):
        self.publisher._run_manager_shell = Mock(
            return_value=subprocess.CompletedProcess(
                [],
                1,
                stdout="",
                stderr="toomanyrequests: pull rate limit",
            )
        )
        self.publisher._load_host_cached_image = Mock(return_value=False)
        contract = ContainerImageContract("redis", "7", "redis", source="pull")

        with self.assertRaises(PublicImagePullRejected) as raised:
            self.publisher.publish_image(contract)

        self.assertEqual(raised.exception.diagnostic, "registry_rate_limited")
        self.assertNotIn("toomanyrequests", str(raised.exception).lower())

    def test_constructor_and_context_path_validation(self):
        with self.assertRaisesRegex(ValueError, "timeout"):
            LxcContainerImagePublisher(
                backend=ManagedLxcBackend.LXD,
                registry_username="admin",
                registry_password="secret",
                timeout_seconds=0,
            )

        for context in ("jenkins", "service-access-dashboard", "service-access-nginx"):
            with self.subTest(context=context):
                path = self.publisher._context_path(
                    ContainerImageContract("example/image", "1", context)
                )
                self.assertIsInstance(path, Path)
        with self.assertRaisesRegex(ValueError, "Unknown image build context"):
            self.publisher._context_path(ContainerImageContract("example/image", "1", "unknown"))

    def test_publish_build_image_transfers_context_logs_in_and_pushes(self):
        contract = ContainerImageContract("example/image", "1", "jenkins")
        self.publisher._manager_build_image_available = Mock(return_value=False)
        self.publisher._context_path = Mock(return_value=Path("/tmp/image"))
        self.publisher._transfer_context = Mock()
        self.publisher._docker_login = Mock()
        self.publisher._run_manager_shell = Mock(
            return_value=subprocess.CompletedProcess([], 0, stdout="", stderr="")
        )

        self.publisher.publish_image(contract)

        self.publisher._transfer_context.assert_called_once_with(Path("/tmp/image"), "$PWD/.tiny-swarm-world/images/jenkins")
        self.publisher._docker_login.assert_called_once_with()
        self.assertEqual(self.publisher._run_manager_shell.call_count, 2)

    def test_publish_pull_returns_on_manager_cache_hit(self):
        contract = ContainerImageContract("redis", "7", "redis", source="pull")
        self.publisher._manager_public_image_available = Mock(return_value=True)
        self.publisher._pull_public_image = Mock()

        self.publisher.publish_image(contract)

        self.publisher._pull_public_image.assert_not_called()

    def test_image_availability_and_pull_cover_cache_and_failure_paths(self):
        build_contract = ContainerImageContract("example/image", "1", "jenkins")
        pull_contract = ContainerImageContract("redis", "7", "redis", source="pull")
        self.publisher._docker_login = Mock()
        self.publisher._manager_public_image_available = Mock(return_value=True)
        self.assertTrue(self.publisher.image_available(pull_contract))
        self.publisher._docker_login.assert_not_called()

        self.publisher._manager_public_image_available.return_value = False
        self.publisher._load_host_cached_image = Mock(return_value=True)
        self.assertTrue(self.publisher.image_available(pull_contract))

        self.publisher._load_host_cached_image.return_value = False
        self.publisher._run_manager_shell = Mock(
            return_value=subprocess.CompletedProcess([], 1, stdout="", stderr="pull failed")
        )
        self.assertFalse(self.publisher.image_available(pull_contract))

        self.publisher._run_manager_shell = Mock(
            return_value=subprocess.CompletedProcess([], 1, stdout="", stderr="pull failed")
        )
        with self.assertRaisesRegex(RuntimeError, "Public container image pull failed"):
            self.publisher._pull_public_image(pull_contract)

        self.publisher._docker_login.reset_mock()
        self.publisher._manager_public_image_available = Mock(return_value=False)
        self.publisher._load_host_cached_image = Mock(return_value=False)
        self.publisher._run_manager_shell = Mock(
            return_value=subprocess.CompletedProcess([], 0, stdout="", stderr="")
        )
        self.assertTrue(self.publisher.image_available(build_contract))
        self.publisher._docker_login.assert_called_once_with()

    def test_manager_cache_inspection_and_shell_errors_are_typed(self):
        contract = ContainerImageContract("example/image", "1", "jenkins")
        self.publisher._run_manager_shell = Mock(
            return_value=subprocess.CompletedProcess([], 0, stdout="", stderr="")
        )
        self.assertTrue(self.publisher._manager_build_image_available(contract))
        self.assertTrue(self.publisher._manager_public_image_available(contract))

        self.publisher._run_manager_shell = Mock(
            return_value=subprocess.CompletedProcess([], 1, stdout="", stderr="")
        )
        self.assertFalse(self.publisher._manager_build_image_available(contract))
        del self.publisher._run_manager_shell

        with patch_run(side_effect=subprocess.TimeoutExpired("lxc", 30)):
            with self.assertRaises(ImagePublisherOperationRejected) as raised:
                self.publisher._run_manager_shell(
                    "true", operation="build_image", timeout_seconds=30
                )
        self.assertEqual(raised.exception.diagnostic, "operation_timeout")

        with patch_run(
            return_value=subprocess.CompletedProcess([], 17, stdout="", stderr="no space left on device")
        ):
            with self.assertRaises(ImagePublisherOperationRejected) as raised:
                self.publisher._run_manager_shell(
                    "true", operation="build_image", timeout_seconds=30
                )
        self.assertEqual(raised.exception.diagnostic, "manager_storage_exhausted")

    def test_host_cache_loader_and_byte_transfer_cover_external_command_results(self):
        contract = ContainerImageContract("redis", "7", "redis", source="pull")
        with patch_run(side_effect=FileNotFoundError):
            self.assertFalse(self.publisher._load_host_cached_image(contract))
        with patch_run(
            return_value=subprocess.CompletedProcess([], 1, stdout="", stderr="missing")
        ):
            self.assertFalse(self.publisher._load_host_cached_image(contract))
        with patch_run(
            side_effect=(
                subprocess.CompletedProcess([], 0, stdout="", stderr=""),
                subprocess.CompletedProcess([], 0, stdout="", stderr=""),
            )
        ):
            self.assertTrue(self.publisher._load_host_cached_image(contract))
        with patch_run(
            side_effect=(
                subprocess.CompletedProcess([], 0, stdout="", stderr=""),
                subprocess.CompletedProcess([], 1, stdout="", stderr="load failed"),
            )
        ):
            self.assertFalse(self.publisher._load_host_cached_image(contract))

        with patch_run(side_effect=subprocess.TimeoutExpired("lxc", 30)):
            with self.assertRaisesRegex(RuntimeError, "transfer timed out"):
                self.publisher._run_manager_shell_bytes(
                    "true", input_bytes=b"data", timeout_seconds=30
                )
        with patch_run(
            return_value=subprocess.CompletedProcess([], 17, stdout=b"", stderr=b"failure")
        ):
            with self.assertRaisesRegex(RuntimeError, "exit code 17"):
                self.publisher._run_manager_shell_bytes(
                    "true", input_bytes=b"data", timeout_seconds=30
                )

    def test_transfer_context_archives_regular_files(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            context_path = Path(temporary_directory)
            (context_path / "Dockerfile").write_text("FROM scratch\n", encoding="utf-8")
            self.publisher._run_manager_shell_bytes = Mock(
                return_value=subprocess.CompletedProcess([], 0, stdout=b"", stderr=b"")
            )

            self.publisher._transfer_context(context_path, "/tmp/context")

        self.publisher._run_manager_shell_bytes.assert_called_once()
        self.assertIn(b"Dockerfile", self.publisher._run_manager_shell_bytes.call_args.kwargs["input_bytes"])


def patch_run(*, return_value=None, side_effect=None):
    return patch(
        "tiny_swarm_world.infrastructure.adapters.clients.lxc.images.lxc_container_image_publisher.subprocess.run",
        return_value=return_value,
        side_effect=side_effect,
    )
