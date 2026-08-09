"""Container image publication through the managed LXC Swarm manager."""

from __future__ import annotations

import io
import shlex
import subprocess
import tarfile
from pathlib import Path

from tiny_swarm_world.application.ports.clients.port_container_image_publisher import (
    PortContainerImagePublisher,
)
from tiny_swarm_world.domain.artifacts import ContainerImageContract
from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
from tiny_swarm_world.infrastructure.adapters.clients.lxc.images.errors import (
    REGISTRY_RATE_LIMITED_OPERATOR_ACTION,
    ImagePublisherOperationRejected,
    PublicImagePullRejected,
    docker_hub_rate_limited,
    image_operation_failure_diagnostic,
    image_operation_operator_action,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.backend_cli import backend_cli
from tiny_swarm_world.infrastructure.adapters.clients.lxc.swarm.swarm_stack_runtime import (
    _quote_remote_path,
)
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory
from tiny_swarm_world.infrastructure.project_paths import ProjectPaths, default_project_paths
from tiny_swarm_world.infrastructure.process import (
    ProcessLaunchError,
    ProcessRunner,
    ProcessTimeoutError,
    SubprocessProcessRunner,
)


class LxcContainerImagePublisher(PortContainerImagePublisher):
    """Build, pull, cache, and publish images without exposing raw output."""

    def __init__(
        self,
        *,
        backend: ManagedLxcBackend,
        registry_username: str,
        registry_password: str,
        manager_node: str = "swarm-manager",
        remote_image_root: str = "$PWD/.tiny-swarm-world/images",
        timeout_seconds: int = 1800,
        project_paths: ProjectPaths | None = None,
        process_runner: ProcessRunner | None = None,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("Image publisher timeout must be positive.")
        self.backend = backend
        self.registry_username = registry_username
        self.registry_password = registry_password
        self.manager_node = manager_node
        self.remote_image_root = remote_image_root.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.project_paths = project_paths or default_project_paths()
        self.process_runner = process_runner or SubprocessProcessRunner()
        self.logger = LoggerFactory.get_logger(self.__class__)

    def publish_image(self, contract: ContainerImageContract) -> None:
        if contract.source == "pull":
            if self._manager_public_image_available(contract):
                self.logger.info(
                    "lxc_image_publisher public_cache_hit image=%s",
                    contract.image_ref,
                )
                return
            self._pull_public_image(contract)
            return
        if self._manager_build_image_available(contract):
            self.logger.info(
                "lxc_image_publisher build_cache_hit image=%s",
                contract.image_ref,
            )
            return
        context_path = self._context_path(contract)
        remote_context_path = f"{self.remote_image_root}/{contract.build_context}"
        self._transfer_context(context_path, remote_context_path)
        build_script = (
            f"docker build -t {shlex.quote(contract.image_ref)} "
            f"{_quote_remote_path(remote_context_path)}"
        )
        self._run_manager_shell(
            build_script,
            operation="build_image",
            timeout_seconds=self.timeout_seconds,
        )
        self._docker_login()
        self._run_manager_shell(
            f"docker push {shlex.quote(contract.image_ref)}",
            operation="push_image",
            timeout_seconds=self.timeout_seconds,
        )

    def _manager_build_image_available(self, contract: ContainerImageContract) -> bool:
        result = self._run_manager_shell(
            f"docker image inspect {shlex.quote(contract.image_ref)}",
            check=False,
            operation="inspect_cached_build_image",
            timeout_seconds=min(self.timeout_seconds, 60),
        )
        return result.returncode == 0

    def _manager_public_image_available(self, contract: ContainerImageContract) -> bool:
        result = self._run_manager_shell(
            f"docker image inspect {shlex.quote(contract.image_ref)}",
            check=False,
            operation="inspect_cached_public_image",
            timeout_seconds=min(self.timeout_seconds, 60),
        )
        return result.returncode == 0

    def image_available(self, contract: ContainerImageContract) -> bool:
        if contract.source == "build":
            self._docker_login()
        elif self._manager_public_image_available(contract):
            self.logger.info(
                "lxc_image_publisher public_verify_cache_hit image=%s",
                contract.image_ref,
            )
            return True
        elif self._load_host_cached_image(contract):
            return True
        result = self._run_manager_shell(
            f"docker pull {shlex.quote(contract.image_ref)}",
            check=False,
            operation="verify_image_pull",
            timeout_seconds=self.timeout_seconds,
        )
        if result.returncode != 0 and docker_hub_rate_limited(result):
            if self._load_host_cached_image(contract):
                return True
            raise PublicImagePullRejected(
                contract.image_ref,
                diagnostic="registry_rate_limited",
                operator_action=REGISTRY_RATE_LIMITED_OPERATOR_ACTION,
            )
        return result.returncode == 0

    def _pull_public_image(self, contract: ContainerImageContract) -> None:
        if self._load_host_cached_image(contract):
            return
        result = self._run_manager_shell(
            f"docker pull {shlex.quote(contract.image_ref)}",
            check=False,
            operation="pull_public_image",
            timeout_seconds=self.timeout_seconds,
        )
        if result.returncode == 0:
            return
        if docker_hub_rate_limited(result):
            if self._load_host_cached_image(contract):
                return
            raise PublicImagePullRejected(
                contract.image_ref,
                diagnostic="registry_rate_limited",
                operator_action=REGISTRY_RATE_LIMITED_OPERATOR_ACTION,
            )
        raise RuntimeError("Public container image pull failed.")

    def _load_host_cached_image(self, contract: ContainerImageContract) -> bool:
        try:
            inspect_result = self.process_runner.run_text(
                ["docker", "image", "inspect", contract.image_ref],
                capture_output=True,
                check=False,
                shell=False,
                timeout=120,
            )
        except ProcessLaunchError:
            return False
        if inspect_result.returncode != 0:
            return False

        command = (
            "set -o pipefail; "
            f"docker save {shlex.quote(contract.image_ref)} | "
            f"{shlex.quote(backend_cli(self.backend))} exec {shlex.quote(self.manager_node)} -- docker load"
        )
        load_result = self.process_runner.run_text(
            ["bash", "-lc", command],
            capture_output=True,
            check=False,
            shell=False,
            timeout=self.timeout_seconds,
        )
        return load_result.returncode == 0

    def _context_path(self, contract: ContainerImageContract) -> Path:
        contexts = {
            "jenkins": self.project_paths.infra_root / "config" / "compose" / "jenkins" / "image",
            "service-access-dashboard": self.project_paths.infra_root / "config" / "compose" / "service-access" / "dashboard",
            "service-access-nginx": self.project_paths.infra_root / "config" / "compose" / "service-access" / "nginx",
        }
        try:
            return contexts[contract.build_context]
        except KeyError as exc:
            raise ValueError(f"Unknown image build context '{contract.build_context}'.") from exc

    def _transfer_context(self, context_path: Path, remote_context_path: str) -> None:
        archive = io.BytesIO()
        with tarfile.open(fileobj=archive, mode="w") as tar:
            for source_file in sorted(context_path.iterdir()):
                if source_file.is_file():
                    tar.add(source_file, arcname=source_file.name)
        archive.seek(0)
        self._run_manager_shell_bytes(
            f"set -e; mkdir -p {_quote_remote_path(remote_context_path)}; "
            f"tar -x -C {_quote_remote_path(remote_context_path)}",
            input_bytes=archive.getvalue(),
            timeout_seconds=self.timeout_seconds,
        )

    def _docker_login(self) -> None:
        login_script = (
            f"docker login -u {shlex.quote(self.registry_username)} "
            "--password-stdin 127.0.0.1:13500"
        )
        self._run_manager_shell(
            login_script,
            input_text=f"{self.registry_password}\n",
            operation="registry_login",
            timeout_seconds=120,
        )

    def _run_manager_shell(
        self,
        script: str,
        *,
        check: bool = True,
        input_text: str | None = None,
        operation: str = "manager_image_operation",
        timeout_seconds: int,
    ) -> subprocess.CompletedProcess[str]:
        self.logger.info("Running LXC manager image operation.")
        try:
            result = self.process_runner.run_text(
                [backend_cli(self.backend), "exec", self.manager_node, "--", "sh", "-lc", script],
                input=input_text,
                capture_output=True,
                check=False,
                shell=False,
                timeout=timeout_seconds,
            )
        except ProcessTimeoutError as exc:
            raise ImagePublisherOperationRejected(
                operation=operation,
                diagnostic="operation_timeout",
                operator_action=(
                    "Inspect the manager node Docker daemon and retry the artifact prepare phase."
                ),
            ) from exc
        except ProcessLaunchError as exc:
            raise ImagePublisherOperationRejected(
                operation=operation,
                diagnostic="operation_unavailable",
                operator_action=(
                    "Inspect the manager node Docker daemon and retry the artifact prepare phase."
                ),
            ) from exc
        if check and result.returncode != 0:
            raise ImagePublisherOperationRejected(
                operation=operation,
                diagnostic=image_operation_failure_diagnostic(operation, result),
                operator_action=image_operation_operator_action(operation, result),
                exit_code=result.returncode,
            )
        return result

    def _run_manager_shell_bytes(
        self,
        script: str,
        *,
        input_bytes: bytes,
        timeout_seconds: int,
    ) -> subprocess.CompletedProcess[bytes]:
        try:
            result = self.process_runner.run_bytes(
                [backend_cli(self.backend), "exec", self.manager_node, "--", "sh", "-lc", script],
                input=input_bytes,
                capture_output=True,
                check=False,
                shell=False,
                timeout=timeout_seconds,
            )
        except ProcessTimeoutError as exc:
            raise RuntimeError("LXC manager image transfer timed out.") from exc
        except ProcessLaunchError as exc:
            raise RuntimeError("LXC manager image transfer could not start.") from exc
        if result.returncode != 0:
            raise RuntimeError(
                f"LXC manager image transfer failed with exit code {result.returncode}."
            )
        return result
