from __future__ import annotations

from collections.abc import Sequence

from tiny_swarm_world.application.ports.node_provider import PortContainerDockerRuntime
from tiny_swarm_world.domain.node_provider import (
    ContainerDockerInstallOutcome,
    ContainerDockerReadiness,
    DockerEngineState,
    DockerInstallState,
    ManagedLxcBackend,
    NodeSpec,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc_node_provider import (
    LxcNodeCommandResult,
    LxcNodeCommandRunner,
)


DEFAULT_DOCKER_INSPECT_TIMEOUT_SECONDS = 30.0
DEFAULT_DOCKER_INSTALL_TIMEOUT_SECONDS = 600.0

_BACKEND_CLI = {
    ManagedLxcBackend.INCUS: "incus",
    ManagedLxcBackend.LXD: "lxc",
}

_DOCKER_INSTALL_SCRIPT = """
set -eu
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
if [ ! -f /etc/apt/keyrings/docker.asc ]; then
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
fi
chmod a+r /etc/apt/keyrings/docker.asc
. /etc/os-release
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" > /etc/apt/sources.list.d/docker.list
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker || service docker start || true
docker info >/dev/null
""".strip()


class LxcContainerDockerRuntime(PortContainerDockerRuntime):
    def __init__(
        self,
        *,
        backend: ManagedLxcBackend,
        runner: LxcNodeCommandRunner,
        inspect_timeout_seconds: float = DEFAULT_DOCKER_INSPECT_TIMEOUT_SECONDS,
        install_timeout_seconds: float = DEFAULT_DOCKER_INSTALL_TIMEOUT_SECONDS,
        allow_live_mutation: bool = False,
    ) -> None:
        if inspect_timeout_seconds <= 0:
            raise ValueError("Docker inspect timeout must be positive.")
        if install_timeout_seconds <= 0:
            raise ValueError("Docker install timeout must be positive.")
        self.backend = backend
        self.runner = runner
        self.inspect_timeout_seconds = inspect_timeout_seconds
        self.install_timeout_seconds = install_timeout_seconds
        self.allow_live_mutation = allow_live_mutation

    async def inspect_docker(self, node: NodeSpec) -> ContainerDockerReadiness:
        result = await self.runner.run(
            _docker_info_args(self.backend, node),
            self.inspect_timeout_seconds,
        )
        return _readiness_from_result(node, result)

    async def install_docker(self, node: NodeSpec) -> ContainerDockerInstallOutcome:
        if not self.allow_live_mutation:
            return ContainerDockerInstallOutcome(
                node=node,
                state=DockerInstallState.FAILED,
                verified=False,
            )

        result = await self.runner.run(
            _docker_install_args(self.backend, node),
            self.install_timeout_seconds,
        )
        if _command_failed(result):
            return ContainerDockerInstallOutcome(
                node=node,
                state=DockerInstallState.FAILED,
                verified=False,
            )

        readiness = await self.verify_docker(node)
        return ContainerDockerInstallOutcome(
            node=node,
            state=DockerInstallState.INSTALLED,
            verified=readiness.ready,
        )

    async def verify_docker(self, node: NodeSpec) -> ContainerDockerReadiness:
        return await self.inspect_docker(node)


def _docker_info_args(
    backend: ManagedLxcBackend,
    node: NodeSpec,
) -> tuple[str, ...]:
    return (
        _BACKEND_CLI[backend],
        "exec",
        node.name,
        "--",
        "docker",
        "info",
        "--format",
        "{{json .ServerVersion}}",
    )


def _docker_install_args(
    backend: ManagedLxcBackend,
    node: NodeSpec,
) -> tuple[str, ...]:
    return (
        _BACKEND_CLI[backend],
        "exec",
        node.name,
        "--",
        "bash",
        "-lc",
        _DOCKER_INSTALL_SCRIPT,
    )


def _readiness_from_result(
    node: NodeSpec,
    result: LxcNodeCommandResult,
) -> ContainerDockerReadiness:
    if not _command_failed(result):
        return ContainerDockerReadiness(
            node=node,
            observed=True,
            engine_state=DockerEngineState.READY,
        )
    return ContainerDockerReadiness(
        node=node,
        observed=not result.timed_out,
        engine_state=_failure_state(result),
    )


def _failure_state(result: LxcNodeCommandResult) -> DockerEngineState:
    output = _combined_output(result)
    if result.timed_out:
        return DockerEngineState.UNKNOWN
    if "not found" in output or "no such file" in output:
        return DockerEngineState.MISSING
    return DockerEngineState.ERROR


def _combined_output(result: LxcNodeCommandResult) -> str:
    return f"{result.stdout}\n{result.stderr}".casefold()


def _command_failed(result: LxcNodeCommandResult) -> bool:
    return result.timed_out or result.returncode != 0


def redact_argv_for_test(args: Sequence[str]) -> tuple[str, ...]:
    return tuple("<script>" if item == _DOCKER_INSTALL_SCRIPT else item for item in args)
