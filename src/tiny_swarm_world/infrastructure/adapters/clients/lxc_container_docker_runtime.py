from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.parse import urlparse
from collections.abc import Sequence
from logging import Logger

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
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory


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
  curl -fsSL "${TSW_DOCKER_APT_GPG_URL:-https://download.docker.com/linux/ubuntu/gpg}" -o /etc/apt/keyrings/docker.asc
fi
chmod a+r /etc/apt/keyrings/docker.asc
. /etc/os-release
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] ${TSW_DOCKER_APT_URL:-https://download.docker.com/linux/ubuntu} ${VERSION_CODENAME} stable" > /etc/apt/sources.list.d/docker.list
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker || service docker start || true
docker info >/dev/null
""".strip()


@dataclass(frozen=True)
class DockerRegistryMirrorConfiguration:
    mirror_url: str

    def __post_init__(self) -> None:
        parsed_url = urlparse(self.mirror_url)
        if parsed_url.scheme not in {"http", "https"}:
            raise ValueError("Docker registry mirror URL must use http or https.")
        if not parsed_url.hostname:
            raise ValueError("Docker registry mirror URL must include a host.")
        if parsed_url.hostname in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("LXC Docker registry mirror must be reachable from inside LXC nodes.")
        if parsed_url.username or parsed_url.password:
            raise ValueError("Docker registry mirror URL must not contain credentials.")
        if parsed_url.query or parsed_url.fragment:
            raise ValueError("Docker registry mirror URL must not contain query or fragment parts.")

    @property
    def registry_authority(self) -> str:
        parsed_url = urlparse(self.mirror_url)
        if parsed_url.port is None:
            return parsed_url.hostname or ""
        return f"{parsed_url.hostname}:{parsed_url.port}"


@dataclass(frozen=True)
class DockerAptMirrorConfiguration:
    ubuntu_archive_url: str | None = None
    ubuntu_security_url: str | None = None
    docker_apt_url: str | None = None
    docker_gpg_url: str | None = None

    def __post_init__(self) -> None:
        for label, value in (
            ("Ubuntu archive APT mirror", self.ubuntu_archive_url),
            ("Ubuntu security APT mirror", self.ubuntu_security_url),
            ("Docker APT mirror", self.docker_apt_url),
            ("Docker APT GPG URL", self.docker_gpg_url),
        ):
            if value is not None:
                _validate_lxc_reachable_url(label, value)

    @property
    def configured(self) -> bool:
        return any(
            (
                self.ubuntu_archive_url,
                self.ubuntu_security_url,
                self.docker_apt_url,
                self.docker_gpg_url,
            )
        )


class LxcContainerDockerRuntime(PortContainerDockerRuntime):
    def __init__(
        self,
        *,
        backend: ManagedLxcBackend,
        runner: LxcNodeCommandRunner,
        inspect_timeout_seconds: float = DEFAULT_DOCKER_INSPECT_TIMEOUT_SECONDS,
        install_timeout_seconds: float = DEFAULT_DOCKER_INSTALL_TIMEOUT_SECONDS,
        allow_live_mutation: bool = False,
        registry_mirror: DockerRegistryMirrorConfiguration | None = None,
        apt_mirror: DockerAptMirrorConfiguration | None = None,
        logger: Logger | None = None,
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
        self.registry_mirror = registry_mirror
        self.apt_mirror = apt_mirror
        self.logger = logger or LoggerFactory.get_logger(self.__class__.__name__)

    async def inspect_docker(self, node: NodeSpec) -> ContainerDockerReadiness:
        result = await self.runner.run(
            _docker_info_args(self.backend, node),
            self.inspect_timeout_seconds,
        )
        self._log_command_result("inspect_docker", node, result)
        return _readiness_from_result(node, result)

    async def install_docker(self, node: NodeSpec) -> ContainerDockerInstallOutcome:
        if not self.allow_live_mutation:
            self.logger.warning(
                "lxc_container_docker_runtime mutation_refused action=install node=%s",
                node.name,
            )
            return ContainerDockerInstallOutcome(
                node=node,
                state=DockerInstallState.FAILED,
                verified=False,
            )

        self.logger.info(
            "lxc_container_docker_runtime install_start backend=%s node=%s mirror=%s",
            self.backend.value,
            node.name,
            self.registry_mirror.registry_authority if self.registry_mirror else "",
        )
        result = await self.runner.run(
            _docker_install_args(
                self.backend,
                node,
                self.registry_mirror,
                self.apt_mirror,
            ),
            self.install_timeout_seconds,
        )
        self._log_command_result("install_docker", node, result)
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

    def _log_command_result(
        self,
        action: str,
        node: NodeSpec,
        result: LxcNodeCommandResult,
    ) -> None:
        log = self.logger.warning if _command_failed(result) else self.logger.info
        log(
            "lxc_container_docker_runtime action=%s backend=%s node=%s returncode=%s timed_out=%s stdout=%s stderr=%s",
            action,
            self.backend.value,
            node.name,
            result.returncode,
            str(result.timed_out).lower(),
            _safe_log_text(result.stdout),
            _safe_log_text(result.stderr),
        )


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
    registry_mirror: DockerRegistryMirrorConfiguration | None = None,
    apt_mirror: DockerAptMirrorConfiguration | None = None,
) -> tuple[str, ...]:
    return (
        _BACKEND_CLI[backend],
        "exec",
        node.name,
        "--",
        "bash",
        "-lc",
        _docker_install_script(registry_mirror, apt_mirror),
    )


def _docker_install_script(
    registry_mirror: DockerRegistryMirrorConfiguration | None,
    apt_mirror: DockerAptMirrorConfiguration | None = None,
) -> str:
    script_parts = [_apt_mirror_script(apt_mirror), _DOCKER_INSTALL_SCRIPT]
    if registry_mirror is None:
        return "\n".join(part for part in script_parts if part)

    daemon_config = json.dumps(
        {
            "registry-mirrors": [registry_mirror.mirror_url],
            "insecure-registries": [registry_mirror.registry_authority],
        },
        indent=2,
    )
    return "\n".join(
        tuple(part for part in script_parts if part)
        + (
            "install -m 0755 -d /etc/docker",
            "cat > /etc/docker/daemon.json <<'TSW_DOCKER_DAEMON_JSON'",
            daemon_config,
            "TSW_DOCKER_DAEMON_JSON",
            "systemctl restart docker || service docker restart || true",
            "docker info >/dev/null",
        )
    )


def _apt_mirror_script(apt_mirror: DockerAptMirrorConfiguration | None) -> str:
    if apt_mirror is None or not apt_mirror.configured:
        return ""

    lines = [
        "install -m 0755 -d /etc/apt/sources.list.d /etc/apt/keyrings",
    ]
    if apt_mirror.ubuntu_archive_url:
        security_url = apt_mirror.ubuntu_security_url or apt_mirror.ubuntu_archive_url
        lines.extend(
            (
                ". /etc/os-release",
                "if [ -f /etc/apt/sources.list ]; then",
                "  mv /etc/apt/sources.list /etc/apt/sources.list.tsw-original",
                "fi",
                "cat > /etc/apt/sources.list.d/ubuntu.sources <<TSW_UBUNTU_APT_SOURCES",
                "Types: deb",
                f"URIs: {apt_mirror.ubuntu_archive_url}",
                "Suites: ${VERSION_CODENAME} ${VERSION_CODENAME}-updates",
                "Components: main restricted universe multiverse",
                "Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg",
                "",
                "Types: deb",
                f"URIs: {security_url}",
                "Suites: ${VERSION_CODENAME}-security",
                "Components: main restricted universe multiverse",
                "Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg",
                "TSW_UBUNTU_APT_SOURCES",
            )
        )
    if apt_mirror.docker_gpg_url:
        lines.extend(
            (
                "rm -f /etc/apt/keyrings/docker.asc",
                f"curl -fsSL {_shell_quote(apt_mirror.docker_gpg_url)} -o /etc/apt/keyrings/docker.asc",
            )
        )
    if apt_mirror.docker_apt_url:
        lines.extend(
            (
                ". /etc/os-release",
                f"TSW_DOCKER_APT_URL={_shell_quote(apt_mirror.docker_apt_url)}",
                'echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] ${TSW_DOCKER_APT_URL} ${VERSION_CODENAME} stable" > /etc/apt/sources.list.d/docker.list',
            )
        )
    return "\n".join(lines)


def _shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def _validate_lxc_reachable_url(label: str, value: str) -> None:
    parsed_url = urlparse(value)
    if parsed_url.scheme not in {"http", "https"}:
        raise ValueError(f"{label} must use http or https.")
    if not parsed_url.hostname:
        raise ValueError(f"{label} must include a host.")
    if parsed_url.hostname in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError(f"{label} must be reachable from inside LXC nodes.")
    if parsed_url.username or parsed_url.password:
        raise ValueError(f"{label} must not contain credentials.")
    if parsed_url.query or parsed_url.fragment:
        raise ValueError(f"{label} must not contain query or fragment parts.")


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


def _safe_log_text(value: str, limit: int = 400) -> str:
    collapsed = " ".join(value.split())
    if len(collapsed) <= limit:
        return collapsed
    return f"{collapsed[:limit]}..."


def redact_argv_for_test(args: Sequence[str]) -> tuple[str, ...]:
    return tuple("<script>" if item == _DOCKER_INSTALL_SCRIPT else item for item in args)
