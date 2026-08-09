"""Container inspection through Docker running inside managed LXC nodes."""

from __future__ import annotations

import subprocess

from tiny_swarm_world.application.ports.clients.port_container_runtime import PortContainerRuntime
from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory
from tiny_swarm_world.infrastructure.process import (
    ProcessRunner,
    SubprocessProcessRunner,
)


_BACKEND_CLI = {
    ManagedLxcBackend.INCUS: "incus",
    ManagedLxcBackend.LXD: "lxc",
}


class LxcContainerRuntime(PortContainerRuntime):
    """Inspect files and containers through a node-local Docker daemon."""

    def __init__(
        self,
        *,
        backend: ManagedLxcBackend,
        manager_node: str = "swarm-manager",
        node_names: tuple[str, ...] = ("swarm-manager",),
        timeout_seconds: int = 120,
        process_runner: ProcessRunner | None = None,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("Container runtime timeout must be positive.")
        if not node_names:
            raise ValueError("Container runtime node list must not be empty.")
        self.backend = backend
        self.manager_node = manager_node
        self.node_names = tuple(dict.fromkeys(node_names))
        self.timeout_seconds = timeout_seconds
        self.process_runner = process_runner or SubprocessProcessRunner()
        self.logger = LoggerFactory.get_logger(self.__class__)

    def find_container_names(self, name_filter: str) -> list[str]:
        container_names: list[str] = []
        for node_name in self.node_names:
            result = self._run_docker(
                ["ps", "--filter", f"name={name_filter}", "--format", "{{.Names}}"],
                check=False,
                node_name=node_name,
            )
            container_names.extend(
                _lxc_container_ref(node_name, line.strip())
                for line in result.stdout.splitlines()
                if line.strip()
            )
        return container_names

    def file_exists(self, container_name: str, file_path: str) -> bool:
        node_name, resolved_container_name = _split_lxc_container_ref(
            container_name,
            self.manager_node,
        )
        result = self._run_docker(
            ["exec", resolved_container_name, "test", "-f", file_path],
            check=False,
            node_name=node_name,
        )
        return result.returncode == 0

    def read_file(self, container_name: str, file_path: str) -> str:
        node_name, resolved_container_name = _split_lxc_container_ref(
            container_name,
            self.manager_node,
        )
        result = self._run_docker(
            ["exec", resolved_container_name, "cat", file_path],
            check=True,
            node_name=node_name,
        )
        return result.stdout

    def _run_docker(
        self,
        docker_args: list[str],
        *,
        check: bool,
        node_name: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        operation = docker_args[0] if docker_args else "operation"
        target_node = node_name or self.manager_node
        self.logger.info("Running LXC Docker operation '%s' on node '%s'.", operation, target_node)
        try:
            result = subprocess.run(
                [_BACKEND_CLI[self.backend], "exec", target_node, "--", "docker", *docker_args],
                capture_output=True,
                text=True,
                check=False,
                shell=False,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"LXC Docker runtime operation timed out on node '{target_node}'."
            ) from exc
        if check and result.returncode != 0:
            raise RuntimeError(
                "LXC Docker runtime operation failed on node "
                f"'{target_node}' with exit code {result.returncode}."
            )
        return result


def _lxc_container_ref(node_name: str, container_name: str) -> str:
    return f"{node_name}::{container_name}"


def _split_lxc_container_ref(container_ref: str, default_node: str) -> tuple[str, str]:
    node_name, separator, container_name = container_ref.partition("::")
    if not separator:
        return default_node, container_ref
    return node_name, container_name
