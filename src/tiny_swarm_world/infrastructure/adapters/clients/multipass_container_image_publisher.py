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
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory
from tiny_swarm_world.infrastructure.project_paths import infra_root


class MultipassContainerImagePublisher(PortContainerImagePublisher):
    def __init__(
        self,
        registry_username: str,
        registry_password: str,
        manager_vm: str = "swarm-manager",
        remote_image_root: str = "/tmp/tiny-swarm-world/images",
        timeout_seconds: int = 1800,
    ):
        if timeout_seconds <= 0:
            raise ValueError("Image publisher timeout must be positive.")
        self.registry_username = registry_username
        self.registry_password = registry_password
        self.manager_vm = manager_vm
        self.remote_image_root = remote_image_root.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.logger = LoggerFactory.get_logger(self.__class__)

    def publish_image(self, contract: ContainerImageContract) -> None:
        context_path = self._context_path(contract)
        remote_context_path = f"{self.remote_image_root}/{contract.build_context}"
        self._transfer_context(context_path, remote_context_path)
        self._run_manager_shell(
            f"docker build -t {shlex.quote(contract.image_ref)} {shlex.quote(remote_context_path)}",
            timeout_seconds=self.timeout_seconds,
        )
        self._docker_login()
        self._run_manager_shell(
            f"docker push {shlex.quote(contract.image_ref)}",
            timeout_seconds=self.timeout_seconds,
        )

    def image_available(self, contract: ContainerImageContract) -> bool:
        self._docker_login()
        result = self._run_manager_shell(
            f"docker pull {shlex.quote(contract.image_ref)}",
            check=False,
            timeout_seconds=self.timeout_seconds,
        )
        return result.returncode == 0

    def _context_path(self, contract: ContainerImageContract) -> Path:
        contexts = {
            "jenkins": infra_root() / "compose" / "jenkins",
            "swagger-nginx": infra_root() / "compose" / "swagger" / "nginx",
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
            f"set -e; mkdir -p {shlex.quote(remote_context_path)}; "
            f"tar -x -C {shlex.quote(remote_context_path)}",
            input_bytes=archive.getvalue(),
            timeout_seconds=self.timeout_seconds,
        )

    def _docker_login(self) -> None:
        self._run_manager_shell(
            f"docker login -u {shlex.quote(self.registry_username)} --password-stdin 127.0.0.1:5000",
            input_text=f"{self.registry_password}\n",
            timeout_seconds=120,
        )

    def _run_manager_shell(
        self,
        script: str,
        *,
        check: bool = True,
        input_text: str | None = None,
        timeout_seconds: int,
    ) -> subprocess.CompletedProcess[str]:
        self.logger.info("Running manager image operation.")
        try:
            result = subprocess.run(
                ["multipass", "exec", self.manager_vm, "--", "sh", "-lc", script],
                input=input_text,
                capture_output=True,
                text=True,
                check=False,
                shell=False,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("Manager image operation timed out.") from exc
        if check and result.returncode != 0:
            raise RuntimeError(f"Manager image operation failed with exit code {result.returncode}.")
        return result

    def _run_manager_shell_bytes(
        self,
        script: str,
        *,
        input_bytes: bytes,
        timeout_seconds: int,
    ) -> subprocess.CompletedProcess[bytes]:
        try:
            result = subprocess.run(
                ["multipass", "exec", self.manager_vm, "--", "sh", "-lc", script],
                input=input_bytes,
                capture_output=True,
                check=False,
                shell=False,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("Manager image transfer timed out.") from exc
        if result.returncode != 0:
            raise RuntimeError(f"Manager image transfer failed with exit code {result.returncode}.")
        return result
