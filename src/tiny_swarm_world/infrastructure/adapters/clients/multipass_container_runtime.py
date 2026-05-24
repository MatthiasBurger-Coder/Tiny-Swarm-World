from __future__ import annotations

import subprocess

from tiny_swarm_world.application.ports.clients.port_container_runtime import (
    PortContainerRuntime,
)
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory


class MultipassContainerRuntime(PortContainerRuntime):
    def __init__(self, manager_vm: str = "swarm-manager", timeout_seconds: int = 120):
        if timeout_seconds <= 0:
            raise ValueError("Container runtime timeout must be positive.")
        self.manager_vm = manager_vm
        self.timeout_seconds = timeout_seconds
        self.logger = LoggerFactory.get_logger(self.__class__)

    def find_container_names(self, name_filter: str) -> list[str]:
        result = self._run_docker(
            ["ps", "--filter", f"name={name_filter}", "--format", "{{.Names}}"],
            check=False,
        )
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]

    def file_exists(self, container_name: str, file_path: str) -> bool:
        result = self._run_docker(["exec", container_name, "test", "-f", file_path], check=False)
        return result.returncode == 0

    def read_file(self, container_name: str, file_path: str) -> str:
        result = self._run_docker(["exec", container_name, "cat", file_path], check=True)
        return result.stdout

    def _run_docker(
        self,
        docker_args: list[str],
        *,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        operation = docker_args[0] if docker_args else "operation"
        self.logger.info("Running manager Docker operation '%s'.", operation)
        try:
            result = subprocess.run(
                ["multipass", "exec", self.manager_vm, "--", "docker", *docker_args],
                capture_output=True,
                text=True,
                check=False,
                shell=False,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("Manager Docker runtime operation timed out.") from exc
        if check and result.returncode != 0:
            raise RuntimeError(f"Manager Docker runtime operation failed with exit code {result.returncode}.")
        return result
